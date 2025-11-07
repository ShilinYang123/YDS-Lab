#!/usr/bin/env node

/**
 * Trae IDE 集成自动部署脚本
 * 
 * 该脚本自动化部署和配置 Trae IDE 长效记忆系统集成功能
 * 
 * 使用方法:
 *   node scripts/deploy-trae-integration.js [options]
 * 
 * 选项:
 *   --config <path>    指定配置文件路径
 *   --env <env>        指定环境 (dev/prod)
 *   --skip-test        跳过测试
 *   --verbose          详细输出
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class TraeIDEDeployment {
    constructor(options = {}) {
        this.options = {
            configPath: options.configPath || './memory-config.yaml',
            environment: options.environment || 'dev',
            skipTest: options.skipTest || false,
            verbose: options.verbose || false,
            ...options
        };
        
        this.deploymentSteps = [
            'validateEnvironment',
            'checkDependencies',
            'createDirectories',
            'generateConfig',
            'installComponents',
            'runTests',
            'startServices',
            'validateDeployment'
        ];
    }

    /**
     * 执行部署
     */
    async deploy() {
        console.log('🚀 开始部署 Trae IDE 长效记忆系统集成...\n');
        
        const startTime = Date.now();
        let completedSteps = 0;
        
        try {
            for (const step of this.deploymentSteps) {
                if (this.options.skipTest && step === 'runTests') {
                    this.log(`⏭️  跳过步骤: ${step}`);
                    continue;
                }
                
                this.log(`📋 执行步骤 ${completedSteps + 1}/${this.deploymentSteps.length}: ${step}`);
                await this[step]();
                completedSteps++;
                this.log(`✅ 步骤完成: ${step}\n`);
            }
            
            const duration = Date.now() - startTime;
            console.log(`🎉 部署成功完成！`);
            console.log(`⏱️  总耗时: ${(duration / 1000).toFixed(2)}秒`);
            console.log(`📊 完成步骤: ${completedSteps}/${this.deploymentSteps.length}`);
            
            await this.generateDeploymentReport(true, duration, completedSteps);
            
        } catch (error) {
            const duration = Date.now() - startTime;
            console.error(`❌ 部署失败: ${error.message}`);
            console.log(`⏱️  失败前耗时: ${(duration / 1000).toFixed(2)}秒`);
            console.log(`📊 完成步骤: ${completedSteps}/${this.deploymentSteps.length}`);
            
            await this.generateDeploymentReport(false, duration, completedSteps, error);
            process.exit(1);
        }
    }

    /**
     * 验证环境
     */
    async validateEnvironment() {
        this.log('检查 Node.js 版本...');
        const nodeVersion = process.version;
        const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
        
        if (majorVersion < 16) {
            throw new Error(`需要 Node.js 16+ 版本，当前版本: ${nodeVersion}`);
        }
        
        this.log(`✓ Node.js 版本: ${nodeVersion}`);
        
        // 检查必要的目录
        const requiredDirs = [
            './src',
            './data',
            './config'
        ];
        
        for (const dir of requiredDirs) {
            try {
                await fs.access(dir);
                this.log(`✓ 目录存在: ${dir}`);
            } catch {
                throw new Error(`缺少必要目录: ${dir}`);
            }
        }
    }

    /**
     * 检查依赖
     */
    async checkDependencies() {
        this.log('检查 package.json...');
        
        try {
            const packageJson = JSON.parse(await fs.readFile('./package.json', 'utf8'));
            this.log(`✓ 项目: ${packageJson.name} v${packageJson.version}`);
            
            // 检查关键依赖
            const requiredDeps = ['typescript', 'yaml'];
            const missingDeps = [];
            
            for (const dep of requiredDeps) {
                if (!packageJson.dependencies?.[dep] && !packageJson.devDependencies?.[dep]) {
                    missingDeps.push(dep);
                }
            }
            
            if (missingDeps.length > 0) {
                this.log(`⚠️  缺少依赖，正在安装: ${missingDeps.join(', ')}`);
                execSync(`npm install ${missingDeps.join(' ')}`, { stdio: 'inherit' });
            }
            
        } catch (error) {
            throw new Error(`package.json 检查失败: ${error.message}`);
        }
    }

    /**
     * 创建目录结构
     */
    async createDirectories() {
        const directories = [
            './data/memories',
            './data/knowledge-graph',
            './logs',
            './backups',
            './examples',
            './docs'
        ];
        
        for (const dir of directories) {
            try {
                await fs.mkdir(dir, { recursive: true });
                this.log(`✓ 创建目录: ${dir}`);
            } catch (error) {
                if (error.code !== 'EEXIST') {
                    throw new Error(`创建目录失败 ${dir}: ${error.message}`);
                }
                this.log(`✓ 目录已存在: ${dir}`);
            }
        }
    }

    /**
     * 生成配置文件
     */
    async generateConfig() {
        const configTemplate = {
            // 基础配置
            dataPath: './data/memories',
            logLevel: this.options.environment === 'prod' ? 'info' : 'debug',
            
            // Trae IDE 集成配置
            traeIDEIntegration: {
                enabled: true,
                config: {
                    // 自动记录配置
                    autoRecord: {
                        enabled: true,
                        batchSize: this.options.environment === 'prod' ? 20 : 10,
                        flushInterval: this.options.environment === 'prod' ? 10000 : 5000,
                        maxRetries: 3
                    },
                    
                    // 智能筛选配置
                    intelligentFilter: {
                        enabled: true,
                        minImportance: this.options.environment === 'prod' ? 0.4 : 0.3,
                        maxSimilarity: 0.8,
                        contentFilters: {
                            minLength: 10,
                            maxLength: 10000,
                            excludePatterns: [
                                '^console\\.log',
                                '^//',
                                '^\\s*$'
                            ]
                        }
                    },
                    
                    // 内容处理配置
                    contentProcessor: {
                        enabled: true,
                        extractKeywords: true,
                        generateSummary: this.options.environment === 'prod',
                        analyzeCode: true,
                        compressContent: this.options.environment === 'prod'
                    },
                    
                    // 上下文提取配置
                    contextExtractor: {
                        enabled: true,
                        extractFileContext: true,
                        extractProjectContext: true,
                        extractGitContext: true,
                        cache: {
                            enabled: true,
                            timeout: 300000,
                            maxSize: this.options.environment === 'prod' ? 2000 : 1000
                        }
                    }
                }
            },
            
            // 性能监控配置
            performanceMonitoring: {
                enabled: true,
                enableCPUMonitoring: true,
                enableMemoryMonitoring: true,
                monitoringInterval: 5000,
                alertThresholds: {
                    cpuUsage: 80,
                    memoryUsage: 85,
                    responseTime: 5000
                }
            }
        };
        
        const configPath = `./config/trae-ide-${this.options.environment}.json`;
        await fs.writeFile(configPath, JSON.stringify(configTemplate, null, 2));
        this.log(`✓ 生成配置文件: ${configPath}`);
        
        // 创建环境变量文件
        const envContent = `# Trae IDE 集成环境变量
NODE_ENV=${this.options.environment}
MEMORY_CONFIG_PATH=${configPath}
LOG_LEVEL=${configTemplate.logLevel}
DATA_PATH=${configTemplate.dataPath}
`;
        
        await fs.writeFile('./.env.trae-ide', envContent);
        this.log('✓ 生成环境变量文件: .env.trae-ide');
    }

    /**
     * 安装组件
     */
    async installComponents() {
        this.log('编译 TypeScript 代码...');
        
        try {
            // 检查是否存在 tsconfig.json
            await fs.access('./tsconfig.json');
            
            // 编译 TypeScript
            execSync('npx tsc', { stdio: this.options.verbose ? 'inherit' : 'pipe' });
            this.log('✓ TypeScript 编译完成');
            
        } catch (error) {
            if (error.code === 'ENOENT') {
                this.log('⚠️  未找到 tsconfig.json，跳过 TypeScript 编译');
            } else {
                throw new Error(`TypeScript 编译失败: ${error.message}`);
            }
        }
        
        // 验证关键文件
        const requiredFiles = [
            './src/index.ts',
            './src/integrations/trae-ide/TraeIDEIntegration.ts',
            './src/middleware/AutoRecordMiddleware.ts'
        ];
        
        for (const file of requiredFiles) {
            try {
                await fs.access(file);
                this.log(`✓ 验证文件: ${file}`);
            } catch {
                throw new Error(`缺少关键文件: ${file}`);
            }
        }
    }

    /**
     * 运行测试
     */
    async runTests() {
        this.log('运行集成测试...');
        
        try {
            // 运行测试脚本
            execSync('node test-auto-record-integration.js', { 
                stdio: this.options.verbose ? 'inherit' : 'pipe',
                cwd: process.cwd()
            });
            this.log('✅ 集成测试通过');
            
        } catch (error) {
            throw new Error(`集成测试失败: ${error.message}`);
        }
    }

    /**
     * 启动服务
     */
    async startServices() {
        this.log('验证服务启动...');
        
        // 创建测试脚本来验证服务
        const testScript = `
const { LongTermMemorySystem } = require('./src/index');

async function testService() {
    const system = new LongTermMemorySystem();
    
    try {
        await system.initialize({
            dataPath: './data/memories',
            traeIDEIntegration: { enabled: true }
        });
        
        const integration = system.getTraeIDEIntegration();
        const status = await integration.getStatus();
        
        console.log('✅ 服务启动成功');
        console.log('状态:', JSON.stringify(status, null, 2));
        
        await system.destroy();
        process.exit(0);
        
    } catch (error) {
        console.error('❌ 服务启动失败:', error.message);
        process.exit(1);
    }
}

testService();
`;
        
        await fs.writeFile('./temp-service-test.js', testScript);
        
        try {
            execSync('node temp-service-test.js', { 
                stdio: this.options.verbose ? 'inherit' : 'pipe' 
            });
            this.log('✅ 服务验证通过');
        } catch (error) {
            throw new Error(`服务启动验证失败: ${error.message}`);
        } finally {
            // 清理临时文件
            try {
                await fs.unlink('./temp-service-test.js');
            } catch {}
        }
    }

    /**
     * 验证部署
     */
    async validateDeployment() {
        this.log('执行部署验证...');
        
        const validationChecks = [
            { name: '配置文件', check: () => fs.access(`./config/trae-ide-${this.options.environment}.json`) },
            { name: '数据目录', check: () => fs.access('./data/memories') },
            { name: '日志目录', check: () => fs.access('./logs') },
            { name: '主入口文件', check: () => fs.access('./src/index.ts') }
        ];
        
        for (const { name, check } of validationChecks) {
            try {
                await check();
                this.log(`✓ ${name} 验证通过`);
            } catch {
                throw new Error(`${name} 验证失败`);
            }
        }
        
        this.log('🎯 所有验证检查通过');
    }

    /**
     * 生成部署报告
     */
    async generateDeploymentReport(success, duration, completedSteps, error = null) {
        const report = {
            deployment: {
                success,
                timestamp: new Date().toISOString(),
                duration: Math.round(duration / 1000),
                environment: this.options.environment,
                completedSteps,
                totalSteps: this.deploymentSteps.length
            },
            configuration: {
                configPath: this.options.configPath,
                skipTest: this.options.skipTest,
                verbose: this.options.verbose
            },
            system: {
                nodeVersion: process.version,
                platform: process.platform,
                arch: process.arch
            }
        };
        
        if (error) {
            report.error = {
                message: error.message,
                stack: error.stack
            };
        }
        
        const reportPath = `./logs/deployment-report-${Date.now()}.json`;
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
        
        console.log(`📋 部署报告已生成: ${reportPath}`);
    }

    /**
     * 日志输出
     */
    log(message) {
        if (this.options.verbose) {
            console.log(`[${new Date().toISOString()}] ${message}`);
        } else {
            console.log(message);
        }
    }
}

