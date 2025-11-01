@echo off
setlocal enabledelayedexpansion

REM ========================================
REM JS003-Trae长记忆功能 源码复制脚本
REM 适用于Windows系统
REM ========================================

echo.
echo ========================================
echo   JS003-Trae长记忆功能 源码复制工具
echo ========================================
echo.

REM 设置默认路径
set "DEFAULT_SOURCE=S:\HQ-OA\tools\LongMemory\TraeLM"
set "DEFAULT_TARGET=.\src\memory-system"

REM 获取用户输入的源项目路径
set /p SOURCE_PATH="请输入源项目路径 (默认: %DEFAULT_SOURCE%): "
if "%SOURCE_PATH%"=="" set "SOURCE_PATH=%DEFAULT_SOURCE%"

REM 获取用户输入的目标路径
set /p TARGET_PATH="请输入目标路径 (默认: %DEFAULT_TARGET%): "
if "%TARGET_PATH%"=="" set "TARGET_PATH=%DEFAULT_TARGET%"

REM 检查源路径是否存在
if not exist "%SOURCE_PATH%" (
    echo ❌ 错误: 源项目路径不存在: %SOURCE_PATH%
    echo 请检查路径是否正确
    pause
    exit /b 1
)

echo.
echo 📋 复制配置:
echo    源路径: %SOURCE_PATH%
echo    目标路径: %TARGET_PATH%
echo.

REM 确认是否继续
set /p CONFIRM="是否继续复制? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo 操作已取消
    pause
    exit /b 0
)

echo.
echo 🚀 开始复制文件...

REM 创建目标目录结构
echo 📁 创建目录结构...
mkdir "%TARGET_PATH%" 2>nul
mkdir "%TARGET_PATH%\config" 2>nul
mkdir "%TARGET_PATH%\services" 2>nul
mkdir "%TARGET_PATH%\utils" 2>nul
mkdir "%TARGET_PATH%\types" 2>nul
mkdir "%TARGET_PATH%\tests" 2>nul
mkdir ".\.memory-system" 2>nul
mkdir ".\.memory-system\rules" 2>nul

REM 复制主入口文件
echo 📄 复制主入口文件...
if exist "%SOURCE_PATH%\src\index.ts" (
    copy "%SOURCE_PATH%\src\index.ts" "%TARGET_PATH%\index.ts" >nul
    echo    ✅ index.ts
) else (
    echo    ❌ 未找到 index.ts
)

REM 复制配置模块
echo 📁 复制配置模块...
if exist "%SOURCE_PATH%\src\config\" (
    xcopy "%SOURCE_PATH%\src\config\*" "%TARGET_PATH%\config\" /E /I /Y /Q >nul 2>&1
    echo    ✅ config/
) else (
    echo    ❌ 未找到 config/ 目录
)

REM 复制服务模块
echo 📁 复制服务模块...
if exist "%SOURCE_PATH%\src\services\" (
    xcopy "%SOURCE_PATH%\src\services\*" "%TARGET_PATH%\services\" /E /I /Y /Q >nul 2>&1
    echo    ✅ services/
) else (
    echo    ❌ 未找到 services/ 目录
)

REM 复制工具模块
echo 📁 复制工具模块...
if exist "%SOURCE_PATH%\src\utils\" (
    xcopy "%SOURCE_PATH%\src\utils\*" "%TARGET_PATH%\utils\" /E /I /Y /Q >nul 2>&1
    echo    ✅ utils/
) else (
    echo    ❌ 未找到 utils/ 目录
)

REM 复制类型定义
echo 📁 复制类型定义...
if exist "%SOURCE_PATH%\src\types\" (
    xcopy "%SOURCE_PATH%\src\types\*" "%TARGET_PATH%\types\" /E /I /Y /Q >nul 2>&1
    echo    ✅ types/
) else (
    echo    ❌ 未找到 types/ 目录
)

REM 复制测试文件
echo 📁 复制测试文件...
if exist "%SOURCE_PATH%\tests\" (
    xcopy "%SOURCE_PATH%\tests\*" "%TARGET_PATH%\tests\" /E /I /Y /Q >nul 2>&1
    echo    ✅ tests/
) else (
    echo    ⚠️  未找到 tests/ 目录 (可选)
)

REM 复制配置文件
echo 📁 复制配置文件...
if exist "%SOURCE_PATH%\.trae\rules\" (
    xcopy "%SOURCE_PATH%\.trae\rules\*" ".\.memory-system\rules\" /E /I /Y /Q >nul 2>&1
    echo    ✅ .memory-system/rules/
) else (
    echo    ❌ 未找到 .trae/rules/ 目录
)

REM 复制其他重要文件
echo 📄 复制其他重要文件...

if exist "%SOURCE_PATH%\package.json" (
    copy "%SOURCE_PATH%\package.json" "%TARGET_PATH%\package.json.reference" >nul
    echo    ✅ package.json (作为参考)
)

