/**
 * JS003-Trae长记忆功能 - 源码复制方式使用示例
 * 
 * 本文件展示了在源码复制方式下如何使用长记忆功能
 * 包括基本使用、高级集成和实际应用场景
 */

// ============================================================================
// 1. 基本导入和初始化
// ============================================================================

import { LongTermMemorySystem } from './memory-system';
import type { 
  Memory, 
  RetrievalQuery, 
  Rule, 
  KnowledgeGraphEntity,
  PerformanceMetrics 
} from './memory-system/types';

// 基本使用示例
export class BasicMemoryExample {
  private memorySystem: LongTermMemorySystem;

  constructor() {
    // 使用默认配置初始化
    this.memorySystem = new LongTermMemorySystem();
  }

  async initialize() {
    try {
      await this.memorySystem.initialize();
      console.log('✅ 长记忆系统初始化成功');
    } catch (error) {
      console.error('❌ 初始化失败:', error);
      throw error;
    }
  }

  // 存储记忆
  async storeBasicMemory() {
    const memory: Partial<Memory> = {
      content: '用户偏好使用深色主题，喜欢简洁的界面设计',
      type: 'user_preference',
      tags: ['ui', 'theme', 'preference'],
      metadata: {
        userId: 'user_001',
        category: 'interface',
        importance: 'high',
        timestamp: new Date().toISOString()
      }
    };

    const memoryId = await this.memorySystem.storeMemory(memory);
    console.log(`✅ 记忆已存储，ID: ${memoryId}`);
    return memoryId;
  }

  // 检索记忆
  async retrieveMemories() {
    const query: RetrievalQuery = {
      query: '用户界面偏好',
      tags: ['ui', 'preference'],
      limit: 5,
      threshold: 0.7
    };

    const memories = await this.memorySystem.retrieveMemories(query);
    console.log(`🔍 找到 ${memories.length} 条相关记忆`);
    return memories;
  }
}

// ============================================================================
// 2. 高级集成示例 - 应用服务层
// ============================================================================

export class AppMemoryService {
  private memorySystem: LongTermMemorySystem;
  private initialized = false;

  constructor(customConfig?: any) {
    // 支持自定义配置
    this.memorySystem = new LongTermMemorySystem(customConfig);
  }

  async initialize() {
    if (!this.initialized) {
      await this.memorySystem.initialize();
      this.initialized = true;
      console.log('🚀 应用记忆服务启动完成');
    }
  }

  // 用户行为记录
  async recordUserAction(userId: string, action: string, context?: any) {
    await this.ensureInitialized();

    const memory: Partial<Memory> = {
      content: `用户 ${userId} 执行了操作: ${action}`,
      type: 'user_action',
      tags: ['user', 'action', userId, action],
      metadata: {
        userId,
        action,
        context,
        timestamp: new Date().toISOString(),
        source: 'user_interaction',
        sessionId: this.generateSessionId()
      }
    };

    return await this.memorySystem.storeMemory(memory);
  }

  // 智能推荐
  async getPersonalizedRecommendations(userId: string, category?: string) {
    await this.ensureInitialized();

    // 获取用户历史行为
    const userMemories = await this.memorySystem.retrieveMemories({
      query: `用户 ${userId} 的行为和偏好`,
      tags: [userId],
      limit: 20,
      threshold: 0.6
    });

    // 获取增强上下文
    const enhancementContext = await this.memorySystem.getEnhancementContext({
      query: `为用户 ${userId} 生成个性化推荐`,
      includeRules: true,
      includeMemories: true,
      maxMemories: 10
    });

    // 分析用户偏好
    const preferences = this.analyzeUserPreferences(userMemories);
    
    return {
      userId,
      category,
      recommendations: this.generateRecommendations(preferences, enhancementContext),
      basedOnMemories: userMemories.length,
      confidence: this.calculateConfidence(userMemories)
    };
  }