// 命令行参数解析
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {};
    
    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        
        switch (arg) {
            case '--config':
                options.configPath = args[++i];
                break;
            case '--env':
                options.environment = args[++i];
                break;
            case '--skip-test':
                options.skipTest = true;
                break;
            case '--verbose':
                options.verbose = true;
                break;
            case '--help':
                console.log(`
Trae IDE 集成部署脚本

使用方法:
  node scripts/deploy-trae-integration.js [options]

选项:
  --config <path>    指定配置文件路径
  --env <env>        指定环境 (dev/prod)
  --skip-test        跳过测试
  --verbose          详细输出
  --help             显示帮助信息

示例:
  node scripts/deploy-trae-integration.js --env prod --verbose
  node scripts/deploy-trae-integration.js --skip-test --config ./custom-config.yaml
`);
                process.exit(0);
                break;
            default:
                console.warn(`未知参数: ${arg}`);
        }
    }
    
    return options;
}

// 主函数
async function main() {
    try {
        const options = parseArgs();
        const deployment = new TraeIDEDeployment(options);
        await deployment.deploy();
    } catch (error) {
        console.error('❌ 部署脚本执行失败:', error.message);
        process.exit(1);
    }
}

// 如果直接运行此脚本
if (require.main === module) {
    main();
}

module.exports = { TraeIDEDeployment };