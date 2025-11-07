/**
 * 知识图谱核心类
 * 实现节点和边的管理、查询和操作
 */

import { EventEmitter } from 'events';
import { KnowledgeNode, KnowledgeEdge } from '../../types/base';

export class KnowledgeGraph extends EventEmitter {
  private nodes: Map<string, KnowledgeNode> = new Map();
  private edges: Map<string, KnowledgeEdge> = new Map();
  private nodesByType: Map<string, Set<string>> = new Map();
  private edgesByType: Map<string, Set<string>> = new Map();
  private adjacencyList: Map<string, Set<string>> = new Map();
  private reverseAdjacencyList: Map<string, Set<string>> = new Map();
  private maxNodes: number;
  private maxEdges: number;

  constructor(options: KnowledgeGraphOptions = {}) {
    super();
    this.maxNodes = options.maxNodes || 10000;
    this.maxEdges = options.maxEdges || 50000;
  }

  /**
   * 添加节点
   */
  addNode(node: KnowledgeNode): boolean {
    if (this.nodes.size >= this.maxNodes) {
      this.emit('capacityWarning', { type: 'nodes', current: this.nodes.size, max: this.maxNodes });
      return false;
    }

    if (this.nodes.has(node.id)) {
      return false;
    }

    // 设置创建时间
    if (!node.createdAt) {
      node.createdAt = new Date();
    }
    node.updatedAt = new Date();

    this.nodes.set(node.id, node);

    // 更新类型索引
    if (!this.nodesByType.has(node.type)) {
      this.nodesByType.set(node.type, new Set());
    }
    this.nodesByType.get(node.type)!.add(node.id);

    // 初始化邻接表
    if (!this.adjacencyList.has(node.id)) {
      this.adjacencyList.set(node.id, new Set());
    }
    if (!this.reverseAdjacencyList.has(node.id)) {
      this.reverseAdjacencyList.set(node.id, new Set());
    }

    this.emit('nodeAdded', node);
    return true;
  }

  /**
   * 更新节点
   */
  updateNode(nodeId: string, updates: Partial<KnowledgeNode>): boolean {
    const node = this.nodes.get(nodeId);
    if (!node) {
      return false;
    }

    const oldType = node.type;
    const updatedNode = { ...node, ...updates, updatedAt: new Date() };

    // 如果类型发生变化，更新类型索引
    if (updates.type && updates.type !== oldType) {
      this.nodesByType.get(oldType)?.delete(nodeId);
      if (!this.nodesByType.has(updates.type)) {
        this.nodesByType.set(updates.type, new Set());
      }
      this.nodesByType.get(updates.type)!.add(nodeId);
    }

    this.nodes.set(nodeId, updatedNode);
    this.emit('nodeUpdated', { old: node, new: updatedNode });
    return true;
  }

  /**
   * 删除节点
   */
  removeNode(nodeId: string): boolean {
    const node = this.nodes.get(nodeId);
    if (!node) {
      return false;
    }

    // 删除所有相关的边
    const relatedEdges = this.getNodeEdges(nodeId);
    for (const edge of relatedEdges) {
      this.removeEdge(edge.id);
    }

    // 从类型索引中删除
    this.nodesByType.get(node.type)?.delete(nodeId);

    // 从邻接表中删除
    this.adjacencyList.delete(nodeId);
    this.reverseAdjacencyList.delete(nodeId);

    // 从其他节点的邻接表中删除引用
    for (const adjacentSet of Array.from(this.adjacencyList.values())) {
      adjacentSet.delete(nodeId);
    }
    for (const reverseAdjacentSet of Array.from(this.reverseAdjacencyList.values())) {
      reverseAdjacentSet.delete(nodeId);
    }

    this.nodes.delete(nodeId);
    this.emit('nodeRemoved', node);
    return true;
  }

  /**
   * 获取节点
   */
  getNode(nodeId: string): KnowledgeNode | undefined {
    return this.nodes.get(nodeId);
  }

