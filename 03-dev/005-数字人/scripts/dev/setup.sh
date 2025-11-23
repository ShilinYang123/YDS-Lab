#!/bin/bash

# 数字员工项目开发环境初始化脚本
# 作者: 雨俊
# 日期: 2025-01-15

set -e

echo "🚀 开始初始化数字员工项目开发环境..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    if netstat -tuln 2>/dev/null | grep -q ":$1 "; then
        print_error "端口 $1 已被占用，请检查其他服务"
        exit 1
    fi
}

# 主函数
main() {
    print_info "检查系统依赖..."
    
    # 检查必要命令
    check_command "node"
    check_command "npm"
    check_command "docker"
    check_command "docker-compose"
    check_command "git"
    
    print_success "系统依赖检查通过"
    
    # 检查端口
    print_info "检查端口占用..."
    check_port "3000"   # 前端端口
    check_port "3001"   # 后端端口
    check_port "5432"   # PostgreSQL端口
    check_port "6379"   # Redis端口
    check_port "9000"   # MinIO API端口
    check_port "9001"   # MinIO控制台端口
    
    print_success "端口检查通过"
    
    # 创建环境变量文件
    print_info "创建环境变量文件..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "环境变量文件创建完成"
        print_warning "请根据需要修改 .env 文件中的配置"
    else
        print_warning "环境变量文件已存在，跳过创建"
    fi
    
    # 创建必要的目录
    print_info "创建项目目录..."
    mkdir -p logs uploads temp
    mkdir -p src/components/common src/components/layout src/components/digital-employee src/components/business
    mkdir -p src/pages/Home src/pages/Login src/pages/Dashboard src/pages/DigitalEmployee src/pages/Tasks src/pages/Analytics src/pages/Settings
    mkdir -p src/hooks src/services src/store src/utils src/styles src/assets src/types src/config
    mkdir -p api/controllers api/models api/routes api/middleware api/services api/config api/utils api/types api/tests
    mkdir -p docker/postgres docker/redis docker/nginx docker/minio docker/monitoring
    mkdir -p scripts/dev scripts/deploy scripts/backup scripts/utils
    mkdir -p docs/api docs/frontend docs/deployment docs/architecture
    
    print_success "目录创建完成"
    
    # 启动基础服务
    print_info "启动基础服务 (PostgreSQL, Redis, MinIO)..."
    docker-compose up -d postgres redis minio
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    print_info "检查服务状态..."
    if docker-compose ps | grep -q "Up"; then
        print_success "基础服务启动成功"
    else
        print_error "基础服务启动失败，请检查日志"
        docker-compose logs postgres redis minio
        exit 1
    fi
    
    # 安装前端依赖
    print_info "安装前端依赖..."
    cd src
    if [ ! -f "package.json" ]; then
        print_info "初始化前端项目..."
        npm init -y
        
        # 安装核心依赖
        npm install react react-dom
        npm install -D @types/react @types/react-dom vite @vitejs/plugin-react
        npm install -D typescript
        npm install -D tailwindcss postcss autoprefixer
        npm install -D @types/node
        
        # 安装UI和工具库
        npm install antd
        npm install axios
        npm install zustand
        npm install react-router-dom
        npm install -D @types/react-router-dom
        
        # 安装开发工具
        npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
        npm install -D prettier
        npm install -D husky lint-staged
    else
        npm install
    fi
    cd ..
    
    print_success "前端依赖安装完成"
    
    # 安装后端依赖
    print_info "安装后端依赖..."
    cd api
    if [ ! -f "package.json" ]; then
        print_info "初始化后端项目..."
        npm init -y
        
        # 安装核心依赖
        npm install express cors helmet compression
        npm install -D @types/express @types/cors @types/compression
        npm install -D typescript ts-node nodemon
        
        # 安装数据库和缓存
        npm install @supabase/supabase-js
        npm install redis
        npm install -D @types/redis
        
        # 安装工具库
        npm install jsonwebtoken bcryptjs joi winston
        npm install -D @types/jsonwebtoken @types/bcryptjs
        
        # 安装文件存储
        npm install @aws-sdk/client-s3
        npm install minio
        
        # 安装AI服务
        npm install openai
        npm install @azure/cognitiveservices-speech
        
        # 安装开发工具
        npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
        npm install -D prettier
        npm install -D jest @types/jest ts-jest
        npm install -D supertest @types/supertest
    else
        npm install
    fi
    cd ..
    
    print_success "后端依赖安装完成"
    
    # 创建基础配置文件
    print_info "创建基础配置文件..."
    
    # 创建前端配置文件
    if [ ! -f "src/vite.config.ts" ]; then
        cat > src/vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:3001',
        ws: true,
      },
    },
  },
})
EOF
    fi
    
    # 创建后端配置文件
    if [ ! -f "api/tsconfig.json" ]; then
        cat > api/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
EOF
    fi
    
    print_success "配置文件创建完成"
    
    # 初始化Git仓库
    if [ ! -d ".git" ]; then
        print_info "初始化Git仓库..."
        git init
        
        # 创建.gitignore文件
        cat > .gitignore << 'EOF'
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
dist/
build/
*.tsbuildinfo

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/
*.lcov

# nyc test coverage
.nyc_output

# Dependency directories
jspm_packages/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env.test

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# Next.js build output
.next

# Nuxt.js build / generate output
.nuxt
dist

# Storybook build outputs
.out
.storybook-out

# Temporary folders
tmp/
temp/

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Docker
.docker/

# Uploads
uploads/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
EOF
        
        git add .
        git commit -m "Initial commit: Digital Employee Project Setup"
        
        print_success "Git仓库初始化完成"
    else
        print_warning "Git仓库已存在，跳过初始化"
    fi
    
    # 创建Docker网络
    print_info "创建Docker网络..."
    docker network create digital-employee-network 2>/dev/null || print_warning "网络已存在"
    
    # 显示服务状态
    print_info "服务状态检查..."
    docker-compose ps
    
    # 显示访问信息
    print_success "🎉 项目初始化完成！"
    echo ""
    echo "=========================================="
    echo "🌐 服务访问地址："
    echo "   前端应用: http://localhost:3000"
    echo "   后端API: http://localhost:3001"
    echo "   API文档: http://localhost:3001/docs"
    echo "   MinIO控制台: http://localhost:9001"
    echo "   PgAdmin: http://localhost:5050"
    echo "   Redis Commander: http://localhost:8081"
    echo ""
    echo "📋 后续步骤："
    echo "   1. 根据需要修改 .env 文件"
    echo "   2. 启动前端开发服务器: cd src && npm run dev"
    echo "   3. 启动后端开发服务器: cd api && npm run dev"
    echo "   4. 访问 http://localhost:3000 开始使用"
    echo "=========================================="
    echo ""
    echo "🔧 常用命令："
    echo "   查看日志: docker-compose logs -f [service-name]"
    echo "   停止服务: docker-compose down"
    echo "   重启服务: docker-compose restart [service-name]"
    echo "   进入容器: docker-compose exec [service-name] /bin/bash"
    echo ""
}

# 错误处理
trap 'print_error "脚本执行失败"; exit 1' ERR

# 执行主函数
main

print_success "✅ 所有任务执行完成！"