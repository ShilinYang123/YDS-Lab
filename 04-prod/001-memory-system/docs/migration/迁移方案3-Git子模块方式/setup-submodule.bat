@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo    JS003-Trae长记忆功能 Git子模块设置
echo ==========================================
echo.

:: 检查参数
if "%~1"=="" (
    echo ❌ 错误: 请提供目标项目路径
    echo.
    echo 用法: %~nx0 ^<目标项目路径^> [子模块路径] [远程仓库URL]
    echo.
    echo 示例:
    echo   %~nx0 "C:\MyProject"
    echo   %~nx0 "C:\MyProject" "src/memory-system"
    echo   %~nx0 "C:\MyProject" "src/memory-system" "https://github.com/user/js003-memory.git"
    echo.
    pause
    exit /b 1
)

set "TARGET_PROJECT=%~1"
set "SUBMODULE_PATH=%~2"
set "REMOTE_URL=%~3"

:: 设置默认值
if "%SUBMODULE_PATH%"=="" set "SUBMODULE_PATH=src/memory-system"
if "%REMOTE_URL%"=="" set "REMOTE_URL=file:///S:/HQ-OA/tools/LongMemory/TraeLM"

echo 📋 配置信息:
echo   目标项目: %TARGET_PROJECT%
echo   子模块路径: %SUBMODULE_PATH%
echo   源仓库: %REMOTE_URL%
echo.

:: 检查目标项目是否存在
if not exist "%TARGET_PROJECT%" (
    echo ❌ 错误: 目标项目路径不存在: %TARGET_PROJECT%
    pause
    exit /b 1
)

:: 检查目标项目是否为Git仓库
cd /d "%TARGET_PROJECT%"
git status >nul 2>&1
if errorlevel 1 (
    echo ⚠️  目标项目不是Git仓库，正在初始化...
    git init
    if errorlevel 1 (
        echo ❌ Git仓库初始化失败
        pause
        exit /b 1
    )
    echo ✅ Git仓库初始化成功
    echo.
)

:: 检查子模块路径是否已存在
if exist "%SUBMODULE_PATH%" (
    echo ⚠️  子模块路径已存在: %SUBMODULE_PATH%
    echo 是否要删除现有内容并重新设置? (y/N)
    set /p "confirm="
    if /i not "!confirm!"=="y" (
        echo 操作已取消
        pause
        exit /b 0
    )
    
    echo 🗑️  删除现有子模块...
    git submodule deinit -f "%SUBMODULE_PATH%" 2>nul
    git rm -f "%SUBMODULE_PATH%" 2>nul
    rmdir /s /q "%SUBMODULE_PATH%" 2>nul
    if exist ".git\modules\%SUBMODULE_PATH%" (
        rmdir /s /q ".git\modules\%SUBMODULE_PATH%" 2>nul
    )
)

echo.
echo 🚀 开始设置Git子模块...
echo.

:: 添加子模块
echo 📥 添加子模块...
git submodule add "%REMOTE_URL%" "%SUBMODULE_PATH%"
if errorlevel 1 (
    echo ❌ 子模块添加失败
    pause
    exit /b 1
)

:: 初始化子模块
echo 🔧 初始化子模块...
git submodule init
if errorlevel 1 (
    echo ❌ 子模块初始化失败
    pause
    exit /b 1
)

:: 更新子模块
echo 📦 更新子模块内容...
git submodule update
if errorlevel 1 (
    echo ❌ 子模块更新失败
    pause
    exit /b 1
)

:: 检查子模块状态
echo.
echo 📊 子模块状态:
git submodule status

:: 创建必要的目录结构
echo.
echo 📁 创建项目结构...

if not exist "config" mkdir config
if not exist "config\memory-rules" mkdir config\memory-rules

:: 复制配置文件
echo 📋 复制配置文件...
if exist "%SUBMODULE_PATH%\.trae\rules\personal-rules.yaml" (
    copy "%SUBMODULE_PATH%\.trae\rules\personal-rules.yaml" "config\memory-rules\" >nul
    echo   ✅ personal-rules.yaml
)
if exist "%SUBMODULE_PATH%\.trae\rules\project-rules.yaml" (
    copy "%SUBMODULE_PATH%\.trae\rules\project-rules.yaml" "config\memory-rules\" >nul
    echo   ✅ project-rules.yaml
)

