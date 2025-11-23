# 智能会议室系统开发实施指南

## 1. 项目初始化

### 1.1 环境准备
```bash
# 安装Node.js (推荐v18+)
# 安装PostgreSQL (推荐v14+)
# 安装Redis (推荐v7+)
# 安装Ollama (本地AI模型服务)
# 安装Shimmy (本地语音服务)
```

### 1.2 项目结构创建
```bash
# 创建项目目录结构
mkdir -p yds-meeting-system
cd yds-meeting-system

# 创建目录结构
mkdir -p backend/{src/{controllers,services,models,middleware,routes,utils,types},tests,config,logs}
mkdir -p frontend/{src/{components,pages,hooks,services,utils,types},public,tests}
mkdir -p shared/{types,constants,utils}
mkdir -p docs/{api,architecture,deployment}
mkdir -p scripts/{dev,deploy,backup}
mkdir -p monitoring/{prometheus,grafana,logs}
```

### 1.3 后端项目初始化
```bash
# 初始化后端项目
cd backend
npm init -y

# 安装核心依赖
npm install express cors helmet morgan compression
npm install socket.io redis pg jsonwebtoken bcryptjs
npm install multer uuid date-fns joi winston
npm install dotenv cross-env

# 安装开发依赖
npm install -D typescript @types/node @types/express
npm install -D @types/cors @types/morgan @types/compression
npm install -D @types/bcryptjs @types/jsonwebtoken @types/uuid
npm install -D nodemon ts-node eslint prettier
npm install -D jest supertest @types/jest @types/supertest

# 安装AI和语音服务依赖
npm install axios form-data
npm install node-cron node-schedule
```

### 1.4 前端项目初始化
```bash
# 初始化前端项目
cd ../frontend
npm create vite@latest . --template react-ts

# 安装UI和状态管理依赖
npm install @headlessui/react @heroicons/react
npm install zustand react-hook-form
npm install sonner @tanstack/react-query

# 安装实时通信和工具依赖
npm install socket.io-client
npm install axios date-fns
npm install react-router-dom
npm install clsx tailwind-merge

# 安装开发工具
npm install -D @types/react @types/react-dom
```

### 1.5 配置文件创建

#### 1.5.1 后端配置文件
```typescript
// backend/src/config/database.ts
export const databaseConfig = {
  development: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'yds_meeting_dev',
    username: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'password',
    maxConnections: parseInt(process.env.DB_MAX_CONNECTIONS || '20'),
    idleTimeout: parseInt(process.env.DB_IDLE_TIMEOUT || '30000'),
    connectionTimeout: parseInt(process.env.DB_CONNECTION_TIMEOUT || '60000'),
  },
  production: {
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME,
    username: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    maxConnections: parseInt(process.env.DB_MAX_CONNECTIONS || '100'),
    idleTimeout: parseInt(process.env.DB_IDLE_TIMEOUT || '30000'),
    connectionTimeout: parseInt(process.env.DB_CONNECTION_TIMEOUT || '60000'),
    ssl: { rejectUnauthorized: false }
  }
};

// backend/src/config/redis.ts
export const redisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  db: parseInt(process.env.REDIS_DB || '0'),
  maxRetriesPerRequest: 3,
  retryDelayOnFailover: 100,
  enableReadyCheck: false,
  maxmemoryPolicy: 'allkeys-lru',
};

// backend/src/config/jwt.ts
export const jwtConfig = {
  secret: process.env.JWT_SECRET || 'your-secret-key',
  expiresIn: process.env.JWT_EXPIRES_IN || '2h',
  refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d',
  issuer: 'yds-meeting-system',
  audience: 'meeting-app',
  algorithm: 'RS256' as const,
};

// backend/src/config/ai.ts
export const aiConfig = {
  ollama: {
    baseURL: process.env.OLLAMA_BASE_URL || 'http://localhost:11434',
    timeout: parseInt(process.env.OLLAMA_TIMEOUT || '30000'),
    maxRetries: parseInt(process.env.OLLAMA_MAX_RETRIES || '3'),
    defaultModel: process.env.OLLAMA_DEFAULT_MODEL || 'qwen2.5:14b',
  },
  shimmy: {
    baseURL: process.env.SHIMMY_BASE_URL || 'http://localhost:51080',
    timeout: parseInt(process.env.SHIMMY_TIMEOUT || '15000'),
    maxRetries: parseInt(process.env.SHIMMY_MAX_RETRIES || '3'),
  }
};
```

