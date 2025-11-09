import { EventEmitter } from "events";
import type { Memory, MemoryContext } from "../../types/base";
import { MemoryType } from "../../types/base";
import { logger } from "../../utils/logger";

export interface MemoryManagerOptions {
  maxMemories?: number;
  enableAutoCleanup?: boolean;
  cleanupInterval?: number;
}

export class MemoryManager extends EventEmitter {
  private options: Required<MemoryManagerOptions>;
  private memories: Map<string, Memory> = new Map();
  private typeIndex: Map<string, Set<string>> = new Map();
  private tagIndex: Map<string, Set<string>> = new Map();
  private sessionIndex: Map<string, Set<string>> = new Map();
  private userIndex: Map<string, Set<string>> = new Map();
  private domainIndex: Map<string, Set<string>> = new Map();
  private cleanupTimer: NodeJS.Timeout | null = null;

  constructor(options: MemoryManagerOptions = {}) {
    super();
    this.options = {
      maxMemories: options.maxMemories ?? 10000,
      enableAutoCleanup: options.enableAutoCleanup ?? true,
      cleanupInterval: options.cleanupInterval ?? 60 * 60 * 1000,
    };
    if (this.options.enableAutoCleanup) {
      this.startCleanupTimer();
    }
  }

  private startCleanupTimer(): void {
    if (this.cleanupTimer) clearInterval(this.cleanupTimer);
    this.cleanupTimer = setInterval(() => {
      try { this.cleanupExpiredMemories(); } catch (error) { logger.warn("Memory cleanup failed", { error }); this.emit("error", error); }
    }, this.options.cleanupInterval);
  }

  public storeMemory(memory: Memory): boolean {
    try {
      if (!memory || !memory.id) return false;
      const now = new Date();
      memory.createdAt = memory.createdAt ?? now;
      memory.updatedAt = now;
      memory.accessCount = memory.accessCount ?? 0;
      if (this.memories.size >= this.options.maxMemories) {
        const oldest = Array.from(this.memories.values()).sort((a, b) => (a.createdAt?.getTime?.() ?? 0) - (b.createdAt?.getTime?.() ?? 0))[0];
        if (oldest) this.removeMemory(oldest.id);
      }
      this.memories.set(memory.id, memory);
      this.indexMemory(memory);
      this.emit("memoryStored", memory);
      return true;
    } catch (error) {
      logger.error("Failed to store memory", { error, memory });
      this.emit("error", error);
      return false;
    }
  }

  public async storeBatch(memories: Memory[]): Promise<Memory[]> {
    const stored: Memory[] = [];
    for (const mem of memories) { if (this.storeMemory(mem)) stored.push(mem); }
    return stored;
  }

  public updateMemory(id: string, patch: Partial<Memory>): boolean {
    const existing = this.memories.get(id);
    if (!existing) return false;
    const updated: Memory = { ...existing, ...patch, updatedAt: new Date() };
    this.deindexMemory(existing);
    this.memories.set(id, updated);
    this.indexMemory(updated);
    this.emit("memoryUpdated", updated);
    return true;
  }

  public removeMemory(id: string): boolean {
    const existing = this.memories.get(id);
    if (!existing) return false;
    this.deindexMemory(existing);
    const ok = this.memories.delete(id);
    if (ok) this.emit("memoryDeleted", id);
    return ok;
  }

  public getMemory(id: string): Memory | undefined { return this.memories.get(id); }

  public async getMemoriesByType(type: MemoryType | string): Promise<Memory[]> {
    const key = typeof type === "string" ? type : type;
    const ids = this.typeIndex.get(key) ?? new Set<string>();
    return Array.from(ids).map(id => this.memories.get(id)!).filter(Boolean);
  }

  public async getAllMemories(): Promise<Memory[]> { return Array.from(this.memories.values()); }

  public findSimilarMemories(target: Memory, limit: number = 10, threshold: number = 0.5): Memory[] {
    const scored: Array<{ m: Memory; s: number }> = [];
    for (const m of this.memories.values()) {
      if (m.id === target.id) continue;
      const s = this.calculateSimilarity(target, m);
      if (s >= threshold) scored.push({ m, s });
    }
    return scored.sort((a, b) => b.s - a.s).slice(0, limit).map(x => x.m);
  }

  public async finalizeConversation(conversationId: string): Promise<void> {
    try {
      const ids = this.sessionIndex.get(conversationId);
      if (!ids) return;
      for (const id of ids) { const mem = this.memories.get(id); if (!mem) continue; mem.updatedAt = new Date(); mem.accessCount = (mem.accessCount ?? 0) + 1; }
      this.emit("conversationFinalized", conversationId);
    } catch (error) { logger.error("Failed to finalize conversation", { conversationId, error }); this.emit("error", error); }
  }

