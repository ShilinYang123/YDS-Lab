// types from express are not needed here
import rateLimit from 'express-rate-limit';
import { logger } from '../utils/logger';

// 通用API限流
export const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100, // 限制每个IP每15分钟最多100个请求
  message: {
    error: 'Too many requests from this IP',
    message: 'Please try again later',
    code: 'RATE_LIMIT_EXCEEDED'
  },
  standardHeaders: true, // 返回RateLimit-*头信息
  legacyHeaders: false,
  handler: (req, res) => {
    logger.warn('Rate limit exceeded', {
      ip: req.ip,
      url: req.originalUrl,
      method: req.method,
      userAgent: req.get('User-Agent')
    });
    
    res.status(429).json({
      success: false,
      error: {
        message: 'Too many requests from this IP, please try again later',
        code: 'RATE_LIMIT_EXCEEDED',
        retryAfter: res.getHeader('Retry-After')
      }
    });
  }
});

// 认证相关限流
export const authRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 5, // 限制每个IP每15分钟最多5次认证尝试
  message: {
    error: 'Too many authentication attempts',
    message: 'Please try again later',
    code: 'AUTH_RATE_LIMIT_EXCEEDED'
  },
  skipSuccessfulRequests: true, // 成功的请求不计入限制
  handler: (req, res) => {
    logger.warn('Authentication rate limit exceeded', {
      ip: req.ip,
      email: req.body.email,
      userAgent: req.get('User-Agent')
    });
    
    res.status(429).json({
      success: false,
      error: {
        message: 'Too many authentication attempts, please try again later',
        code: 'AUTH_RATE_LIMIT_EXCEEDED',
        retryAfter: res.getHeader('Retry-After')
      }
    });
  }
});

// 文件上传限流
export const uploadRateLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1小时
  max: 10, // 限制每个IP每小时最多10次文件上传
  message: {
    error: 'Too many file uploads',
    message: 'Please try again later',
    code: 'UPLOAD_RATE_LIMIT_EXCEEDED'
  },
  handler: (req, res) => {
    logger.warn('Upload rate limit exceeded', {
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
    
    res.status(429).json({
      success: false,
      error: {
        message: 'Too many file uploads, please try again later',
        code: 'UPLOAD_RATE_LIMIT_EXCEEDED',
        retryAfter: res.getHeader('Retry-After')
      }
    });
  }
});

// WebSocket连接限流
export class WebSocketRateLimiter {
  private connections: Map<string, number> = new Map();
  private readonly maxConnections: number;
  private readonly windowMs: number;

  constructor(maxConnections = 10, windowMs = 60 * 1000) {
    this.maxConnections = maxConnections;
    this.windowMs = windowMs;
  }

  isAllowed(ip: string): boolean {
    const now = Date.now();
    const key = `${ip}:${Math.floor(now / this.windowMs)}`;
    
    const current = this.connections.get(key) || 0;
    
    if (current >= this.maxConnections) {
      logger.warn('WebSocket rate limit exceeded', { ip, current });
      return false;
    }
    
    this.connections.set(key, current + 1);
    
    // 清理过期的记录
    this.cleanup();
    
    return true;
  }

  private cleanup(): void {
    const now = Date.now();
    const cutoff = now - (this.windowMs * 2);
    
    for (const key of this.connections.keys()) {
      const part = key.split(':')[1] || '0';
      const keyTimestamp = parseInt(part, 10) * this.windowMs;
      if (keyTimestamp < cutoff) {
        this.connections.delete(key);
      }
    }
  }
}