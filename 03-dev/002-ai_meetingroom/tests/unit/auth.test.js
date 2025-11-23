// 认证中间件测试
const { 
  generateToken, 
  verifyToken, 
  authenticateToken, 
  authRoutes,
  users 
} = require('../../middleware/auth');

describe('认证中间件测试', () => {
  const mockUser = {
    id: 'testuser',
    username: 'testuser',
    role: 'user'
  };

  describe('JWT令牌生成与验证', () => {
    test('应该生成有效的JWT令牌', () => {
      const token = generateToken(mockUser);
      
      expect(token).toBeDefined();
      expect(typeof token).toBe('string');
      expect(token.split('.')).toHaveLength(3); // JWT格式检查
    });

    test('应该验证有效的JWT令牌', () => {
      const token = generateToken(mockUser);
      const decoded = verifyToken(token);
      
      expect(decoded).toMatchObject(mockUser);
    });

    test('应该拒绝无效的JWT令牌', () => {
      const invalidToken = 'invalid.token.here';
      const decoded = verifyToken(invalidToken);
      
      expect(decoded).toBeNull();
    });
  });

  describe('认证中间件', () => {
    let req, res, next;

    beforeEach(() => {
      req = global.testUtils.createMockReq();
      res = global.testUtils.createMockRes();
      next = jest.fn();
    });

    test('应该通过有效的认证令牌', () => {
      const token = generateToken(mockUser);
      req.headers['authorization'] = `Bearer ${token}`;
      
      authenticateToken(req, res, next);
      
      expect(req.user).toMatchObject(mockUser);
      expect(next).toHaveBeenCalled();
    });

    test('应该拒绝缺失的认证令牌', () => {
      authenticateToken(req, res, next);
      
      expect(res.statusCode).toBe(401);
      expect(res.jsonData).toMatchObject({
        error: '访问令牌缺失',
        code: 'TOKEN_MISSING'
      });
      expect(next).not.toHaveBeenCalled();
    });

    test('应该拒绝无效的认证令牌', () => {
      req.headers['authorization'] = 'Bearer invalid.token';
      
      authenticateToken(req, res, next);
      
      expect(res.statusCode).toBe(403);
      expect(res.jsonData).toMatchObject({
        error: '无效的访问令牌',
        code: 'INVALID_TOKEN'
      });
      expect(next).not.toHaveBeenCalled();
    });
  });

  describe('认证路由', () => {
    let req, res;

    beforeEach(() => {
      req = global.testUtils.createMockReq();
      res = global.testUtils.createMockRes();
    });

    test('应该处理登录请求', async () => {
      req.body = {
        action: 'login',
        username: 'admin',
        password: 'admin123'
      };
      
      await authRoutes(req, res);
      
      expect(res.jsonData.success).toBe(true);
      expect(res.jsonData.token).toBeDefined();
      expect(res.jsonData.user.username).toBe('admin');
    });

    test('应该拒绝错误的登录凭据', async () => {
      req.body = {
        action: 'login',
        username: 'admin',
        password: 'wrongpassword'
      };
      
      await authRoutes(req, res);
      
      expect(res.statusCode).toBe(401);
      expect(res.jsonData.code).toBe('INVALID_CREDENTIALS');
    });

    test('应该处理注册请求', async () => {
      req.body = {
        action: 'register',
        username: 'newuser',
        password: 'password123'
      };
      
      await authRoutes(req, res);
      
      expect(res.statusCode).toBe(201);
      expect(res.jsonData.success).toBe(true);
      expect(res.jsonData.token).toBeDefined();
    });

    test('应该拒绝重复的注册用户名', async () => {
      req.body = {
        action: 'register',
        username: 'admin',
        password: 'password123'
      };
      
      await authRoutes(req, res);
      
      expect(res.statusCode).toBe(409);
      expect(res.jsonData.code).toBe('USERNAME_EXISTS');
    });

    test('应该处理令牌验证', async () => {
      const token = generateToken(mockUser);
      req.headers['authorization'] = `Bearer ${token}`;
      req.body = { action: 'verify' };
      
      await authRoutes(req, res);
      
      expect(res.jsonData.valid).toBe(true);
      expect(res.jsonData.user).toMatchObject(mockUser);
    });
  });
});