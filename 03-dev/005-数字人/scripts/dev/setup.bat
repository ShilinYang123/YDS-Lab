@echo off
REM 数字员工项目开发环境初始化脚本（Windows版本）
REM 作者: 雨俊
REM 日期: 2025-01-15

setlocal enabledelayedexpansion

echo 🚀 开始初始化数字员工项目开发环境...

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 请以管理员身份运行此脚本
    pause
    exit /b 1
)

REM 颜色定义（Windows 10+支持）
set "COLOR_INFO=[94m"
set "COLOR_SUCCESS=[92m"
set "COLOR_WARNING=[93m"
set "COLOR_ERROR=[91m"
set "COLOR_RESET=[0m"

REM 打印带颜色的信息
goto :print_info
:print_info
echo %COLOR_INFO%[INFO]%COLOR_RESET% %~1
goto :eof

:print_success
echo %COLOR_SUCCESS%[SUCCESS]%COLOR_RESET% %~1
goto :eof

:print_warning
echo %COLOR_WARNING%[WARNING]%COLOR_RESET% %~1
goto :eof

:print_error
echo %COLOR_ERROR%[ERROR]%COLOR_RESET% %~1
goto :eof

REM 检查命令是否存在
goto :check_command
:check_command
where %~1 >nul 2>&1
if %errorlevel% neq 0 (
    call :print_error "%~1 未安装，请先安装 %~1"
    pause
    exit /b 1
)
goto :eof

REM 检查端口是否被占用
goto :check_port
:check_port
netstat -an | findstr ":%~1 " >nul
if %errorlevel% equ 0 (
    call :print_error "端口 %~1 已被占用，请检查其他服务"
    pause
    exit /b 1
)
goto :eof

REM 主函数
goto :main
:main
call :print_info "检查系统依赖..."

REM 检查必要命令
call :check_command "node"
call :check_command "npm"
call :check_command "docker"
call :check_command "docker-compose"
call :check_command "git"

call :print_success "系统依赖检查通过"

REM 检查端口
call :print_info "检查端口占用..."
call :check_port "3000"   REM 前端端口
call :check_port "3001"   REM 后端端口
call :check_port "5432"   REM PostgreSQL端口
call :check_port "6379"   REM Redis端口
call :check_port "9000"   REM MinIO API端口
call :check_port "9001"   REM MinIO控制台端口

call :print_success "端口检查通过"

REM 创建环境变量文件
call :print_info "创建环境变量文件..."
if not exist ".env" (
    copy ".env.example" ".env"
    call :print_success "环境变量文件创建完成"
    call :print_warning "请根据需要修改 .env 文件中的配置"
) else (
    call :print_warning "环境变量文件已存在，跳过创建"
)

REM 创建必要的目录
call :print_info "创建项目目录..."
mkdir logs uploads temp 2>nul
mkdir "src\components\common" "src\components\layout" "src\components\digital-employee" "src\components\business" 2>nul
mkdir "src\pages\Home" "src\pages\Login" "src\pages\Dashboard" "src\pages\DigitalEmployee" "src\pages\Tasks" "src\pages\Analytics" "src\pages\Settings" 2>nul
mkdir "src\hooks" "src\services" "src\store" "src\utils" "src\styles" "src\assets" "src\types" "src\config" 2>nul
mkdir "api\controllers" "api\models" "api\routes" "api\middleware" "api\services" "api\config" "api\utils" "api\types" "api\tests" 2>nul
mkdir "docker\postgres" "docker\redis" "docker\nginx" "docker\minio" "docker\monitoring" 2>nul
mkdir "scripts\dev" "scripts\deploy" "scripts\backup" "scripts\utils" 2>nul
mkdir "docs\api" "docs\frontend" "docs\deployment" "docs\architecture" 2>nul

call :print_success "目录创建完成"

REM 启动基础服务
call :print_info "启动基础服务 (PostgreSQL, Redis, MinIO)..."
docker-compose up -d postgres redis minio

