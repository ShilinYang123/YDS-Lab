# Docker部署指南

## 概述
本文档详细说明数字员工系统的Docker容器化部署方案，包括基础服务配置、应用服务部署和运维管理。

## 服务架构

### 核心服务
- **PostgreSQL**: 主数据库服务
- **Redis**: 缓存和会话存储
- **MinIO**: 对象存储服务
- **Nginx**: 反向代理和负载均衡

### 应用服务
- **Frontend**: React前端应用
- **API**: Node.js后端API服务

### 工具服务
- **PgAdmin**: PostgreSQL管理工具
- **Redis Commander**: Redis管理工具

## Docker Compose配置详解

### 基础服务配置

#### PostgreSQL服务
```yaml
postgres:
  image: postgres:15-alpine
  container_name: digital-employee-postgres
  environment:
    POSTGRES_DB: digital_employee
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres123
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
  networks:
    - digital-employee-network
  restart: unless-stopped
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 30s
    timeout: 10s
    retries: 3
```

#### Redis服务
```yaml
redis:
  image: redis:7-alpine
  container_name: digital-employee-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
    - ./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf
  command: redis-server /usr/local/etc/redis/redis.conf
  networks:
    - digital-employee-network
  restart: unless-stopped
```

#### MinIO服务
```yaml
minio:
  image: minio/minio:latest
  container_name: digital-employee-minio
  ports:
    - "9000:9000"  # API端口
    - "9001:9001"  # 控制台端口
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin123
  volumes:
    - minio_data:/data
  command: server /data --console-address ":9001"
  networks:
    - digital-employee-network
  restart: unless-stopped
```

## 部署步骤

### 1. 环境准备
```bash
# 安装Docker和Docker Compose
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 项目配置
```bash
# 克隆项目代码
git clone <repository-url>
cd digital-employee

# 创建环境变量文件
cp .env.example .env
# 编辑.env文件，配置数据库、Redis、MinIO等连接信息
```

### 3. 基础服务启动
```bash
# 启动PostgreSQL、Redis、MinIO
docker-compose up -d postgres redis minio

# 检查服务状态
docker-compose ps

# 查看服务日志
docker-compose logs postgres
docker-compose logs redis
docker-compose logs minio
```

### 4. 应用服务部署
```bash
# 构建并启动所有服务
docker-compose --profile fullstack up -d

# 仅启动后端API
docker-compose --profile fullstack up -d api

# 仅启动前端应用
docker-compose --profile fullstack up -d frontend
```

### 5. 验证部署
```bash
# 检查所有服务状态
docker-compose ps

# 测试API连接
curl http://localhost:3001/health

# 测试前端访问
curl http://localhost:3000

# 访问MinIO控制台
open http://localhost:9001
```

## 配置文件详解

### Redis配置 (redis.conf)
```conf
# 基本配置
port 6379
bind 0.0.0.0
timeout 300
tcp-keepalive 60

# 内存配置
maxmemory 256mb
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000
rdbcompression yes

# 安全配置
requirepass your-redis-password

# 性能优化
tcp-backlog 511
databases 16
```

### Nginx配置 (nginx.conf)
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:3001;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        # 前端代理
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        # API代理
        location /api/ {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
        
        # WebSocket支持
        location /ws/ {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### 数据库初始化 (init.sql)
```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS digital_employee;

-- 创建用户
CREATE USER IF NOT EXISTS 'de_user'@'%' IDENTIFIED BY 'de_password';
GRANT ALL PRIVILEGES ON digital_employee.* TO 'de_user'@'%';
FLUSH PRIVILEGES;

-- 使用数据库
USE digital_employee;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建数字员工表
CREATE TABLE IF NOT EXISTS digital_employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    avatar_url VARCHAR(255),
    voice_config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 运维管理

### 服务监控
```bash
# 查看服务资源使用情况
docker stats

# 查看服务日志
docker-compose logs -f <service-name>

# 监控容器健康状态
docker-compose ps
```

### 数据备份
```bash
# PostgreSQL备份
docker-compose exec postgres pg_dump -U postgres digital_employee > backup.sql

# Redis备份
docker-compose exec redis redis-cli SAVE
docker cp digital-employee-redis:/data/dump.rdb ./redis-backup.rdb

# MinIO备份
docker run --rm -v minio_data:/data -v $(pwd):/backup alpine tar czf /backup/minio-backup.tar.gz /data
```

### 服务更新
```bash
# 拉取最新镜像
docker-compose pull

# 重新构建服务
docker-compose build --no-cache

# 滚动更新
docker-compose up -d --no-deps <service-name>
```

### 故障排查
```bash
# 查看服务日志
docker-compose logs <service-name>

# 进入容器调试
docker-compose exec <service-name> /bin/bash

# 检查网络连接
docker-compose exec <service-name> ping <other-service>

# 检查端口监听
docker-compose exec <service-name> netstat -tlnp
```

## 性能优化

### 资源配置建议
- **PostgreSQL**: 2GB内存，SSD存储
- **Redis**: 512MB内存
- **MinIO**: 根据文件存储需求配置
- **API服务**: 1GB内存，根据并发量调整
- **前端应用**: 512MB内存

### 环境变量调优
```yaml
# PostgreSQL性能优化
POSTGRES_SHARED_BUFFERS=256MB
POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
POSTGRES_WORK_MEM=4MB

# Redis性能优化
REDIS_MAXMEMORY=512mb
REDIS_MAXMEMORY_POLICY=allkeys-lru
```

## 安全加固

### 网络安全
- 使用Docker网络隔离
- 配置防火墙规则
- 启用HTTPS通信
- 限制容器间通信

### 数据安全
- 数据库连接加密
- 敏感数据加密存储
- 定期数据备份
- 访问日志记录

### 容器安全
- 使用官方基础镜像
- 定期更新镜像
- 最小权限原则
- 容器运行时安全

## 扩展部署

### 多环境部署
- 开发环境: `docker-compose.dev.yml`
- 测试环境: `docker-compose.test.yml`
- 生产环境: `docker-compose.prod.yml`

### 集群部署
- 使用Docker Swarm
- Kubernetes部署
- 负载均衡配置
- 服务发现机制