// 配置模块测试
const { config, validateConfig } = require('../../config');

describe('配置模块测试', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    // 保存原始环境变量
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    // 恢复原始环境变量
    process.env = originalEnv;
  });

  describe('配置加载', () => {
    test('应该正确加载默认配置', () => {
      expect(config).toBeDefined();
      expect(config.server).toBeDefined();
      expect(config.openai).toBeDefined();
      expect(config.security).toBeDefined();
    });

    test('应该使用环境变量覆盖默认配置', () => {
      process.env.PORT = '8080';
      process.env.NODE_ENV = 'production';
      
      // 重新加载配置
      jest.resetModules();
      const newConfig = require('../../config').config;
      
      expect(newConfig.server.port).toBe(8080);
      expect(newConfig.server.env).toBe('production');
    });
  });

  describe('配置验证', () => {
    test('应该验证必需的环境变量', () => {
      const errors = validateConfig();
      
      // 在测试环境中，OPENAI_API_KEY是可选的
      expect(Array.isArray(errors)).toBe(true);
    });

    test('应该检测缺失的必需变量', () => {
      process.env.OPENAI_API_KEY = '';
      
      const errors = validateConfig();
      const hasOpenAIError = errors.some(error => 
        error.includes('OPENAI_API_KEY') || 
        error.includes('OpenAI API')
      );
      
      expect(hasOpenAIError).toBe(true);
    });

    test('应该检测弱密钥', () => {
      process.env.JWT_SECRET = '123';
      
      const errors = validateConfig();
      const hasWeakKeyError = errors.some(error => 
        error.includes('JWT_SECRET') && error.includes('太简单')
      );
      
      expect(hasWeakKeyError).toBe(true);
    });
  });

  describe('安全配置', () => {
    test('应该包含安全相关配置', () => {
      expect(config.security).toMatchObject({
        jwtSecret: expect.any(String),
        bcryptRounds: expect.any(Number),
        rateLimitWindow: expect.any(Number),
        rateLimitMax: expect.any(Number)
      });
    });

    test('JWT密钥不应该使用默认值', () => {
      // 确保JWT密钥不是默认值
      expect(config.security.jwtSecret).not.toBe('your-super-secret-jwt-key');
    });
  });

  describe('多环境支持', () => {
    test('应该支持开发环境配置', () => {
      process.env.NODE_ENV = 'development';
      jest.resetModules();
      const devConfig = require('../../config').config;
      
      expect(devConfig.server.env).toBe('development');
    });

    test('应该支持生产环境配置', () => {
      process.env.NODE_ENV = 'production';
      jest.resetModules();
      const prodConfig = require('../../config').config;
      
      expect(prodConfig.server.env).toBe('production');
    });
  });
});