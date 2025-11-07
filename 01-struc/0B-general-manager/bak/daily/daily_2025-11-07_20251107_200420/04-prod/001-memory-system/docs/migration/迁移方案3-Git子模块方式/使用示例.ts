// JS003-Trae长记忆功能 Git子模块方式使用示例
// 本文件展示了如何在使用Git子模块集成长记忆功能后进行开发

import { LongTermMemorySystem } from '../src/memory-system/src';
import type { 
  Memory, 
  RetrievalQuery, 
  EnhancementContext,
  MemoryMetadata 
} from '../src/memory-system/src/types';

// ============================================================================
// 1. 基本集成示例
// ============================================================================

export class ProjectMemoryService {
  private memorySystem: LongTermMemorySystem;
  private initialized = false;

  constructor() {
    // 使用相对于子模块的配置路径
    const config = {
      rules: {
        personalRulesPath: './config/memory-rules/personal-rules.yaml',
        projectRulesPath: './config/memory-rules/project-rules.yaml'
      },
      knowledgeGraph: {
        enablePersistence: true,
        persistencePath: './data/knowledge-graph.json'
      },
      performance: {
        enableMonitoring: true,
        metricsPath: './logs/performance-metrics.json'
      }
    };
    
    this.memorySystem = new LongTermMemorySystem(config);
  }

  async initialize() {
    if (!this.initialized) {
      await this.memorySystem.initialize();
      this.initialized = true;
      console.log('✅ 项目记忆服务初始化完成');
    }
  }

  async storeProjectMemory(content: string, type: string, metadata?: any) {
    await this.ensureInitialized();
    
    return await this.memorySystem.storeMemory({
      content,
      type,
      tags: ['project', type],
      metadata: {
        ...metadata,
        projectName: 'your-project',
        timestamp: new Date().toISOString(),
        source: 'submodule_integration'
      }
    });
  }

  async getProjectContext(query: string) {
    await this.ensureInitialized();
    
    const memories = await this.memorySystem.retrieveMemories({
      query,
      tags: ['project'],
      limit: 10,
      threshold: 0.7
    });

    const enhancementContext = await this.memorySystem.getEnhancementContext({
      query,
      includeRules: true,
      includeMemories: true,
      maxMemories: 5
    });

    return {
      memories,
      enhancementContext,
      projectInsights: this.generateProjectInsights(memories)
    };
  }

  private async ensureInitialized() {
    if (!this.initialized) {
      await this.initialize();
    }
  }

  private generateProjectInsights(memories: Memory[]) {
    return {
      totalMemories: memories.length,
      commonTags: this.extractCommonTags(memories),
      timeRange: this.getTimeRange(memories),
      categories: this.categorizeMemories(memories)
    };
  }

  private extractCommonTags(memories: Memory[]): string[] {
    const tagCounts: Record<string, number> = {};
    memories.forEach(memory => {
      memory.tags.forEach(tag => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      });
    });

    return Object.entries(tagCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([tag]) => tag);
  }

  private getTimeRange(memories: Memory[]) {
    if (memories.length === 0) return null;
    
    const dates = memories.map(m => new Date(m.createdAt));
    return {
      earliest: new Date(Math.min(...dates.map(d => d.getTime()))),
      latest: new Date(Math.max(...dates.map(d => d.getTime())))
    };
  }

  private categorizeMemories(memories: Memory[]) {
    const categories: Record<string, number> = {};
    memories.forEach(memory => {
      categories[memory.type] = (categories[memory.type] || 0) + 1;
    });
    return categories;
  }
}

// ============================================================================
// 2. 团队协作增强服务
// ============================================================================

export class TeamMemoryService extends ProjectMemoryService {
  async recordTeamActivity(userId: string, activity: string, details?: any) {
    return await this.storeProjectMemory(
      `团队成员 ${userId} ${activity}`,
      'team_activity',
      {
        userId,
        activity,
        details,
        teamContext: true
      }
    );
  }

  async getTeamInsights(timeRange?: { start: Date; end: Date }) {
    const query = timeRange 
      ? `团队活动 从 ${timeRange.start.toISOString()} 到 ${timeRange.end.toISOString()}`
      : '团队活动和协作';

    const context = await this.getProjectContext(query);
    
    return {
      ...context,
      teamMetrics: this.calculateTeamMetrics(context.memories),
      collaborationPatterns: this.analyzeCollaborationPatterns(context.memories)
    };
  }