if exist "%SOURCE_PATH%\tsconfig.json" (
    copy "%SOURCE_PATH%\tsconfig.json" "%TARGET_PATH%\tsconfig.json.reference" >nul
    echo    ✅ tsconfig.json (作为参考)
)

if exist "%SOURCE_PATH%\README.md" (
    copy "%SOURCE_PATH%\README.md" "%TARGET_PATH%\README.original.md" >nul
    echo    ✅ README.md (原始文档)
)

echo.
echo 🔧 生成集成文件...

REM 生成集成示例文件
(
echo // 长记忆功能集成示例
echo // 生成时间: %date% %time%
echo.
echo import { LongTermMemorySystem } from './memory-system';
echo import type { Memory, RetrievalQuery } from './memory-system/types';
echo.
echo // 基本使用示例
echo export class AppMemoryService {
echo   private memorySystem: LongTermMemorySystem;
echo.
echo   constructor^(^) {
echo     this.memorySystem = new LongTermMemorySystem^(^);
echo   }
echo.
echo   async initialize^(^) {
echo     await this.memorySystem.initialize^(^);
echo     console.log^('✅ 长记忆功能初始化完成'^);
echo   }
echo.
echo   async storeMemory^(content: string, type: string = 'general'^) {
echo     return await this.memorySystem.storeMemory^({
echo       content,
echo       type,
echo       tags: [type],
echo       metadata: {
echo         timestamp: new Date^(^).toISOString^(^),
echo         source: 'app'
echo       }
echo     }^);
echo   }
echo.
echo   async searchMemories^(query: string, limit: number = 5^) {
echo     return await this.memorySystem.retrieveMemories^({
echo       query,
echo       limit,
echo       threshold: 0.7
echo     }^);
echo   }
echo }
) > "%TARGET_PATH%\integration-example.ts"

echo    ✅ integration-example.ts

REM 生成依赖清单
(
echo # 长记忆功能依赖清单
echo # 生成时间: %date% %time%
echo.
echo ## 核心依赖
echo ```json
echo {
echo   "dependencies": {
echo     "yaml": "^2.3.4",
echo     "uuid": "^9.0.1",
echo     "lodash": "^4.17.21"
echo   },
echo   "devDependencies": {
echo     "@types/uuid": "^9.0.7",
echo     "@types/lodash": "^4.14.202",
echo     "@types/node": "^20.10.0",
echo     "typescript": "^5.3.0"
echo   }
echo }
echo ```
echo.
echo ## 安装命令
echo ```bash
echo # 安装核心依赖
echo npm install yaml uuid lodash
echo.
echo # 安装开发依赖
echo npm install --save-dev @types/uuid @types/lodash @types/node typescript
echo ```
echo.
echo ## TypeScript配置
echo 确保 tsconfig.json 包含以下配置:
echo ```json
echo {
echo   "compilerOptions": {
echo     "target": "ES2020",
echo     "module": "commonjs",
echo     "lib": ["ES2020"],
echo     "strict": true,
echo     "esModuleInterop": true,
echo     "skipLibCheck": true,
echo     "forceConsistentCasingInFileNames": true,
echo     "resolveJsonModule": true,
echo     "declaration": true,
echo     "outDir": "./dist",
echo     "rootDir": "./src"
echo   }
echo }
echo ```
) > "%TARGET_PATH%\DEPENDENCIES.md"

echo    ✅ DEPENDENCIES.md

REM 统计复制结果
echo.
echo 📊 复制统计:
for /f %%i in ('dir /s /b "%TARGET_PATH%\*.ts" 2^>nul ^| find /c /v ""') do set TS_COUNT=%%i
for /f %%i in ('dir /s /b "%TARGET_PATH%\*.js" 2^>nul ^| find /c /v ""') do set JS_COUNT=%%i
for /f %%i in ('dir /s /b "%TARGET_PATH%\*.json" 2^>nul ^| find /c /v ""') do set JSON_COUNT=%%i
for /f %%i in ('dir /s /b "%TARGET_PATH%\*.md" 2^>nul ^| find /c /v ""') do set MD_COUNT=%%i

echo    TypeScript 文件: %TS_COUNT%
echo    JavaScript 文件: %JS_COUNT%
echo    JSON 文件: %JSON_COUNT%
echo    Markdown 文件: %MD_COUNT%

echo.
echo ✅ 复制完成！
echo.
echo 📋 后续步骤:
echo    1. 检查 %TARGET_PATH%\DEPENDENCIES.md 安装依赖
echo    2. 查看 %TARGET_PATH%\integration-example.ts 了解使用方法
echo    3. 根据项目需求调整导入路径
echo    4. 运行测试确保集成成功
echo.
echo 📚 参考文档:
echo    - 原始文档: %TARGET_PATH%\README.original.md
echo    - 依赖说明: %TARGET_PATH%\DEPENDENCIES.md
echo    - 集成示例: %TARGET_PATH%\integration-example.ts
echo.

pause