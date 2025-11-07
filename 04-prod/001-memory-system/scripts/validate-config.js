#!/usr/bin/env node

/**
 * YDS-Lab 长记忆系统配置验证脚本
 * 
 * 验证memory-config.yaml配置文件的正确性
 */

const fs = require('fs-extra');
const path = require('path');
const yaml = require('yaml');

// 简单的颜色输出函数，替代chalk
const colors = {
  blue: (text) => `\x1b[34m${text}\x1b[0m`,
  green: (text) => `\x1b[32m${text}\x1b[0m`,
  yellow: (text) => `\x1b[33m${text}\x1b[0m`,
  red: (text) => `\x1b[31m${text}\x1b[0m`,
  gray: (text) => `\x1b[90m${text}\x1b[0m`
};

const chalk = colors;

class ConfigValidator {
  constructor() {
    this.configPath = path.join(process.cwd(), 'memory-config.yaml');
    this.errors = [];
    this.warnings = [];
  }

  async validate() {
    console.log(chalk.blue('🔍 验证YDS-Lab长记忆系统配置...'));
    
    try {
      // 检查配置文件是否存在
      if (!await fs.pathExists(this.configPath)) {
        throw new Error('配置文件 memory-config.yaml 不存在');
      }

      // 读取并解析配置文件
      const configContent = await fs.readFile(this.configPath, 'utf8');
      const config = yaml.parse(configContent);

      // 验证配置结构
      this.validateSystemConfig(config.system);
      this.validateStorageConfig(config.storage);
      this.validateRulesConfig(config.rules);
      this.validateKnowledgeGraphConfig(config.knowledge_graph);
      this.validateMemoryRetrievalConfig(config.memory_retrieval);
      this.validatePerformanceConfig(config.performance);
      this.validateLoggingConfig(config.logging);
      this.validateIntegrationConfig(config.integration);

      // 输出验证结果
      this.outputResults();

    } catch (error) {
      console.error(chalk.red('❌ 配置验证失败：'), error.message);
      process.exit(1);
    }
  }

  validateSystemConfig(system) {
    if (!system) {
      this.errors.push('缺少 system 配置节');
      return;
    }

    if (!system.name) {
      this.errors.push('system.name 不能为空');
    }

    if (!system.version) {
      this.errors.push('system.version 不能为空');
    }

    if (!['development', 'production', 'test'].includes(system.environment)) {
      this.warnings.push('system.environment 应该是 development, production 或 test 之一');
    }
  }

  validateStorageConfig(storage) {
    if (!storage) {
      this.errors.push('缺少 storage 配置节');
      return;
    }

    const requiredPaths = ['memory_path', 'knowledge_graph_path', 'rules_path', 'cache_path'];
    for (const pathKey of requiredPaths) {
      if (!storage[pathKey]) {
        this.errors.push(`storage.${pathKey} 不能为空`);
      }
    }
  }

  validateRulesConfig(rules) {
    if (!rules) {
      this.warnings.push('缺少 rules 配置节');
      return;
    }

    if (!rules.scan_paths || !Array.isArray(rules.scan_paths)) {
      this.errors.push('rules.scan_paths 必须是数组');
    }

    if (rules.cache && rules.cache.ttl && rules.cache.ttl < 60) {
      this.warnings.push('rules.cache.ttl 建议不少于60秒');
    }
  }

  validateKnowledgeGraphConfig(knowledgeGraph) {
    if (!knowledgeGraph) {
      this.warnings.push('缺少 knowledge_graph 配置节');
      return;
    }

    if (!knowledgeGraph.node_types || !Array.isArray(knowledgeGraph.node_types)) {
      this.errors.push('knowledge_graph.node_types 必须是数组');
    }

    if (!knowledgeGraph.relation_types || !Array.isArray(knowledgeGraph.relation_types)) {
      this.errors.push('knowledge_graph.relation_types 必须是数组');
    }

    if (knowledgeGraph.optimization && knowledgeGraph.optimization.max_nodes) {
      if (knowledgeGraph.optimization.max_nodes < 1000) {
        this.warnings.push('knowledge_graph.optimization.max_nodes 建议不少于1000');
      }
    }
  }

  validateMemoryRetrievalConfig(memoryRetrieval) {
    if (!memoryRetrieval) {
      this.warnings.push('缺少 memory_retrieval 配置节');
      return;
    }

    if (memoryRetrieval.similarity_threshold) {
      if (memoryRetrieval.similarity_threshold < 0 || memoryRetrieval.similarity_threshold > 1) {
        this.errors.push('memory_retrieval.similarity_threshold 必须在0-1之间');
      }
    }

    if (memoryRetrieval.strategy) {
      if (!['semantic', 'keyword', 'hybrid'].includes(memoryRetrieval.strategy)) {
        this.errors.push('memory_retrieval.strategy 必须是 semantic, keyword 或 hybrid 之一');
      }
    }
  }

  validatePerformanceConfig(performance) {
    if (!performance) {
      this.warnings.push('缺少 performance 配置节');
      return;
    }

    if (performance.interval && performance.interval < 30) {
      this.warnings.push('performance.interval 建议不少于30秒');
    }

    if (performance.thresholds) {
      if (performance.thresholds.memory_usage && 
          (performance.thresholds.memory_usage < 0 || performance.thresholds.memory_usage > 1)) {
        this.errors.push('performance.thresholds.memory_usage 必须在0-1之间');
      }
    }
  }

  validateLoggingConfig(logging) {
    if (!logging) {
      this.warnings.push('缺少 logging 配置节');
      return;
    }

    if (logging.level) {
      if (!['debug', 'info', 'warn', 'error'].includes(logging.level)) {
        this.errors.push('logging.level 必须是 debug, info, warn 或 error 之一');
      }
    }

    if (logging.format) {
      if (!['json', 'text'].includes(logging.format)) {
        this.warnings.push('logging.format 建议是 json 或 text 之一');
      }
    }
  }

  validateIntegrationConfig(integration) {
    if (!integration) {
      this.warnings.push('缺少 integration 配置节');
      return;
    }

    if (integration.yds_lab) {
      if (!integration.yds_lab.projects_path) {
        this.warnings.push('integration.yds_lab.projects_path 建议配置');
      }
      if (!integration.yds_lab.agents_path) {
        this.warnings.push('integration.yds_lab.agents_path 建议配置');
      }
    }
  }

  outputResults() {
    console.log('');
    
    if (this.errors.length === 0 && this.warnings.length === 0) {
      console.log(chalk.green('✅ 配置验证通过！'));
    } else {
      if (this.errors.length > 0) {
        console.log(chalk.red('❌ 发现配置错误：'));
        this.errors.forEach(error => {
          console.log(chalk.red(`  • ${error}`));
        });
      }

      if (this.warnings.length > 0) {
        console.log(chalk.yellow('⚠️  配置警告：'));
        this.warnings.forEach(warning => {
          console.log(chalk.yellow(`  • ${warning}`));
        });
      }

      if (this.errors.length > 0) {
        console.log('');
        console.log(chalk.red('请修复配置错误后重新验证'));
        process.exit(1);
      } else {
        console.log('');
        console.log(chalk.green('✅ 配置验证通过（有警告）'));
      }
    }
  }
}

// 运行验证
if (require.main === module) {
  const validator = new ConfigValidator();
  validator.validate().catch(console.error);
}

module.exports = ConfigValidator;