#!/usr/bin/env node

const sqlite3 = require('sqlite3').verbose();
const { v4: uuidv4 } = require('uuid');
const bcrypt = require('bcryptjs');

const db = new sqlite3.Database('meetingroom.db');

async function createFixedMeetingRoom() {
  return new Promise((resolve, reject) => {
    db.serialize(async () => {
      try {
        // 检查是否已经存在固定会议室
        const existingRoom = await new Promise((resolve, reject) => {
          db.get('SELECT id FROM meeting_rooms WHERE name = ?', ['YDS-Lab董事会会议室'], (err, row) => {
            if (err) reject(err);
            else resolve(row);
          });
        });

        if (existingRoom) {
          console.log('✅ 固定会议室已存在');
          resolve(existingRoom);
          return;
        }

        // 获取管理员ID
        const admin = await new Promise((resolve, reject) => {
          db.get('SELECT id FROM users WHERE username = ?', ['admin'], (err, row) => {
            if (err) reject(err);
            else resolve(row);
          });
        });

        if (!admin) {
          throw new Error('管理员账户不存在');
        }

        // 创建固定会议室
        const roomId = uuidv4();
        const roomData = {
          id: roomId,
          name: 'YDS-Lab董事会会议室',
          location: '三楼董事层',
          building: 'YDS总部大楼',
          capacity: 15,
          equipment: JSON.stringify(['视频会议设备', '投影仪', '音响系统', '白板', '电话会议系统']),
          description: 'YDS-Lab董事会专用会议室，支持远程视频会议，配备高端设备',
          status: 'available',
          images: '[]',
          hourly_rate: 200,
          open_time: '08:00',
          close_time: '20:00',
          working_days: JSON.stringify([1,2,3,4,5,6]),
          floor: 3,
          manager_id: admin.id
        };

        await new Promise((resolve, reject) => {
          db.run(
            `INSERT INTO meeting_rooms 
            (id, name, location, building, capacity, equipment, description, status, images, hourly_rate, open_time, close_time, working_days, floor, manager_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [
              roomData.id, roomData.name, roomData.location, roomData.building,
              roomData.capacity, roomData.equipment, roomData.description,
              roomData.status, roomData.images, roomData.hourly_rate,
              roomData.open_time, roomData.close_time, roomData.working_days,
              roomData.floor, roomData.manager_id
            ],
            function(err) {
              if (err) reject(err);
              else resolve();
            }
          );
        });

        console.log('✅ 固定会议室创建成功！');
        console.log('📋 会议室详情:');
        console.log(`   房间号: YDS-Lab董事会会议室`);
        console.log(`   位置: ${roomData.location}`);
        console.log(`   建筑: ${roomData.building}`);
        console.log(`   容量: ${roomData.capacity}人`);
        console.log(`   设备: ${JSON.parse(roomData.equipment).join(', ')}`);
        console.log(`   开放时间: ${roomData.open_time} - ${roomData.close_time}`);
        console.log(`   楼层: ${roomData.floor}楼`);
        
        resolve({ id: roomId, ...roomData });

      } catch (error) {
        console.error('❌ 创建会议室失败:', error.message);
        reject(error);
      }
    });
  });
}

// 运行脚本
if (require.main === module) {
  createFixedMeetingRoom()
    .then(() => {
      console.log('\n🎯 现在您可以使用管理员账号 (admin/admin123) 登录系统，找到"YDS-Lab董事会会议室"并组织会议！');
      db.close();
    })
    .catch((error) => {
      console.error('脚本执行失败:', error);
      db.close();
      process.exit(1);
    });
}

module.exports = { createFixedMeetingRoom };