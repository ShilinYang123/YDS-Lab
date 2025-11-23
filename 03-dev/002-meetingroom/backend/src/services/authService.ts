import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { getRedisClient } from '../config/database';
import UserModel, { User } from '../models/User';
import { logger } from '../utils/logger';
import { AppError } from '../middleware/errorHandler';

interface JWTPayload {
  userId: string;
  username: string;
  email: string;
  role: string;
  sessionId: string;
  iat: number;
  exp: number;
}

export interface RefreshTokenPayload {
  userId: string;
  sessionId: string;
  iat: number;
  exp: number;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginData {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  role?: 'admin' | 'manager' | 'user';
  department?: string;
  phone?: string;
}

export class AuthService {
  private static readonly ACCESS_TOKEN_SECRET = process.env['JWT_ACCESS_SECRET'] || 'your-access-secret-key';
  private static readonly REFRESH_TOKEN_SECRET = process.env['JWT_REFRESH_SECRET'] || 'your-refresh-secret-key';
  private static readonly ACCESS_TOKEN_EXPIRES_IN = process.env['JWT_ACCESS_EXPIRES_IN'] || '15m';
  private static readonly REFRESH_TOKEN_EXPIRES_IN = process.env['JWT_REFRESH_EXPIRES_IN'] || '7d';

  /**
   * 用户登录
   */
  static async login(data: LoginData): Promise<AuthTokens> {
    const { username, password, rememberMe = false } = data;

    try {
      logger.info('登录请求接收', { username, rememberMe });
      // 验证用户凭据
      const user = await UserModel.findByUsername(username);
      logger.debug('登录用户查询结果', { exists: !!user });
      if (!user) {
        throw new AppError('用户名或密码错误', 401, 'INVALID_CREDENTIALS');
      }

      // 验证密码
      const isPasswordValid = await UserModel.validatePassword(password, (user as any).password_hash);
      logger.debug('登录密码校验结果', { isPasswordValid });
      if (!isPasswordValid) {
        throw new AppError('用户名或密码错误', 401, 'INVALID_CREDENTIALS');
      }

      // 检查用户状态
      if (user.status !== 'active') {
        throw new AppError('账户已被禁用', 403, 'ACCOUNT_DISABLED');
      }

      // 生成会话ID
      const sessionId = uuidv4();

      // 生成访问令牌
      const accessToken = this.generateAccessToken(user, sessionId);
      logger.debug('访问令牌生成完成', { userId: user.id, sessionId });
      
      // 生成刷新令牌
      const refreshToken = this.generateRefreshToken(user.id, sessionId, rememberMe);
      logger.debug('刷新令牌生成完成', { userId: user.id, sessionId, rememberMe });

      // 将会话信息存储到Redis
      try {
        await this.storeSession(user.id, sessionId, refreshToken, rememberMe);
      } catch (e) {
        logger.warn('会话存储失败（已忽略）', { userId: user.id, sessionId, error: (e as Error).message });
      }

      // 更新最后登录时间
      await UserModel.updateLastLogin(user.id);
      logger.debug('最后登录时间已更新', { userId: user.id });

      logger.info('用户登录成功', { userId: user.id, username: user.username, sessionId });

      return {
        accessToken,
        refreshToken,
        expiresIn: this.parseExpiresIn(this.ACCESS_TOKEN_EXPIRES_IN)
      };
    } catch (error) {
      logger.error('用户登录失败', { username, error: (error as Error).message, stack: (error as Error).stack });
      throw error;
    }
  }

  /**
   * 用户注册
   */
  static async register(data: RegisterData): Promise<{ user: User; tokens: AuthTokens }> {
    const { username, email, password, role = 'user', department, phone } = data;

    try {
      logger.info('注册请求接收', { username, email, role });
      // 检查用户名是否已存在
      const existingUser = await UserModel.findByUsername(username);
      logger.debug('用户名查询结果', { exists: !!existingUser });
      if (existingUser) {
        throw new AppError('用户名已存在', 409, 'USERNAME_EXISTS');
      }

      // 检查邮箱是否已存在
      const existingEmail = await UserModel.findByEmail(email);
      logger.debug('邮箱查询结果', { exists: !!existingEmail });
      if (existingEmail) {
        throw new AppError('邮箱已被使用', 409, 'EMAIL_EXISTS');
      }

      // 创建用户
      const createData: any = {
        username,
        email,
        password,
        role
      };
      if (department !== undefined) createData.department = department;
      if (phone !== undefined) createData.phone = phone;

      const user = await UserModel.create(createData);
      logger.debug('用户创建完成', { userId: user.id });

      // 生成会话
      const sessionId = uuidv4();
      const accessToken = this.generateAccessToken(user, sessionId);
      const refreshToken = this.generateRefreshToken(user.id, sessionId, false);
      logger.debug('注册令牌生成完成', { userId: user.id, sessionId });

      // 存储会话
      try {
        await this.storeSession(user.id, sessionId, refreshToken, false);
      } catch (e) {
        logger.warn('会话存储失败（已忽略）', { userId: user.id, sessionId, error: (e as Error).message });
      }

      logger.info('用户注册成功', { userId: user.id, username: user.username });

      return {
        user,
        tokens: {
          accessToken,
          refreshToken,
          expiresIn: this.parseExpiresIn(this.ACCESS_TOKEN_EXPIRES_IN)
        }
      };
    } catch (error) {
      logger.error('用户注册失败', { username, email, error: (error as Error).message, stack: (error as Error).stack });
      throw error;
    }
  }