#### 1.5.2 环境变量文件
```bash
# backend/.env.example
NODE_ENV=development
PORT=3000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=yds_meeting_dev
DB_USER=postgres
DB_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# JWT
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=2h
JWT_REFRESH_EXPIRES_IN=7d

# AI Services
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=30000
SHIMMY_BASE_URL=http://localhost:51080
SHIMMY_TIMEOUT=15000

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE=104857600
ALLOWED_FILE_TYPES=pdf,doc,docx,txt,md,jpg,png

# Security
BCRYPT_ROUNDS=12
SESSION_SECRET=your-session-secret

# Logging
LOG_LEVEL=info
LOG_FILE=logs/app.log

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
```

## 2. 数据库初始化

### 2.1 创建数据库
```bash
# 创建PostgreSQL数据库
createdb yds_meeting_dev

# 创建用户
psql -d yds_meeting_dev -c "
CREATE USER yds_meeting_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE yds_meeting_dev TO yds_meeting_user;
"
```

### 2.2 数据库迁移脚本
```bash
# 创建迁移目录
mkdir -p backend/migrations

# 创建初始迁移文件
# backend/migrations/001_create_initial_schema.sql
```

## 3. 后端核心实现

### 3.1 应用入口文件
```typescript
// backend/src/app.ts
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import compression from 'compression';
import { createServer } from 'http';
import { Server } from 'socket.io';

import { errorHandler } from './middleware/errorHandler';
import { rateLimiter } from './middleware/rateLimiter';
import { authRouter } from './routes/auth';
import { meetingRouter } from './routes/meetings';
import { socketHandler } from './services/socketService';

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.FRONTEND_URL || "http://localhost:5173",
    methods: ["GET", "POST"]
  }
});

// 安全中间件
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || "http://localhost:5173",
  credentials: true
}));

// 性能中间件
app.use(compression());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 限流中间件
app.use('/api/', rateLimiter);

// 路由
app.use('/api/auth', authRouter);
app.use('/api/meetings', meetingRouter);

// Socket.io处理
socketHandler(io);

// 错误处理中间件
app.use(errorHandler);

// 健康检查
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

export { app, server, io };
```

### 3.2 数据库连接
```typescript
// backend/src/config/database.ts
import { Pool } from 'pg';
import { databaseConfig } from './database';

const environment = process.env.NODE_ENV || 'development';
const config = databaseConfig[environment as keyof typeof databaseConfig];

export const pool = new Pool({
  host: config.host,
  port: config.port,
  database: config.database,
  user: config.username,
  password: config.password,
  max: config.maxConnections,
  idleTimeoutMillis: config.idleTimeout,
  connectionTimeoutMillis: config.connectionTimeout,
});

// 连接测试
pool.on('connect', () => {
  console.log('Database connected successfully');
});

pool.on('error', (err) => {
  console.error('Database connection error:', err);
});
```

### 3.3 认证服务
```typescript
// backend/src/services/authService.ts
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { pool } from '../config/database';
import { jwtConfig } from '../config/jwt';

export class AuthService {
  async login(email: string, password: string) {
    // 查询用户
    const result = await pool.query(
      'SELECT id, username, email, password_hash, role FROM users WHERE email = $1 AND is_active = true',
      [email]
    );
    
    if (result.rows.length === 0) {
      throw new Error('Invalid credentials');
    }
    
    const user = result.rows[0];
    
    // 验证密码
    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    if (!isValidPassword) {
      throw new Error('Invalid credentials');
    }
    
    // 生成令牌
    const accessToken = jwt.sign(
      { 
        userId: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      },
      jwtConfig.secret,
      { 
        expiresIn: jwtConfig.expiresIn,
        issuer: jwtConfig.issuer,
        audience: jwtConfig.audience
      }
    );
    
    const refreshToken = jwt.sign(
      { userId: user.id },
      jwtConfig.secret,
      { expiresIn: jwtConfig.refreshExpiresIn }
    );
    
    return {
      accessToken,
      refreshToken,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      }
    };
  }
  
  async refreshToken(refreshToken: string) {
    try {
      const decoded = jwt.verify(refreshToken, jwtConfig.secret) as any;
      
      // 查询用户确保仍然存在
      const result = await pool.query(
        'SELECT id, username, email, role FROM users WHERE id = $1 AND is_active = true',
        [decoded.userId]
      );
      
      if (result.rows.length === 0) {
        throw new Error('User not found');
      }
      
      const user = result.rows[0];
      
      // 生成新的访问令牌
      const accessToken = jwt.sign(
        { 
          userId: user.id,
          username: user.username,
          email: user.email,
          role: user.role
        },
        jwtConfig.secret,
        { 
          expiresIn: jwtConfig.expiresIn,
          issuer: jwtConfig.issuer,
          audience: jwtConfig.audience
        }
      );
      
      return { accessToken };
    } catch (error) {
      throw new Error('Invalid refresh token');
    }
  }
}
```

