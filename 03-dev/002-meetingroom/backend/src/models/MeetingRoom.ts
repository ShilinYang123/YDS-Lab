import { query, run } from '../config/database';

export interface MeetingRoom {
  id: string;
  name: string;
  description?: string;
  capacity: number;
  location: string;
  floor: number;
  building: string;
  equipment: string[]; // JSON array of equipment IDs
  images: string[]; // JSON array of image URLs
  status: 'available' | 'occupied' | 'maintenance' | 'disabled';
  hourlyRate: number;
  openTime: string; // HH:MM format
  closeTime: string; // HH:MM format
  workingDays: number[]; // 0-6, Sunday to Saturday
  managerId: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface CreateMeetingRoomData {
  name: string;
  description?: string;
  capacity: number;
  location: string;
  floor: number;
  building: string;
  equipment?: string[];
  images?: string[];
  hourlyRate: number;
  openTime: string;
  closeTime: string;
  workingDays?: number[];
  managerId: string;
}

export interface UpdateMeetingRoomData {
  name?: string;
  description?: string;
  capacity?: number;
  location?: string;
  floor?: number;
  building?: string;
  equipment?: string[];
  images?: string[];
  status?: 'available' | 'occupied' | 'maintenance' | 'disabled';
  hourlyRate?: number;
  openTime?: string;
  closeTime?: string;
  workingDays?: number[];
  managerId?: string;
}

export class MeetingRoomModel {
  static async create(data: CreateMeetingRoomData): Promise<MeetingRoom> {
    const { v4: uuidv4 } = require('uuid');
    const id = uuidv4();
    const sql = `
      INSERT INTO meeting_rooms (
        id, name, description, capacity, location, floor, building,
        equipment, images, status, hourly_rate, open_time, close_time,
        working_days, manager_id, created_at, updated_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, 'available', $10, $11, $12, $13, $14, datetime('now'), datetime('now')
      )
    `;
    
    const values = [
      data.name,
      data.description || null,
      data.capacity,
      data.location,
      data.floor,
      data.building,
      JSON.stringify(data.equipment || []),
      JSON.stringify(data.images || []),
      data.hourlyRate,
      data.openTime,
      data.closeTime,
      JSON.stringify(data.workingDays || [1, 2, 3, 4, 5]), // 默认工作日
      data.managerId
    ];

    await run(sql, [
      id,
      ...values
    ]);
    const fetched = await query<any>('SELECT * FROM meeting_rooms WHERE id = $1', [id]);
    return this.mapRowToMeetingRoom(fetched.rows[0]);
  }

  static async findById(id: string): Promise<MeetingRoom | null> {
    const sql = 'SELECT * FROM meeting_rooms WHERE id = $1';
    const result = await query<any>(sql, [id]);
    
    if (result.rows.length === 0) {
      return null;
    }
    
    return this.mapRowToMeetingRoom(result.rows[0]);
  }

  static async findAll(filters: {
    status?: string;
    capacityMin?: number;
    capacityMax?: number;
    location?: string;
    building?: string;
    managerId?: string;
  } = {}): Promise<MeetingRoom[]> {
    let sql = 'SELECT * FROM meeting_rooms WHERE 1=1';
    const values: any[] = [];
    let paramIndex = 1;

    if (filters.status) {
      sql += ` AND status = $${paramIndex}`;
      values.push(filters.status);
      paramIndex++;
    }

    if (filters.capacityMin) {
      sql += ` AND capacity >= $${paramIndex}`;
      values.push(filters.capacityMin);
      paramIndex++;
    }

    if (filters.capacityMax) {
      sql += ` AND capacity <= $${paramIndex}`;
      values.push(filters.capacityMax);
      paramIndex++;
    }

    if (filters.location) {
      sql += ` AND location LIKE $${paramIndex}`;
      values.push(`%${filters.location}%`);
      paramIndex++;
    }

    if (filters.building) {
      sql += ` AND building = $${paramIndex}`;
      values.push(filters.building);
      paramIndex++;
    }

    if (filters.managerId) {
      sql += ` AND manager_id = $${paramIndex}`;
      values.push(filters.managerId);
      paramIndex++;
    }

    sql += ' ORDER BY name ASC';

    const result = await query<any>(sql, values);
    return result.rows.map((row: any) => this.mapRowToMeetingRoom(row));
  }

