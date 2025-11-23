// Jest测试环境设置
const { config } = require('../config');

// 设置测试环境变量
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-jwt-secret-key';
process.env.OPENAI_API_KEY = 'test-openai-api-key';
process.env.PORT = '3001'; // 使用不同的端口避免冲突

// 全局测试工具
global.testUtils = {
  // 创建模拟请求对象
  createMockReq: (overrides = {}) => ({
    headers: {},
    body: {},
    query: {},
    params: {},
    user: null,
    ...overrides
  }),

  // 创建模拟响应对象
  createMockRes: () => {
    const res = {
      statusCode: 200,
      jsonData: null,
      status: function(code) {
        this.statusCode = code;
        return this;
      },
      json: function(data) {
        this.jsonData = data;
        return this;
      },
      send: function(data) {
        this.jsonData = data;
        return this;
      }
    };
    return res;
  },

  // 延迟函数
  delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  // 模拟异步操作
  mockAsync: (data, delay = 0) => {
    return new Promise(resolve => {
      setTimeout(() => resolve(data), delay);
    });
  }
};

// 测试前的全局设置
beforeAll(() => {
  console.log('🧪 开始会议室系统测试套件');
});

// 测试后的全局清理
afterAll(() => {
  console.log('✅ 测试套件完成');
});

// 每个测试前的设置
beforeEach(() => {
  jest.clearAllMocks();
  jest.resetModules();
});

// 每个测试后的清理
afterEach(() => {
  // 清理任何全局状态
  if (global.io && global.io.close) {
    global.io.close();
  }
});