## 4. 前端核心实现

### 4.1 状态管理
```typescript
// frontend/src/stores/authStore.ts
import { create } from 'zustand';
import { authService } from '../services/authService';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isLoading: boolean;
  error: string | null;
  
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  isLoading: false,
  error: null,
  
  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await authService.login(email, password);
      
      set({
        user: response.user,
        accessToken: response.accessToken,
        isLoading: false,
        error: null
      });
      
      // 存储刷新令牌
      localStorage.setItem('refreshToken', response.refreshToken);
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Login failed'
      });
      throw error;
    }
  },
  
  logout: () => {
    set({ user: null, accessToken: null });
    localStorage.removeItem('refreshToken');
  },
  
  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) return;
    
    try {
      const response = await authService.refreshToken(refreshToken);
      set({ accessToken: response.accessToken });
    } catch (error) {
      // 刷新失败，需要重新登录
      get().logout();
      throw error;
    }
  },
  
  clearError: () => set({ error: null })
}));
```

### 4.2 会议组件
```typescript
// frontend/src/components/MeetingRoom.tsx
import { useState, useEffect } from 'react';
import { useMeetingStore } from '../stores/meetingStore';
import { useSocketStore } from '../stores/socketStore';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { AgendaPanel } from './AgendaPanel';
import { VotePanel } from './VotePanel';
import { DocumentPanel } from './DocumentPanel';

interface MeetingRoomProps {
  roomId: string;
}

export function MeetingRoom({ roomId }: MeetingRoomProps) {
  const { currentRoom, messages, loading, error } = useMeetingStore();
  const { socket, isConnected } = useSocketStore();
  const [activeTab, setActiveTab] = useState<'chat' | 'agenda' | 'vote' | 'docs'>('chat');
  
  useEffect(() => {
    // 加入会议室
    if (socket && isConnected) {
      socket.emit('join_room', { roomId });
    }
    
    return () => {
      // 离开会议室
      if (socket && isConnected) {
        socket.emit('leave_room', { roomId });
      }
    };
  }, [socket, isConnected, roomId]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-center text-red-600 p-4">
        <p className="text-lg font-semibold">加载会议室失败</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }
  
  if (!currentRoom) {
    return (
      <div className="text-center text-gray-600 p-4">
        <p className="text-lg">会议室不存在</p>
      </div>
    );
  }
  
  return (
    <div className="flex h-screen bg-gray-50">
      {/* 侧边栏 */}
      <div className="w-80 bg-white border-r border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {currentRoom.name}
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            类型: {getMeetingTypeLabel(currentRoom.type)}
          </p>
          <div className="flex items-center mt-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="ml-2 text-sm text-gray-600">
              {isConnected ? '已连接' : '未连接'}
            </span>
          </div>
        </div>
        
        {/* 标签页导航 */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-4">
            {[
              { key: 'chat', label: '讨论', icon: ChatIcon },
              { key: 'agenda', label: '议程', icon: AgendaIcon },
              { key: 'vote', label: '投票', icon: VoteIcon },
              { key: 'docs', label: '文档', icon: DocumentIcon }
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as any)}
                className={`flex items-center px-1 py-4 text-sm font-medium border-b-2 ${
                  activeTab === key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {label}
              </button>
            ))}
          </nav>
        </div>
        
        {/* 标签页内容 */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === 'chat' && <MessageList messages={messages} />}
          {activeTab === 'agenda' && <AgendaPanel roomId={roomId} />}
          {activeTab === 'vote' && <VotePanel roomId={roomId} />}
          {activeTab === 'docs' && <DocumentPanel roomId={roomId} />}
        </div>
        
        {/* 消息输入 */}
        <div className="p-4 border-t border-gray-200">
          <MessageInput roomId={roomId} />
        </div>
      </div>
      
      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col">
        {/* 可以在这里添加更多内容，如会议统计、参与者列表等 */}
        <div className="flex-1 p-6">
          <div className="text-center text-gray-500">
            <p>会议室主内容区域</p>
            <p className="text-sm mt-2">当前有 {messages.length} 条消息</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function getMeetingTypeLabel(type: string): string {
  const labels = {
    'A': 'A级（战略）',
    'B': 'B级（业务）',
    'C': 'C级（日常）'
  };
  return labels[type as keyof typeof labels] || type;
}
```

## 5. 开发工具配置

### 5.1 ESLint配置
```json
// backend/.eslintrc.json
{
  "parser": "@typescript-eslint/parser",
  "extends": [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "plugins": ["@typescript-eslint"],
  "env": {
    "node": true,
    "es2020": true
  },
  "rules": {
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
  }
}
```

### 5.2 Prettier配置
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
```

### 5.3 TypeScript配置
```json
// backend/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

## 6. 部署脚本

### 6.1 开发环境启动脚本
```bash
#!/bin/bash
# scripts/dev/start-dev.sh

echo "Starting YDS Meeting System Development Environment..."

# 启动PostgreSQL
echo "Starting PostgreSQL..."
docker-compose up -d postgres redis

# 等待数据库启动
sleep 5

# 运行数据库迁移
echo "Running database migrations..."
cd backend
npm run migrate

# 启动后端服务
echo "Starting backend server..."
npm run dev &
BACKEND_PID=$!

# 启动前端服务
echo "Starting frontend server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

# 等待服务启动
sleep 3

echo "Development environment started!"
echo "Backend: http://localhost:3000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# 捕获中断信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# 等待子进程
wait
```

### 6.2 Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    container_name: yds-meeting-postgres
    environment:
      POSTGRES_DB: yds_meeting_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d
    networks:
      - meeting-network

  redis:
    image: redis:7-alpine
    container_name: yds-meeting-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - meeting-network

  ollama:
    image: ollama/ollama
    container_name: yds-meeting-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - meeting-network

  shimmy:
    image: shimmy/shimmy:latest
    container_name: yds-meeting-shimmy
    ports:
      - "51080:51080"
    volumes:
      - ./external_models.json:/app/config/models.json
    depends_on:
      - ollama
    networks:
      - meeting-network

volumes:
  postgres_data:
  redis_data:
  ollama_data:

networks:
  meeting-network:
    driver: bridge
```

## 7. 测试策略

### 7.1 单元测试配置
```typescript
// backend/jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.ts',
    '**/?(*.)+(spec|test).ts'
  ],
  transform: {
    '^.+\\.ts$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/config/**',
    '!src/types/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

### 7.2 API测试示例
```typescript
// backend/tests/routes/auth.test.ts
import request from 'supertest';
import { app } from '../../src/app';

describe('Auth Routes', () => {
  describe('POST /api/auth/login', () => {
    it('should login with valid credentials', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'test@example.com',
          password: 'password123'
        });
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('accessToken');
      expect(response.body).toHaveProperty('refreshToken');
      expect(response.body.user).toHaveProperty('email', 'test@example.com');
    });
    
    it('should fail with invalid credentials', async () => {
      const response = await request(app)
        .post('/api/auth/login')
        .send({
          email: 'test@example.com',
          password: 'wrongpassword'
        });
      
      expect(response.status).toBe(401);
      expect(response.body).toHaveProperty('error');
    });
  });
});
```

## 8. 部署指南

### 8.1 生产环境部署
```bash
#!/bin/bash
# scripts/deploy/deploy-production.sh

echo "Deploying YDS Meeting System to Production..."

# 环境检查
echo "Checking environment..."
if [ -z "$PRODUCTION_ENV_FILE" ]; then
  echo "Error: PRODUCTION_ENV_FILE not set"
  exit 1
fi

# 构建后端
echo "Building backend..."
cd backend
npm ci
npm run build
npm run test:coverage

# 构建前端
echo "Building frontend..."
cd ../frontend
npm ci
npm run build

# 数据库迁移
echo "Running database migrations..."
cd ../backend
npm run migrate:production

# 启动服务
echo "Starting services..."
pm run start:production

echo "Deployment completed successfully!"
```

### 8.2 监控和日志
```bash
# 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 查看应用日志
docker-compose logs -f app

# 查看系统资源
docker stats
```

这个实施指南为智能会议室系统提供了完整的开发、测试和部署方案，确保项目能够按照既定的技术架构顺利实施。