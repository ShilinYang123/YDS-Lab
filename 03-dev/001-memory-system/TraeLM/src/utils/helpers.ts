import { logger } from './logger';

// 延迟执行函数
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 重试函数
export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    delay?: number;
    backoff?: 'linear' | 'exponential';
    onRetry?: (attempt: number, error: Error) => void;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    delay: baseDelay = 1000,
    backoff = 'exponential',
    onRetry
  } = options;

  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (attempt === maxAttempts) {
        throw lastError;
      }

      if (onRetry) {
        onRetry(attempt, lastError);
      }

      const delayMs = backoff === 'exponential' 
        ? baseDelay * Math.pow(2, attempt - 1)
        : baseDelay * attempt;

      logger.debug('Retrying operation', { 
        attempt, 
        maxAttempts, 
        delayMs, 
        error: lastError.message 
      }, 'retry');

      await delay(delayMs);
    }
  }

  throw lastError!;
}

// 防抖函数
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number,
  immediate: boolean = false
): T & { cancel: () => void } {
  let timeout: NodeJS.Timeout | null = null;
  let result: ReturnType<T>;

  const debounced = function(this: any, ...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      if (!immediate) result = func.apply(this, args);
    };

    const callNow = immediate && !timeout;
    
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    
    if (callNow) result = func.apply(this, args);
    
    return result;
  } as T & { cancel: () => void };

  debounced.cancel = () => {
    if (timeout) {
      clearTimeout(timeout);
      timeout = null;
    }
  };

  return debounced;
}

// 节流函数
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): T & { cancel: () => void } {
  let inThrottle: boolean = false;
  let lastResult: ReturnType<T>;

  const throttled = function(this: any, ...args: Parameters<T>) {
    if (!inThrottle) {
      lastResult = func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
    return lastResult;
  } as T & { cancel: () => void };

  throttled.cancel = () => {
    inThrottle = false;
  };

  return throttled;
}

// 深拷贝函数
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as T;
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item)) as T;
  }

  if (typeof obj === 'object') {
    const cloned = {} as T;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        cloned[key] = deepClone(obj[key]);
      }
    }
    return cloned;
  }

  return obj;
}

// 深度合并对象
export function deepMerge<T extends Record<string, any>>(
  target: T,
  ...sources: Partial<T>[]
): T {
  if (!sources.length) return target;
  const source = sources.shift();

  if (isObject(target) && isObject(source)) {
    for (const key in source) {
      if (isObject(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} });
        deepMerge(target[key] as any, source[key] as any);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }

  return deepMerge(target, ...sources);
}

// 检查是否为对象
function isObject(item: any): item is Record<string, any> {
  return item && typeof item === 'object' && !Array.isArray(item);
}

// 生成唯一ID
export function generateId(prefix: string = '', length: number = 8): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  
  return prefix ? `${prefix}_${result}` : result;
}

// 生成UUID v4
export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// 格式化字节大小
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// 格式化持续时间
export function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else if (seconds > 0) {
    return `${seconds}s`;
  } else {
    return `${ms}ms`;
  }
}

// 计算相似度（余弦相似度）
export function cosineSimilarity(vecA: number[], vecB: number[]): number {
  if (vecA.length !== vecB.length) {
    throw new Error('Vectors must have the same length');
  }

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    const a = vecA[i]!;
    const b = vecB[i]!;
    dotProduct += a * b;
    normA += a * a;
    normB += b * b;
  }

  if (normA === 0 || normB === 0) {
    return 0;
  }

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

// 计算编辑距离（Levenshtein距离）
export function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = [];

  // 初始化矩阵
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }

  for (let j = 0; j <= str1.length; j++) {
    matrix[0]![j] = j;
  }

  // 填充矩阵
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i]![j] = matrix[i - 1]![j - 1]!;
      } else {
        matrix[i]![j] = Math.min(
          matrix[i - 1]![j - 1]! + 1, // 替换
          matrix[i]![j - 1]! + 1,     // 插入
          matrix[i - 1]![j]! + 1      // 删除
        );
      }
    }
  }

  return matrix[str2.length]![str1.length]!;
}

// 文本相似度（基于编辑距离）
export function textSimilarity(str1: string, str2: string): number {
  const maxLength = Math.max(str1.length, str2.length);
  if (maxLength === 0) return 1;
  
  const distance = levenshteinDistance(str1, str2);
  return 1 - (distance / maxLength);
}

