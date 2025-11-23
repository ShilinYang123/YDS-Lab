const http = require('http');

// 使用错误的凭据来测试登录失败的情况
const loginData = {
  username: 'wronguser',
  password: 'wrongpass123'
};

const postData = JSON.stringify(loginData);

const options = {
  hostname: 'localhost',
  port: 3000,
  path: '/api/auth/login',
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