REM 等待服务启动
call :print_info "等待服务启动..."
timeout /t 10 /nobreak >nul

REM 检查服务状态
call :print_info "检查服务状态..."
docker-compose ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    call :print_success "基础服务启动成功"
) else (
    call :print_error "基础服务启动失败，请检查日志"
    docker-compose logs postgres redis minio
    pause
    exit /b 1
)

REM 安装前端依赖
call :print_info "安装前端依赖..."
cd src
if not exist "package.json" (
    call :print_info "初始化前端项目..."
    echo { > package.json
    echo   "name": "digital-employee-frontend", >> package.json
    echo   "version": "1.0.0", >> package.json
    echo   "type": "module", >> package.json
    echo   "scripts": { >> package.json
    echo     "dev": "vite", >> package.json
    echo     "build": "tsc && vite build", >> package.json
    echo     "preview": "vite preview", >> package.json
    echo     "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0" >> package.json
    echo   }, >> package.json
    echo   "dependencies": {}, >> package.json
    echo   "devDependencies": {} >> package.json
    echo } >> package.json
    
    REM 安装核心依赖
    call npm install react react-dom
    call npm install -D @types/react @types/react-dom vite @vitejs/plugin-react
    call npm install -D typescript
    call npm install -D tailwindcss postcss autoprefixer
    call npm install -D @types/node
    
    REM 安装UI和工具库
    call npm install antd
    call npm install axios
    call npm install zustand
    call npm install react-router-dom
    call npm install -D @types/react-router-dom
    
    REM 安装开发工具
    call npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
    call npm install -D prettier
    call npm install -D husky lint-staged
) else (
    call npm install
)
cd ..

call :print_success "前端依赖安装完成"

REM 安装后端依赖
call :print_info "安装后端依赖..."
cd api
if not exist "package.json" (
    call :print_info "初始化后端项目..."
    echo { > package.json
    echo   "name": "digital-employee-api", >> package.json
    echo   "version": "1.0.0", >> package.json
    echo   "type": "module", >> package.json
    echo   "scripts": { >> package.json
    echo     "dev": "nodemon", >> package.json
    echo     "build": "tsc", >> package.json
    echo     "start": "node dist/server.js", >> package.json
    echo     "test": "jest", >> package.json
    echo     "lint": "eslint . --ext ts --report-unused-disable-directives --max-warnings 0" >> package.json
    echo   }, >> package.json
    echo   "dependencies": {}, >> package.json
    echo   "devDependencies": {} >> package.json
    echo } >> package.json
    
    REM 安装核心依赖
    call npm install express cors helmet compression
    call npm install -D @types/express @types/cors @types/compression
    call npm install -D typescript ts-node nodemon
    
    REM 安装数据库和缓存
    call npm install @supabase/supabase-js
    call npm install redis
    call npm install -D @types/redis
    
    REM 安装工具库
    call npm install jsonwebtoken bcryptjs joi winston
    call npm install -D @types/jsonwebtoken @types/bcryptjs
    
    REM 安装文件存储
    call npm install @aws-sdk/client-s3
    call npm install minio
    
    REM 安装AI服务
    call npm install openai
    call npm install @azure/cognitiveservices-speech
    
    REM 安装开发工具
    call npm install -D eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
    call npm install -D prettier
    call npm install -D jest @types/jest ts-jest
    call npm install -D supertest @types/supertest
) else (
    call npm install
)
cd ..

call :print_success "后端依赖安装完成"

REM 创建基础配置文件
call :print_info "创建基础配置文件..."

