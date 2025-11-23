# OpenSpec安装部署任务书

## 项目概述

本文档旨在提供OpenSpec系统的完整安装部署指南，确保系统能够在不同环境中稳定运行。

## 系统要求

### 硬件要求

- CPU: 4核心以上，推荐8核心
- 内存: 最低8GB，推荐16GB
- 存储: 至少50GB可用空间
- 网络: 稳定的互联网连接

### 软件要求

- 操作系统: Windows 10/11, Linux (Ubuntu 20.04+), macOS 10.15+
- Python: 3.8或更高版本
- Node.js: 16.0或更高版本
- Docker: 20.10或更高版本（可选）

## 安装步骤

### 1. 环境准备

1.1 检查Python版本
```bash
python --version
```

1.2 检查Node.js版本
```bash
node --version
```

1.3 检查Docker版本（如使用Docker部署）
```bash
docker --version
```

### 2. 获取源码

2.1 克隆仓库
```bash
git clone https://github.com/your-org/OpenSpec.git
cd OpenSpec
```

2.2 切换到稳定版本
```bash
git checkout v1.0.0
```

### 3. 后端安装

3.1 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3.2 安装依赖
```bash
pip install -r requirements.txt
```

3.3 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入必要配置
```

3.4 初始化数据库
```bash
python manage.py migrate
```

3.5 启动后端服务
```bash
python manage.py runserver
```

### 4. 前端安装

4.1 安装依赖
```bash
cd frontend
npm install
```

4.2 配置环境变量
```bash
cp .env.example .env.local
# 编辑.env.local文件，填入API地址等配置
```

4.3 构建前端
```bash
npm run build
```

4.4 启动前端服务（开发模式）
```bash
npm run dev
```

### 5. Docker部署（可选）

5.1 构建镜像
```bash
docker-compose build
```

5.2 启动服务
```bash
docker-compose up -d
```

## 配置说明

### 后端配置

主要配置项位于`.env`文件：

```
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/openspec

# Redis配置
REDIS_URL=redis://localhost:6379

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# 文件存储配置
MEDIA_ROOT=/var/www/openspec/media
```

### 前端配置

主要配置项位于`.env.local`文件：

```
# API地址
REACT_APP_API_URL=http://localhost:8000/api

# 其他配置
REACT_APP_VERSION=1.0.0
```

## 验证安装

1. 访问前端地址：http://localhost:3000
2. 访问API文档：http://localhost:8000/docs
3. 执行健康检查：
```bash
curl http://localhost:8000/health
```

## 常见问题

### Q: 安装过程中出现依赖冲突
A: 尝试使用虚拟环境，并确保Python版本符合要求

### Q: 前端无法连接后端API
A: 检查`.env.local`中的API地址配置是否正确

### Q: 数据库迁移失败
A: 检查数据库连接配置，确保数据库服务已启动

## 维护与更新

### 备份数据

定期备份数据库和媒体文件：

```bash
# 备份数据库
pg_dump openspec > openspec_backup.sql

# 备份媒体文件
tar -czf media_backup.tar.gz /var/www/openspec/media
```

### 更新系统

1. 获取最新代码
```bash
git pull origin main
```

2. 更新后端依赖
```bash
pip install -r requirements.txt
```

3. 更新前端依赖
```bash
cd frontend
npm install
```

4. 执行数据库迁移
```bash
python manage.py migrate
```

5. 重启服务

## 监控与日志

### 日志位置

- 后端日志：`/var/log/openspec/backend.log`
- 前端日志：浏览器控制台
- Nginx日志：`/var/log/nginx/`

### 监控指标

- API响应时间
- 数据库连接数
- 系统资源使用率
- 错误率

## 安全建议

1. 定期更新系统和依赖包
2. 使用强密码和密钥
3. 启用HTTPS
4. 配置防火墙规则
5. 定期备份数据
6. 实施访问控制

## 联系支持

如遇到问题，请联系技术支持：

- 邮箱：support@openspec.com
- 文档：https://docs.openspec.com
- 社区：https://community.openspec.com