:: 检查package.json是否存在
if not exist "package.json" (
    echo 📦 创建package.json...
    (
        echo {
        echo   "name": "project-with-memory-system",
        echo   "version": "1.0.0",
        echo   "description": "Project integrated with JS003 Long-term Memory System",
        echo   "main": "src/index.ts",
        echo   "scripts": {
        echo     "build": "npm run build:memory && tsc",
        echo     "build:memory": "cd %SUBMODULE_PATH% && npm run build",
        echo     "test": "npm run test:memory && jest",
        echo     "test:memory": "cd %SUBMODULE_PATH% && npm test",
        echo     "dev": "npm run dev:memory && npm run dev:main",
        echo     "dev:memory": "cd %SUBMODULE_PATH% && npm run dev",
        echo     "dev:main": "nodemon src/index.ts",
        echo     "update:memory": "git submodule update --remote %SUBMODULE_PATH%",
        echo     "install:all": "npm install && cd %SUBMODULE_PATH% && npm install"
        echo   },
        echo   "dependencies": {
        echo     "yaml": "^2.3.4",
        echo     "uuid": "^9.0.1",
        echo     "lodash": "^4.17.21"
        echo   },
        echo   "devDependencies": {
        echo     "@types/node": "^20.10.0",
        echo     "@types/uuid": "^9.0.7",
        echo     "@types/lodash": "^4.14.202",
        echo     "typescript": "^5.3.0",
        echo     "nodemon": "^3.0.2",
        echo     "jest": "^29.7.0"
        echo   }
        echo }
    ) > package.json
    echo   ✅ package.json 已创建
)

:: 检查tsconfig.json是否存在
if not exist "tsconfig.json" (
    echo 🔧 创建tsconfig.json...
    (
        echo {
        echo   "compilerOptions": {
        echo     "target": "ES2020",
        echo     "module": "commonjs",
        echo     "lib": ["ES2020"],
        echo     "outDir": "./dist",
        echo     "rootDir": "./src",
        echo     "strict": true,
        echo     "esModuleInterop": true,
        echo     "skipLibCheck": true,
        echo     "forceConsistentCasingInFileNames": true,
        echo     "resolveJsonModule": true,
        echo     "declaration": true,
        echo     "declarationMap": true,
        echo     "sourceMap": true,
        echo     "baseUrl": "./src",
        echo     "paths": {
        echo       "@memory/*": ["%SUBMODULE_PATH:\=/%/src/*"],
        echo       "@memory-config/*": ["%SUBMODULE_PATH:\=/%/src/config/*"],
        echo       "@memory-services/*": ["%SUBMODULE_PATH:\=/%/src/services/*"],
        echo       "@memory-utils/*": ["%SUBMODULE_PATH:\=/%/src/utils/*"],
        echo       "@memory-types/*": ["%SUBMODULE_PATH:\=/%/src/types/*"]
        echo     }
        echo   },
        echo   "include": [
        echo     "src/**/*",
        echo     "%SUBMODULE_PATH:\=/%/src/**/*"
        echo   ],
        echo   "exclude": [
        echo     "node_modules",
        echo     "dist",
        echo     "**/*.test.ts"
        echo   ]
        echo }
    ) > tsconfig.json
    echo   ✅ tsconfig.json 已创建
)

:: 创建示例集成文件
if not exist "src" mkdir src

echo 📝 创建集成示例...
(
    echo // src/memory-integration-example.ts
    echo // JS003-Trae长记忆功能 Git子模块集成示例
    echo.
    echo import { LongTermMemorySystem } from '../%SUBMODULE_PATH:\=/%/src';
    echo import type { Memory, RetrievalQuery } from '../%SUBMODULE_PATH:\=/%/src/types';
    echo.
    echo export class ProjectMemoryService {
    echo   private memorySystem: LongTermMemorySystem;
    echo   private initialized = false;
    echo.
    echo   constructor(^) {
    echo     const config = {
    echo       rules: {
    echo         personalRulesPath: './config/memory-rules/personal-rules.yaml',
    echo         projectRulesPath: './config/memory-rules/project-rules.yaml'
    echo       }
    echo     };
    echo     
    echo     this.memorySystem = new LongTermMemorySystem(config^);
    echo   }
    echo.
    echo   async initialize(^) {
    echo     if (^!this.initialized^) {
    echo       await this.memorySystem.initialize(^);
    echo       this.initialized = true;
    echo       console.log('✅ 项目记忆服务初始化完成'^);
    echo     }
    echo   }
    echo.
    echo   async storeProjectMemory(content: string, type: string, metadata?: any^) {
    echo     await this.ensureInitialized(^);
    echo     
    echo     return await this.memorySystem.storeMemory({
    echo       content,
    echo       type,
    echo       tags: ['project', type],
    echo       metadata: {
    echo         ...metadata,
    echo         projectName: 'your-project',
    echo         timestamp: new Date(^).toISOString(^),
    echo         source: 'submodule_integration'
    echo       }
    echo     }^);
    echo   }
    echo.
    echo   async getProjectContext(query: string^) {
    echo     await this.ensureInitialized(^);
    echo     
    echo     const memories = await this.memorySystem.retrieveMemories({
    echo       query,
    echo       tags: ['project'],
    echo       limit: 10,
    echo       threshold: 0.7
    echo     }^);
    echo.
    echo     const enhancementContext = await this.memorySystem.getEnhancementContext({
    echo       query,
    echo       includeRules: true,
    echo       includeMemories: true,
    echo       maxMemories: 5
    echo     }^);
    echo.
    echo     return {
    echo       memories,
    echo       enhancementContext
    echo     };
    echo   }
    echo.
    echo   private async ensureInitialized(^) {
    echo     if (^!this.initialized^) {
    echo       await this.initialize(^);
    echo     }
    echo   }
    echo }
    echo.
    echo // 使用示例
    echo async function example(^) {
    echo   const memoryService = new ProjectMemoryService(^);
    echo   await memoryService.initialize(^);
    echo.
    echo   // 存储项目记忆
    echo   await memoryService.storeProjectMemory(
    echo     '实现了用户认证功能',
    echo     'feature_implementation',
    echo     { module: 'auth', complexity: 'medium' }
    echo   ^);
    echo.
    echo   // 检索项目上下文
    echo   const context = await memoryService.getProjectContext('用户认证'^);
    echo   console.log('项目上下文:', context^);
    echo }
) > "src\memory-integration-example.ts"

