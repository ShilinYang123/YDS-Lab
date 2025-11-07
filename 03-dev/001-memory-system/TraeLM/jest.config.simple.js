/**
 * 简化的Jest配置文件
 * 
 * @description 长期记忆系统测试配置
 * @author 高级软件专家
 */

module.exports = {
  // 测试环境
  preset: 'ts-jest',
  testEnvironment: 'node',

  // 根目录
  rootDir: '.',

  // 测试文件匹配模式
  testMatch: [
    '<rootDir>/tests/**/*.test.ts',
    '<rootDir>/tests/**/*.spec.ts'
  ],

  // 忽略的测试文件
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/'
  ],

  // TypeScript 转换
  transform: {
    '^.+\\.ts$': 'ts-jest'
  },

  // 文件扩展名
  moduleFileExtensions: [
    'ts',
    'js',
    'json'
  ],

  // 模块路径映射
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },

  // 覆盖率配置
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html'
  ],

  // 设置文件
  setupFilesAfterEnv: [
    '<rootDir>/tests/setup.ts'
  ],

  // 测试超时
  testTimeout: 30000,

  // 详细输出
  verbose: true,

  // 清除模拟
  clearMocks: true,
  restoreMocks: true,

  // 全局变量
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json'
    }
  }
};