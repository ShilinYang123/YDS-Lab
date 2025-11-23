import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import compression from 'compression';
import { createServer } from 'http';
import { Server } from 'socket.io';
import dotenv from 'dotenv';

import { errorHandler } from './middleware/errorHandler';
import { rateLimiter } from './middleware/rateLimiter';
import authRouter from './routes/auth';
import usersRouter from './routes/users';
import meetingRoomsRouter from './routes/meetingRooms';

import { logger } from './utils/logger';
import { initializeDB } from './config/database';

// 加载环境变量
dotenv.config();

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env['FRONTEND_URL'] || "http://localhost:5173",
    methods: ["GET", "POST", "PUT", "DELETE"],
    credentials: true
  },
  transports: ['websocket', 'polling']
});

const PORT = process.env['PORT'] || 3000;
const NODE_ENV = process.env['NODE_ENV'] || 'development';

// 安全中间件
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "ws:", "wss:"],
    },
  },
}));

// CORS配置
app.use(cors({
  origin: process.env['FRONTEND_URL'] || "http://localhost:5173",
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// 性能中间件
app.use(compression());
app.use(morgan(NODE_ENV === 'production' ? 'combined' : 'dev'));

// 解析中间件
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

app.use((req, _res, next) => {
  logger.info('http_request', { method: req.method, url: req.originalUrl });
  next();
});

// 限流中间件
app.use('/api/', rateLimiter);

// 健康检查
app.get('/health', (_req, res) => {
  res.status(200).json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: NODE_ENV,
    version: process.env['npm_package_version'] || '1.0.0'
  });
});

// API路由
app.use('/api/auth', authRouter);
app.use('/api/users', usersRouter);
app.use('/api/meeting-rooms', meetingRoomsRouter);



// 404处理
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: 'The requested resource was not found',
    path: req.originalUrl
  });
});

// 错误处理中间件
app.use(errorHandler);

// 启动服务器
const start = async () => {
  try {
    await initializeDB();
    server.listen(PORT, () => {
      logger.info(`🚀 YDS Meeting System Server running on port ${PORT}`);
      logger.info(`📝 Environment: ${NODE_ENV}`);
      logger.info(`🔧 API Version: ${process.env['API_VERSION'] || 'v1'}`);
      const stack = (app as any)._router?.stack || [];
      const routes = [] as Array<{ path: string; methods: string }>;
      for (const layer of stack) {
        const route = (layer as any).route;
        if (route && route.path) {
          const methods = Object.keys(route.methods).join(',');
          routes.push({ path: route.path, methods });
        }
      }
      logger.info('registered_routes', { routes });
    });
  } catch (error) {
    logger.error('服务器启动失败（数据库初始化异常）', { error: (error as Error).message });
    process.exit(1);
  }
};

start();

// 优雅关闭
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

export { app, server, io };