// 数组去重
export function unique<T>(array: T[], keyFn?: (item: T) => any): T[] {
  if (!keyFn) {
    return [...Array.from(new Set(array))];
  }

  const seen = new Set();
  return array.filter(item => {
    const key = keyFn(item);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

// 数组分组
export function groupBy<T, K extends string | number | symbol>(
  array: T[],
  keyFn: (item: T) => K
): Record<K, T[]> {
  return array.reduce((groups, item) => {
    const key = keyFn(item);
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {} as Record<K, T[]>);
}

// 数组分块
export function chunk<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

// 随机选择数组元素
export function sample<T>(array: T[], count: number = 1): T[] {
  if (count >= array.length) {
    return [...array];
  }

  const result: T[] = [];
  const indices = new Set<number>();

  while (result.length < count) {
    const index = Math.floor(Math.random() * array.length);
    if (!indices.has(index)) {
      indices.add(index);
      const item = array[index];
      if (item !== undefined) {
        result.push(item);
      }
    }
  }

  return result;
}

// 洗牌算法
export function shuffle<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const temp = result[i]!;
    result[i] = result[j]!;
    result[j] = temp;
  }
  return result;
}

// 范围生成器
export function range(start: number, end?: number, step: number = 1): number[] {
  if (end === undefined) {
    end = start;
    start = 0;
  }

  const result: number[] = [];
  if (step > 0) {
    for (let i = start; i < end; i += step) {
      result.push(i);
    }
  } else if (step < 0) {
    for (let i = start; i > end; i += step) {
      result.push(i);
    }
  }

  return result;
}

// 安全的JSON解析
export function safeJsonParse<T = any>(
  str: string,
  defaultValue: T | null = null
): T | null {
  try {
    return JSON.parse(str);
  } catch {
    return defaultValue;
  }
}

// 安全的JSON字符串化
export function safeJsonStringify(
  obj: any,
  space?: number,
  replacer?: (key: string, value: any) => any
): string {
  try {
    return JSON.stringify(obj, replacer, space);
  } catch (error) {
    logger.warn('Failed to stringify object', { error }, 'safeJsonStringify');
    return '{}';
  }
}

// 类型守卫：检查是否为字符串
export function isString(value: any): value is string {
  return typeof value === 'string';
}

// 类型守卫：检查是否为数字
export function isNumber(value: any): value is number {
  return typeof value === 'number' && !isNaN(value);
}

// 类型守卫：检查是否为布尔值
export function isBoolean(value: any): value is boolean {
  return typeof value === 'boolean';
}

// 类型守卫：检查是否为数组
export function isArray<T = any>(value: any): value is T[] {
  return Array.isArray(value);
}

// 类型守卫：检查是否为函数
export function isFunction(value: any): value is Function {
  return typeof value === 'function';
}

// 类型守卫：检查是否为Promise
export function isPromise<T = any>(value: any): value is Promise<T> {
  return value && typeof value.then === 'function';
}

// 类型守卫：检查是否为空值
export function isEmpty(value: any): boolean {
  if (value == null) return true;
  if (isArray(value) || isString(value)) return value.length === 0;
  if (isObject(value)) return Object.keys(value).length === 0;
  return false;
}

// 环境变量获取
export function getEnv(key: string, defaultValue?: string): string | undefined {
  return process.env[key] || defaultValue;
}

// 环境变量获取（数字）
export function getEnvNumber(key: string, defaultValue?: number): number | undefined {
  const value = process.env[key];
  if (value === undefined) return defaultValue;
  
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? defaultValue : parsed;
}

// 环境变量获取（布尔值）
export function getEnvBoolean(key: string, defaultValue?: boolean): boolean | undefined {
  const value = process.env[key];
  if (value === undefined) return defaultValue;
  
  return value.toLowerCase() === 'true' || value === '1';
}

// 创建可取消的Promise
export function createCancellablePromise<T>(
  executor: (
    resolve: (value: T | PromiseLike<T>) => void,
    reject: (reason?: any) => void,
    isCancelled: () => boolean
  ) => void
): { promise: Promise<T>; cancel: () => void } {
  let cancelled = false;
  
  const promise = new Promise<T>((resolve, reject) => {
    executor(resolve, reject, () => cancelled);
  });
  
  return {
    promise,
    cancel: () => {
      cancelled = true;
    }
  };
}

// 超时Promise
export function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  timeoutMessage: string = 'Operation timed out'
): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs);
    })
  ]);
}

// 批处理函数
export async function batch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  batchSize: number = 10,
  delayMs: number = 0
): Promise<R[]> {
  const results: R[] = [];
  const chunks = chunk(items, batchSize);
  
  for (const chunk of chunks) {
    const chunkResults = await Promise.all(chunk.map(processor));
    results.push(...chunkResults);
    
    if (delayMs > 0 && chunk !== chunks[chunks.length - 1]) {
      await delay(delayMs);
    }
  }
  
  return results;
}

// 并发限制函数
export async function concurrentLimit<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  limit: number = 5
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  const executing: Promise<void>[] = [];
  
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item === undefined) continue;
    
    const promise = processor(item).then(result => {
      results[i] = result;
    });
    
    executing.push(promise);
    
    if (executing.length >= limit) {
      await Promise.race(executing);
      executing.splice(executing.findIndex(p => p === promise), 1);
    }
  }
  
  await Promise.all(executing);
  return results;
}