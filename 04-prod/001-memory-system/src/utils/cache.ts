import { EventEmitter } from 'events';
import { logger } from './logger';
import type { CacheConfig } from '../types/base';

export interface CacheItem<T = any> {
  key: string;
  value: T;
  createdAt: Date;
  expiresAt?: Date | undefined;
  accessCount: number;
  lastAccessed: Date;
  size: number; // 估算的内存大小
  tags?: string[] | undefined;
}

export interface CacheStats {
  totalItems: number;
  totalMemory: number;
  hitCount: number;
  missCount: number;
  hitRate: number;
  oldestItem?: Date | undefined;
  newestItem?: Date | undefined;
  averageAccessCount: number;
}

export class Cache<T = any> extends EventEmitter {
  private config: CacheConfig;
  private items: Map<string, CacheItem<T>> = new Map();
  private hitCount: number = 0;
  private missCount: number = 0;
  private cleanupTimer: NodeJS.Timeout | null = null;
  private totalMemory: number = 0;

  constructor(config: Partial<CacheConfig> = {}) {
    super();
    
    this.config = {
      enabled: true,
      maxSize: 1000,
      ttl: 60 * 60 * 1000,
      strategy: 'lru',
      maxMemory: 100 * 1024 * 1024, // 100MB
      defaultTTL: 60 * 60 * 1000, // 1小时
      cleanupInterval: 5 * 60 * 1000, // 5分钟
      enablePersistence: false,
      compressionEnabled: false,
      ...config
    };

    this.startCleanupTimer();
    
    if (this.config.enablePersistence && this.config.persistenceFile) {
      this.loadFromPersistence();
    }
  }