  /**
   * 获取所有节点
   */
  getAllNodes(): KnowledgeNode[] {
    return Array.from(this.nodes.values());
  }

  /**
   * 根据类型获取节点
   */
  getNodesByType(type: string): KnowledgeNode[] {
    const nodeIds = this.nodesByType.get(type);
    if (!nodeIds) {
      return [];
    }

    return Array.from(nodeIds)
      .map(id => this.nodes.get(id))
      .filter((node): node is KnowledgeNode => node !== undefined);
  }

  /**
   * 搜索节点
   */
  searchNodes(query: NodeSearchQuery): KnowledgeNode[] {
    let results = Array.from(this.nodes.values());

    // 按类型过滤
    if (query.type) {
      results = results.filter(node => node.type === query.type);
    }

    // 按标签过滤
    if (query.tags && query.tags.length > 0) {
      results = results.filter(node => 
        query.tags!.some(tag => node.tags?.includes(tag))
      );
    }

    // 按属性过滤
    if (query.properties) {
      results = results.filter(node => {
        for (const [key, value] of Object.entries(query.properties!)) {
          if (node.properties[key] !== value) {
            return false;
          }
        }
        return true;
      });
    }

    // 文本搜索
    if (query.text) {
      const searchText = query.text.toLowerCase();
      results = results.filter(node => 
        node.label.toLowerCase().includes(searchText) ||
        (node.description && node.description.toLowerCase().includes(searchText)) ||
        (node.content && node.content.toLowerCase().includes(searchText)) ||
        (node.tags && node.tags.some(tag => tag.toLowerCase().includes(searchText))) ||
        Object.values(node.properties).some(value => 
          String(value).toLowerCase().includes(searchText)
        )
      );
    }

    // 按时间范围过滤
    if (query.createdAfter) {
      results = results.filter(node => node.createdAt >= query.createdAfter!);
    }
    if (query.createdBefore) {
      results = results.filter(node => node.createdAt <= query.createdBefore!);
    }

    // 排序
    if (query.sortBy) {
      results.sort((a, b) => {
        let aValue: any, bValue: any;
        
        switch (query.sortBy) {
          case 'createdAt':
            aValue = a.createdAt.getTime();
            bValue = b.createdAt.getTime();
            break;
          case 'updatedAt':
            aValue = a.updatedAt?.getTime() || 0;
            bValue = b.updatedAt?.getTime() || 0;
            break;
          case 'label':
            aValue = a.label;
            bValue = b.label;
            break;
          default:
            aValue = a.properties?.[query.sortBy as string] || '';
            bValue = b.properties?.[query.sortBy as string] || '';
        }

        if (query.sortOrder === 'desc') {
          return bValue > aValue ? 1 : bValue < aValue ? -1 : 0;
        } else {
          return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
        }
      });
    }

    // 限制结果数量
    if (query.limit) {
      results = results.slice(0, query.limit);
    }

    return results;
  }

  /**
   * 添加边
   */
  addEdge(edge: KnowledgeEdge): boolean {
    if (this.edges.size >= this.maxEdges) {
      this.emit('capacityWarning', { type: 'edges', current: this.edges.size, max: this.maxEdges });
      return false;
    }

    if (this.edges.has(edge.id)) {
      return false;
    }

    // 检查源节点和目标节点是否存在
    if (!this.nodes.has(edge.sourceId) || !this.nodes.has(edge.targetId)) {
      return false;
    }

    // 设置创建时间
    if (!edge.createdAt) {
      edge.createdAt = new Date();
    }
    edge.updatedAt = new Date();

    this.edges.set(edge.id, edge);

    // 更新类型索引
    if (edge.type) {
      if (!this.edgesByType.has(edge.type)) {
        this.edgesByType.set(edge.type, new Set());
      }
      this.edgesByType.get(edge.type)!.add(edge.id);
    }

    // 更新邻接表
    this.adjacencyList.get(edge.sourceId)!.add(edge.targetId);
    this.reverseAdjacencyList.get(edge.targetId)!.add(edge.sourceId);

    this.emit('edgeAdded', edge);
    return true;
  }