  /**
   * 刷新访问令牌
   */
  static async refreshToken(refreshToken: string): Promise<AuthTokens> {
    try {
      // 验证刷新令牌
      const payload = jwt.verify(refreshToken, this.REFRESH_TOKEN_SECRET) as RefreshTokenPayload;
      
      // 检查会话是否存在
      const sessionKey = `session:${payload.userId}:${payload.sessionId}`;
      const redisClient = getRedisClient();
      await redisClient.connect();
      
      const sessionData = await redisClient.get(sessionKey);
      if (!sessionData) {
        throw new AppError('会话已过期', 401, 'SESSION_EXPIRED');
      }

      const session = JSON.parse(sessionData);
      if (session.refreshToken !== refreshToken) {
        throw new AppError('无效的刷新令牌', 401, 'INVALID_REFRESH_TOKEN');
      }

      // 获取用户信息
      const user = await UserModel.findById(payload.userId);
      if (!user || user.status !== 'active') {
        throw new AppError('用户不存在或已被禁用', 401, 'USER_NOT_FOUND');
      }

      // 生成新的访问令牌
      const newAccessToken = this.generateAccessToken(user, payload.sessionId);
      
      // 更新会话的最后访问时间
      session.lastAccessTime = new Date().toISOString();
      await redisClient.setEx(sessionKey, this.parseExpiresInSeconds(this.REFRESH_TOKEN_EXPIRES_IN), JSON.stringify(session));

      logger.info('令牌刷新成功', { userId: user.id, sessionId: payload.sessionId });

      return {
        accessToken: newAccessToken,
        refreshToken, // 继续使用相同的刷新令牌
        expiresIn: this.parseExpiresIn(this.ACCESS_TOKEN_EXPIRES_IN)
      };
    } catch (error: any) {
      if (error?.name === 'JsonWebTokenError') {
        throw new AppError('无效的刷新令牌', 401, 'INVALID_REFRESH_TOKEN');
      }
      if (error?.name === 'TokenExpiredError') {
        throw new AppError('刷新令牌已过期', 401, 'REFRESH_TOKEN_EXPIRED');
      }
      logger.error('令牌刷新失败', { error: (error as Error).message });
      throw error;
    } finally {
      try { const redisClient = getRedisClient(); await redisClient.disconnect(); } catch {}
    }
  }

  /**
   * 用户登出
   */
  static async logout(userId: string, sessionId: string): Promise<void>;
  static async logout(refreshToken: string): Promise<void>;
  static async logout(arg1: string, arg2?: string): Promise<void> {
    if (arg2 === undefined) {
      const payload = jwt.verify(arg1, this.REFRESH_TOKEN_SECRET) as RefreshTokenPayload;
      return this.logout(payload.userId, payload.sessionId);
    }
    const userId = arg1;
    const sessionId = arg2!;
    const redisClient = getRedisClient();
    try {
      const sessionKey = `session:${userId}:${sessionId}`;
      await redisClient.connect();
      await redisClient.del(sessionKey);
      logger.info('用户登出成功', { userId, sessionId });
    } catch (error) {
      logger.error('用户登出失败', { userId, sessionId, error: (error as Error).message });
      throw new AppError('登出失败', 500, 'LOGOUT_FAILED');
    } finally {
      try { await redisClient.disconnect(); } catch {}
    }
  }

