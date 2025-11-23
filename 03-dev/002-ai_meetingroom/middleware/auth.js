// 基础身份认证中间件
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { config } = require('../config');

// JWT工具函数
const generateToken = (payload, expiresIn = '24h') => {
  return jwt.sign(payload, config.security.jwtSecret, { expiresIn });
};

const verifyToken = (token) => {
  try {
    return jwt.verify(token, config.security.jwtSecret);
  } catch (error) {
    return null;
  }
};

// 简单的用户模拟（生产环境应该使用数据库）
const users = new Map();

// 创建默认管理员用户
const createDefaultUser = async () => {
  const defaultPassword = await bcrypt.hash('admin123', 10);
  users.set('admin', {
    id: 'admin',
    username: 'admin',
    password: defaultPassword,
    role: 'admin',
    createdAt: new Date()
  });
};

// JWT认证中间件
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ 
      error: '访问令牌缺失',
      code: 'TOKEN_MISSING'
    });
  }

  const decoded = verifyToken(token);
  if (!decoded) {
    return res.status(403).json({ 
      error: '无效的访问令牌',
      code: 'INVALID_TOKEN'
    });
  }

  req.user = decoded;
  next();
};

// 可选认证中间件（用于WebSocket）
const optionalAuth = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (token) {
    const decoded = verifyToken(token);
    if (decoded) {
      req.user = decoded;
    }
  }
  
  next();
};

// 角色权限检查
const requireRole = (roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ 
        error: '需要身份认证',
        code: 'AUTH_REQUIRED'
      });
    }

    const userRole = req.user.role;
    const allowedRoles = Array.isArray(roles) ? roles : [roles];
    
    if (!allowedRoles.includes(userRole)) {
      return res.status(403).json({ 
        error: '权限不足',
        code: 'INSUFFICIENT_PERMISSIONS',
        required: allowedRoles,
        current: userRole
      });
    }

    next();
  };
};

// 基础认证路由
const authRoutes = (req, res) => {
  const { action, username, password } = req.body;

  switch (action) {
    case 'login':
      return handleLogin(username, password, res);
    
    case 'register':
      return handleRegister(username, password, res);
    
    case 'verify':
      return handleVerifyToken(req, res);
    
    default:
      return res.status(400).json({
        error: '无效的认证操作',
        code: 'INVALID_AUTH_ACTION'
      });
  }
};

// 登录处理
const handleLogin = async (username, password, res) => {
  if (!username || !password) {
    return res.status(400).json({
      error: '用户名和密码不能为空',
      code: 'MISSING_CREDENTIALS'
    });
  }

  const user = users.get(username);
  if (!user) {
    return res.status(401).json({
      error: '用户名或密码错误',
      code: 'INVALID_CREDENTIALS'
    });
  }

  const isValidPassword = await bcrypt.compare(password, user.password);
  if (!isValidPassword) {
    return res.status(401).json({
      error: '用户名或密码错误',
      code: 'INVALID_CREDENTIALS'
    });
  }

  const token = generateToken({
    id: user.id,
    username: user.username,
    role: user.role
  });

  res.json({
    success: true,
    token,
    user: {
      id: user.id,
      username: user.username,
      role: user.role
    }
  });
};

// 注册处理
const handleRegister = async (username, password, res) => {
  if (!username || !password) {
    return res.status(400).json({
      error: '用户名和密码不能为空',
      code: 'MISSING_CREDENTIALS'
    });
  }

  if (users.has(username)) {
    return res.status(409).json({
      error: '用户名已存在',
      code: 'USERNAME_EXISTS'
    });
  }

  if (password.length < 6) {
    return res.status(400).json({
      error: '密码长度至少6位',
      code: 'WEAK_PASSWORD'
    });
  }

  try {
    const hashedPassword = await bcrypt.hash(password, 10);
    const newUser = {
      id: username,
      username,
      password: hashedPassword,
      role: 'user',
      createdAt: new Date()
    };

    users.set(username, newUser);

    const token = generateToken({
      id: newUser.id,
      username: newUser.username,
      role: newUser.role
    });

    res.status(201).json({
      success: true,
      token,
      user: {
        id: newUser.id,
        username: newUser.username,
        role: newUser.role
      }
    });
  } catch (error) {
    res.status(500).json({
      error: '注册失败',
      code: 'REGISTRATION_FAILED',
      details: error.message
    });
  }
};

// 令牌验证
const handleVerifyToken = (req, res) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({
      valid: false,
      error: '令牌缺失'
    });
  }

  const decoded = verifyToken(token);
  if (!decoded) {
    return res.status(403).json({
      valid: false,
      error: '无效令牌'
    });
  }

  res.json({
    valid: true,
    user: decoded
  });
};

// 初始化默认用户
createDefaultUser();

module.exports = {
  generateToken,
  verifyToken,
  authenticateToken,
  optionalAuth,
  requireRole,
  authRoutes,
  users
};