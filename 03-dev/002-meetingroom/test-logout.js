const http = require('http');

// 使用之前获得的刷新令牌来测试登出功能
const refreshToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI0YjI5Y2Q3Yy1hZjc3LTQxNGUtYTZhZi1jYjIxMmQwNzRhYzAiLCJzZXNzaW9uSWQiOiIzNTVkZGE5OC1mY2RlLTRlY2UtYWFmNi05OTc2NDM4MTYxNjEiLCJpYXQiOjE3NjMzNTYxNjIsImV4cCI6MTc2Mzk2MDk2Mn0.SOpLLpsQaaF6jpNSkbu_oakPISuve3fGpxZQP-b35Pw';

const postData = JSON.stringify({ refreshToken });

const options = {
  hostname: 'localhost',
  port: 3000,
  path: '/api/auth/logout',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData)
  }
};

const req = http.request(options, (res) => {
  console.log(`Status: ${res.statusCode}`);
  console.log(`Status Text: ${res.statusMessage}`);
  
  let data = '';
  
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    try {
      // 尝试解析JSON响应
      const jsonData = JSON.parse(data);
      console.log('Response:', JSON.stringify(jsonData, null, 2));
    } catch (parseError) {
      // 如果不是JSON格式，则直接输出
      console.log('Response:', data);
    }
  });
});

req.on('error', (error) => {
  console.error('请求发生错误:', error.message);
});

req.write(postData);
req.end();