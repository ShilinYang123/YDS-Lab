// 环境变量加载模块
const dotenv = require('dotenv');
const path = require('path');

// 加载环境变量
const envFile = process.env.NODE_ENV === 'production' ? '.env' : '.env.development';
const envPath = path.resolve(process.cwd(), envFile);

try {
  dotenv.config({ path: envPath });
} catch (error) {
  console.warn(`警告: 无法加载环境变量文件 ${envPath}`);
}

// 配置验证
const config = {
  // 服务器配置
  server: {
    port: parseInt(process.env.PORT) || 3000,
    env: process.env.NODE_ENV || 'development',
    host: process.env.HOST || 'localhost'
  },
  
  // OpenAI配置
  openai: {
    apiKey: process.env.OPENAI_API_KEY,
    model: process.env.OPENAI_MODEL || 'gpt-3.5-turbo',
    maxTokens: parseInt(process.env.OPENAI_MAX_TOKENS) || 1000,
    temperature: parseFloat(process.env.OPENAI_TEMPERATURE) || 0.7
  },
  
  // 安全配置
  security: {
    jwtSecret: process.env.JWT_SECRET || 'your-super-secret-jwt-key',
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS) || 10,
    rateLimitWindow: parseInt(process.env.RATE_LIMIT_WINDOW) || 15,
    rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX) || 100
  },
  
  // 数据库配置
  database: {
    url: process.env.DATABASE_URL || 'sqlite:./database.sqlite'
  },
  
  // 日志配置
  log: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || './logs/app.log'
  }
};

// 配置验证函数
function validateConfig() {
  const errors = [];
  
  // 检查必需的环境变量
  if (!config.openai.apiKey) {
    errors.push('缺少 OPENAI_API_KEY 环境变量');
  }
  
  // 安全警告
  if (config.security.jwtSecret === 'your-super-secret-jwt-key') {
    errors.push('警告: JWT_SECRET 使用默认值，请设置强密钥');
  }
  
  // 检查端口号
  if (config.server.port < 1024 || config.server.port > 65535) {
    errors.push('端口号必须在 1024-65535 范围内');
  }
  
  // 检查JWT密钥强度
  if (config.security.jwtSecret.length < 16) {
    errors.push('JWT_SECRET 至少需要 16 个字符');
  }
  
  return errors;
}

module.exports = {
  config,
  validateConfig
};