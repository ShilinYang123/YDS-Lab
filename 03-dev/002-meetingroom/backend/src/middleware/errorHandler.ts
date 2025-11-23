import { Request, Response, NextFunction } from 'express';
import { errorLogger } from '../utils/logger';

export class AppError extends Error {
  statusCode: number;
  isOperational: boolean;
  code: string | undefined;

  constructor(message: string, statusCode: number = 500, code?: string) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;
    this.code = code ?? undefined;
    Error.captureStackTrace(this, this.constructor);
    this.name = 'AppError';
  }
}

export const errorHandler = (
  err: AppError | Error,
  req: Request,
  res: Response,
  _next: NextFunction
): void => {
  // no-op

  // 默认错误
  let statusCode = (err as any).statusCode || 500;
  let message = err.message || 'Internal Server Error';

  // JWT错误
  if (err.name === 'JsonWebTokenError') {
    statusCode = 401;
    message = 'Invalid token';
  }

  // JWT过期错误
  if (err.name === 'TokenExpiredError') {
    statusCode = 401;
    message = 'Token expired';
  }

  // 验证错误
  if (err.name === 'ValidationError') {
    statusCode = 400;
    message = 'Validation Error';
  }

  // 数据库错误
  if (err.name === 'DatabaseError') {
    statusCode = 500;
    message = 'Database Error';
  }

  // 记录错误日志
  errorLogger(err, {
    url: req.originalUrl,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    userId: (req as any).user?.id
  });

  // 开发环境返回详细错误信息
  if ((process.env['NODE_ENV'] || 'development') === 'development') {
    res.status(statusCode).json({
      success: false,
      error: {
        message,
        stack: err.stack,
        name: err.name
      },
      timestamp: new Date().toISOString()
    });
  } else {
    // 生产环境只返回基本信息
    res.status(statusCode).json({
      success: false,
      error: {
        message: statusCode === 500 ? 'Internal Server Error' : message
      },
      timestamp: new Date().toISOString()
    });
  }
};

// 404错误处理
export const notFound = (req: Request, _res: Response, next: NextFunction): void => {
  const error = new Error(`Not Found - ${req.originalUrl}`) as AppError;
  error.statusCode = 404;
  next(error);
};

// 异步错误处理包装器
export const asyncHandler = (fn: Function) => (req: Request, res: Response, next: NextFunction) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// 创建自定义错误
export class CustomError extends AppError {
  constructor(message: string, statusCode: number = 500, code?: string) {
    super(message, statusCode, code);
    this.name = 'CustomError';
  }
}

// 验证错误
export class ValidationError extends CustomError {
  constructor(message: string) {
    super(message, 400);
    this.name = 'ValidationError';
  }
}

// 认证错误
export class AuthenticationError extends CustomError {
  constructor(message: string = 'Authentication failed') {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

// 授权错误
export class AuthorizationError extends CustomError {
  constructor(message: string = 'Access denied') {
    super(message, 403);
    this.name = 'AuthorizationError';
  }
}

// 资源未找到错误
export class NotFoundError extends CustomError {
  constructor(resource: string = 'Resource') {
    super(`${resource} not found`, 404);
    this.name = 'NotFoundError';
  }
}