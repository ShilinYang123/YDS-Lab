import winston from 'winston';
// path import not used

const logLevel = process.env['LOG_LEVEL'] || 'info';
const logFile = process.env['LOG_FILE'] || 'logs/app.log';
const nodeEnv = process.env['NODE_ENV'] || 'development';

// 自定义日志格式
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

// 开发环境格式
const devFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.printf(({ timestamp, level, message, stack }) => {
    return `${timestamp} [${level}]: ${stack || message}`;
  })
);

// 创建日志目录（按需）

// 配置transports
const transports: winston.transport[] = [
  // 控制台输出
  new winston.transports.Console({
    level: nodeEnv === 'production' ? 'warn' : 'debug',
    format: nodeEnv === 'production' ? logFormat : devFormat
  })
];

// 文件输出（生产环境）
if (nodeEnv === 'production') {
  transports.push(
    new winston.transports.File({
      filename: logFile,
      level: logLevel,
      format: logFormat,
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
      tailable: true
    }),
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      format: logFormat,
      maxsize: 10 * 1024 * 1024,
      maxFiles: 5,
      tailable: true
    })
  );
}

// 创建logger实例
export const logger = winston.createLogger({
  level: logLevel,
  format: logFormat,
  defaultMeta: { service: 'yds-meeting-system' },
  transports,
  exitOnError: false
});

// 创建流用于morgan
export const stream = {
  write: (message: string) => {
    logger.info(message.trim());
  }
};

// 错误日志记录器
export const errorLogger = (error: Error, context?: any) => {
  logger.error('Application Error', {
    error: {
      message: error.message,
      stack: error.stack,
      name: error.name
    },
    context,
    timestamp: new Date().toISOString()
  });
};

// 审计日志记录器
export const auditLogger = (action: string, userId: string, details: any) => {
  logger.info('Audit Log', {
    action,
    userId,
    details,
    timestamp: new Date().toISOString(),
    ip: details.ip,
    userAgent: details.userAgent
  });
};