  // 上下文感知对话
  async getConversationContext(userId: string, currentMessage: string) {
    await this.ensureInitialized();

    // 获取相关对话历史
    const conversationHistory = await this.memorySystem.retrieveMemories({
      query: currentMessage,
      tags: [userId, 'conversation'],
      limit: 5,
      threshold: 0.7
    });

    // 获取用户偏好和规则
    const enhancementContext = await this.memorySystem.getEnhancementContext({
      query: `用户 ${userId} 的对话上下文和偏好`,
      includeRules: true,
      includeMemories: true,
      maxMemories: 3
    });

    return {
      currentMessage,
      relevantHistory: conversationHistory,
      userPreferences: enhancementContext.rules?.personal || [],
      projectContext: enhancementContext.rules?.project || [],
      suggestedResponse: this.generateContextualResponse(
        currentMessage, 
        conversationHistory, 
        enhancementContext
      )
    };
  }

  // 性能监控
  async getPerformanceMetrics(): Promise<PerformanceMetrics> {
    await this.ensureInitialized();
    return await this.memorySystem.getPerformanceMetrics();
  }

  // 私有辅助方法
  private async ensureInitialized() {
    if (!this.initialized) {
      await this.initialize();
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private analyzeUserPreferences(memories: Memory[]) {
    const preferences: Record<string, number> = {};
    
    memories.forEach(memory => {
      memory.tags.forEach(tag => {
        preferences[tag] = (preferences[tag] || 0) + 1;
      });
    });

    return Object.entries(preferences)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([tag, count]) => ({ tag, frequency: count }));
  }

  private generateRecommendations(preferences: any[], context: any) {
    return preferences.map(pref => ({
      type: 'preference_based',
      content: `基于您对 ${pref.tag} 的偏好推荐`,
      confidence: Math.min(pref.frequency / 10, 1),
      source: 'user_behavior_analysis'
    }));
  }

  private calculateConfidence(memories: Memory[]): number {
    if (memories.length === 0) return 0;
    return Math.min(memories.length / 20, 1);
  }

  private generateContextualResponse(message: string, history: Memory[], context: any) {
    return {
      suggestedTone: this.inferToneFromHistory(history),
      relevantTopics: this.extractTopicsFromHistory(history),
      personalizedElements: context.rules?.personal?.slice(0, 3) || []
    };
  }

  private inferToneFromHistory(history: Memory[]): string {
    // 简单的语调推断逻辑
    const formalKeywords = ['请', '您', '谢谢', '麻烦'];
    const casualKeywords = ['嗯', '哈哈', '好的', '行'];
    
    let formalCount = 0;
    let casualCount = 0;

    history.forEach(memory => {
      formalKeywords.forEach(keyword => {
        if (memory.content.includes(keyword)) formalCount++;
      });
      casualKeywords.forEach(keyword => {
        if (memory.content.includes(keyword)) casualCount++;
      });
    });

    return formalCount > casualCount ? 'formal' : 'casual';
  }

  private extractTopicsFromHistory(history: Memory[]): string[] {
    const topics = new Set<string>();
    history.forEach(memory => {
      memory.tags.forEach(tag => {
        if (!['user', 'conversation'].includes(tag)) {
          topics.add(tag);
        }
      });
    });
    return Array.from(topics).slice(0, 5);
  }
}

// ============================================================================
// 3. Web应用集成示例 (Express.js)
// ============================================================================

export class WebAppMemoryIntegration {
  private memoryService: AppMemoryService;

  constructor() {
    // 自定义配置适合Web应用
    const webConfig = {
      memory: {
        maxMemories: 10000,
        defaultThreshold: 0.75
      },
      performance: {
        enableMonitoring: true,
        logLevel: 'info'
      },
      rules: {
        personalRulesPath: './config/web-personal-rules.yaml',
        projectRulesPath: './config/web-project-rules.yaml'
      }
    };

    this.memoryService = new AppMemoryService(webConfig);
  }

  async initialize() {
    await this.memoryService.initialize();
    console.log('🌐 Web应用记忆系统初始化完成');
  }

