const http = require('http');

// 测试不同错误情况的登录
async function testLogin(username, password, description) {
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
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          console.log(`\n${description}`);
          console.log(`Status: ${res.statusCode}`);
          console.log(`Response:`, JSON.stringify(jsonData, null, 2));
          resolve({ status: res.statusCode, data: jsonData });
        } catch (parseError) {
          console.log(`\n${description}`);
          console.log(`Status: ${res.statusCode}`);
          console.log(`Response:`, data);
          resolve({ status: res.statusCode, data: data });
        }
      });
    });

    req.on('error', (error) => {
      console.log(`\n${description}`);
      console.error('请求发生错误:', error.message);
      resolve({ error: error.message });
    });

    req.write(postData);
    req.end();
  });
}

// 运行所有测试
async function runTests() {
  console.log('开始测试登录错误处理...');
  
  // 1. 测试正确的凭据
  await testLogin('admin', 'admin123', '1. 正确凭据登录测试:');
  
  // 2. 测试错误的密码
  await testLogin('admin', 'wrongpassword', '2. 错误密码登录测试:');
  
  // 3. 测试不存在的用户
  await testLogin('nonexistentuser', 'anypassword', '3. 不存在用户登录测试:');
  
  // 4. 测试被禁用的用户 (需要先在数据库中创建一个被禁用的用户才能测试)
  // await testLogin('disableduser', 'anypassword', '4. 被禁用用户登录测试:');
  
  console.log('\n测试完成。');
}

// 执行测试
runTests();