  /**
   * 更新边
   */
  updateEdge(edgeId: string, updates: Partial<KnowledgeEdge>): boolean {
    const edge = this.edges.get(edgeId);
    if (!edge) {
      return false;
    }

    const oldType = edge.type;
    const updatedEdge = { ...edge, ...updates, updatedAt: new Date() };

    // 如果类型发生变化，更新类型索引
    if (updates.type && updates.type !== oldType) {
      if (oldType) {
        this.edgesByType.get(oldType)?.delete(edgeId);
      }
      if (!this.edgesByType.has(updates.type)) {
        this.edgesByType.set(updates.type, new Set());
      }
      this.edgesByType.get(updates.type)!.add(edgeId);
    }

    this.edges.set(edgeId, updatedEdge);
    this.emit('edgeUpdated', { old: edge, new: updatedEdge });
    return true;
  }

  /**
   * 删除边
   */
  removeEdge(edgeId: string): boolean {
    const edge = this.edges.get(edgeId);
    if (!edge) {
      return false;
    }

    // 从类型索引中删除
    if (edge.type) {
      this.edgesByType.get(edge.type)?.delete(edgeId);
    }

    // 从邻接表中删除
    this.adjacencyList.get(edge.sourceId)?.delete(edge.targetId);
    this.reverseAdjacencyList.get(edge.targetId)?.delete(edge.sourceId);

    this.edges.delete(edgeId);
    this.emit('edgeRemoved', edge);
    return true;
  }

  /**
   * 获取边
   */
  getEdge(edgeId: string): KnowledgeEdge | undefined {
    return this.edges.get(edgeId);
  }

  /**
   * 获取所有边
   */
  getAllEdges(): KnowledgeEdge[] {
    return Array.from(this.edges.values());
  }

  /**
   * 根据类型获取边
   */
  getEdgesByType(type: string): KnowledgeEdge[] {
    const edgeIds = this.edgesByType.get(type);
    if (!edgeIds) {
      return [];
    }

    return Array.from(edgeIds)
      .map(id => this.edges.get(id))
      .filter((edge): edge is KnowledgeEdge => edge !== undefined);
  }

  /**
   * 获取节点的所有边
   */
  getNodeEdges(nodeId: string): KnowledgeEdge[] {
    const edges: KnowledgeEdge[] = [];

    for (const edge of Array.from(this.edges.values())) {
      if (edge.sourceId === nodeId || edge.targetId === nodeId) {
        edges.push(edge);
      }
    }

    return edges;
  }

  /**
   * 获取节点的出边
   */
  getOutgoingEdges(nodeId: string): KnowledgeEdge[] {
    const edges: KnowledgeEdge[] = [];

    for (const edge of Array.from(this.edges.values())) {
      if (edge.sourceId === nodeId) {
        edges.push(edge);
      }
    }

    return edges;
  }

  /**
   * 获取节点的入边
   */
  getIncomingEdges(nodeId: string): KnowledgeEdge[] {
    const edges: KnowledgeEdge[] = [];

    for (const edge of Array.from(this.edges.values())) {
      if (edge.targetId === nodeId) {
        edges.push(edge);
      }
    }

    return edges;
  }

  /**
   * 获取节点的邻居
   */
  getNeighbors(nodeId: string): KnowledgeNode[] {
    const neighbors: KnowledgeNode[] = [];
    const adjacentIds = this.adjacencyList.get(nodeId);
    const reverseAdjacentIds = this.reverseAdjacencyList.get(nodeId);

    if (adjacentIds) {
      for (const id of Array.from(adjacentIds)) {
        const node = this.nodes.get(id);
        if (node) {
          neighbors.push(node);
        }
      }
    }

    if (reverseAdjacentIds) {
      for (const id of Array.from(reverseAdjacentIds)) {
        const node = this.nodes.get(id);
        if (node && !neighbors.find(n => n.id === id)) {
          neighbors.push(node);
        }
      }
    }

    return neighbors;
  }

