import { MeetingRoomModel, MeetingRoom, CreateMeetingRoomData, UpdateMeetingRoomData } from '../models/MeetingRoom';
import { query } from '../config/database';
import { UserModel } from '../models/User';
import { CustomError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

export class MeetingRoomService {
  static async createMeetingRoom(data: CreateMeetingRoomData, userId: string): Promise<MeetingRoom> {
    try {
      // 验证管理员权限
      const user = await UserModel.findById(userId);
      if (!user || user.role !== 'admin') {
        throw new CustomError('只有管理员可以创建会议室', 403);
      }

      // 验证必填字段
      if (!data.name || !data.capacity || !data.location || !data.building || !data.hourlyRate) {
        throw new CustomError('会议室名称、容量、位置、建筑和小时费率是必填项', 400);
      }

      // 验证容量
      if (data.capacity <= 0) {
        throw new CustomError('会议室容量必须大于0', 400);
      }

      // 验证费率
      if (data.hourlyRate < 0) {
        throw new CustomError('小时费率不能为负数', 400);
      }

      // 验证时间格式
      const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
      if (!timeRegex.test(data.openTime) || !timeRegex.test(data.closeTime)) {
        throw new CustomError('营业时间格式不正确，请使用HH:MM格式', 400);
      }

      // 验证营业时间逻辑
      if (data.openTime >= data.closeTime) {
        throw new CustomError('营业时间设置不正确，开始时间必须早于结束时间', 400);
      }

      // 设置默认工作日
      if (!data.workingDays || data.workingDays.length === 0) {
        data.workingDays = [1, 2, 3, 4, 5]; // 周一到周五
      }

      // 验证工作日
      const validDays = data.workingDays.every(day => day >= 0 && day <= 6);
      if (!validDays) {
        throw new CustomError('工作日设置不正确，有效值为0-6', 400);
      }

      const meetingRoom = await MeetingRoomModel.create(data);
      
      logger.info(`会议室创建成功: ${meetingRoom.name} (ID: ${meetingRoom.id})`, {
        userId,
        meetingRoomId: meetingRoom.id,
        action: 'create_meeting_room'
      });

      return meetingRoom;
    } catch (error) {
      if (error instanceof CustomError) {
        throw error;
      }
      logger.error('创建会议室失败', { error, userId, data });
      throw new CustomError('创建会议室失败', 500);
    }
  }

  static async getMeetingRoomById(id: string): Promise<MeetingRoom> {
    try {
      const meetingRoom = await MeetingRoomModel.findById(id);
      
      if (!meetingRoom) {
        throw new CustomError('会议室不存在', 404);
      }

      return meetingRoom;
    } catch (error) {
      if (error instanceof CustomError) {
        throw error;
      }
      logger.error('获取会议室信息失败', { error, meetingRoomId: id });
      throw new CustomError('获取会议室信息失败', 500);
    }
  }

  static async getAllMeetingRooms(filters: {
    status?: string;
    capacityMin?: number;
    capacityMax?: number;
    location?: string;
    building?: string;
    managerId?: string;
  } = {}): Promise<MeetingRoom[]> {
    try {
      const meetingRooms = await MeetingRoomModel.findAll(filters);
      return meetingRooms;
    } catch (error) {
      logger.error('获取会议室列表失败', { error, filters });
      throw new CustomError('获取会议室列表失败', 500);
    }
  }

  static async updateMeetingRoom(id: string, data: UpdateMeetingRoomData, userId: string): Promise<MeetingRoom> {
    try {
      // 验证管理员权限
      const user = await UserModel.findById(userId);
      if (!user || user.role !== 'admin') {
        throw new CustomError('只有管理员可以更新会议室', 403);
      }

      // 检查会议室是否存在
      const existingRoom = await MeetingRoomModel.findById(id);
      if (!existingRoom) {
        throw new CustomError('会议室不存在', 404);
      }

      // 验证容量
      if (data.capacity !== undefined && data.capacity <= 0) {
        throw new CustomError('会议室容量必须大于0', 400);
      }

      // 验证费率
      if (data.hourlyRate !== undefined && data.hourlyRate < 0) {
        throw new CustomError('小时费率不能为负数', 400);
      }

      // 验证时间格式
      if (data.openTime || data.closeTime) {
        const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
        const openTime = data.openTime || existingRoom.openTime;
        const closeTime = data.closeTime || existingRoom.closeTime;
        
        if (!timeRegex.test(openTime) || !timeRegex.test(closeTime)) {
          throw new CustomError('营业时间格式不正确，请使用HH:MM格式', 400);
        }

        if (openTime >= closeTime) {
          throw new CustomError('营业时间设置不正确，开始时间必须早于结束时间', 400);
        }
      }

      // 验证工作日
      if (data.workingDays) {
        const validDays = data.workingDays.every(day => day >= 0 && day <= 6);
        if (!validDays) {
          throw new CustomError('工作日设置不正确，有效值为0-6', 400);
        }
      }

      const updatedRoom = await MeetingRoomModel.update(id, data);
      
      logger.info(`会议室更新成功: ${updatedRoom!.name} (ID: ${id})`, {
        userId,
        meetingRoomId: id,
        action: 'update_meeting_room',
        changes: data
      });

      return updatedRoom!;
    } catch (error) {
      if (error instanceof CustomError) {
        throw error;
      }
      logger.error('更新会议室失败', { error, meetingRoomId: id, userId, data });
      throw new CustomError('更新会议室失败', 500);
    }
  }

  static async deleteMeetingRoom(id: string, userId: string): Promise<void> {
    try {
      // 验证管理员权限
      const user = await UserModel.findById(userId);
      if (!user || user.role !== 'admin') {
        throw new CustomError('只有管理员可以删除会议室', 403);
      }

      // 检查会议室是否存在
      const meetingRoom = await MeetingRoomModel.findById(id);
      if (!meetingRoom) {
        throw new CustomError('会议室不存在', 404);
      }

      const deleted = await MeetingRoomModel.delete(id);
      
      if (!deleted) {
        throw new CustomError('删除会议室失败', 500);
      }

      logger.info(`会议室删除成功: ${meetingRoom.name} (ID: ${id})`, {
        userId,
        meetingRoomId: id,
        action: 'delete_meeting_room'
      });
    } catch (error) {
      if (error instanceof CustomError) {
        throw error;
      }
      logger.error('删除会议室失败', { error, meetingRoomId: id, userId });
      throw new CustomError('删除会议室失败', 500);
    }
  }

  static async updateMeetingRoomStatus(id: string, status: MeetingRoom['status'], userId: string): Promise<void> {
    try {
      // 验证管理员权限
      const user = await UserModel.findById(userId);
      if (!user || user.role !== 'admin') {
        throw new CustomError('只有管理员可以更新会议室状态', 403);
      }

      // 检查会议室是否存在
      const meetingRoom = await MeetingRoomModel.findById(id);
      if (!meetingRoom) {
        throw new CustomError('会议室不存在', 404);
      }

      const updated = await MeetingRoomModel.updateStatus(id, status);
      
      if (!updated) {
        throw new CustomError('更新会议室状态失败', 500);
      }

      logger.info(`会议室状态更新成功: ${meetingRoom.name} (ID: ${id}) - 新状态: ${status}`, {
        userId,
        meetingRoomId: id,
        action: 'update_meeting_room_status',
        oldStatus: meetingRoom.status,
        newStatus: status
      });
    } catch (error) {
      if (error instanceof CustomError) {
        throw error;
      }
      logger.error('更新会议室状态失败', { error, meetingRoomId: id, userId, status });
      throw new CustomError('更新会议室状态失败', 500);
    }
  }

  static async getMeetingRoomsByManager(managerId: string): Promise<MeetingRoom[]> {
    try {
      const meetingRooms = await MeetingRoomModel.findAll({ managerId });
      return meetingRooms;
    } catch (error) {
      logger.error('获取管理的会议室失败', { error, managerId });
      throw new CustomError('获取管理的会议室失败', 500);
    }
  }

  static async searchMeetingRooms(q: string): Promise<MeetingRoom[]> {
    try {
      // 简单的搜索实现，可以根据名称、位置、建筑进行搜索
      const searchQuery = `%${q}%`;
      const sqlQuery = `
        SELECT * FROM meeting_rooms 
        WHERE name LIKE $1 OR location LIKE $1 OR building LIKE $1
        ORDER BY name ASC
      `;
      
      const result = await query<any>(sqlQuery, [searchQuery]);
      return result.rows.map((row: any) => MeetingRoomModel['mapRowToMeetingRoom'](row));
    } catch (error) {
      logger.error('搜索会议室失败', { error, query: q });
      throw new CustomError('搜索会议室失败', 500);
    }
  }
}