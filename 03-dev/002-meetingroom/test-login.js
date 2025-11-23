const https = require('https');

// 忽略 SSL 证书验证（仅用于开发环境）
const agent = new https.Agent({  
  rejectUnauthorized: false
});

async function testLogin() {
  try {
    // 使用 Node.js 内置的 fetch（Node.js 18+）
    const response = await fetch('http://localhost:3000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'admin',
        password: 'admin123'
      }),
    });

    console.log('Status:', response.status);
    console.log('Status Text:', response.statusText);
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('Response:', data);
    } else {
      const text = await response.text();
      console.log('Response (text):', text);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

testLogin();