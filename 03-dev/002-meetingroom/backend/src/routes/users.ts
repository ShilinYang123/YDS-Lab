import { Router, Request, Response, NextFunction } from 'express';
import { body, param, query, validationResult } from 'express-validator';
import UserModel from '../models/User';
import { authMiddleware } from '../middleware/auth';
import { requireRole } from '../middleware/auth';
// AppError not used here
import { logger } from '../utils/logger';

const router = Router();

// 获取用户列表（管理员功能）
router.get('/', 
  authMiddleware, 
  requireRole(['admin', 'manager']),
  [
    query('page')
      .optional()
      .isInt({ min: 1 })
      .withMessage('页码必须是大于0的整数'),
    query('limit')
      .optional()
      .isInt({ min: 1, max: 100 })
      .withMessage('每页数量必须是1-100之间的整数'),
    query('role')
      .optional()
      .isIn(['admin', 'manager', 'user'])
      .withMessage('角色必须是admin、manager或user'),
    query('status')
      .optional()
      .isIn(['active', 'inactive', 'suspended'])
      .withMessage('状态必须是active、inactive或suspended'),
    query('department')
      .optional()
      .isLength({ max: 100 })
      .withMessage('部门名称不能超过100个字符'),
    query('search')
      .optional()
      .isLength({ max: 100 })
      .withMessage('搜索关键词不能超过100个字符'),
  ],
  async (req: Request, res: Response, next: NextFunction): Promise<void> => {
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

      const { page = 1, limit = 10, role, status, department, search } = req.query;

      // 获取用户列表
      const result = await UserModel.findAll({
        page: parseInt(page as string),
        limit: parseInt(limit as string),
        role: role as string,
        status: status as string,
        department: department as string,
        search: search as string,
      });

      res.json({
        success: true,
        message: '获取用户列表成功',
        data: {
          users: result.users,
          pagination: {
            total: result.total,
            page: result.page,
            totalPages: result.totalPages,
            limit: parseInt(limit as string),
          },
        },
      });
      return;
    } catch (error) {
      logger.error('获取用户列表失败:', error);
      next(error);
      return;
    }
  }
);

// 获取用户统计信息（管理员功能）
router.get('/stats',
  authMiddleware,
  requireRole(['admin', 'manager']),
  async (_req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      // 获取用户统计信息
      const stats = await UserModel.getStats();

      res.json({
        success: true,
        message: '获取用户统计信息成功',
        data: {
          stats,
        },
      });
      return;
    } catch (error) {
      logger.error('获取用户统计信息失败:', error);
      next(error);
      return;
    }
  }
);

// 获取用户信息
router.get('/:id',
  authMiddleware,
  requireRole(['admin', 'manager']),
  [
    param('id')
      .isUUID()
      .withMessage('用户ID必须是有效的UUID'),
  ],
  async (req: Request, res: Response, next: NextFunction): Promise<void> => {
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

      const { id } = req.params as { id: string };

      // 获取用户信息
      const user = await UserModel.findById(id);
      if (!user) {
        res.status(404).json({
          success: false,
          message: '用户不存在',
        });
        return;
      }

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
      return;
    }
  }
);

// 更新用户信息（管理员功能）
router.put('/:id',
  authMiddleware,
  requireRole(['admin', 'manager']),
  [
    param('id')
      .isUUID()
      .withMessage('用户ID必须是有效的UUID'),
    body('username')
      .optional()
      .isLength({ min: 3, max: 50 })
      .withMessage('用户名长度必须在3-50个字符之间')
      .matches(/^[a-zA-Z0-9_]+$/)
      .withMessage('用户名只能包含字母、数字和下划线'),
    body('email')
      .optional()
      .isEmail()
      .withMessage('请输入有效的邮箱地址')
      .normalizeEmail(),
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
    body('status')
      .optional()
      .isIn(['active', 'inactive', 'suspended'])
      .withMessage('状态必须是active、inactive或suspended'),
  ],
  async (req: Request, res: Response, next: NextFunction): Promise<void> => {
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

      const { id } = req.params as { id: string };
      const updateData = req.body;

      // 检查用户是否存在
      const existingUser = await UserModel.findById(id);
      if (!existingUser) {
        res.status(404).json({
          success: false,
          message: '用户不存在',
        });
        return;
      }

      // 管理员不能修改自己的角色
      const currentUser = (req as any).user;
      if (currentUser.id === id && updateData.role && updateData.role !== currentUser.role) {
        res.status(403).json({
          success: false,
          message: '不能修改自己的角色',
        });
        return;
      }

      // 更新用户信息
      const updatedUser = await UserModel.update(id, updateData);
      if (!updatedUser) {
        res.status(404).json({
          success: false,
          message: '用户更新失败',
        });
        return;
      }

      logger.info('用户信息更新成功', { userId: id, updateData });

      res.json({
        success: true,
        message: '用户信息更新成功',
        data: {
          user: {
            id: updatedUser.id,
            username: updatedUser.username,
            email: updatedUser.email,
            role: updatedUser.role,
            department: updatedUser.department,
            phone: updatedUser.phone,
            avatar: updatedUser.avatar,
            status: updatedUser.status,
            lastLoginAt: updatedUser.last_login_at,
            createdAt: updatedUser.created_at,
            updatedAt: updatedUser.updated_at,
          },
        },
      });
      return;
    } catch (error) {
      logger.error('更新用户信息失败:', error);
      next(error);
      return;
    }
  }
);

