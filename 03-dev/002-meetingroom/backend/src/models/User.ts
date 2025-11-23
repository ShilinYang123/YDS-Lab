import { query, run } from '../config/database';
import bcrypt from 'bcryptjs';
import { logger } from '../utils/logger';

export interface User {
  id: string;
  username: string;
  email: string;
  password_hash: string;
  role: 'admin' | 'manager' | 'user';
  department?: string;
  phone?: string;
  avatar?: string;
  status: 'active' | 'inactive' | 'suspended';
  last_login_at?: Date;
  created_at: Date;
  updated_at: Date;
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  role?: 'admin' | 'manager' | 'user';
  department?: string;
  phone?: string;
  avatar?: string;
}

export interface UpdateUserData {
  username?: string;
  email?: string;
  department?: string;
  phone?: string;
  avatar?: string;
  status?: 'active' | 'inactive' | 'suspended';
}

export class UserModel {
  // 创建用户表
  static async createTable(): Promise<void> {
    const createTableSQL = `
      CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'user')),
        department VARCHAR(100),
        phone VARCHAR(20),
        avatar TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
        last_login_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        CONSTRAINT users_username_check CHECK (char_length(username) >= 3),
        CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
      );

      -- 创建索引
      CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
      CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
      CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
      CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
      CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);

      -- 创建更新时间触发器
      CREATE OR REPLACE FUNCTION update_updated_at_column()
      RETURNS TRIGGER AS $$
      BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
      END;
      $$ language 'plpgsql';

      CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    `;

    try {
      await query(createTableSQL);
      logger.info('用户表创建成功');
    } catch (error) {
      logger.error('用户表创建失败:', error);
      throw error;
    }
  }

  // 创建用户
  static async create(userData: CreateUserData): Promise<User> {
    const { username, email, password, role = 'user', department, phone, avatar } = userData;
    
    // 密码加密
    const saltRounds = 12;
    const passwordHash = await bcrypt.hash(password, saltRounds);

    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    const insertSQL = `
      INSERT INTO users (id, username, email, password_hash, role, department, phone, avatar)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `;

    try {
      await query(insertSQL, [id, username, email, passwordHash, role, department, phone, avatar]);
      logger.info('用户创建成功:', { username, email, role });
      const fetched = await query('SELECT * FROM users WHERE id = $1', [id]);
      return fetched.rows[0];
    } catch (error) {
      logger.error('用户创建失败:', { username, email, error });
      throw error;
    }
  }

  // 根据ID查找用户
  static async findById(id: string): Promise<User | null> {
    const selectSQL = 'SELECT * FROM users WHERE id = $1';
    
    try {
      const result = await query(selectSQL, [id]);
      return result.rows[0] || null;
    } catch (error) {
      logger.error('用户查找失败:', { id, error });
      throw error;
    }
  }

  // 根据用户名查找用户
  static async findByUsername(username: string): Promise<User | null> {
    const selectSQL = 'SELECT * FROM users WHERE username = $1';
    
    try {
      const result = await query(selectSQL, [username]);
      return result.rows[0] || null;
    } catch (error) {
      logger.error('用户查找失败:', { username, error });
      throw error;
    }
  }

  // 根据邮箱查找用户
  static async findByEmail(email: string): Promise<User | null> {
    const selectSQL = 'SELECT * FROM users WHERE email = $1';
    
    try {
      const result = await query(selectSQL, [email]);
      return result.rows[0] || null;
    } catch (error) {
      logger.error('用户查找失败:', { email, error });
      throw error;
    }
  }

  // 验证用户密码
  static async validatePassword(password: string, passwordHash: string): Promise<boolean> {
    try {
      return await bcrypt.compare(password, passwordHash);
    } catch (error) {
      logger.error('密码验证失败:', error);
      return false;
    }
  }

  // 更新用户最后登录时间
  static async updateLastLogin(id: string): Promise<void> {
    const updateSQL = 'UPDATE users SET last_login_at = datetime("now") WHERE id = $1';
    
    try {
      await query(updateSQL, [id]);
      logger.info('用户最后登录时间更新成功:', { id });
    } catch (error) {
      logger.error('用户最后登录时间更新失败:', { id, error });
      throw error;
    }
  }

  // 更新用户信息
  static async update(id: string, updateData: UpdateUserData): Promise<User | null> {
    const fields: string[] = [];
    const values: any[] = [];
    let paramCount = 1;

    Object.entries(updateData).forEach(([key, value]) => {
      if (value !== undefined) {
        fields.push(`${key} = $${paramCount}`);
        values.push(value);
        paramCount++;
      }
    });

    if (fields.length === 0) {
      return await this.findById(id);
    }

    const updateSQL = `
      UPDATE users 
      SET ${fields.join(', ')}
      WHERE id = $${paramCount}
      RETURNING *
    `;

    try {
      const result = await query(updateSQL, [...values, id]);
      logger.info('用户信息更新成功:', { id, updateData });
      return result.rows[0] || null;
    } catch (error) {
      logger.error('用户信息更新失败:', { id, updateData, error });
      throw error;
    }
  }

