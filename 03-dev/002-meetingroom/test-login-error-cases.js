const http = require('http');

// 测试登录功能的不同错误情况
async function testLogin(title, username, password) {
  return new Promise((resolve) => {
    console.log(`\n=== ${title} ===`);
    
    const postData = JSON.stringify({ username, password });
    
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
        console.log(`Status Code: ${res.statusCode}`);
        console.log(`Headers: ${JSON.stringify(res.headers, null, 2)}`);
        
        try {
          const jsonData = JSON.parse(data);
          console.log(`Response Body: ${JSON.stringify(jsonData, null, 2)}`);
          
          // 检查是否有错误代码
          if (jsonData.code) {
            console.log(`Error Code: ${jsonData.code}`);
          }
        } catch (parseError) {
          console.log('Response Body (raw):', data);
        }
        
        resolve({ statusCode: res.statusCode, data });
      });
    });

    req.on('error', (error) => {
      console.error('Request Error:', error.message);
      resolve({ error: error.message });
    });

    req.write(postData);
    req.end();
  });
}

// 运行所有测试
async function runTests() {
  console.log('开始测试登录功能的不同错误情况...');
  
  // 1. 正确凭据登录
  await testLogin(
    '正确凭据登录',
    'admin', 
    'Admin123!'
  );
  
  // 2. 错误密码登录
  await testLogin(
    '错误密码登录',
    'admin',
    'wrongpassword'
  );
  
  // 3. 不存在的用户登录
  await testLogin(
    '不存在的用户登录',
    'nonexistentuser',
    'anypassword'
  );
  
  // 4. 禁用账户登录 (假设有一个被禁用的测试账户)
  // 注意：这需要先在数据库中创建一个状态为'disabled'的用户
  await testLogin(
    '禁用账户登录',
    'disableduser',
    'anypassword'
  );
  
  console.log('\n所有测试完成！');
}

// 执行测试
runTests().catch(console.error);