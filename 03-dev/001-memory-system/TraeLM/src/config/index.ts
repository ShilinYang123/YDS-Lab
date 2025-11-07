/**
 * 配置模块入口
 * 导出配置相关的所有功能
 */

export * from './defaults';
export * from './loader';
export * from './validator';

// 导出配置管理器
export { ConfigurationManager } from './manager';