REM 创建前端配置文件
if not exist "src\vite.config.ts" (
    echo import { defineConfig } from 'vite' > src/vite.config.ts
    echo import react from '@vitejs/plugin-react' >> src/vite.config.ts
    echo import path from 'path' >> src/vite.config.ts
    echo. >> src/vite.config.ts
    echo export default defineConfig({ >> src/vite.config.ts
    echo   plugins: [react()], >> src/vite.config.ts
    echo   resolve: { >> src/vite.config.ts
    echo     alias: { >> src/vite.config.ts
    echo       '@': path.resolve(__dirname, './src'), >> src/vite.config.ts
    echo     }, >> src/vite.config.ts
    echo   }, >> src/vite.config.ts
    echo   server: { >> src/vite.config.ts
    echo     port: 3000, >> src/vite.config.ts
    echo     proxy: { >> src/vite.config.ts
    echo       '/api': { >> src/vite.config.ts
    echo         target: 'http://localhost:3001', >> src/vite.config.ts
    echo         changeOrigin: true, >> src/vite.config.ts
    echo       }, >> src/vite.config.ts
    echo       '/ws': { >> src/vite.config.ts
    echo         target: 'ws://localhost:3001', >> src/vite.config.ts
    echo         ws: true, >> src/vite.config.ts
    echo       }, >> src/vite.config.ts
    echo     }, >> src/vite.config.ts
    echo   }, >> src/vite.config.ts
    echo }) >> src/vite.config.ts
)

REM 创建后端配置文件
if not exist "api\tsconfig.json" (
    echo { > api/tsconfig.json
    echo   "compilerOptions": { >> api/tsconfig.json
    echo     "target": "ES2020", >> api/tsconfig.json
    echo     "module": "commonjs", >> api/tsconfig.json
    echo     "lib": ["ES2020"], >> api/tsconfig.json
    echo     "outDir": "./dist", >> api/tsconfig.json
    echo     "rootDir": "./", >> api/tsconfig.json
    echo     "strict": true, >> api/tsconfig.json
    echo     "esModuleInterop": true, >> api/tsconfig.json
    echo     "skipLibCheck": true, >> api/tsconfig.json
    echo     "forceConsistentCasingInFileNames": true, >> api/tsconfig.json
    echo     "resolveJsonModule": true, >> api/tsconfig.json
    echo     "declaration": true, >> api/tsconfig.json
    echo     "declarationMap": true, >> api/tsconfig.json
    echo     "sourceMap": true >> api/tsconfig.json
    echo   }, >> api/tsconfig.json
    echo   "include": ["**/*"], >> api/tsconfig.json
    echo   "exclude": ["node_modules", "dist", "tests"] >> api/tsconfig.json
    echo } >> api/tsconfig.json
)

call :print_success "配置文件创建完成"