  /**
   * 验证访问令牌
   */
  static async verifyAccessToken(token: string): Promise<JWTPayload> {
    try {
      const payload = jwt.verify(token, this.ACCESS_TOKEN_SECRET) as JWTPayload;
      
      // 检查会话是否存在
      const sessionKey = `session:${payload.userId}:${payload.sessionId}`;
      const redisClient = getRedisClient();
      await redisClient.connect();
      
      const sessionData = await redisClient.get(sessionKey);
      if (!sessionData) {
        throw new AppError('会话已过期', 401, 'SESSION_EXPIRED');
      }

      return payload;
    } catch (error: any) {
      if (error?.name === 'JsonWebTokenError') {
        throw new AppError('无效的访问令牌', 401, 'INVALID_ACCESS_TOKEN');
      }
      if (error?.name === 'TokenExpiredError') {
        throw new AppError('访问令牌已过期', 401, 'ACCESS_TOKEN_EXPIRED');
      }
      throw error;
    } finally {
      try { const redisClient = getRedisClient(); await redisClient.disconnect(); } catch {}
    }
  }

  /**
   * 强制用户登出所有设备
   */
  static async forceLogoutAllDevices(userId: string): Promise<void> {
    const redisClient = getRedisClient();
    try {
      await redisClient.connect();
      
      // 获取用户的所有会话键
      const pattern = `session:${userId}:*`;
      const keys = await redisClient.keys(pattern);
      
      if (keys.length > 0) {
        await redisClient.del(keys);
      }
      
      logger.info('强制用户登出所有设备成功', { userId, sessionCount: keys.length });
    } catch (error) {
      logger.error('强制用户登出所有设备失败:', { userId, error: (error as Error).message });
      throw new AppError('强制登出失败', 500, 'FORCE_LOGOUT_FAILED');
    } finally {
      try { await redisClient.disconnect(); } catch {}
    }
  }

  static async getUserSessions(userId: string): Promise<any[]> {
    const redisClient = getRedisClient();
    try {
      await redisClient.connect();
      const pattern = `session:${userId}:*`;
      const keys = await redisClient.keys(pattern);
      const sessions: any[] = [];
      for (const key of keys) {
        const data = await redisClient.get(key);
        if (data) {
          try {
            sessions.push(JSON.parse(data));
          } catch {
            sessions.push({ raw: data });
          }
        }
      }
      return sessions;
    } finally {
      try { await redisClient.disconnect(); } catch {}
    }
  }

  /**
   * 生成访问令牌
   */
  private static generateAccessToken(user: User, sessionId: string): string {
    const payload: JWTPayload = {
      userId: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      sessionId,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + this.parseExpiresInSeconds(this.ACCESS_TOKEN_EXPIRES_IN)
    };

    return jwt.sign(payload, this.ACCESS_TOKEN_SECRET);
  }

  /**
   * 生成刷新令牌
   */
  private static generateRefreshToken(userId: string, sessionId: string, rememberMe: boolean): string {
    const expiresIn = rememberMe ? '30d' : this.REFRESH_TOKEN_EXPIRES_IN;
    const payload: RefreshTokenPayload = {
      userId,
      sessionId,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + this.parseExpiresInSeconds(expiresIn)
    };

    return jwt.sign(payload, this.REFRESH_TOKEN_SECRET);
  }

  /**
   * 存储会话信息
   */
  private static async storeSession(userId: string, sessionId: string, refreshToken: string, rememberMe: boolean): Promise<void> {
    const redisClient = getRedisClient();
    await redisClient.connect();
    
    const sessionKey = `session:${userId}:${sessionId}`;
    const sessionData = {
      userId,
      sessionId,
      refreshToken,
      rememberMe,
      createdAt: new Date().toISOString(),
      lastAccessTime: new Date().toISOString()
    };

    const expiresIn = rememberMe ? '30d' : this.REFRESH_TOKEN_EXPIRES_IN;
    await redisClient.setEx(sessionKey, this.parseExpiresInSeconds(expiresIn), JSON.stringify(sessionData));
  }

  /**
   * 解析过期时间（转换为秒）
   */
  private static parseExpiresInSeconds(expiresIn: string): number {
    const match = expiresIn.match(/^(\d+)([smhd])$/) as RegExpMatchArray | null;
    if (!match) {
      return 900; // 默认15分钟
    }

    const value = parseInt((match as RegExpMatchArray)[1] || '0', 10);
    const unit = (match as RegExpMatchArray)[2] || 'm';

    switch (unit) {
      case 's': return value;
      case 'm': return value * 60;
      case 'h': return value * 3600;
      case 'd': return value * 86400;
      default: return 900;
    }
  }

  /**
   * 解析过期时间（转换为毫秒）
   */
  private static parseExpiresIn(expiresIn: string): number {
    return this.parseExpiresInSeconds(expiresIn) * 1000;
  }

  /**
   * 支持通过刷新令牌登出（重载）
   */
  
}

export default AuthService;