  async generateTeamReport(period: 'daily' | 'weekly' | 'monthly' = 'weekly') {
    const now = new Date();
    const startDate = new Date();
    
    switch (period) {
      case 'daily':
        startDate.setDate(now.getDate() - 1);
        break;
      case 'weekly':
        startDate.setDate(now.getDate() - 7);
        break;
      case 'monthly':
        startDate.setMonth(now.getMonth() - 1);
        break;
    }

    const insights = await this.getTeamInsights({ start: startDate, end: now });
    
    return {
      period,
      timeRange: { start: startDate, end: now },
      summary: {
        totalActivities: insights.teamMetrics.totalActivities,
        activeMembers: insights.teamMetrics.activeUsers,
        topActivities: insights.collaborationPatterns.commonActivities.slice(0, 3),
        peakHours: insights.collaborationPatterns.peakHours
      },
      details: insights,
      recommendations: this.generateTeamRecommendations(insights)
    };
  }

  private calculateTeamMetrics(memories: Memory[]) {
    const teamMemories = memories.filter(m => m.type === 'team_activity');
    const userActivities: Record<string, number> = {};
    
    teamMemories.forEach(memory => {
      const userId = memory.metadata?.userId;
      if (userId) {
        userActivities[userId] = (userActivities[userId] || 0) + 1;
      }
    });

    return {
      totalActivities: teamMemories.length,
      activeUsers: Object.keys(userActivities).length,
      averageActivitiesPerUser: teamMemories.length / Object.keys(userActivities).length || 0,
      mostActiveUser: Object.entries(userActivities)
        .sort(([, a], [, b]) => b - a)[0]?.[0],
      userActivities
    };
  }

  private analyzeCollaborationPatterns(memories: Memory[]) {
    return {
      peakHours: this.findPeakActivityHours(memories),
      commonActivities: this.findCommonActivities(memories),
      collaborationFrequency: this.calculateCollaborationFrequency(memories),
      activityTrends: this.calculateActivityTrends(memories)
    };
  }

  private findPeakActivityHours(memories: Memory[]): number[] {
    const hourCounts: Record<number, number> = {};
    
    memories.forEach(memory => {
      const hour = new Date(memory.createdAt).getHours();
      hourCounts[hour] = (hourCounts[hour] || 0) + 1;
    });

    return Object.entries(hourCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([hour]) => parseInt(hour));
  }

  private findCommonActivities(memories: Memory[]): string[] {
    const activities: Record<string, number> = {};
    
    memories.forEach(memory => {
      const activity = memory.metadata?.activity;
      if (activity) {
        activities[activity] = (activities[activity] || 0) + 1;
      }
    });

    return Object.entries(activities)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 5)
      .map(([activity]) => activity);
  }

  private calculateCollaborationFrequency(memories: Memory[]): number {
    const teamMemories = memories.filter(m => m.type === 'team_activity');
    const totalDays = this.calculateDateRange(teamMemories);
    
    return totalDays > 0 ? teamMemories.length / totalDays : 0;
  }

  private calculateActivityTrends(memories: Memory[]) {
    const dailyActivities: Record<string, number> = {};
    
    memories.forEach(memory => {
      const date = new Date(memory.createdAt).toISOString().split('T')[0];
      dailyActivities[date] = (dailyActivities[date] || 0) + 1;
    });

    const dates = Object.keys(dailyActivities).sort();
    const activities = dates.map(date => dailyActivities[date]);
    
    return {
      dates,
      activities,
      trend: this.calculateTrend(activities),
      average: activities.reduce((sum, count) => sum + count, 0) / activities.length || 0
    };
  }

  private calculateTrend(values: number[]): 'increasing' | 'decreasing' | 'stable' {
    if (values.length < 2) return 'stable';
    
    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    
    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
    
    const difference = secondAvg - firstAvg;
    const threshold = firstAvg * 0.1; // 10% threshold
    
    if (difference > threshold) return 'increasing';
    if (difference < -threshold) return 'decreasing';
    return 'stable';
  }

  private calculateDateRange(memories: Memory[]): number {
    if (memories.length === 0) return 0;
    
    const dates = memories.map(m => new Date(m.createdAt));
    const earliest = Math.min(...dates.map(d => d.getTime()));
    const latest = Math.max(...dates.map(d => d.getTime()));
    
    return Math.ceil((latest - earliest) / (1000 * 60 * 60 * 24)) + 1;
  }

  private generateTeamRecommendations(insights: any) {
    const recommendations: string[] = [];
    
    // 基于活动频率的建议
    if (insights.collaborationPatterns.collaborationFrequency < 1) {
      recommendations.push('建议增加团队协作频率，目前平均每天少于1次活动');
    }
    
    // 基于活跃用户数的建议
    if (insights.teamMetrics.activeUsers < 3) {
      recommendations.push('团队参与度较低，建议鼓励更多成员参与项目活动');
    }
    
    // 基于活动趋势的建议
    if (insights.collaborationPatterns.activityTrends.trend === 'decreasing') {
      recommendations.push('团队活动呈下降趋势，建议组织团队会议或活动');
    }
    
    // 基于峰值时间的建议
    const peakHours = insights.collaborationPatterns.peakHours;
    if (peakHours.length > 0) {
      recommendations.push(`团队最活跃时间为 ${peakHours.join(', ')} 点，建议在此时间安排重要会议`);
    }
    
    return recommendations;
  }
}

