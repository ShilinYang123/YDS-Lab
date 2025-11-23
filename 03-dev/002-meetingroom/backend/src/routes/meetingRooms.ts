import { Router, Request, Response, NextFunction } from 'express';
import { authenticate, authorize, AuthRequest } from '../middleware/auth';
import { MeetingRoomService } from '../services/meetingRoomService';
import { BookingService } from '../services/bookingService';
import { CustomError } from '../middleware/errorHandler';
import { logger } from '../utils/logger';

const router = Router();

// 获取所有会议室
router.get('/', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const q = req.query as Record<string, string>;
    const filters: { status?: string; capacityMin?: number; capacityMax?: number; location?: string; building?: string; managerId?: string } = {};
    if (q['status']) filters.status = q['status'];
    if (q['capacityMin']) filters.capacityMin = parseInt(q['capacityMin'], 10);
    if (q['capacityMax']) filters.capacityMax = parseInt(q['capacityMax'], 10);
    if (q['location']) filters.location = q['location'];
    if (q['building']) filters.building = q['building'];
    if (q['managerId']) filters.managerId = q['managerId'];

    const meetingRooms = await MeetingRoomService.getAllMeetingRooms(filters);
    
    res.json({
      success: true,
      data: {
        meetingRooms,
        total: meetingRooms.length
      }
    });
  } catch (error) {
    next(error);
  }
});

// 获取单个会议室详情
router.get('/:id', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params as { id: string };
    const meetingRoom = await MeetingRoomService.getMeetingRoomById(id);
    
    res.json({
      success: true,
      data: { meetingRoom }
    });
  } catch (error) {
    next(error);
  }
});

// 搜索会议室
router.get('/search/:query', authenticate, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { query } = req.params as { query: string };
    const meetingRooms = await MeetingRoomService.searchMeetingRooms(query);
    
    res.json({
      success: true,
      data: { meetingRooms }
    });
  } catch (error) {
    next(error);
  }
});

// 创建会议室（管理员权限）
router.post('/', authenticate, authorize(['admin']), async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const meetingRoom = await MeetingRoomService.createMeetingRoom(req.body, req.user!.id);
    
    logger.info(`会议室创建成功: ${meetingRoom.name}`, {
      userId: req.user!.id,
      meetingRoomId: meetingRoom.id,
      action: 'create_meeting_room'
    });
    
    res.status(201).json({
      success: true,
      data: { meetingRoom },
      message: '会议室创建成功'
    });
  } catch (error) {
    next(error);
  }
});

// 更新会议室（管理员权限）
router.put('/:id', authenticate, authorize(['admin']), async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params as { id: string };
    const meetingRoom = await MeetingRoomService.updateMeetingRoom(id, req.body, req.user!.id);
    
    logger.info(`会议室更新成功: ${meetingRoom.name}`, {
      userId: req.user!.id,
      meetingRoomId: id,
      action: 'update_meeting_room'
    });
    
    res.json({
      success: true,
      data: { meetingRoom },
      message: '会议室更新成功'
    });
  } catch (error) {
    next(error);
  }
});

// 删除会议室（管理员权限）
router.delete('/:id', authenticate, authorize(['admin']), async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params as { id: string };
    await MeetingRoomService.deleteMeetingRoom(id, req.user!.id);
    
    logger.info(`会议室删除成功: ID ${id}`, {
      userId: req.user!.id,
      meetingRoomId: id,
      action: 'delete_meeting_room'
    });
    
    res.json({
      success: true,
      message: '会议室删除成功'
    });
  } catch (error) {
    next(error);
  }
});

// 更新会议室状态（管理员权限）
router.patch('/:id/status', authenticate, authorize(['admin']), async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params as { id: string };
    const { status } = req.body;
    
    if (!status || !['available', 'occupied', 'maintenance', 'disabled'].includes(status)) {
      throw new CustomError('无效的状态值', 400);
    }
    
    await MeetingRoomService.updateMeetingRoomStatus(id, status, req.user!.id);
    
    logger.info(`会议室状态更新成功: ID ${id} -> ${status}`, {
      userId: req.user!.id,
      meetingRoomId: id,
      action: 'update_meeting_room_status'
    });
    
    res.json({
      success: true,
      message: '会议室状态更新成功'
    });
  } catch (error) {
    next(error);
  }
});

// 获取管理的会议室（管理员或经理权限）
router.get('/managed/by-me', authenticate, authorize(['admin', 'manager']), async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const meetingRooms = await MeetingRoomService.getMeetingRoomsByManager(req.user!.id);
    
    res.json({
      success: true,
      data: { meetingRooms }
    });
  } catch (error) {
    next(error);
  }
});

// 创建预订（认证用户）
router.post('/:id/bookings', authenticate, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params as { id: string };
    const booking = await BookingService.create({
      roomId: id,
      title: req.body.title,
      startTime: req.body.startTime,
      endTime: req.body.endTime,
      bookedBy: req.user!.id,
      attendees: req.body.attendees || [],
      description: req.body.description || undefined
    });
    res.status(201).json({ success: true, data: { booking } });
  } catch (error) {
    next(error);
  }
});

// 获取会议室预订列表（认证用户）
router.get('/:id/bookings', authenticate, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params as { id: string };
    const bookings = await BookingService.listByRoom(id);
    res.json({ success: true, data: { bookings } });
  } catch (error) {
    next(error);
  }
});

// 取消预订（预订创建者或管理员）
router.delete('/:roomId/bookings/:bookingId', authenticate, async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    const { roomId, bookingId } = req.params as { roomId: string; bookingId: string };
    // 管理员可取消任意预订；普通用户只能取消自己创建的预订
    if (req.user!.role === 'admin') {
      await BookingService.cancel(roomId, bookingId, req.user!.id).catch(async (err) => {
        if ((err as any).statusCode === 403) {
          const { BookingModel } = await import('../models/Booking');
          const deleted = await BookingModel.delete(bookingId);
          if (!deleted) throw err;
          return;
        }
        throw err;
      });
      res.json({ success: true, message: '预订已取消' });
      return;
    }
    await BookingService.cancel(roomId, bookingId, req.user!.id);
    res.json({ success: true, message: '预订已取消' });
  } catch (error) {
    next(error);
  }
});

export default router;