REM 初始化Git仓库
if not exist ".git" (
    call :print_info "初始化Git仓库..."
    git init
    
    REM 创建.gitignore文件
    echo # Dependencies > .gitignore
    echo node_modules/ >> .gitignore
    echo npm-debug.log* >> .gitignore
    echo yarn-debug.log* >> .gitignore
    echo yarn-error.log* >> .gitignore
    echo. >> .gitignore
    echo # Build outputs >> .gitignore
    echo dist/ >> .gitignore
    echo build/ >> .gitignore
    echo *.tsbuildinfo >> .gitignore
    echo. >> .gitignore
    echo # Environment variables >> .gitignore
    echo .env >> .gitignore
    echo .env.local >> .gitignore
    echo .env.development.local >> .gitignore
    echo .env.test.local >> .gitignore
    echo .env.production.local >> .gitignore
    echo. >> .gitignore
    echo # Logs >> .gitignore
    echo logs/ >> .gitignore
    echo *.log >> .gitignore
    echo. >> .gitignore
    echo # Runtime data >> .gitignore
    echo pids/ >> .gitignore
    echo *.pid >> .gitignore
    echo *.seed >> .gitignore
    echo *.pid.lock >> .gitignore
    echo. >> .gitignore
    echo # Coverage directory used by tools like istanbul >> .gitignore
    echo coverage/ >> .gitignore
    echo *.lcov >> .gitignore
    echo. >> .gitignore
    echo # Dependency directories >> .gitignore
    echo jspm_packages/ >> .gitignore
    echo. >> .gitignore
    echo # Optional npm cache directory >> .gitignore
    echo .npm >> .gitignore
    echo. >> .gitignore
    echo # Optional REPL history >> .gitignore
    echo .node_repl_history >> .gitignore
    echo. >> .gitignore
    echo # Output of 'npm pack' >> .gitignore
    echo *.tgz >> .gitignore
    echo. >> .gitignore
    echo # Yarn Integrity file >> .gitignore
    echo .yarn-integrity >> .gitignore
    echo. >> .gitignore
    echo # dotenv environment variables file >> .gitignore
    echo .env.test >> .gitignore
    echo. >> .gitignore
    echo # parcel-bundler cache (https://parceljs.org/) >> .gitignore
    echo .cache >> .gitignore
    echo .parcel-cache >> .gitignore
    echo. >> .gitignore
    echo # Next.js build output >> .gitignore
    echo .next >> .gitignore
    echo. >> .gitignore
    echo # Nuxt.js build / generate output >> .gitignore
    echo .nuxt >> .gitignore
    echo dist >> .gitignore
    echo. >> .gitignore
    echo # Storybook build outputs >> .gitignore
    echo .out >> .gitignore
    echo .storybook-out >> .gitignore
    echo. >> .gitignore
    echo # Temporary folders >> .gitignore
    echo tmp/ >> .gitignore
    echo temp/ >> .gitignore
    echo. >> .gitignore
    echo # Editor directories and files >> .gitignore
    echo .vscode/* >> .gitignore
    echo !.vscode/extensions.json >> .gitignore
    echo .idea >> .gitignore
    echo .DS_Store >> .gitignore
    echo *.suo >> .gitignore
    echo *.ntvs* >> .gitignore
    echo *.njsproj >> .gitignore
    echo *.sln >> .gitignore
    echo *.sw? >> .gitignore
    echo. >> .gitignore
    echo # Docker >> .gitignore
    echo .docker/ >> .gitignore
    echo. >> .gitignore
    echo # Uploads >> .gitignore
    echo uploads/ >> .gitignore
    echo. >> .gitignore
    echo # OS generated files >> .gitignore
    echo .DS_Store >> .gitignore
    echo .DS_Store? >> .gitignore
    echo ._ * >> .gitignore
    echo .Spotlight-V100 >> .gitignore
    echo .Trashes >> .gitignore
    echo ehthumbs.db >> .gitignore
    echo Thumbs.db >> .gitignore
    
    git add .
    git commit -m "Initial commit: Digital Employee Project Setup"
    
    call :print_success "Git仓库初始化完成"
) else (
    call :print_warning "Git仓库已存在，跳过初始化"
)

REM 创建Docker网络
call :print_info "创建Docker网络..."
docker network create digital-employee-network 2>nul
call :print_success "Docker网络创建完成"

REM 显示服务状态
call :print_info "服务状态检查..."
docker-compose ps

REM 显示访问信息
call :print_success "🎉 项目初始化完成！"
echo.
echo ==========================================
echo 🌐 服务访问地址：
echo    前端应用: http://localhost:3000
echo    后端API: http://localhost:3001
echo    API文档: http://localhost:3001/docs
echo    MinIO控制台: http://localhost:9001
echo    PgAdmin: http://localhost:5050
echo    Redis Commander: http://localhost:8081
echo.
echo 📋 后续步骤：
echo    1. 根据需要修改 .env 文件
echo    2. 启动前端开发服务器: cd src ^&^& npm run dev
echo    3. 启动后端开发服务器: cd api ^&^& npm run dev
echo    4. 访问 http://localhost:3000 开始使用
echo ==========================================
echo.
echo 🔧 常用命令：
echo    查看日志: docker-compose logs -f [service-name]
echo    停止服务: docker-compose down
echo    重启服务: docker-compose restart [service-name]
echo    进入容器: docker-compose exec [service-name] /bin/bash
echo.

REM 错误处理
if %errorlevel% neq 0 (
    call :print_error "脚本执行失败"
    pause
    exit /b 1
)

call :print_success "✅ 所有任务执行完成！"
pause

endlocal