  // 用户登录处理
  async handleUserLogin(req: any, res: any) {
    const { userId, loginInfo } = req.body;

    try {
      // 记录登录行为
      await this.memoryService.recordUserAction(userId, 'login', {
        timestamp: new Date(),
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        device: loginInfo.device
      });

      // 获取个性化推荐
      const recommendations = await this.memoryService.getPersonalizedRecommendations(
        userId, 
        'dashboard'
      );

      res.json({
        success: true,
        message: '登录成功',
        userId,
        personalizedContent: recommendations,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('登录处理错误:', error);
      res.status(500).json({ error: '服务器内部错误' });
    }
  }

  // 聊天消息处理
  async handleChatMessage(req: any, res: any) {
    const { userId, message } = req.body;

    try {
      // 记录对话
      await this.memoryService.recordUserAction(userId, 'send_message', {
        message,
        timestamp: new Date(),
        messageLength: message.length
      });

      // 获取对话上下文
      const context = await this.memoryService.getConversationContext(userId, message);

      // 存储对话记忆
      await this.memoryService.recordUserAction(userId, 'conversation', {
        content: message,
        type: 'user_message',
        tags: ['conversation', userId, 'chat'],
        metadata: {
          messageId: this.generateMessageId(),
          conversationId: req.body.conversationId,
          timestamp: new Date().toISOString()
        }
      });

      res.json({
        success: true,
        context,
        suggestions: context.suggestedResponse,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('消息处理错误:', error);
      res.status(500).json({ error: '消息处理失败' });
    }
  }

  // 用户偏好设置
  async updateUserPreferences(req: any, res: any) {
    const { userId, preferences } = req.body;

    try {
      // 记录偏好更新
      await this.memoryService.recordUserAction(userId, 'update_preferences', {
        preferences,
        timestamp: new Date(),
        source: 'settings_page'
      });

      // 存储偏好记忆
      for (const [key, value] of Object.entries(preferences)) {
        await this.memoryService.recordUserAction(userId, 'preference_setting', {
          content: `用户设置 ${key} 为 ${value}`,
          type: 'user_preference',
          tags: ['preference', userId, key],
          metadata: {
            preferenceKey: key,
            preferenceValue: value,
            timestamp: new Date().toISOString()
          }
        });
      }

      res.json({
        success: true,
        message: '偏好设置已更新',
        updatedPreferences: Object.keys(preferences).length
      });

    } catch (error) {
      console.error('偏好更新错误:', error);
      res.status(500).json({ error: '偏好更新失败' });
    }
  }

  // 获取用户仪表板数据
  async getUserDashboard(req: any, res: any) {
    const { userId } = req.params;

    try {
      // 获取个性化推荐
      const recommendations = await this.memoryService.getPersonalizedRecommendations(
        userId, 
        'dashboard'
      );

      // 获取最近活动
      const recentActivities = await this.memoryService.getConversationContext(
        userId, 
        '最近的活动和操作'
      );

      // 获取性能指标
      const performanceMetrics = await this.memoryService.getPerformanceMetrics();

      res.json({
        success: true,
        dashboard: {
          userId,
          recommendations: recommendations.recommendations,
          recentActivities: recentActivities.relevantHistory.slice(0, 10),
          userPreferences: recentActivities.userPreferences,
          systemHealth: {
            memoryCount: performanceMetrics.memoryCount,
            averageRetrievalTime: performanceMetrics.averageRetrievalTime,
            lastUpdated: new Date().toISOString()
          }
        }
      });

    } catch (error) {
      console.error('仪表板数据获取错误:', error);
      res.status(500).json({ error: '仪表板数据获取失败' });
    }
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// ============================================================================
// 4. 桌面应用集成示例 (Electron)
// ============================================================================

export class DesktopAppMemoryIntegration {
  private memoryService: AppMemoryService;

  constructor() {
    // 桌面应用配置
    const desktopConfig = {
      memory: {
        maxMemories: 5000,
        defaultThreshold: 0.8
      },
      rules: {
        personalRulesPath: './resources/desktop-personal-rules.yaml',
        projectRulesPath: './resources/desktop-project-rules.yaml'
      },
      performance: {
        enableMonitoring: true,
        logLevel: 'debug'
      }
    };

    this.memoryService = new AppMemoryService(desktopConfig);
  }

  async initialize() {
    await this.memoryService.initialize();
    console.log('🖥️ 桌面应用记忆系统初始化完成');
  }

  // 窗口操作记录
  async recordWindowAction(action: string, windowInfo: any) {
    return await this.memoryService.recordUserAction('desktop_user', action, {
      windowTitle: windowInfo.title,
      windowSize: windowInfo.size,
      windowPosition: windowInfo.position,
      timestamp: new Date(),
      source: 'window_manager'
    });
  }

  // 文件操作记录
  async recordFileAction(action: string, filePath: string, fileInfo?: any) {
    return await this.memoryService.recordUserAction('desktop_user', `file_${action}`, {
      filePath,
      fileName: this.extractFileName(filePath),
      fileExtension: this.extractFileExtension(filePath),
      fileSize: fileInfo?.size,
      timestamp: new Date(),
      source: 'file_manager'
    });
  }

  // 获取工作区推荐
  async getWorkspaceRecommendations() {
    const recommendations = await this.memoryService.getPersonalizedRecommendations(
      'desktop_user',
      'workspace'
    );

    return {
      recentFiles: this.getRecentFileRecommendations(recommendations),
      frequentActions: this.getFrequentActionRecommendations(recommendations),
      workspaceLayout: this.getLayoutRecommendations(recommendations)
    };
  }

  // 智能搜索
  async intelligentSearch(query: string) {
    const context = await this.memoryService.getConversationContext('desktop_user', query);
    
    return {
      query,
      contextualResults: context.relevantHistory,
      suggestedFilters: this.generateSearchFilters(context),
      relatedQueries: this.generateRelatedQueries(context)
    };
  }

  private extractFileName(filePath: string): string {
    return filePath.split(/[\\/]/).pop() || '';
  }

  private extractFileExtension(filePath: string): string {
    const fileName = this.extractFileName(filePath);
    const lastDot = fileName.lastIndexOf('.');
    return lastDot > 0 ? fileName.substring(lastDot + 1) : '';
  }

  private getRecentFileRecommendations(recommendations: any) {
    return recommendations.recommendations
      .filter((rec: any) => rec.content.includes('file_'))
      .slice(0, 10);
  }

  private getFrequentActionRecommendations(recommendations: any) {
    return recommendations.recommendations
      .filter((rec: any) => !rec.content.includes('file_'))
      .slice(0, 5);
  }

  private getLayoutRecommendations(recommendations: any) {
    return {
      suggestedWindowSize: { width: 1200, height: 800 },
      suggestedPosition: { x: 100, y: 100 },
      suggestedTheme: 'auto'
    };
  }

  private generateSearchFilters(context: any): string[] {
    const topics = context.relevantHistory
      .flatMap((memory: Memory) => memory.tags)
      .filter((tag: string) => !['desktop_user', 'conversation'].includes(tag));
    
    return [...new Set(topics)].slice(0, 5);
  }

  private generateRelatedQueries(context: any): string[] {
    return [
      '最近打开的文件',
      '常用操作',
      '项目相关文件',
      '今天的活动'
    ];
  }
}

// ============================================================================
// 5. 使用示例和测试
// ============================================================================

export class MemorySystemDemo {
  static async runBasicDemo() {
    console.log('🚀 开始基本功能演示...');
    
    const basicExample = new BasicMemoryExample();
    await basicExample.initialize();
    
    // 存储一些示例记忆
    await basicExample.storeBasicMemory();
    
    // 检索记忆
    const memories = await basicExample.retrieveMemories();
    console.log('检索到的记忆:', memories);
  }

  static async runAdvancedDemo() {
    console.log('🚀 开始高级功能演示...');
    
    const appService = new AppMemoryService();
    await appService.initialize();
    
    // 模拟用户行为
    await appService.recordUserAction('demo_user', 'create_project', {
      projectName: '演示项目',
      projectType: 'web_app'
    });
    
    await appService.recordUserAction('demo_user', 'edit_file', {
      fileName: 'index.html',
      fileType: 'html'
    });
    
    // 获取推荐
    const recommendations = await appService.getPersonalizedRecommendations('demo_user');
    console.log('个性化推荐:', recommendations);
    
    // 获取对话上下文
    const context = await appService.getConversationContext('demo_user', '帮我优化项目结构');
    console.log('对话上下文:', context);
  }

  static async runWebAppDemo() {
    console.log('🌐 开始Web应用演示...');
    
    const webApp = new WebAppMemoryIntegration();
    await webApp.initialize();
    
    // 模拟HTTP请求
    const mockReq = {
      body: { userId: 'web_user', message: '你好，我需要帮助' },
      ip: '127.0.0.1',
      get: () => 'Mozilla/5.0'
    };
    
    const mockRes = {
      json: (data: any) => console.log('响应:', data),
      status: (code: number) => ({ json: (data: any) => console.log(`错误 ${code}:`, data) })
    };
    
    await webApp.handleChatMessage(mockReq, mockRes);
  }

  static async runDesktopAppDemo() {
    console.log('🖥️ 开始桌面应用演示...');
    
    const desktopApp = new DesktopAppMemoryIntegration();
    await desktopApp.initialize();
    
    // 模拟桌面操作
    await desktopApp.recordWindowAction('open', {
      title: '代码编辑器',
      size: { width: 1200, height: 800 },
      position: { x: 100, y: 100 }
    });
    
    await desktopApp.recordFileAction('open', '/path/to/project/src/main.ts', {
      size: 1024
    });
    
    // 获取工作区推荐
    const workspaceRec = await desktopApp.getWorkspaceRecommendations();
    console.log('工作区推荐:', workspaceRec);
    
    // 智能搜索
    const searchResults = await desktopApp.intelligentSearch('TypeScript 配置');
    console.log('搜索结果:', searchResults);
  }

  static async runPerformanceTest() {
    console.log('⚡ 开始性能测试...');
    
    const appService = new AppMemoryService();
    await appService.initialize();
    
    const startTime = Date.now();
    
    // 批量存储记忆
    const promises = [];
    for (let i = 0; i < 100; i++) {
      promises.push(
        appService.recordUserAction(`test_user_${i % 10}`, `action_${i}`, {
          index: i,
          timestamp: new Date()
        })
      );
    }
    
    await Promise.all(promises);
    
    const storageTime = Date.now() - startTime;
    console.log(`✅ 存储100条记忆耗时: ${storageTime}ms`);
    
    // 批量检索测试
    const retrievalStart = Date.now();
    
    const retrievalPromises = [];
    for (let i = 0; i < 20; i++) {
      retrievalPromises.push(
        appService.getPersonalizedRecommendations(`test_user_${i % 10}`)
      );
    }
    
    await Promise.all(retrievalPromises);
    
    const retrievalTime = Date.now() - retrievalStart;
    console.log(`✅ 20次检索耗时: ${retrievalTime}ms`);
    
    // 获取性能指标
    const metrics = await appService.getPerformanceMetrics();
    console.log('📊 性能指标:', metrics);
  }
}

// ============================================================================
// 6. 导出所有示例
// ============================================================================

export {
  BasicMemoryExample,
  AppMemoryService,
  WebAppMemoryIntegration,
  DesktopAppMemoryIntegration,
  MemorySystemDemo
};

// 如果直接运行此文件，执行演示
if (require.main === module) {
  (async () => {
    try {
      await MemorySystemDemo.runBasicDemo();
      await MemorySystemDemo.runAdvancedDemo();
      await MemorySystemDemo.runPerformanceTest();
    } catch (error) {
      console.error('演示运行错误:', error);
    }
  })();
}