  private cleanupExpiredMemories(): void {
    const now = Date.now();
    for (const mem of this.memories.values()) { const exp = mem.expiresAt?.getTime?.(); if (exp && exp < now) { this.removeMemory(mem.id); } }
  }

  private indexMemory(memory: Memory): void {
    const typeKey = memory.type ?? MemoryType.FACT;
    if (!this.typeIndex.has(typeKey)) this.typeIndex.set(typeKey, new Set());
    this.typeIndex.get(typeKey)!.add(memory.id);
    for (const t of (memory.tags ?? [])) { const key = t.toLowerCase(); if (!this.tagIndex.has(key)) this.tagIndex.set(key, new Set()); this.tagIndex.get(key)!.add(memory.id); }
    const ctx = memory.context as MemoryContext | undefined;
    if (ctx?.sessionId) { if (!this.sessionIndex.has(ctx.sessionId)) this.sessionIndex.set(ctx.sessionId, new Set()); this.sessionIndex.get(ctx.sessionId)!.add(memory.id); }
    if (ctx?.userId) { if (!this.userIndex.has(ctx.userId)) this.userIndex.set(ctx.userId, new Set()); this.userIndex.get(ctx.userId)!.add(memory.id); }
    if (ctx?.domain) { const d = ctx.domain.toLowerCase(); if (!this.domainIndex.has(d)) this.domainIndex.set(d, new Set()); this.domainIndex.get(d)!.add(memory.id); }
  }

  private deindexMemory(memory: Memory): void {
    const typeKey = memory.type ?? MemoryType.FACT; this.typeIndex.get(typeKey)?.delete(memory.id);
    for (const t of (memory.tags ?? [])) this.tagIndex.get(t.toLowerCase())?.delete(memory.id);
    const ctx = memory.context as MemoryContext | undefined;
    if (ctx?.sessionId) this.sessionIndex.get(ctx.sessionId)?.delete(memory.id);
    if (ctx?.userId) this.userIndex.get(ctx.userId)?.delete(memory.id);
    if (ctx?.domain) this.domainIndex.get(ctx.domain.toLowerCase())?.delete(memory.id);
  }

  private calculateSimilarity(a: Memory, b: Memory): number {
    const textSim = this.textSimilarity(String(a.content || ""), String(b.content || ""));
    const tagSim = this.tagSimilarity(a.tags || [], b.tags || []);
    const ctxSim = this.contextSimilarity(a.context as any, b.context as any);
    return 0.6 * textSim + 0.25 * tagSim + 0.15 * ctxSim;
  }

  private textSimilarity(t1: string, t2: string): number {
    const tokens1 = new Set(t1.toLowerCase().split(/\W+/).filter(Boolean));
    const tokens2 = new Set(t2.toLowerCase().split(/\W+/).filter(Boolean));
    const inter = new Set([...tokens1].filter(x => tokens2.has(x)));
    const union = new Set([...tokens1, ...tokens2]);
    return union.size === 0 ? 0 : inter.size / union.size;
  }

  private tagSimilarity(tags1: string[], tags2: string[]): number {
    if (tags1.length === 0 && tags2.length === 0) return 0;
    const set1 = new Set(tags1.map(t => t.toLowerCase()));
    const set2 = new Set(tags2.map(t => t.toLowerCase()));
    const inter = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([...set1, ...set2]);
    return union.size === 0 ? 0 : inter.size / union.size;
  }

  private contextSimilarity(c1?: MemoryContext, c2?: MemoryContext): number {
    if (!c1 || !c2) return 0;
    let score = 0;
    if (c1.userId && c2.userId && c1.userId === c2.userId) score += 0.4;
    if (c1.sessionId && c2.sessionId && c1.sessionId === c2.sessionId) score += 0.3;
    if (c1.domain && c2.domain && c1.domain.toLowerCase() === c2.domain.toLowerCase()) score += 0.2;
    if (c1.task && c2.task && c1.task === c2.task) score += 0.1;
    return Math.min(1, score);
  }

  public getStats() {
    return {
      totalMemories: this.memories.size,
      byType: Array.from(this.typeIndex.entries()).reduce((acc, [type, ids]) => { acc[type] = ids.size; return acc; }, {} as Record<string, number>),
      byTagCount: this.tagIndex.size,
      sessions: this.sessionIndex.size,
      users: this.userIndex.size,
      domains: this.domainIndex.size,
    };
  }

  public destroy(): void {
    if (this.cleanupTimer) clearInterval(this.cleanupTimer);
    this.memories.clear(); this.typeIndex.clear(); this.tagIndex.clear(); this.sessionIndex.clear(); this.userIndex.clear(); this.domainIndex.clear(); this.removeAllListeners();
  }
}
