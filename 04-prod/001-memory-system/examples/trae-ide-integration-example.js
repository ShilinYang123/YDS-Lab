/**
 * Trae IDE 自动记录功能集成示例
 * 
 * 本示例展示如何在实际项目中集成和使用长效记忆系统的自动记录功能
 * 适用于 JS-004-本地AI模型部署与Trae IDE集成 项目
 */

const { LongTermMemorySystem } = require('../src/index');
const path = require('path');

class ProjectMemoryManager {
    constructor(projectConfig) {
        this.projectConfig = projectConfig;
        this.memorySystem = null;
        this.isInitialized = false;
    }

    /**
     * 初始化项目记忆管理器
     */
    async initialize() {
        try {
            console.log('🚀 初始化项目记忆管理器...');
            
            // 创建长效记忆系统实例
            this.memorySystem = new LongTermMemorySystem();
            
            // 使用项目特定的配置
            const memoryConfig = {
                // 基础配置
                dataPath: this.projectConfig.memory_storage.project_memories,
                logLevel: 'info',
                
                // Trae IDE 集成配置
                traeIDEIntegration: {
                    enabled: true,
                    config: {
                        // 自动记录配置
                        autoRecord: {
                            enabled: true,
                            batchSize: 10,
                            flushInterval: 5000,
                            maxRetries: 3
                        },
                        
                        // 智能筛选配置
                        intelligentFilter: {
                            enabled: true,
                            minImportance: 0.3,
                            maxSimilarity: 0.8,
                            contentFilters: {
                                minLength: 10,
                                maxLength: 10000,
                                excludePatterns: [
                                    /^console\.log/,
                                    /^\/\//,
                                    /^\s*$/
                                ]
                            }
                        },
                        
                        // 内容处理配置
                        contentProcessor: {
                            enabled: true,
                            extractKeywords: true,
                            generateSummary: true,
                            analyzeCode: true,
                            compressContent: true
                        },
                        
                        // 上下文提取配置
                        contextExtractor: {
                            enabled: true,
                            extractFileContext: true,
                            extractProjectContext: true,
                            extractGitContext: true,
                            cacheTimeout: 300000 // 5分钟
                        }
                    }
                }
            };
            
            // 初始化记忆系统
            await this.memorySystem.initialize(memoryConfig);
            
            // 启用自动记录功能
            await this.memorySystem.enableAutoRecord();
            
            this.isInitialized = true;
            console.log('✅ 项目记忆管理器初始化成功');
            
            // 记录初始化事件
            await this.recordProjectEvent('system_initialization', {
                project: this.projectConfig.project.name,
                version: this.projectConfig.project.version,
                timestamp: new Date().toISOString(),
                config: memoryConfig
            });
            
        } catch (error) {
            console.error('❌ 项目记忆管理器初始化失败:', error);
            throw error;
        }
    }

    /**
     * 记录项目事件
     */
    async recordProjectEvent(eventType, eventData) {
        if (!this.isInitialized) {
            console.warn('⚠️ 记忆系统未初始化，跳过事件记录');
            return;
        }

        try {
            const memory = {
                content: `项目事件: ${eventType}`,
                type: 'episodic',
                metadata: {
                    eventType,
                    project: this.projectConfig.project.name,
                    timestamp: new Date().toISOString(),
                    ...eventData
                },
                context: {
                    project: this.projectConfig.project.name,
                    environment: 'development',
                    platform: process.platform
                },
                importance: this.calculateEventImportance(eventType),
                tags: [eventType, 'project_event', this.projectConfig.project.name]
            };

            const memoryId = await this.memorySystem.storeMemory(memory);
            console.log(`📝 事件已记录: ${eventType} (ID: ${memoryId})`);
            
            return memoryId;
        } catch (error) {
            console.error('❌ 事件记录失败:', error);
        }
    }

    /**
     * 计算事件重要性
     */
    calculateEventImportance(eventType) {
        const importanceMap = {
            'system_initialization': 0.9,
            'deployment_start': 0.8,
            'deployment_complete': 0.8,
            'model_download': 0.7,
            'api_test': 0.6,
            'configuration_change': 0.7,
            'error_occurred': 0.9,
            'performance_issue': 0.8,
            'user_interaction': 0.5
        };
        
        return importanceMap[eventType] || 0.5;
    }

    /**
     * 获取项目记忆统计
     */
    async getProjectMemoryStats() {
        if (!this.isInitialized) {
            return null;
        }

        try {
            const stats = await this.memorySystem.getSystemStats();
            const autoRecordStatus = await this.memorySystem.getAutoRecordStatus();
            
            return {
                ...stats,
                autoRecord: autoRecordStatus,
                project: {
                    name: this.projectConfig.project.name,
                    version: this.projectConfig.project.version
                }
            };
        } catch (error) {
            console.error('❌ 获取统计信息失败:', error);
            return null;
        }
    }

