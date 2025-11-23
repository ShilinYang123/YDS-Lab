import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { query } from '../config/database';
import { jwtConfig } from '../config/jwt';
import { AuthenticationError, AuthorizationError } from './errorHandler';
import { logger } from '../utils/logger';

export interface AuthRequest extends Request {
  user?: {
    id: string;
    username: string;
    email: string;
    role: string;
  };
}

// JWT认证中间件
export const authenticate = async (
  req: AuthRequest,
  _res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new AuthenticationError('No token provided');
    }

    const token = authHeader.substring(7);
    
    // 验证JWT令牌
    const decoded = jwt.verify(token, jwtConfig.secret) as any;
    
    // 查询用户确保仍然存在且活跃
    const result = await query<{ id: string; username: string; email: string; role: string; is_active: number }>(
      'SELECT id, username, email, role, 1 as is_active FROM users WHERE id = $1',
      [decoded.userId]
    );
    
    if (result.rows.length === 0) {
      throw new AuthenticationError('User not found');
    }
    
    const user = result.rows[0] as any;
    
    if (!user.is_active) {
      throw new AuthenticationError('User account is inactive');
    }
    
    // 附加用户信息到请求对象
    req.user = {
      id: user.id,
      username: user.username,
      email: user.email,
      role: user.role
    };
    
    logger.info('User authenticated', {
      userId: user.id,
      username: user.username,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
    
    next();
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      throw new AuthenticationError('Token expired');
    } else if (error instanceof jwt.JsonWebTokenError) {
      throw new AuthenticationError('Invalid token');
    }
    
    logger.error('Authentication failed', {
      error: error instanceof Error ? error.message : 'Unknown error',
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
    
    next(error);
  }
};

// 角色权限检查
export const authorize = (roles: string[]) => {
  return (req: AuthRequest, _res: Response, next: NextFunction): void => {
    if (!req.user) {
      throw new AuthenticationError('User not authenticated');
    }
    
    if (!roles.includes(req.user.role)) {
      logger.warn('Authorization failed', {
        userId: req.user.id,
        username: req.user.username,
        requiredRoles: roles,
        userRole: req.user.role,
        ip: req.ip
      });
      
      throw new AuthorizationError(`Access denied. Required roles: ${roles.join(', ')}`);
    }
    
    next();
  };
};

export const requireRole = authorize;
export const authMiddleware = authenticate;

// WebSocket认证
export const authenticateSocket = async (token: string): Promise<any> => {
  try {
    const decoded = jwt.verify(token, jwtConfig.secret) as any;
    
    // 查询用户
    const result = await query<any>(
      'SELECT id, username, email, role, is_active FROM users WHERE id = $1',
      [decoded.userId]
    );
    
    if (result.rows.length === 0) {
      throw new AuthenticationError('User not found');
    }
    
    const user = result.rows[0];
    
    if (!user.is_active) {
      throw new AuthenticationError('User account is inactive');
    }
    
    return {
      id: user.id,
      username: user.username,
      email: user.email,
      role: user.role
    };
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      throw new AuthenticationError('Token expired');
    } else if (error instanceof jwt.JsonWebTokenError) {
      throw new AuthenticationError('Invalid token');
    }
    throw error;
  }
};

// 资源权限检查
export const checkResourcePermission = async (
  userId: string,
  resourceType: string,
  resourceId: string,
  action: string
): Promise<boolean> => {
  try {
    // 这里可以实现更复杂的资源权限检查逻辑
    // 例如：检查用户是否是资源的所有者，或者是否有特定的权限
    
    switch (resourceType) {
      case 'meeting':
    const meetingResult = await query<any>(
      'SELECT creator_id FROM meeting_rooms WHERE id = $1',
      [resourceId]
    );
        
        if (meetingResult.rows.length === 0) {
          return false;
        }
        
        // 会议创建者有所有权限
        if (meetingResult.rows[0].creator_id === userId) {
          return true;
        }
        
        // 检查参与者权限
    const participantResult = await query<any>(
      'SELECT role FROM meeting_participants WHERE meeting_id = $1 AND user_id = $2',
      [resourceId, userId]
    );
        
        return participantResult.rows.length > 0;
        
      default:
        return false;
    }
  } catch (error) {
    logger.error('Resource permission check failed', {
      userId,
      resourceType,
      resourceId,
      action,
      error: error instanceof Error ? error.message : 'Unknown error'
    });
    return false;
  }
};