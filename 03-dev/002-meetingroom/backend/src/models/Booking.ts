import { query, run } from '../config/database';

export interface Booking {
  id: string;
  roomId: string;
  title: string;
  startTime: string;
  endTime: string;
  bookedBy: string;
  attendees: string[];
  description?: string;
  status: 'confirmed' | 'cancelled' | 'completed';
  createdAt: string;
  updatedAt: string;
}

export interface CreateBookingData {
  roomId: string;
  title: string;
  startTime: string;
  endTime: string;
  bookedBy: string;
  attendees?: string[];
  description?: string;
}

export class BookingModel {
  static async create(data: CreateBookingData): Promise<Booking> {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    const sql = `
      INSERT INTO meeting_bookings (
        id, room_id, title, start_time, end_time, booked_by, attendees, description, status, created_at, updated_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, 'confirmed', datetime('now'), datetime('now')
      )
    `;
    await run(sql, [
      id,
      data.roomId,
      data.title,
      data.startTime,
      data.endTime,
      data.bookedBy,
      JSON.stringify(data.attendees || []),
      data.description || null
    ]);
    const res = await query<any>('SELECT * FROM meeting_bookings WHERE id = $1', [id]);
    return this.map(res.rows[0]);
  }

  static async delete(id: string): Promise<boolean> {
    const r = await run('DELETE FROM meeting_bookings WHERE id = $1'.replace('$1','?'), [id]);
    return ((r.changes ?? 0) > 0);
  }

  static async findByRoom(roomId: string): Promise<Booking[]> {
    const res = await query<any>('SELECT * FROM meeting_bookings WHERE room_id = $1 ORDER BY start_time ASC', [roomId]);
    return res.rows.map(this.map);
  }

  static async findOverlapping(roomId: string, startISO: string, endISO: string): Promise<Booking[]> {
    const res = await query<any>(
      `SELECT * FROM meeting_bookings 
       WHERE room_id = $1 
         AND status = 'confirmed'
         AND start_time < $3 AND end_time > $2`,
      [roomId, startISO, endISO]
    );
    return res.rows.map(this.map);
  }

  private static map(row: any): Booking {
    return {
      id: row.id,
      roomId: row.room_id,
      title: row.title,
      startTime: row.start_time,
      endTime: row.end_time,
      bookedBy: row.booked_by,
      attendees: row.attendees ? JSON.parse(row.attendees) : [],
      description: row.description,
      status: row.status,
      createdAt: row.created_at,
      updatedAt: row.updated_at
    };
  }
}