    /**
     * 搜索项目相关记忆
     */
    async searchProjectMemories(query, options = {}) {
        if (!this.isInitialized) {
            return { memories: [], totalResults: 0 };
        }

        try {
            const searchOptions = {
                limit: 10,
                minConfidence: 0.3,
                ...options,
                filters: {
                    project: this.projectConfig.project.name,
                    ...options.filters
                }
            };

            const results = await this.memorySystem.retrieveMemories(query, searchOptions);
            console.log(`🔍 搜索到 ${results.memories.length} 条相关记忆`);
            
            return results;
        } catch (error) {
            console.error('❌ 记忆搜索失败:', error);
            return { memories: [], totalResults: 0 };
        }
    }

    /**
     * 生成项目报告
     */
    async generateProjectReport() {
        if (!this.isInitialized) {
            return null;
        }

        try {
            console.log('📊 生成项目记忆报告...');
            
            const stats = await this.getProjectMemoryStats();
            const recentMemories = await this.searchProjectMemories('', { limit: 20 });
            
            const report = {
                project: {
                    name: this.projectConfig.project.name,
                    version: this.projectConfig.project.version
                },
                timestamp: new Date().toISOString(),
                statistics: stats,
                recentActivities: recentMemories.memories.map(memory => ({
                    id: memory.id,
                    type: memory.type,
                    content: memory.content.substring(0, 100) + '...',
                    importance: memory.importance,
                    createdAt: memory.createdAt
                })),
                summary: {
                    totalMemories: stats?.memories?.total || 0,
                    autoRecordEnabled: stats?.autoRecord?.enabled || false,
                    systemHealth: stats?.performance?.status || 'unknown'
                }
            };
            
            console.log('✅ 项目报告生成完成');
            return report;
        } catch (error) {
            console.error('❌ 报告生成失败:', error);
            return null;
        }
    }

    /**
     * 清理和关闭
     */
    async cleanup() {
        if (this.memorySystem && this.isInitialized) {
            try {
                console.log('🧹 清理项目记忆管理器...');
                
                // 记录关闭事件
                await this.recordProjectEvent('system_shutdown', {
                    timestamp: new Date().toISOString()
                });
                
                // 关闭记忆系统
                await this.memorySystem.destroy();
                
                this.isInitialized = false;
                console.log('✅ 项目记忆管理器已清理');
            } catch (error) {
                console.error('❌ 清理失败:', error);
            }
        }
    }
}

// 使用示例
async function demonstrateUsage() {
    // 模拟项目配置
    const projectConfig = {
        project: {
            name: "JS-004-本地AI模型部署与Trae IDE集成",
            version: "1.0.0"
        },
        memory_storage: {
            project_memories: path.join(__dirname, '../data/memories')
        }
    };

    const projectManager = new ProjectMemoryManager(projectConfig);

    try {
        // 1. 初始化
        await projectManager.initialize();

        // 2. 记录一些项目事件
        await projectManager.recordProjectEvent('deployment_start', {
            target: 'Shimmy 1.7.4',
            environment: 'local'
        });

        await projectManager.recordProjectEvent('model_download', {
            model: 'llama3.2:3b',
            size: '2.0GB',
            source: 'ollama'
        });

        await projectManager.recordProjectEvent('api_test', {
            endpoint: 'http://localhost:11434/api/generate',
            status: 'success',
            responseTime: '1.2s'
        });

        // 3. 搜索记忆
        const searchResults = await projectManager.searchProjectMemories('部署');
        console.log('\n🔍 搜索结果:');
        searchResults.memories.forEach((memory, index) => {
            console.log(`  ${index + 1}. ${memory.content.substring(0, 50)}...`);
        });

        // 4. 生成报告
        const report = await projectManager.generateProjectReport();
        console.log('\n📊 项目报告:');
        console.log(`  项目: ${report.project.name}`);
        console.log(`  总记忆数: ${report.summary.totalMemories}`);
        console.log(`  自动记录: ${report.summary.autoRecordEnabled ? '启用' : '禁用'}`);

        // 5. 清理
        await projectManager.cleanup();

    } catch (error) {
        console.error('❌ 演示过程中发生错误:', error);
        await projectManager.cleanup();
    }
}

// 如果直接运行此文件，则执行演示
if (require.main === module) {
    demonstrateUsage().catch(console.error);
}

module.exports = { ProjectMemoryManager };