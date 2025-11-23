import sqlite3 from 'sqlite3';
import { logger } from '../utils/logger';

type QueryResult<T = any> = { rows: T[] };

const db = new sqlite3.Database('meetingroom.db', (err) => {
  if (err) {
    logger.error('SQLite 连接失败', { error: err.message });
  } else {
    logger.info('SQLite 已连接');
  }
});

const run = (sql: string, params: any[] = []): Promise<{ changes?: number }> => {
  return new Promise((resolve, reject) => {
    const stmt = normalizeSql(sql);
    db.run(stmt.sql, stmt.params(params), function (err) {
      if (err) return reject(err);
      resolve({ changes: (this as any).changes });
    });
  });
};

const all = <T = any>(sql: string, params: any[] = []): Promise<T[]> => {
  return new Promise((resolve, reject) => {
    const stmt = normalizeSql(sql);
    db.all(stmt.sql, stmt.params(params), (err, rows) => {
      if (err) return reject(err);
      resolve(rows as T[]);
    });
  });
};

const get = <T = any>(sql: string, params: any[] = []): Promise<T | undefined> => {
  return new Promise((resolve, reject) => {
    const stmt = normalizeSql(sql);
    db.get(stmt.sql, stmt.params(params), (err, row) => {
      if (err) return reject(err);
      resolve(row as T | undefined);
    });
  });
};

export const query = async <T = any>(sql: string, params: any[] = []): Promise<QueryResult<T>> => {
  const rows = await all<T>(sql, params);
  return { rows };
};

export const transaction = async (fn: () => Promise<void>): Promise<void> => {
  await run('BEGIN');
  try {
    await fn();
    await run('COMMIT');
  } catch (error) {
    await run('ROLLBACK');
    throw error;
  }
};

const normalizeSql = (sql: string) => {
  let index = 0;
  const converted = sql.replace(/\$(\d+)/g, () => {
    index += 1;
    return '?';
  });
  return {
    sql: converted,
    params: (arr: any[]) => arr,
  };
};

