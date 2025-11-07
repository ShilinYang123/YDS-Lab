/**
 * Jest测试环境设置文件
 * 
 * @description 配置测试全局环境，包括模拟、全局变量等
 * @author 高级软件专家
 */

import { jest } from '@jest/globals';

// 设置测试超时时间
jest.setTimeout(10000);

// 环境变量模拟
process.env['NODE_ENV'] = 'test';
process.env['TRAE_ENV'] = 'test';

// 全局测试配置
global.console = {
  ...console,
  // 在测试中静默某些日志
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: console.warn,
  error: console.error,
};

// 模拟Trae SDK
jest.mock('@traejs/sdk', () => ({
  TraeAgent: jest.fn().mockImplementation(() => ({
    initialize: jest.fn(),
    execute: jest.fn(),
    getStatus: jest.fn(),
    stop: jest.fn()
  })),
  TraeLogger: jest.fn().mockImplementation(() => ({
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn(),
    debug: jest.fn()
  }))
}), { virtual: true });

// 测试前的全局设置
beforeAll(() => {
  // 初始化测试环境
});

// 每个测试前的设置
beforeEach(() => {
  // 清除所有模拟
  jest.clearAllMocks();
});

// 每个测试后的清理
afterEach(() => {
  // 清理测试数据
});

// 测试后的全局清理
afterAll(() => {
  // 清理全局资源
});