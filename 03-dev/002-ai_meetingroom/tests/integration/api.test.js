// 集成测试 - API端点测试
const request = require('supertest');
const app = require('../../index'); // 假设主应用文件

describe('API集成测试', () => {
  let server;

  beforeAll(async () => {
    // 启动测试服务器
    server = app.listen(process.env.PORT || 3001);
  });

  afterAll(async () => {
    // 关闭测试服务器
    if (server) {
      await new Promise(resolve => server.close(resolve));
    }
  });

  describe('健康检查端点', () => {
    test('GET /health 应该返回服务状态', async () => {
      const response = await request(server)
        .get('/health')
        .expect(200);

      expect(response.body).toMatchObject({
        status: 'healthy',
        timestamp: expect.any(String)
      });
    });
  });

  describe('认证端点', () => {
    test('POST /api/auth 登录应该返回JWT令牌', async () => {
      const response = await request(server)
        .post('/api/auth')
        .send({
          action: 'login',
          username: 'admin',
          password: 'admin123'
        })
        .expect(200);

      expect(response.body).toMatchObject({
        success: true,
        token: expect.any(String),
        user: expect.objectContaining({
          username: 'admin',
          role: 'admin'
        })
      });
    });

    test('POST /api/auth 注册应该创建新用户', async () => {
      const response = await request(server)
        .post('/api/auth')
        .send({
          action: 'register',
          username: 'testuser',
          password: 'password123'
        })
        .expect(201);

      expect(response.body).toMatchObject({
        success: true,
        token: expect.any(String),
        user: expect.objectContaining({
          username: 'testuser',
          role: 'user'
        })
      });
    });

    test('POST /api/auth 应该拒绝无效凭据', async () => {
      const response = await request(server)
        .post('/api/auth')
        .send({
          action: 'login',
          username: 'admin',
          password: 'wrongpassword'
        })
        .expect(401);

      expect(response.body).toMatchObject({
        error: '用户名或密码错误',
        code: 'INVALID_CREDENTIALS'
      });
    });
  });

  describe('会议室API', () => {
    let authToken;

    beforeEach(async () => {
      // 获取认证令牌
      const authResponse = await request(server)
        .post('/api/auth')
        .send({
          action: 'login',
          username: 'admin',
          password: 'admin123'
        });

      authToken = authResponse.body.token;
    });

    test('GET /api/meetings 应该需要认证', async () => {
      const response = await request(server)
        .get('/api/meetings')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(Array.isArray(response.body)).toBe(true);
    });

    test('GET /api/meetings 应该拒绝无认证请求', async () => {
      const response = await request(server)
        .get('/api/meetings')
        .expect(401);

      expect(response.body).toMatchObject({
        error: '访问令牌缺失',
        code: 'TOKEN_MISSING'
      });
    });
  });

  describe('安全测试', () => {
    test('应该阻止XSS攻击', async () => {
      const response = await request(server)
        .post('/api/auth')
        .send({
          action: 'register',
          username: '<script>alert("xss")</script>',
          password: 'password123'
        })
        .expect(201);

      // 用户名应该被清理
      expect(response.body.user.username).not.toContain('<script>');
    });

    test('应该实施速率限制', async () => {
      const promises = [];
      
      // 发送多个请求以触发速率限制
      for (let i = 0; i < 10; i++) {
        promises.push(
          request(server)
            .post('/api/auth')
            .send({
              action: 'login',
              username: 'admin',
              password: 'wrongpassword'
            })
        );
      }

      const responses = await Promise.all(promises);
      
      // 检查是否有请求被速率限制
      const rateLimitedResponses = responses.filter(
        response => response.status === 429
      );
      
      // 至少应该有一些请求被限制
      expect(rateLimitedResponses.length).toBeGreaterThan(0);
    });
  });
});