  static async update(id: string, data: UpdateMeetingRoomData): Promise<MeetingRoom | null> {
    const fields = [];
    const values = [];
    let paramIndex = 1;

    if (data.name !== undefined) {
      fields.push(`name = $${paramIndex}`);
      values.push(data.name);
      paramIndex++;
    }

    if (data.description !== undefined) {
      fields.push(`description = $${paramIndex}`);
      values.push(data.description);
      paramIndex++;
    }

    if (data.capacity !== undefined) {
      fields.push(`capacity = $${paramIndex}`);
      values.push(data.capacity);
      paramIndex++;
    }

    if (data.location !== undefined) {
      fields.push(`location = $${paramIndex}`);
      values.push(data.location);
      paramIndex++;
    }

    if (data.floor !== undefined) {
      fields.push(`floor = $${paramIndex}`);
      values.push(data.floor);
      paramIndex++;
    }

    if (data.building !== undefined) {
      fields.push(`building = $${paramIndex}`);
      values.push(data.building);
      paramIndex++;
    }

    if (data.equipment !== undefined) {
      fields.push(`equipment = $${paramIndex}`);
      values.push(JSON.stringify(data.equipment));
      paramIndex++;
    }

    if (data.images !== undefined) {
      fields.push(`images = $${paramIndex}`);
      values.push(JSON.stringify(data.images));
      paramIndex++;
    }

    if (data.status !== undefined) {
      fields.push(`status = $${paramIndex}`);
      values.push(data.status);
      paramIndex++;
    }

    if (data.hourlyRate !== undefined) {
      fields.push(`hourly_rate = $${paramIndex}`);
      values.push(data.hourlyRate);
      paramIndex++;
    }

    if (data.openTime !== undefined) {
      fields.push(`open_time = $${paramIndex}`);
      values.push(data.openTime);
      paramIndex++;
    }

    if (data.closeTime !== undefined) {
      fields.push(`close_time = $${paramIndex}`);
      values.push(data.closeTime);
      paramIndex++;
    }

    if (data.workingDays !== undefined) {
      fields.push(`working_days = $${paramIndex}`);
      values.push(JSON.stringify(data.workingDays));
      paramIndex++;
    }

    if (data.managerId !== undefined) {
      fields.push(`manager_id = $${paramIndex}`);
      values.push(data.managerId);
      paramIndex++;
    }

    if (fields.length === 0) {
      return this.findById(id);
    }

    fields.push(`updated_at = $${paramIndex}`);
    values.push(new Date());
    paramIndex++;

    const sql = `
      UPDATE meeting_rooms 
      SET ${fields.join(', ')}
      WHERE id = $${paramIndex}
      RETURNING *
    `;
    
    values.push(id);

    const result = await query<any>(sql, values);
    
    if (result.rows.length === 0) {
      return null;
    }
    
    return this.mapRowToMeetingRoom(result.rows[0]);
  }

  static async delete(id: string): Promise<boolean> {
    const q = 'DELETE FROM meeting_rooms WHERE id = $1';
    const result = await run(q.replace('$1', '?'), [id]);
    return ((result.changes ?? 0) > 0);
  }

  static async updateStatus(id: string, status: MeetingRoom['status']): Promise<boolean> {
    const q = 'UPDATE meeting_rooms SET status = $1, updated_at = datetime("now") WHERE id = $2';
    const result = await run(q.replace('$1', '?').replace('$2', '?'), [status, id]);
    return ((result.changes ?? 0) > 0);
  }

  private static mapRowToMeetingRoom(row: any): MeetingRoom {
    const parseArr = (val: any): string[] => {
      if (!val) return [];
      try {
        const parsed = JSON.parse(val);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        if (typeof val === 'string' && val.includes(',')) {
          return val.split(',').map((s) => s.trim()).filter(Boolean);
        }
        return [];
      }
    };
    const parseDays = (val: any): number[] => {
      if (!val) return [];
      try {
        const parsed = JSON.parse(val);
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    };
    return {
      id: row.id,
      name: row.name,
      description: row.description,
      capacity: row.capacity,
      location: row.location,
      floor: row.floor,
      building: row.building,
      equipment: parseArr(row.equipment),
      images: parseArr(row.images),
      status: row.status,
      hourlyRate: row.hourly_rate,
      openTime: row.open_time,
      closeTime: row.close_time,
      workingDays: parseDays(row.working_days),
      managerId: row.manager_id,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    };
  }
}