export const initializeDB = async (): Promise<void> => {
  await run(`CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    avatar TEXT,
    last_login_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
  )`);

  await run(`CREATE TABLE IF NOT EXISTS meeting_rooms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    building TEXT,
    capacity INTEGER DEFAULT 10,
    equipment TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'available',
    images TEXT,
    hourly_rate INTEGER,
    open_time TEXT,
    close_time TEXT,
    working_days TEXT,
    floor INTEGER,
    manager_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
  )`);

  const cols = await all<{ name: string }>(`PRAGMA table_info(meeting_rooms)`);
  const names = new Set(cols.map(c => (c as any).name));
  const addCol = async (sql: string) => { try { await run(sql); } catch (_) {} };
  if (!names.has('images')) await addCol(`ALTER TABLE meeting_rooms ADD COLUMN images TEXT`);
  if (!names.has('hourly_rate')) await addCol(`ALTER TABLE meeting_rooms ADD COLUMN hourly_rate INTEGER`);
  if (!names.has('open_time')) await addCol(`ALTER TABLE meeting_rooms ADD COLUMN open_time TEXT`);
  if (!names.has('close_time')) await addCol(`ALTER TABLE meeting_rooms ADD COLUMN close_time TEXT`);
  if (!names.has('working_days')) await addCol(`ALTER TABLE meeting_rooms ADD COLUMN working_days TEXT`);
  if (!names.has('floor')) await addCol(`ALTER TABLE meeting_rooms ADD COLUMN floor INTEGER`);
  if (!names.has('manager_id')) await addCol(`ALTER TABLE meeting_rooms ADD COLUMN manager_id TEXT`);

  const adminRow = await get<{ id: string }>('SELECT id FROM users WHERE username = ?', ['admin']);
  const adminId = adminRow ? (adminRow as any).id : null;
  await run(`UPDATE meeting_rooms SET images = COALESCE(images, '[]')`);
  await run(`UPDATE meeting_rooms SET equipment = COALESCE(equipment, '[]')`);
  await run(`UPDATE meeting_rooms SET hourly_rate = COALESCE(hourly_rate, 0)`);
  await run(`UPDATE meeting_rooms SET open_time = COALESCE(open_time, '08:00')`);
  await run(`UPDATE meeting_rooms SET close_time = COALESCE(close_time, '18:00')`);
  await run(`UPDATE meeting_rooms SET working_days = COALESCE(working_days, '[1,2,3,4,5]')`);
  await run(`UPDATE meeting_rooms SET floor = COALESCE(floor, 1)`);
  if (adminId) {
    await run(`UPDATE meeting_rooms SET manager_id = COALESCE(manager_id, ?)`, [adminId]);
  }

  await run(`CREATE TABLE IF NOT EXISTS meeting_bookings (
    id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL,
    title TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    booked_by TEXT NOT NULL,
    attendees TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
  )`);

  await run(`CREATE TABLE IF NOT EXISTS user_sessions (
    key TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    remember_me INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    last_access_time TEXT DEFAULT (datetime('now')),
    expires_at INTEGER NOT NULL
  )`);

  const admin = await get<{ id: string }>('SELECT id FROM users WHERE username = ?', ['admin']);
  if (!admin) {
    const { v4: uuidv4 } = require('uuid');
    const bcrypt = require('bcryptjs');
    const id = uuidv4();
    const hash = await bcrypt.hash('admin123', 10);
    await run(
      `INSERT INTO users (id, username, email, password_hash, role, department, status)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [id, 'admin', 'admin@yds.com', hash, 'admin', 'IT部门', 'active']
    );
  }

  const count = await get<{ c: number }>('SELECT COUNT(*) as c FROM meeting_rooms');
  const cVal = (count && (count as any).c) || 0;
  if (cVal === 0) {
    const { v4: uuidv4 } = require('uuid');
    const rooms = [
      { name: 'A101会议室', location: '一楼东侧', building: '研发楼', capacity: 12, equipment: ['投影仪','音响系统','白板'], description: '小型会议室', status: 'available', floor: 1 },
      { name: 'B205多功能厅', location: '二楼中央', building: '研发楼', capacity: 30, equipment: ['视频会议设备','白板'], description: '中型会议室', status: 'available', floor: 2 },
      { name: 'C301董事会议室', location: '三楼南侧', building: '行政楼', capacity: 20, equipment: ['视频会议设备','打印机','白板'], description: '高端会议室', status: 'maintenance', floor: 3 }
    ];
    for (const r of rooms) {
      await run(
        `INSERT INTO meeting_rooms (id, name, location, building, capacity, equipment, description, status, images, hourly_rate, open_time, close_time, working_days, floor, manager_id)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [uuidv4(), r.name, r.location, r.building, r.capacity, JSON.stringify(r.equipment), r.description, r.status, '[]', 100, '08:00', '18:00', JSON.stringify([1,2,3,4,5]), r.floor, adminId]
      );
    }
  }
};

export const getRedisClient = () => {
  return {
    connect: async () => {},
    disconnect: async () => {},
    get: async (key: string) => {
      const row = await get<{ user_id: string; session_id: string; refresh_token: string; remember_me: number; created_at: string; last_access_time: string }>(
        'SELECT user_id, session_id, refresh_token, remember_me, created_at, last_access_time FROM user_sessions WHERE key = ?',
        [key]
      );
      if (!row) return null;
      const payload = {
        userId: (row as any).user_id,
        sessionId: (row as any).session_id,
        refreshToken: (row as any).refresh_token,
        rememberMe: ((row as any).remember_me ?? 0) === 1,
        createdAt: (row as any).created_at,
        lastAccessTime: (row as any).last_access_time
      };
      return JSON.stringify(payload);
    },
    setEx: async (key: string, seconds: number, value: string) => {
      const payload = JSON.parse(value);
      const expires = Math.floor(Date.now() / 1000) + seconds;
      await run(
        `INSERT OR REPLACE INTO user_sessions (key, user_id, session_id, refresh_token, remember_me, created_at, last_access_time, expires_at)
         VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), ?)`,
        [key, payload.userId, payload.sessionId, payload.refreshToken || value, payload.rememberMe ? 1 : 0, expires]
      );
    },
    del: async (keys: string | string[]) => {
      const arr = Array.isArray(keys) ? keys : [keys];
      for (const k of arr) {
        await run('DELETE FROM user_sessions WHERE key = ?', [k]);
      }
    },
    keys: async (pattern: string) => {
      const like = pattern.replace('*', '%');
      const rows = await all<{ key: string }>('SELECT key FROM user_sessions WHERE key LIKE ?', [like]);
      return rows.map(r => r.key);
    }
  };
};

export default {
  query,
  transaction,
};
export { run, get, all };