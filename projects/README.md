# 项目目录

本目录包含 YDS-Lab 的所有项目和项目模板。

## 📁 目录结构

### 🚀 活跃项目
- `001-dewatermark-ai/` - AI去水印项目
  - 基于 Tauri + Python 的桌面应用
  - 包含前端UI、后端服务和AI模型

### 📋 项目模板
- `templates/` - 项目模板库
  - `tauri-python-ai/` - Tauri+Python+AI 项目模板

## 🎯 项目管理规范

### 项目结构标准
每个项目应包含：
```
project-name/
├── README.md          # 项目说明
├── requirements.txt   # Python依赖 (如适用)
├── package.json       # Node.js依赖 (如适用)
├── docs/             # 项目文档
├── src/              # 源代码
├── tests/            # 测试代码
├── output/           # 输出文件
└── backups/          # 备份文件
```

### 命名规范
- 项目名称：使用小写字母和连字符 (`project-name`)
- 目录名称：简洁明确，避免特殊字符
- 文档文件：使用 Markdown 格式

## 🛠️ 项目创建

### 使用模板创建新项目
```bash
# 使用工具创建项目
python tools/project/create_project.py

# 手动从模板复制
cp -r templates/tauri-python-ai/ new-project-name/
```

### 项目初始化检查清单
- [ ] 更新 README.md 项目信息
- [ ] 配置依赖文件 (requirements.txt/package.json)
- [ ] 设置版本控制 (.gitignore)
- [ ] 创建基本目录结构
- [ ] 编写初始文档

## 📊 项目状态

| 项目名称 | 状态 | 技术栈 | 描述 |
|---------|------|--------|------|
| 001-dewatermark-ai | 🟢 活跃 | Tauri+Python+AI | AI去水印桌面应用 |

## 🔄 项目生命周期

1. **规划阶段** - 在 `/Struc/PlanningDept/` 进行项目规划
2. **开发阶段** - 在本目录创建项目文件夹
3. **测试阶段** - 使用 `/tools/` 中的测试工具
4. **部署阶段** - 参考项目内的部署文档
5. **维护阶段** - 定期更新和备份

## 📝 贡献指南

- 新项目请先在规划部门讨论可行性
- 遵循既定的代码规范和文档标准
- 及时更新项目状态和文档
- 重要变更需要在会议中讨论