  private startCleanupTimer(): void {
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);
  }

  private stopCleanupTimer(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  private estimateSize(value: T): number {
    try {
      const jsonString = JSON.stringify(value);
      return jsonString.length * 2; // 假设每个字符占用2字节
    } catch {
      return 1024; // 默认1KB
    }
  }

  private evictLRU(): void {
    if (this.items.size === 0) return;

    // 找到最少使用的项
    let lruKey: string | null = null;
    let lruTime = new Date();
    
    for (const [key, item] of Array.from(this.items)) {
      if (item.lastAccessed < lruTime) {
        lruTime = item.lastAccessed;
        lruKey = key;
      }
    }
    
    if (lruKey) {
      this.delete(lruKey);
      logger.debug('Evicted LRU item', { key: lruKey }, 'Cache');
    }
  }

  private evictByMemory(): void {
    // 按访问频率排序，删除最少使用的项
    const sortedItems = Array.from(this.items.entries())
      .sort(([, a], [, b]) => a.accessCount - b.accessCount);
    
    for (const [key] of sortedItems) {
      this.delete(key);
      if (this.totalMemory <= (this.config.maxMemory || 0) * 0.8) {
        break;
      }
    }
  }

  public set(
    key: string, 
    value: T, 
    ttl?: number, 
    tags?: string[]
  ): void {
    const now = new Date();
    const size = this.estimateSize(value);
    const expiresAt = ttl ? new Date(now.getTime() + ttl) : 
                     ((this.config.defaultTTL || 0) > 0 ? new Date(now.getTime() + (this.config.defaultTTL || 0)) : undefined);

    // 检查是否需要删除现有项
    if (this.items.has(key)) {
      const existingItem = this.items.get(key)!;
      this.totalMemory -= existingItem.size;
    }

    // 检查大小限制
    while (this.items.size >= this.config.maxSize && !this.items.has(key)) {
      this.evictLRU();
    }

    // 检查内存限制
    while (this.totalMemory + size > (this.config.maxMemory || 0)) {
      this.evictByMemory();
    }

    const item: CacheItem<T> = {
      key,
      value,
      createdAt: now,
      expiresAt,
      accessCount: 0,
      lastAccessed: now,
      size,
      tags
    };

    this.items.set(key, item);
    this.totalMemory += size;

    logger.debug('Cache item set', { 
      key, 
      size, 
      expiresAt, 
      tags,
      totalItems: this.items.size,
      totalMemory: this.totalMemory
    }, 'Cache');

    this.emit('set', { key, value, item });
  }

  public get(key: string): T | undefined {
    const item = this.items.get(key);
    
    if (!item) {
      this.missCount++;
      this.emit('miss', { key });
      return undefined;
    }

    // 检查是否过期
    if (item.expiresAt && item.expiresAt <= new Date()) {
      this.delete(key);
      this.missCount++;
      this.emit('miss', { key, reason: 'expired' });
      return undefined;
    }

    // 更新访问信息
    item.accessCount++;
    item.lastAccessed = new Date();
    
    this.hitCount++;
    this.emit('hit', { key, item });
    
    return item.value;
  }

  public has(key: string): boolean {
    const item = this.items.get(key);
    
    if (!item) return false;
    
    // 检查是否过期
    if (item.expiresAt && item.expiresAt <= new Date()) {
      this.delete(key);
      return false;
    }
    
    return true;
  }

  public delete(key: string): boolean {
    const item = this.items.get(key);
    
    if (!item) return false;
    
    this.items.delete(key);
    this.totalMemory -= item.size;
    
    logger.debug('Cache item deleted', { 
      key, 
      size: item.size,
      totalItems: this.items.size,
      totalMemory: this.totalMemory
    }, 'Cache');
    
    this.emit('delete', { key, item });
    return true;
  }

  public clear(): void {
    const itemCount = this.items.size;
    this.items.clear();
    this.totalMemory = 0;
    this.hitCount = 0;
    this.missCount = 0;
    
    logger.info('Cache cleared', { itemCount }, 'Cache');
    this.emit('clear', { itemCount });
  }

  public keys(): string[] {
    return Array.from(this.items.keys());
  }

  public values(): T[] {
    return Array.from(this.items.values()).map(item => item.value);
  }

  public entries(): [string, T][] {
    return Array.from(this.items.entries()).map(([key, item]) => [key, item.value]);
  }

  public getByTag(tag: string): Map<string, T> {
    const result = new Map<string, T>();
    
    for (const [key, item] of Array.from(this.items)) {
      if (item.tags && item.tags.includes(tag)) {
        // 检查是否过期
        if (!item.expiresAt || item.expiresAt > new Date()) {
          result.set(key, item.value);
        }
      }
    }
    
    return result;
  }

  public deleteByTag(tag: string): number {
    let deletedCount = 0;
    
    for (const [key, item] of Array.from(this.items)) {
      if (item.tags && item.tags.includes(tag)) {
        this.delete(key);
        deletedCount++;
      }
    }
    
    logger.debug('Cache items deleted by tag', { tag, deletedCount }, 'Cache');
    return deletedCount;
  }

  public touch(key: string, ttl?: number): boolean {
    const item = this.items.get(key);
    
    if (!item) return false;
    
    const now = new Date();
    item.lastAccessed = now;
    
    if (ttl !== undefined) {
      item.expiresAt = ttl > 0 ? new Date(now.getTime() + ttl) : undefined;
    }
    
    return true;
  }

  public cleanup(): void {
    const now = new Date();
    let cleanedCount = 0;
    
    for (const [key, item] of Array.from(this.items)) {
      if (item.expiresAt && item.expiresAt <= now) {
        this.delete(key);
        cleanedCount++;
      }
    }
    
    if (cleanedCount > 0) {
      logger.debug('Cache cleanup completed', { cleanedCount }, 'Cache');
      this.emit('cleanup', { cleanedCount });
    }
  }

  public getStats(): CacheStats {
    const items = Array.from(this.items.values());
    const totalAccess = items.reduce((sum, item) => sum + item.accessCount, 0);
    const dates = items.map(item => item.createdAt);
    
    return {
      totalItems: this.items.size,
      totalMemory: this.totalMemory,
      hitCount: this.hitCount,
      missCount: this.missCount,
      hitRate: this.hitCount + this.missCount > 0 ? 
               this.hitCount / (this.hitCount + this.missCount) : 0,
      oldestItem: dates.length > 0 ? new Date(Math.min(...dates.map(d => d.getTime()))) : undefined,
      newestItem: dates.length > 0 ? new Date(Math.max(...dates.map(d => d.getTime()))) : undefined,
      averageAccessCount: items.length > 0 ? totalAccess / items.length : 0
    };
  }

  public getItem(key: string): CacheItem<T> | undefined {
    return this.items.get(key);
  }

  public getAllItems(): CacheItem<T>[] {
    return Array.from(this.items.values());
  }

  public resize(maxSize: number, maxMemory?: number): void {
    this.config.maxSize = maxSize;
    if (maxMemory !== undefined) {
      this.config.maxMemory = maxMemory;
    }
    
    // 如果当前大小超过新限制，进行清理
    while (this.items.size > this.config.maxSize) {
      this.evictLRU();
    }
    
    while (this.totalMemory > (this.config.maxMemory || 0)) {
      this.evictByMemory();
    }
    
    logger.info('Cache resized', { 
      maxSize: this.config.maxSize, 
      maxMemory: this.config.maxMemory 
    }, 'Cache');
  }

  private async loadFromPersistence(): Promise<void> {
    if (!this.config.persistenceFile) return;
    
    try {
      const fs = await import('fs/promises');
      const data = await fs.readFile(this.config.persistenceFile, 'utf-8');
      const parsed = JSON.parse(data);
      
      for (const itemData of parsed.items || []) {
        const item: CacheItem<T> = {
          ...itemData,
          createdAt: new Date(itemData.createdAt),
          expiresAt: itemData.expiresAt ? new Date(itemData.expiresAt) : undefined,
          lastAccessed: new Date(itemData.lastAccessed)
        };
        
        // 检查是否过期
        if (!item.expiresAt || item.expiresAt > new Date()) {
          this.items.set(item.key, item);
          this.totalMemory += item.size;
        }
      }
      
      logger.info('Cache loaded from persistence', { 
        file: this.config.persistenceFile,
        itemCount: this.items.size
      }, 'Cache');
      
    } catch (error) {
      logger.warn('Failed to load cache from persistence', { 
        file: this.config.persistenceFile,
        error 
      }, 'Cache');
    }
  }

  public async saveToPersistence(): Promise<void> {
    if (!this.config.enablePersistence || !this.config.persistenceFile) return;
    
    try {
      const fs = await import('fs/promises');
      const data = {
        version: '1.0',
        timestamp: new Date().toISOString(),
        items: Array.from(this.items.values())
      };
      
      await fs.writeFile(this.config.persistenceFile, JSON.stringify(data, null, 2));
      
      logger.debug('Cache saved to persistence', { 
        file: this.config.persistenceFile,
        itemCount: this.items.size
      }, 'Cache');
      
    } catch (error) {
      logger.error('Failed to save cache to persistence', { 
        file: this.config.persistenceFile,
        error 
      }, 'Cache');
    }
  }

  public destroy(): void {
    this.stopCleanupTimer();
    
    if (this.config.enablePersistence) {
      this.saveToPersistence().catch(error => {
        logger.error('Failed to save cache during destroy', { error }, 'Cache');
      });
    }
    
    this.clear();
    this.removeAllListeners();
    
    logger.info('Cache destroyed', {}, 'Cache');
  }
}

