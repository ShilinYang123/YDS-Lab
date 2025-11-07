module.exports = {
  // 测试环境
  preset: 'ts-jest',
  testEnvironment: 'node',

  // 根目录
  rootDir: '.',

  // 测试文件匹配模式
  testMatch: [
    '<rootDir>/tests/**/*.test.ts',
    '<rootDir>/tests/**/*.spec.ts',
    '<rootDir>/src/**/__tests__/**/*.ts',
    '<rootDir>/src/**/*.test.ts',
    '<rootDir>/src/**/*.spec.ts',
  ],

  // 忽略的测试文件
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/dist/',
    '<rootDir>/coverage/',
  ],

  // 模块文件扩展名
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],

  // 模块路径映射
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@/types/(.*)$': '<rootDir>/src/types/$1',
    '^@/utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@/services/(.*)$': '<rootDir>/src/services/$1',
    '^@/config/(.*)$': '<rootDir>/src/config/$1',
  },

  // 转换配置
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },

  // 覆盖率配置
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.test.ts',
    '!src/**/*.spec.ts',
    '!src/**/__tests__/**',
    '!src/index.ts',
  ],

  // 覆盖率报告格式
  coverageReporters: ['text', 'lcov', 'html', 'json'],

  // 覆盖率输出目录
  coverageDirectory: 'coverage',

  // 覆盖率阈值
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },

  // 设置文件
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],

  // 全局变量
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.json',
    },
  },

  // 清除模拟
  clearMocks: true,
  restoreMocks: true,

  // 详细输出
  verbose: true,

  // 测试超时
  testTimeout: 10000,

  // 错误处理
  errorOnDeprecated: true,

  // 监听模式配置
  watchman: true,
  watchPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/dist/',
    '<rootDir>/coverage/',
  ],

  // 报告器配置
  reporters: [
    'default',
    [
      'jest-junit',
      {
        outputDirectory: 'test-results',
        outputName: 'junit.xml',
        classNameTemplate: '{classname}',
        titleTemplate: '{title}',
        ancestorSeparator: ' › ',
        usePathForSuiteName: true,
      },
    ],
  ],

  // 模拟配置
  modulePathIgnorePatterns: ['<rootDir>/dist/'],

  // TypeScript 配置
  preset: 'ts-jest/presets/default',
  extensionsToTreatAsEsm: ['.ts'],
  
  // 环境变量
  testEnvironmentOptions: {
    NODE_ENV: 'test',
  },
};