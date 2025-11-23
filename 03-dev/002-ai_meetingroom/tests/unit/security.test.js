// 安全中间件测试
const { 
  corsMiddleware, 
  rateLimitMiddleware, 
  securityHeaders, 
  inputSanitizer,
  errorHandler 
} = require('../../middleware/security');

describe('安全中间件测试', () => {
  let req, res, next;

  beforeEach(() => {
    req = global.testUtils.createMockReq();
    res = global.testUtils.createMockRes();
    next = jest.fn();
  });

  describe('CORS中间件', () => {
    test('应该正确配置CORS头', () => {
      corsMiddleware(req, res, next);
      
      expect(res.header).toBeDefined();
      expect(next).toHaveBeenCalled();
    });
  });

  describe('速率限制中间件', () => {
    test('应该限制请求频率', async () => {
      const rateLimit = rateLimitMiddleware();
      
      // 模拟多次请求
      for (let i = 0; i < 5; i++) {
        await rateLimit(req, res, next);
      }
      
      expect(next).toHaveBeenCalledTimes(5);
    });
  });

  describe('安全头中间件', () => {
    test('应该添加安全响应头', () => {
      securityHeaders(req, res, next);
      
      expect(res.removeHeader).toHaveBeenCalledWith('X-Powered-By');
      expect(next).toHaveBeenCalled();
    });
  });

  describe('输入清理函数', () => {
    test('应该清理XSS攻击代码', () => {
      const maliciousInput = '<script>alert("xss")</script>';
      const cleaned = inputSanitizer(maliciousInput);
      
      expect(cleaned).not.toContain('<script>');
      expect(cleaned).toBe('');
    });

    test('应该保留正常文本', () => {
      const normalInput = '正常的会议标题';
      const cleaned = inputSanitizer(normalInput);
      
      expect(cleaned).toBe(normalInput);
    });
  });

  describe('错误处理中间件', () => {
    test('应该处理应用错误', () => {
      const error = new Error('测试错误');
      errorHandler(error, req, res, next);
      
      expect(res.statusCode).toBe(500);
      expect(res.jsonData).toMatchObject({
        error: '服务器内部错误',
        code: 'INTERNAL_ERROR'
      });
    });

    test('应该处理验证错误', () => {
      const validationError = new Error('验证失败');
      validationError.name = 'ValidationError';
      errorHandler(validationError, req, res, next);
      
      expect(res.statusCode).toBe(400);
    });
  });
});