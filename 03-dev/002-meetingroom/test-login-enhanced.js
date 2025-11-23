const http = require('http');

// 依次运行测试用例
runTests();

async function runTests() {
  console.log('=== 测试用例1: 正确凭据登录 ===');
  await testLogin('admin', 'admin123');
  
  console.log('\n=== 测试用例2: 错误凭据登录 ===');
  await testLogin('admin', 'wrongpassword');
  
  console.log('\n=== 测试用例3: 不存在的用户 ===');
  await testLogin('nonexistentuser', 'password123');
}

function testLogin(username, password) {
  return new Promise((resolve) => {
    const loginData = { username, password };
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
          
          // 检查是否有错误代码
          if (jsonData.code) {
            console.log('Error Code:', jsonData.code);
          }
        } catch (parseError) {
          // 如果不是JSON格式，则直接输出
          console.log('Response:', data);
        }
        resolve();
      });
    });

    req.on('error', (error) => {
      console.error('请求发生错误:', error.message);
      resolve();
    });

    req.write(postData);
    req.end();
  });
}