  // 更新用户密码
  static async updatePassword(id: string, newPassword: string): Promise<void> {
    const saltRounds = 12;
    const passwordHash = await bcrypt.hash(newPassword, saltRounds);
    
    const updateSQL = 'UPDATE users SET password_hash = $1 WHERE id = $2';
    
    try {
      await query(updateSQL, [passwordHash, id]);
      logger.info('用户密码更新成功:', { id });
    } catch (error) {
      logger.error('用户密码更新失败:', { id, error });
      throw error;
    }
  }

  // 删除用户
  static async delete(id: string): Promise<boolean> {
    const deleteSQL = 'DELETE FROM users WHERE id = $1';
    
    try {
      const result = await run(deleteSQL.replace('$1', '?'), [id]);
      const deleted = (result.changes ?? 0) > 0;
      if (deleted) {
        logger.info('用户删除成功:', { id });
      }
      return deleted;
    } catch (error) {
      logger.error('用户删除失败:', { id, error });
      throw error;
    }
  }

  // 获取用户列表（支持分页和筛选）
  static async findAll(options: {
    page?: number;
    limit?: number;
    role?: string;
    status?: string;
    department?: string;
    search?: string;
  } = {}): Promise<{ users: User[]; total: number; page: number; totalPages: number }> {
    const { page = 1, limit = 10, role, status, department, search } = options;
    const offset = (page - 1) * limit;

    let whereConditions = [];
    let whereValues = [];
    let paramCount = 1;

    if (role) {
      whereConditions.push(`role = $${paramCount}`);
      whereValues.push(role);
      paramCount++;
    }

    if (status) {
      whereConditions.push(`status = $${paramCount}`);
      whereValues.push(status);
      paramCount++;
    }

    if (department) {
      whereConditions.push(`department = $${paramCount}`);
      whereValues.push(department);
      paramCount++;
    }

    if (search) {
      whereConditions.push(`(username ILIKE $${paramCount} OR email ILIKE $${paramCount} OR department ILIKE $${paramCount})`);
      whereValues.push(`%${search}%`);
      paramCount++;
    }

    const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

    try {
      // 获取总数
      const countSQL = `SELECT COUNT(*) FROM users ${whereClause}`;
      const countResult = await query(countSQL, whereValues);
      const total = parseInt(countResult.rows[0].count);

      // 获取用户列表
      const selectSQL = `
        SELECT * FROM users 
        ${whereClause}
        ORDER BY created_at DESC
        LIMIT $${paramCount} OFFSET $${paramCount + 1}
      `;
      const selectResult = await query(selectSQL, [...whereValues, limit, offset]);

      const totalPages = Math.ceil(total / limit);

      return {
        users: selectResult.rows,
        total,
        page,
        totalPages,
      };
    } catch (error) {
      logger.error('用户列表查询失败:', { options, error });
      throw error;
    }
  }

  // 获取用户统计信息
  static async getStats(): Promise<{
    total: number;
    active: number;
    inactive: number;
    suspended: number;
    byRole: Record<string, number>;
    byDepartment: Record<string, number>;
  }> {
    try {
      const statsSQL = `
        SELECT 
          COUNT(*) as total,
          COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
          COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive,
          COUNT(CASE WHEN status = 'suspended' THEN 1 END) as suspended
        FROM users
      `;
      const statsResult = await query(statsSQL);

      const roleStatsSQL = 'SELECT role, COUNT(*) as count FROM users GROUP BY role';
      const roleStatsResult = await query(roleStatsSQL);

      const deptStatsSQL = 'SELECT department, COUNT(*) as count FROM users WHERE department IS NOT NULL GROUP BY department';
      const deptStatsResult = await query(deptStatsSQL);

      const byRole: Record<string, number> = {};
      roleStatsResult.rows.forEach((row: any) => {
        byRole[row.role] = parseInt(row.count);
      });

      const byDepartment: Record<string, number> = {};
      deptStatsResult.rows.forEach((row: any) => {
        byDepartment[row.department] = parseInt(row.count);
      });

      return {
        total: parseInt(statsResult.rows[0].total),
        active: parseInt(statsResult.rows[0].active),
        inactive: parseInt(statsResult.rows[0].inactive),
        suspended: parseInt(statsResult.rows[0].suspended),
        byRole,
        byDepartment,
      };
    } catch (error) {
      logger.error('用户统计信息查询失败:', error);
      throw error;
    }
  }
}

export default UserModel;