  /**
   * 查找两个节点之间的路径
   */
  findPath(sourceId: string, targetId: string, maxDepth: number = 5): KnowledgeNode[] | null {
    if (!this.nodes.has(sourceId) || !this.nodes.has(targetId)) {
      return null;
    }

    if (sourceId === targetId) {
      return [this.nodes.get(sourceId)!];
    }

    const visited = new Set<string>();
    const queue: { nodeId: string; path: string[] }[] = [{ nodeId: sourceId, path: [sourceId] }];

    while (queue.length > 0) {
      const { nodeId, path } = queue.shift()!;

      if (path.length > maxDepth) {
        continue;
      }

      if (visited.has(nodeId)) {
        continue;
      }

      visited.add(nodeId);

      const adjacentIds = this.adjacencyList.get(nodeId);
      if (adjacentIds) {
        for (const adjacentId of Array.from(adjacentIds)) {
          if (adjacentId === targetId) {
            const fullPath = [...path, adjacentId];
            return fullPath.map(id => this.nodes.get(id)!);
          }

          if (!visited.has(adjacentId)) {
            queue.push({ nodeId: adjacentId, path: [...path, adjacentId] });
          }
        }
      }
    }

    return null;
  }

  /**
   * 获取子图
   */
  getSubgraph(nodeIds: string[]): { nodes: KnowledgeNode[]; edges: KnowledgeEdge[] } {
    const nodeIdSet = new Set(nodeIds);
    const nodes: KnowledgeNode[] = [];
    const edges: KnowledgeEdge[] = [];

    // 获取节点
    for (const nodeId of nodeIds) {
      const node = this.nodes.get(nodeId);
      if (node) {
        nodes.push(node);
      }
    }

    // 获取节点之间的边
    for (const edge of Array.from(this.edges.values())) {
      if (nodeIdSet.has(edge.sourceId) && nodeIdSet.has(edge.targetId)) {
        edges.push(edge);
      }
    }

    return { nodes, edges };
  }

  /**
   * 获取图统计信息
   */
  getStats(): KnowledgeGraphStats {
    const nodeTypeStats: Record<string, number> = {};
    const edgeTypeStats: Record<string, number> = {};

    for (const [type, nodeIds] of Array.from(this.nodesByType)) {
      nodeTypeStats[type] = nodeIds.size;
    }

    for (const [type, edgeIds] of Array.from(this.edgesByType)) {
      edgeTypeStats[type] = edgeIds.size;
    }

    return {
      totalNodes: this.nodes.size,
      totalEdges: this.edges.size,
      nodeTypeStats,
      edgeTypeStats,
      maxNodes: this.maxNodes,
      maxEdges: this.maxEdges,
      memoryUsage: this.estimateMemoryUsage()
    };
  }

  /**
   * 估算内存使用量
   */
  private estimateMemoryUsage(): number {
    // 简单的内存使用量估算
    let size = 0;
    
    for (const node of Array.from(this.nodes.values())) {
      size += JSON.stringify(node).length;
    }
    
    for (const edge of Array.from(this.edges.values())) {
      size += JSON.stringify(edge).length;
    }

    return size;
  }

  /**
   * 清空图
   */
  clear(): void {
    this.nodes.clear();
    this.edges.clear();
    this.nodesByType.clear();
    this.edgesByType.clear();
    this.adjacencyList.clear();
    this.reverseAdjacencyList.clear();
    this.emit('graphCleared');
  }

