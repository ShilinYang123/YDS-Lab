# 工具脚本目录

本目录包含 YDS-Lab 系统的核心维护和管理工具。

## 🔧 核心工具

### 系统管理
- `start.py` - 系统启动脚本
- `finish.py` - 系统完成脚本
- `refresh_env.bat` - 环境刷新批处理

### 结构管理
- `check_structure.py` - 目录结构检查
- `update_structure.py` - 目录结构更新
- `setup_git_path.py` - Git路径配置

### 功能模块
- `check/env_ready.py` - 环境就绪检查
- `docs/generate_meeting_log.py` - 会议日志生成
- `git/auto_push.py` - 自动Git推送
- `project/create_project.py` - 项目创建工具

## 📁 -sub 目录

`-sub/` 目录包含从老项目继承的工具集，作为功能库暂存：
- 🚫 **不会备份到Git** (已在.gitignore中排除)
- 📦 **按需提取** 需要时从中提取有用的工具
- 🔄 **逐步整合** 将有价值的工具整合到主工具集

## 📋 配置文件

配置文件已迁移到 `/config/` 目录统一管理：
- `finish_config.yaml` → `/config/finish_config.yaml`
- `startup_config.yaml` → `/config/startup_config.yaml`
- `structure_config.yaml` → `/config/structure_config.yaml`

## 🚀 使用方法

### 基本操作
```bash
# 启动系统
python tools/start.py

# 检查结构
python tools/check_structure.py

# 更新结构
python tools/update_structure.py

# 完成操作
python tools/finish.py
```

### 环境管理
```bash
# 刷新环境
tools/refresh_env.bat

# 检查环境就绪
python tools/check/env_ready.py
```

## 📝 开发规范

1. **新工具添加**: 按功能分类到对应子目录
2. **配置管理**: 统一使用 `/config/` 目录的配置文件
3. **文档更新**: 新增工具需更新本README
4. **测试验证**: 确保工具在不同环境下正常运行

## ⚠️ 注意事项

- `-sub/` 目录内容不会同步到Git仓库
- 修改核心工具前请先备份
- 配置文件路径已更改，注意更新引用