// 更新当前用户信息
router.put('/profile/me',
  authMiddleware,
  [
    body('username')
      .optional()
      .isLength({ min: 3, max: 50 })
      .withMessage('用户名长度必须在3-50个字符之间')
      .matches(/^[a-zA-Z0-9_]+$/)
      .withMessage('用户名只能包含字母、数字和下划线'),
    body('email')
      .optional()
      .isEmail()
      .withMessage('请输入有效的邮箱地址')
      .normalizeEmail(),
    body('department')
      .optional()
      .isLength({ max: 100 })
      .withMessage('部门名称不能超过100个字符'),
    body('phone')
      .optional()
      .matches(/^1[3-9]\d{9}$/)
      .withMessage('请输入有效的手机号码'),
  ],
  async (req: Request, res: Response, next: NextFunction): Promise<void> => {
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

      const currentUser = (req as any).user;
      const updateData = req.body;

      // 更新用户信息
      const updatedUser = await UserModel.update(currentUser.id, updateData);
      if (!updatedUser) {
        res.status(404).json({
          success: false,
          message: '用户更新失败',
        });
        return;
      }

      logger.info('当前用户信息更新成功', { userId: currentUser.id, updateData });

      res.json({
        success: true,
        message: '个人信息更新成功',
        data: {
          user: {
            id: updatedUser.id,
            username: updatedUser.username,
            email: updatedUser.email,
            role: updatedUser.role,
            department: updatedUser.department,
            phone: updatedUser.phone,
            avatar: updatedUser.avatar,
            status: updatedUser.status,
            lastLoginAt: updatedUser.last_login_at,
            createdAt: updatedUser.created_at,
            updatedAt: updatedUser.updated_at,
          },
        },
      });
      return;
    } catch (error) {
      logger.error('更新当前用户信息失败:', error);
      next(error);
      return;
    }
  }
);

// 更新用户密码（管理员功能）
router.put('/:id/password',
  authMiddleware,
  requireRole(['admin', 'manager']),
  [
    param('id')
      .isUUID()
      .withMessage('用户ID必须是有效的UUID'),
    body('newPassword')
      .isLength({ min: 8 })
      .withMessage('新密码长度至少为8个字符')
      .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
      .withMessage('新密码必须包含大小写字母、数字和特殊字符'),
  ],
  async (req: Request, res: Response, next: NextFunction): Promise<void> => {
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

      const { id } = req.params as { id: string };
      const { newPassword } = req.body;

      // 检查用户是否存在
      const existingUser = await UserModel.findById(id);
      if (!existingUser) {
        res.status(404).json({
          success: false,
          message: '用户不存在',
        });
        return;
      }

      // 更新用户密码
      await UserModel.updatePassword(id, newPassword);

      logger.info('用户密码更新成功', { userId: id });

      res.json({
        success: true,
        message: '用户密码更新成功',
      });
      return;
    } catch (error) {
      logger.error('更新用户密码失败:', error);
      next(error);
      return;
    }
  }
);

// 更新当前用户密码
router.put('/profile/password',
  authMiddleware,
  [
    body('currentPassword')
      .notEmpty()
      .withMessage('当前密码不能为空'),
    body('newPassword')
      .isLength({ min: 8 })
      .withMessage('新密码长度至少为8个字符')
      .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
      .withMessage('新密码必须包含大小写字母、数字和特殊字符'),
  ],
  async (req: Request, res: Response, next: NextFunction): Promise<void> => {
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

      const currentUser = (req as any).user;
      const { currentPassword, newPassword } = req.body;

      // 验证当前密码
      const isCurrentPasswordValid = await UserModel.validatePassword(currentPassword, (currentUser as any).password_hash);
      if (!isCurrentPasswordValid) {
        res.status(400).json({
          success: false,
          message: '当前密码错误',
        });
        return;
      }

      // 更新用户密码
      await UserModel.updatePassword(currentUser.id, newPassword);

      logger.info('当前用户密码更新成功', { userId: currentUser.id });

      res.json({
        success: true,
        message: '密码修改成功',
      });
      return;
    } catch (error) {
      logger.error('更新当前用户密码失败:', error);
      next(error);
      return;
    }
  }
);

// 删除用户（管理员功能）
router.delete('/:id',
  authMiddleware,
  requireRole(['admin']),
  [
    param('id')
      .isUUID()
      .withMessage('用户ID必须是有效的UUID'),
  ],
  async (req: Request, res: Response, next: NextFunction): Promise<void> => {
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

      const { id } = req.params as { id: string };
      const currentUser = (req as any).user;

      // 不能删除自己
      if (currentUser.id === id) {
        res.status(403).json({
          success: false,
          message: '不能删除自己的账户',
        });
        return;
      }

      // 检查用户是否存在
      const existingUser = await UserModel.findById(id);
      if (!existingUser) {
        res.status(404).json({
          success: false,
          message: '用户不存在',
        });
        return;
      }

      // 删除用户
      const deleted = await UserModel.delete(id);
      if (!deleted) {
        res.status(404).json({
          success: false,
          message: '用户删除失败',
        });
        return;
      }

      logger.info('用户删除成功', { userId: id, username: existingUser.username });

      res.json({
        success: true,
        message: '用户删除成功',
      });
      return;
    } catch (error) {
      logger.error('删除用户失败:', error);
      next(error);
      return;
    }
  }
);

export default router;