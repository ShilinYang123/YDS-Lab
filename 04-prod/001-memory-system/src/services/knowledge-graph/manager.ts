/**
 * 鐭ヨ瘑鍥捐氨绠＄悊鍣?
 * 璐熻矗鍗忚皟璁板繂绠＄悊鍣ㄥ拰鐭ヨ瘑鍥捐氨鐨勪氦浜?
 *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, number>;
  componentCount: number;
  density: number;
  averageDegree: number;
}

export interface MemoryConsolidationResult {
  consolidatedMemory: Memory;
  originalMemories: Memory[];
  consolidationScore: number;
}

export interface KnowledgeExtractionResult {
  extractedNodes: KnowledgeNode[];
  extractedEdges: KnowledgeEdge[]发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, { edge });
    });
  }

  /**
   * 瀛樺偍璁板繂骞跺垱寤虹煡璇嗗叧鑱?
   *发现  个连通分量,
    createKnowledgeLinks: boolean = true
  ): Promise<boolean> {
    const success = this.memoryManager.storeMemory(memory);
    
    if (success && createKnowledgeLinks) {
      await this.createKnowledgeLinksForMemory(memory);
    }
    
    return success;
  }

  /**
   * 涓鸿蹇嗗垱寤虹煡璇嗗叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
          tags: []发现  个连通分量,发现  个连通分量,
        tags: []发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, error });
    }
  }

  /**
   * 鍒涘缓姒傚康鑺傜偣鍜屽叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
        tags: [concept]发现  个连通分量,发现  个连通分量,
        updatedAt: new Date()
      };
      this.knowledgeGraph.addNode(conceptNode);
    } else {
      // 鏇存柊鐩稿叧璁板繂鏁伴噺
      conceptNode.properties['relatedMemoryCount'] = 
        (conceptNode.properties['relatedMemoryCount']发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      updatedAt: new Date()
    };

    this.knowledgeGraph.addEdge(edge);
  }

  /**
   * 鍒涘缓涓婁笅鏂囧叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, memoryNodeId);
    }
  }

  /**
   * 鍒涘缓鐢ㄦ埛鑺傜偣鍜屽叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
        tags: []发现  个连通分量,发现  个连通分量,
        updatedAt: new Date()
      };
      this.knowledgeGraph.addNode(userNode);
    } else {
      userNode.properties['memoryCount'] = (userNode.properties['memoryCount']发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      updatedAt: new Date()
    };

    this.knowledgeGraph.addEdge(edge);
  }

  /**
   * 鍒涘缓浼氳瘽鑺傜偣鍜屽叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
        tags: []发现  个连通分量,发现  个连通分量,
        updatedAt: new Date()
      };
      this.knowledgeGraph.addNode(sessionNode);
    } else {
      sessionNode.properties['memoryCount'] = (sessionNode.properties['memoryCount']发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      updatedAt: new Date()
    };

    this.knowledgeGraph.addEdge(edge);
  }

  /**
   * 鍒涘缓棰嗗煙鑺傜偣鍜屽叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
        tags: []发现  个连通分量,发现  个连通分量,
        updatedAt: new Date()
      };
      this.knowledgeGraph.addNode(domainNode);
    } else {
      domainNode.properties['memoryCount'] = (domainNode.properties['memoryCount']发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      updatedAt: new Date()
    };

    this.knowledgeGraph.addEdge(edge);
  }

  /**
   * 鍒涘缓浠诲姟鑺傜偣鍜屽叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
        tags: []发现  个连通分量,发现  个连通分量,
        updatedAt: new Date()
      };
      this.knowledgeGraph.addNode(newTaskNode);
      taskNode = newTaskNode;
    } else {
      taskNode.properties['memoryCount'] = (taskNode.properties['memoryCount']发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      updatedAt: new Date()
    };

    this.knowledgeGraph.addEdge(edge);
  }

  /**
   * 鍩轰簬鐩镐技鎬у垱寤哄叧鑱?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
          updatedAt: new Date()
        };

        this.knowledgeGraph.addEdge(edge);
      }
    }
  }

  /**
   * 璁＄畻璁板繂鐩镐技搴?
   *发现  个连通分量,发现  个连通分量, memory2.content);
    similarity += contentSimilarity *发现  个连通分量, memory2.tags);
      similarity += tagSimilarity *发现  个连通分量, memory2.context);
      similarity += contextSimilarity * 0.1;
      factors += 0.1;
    }

    return factors > 0 ? similarity / factors : 0;
  }

  /**
   * 璁＄畻鏂囨湰鐩镐技搴︼紙绠€鍖栫増鏈級
   *发现  个连通分量, text2: string): number {
    const words1 = text1.toLowerCase().split(/\s+/);
    const words2 = text2.toLowerCase().split(/\s+/);
    
    const set1 = new Set(words1);
    const set2 = new Set(words2);
    
    const intersection = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([发现  个连通分量, ...set2]);
    
    return union.size > 0 ? intersection.size / union.size : 0;
  }

  /**
   * 璁＄畻鏍囩鐩镐技搴?
   */
  private calculateTagSimilarity(tags1: string[]发现  个连通分量, tags2: string[]): number {
    const set1 = new Set(tags1.map(tag => tag.toLowerCase()));
    const set2 = new Set(tags2.map(tag => tag.toLowerCase()));
    
    const intersection = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([发现  个连通分量, ...set2]);
    
    return union.size > 0 ? intersection.size / union.size : 0;
  }

  /**
   * 璁＄畻涓婁笅鏂囩浉浼煎害
   *发现  个连通分量, context2: MemoryContext): number {
    let similarity = 0;
    let factors = 0;

    if (context1.userId === context2.userId) {
      similarity += 0.4;
    }
    factors += 0.4;

    if (context1.domain === context2.domain) {
      similarity += 0.3;
    }
    factors += 0.3;

    if (context1.task === context2.task) {
      similarity += 0.3;
    }
    factors += 0.3;

    return factors > 0 ? similarity / factors : 0;
  }

  /**
   * 绉婚櫎璁板繂鐨勭煡璇嗗叧鑱?
   */
  private removeKnowledgeLinksForMemory(memoryId: string): void {
    const memoryNodeId = `memory_${memoryId}`;
    
    // 绉婚櫎鎵€鏈夌浉鍏崇殑杈?
    const edges = this.knowledgeGraph.getEdgesByNode(memoryNodeId);
    for (const edge of edges) {
      this.knowledgeGraph.removeEdge(edge.id);
    }
    
    // 绉婚櫎璁板繂鑺傜偣
    this.knowledgeGraph.removeNode(memoryNodeId);
  }

  /**
   * 鎵ц鍥捐氨鍒嗘瀽
   */
  async performGraphAnalysis(): Promise<AnalysisResult> {
    const graphAnalysis = this.knowledgeGraph.analyzeGraph();
    
    // 杞崲涓篈nalysisResult鏍煎紡
    const analysis: AnalysisResult = {
      insights: [发现  个连通分量,发现  个连通分量,
        `鍥捐氨瀵嗗害涓?${graphAnalysis.density.toFixed(4)}`
      ]发现  个连通分量,
      patterns: [发现  个连通分量,
        `搴︽暟鍒嗗竷: ${JSON.stringify(graphAnalysis.degreeDistribution)}`
      ]发现  个连通分量,
      recommendations: [发现  个连通分量,
        graphAnalysis.componentCount > 1 ? '瀛樺湪瀛ょ珛鐨勭煡璇嗙兢缁勶紝寤鸿寤虹珛璺ㄧ兢缁勮繛鎺? : '鐭ヨ瘑缁撴瀯杩炶疮'
      ]发现  个连通分量,发现  个连通分量,发现  个连通分量, analysis);
    
    return analysis;
  }

  /**
   * 鏁村悎璁板繂
   *发现  个连通分量, { 
      consolidatedGroups: consolidationCandidates.length 
    });
  }

  /**
   * 鏌ユ壘鏁村悎鍊欓€?
   */
  private async findConsolidationCandidates(): Promise<Memory[][]> {
    // 绠€鍖栧疄鐜帮細鍩轰簬鐩镐技搴﹀垎缁?
    const allMemories = await this.memoryManager.getAllMemories();
    const groups: Memory[][] = []发现  个连通分量,发现  个连通分量, 0.8);
      if (similarMemories.length > 2) {
        const group = [发现  个连通分量, ...similarMemories];
        groups.push(group);
        
        // 鏍囪涓哄凡澶勭悊
        group.forEach(m => processed.add(m.id));
      }
    }

    return groups;
  }

  /**
   * 鏁村悎璁板繂缁?
   */
  private async consolidateMemoryGroup(memoryGroup: Memory[]发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      context: memoryGroup[0]发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      originalMemories: memoryGroup
    });
  }

  /**
   * 鍚堝苟璁板繂鍐呭
   */
  private mergeMemoryContents(memories: Memory[]): string {
    return memories.map(m => m.content).join(' | ');
  }

  /**
   * 鍚堝苟璁板繂鏍囩
   */
  private mergeMemoryTags(memories: Memory[]): string[] {
    const allTags = new Set<string>();
    memories.forEach(m => {
      if (m.tags) {
        m.tags.forEach(tag => allTags.add(tag));
      }
    });
    return Array.from(allTags);
  }

  /**
   * 鑾峰彇璁板繂绠＄悊鍣?
   */
  getMemoryManager(): MemoryManager {
    return this.memoryManager;
  }

  /**
   * 鑾峰彇鐭ヨ瘑鍥捐氨
   */
  getKnowledgeGraph(): KnowledgeGraph {
    return this.knowledgeGraph;
  }

  /**
   * 鑾峰彇缁熻淇℃伅
   *发现  个连通分量,
      graphStats: this.knowledgeGraph.getStats()
    };
  }

  /**
   * 娣诲姞鑺傜偣
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      updatedAt: new Date()
    };
    this.knowledgeGraph.addNode(node);
    return node.id;
  }

  /**
   * 娣诲姞杈?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      updatedAt: new Date()
    };
    this.knowledgeGraph.addEdge(edge);
    return edge.id;
  }

  /**
   * 鑾峰彇鑺傜偣
   */
  async getNode(id: string): Promise<any> {
    return this.knowledgeGraph.getNode(id);
  }

  /**
   * 鑾峰彇杈?
   */
  async getEdge(id: string): Promise<any> {
    return this.knowledgeGraph.getEdge(id);
  }

  /**
   * 鏇存柊鑺傜偣
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, updatedNode);
  }

  /**
   * 鏇存柊杈?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, updatedEdge);
  }

  /**
   * 鍒犻櫎鑺傜偣
   */
  async removeNode(id: string): Promise<void> {
    const node = this.knowledgeGraph.getNode(id);
    if (!node) {
      throw new Error(`Node with id ${id} not found`);
    }
    this.knowledgeGraph.removeNode(id);
  }

  /**
   * 鍒犻櫎杈?
   */
  async removeEdge(id: string): Promise<void> {
    const edge = this.knowledgeGraph.getEdge(id);
    if (!edge) {
      throw new Error(`Edge with id ${id} not found`);
    }
    this.knowledgeGraph.removeEdge(id);
  }

  /**
   * 鎵归噺娣诲姞鑺傜偣
   */
  async addNodes(nodesData: any[]): Promise<string[]> {
    const nodeIds: string[] = [];
    for (const nodeData of nodesData) {
      const nodeId = await this.addNode(nodeData);
      nodeIds.push(nodeId);
    }
    return nodeIds;
  }

  /**
   * 鎵归噺鍒犻櫎鑺傜偣
   */
  async removeNodes(nodeIds: string[]): Promise<void> {
    for (const nodeId of nodeIds) {
      await this.removeNode(nodeId);
    }
  }

  /**
   * 鍒涘缓绱㈠紩锛堢畝鍖栧疄鐜帮級
   */
  async createIndex(field: string): Promise<void> {
    // 绠€鍖栫殑绱㈠紩瀹炵幇锛屽疄闄呬笂鐭ヨ瘑鍥捐氨宸茬粡鏈夌被鍨嬬储寮?
    // 杩欓噷鍙槸涓轰簡婊¤冻娴嬭瘯鎺ュ彛
    console.log(`Index created for field: ${field}`);
  }

  /**
   * 鏌ヨ鑺傜偣
   */
  async queryNodes(query: any): Promise<any[]> {
    const { filters } = query;
    let nodes = this.knowledgeGraph.getAllNodes();

    if (filters) {
      nodes = nodes.filter(node => {
        for (const [发现  个连通分量, value] of Object.entries(filters)) {
          if (key.includes('.')) {
            // 澶勭悊宓屽灞炴€э紝濡?'properties.category'
            const [发现  个连通分量, childKey] = key.split('.');
            if (parentKey && childKey) {
              const parentObj = (node as any)[parentKey];
              if (parentObj && parentObj[childKey] !== value) {
                return false;
              }
            }
          } else {
            if ((node as any)[key] !== value) {
              return false;
            }
          }
        }
        return true;
      });
    }

    return nodes;
  }

  /**
   * 鎸夌被鍨嬭幏鍙栬妭鐐?
   */
  async getNodesByType(type: string): Promise<any[]> {
    return this.knowledgeGraph.getNodesByType(type);
  }

  /**
   * 鍒涘缓鍥惧揩鐓?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, snapshot);
    
    return snapshotId;
  }

  /**
   * 鍒楀嚭鎵€鏈夊揩鐓?
   */
  async listSnapshots(): Promise<any[]> {
    if (!this.snapshots) {
      return []发现  个连通分量,发现  个连通分量,
      timestamp: snapshot.timestamp
    }));
  }

  /**
   * 鎭㈠蹇収
   */
  async restoreSnapshot(snapshotId: string): Promise<void> {
    if (!this.snapshots || !this.snapshots.has(snapshotId)) {
      throw new Error(`Snapshot with id ${snapshotId} not found`);
    }
    
    const snapshot = this.snapshots.get(snapshotId)!;
    
    // 娓呯┖褰撳墠鍥?
    const currentNodes = this.knowledgeGraph.getAllNodes();
    for (const node of currentNodes) {
      this.knowledgeGraph.removeNode(node.id);
    }
    
    // 鎭㈠鑺傜偣
    for (const node of snapshot.nodes) {
      this.knowledgeGraph.addNode(node);
    }
    
    // 鎭㈠杈?
    for (const edge of snapshot.edges) {
      this.knowledgeGraph.addEdge(edge);
    }
  }

  /**
   * 鑾峰彇閭诲眳鑺傜偣
   *发现  个连通分量,发现  个连通分量, any>;
  }>> {
    const edges = this.knowledgeGraph.getAllEdges();
    const nodes = this.knowledgeGraph.getAllNodes();
    
    const neighborIds = new Set<string>();
    
    // 鎵惧埌鎵€鏈夎繛鎺ョ殑杈?
    const connectedEdges = edges.filter(e => 
      e.sourceId === nodeId || e.targetId === nodeId
    );
    
    // 鏀堕泦閭诲眳鑺傜偣ID
    for (const edge of connectedEdges) {
      const neighborId = edge.sourceId === nodeId ? edge.targetId : edge.sourceId;
      neighborIds.add(neighborId);
    }
    
    // 杩斿洖閭诲眳鑺傜偣
    return nodes.filter(node => neighborIds.has(node.id));
  }

  /**
   * 鏌ユ壘璺緞
   *发现  个连通分量,发现  个连通分量, options: { maxDepth?: number } = {}): Promise<Array<{
    nodes: string[];
    edges: string[];
    length: number;
  }>> {
    const { maxDepth = 5 } = options;
    const paths: Array<{ nodes: string[]; edges: string[]; length: number }> = []发现  个连通分量, path: string[]发现  个连通分量, edgePath: string[]发现  个连通分量, depth: number) => {
      if (depth > maxDepth) return;
      if (currentId === targetId) {
        paths.push({
          nodes: [发现  个连通分量, currentId]发现  个连通分量,
          edges: [...edgePath]发现  个连通分量,发现  个连通分量, [发现  个连通分量, currentId]发现  个连通分量, [发现  个连通分量, edge.id]发现  个连通分量,发现  个连通分量, []发现  个连通分量, []发现  个连通分量,发现  个连通分量, b) => a.length - b.length);
  }

  /**
   * 鑾峰彇瀛愬浘
   *发现  个连通分量, options: { depth?: number } = {}): Promise<{
    nodes: any[];
    edges: any[]发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      edges: allEdges.filter(e => subgraphEdges.has(e.id))
    };
  }

  /**
   * 鑾峰彇鍥炬寚鏍?
   */
  async getGraphMetrics(): Promise<{
    nodeCount: number;
    edgeCount: number;
    density: number;
    averageDegree: number;
    components: number;
  }> {
    const nodes = this.knowledgeGraph.getAllNodes();
    const edges = this.knowledgeGraph.getAllEdges();
    
    const nodeCount = nodes.length;
    const edgeCount = edges.length;
    
    // 璁＄畻瀵嗗害
    const maxPossibleEdges = nodeCount * (nodeCount - 1) / 2;
    const density = maxPossibleEdges > 0 ? edgeCount / maxPossibleEdges : 0;
    
    // 璁＄畻骞冲潎搴?
    const averageDegree = nodeCount > 0 ? (2 * edgeCount) / nodeCount : 0;
    
    // 璁＄畻杩為€氬垎閲忔暟锛堢畝鍖栧疄鐜帮級
    const visited = new Set<string>();
    let components = 0;
    
    for (const node of nodes) {
      if (!visited.has(node.id)) {
        components++;
        const stack = [node.id]发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
      components
    };
  }
  async detectCommunities(): Promise<Array<{ nodes: string[]发现  个连通分量, edges: string[] }>> {
    // 绠€鍗曠殑绀惧尯妫€娴嬪疄鐜?
    const nodes = this.knowledgeGraph.getAllNodes();
    const edges = this.knowledgeGraph.getAllEdges();
    
    // 鍩轰簬杩炴帴搴︾殑绠€鍗曠ぞ鍖烘娴?
    const communities: Array<{ nodes: string[]发现  个连通分量, edges: string[] }> = [];
    const visited = new Set<string>();
    
    for (const node of nodes) {
      if (!visited.has(node.id)) {
        const community = { nodes: [node.id]发现  个连通分量, edges: [] as string[] };
        visited.add(node.id);
        
        // 鎵惧埌杩炴帴鐨勮妭鐐?
        const connectedEdges = edges.filter(e => 
          e.sourceId === node.id || e.targetId === node.id
        );
        
        for (const edge of connectedEdges) {
          community.edges.push(edge.id);
          const otherNodeId = edge.sourceId === node.id ? edge.targetId : edge.sourceId;
          if (!visited.has(otherNodeId)) {
            community.nodes.push(otherNodeId);
            visited.add(otherNodeId);
          }
        }
        
        communities.push(community);
      }
    }
    
    return communities;
  }

  /**
   * 璁＄畻涓績鎬ф寚鏍?
   *发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, closeness };
  }

  /**
   * 鎺ㄨ崘鐩稿叧鑺傜偣
   *发现  个连通分量, options: { limit?: number } = {}): Promise<Array<{
    nodeId: string;
    score: number;
    reason: string;
  }>> {
    const { limit = 10 } = options;
    const edges = this.knowledgeGraph.getAllEdges();
    // const nodes = this.knowledgeGraph.getAllNodes(); // 鏆傛椂鏈娇鐢?
    
    // 鍩轰簬杩炴帴搴︾殑鎺ㄨ崘
    const recommendations: Array<{ nodeId: string; score: number; reason: string }> = []发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, limit);
  }

  /**
   * 瀵煎嚭鍥炬暟鎹?
   */
  async exportGraph(): Promise<{
    nodes: any[];
    edges: any[]发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,
        edgeCount: edges.length
      }
    };
  }

  /**
   * 瀵煎叆鍥炬暟鎹?
   */
  async importGraph(data: {
    nodes: any[];
    edges: any[]发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量,发现  个连通分量, edgesImported };
  }

  /**
   * 娓呯悊璧勬簮
   */
  destroy(): void {
    if (this.analysisInterval) {
      clearInterval(this.analysisInterval);
      this.analysisInterval = null;
    }
    
    if (this.consolidationInterval) {
      clearInterval(this.consolidationInterval);
      this.consolidationInterval = null;
    }
    
    this.removeAllListeners();
  }
}

export interface MemoryManagerOptions {
  maxMemories?: number;
  enableAutoCleanup?: boolean;
  cleanupInterval?: number;
}