// ============================================================================
// 3. Web应用集成 (Express.js)
// ============================================================================

import express from 'express';

export class WebMemoryController {
  private memoryService: TeamMemoryService;

  constructor() {
    this.memoryService = new TeamMemoryService();
  }

  async initialize() {
    await this.memoryService.initialize();
  }

  setupRoutes(app: express.Application) {
    // 存储记忆
    app.post('/api/memory', async (req, res) => {
      try {
        const { content, type, metadata } = req.body;
        const memory = await this.memoryService.storeProjectMemory(content, type, metadata);
        res.json({ success: true, memory });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // 检索记忆
    app.get('/api/memory/search', async (req, res) => {
      try {
        const { query, tags, limit } = req.query;
        const context = await this.memoryService.getProjectContext(query as string);
        res.json({ success: true, context });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // 团队活动记录
    app.post('/api/team/activity', async (req, res) => {
      try {
        const { userId, activity, details } = req.body;
        const memory = await this.memoryService.recordTeamActivity(userId, activity, details);
        res.json({ success: true, memory });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // 团队洞察
    app.get('/api/team/insights', async (req, res) => {
      try {
        const { startDate, endDate } = req.query;
        const timeRange = startDate && endDate ? {
          start: new Date(startDate as string),
          end: new Date(endDate as string)
        } : undefined;
        
        const insights = await this.memoryService.getTeamInsights(timeRange);
        res.json({ success: true, insights });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // 团队报告
    app.get('/api/team/report/:period', async (req, res) => {
      try {
        const { period } = req.params;
        const report = await this.memoryService.generateTeamReport(period as any);
        res.json({ success: true, report });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });
  }
}

// ============================================================================
// 4. 桌面应用集成 (Electron)
// ============================================================================

export class DesktopMemoryManager {
  private memoryService: TeamMemoryService;
  private isElectron: boolean;

  constructor() {
    this.memoryService = new TeamMemoryService();
    this.isElectron = typeof window !== 'undefined' && window.process?.type === 'renderer';
  }

  async initialize() {
    await this.memoryService.initialize();
    
    if (this.isElectron) {
      this.setupElectronIntegration();
    }
  }

  private setupElectronIntegration() {
    const { ipcRenderer } = require('electron');
    
    // 监听主进程的记忆请求
    ipcRenderer.on('store-memory', async (event, data) => {
      try {
        const memory = await this.memoryService.storeProjectMemory(
          data.content,
          data.type,
          data.metadata
        );
        event.reply('memory-stored', { success: true, memory });
      } catch (error) {
        event.reply('memory-stored', { success: false, error: error.message });
      }
    });

    // 监听记忆检索请求
    ipcRenderer.on('retrieve-memories', async (event, query) => {
      try {
        const context = await this.memoryService.getProjectContext(query);
        event.reply('memories-retrieved', { success: true, context });
      } catch (error) {
        event.reply('memories-retrieved', { success: false, error: error.message });
      }
    });

    // 监听团队报告请求
    ipcRenderer.on('generate-team-report', async (event, period) => {
      try {
        const report = await this.memoryService.generateTeamReport(period);
        event.reply('team-report-generated', { success: true, report });
      } catch (error) {
        event.reply('team-report-generated', { success: false, error: error.message });
      }
    });
  }

  // 桌面应用专用方法
  async exportMemories(format: 'json' | 'csv' | 'markdown' = 'json') {
    const allMemories = await this.memoryService.getProjectContext('');
    
    switch (format) {
      case 'json':
        return JSON.stringify(allMemories, null, 2);
      
      case 'csv':
        return this.convertToCSV(allMemories.memories);
      
      case 'markdown':
        return this.convertToMarkdown(allMemories.memories);
      
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  private convertToCSV(memories: Memory[]): string {
    const headers = ['ID', 'Content', 'Type', 'Tags', 'Created At', 'Metadata'];
    const rows = memories.map(memory => [
      memory.id,
      `"${memory.content.replace(/"/g, '""')}"`,
      memory.type,
      memory.tags.join(';'),
      memory.createdAt,
      JSON.stringify(memory.metadata || {})
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  private convertToMarkdown(memories: Memory[]): string {
    let markdown = '# 项目记忆导出\n\n';
    
    memories.forEach((memory, index) => {
      markdown += `## 记忆 ${index + 1}\n\n`;
      markdown += `**ID**: ${memory.id}\n`;
      markdown += `**类型**: ${memory.type}\n`;
      markdown += `**标签**: ${memory.tags.join(', ')}\n`;
      markdown += `**创建时间**: ${memory.createdAt}\n\n`;
      markdown += `**内容**:\n${memory.content}\n\n`;
      
      if (memory.metadata && Object.keys(memory.metadata).length > 0) {
        markdown += `**元数据**:\n\`\`\`json\n${JSON.stringify(memory.metadata, null, 2)}\n\`\`\`\n\n`;
      }
      
      markdown += '---\n\n';
    });
    
    return markdown;
  }
}

// ============================================================================
// 5. 使用示例和测试
// ============================================================================

// 基本使用演示
export async function basicUsageDemo() {
  console.log('🚀 基本使用演示');
  
  const memoryService = new ProjectMemoryService();
  await memoryService.initialize();

  // 存储一些示例记忆
  await memoryService.storeProjectMemory(
    '实现了用户认证功能，包括登录、注册和密码重置',
    'feature_implementation',
    { 
      module: 'auth', 
      complexity: 'medium',
      estimatedHours: 8,
      technologies: ['JWT', 'bcrypt', 'express-validator']
    }
  );

  await memoryService.storeProjectMemory(
    '修复了数据库连接池的内存泄漏问题',
    'bug_fix',
    { 
      severity: 'high',
      affectedUsers: 'all',
      fixTime: '2 hours'
    }
  );

  await memoryService.storeProjectMemory(
    '优化了API响应时间，平均提升了40%',
    'performance_optimization',
    { 
      improvement: '40%',
      metrics: ['response_time', 'throughput'],
      techniques: ['caching', 'query_optimization']
    }
  );

  // 检索相关记忆
  const context = await memoryService.getProjectContext('用户认证和安全');
  console.log('检索到的上下文:', {
    memoriesCount: context.memories.length,
    insights: context.projectInsights
  });

  return context;
}

// 团队协作演示
export async function teamCollaborationDemo() {
  console.log('👥 团队协作演示');
  
  const teamService = new TeamMemoryService();
  await teamService.initialize();

  // 记录团队活动
  await teamService.recordTeamActivity('alice', '代码审查', {
    pullRequest: 'PR-123',
    reviewType: 'security',
    findings: 3
  });

  await teamService.recordTeamActivity('bob', '功能开发', {
    feature: 'user-dashboard',
    status: 'completed',
    linesOfCode: 450
  });

  await teamService.recordTeamActivity('charlie', '测试编写', {
    testType: 'integration',
    coverage: '85%',
    testsAdded: 12
  });

  // 生成团队报告
  const report = await teamService.generateTeamReport('weekly');
  console.log('团队周报:', {
    period: report.period,
    summary: report.summary,
    recommendations: report.recommendations
  });

  return report;
}

// Web应用演示
export async function webApplicationDemo() {
  console.log('🌐 Web应用演示');
  
  const app = express();
  app.use(express.json());

  const webController = new WebMemoryController();
  await webController.initialize();
  webController.setupRoutes(app);

  // 模拟启动服务器
  console.log('Web服务器已配置，路由包括:');
  console.log('- POST /api/memory - 存储记忆');
  console.log('- GET /api/memory/search - 搜索记忆');
  console.log('- POST /api/team/activity - 记录团队活动');
  console.log('- GET /api/team/insights - 获取团队洞察');
  console.log('- GET /api/team/report/:period - 生成团队报告');

  return app;
}

// 桌面应用演示
export async function desktopApplicationDemo() {
  console.log('🖥️ 桌面应用演示');
  
  const desktopManager = new DesktopMemoryManager();
  await desktopManager.initialize();

  // 模拟导出功能
  const jsonExport = await desktopManager.exportMemories('json');
  const csvExport = await desktopManager.exportMemories('csv');
  const markdownExport = await desktopManager.exportMemories('markdown');

  console.log('导出功能演示完成:', {
    jsonLength: jsonExport.length,
    csvLength: csvExport.length,
    markdownLength: markdownExport.length
  });

  return {
    json: jsonExport,
    csv: csvExport,
    markdown: markdownExport
  };
}

// 性能测试
export async function performanceTest() {
  console.log('⚡ 性能测试');
  
  const memoryService = new ProjectMemoryService();
  await memoryService.initialize();

  const startTime = Date.now();
  const batchSize = 100;

  // 批量存储测试
  console.log(`📝 批量存储 ${batchSize} 条记忆...`);
  const storePromises = Array.from({ length: batchSize }, (_, i) => 
    memoryService.storeProjectMemory(
      `测试记忆 ${i + 1}: 这是一个性能测试记忆，包含一些示例内容`,
      'performance_test',
      { 
        testId: i + 1,
        batchSize,
        timestamp: new Date().toISOString()
      }
    )
  );

  await Promise.all(storePromises);
  const storeTime = Date.now() - startTime;

  // 批量检索测试
  console.log('🔍 批量检索测试...');
  const retrieveStartTime = Date.now();
  
  const retrievePromises = Array.from({ length: 10 }, (_, i) =>
    memoryService.getProjectContext(`测试记忆 ${i * 10 + 1}`)
  );

  const results = await Promise.all(retrievePromises);
  const retrieveTime = Date.now() - retrieveStartTime;

  const totalTime = Date.now() - startTime;

  console.log('📊 性能测试结果:', {
    batchSize,
    storeTime: `${storeTime}ms`,
    retrieveTime: `${retrieveTime}ms`,
    totalTime: `${totalTime}ms`,
    averageStoreTime: `${(storeTime / batchSize).toFixed(2)}ms/记忆`,
    averageRetrieveTime: `${(retrieveTime / 10).toFixed(2)}ms/查询`,
    totalMemoriesRetrieved: results.reduce((sum, result) => sum + result.memories.length, 0)
  });

  return {
    batchSize,
    storeTime,
    retrieveTime,
    totalTime,
    results
  };
}

// 综合演示函数
export async function runAllDemos() {
  console.log('🎯 开始运行所有演示...\n');

  try {
    // 1. 基本使用
    await basicUsageDemo();
    console.log('✅ 基本使用演示完成\n');

    // 2. 团队协作
    await teamCollaborationDemo();
    console.log('✅ 团队协作演示完成\n');

    // 3. Web应用
    await webApplicationDemo();
    console.log('✅ Web应用演示完成\n');

    // 4. 桌面应用
    await desktopApplicationDemo();
    console.log('✅ 桌面应用演示完成\n');

    // 5. 性能测试
    await performanceTest();
    console.log('✅ 性能测试完成\n');

    console.log('🎉 所有演示运行完成！');
    console.log('\n📚 更多信息请查看:');
    console.log('- README.md - 详细使用说明');
    console.log('- 子模块文档 - src/memory-system/README.md');
    console.log('- 配置文件 - config/memory-rules/');

  } catch (error) {
    console.error('❌ 演示运行失败:', error);
    throw error;
  }
}

// 如果直接运行此文件，执行所有演示
if (require.main === module) {
  runAllDemos().catch(console.error);
}