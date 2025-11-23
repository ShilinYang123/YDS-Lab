import { Router, Request, Response, NextFunction } from 'express';
import { body, validationResult } from 'express-validator';
import AuthService from '../services/authService';
import { authMiddleware } from '../middleware/auth';
import { AppError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

const router = Router();

// 用户注册
router.post('/register', [
  body('username')
    .isLength({ min: 3, max: 50 })
    .withMessage('用户名长度必须在3-50个字符之间')
    .matches(/^[a-zA-Z0-9_]+$/)
    .withMessage('用户名只能包含字母、数字和下划线'),
  body('email')
    .isEmail()
    .withMessage('请输入有效的邮箱地址')
    .normalizeEmail(),
  body('password')
    .isLength({ min: 8 })
    .withMessage('密码长度至少为8个字符')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
    .withMessage('密码必须包含大小写字母、数字和特殊字符'),
  body('role')
    .optional()
    .isIn(['admin', 'manager', 'user'])
    .withMessage('角色必须是admin、manager或user'),
  body('department')
    .optional()
    .isLength({ max: 100 })
    .withMessage('部门名称不能超过100个字符'),
  body('phone')
    .optional()
    .matches(/^1[3-9]\d{9}$/)
    .withMessage('请输入有效的手机号码'),
], async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    // 验证输入
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      res.status(400).json({
        success: false,
        message: '输入验证失败',
        errors: errors.array(),
      });
      return;
    }

    const { username, email, password, role, department, phone } = req.body;

    // 注册用户
    const { user, tokens } = await AuthService.register({
      username,
      email,
      password,
      role,
      department,
      phone,
    });

    logger.info('用户注册成功', { userId: user.id, username });

    res.status(201).json({
      success: true,
      message: '注册成功',
      data: {
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          role: user.role,
          department: user.department,
          phone: user.phone,
          status: user.status,
          createdAt: user.created_at,
        },
        tokens,
      },
    });
    return;
  } catch (error) {
    if (error instanceof AppError) {
      res.status(error.statusCode).json({
        success: false,
        message: error.message,
        code: error.code,
      });
      return;
    }
    logger.error('注册请求处理失败:', error);
    next(error);
  }
});

// 用户登录
router.post('/login', [
  body('username')
    .notEmpty()
    .withMessage('用户名不能为空'),
  body('password')
    .notEmpty()
    .withMessage('密码不能为空'),
  body('rememberMe')
    .optional()
    .isBoolean()
    .withMessage('记住我必须是布尔值'),
], async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    // 验证输入
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      res.status(400).json({
        success: false,
        message: '输入验证失败',
        errors: errors.array(),
      });
      return;
    }

    const { username, password, rememberMe } = req.body;
    // const userAgent = req.get('User-Agent') || 'Unknown';
    const ip = req.ip || req.connection.remoteAddress || 'Unknown';

    // 用户登录
    const tokens = await AuthService.login({ username, password, rememberMe });

    logger.info('用户登录成功', { username, ip });

    res.json({
      success: true,
      message: '登录成功',
      data: {
        tokens,
      },
    });
    return;
  } catch (error) {
    if (error instanceof AppError) {
      res.status(error.statusCode).json({
        success: false,
        message: error.message,
        code: error.code,
      });
      return;
    }
    logger.error('登录请求处理失败:', error);
    next(error);
  }
});

// 刷新访问令牌
router.post('/refresh', [
  body('refreshToken')
    .notEmpty()
    .withMessage('刷新令牌不能为空'),
], async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    // 验证输入
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      res.status(400).json({
        success: false,
        message: '输入验证失败',
        errors: errors.array(),
      });
      return;
    }

  const { refreshToken } = req.body;

    // 刷新令牌
    const tokens = await AuthService.refreshToken(refreshToken);

    res.json({
      success: true,
      message: '令牌刷新成功',
      data: {
        tokens,
      },
    });
    return;
  } catch (error) {
    if (error instanceof AppError) {
      res.status(error.statusCode).json({
        success: false,
        message: error.message,
        code: error.code,
      });
      return;
    }
    logger.error('令牌刷新失败:', error);
    next(error);
  }
});

// 用户登出
router.post('/logout', [
  body('refreshToken')
    .notEmpty()
    .withMessage('刷新令牌不能为空'),
], async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    // 验证输入
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      res.status(400).json({
        success: false,
        message: '输入验证失败',
        errors: errors.array(),
      });
      return;
    }

  const { refreshToken } = req.body;

    // 用户登出（通过刷新令牌解析会话）
    await AuthService.logout(refreshToken);

    res.json({
      success: true,
      message: '登出成功',
    });
    return;
  } catch (error) {
    if (error instanceof AppError) {
      res.status(error.statusCode).json({
        success: false,
        message: error.message,
        code: error.code,
      });
      return;
    }
    logger.error('登出失败:', error);
    next(error);
  }
});

// 获取当前用户信息（需要认证）
router.get('/me', authMiddleware, async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const user = (req as any).user;

    res.json({
      success: true,
      message: '获取用户信息成功',
      data: {
        user: {
          id: user.id,
          username: user.username,
          email: user.email,
          role: user.role,
          department: user.department,
          phone: user.phone,
          avatar: user.avatar,
          status: user.status,
          lastLoginAt: user.last_login_at,
          createdAt: user.created_at,
          updatedAt: user.updated_at,
        },
      },
    });
    return;
  } catch (error) {
    logger.error('获取用户信息失败:', error);
    next(error);
  }
});

// 获取用户会话列表（需要认证）
router.get('/sessions', authMiddleware, async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const user = (req as any).user;

    // 获取用户会话
    const sessions = await AuthService.getUserSessions(user.id);

    res.json({
      success: true,
      message: '获取会话列表成功',
      data: {
        sessions,
      },
    });
    return;
  } catch (error) {
    logger.error('获取会话列表失败:', error);
    next(error);
  }
});

// 强制登出所有设备（需要认证）
router.post('/logout-all', authMiddleware, async (req: Request, res: Response, next: NextFunction): Promise<void> => {
  try {
    const user = (req as any).user;

    // 强制登出所有设备
    await AuthService.forceLogoutAllDevices(user.id);

    logger.info('用户强制登出所有设备', { userId: user.id, username: user.username });

    res.json({
      success: true,
      message: '已强制登出所有设备',
    });
    return;
  } catch (error) {
    logger.error('强制登出所有设备失败:', error);
    next(error);
  }
});

export default router;