  /**
   * 导出图数据
   */
  export(): GraphExportData {
    return {
      nodes: Array.from(this.nodes.values()).map(node => ({
        ...node,
        createdAt: node.createdAt.toISOString(),
        updatedAt: node.updatedAt?.toISOString() || new Date().toISOString()
      })),
      edges: Array.from(this.edges.values()).map(edge => ({
        ...edge,
        createdAt: edge.createdAt.toISOString(),
        updatedAt: edge.updatedAt.toISOString()
      })),
      stats: this.getStats(),
      exportedAt: new Date().toISOString(),
      version: '1.0.0'
    };
  }

  /**
   * 导入图数据
   */
  import(data: GraphExportData): void {
    this.clear();

    // 导入节点
    for (const nodeData of data.nodes) {
      const node: KnowledgeNode = {
        ...nodeData,
        createdAt: new Date(nodeData.createdAt),
        updatedAt: new Date(nodeData.updatedAt)
      };
      this.addNode(node);
    }

    // 导入边
    for (const edgeData of data.edges) {
      const edge: KnowledgeEdge = {
        ...edgeData,
        createdAt: new Date(edgeData.createdAt),
        updatedAt: new Date(edgeData.updatedAt)
      };
      this.addEdge(edge);
    }

    this.emit('graphImported', { nodeCount: data.nodes.length, edgeCount: data.edges.length });
  }

  /**
   * 根据节点获取相关边
   */
  getEdgesByNode(nodeId: string): KnowledgeEdge[] {
    const edges: KnowledgeEdge[] = [];
    
    for (const edge of Array.from(this.edges.values())) {
      if (edge.sourceId === nodeId || edge.targetId === nodeId) {
        edges.push(edge);
      }
    }
    
    return edges;
  }

  /**
   * 分析图谱结构
   */
  analyzeGraph(): GraphAnalysisResult {
    const nodeCount = this.nodes.size;
    const edgeCount = this.edges.size;
    
    // 计算节点度数分布
    const degreeDistribution: Record<number, number> = {};
    for (const nodeId of this.nodes.keys()) {
      const degree = this.getEdgesByNode(nodeId).length;
      degreeDistribution[degree] = (degreeDistribution[degree] || 0) + 1;
    }
    
    // 计算连通组件数量
    const visited = new Set<string>();
    let componentCount = 0;
    
    for (const nodeId of this.nodes.keys()) {
      if (!visited.has(nodeId)) {
        componentCount++;
        this.dfsVisit(nodeId, visited);
      }
    }
    
    return {
      nodeCount,
      edgeCount,
      degreeDistribution,
      componentCount,
      density: nodeCount > 1 ? (2 * edgeCount) / (nodeCount * (nodeCount - 1)) : 0,
      averageDegree: nodeCount > 0 ? (2 * edgeCount) / nodeCount : 0
    };
  }

  /**
   * 深度优先搜索访问节点
   */
  private dfsVisit(nodeId: string, visited: Set<string>): void {
    visited.add(nodeId);
    
    const adjacentIds = this.adjacencyList.get(nodeId);
    if (adjacentIds) {
      for (const adjacentId of adjacentIds) {
        if (!visited.has(adjacentId)) {
          this.dfsVisit(adjacentId, visited);
        }
      }
    }
  }
}

// 接口定义
export interface KnowledgeGraphOptions {
  maxNodes?: number;
  maxEdges?: number;
}

export interface NodeSearchQuery {
  type?: string;
  tags?: string[];
  properties?: Record<string, any>;
  text?: string;
  createdAfter?: Date;
  createdBefore?: Date;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
}

export interface KnowledgeGraphStats {
  totalNodes: number;
  totalEdges: number;
  nodeTypeStats: Record<string, number>;
  edgeTypeStats: Record<string, number>;
  maxNodes: number;
  maxEdges: number;
  memoryUsage: number;
}

export interface GraphExportData {
  nodes: any[];
  edges: any[];
  stats: KnowledgeGraphStats;
  exportedAt: string;
  version: string;
}

export interface GraphAnalysisResult {
  nodeCount: number;
  edgeCount: number;
  degreeDistribution: Record<number, number>;
  componentCount: number;
  density: number;
  averageDegree: number;
}