// 缓存管理器
export class CacheManager extends EventEmitter {
  private caches: Map<string, Cache> = new Map();
  private defaultConfig: CacheConfig;

  constructor(defaultConfig: Partial<CacheConfig> = {}) {
    super();
    
    this.defaultConfig = {
      enabled: true,
      maxSize: 1000,
      ttl: 60 * 60 * 1000,
      strategy: 'lru',
      maxMemory: 100 * 1024 * 1024, // 100MB
      defaultTTL: 60 * 60 * 1000, // 1小时
      cleanupInterval: 5 * 60 * 1000, // 5分钟
      enablePersistence: false,
      compressionEnabled: false,
      ...defaultConfig
    };
  }

  public createCache<T = any>(
    name: string, 
    config?: Partial<CacheConfig>
  ): Cache<T> {
    if (this.caches.has(name)) {
      throw new Error(`Cache '${name}' already exists`);
    }
    
    const cache = new Cache<T>({ ...this.defaultConfig, ...config });
    this.caches.set(name, cache as Cache);
    
    // 转发缓存事件
    cache.on('set', (data) => this.emit('cacheSet', { cacheName: name, ...data }));
    cache.on('hit', (data) => this.emit('cacheHit', { cacheName: name, ...data }));
    cache.on('miss', (data) => this.emit('cacheMiss', { cacheName: name, ...data }));
    cache.on('delete', (data) => this.emit('cacheDelete', { cacheName: name, ...data }));
    cache.on('clear', (data) => this.emit('cacheClear', { cacheName: name, ...data }));
    
    logger.info('Cache created', { name, config }, 'CacheManager');
    return cache;
  }

  public getCache<T = any>(name: string): Cache<T> | undefined {
    return this.caches.get(name) as Cache<T>;
  }

  public deleteCache(name: string): boolean {
    const cache = this.caches.get(name);
    if (!cache) return false;
    
    cache.destroy();
    this.caches.delete(name);
    
    logger.info('Cache deleted', { name }, 'CacheManager');
    return true;
  }

  public listCaches(): string[] {
    return Array.from(this.caches.keys());
  }

  public getAllStats(): Map<string, CacheStats> {
    const stats = new Map<string, CacheStats>();
    
    for (const [name, cache] of Array.from(this.caches)) {
      stats.set(name, cache.getStats());
    }
    
    return stats;
  }

  public clearAllCaches(): void {
    for (const cache of Array.from(this.caches.values())) {
      cache.clear();
    }
    
    logger.info('All caches cleared', { cacheCount: this.caches.size }, 'CacheManager');
  }

  public destroy(): void {
    for (const cache of Array.from(this.caches.values())) {
      cache.destroy();
    }
    
    this.caches.clear();
    this.removeAllListeners();
    
    logger.info('Cache manager destroyed', {}, 'CacheManager');
  }
}

// 全局缓存管理器实例
export const cacheManager = new CacheManager();