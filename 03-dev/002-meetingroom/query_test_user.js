const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, 'backend', 'data', 'meetingroom.db');

// 创建数据库连接
const db = new sqlite3.Database(dbPath);

console.log('查询test@example.com用户信息...');

const query = `
SELECT id, username, email, password_hash, status, created_at 
FROM users 
WHERE email = 'test@example.com' OR email = 'test@abc.com' OR username LIKE '%test%'
ORDER BY created_at DESC
`;

db.all(query, [], (err, rows) => {
  if (err) {
    console.error('查询错误:', err);
  } else {
    console.log('找到的用户:');
    rows.forEach(user => {
      console.log('------------------------');
      console.log('用户ID:', user.id);
      console.log('用户名:', user.username);
      console.log('邮箱:', user.email);
      console.log('密码哈希:', user.password_hash);
      console.log('状态:', user.status);
      console.log('创建时间:', user.created_at);
      console.log('------------------------');
    });
    
    if (rows.length === 0) {
      console.log('未找到测试用户');
    }
  }
  
  db.close();
});