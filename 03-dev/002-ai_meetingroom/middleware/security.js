// 安全中间件模块
const helmet = require('helmet');
const { body, validationResult } = require('express-validator');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

// CORS配置
const corsOptions = {
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true,
  optionsSuccessStatus: 200
};

// 速率限制配置
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100, // 限制每个IP 15分钟内最多100次请求
  message: {
    error: '请求过于频繁，请稍后再试',
    retryAfter: '15分钟'
  },
  standardHeaders: true,
  legacyHeaders: false
});

// 更严格的API速率限制
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 50, // API请求更严格
  message: {
    error: 'API请求过于频繁，请稍后再试',
    retryAfter: '15分钟'
  }
});

// 输入验证规则
const validationRules = {
  // 消息发送验证
  sendMessage: [
    body('content')
      .trim()
      .isLength({ min: 1, max: 1000 })
      .withMessage('消息内容长度必须在1-1000字符之间')
      .escape(), // XSS防护
    body('agentId')
      .optional()
      .isAlphanumeric()
      .withMessage('Agent ID必须是字母数字')
      .isLength({ min: 1, max: 50 })
      .withMessage('Agent ID长度必须在1-50字符之间')
  ],

  // 会议控制验证
  controlMeeting: [
    body('action')
      .isIn(['start', 'pause', 'resume', 'end'])
      .withMessage('无效的会议操作'),
    body('agentId')
      .optional()
      .isAlphanumeric()
      .withMessage('Agent ID必须是字母数字')
  ],

  // 演示文稿验证
  presentation: [
    body('presentationId')
      .isAlphanumeric()
      .withMessage('演示文稿ID必须是字母数字')
      .isLength({ min: 1, max: 100 })
      .withMessage('演示文稿ID长度必须在1-100字符之间')
  ]
};

// 验证结果处理中间件
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      error: '输入验证失败',
      details: errors.array().map(err => ({
        field: err.path,
        message: err.msg
      }))
    });
  }
  next();
};

// 安全头配置
const securityHeaders = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "ws:", "wss:"],
      fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"]
    }
  },
  hsts: {
    maxAge: 31536000, // 1年
    includeSubDomains: true,
    preload: true
  }
});

// 输入清理函数
const sanitizeInput = (input) => {
  if (typeof input !== 'string') return input;
  
  return input
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    .trim();
};

// 全局错误处理
const errorHandler = (err, req, res, next) => {
  console.error('错误详情:', err);
  
  // 开发环境返回详细错误
  if (process.env.NODE_ENV === 'development') {
    res.status(err.status || 500).json({
      error: err.message,
      stack: err.stack,
      details: err.details || null
    });
  } else {
    // 生产环境返回简化错误
    res.status(err.status || 500).json({
      error: '服务器内部错误',
      message: err.status === 400 ? err.message : '请稍后重试'
    });
  }
};

module.exports = {
  corsOptions,
  limiter,
  apiLimiter,
  validationRules,
  handleValidationErrors,
  securityHeaders,
  sanitizeInput,
  errorHandler
};