:: 创建更新脚本
echo 📜 创建更新脚本...
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo echo 🔄 更新长记忆功能子模块...
    echo.
    echo :: 检查是否有未提交的更改
    echo git diff-index --quiet HEAD --
    echo if errorlevel 1 (
    echo     echo ❌ 请先提交当前更改
    echo     pause
    echo     exit /b 1
    echo ^)
    echo.
    echo :: 更新子模块
    echo echo 📥 拉取最新更改...
    echo git submodule update --remote %SUBMODULE_PATH%
    echo.
    echo :: 检查是否有更新
    echo git diff --quiet %SUBMODULE_PATH%
    echo if not errorlevel 1 (
    echo     echo ✅ 子模块已是最新版本
    echo     pause
    echo     exit /b 0
    echo ^)
    echo.
    echo :: 显示更新内容
    echo echo 📋 子模块更新内容:
    echo cd %SUBMODULE_PATH%
    echo git log --oneline HEAD@{1}..HEAD
    echo cd ..\..
    echo.
    echo :: 提交更新
    echo echo ✅ 提交子模块更新
    echo git add %SUBMODULE_PATH%
    echo for /f "tokens=*" %%%%i in ('cd %SUBMODULE_PATH% ^&^& git rev-parse --short HEAD'^) do set "COMMIT_HASH=%%%%i"
    echo git commit -m "Update memory-system submodule to %%COMMIT_HASH%%"
    echo echo 🎉 子模块更新完成
    echo pause
) > "update-memory-system.bat"

:: 安装依赖
echo.
echo 📦 安装依赖...
if exist "%SUBMODULE_PATH%\package.json" (
    echo   🔧 安装子模块依赖...
    cd "%SUBMODULE_PATH%"
    call npm install
    if errorlevel 1 (
        echo   ⚠️  子模块依赖安装失败，请手动安装
    ) else (
        echo   ✅ 子模块依赖安装成功
    )
    cd ..
    if "%SUBMODULE_PATH:~0,4%"=="src\" cd ..
)

echo   🔧 安装项目依赖...
call npm install
if errorlevel 1 (
    echo   ⚠️  项目依赖安装失败，请手动运行 npm install
) else (
    echo   ✅ 项目依赖安装成功
)

:: 提交初始设置
echo.
echo 💾 提交初始设置...
git add .
git commit -m "Add JS003 Long-term Memory System as submodule

- Added submodule at %SUBMODULE_PATH%
- Configured TypeScript paths for memory system
- Added integration example and scripts
- Copied configuration files"

if errorlevel 1 (
    echo   ⚠️  提交失败，可能没有更改需要提交
) else (
    echo   ✅ 初始设置已提交
)

:: 显示完成信息
echo.
echo ==========================================
echo           🎉 设置完成！
echo ==========================================
echo.
echo 📁 项目结构:
echo   %TARGET_PROJECT%\
echo   ├── %SUBMODULE_PATH%\          (Git子模块)
echo   ├── config\memory-rules\       (配置文件)
echo   ├── src\                       (你的代码)
echo   │   └── memory-integration-example.ts
echo   ├── package.json               (项目配置)
echo   ├── tsconfig.json              (TypeScript配置)
echo   └── update-memory-system.bat   (更新脚本)
echo.
echo 🚀 下一步操作:
echo   1. 查看集成示例: src\memory-integration-example.ts
echo   2. 运行测试: npm run test
echo   3. 构建项目: npm run build
echo   4. 更新子模块: update-memory-system.bat
echo.
echo 📚 有用的命令:
echo   git submodule status           - 查看子模块状态
echo   git submodule update --remote  - 更新子模块
echo   npm run install:all            - 安装所有依赖
echo   npm run update:memory          - 更新记忆系统
echo.
echo 📖 更多信息请查看: README.md
echo.
pause