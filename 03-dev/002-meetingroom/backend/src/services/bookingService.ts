import { BookingModel, CreateBookingData, Booking } from '../models/Booking';
import { MeetingRoomModel } from '../models/MeetingRoom';
import { CustomError } from '../middleware/errorHandler';

export class BookingService {
  static async create(data: CreateBookingData): Promise<Booking> {
    const room = await MeetingRoomModel.findById(data.roomId);
    if (!room) throw new CustomError('会议室不存在', 404);

    const start = new Date(data.startTime);
    const end = new Date(data.endTime);
    if (!(start instanceof Date) || isNaN(start.getTime()) || !(end instanceof Date) || isNaN(end.getTime())) {
      throw new CustomError('开始或结束时间格式错误', 400);
    }
    if (start >= end) throw new CustomError('开始时间必须早于结束时间', 400);

    const day = start.getDay();
    if (room.workingDays && room.workingDays.length > 0 && !room.workingDays.includes(day)) {
      throw new CustomError('该日期不在会议室营业工作日内', 400);
    }

    const [openH = 0, openM = 0] = room.openTime.split(':').map(Number);
    const [closeH = 23, closeM = 59] = room.closeTime.split(':').map(Number);
    const startMinutes = start.getHours() * 60 + start.getMinutes();
    const endMinutes = end.getHours() * 60 + end.getMinutes();
    const openMinutes = openH * 60 + openM;
    const closeMinutes = closeH * 60 + closeM;
    if (startMinutes < openMinutes || endMinutes > closeMinutes) {
      throw new CustomError('预订时间不在营业时段内', 400);
    }

    const startStr = data.startTime;
    const endStr = data.endTime;
    const overlaps = await BookingModel.findOverlapping(data.roomId, startStr, endStr);
    if (overlaps.length > 0) {
      throw new CustomError('预订冲突：该时段已有预订', 409);
    }

    return BookingModel.create(data);
  }

  static async listByRoom(roomId: string): Promise<Booking[]> {
    const room = await MeetingRoomModel.findById(roomId);
    if (!room) throw new CustomError('会议室不存在', 404);
    return BookingModel.findByRoom(roomId);
  }

  static async cancel(roomId: string, bookingId: string, requesterId: string): Promise<void> {
    const bookings = await BookingModel.findByRoom(roomId);
    const booking = bookings.find(b => b.id === bookingId);
    if (!booking) throw new CustomError('预订不存在', 404);
    if (booking.bookedBy !== requesterId) throw new CustomError('只能取消自己创建的预订', 403);
    const ok = await BookingModel.delete(bookingId);
    if (!ok) throw new CustomError('取消预订失败', 500);
  }
}