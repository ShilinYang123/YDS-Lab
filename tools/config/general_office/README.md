# 配置文件目录

本目录统一管理项目的所有配置文件。

## 文件说明

### 系统配置
- `startup_config.yaml` - 系统启动配置
- `finish_config.yaml` - 系统完成配置  
- （已迁移）`tools/structure_config.yaml` - 目录结构配置（统一至 tools 目录）

## 配置文件规范

1. **命名规范**: 使用 `功能_config.扩展名` 格式
2. **格式优先级**: YAML > JSON > INI
3. **环境分离**: 
   - 开发环境: `*_config.dev.yaml`
   - 生产环境: `*_config.prod.yaml`
   - 本地环境: `*_config.local.yaml` (不提交到git)

## 安全注意事项

- 敏感信息请使用 `*.local.*` 文件存储
- 所有 `*.local.*` 文件已在 .gitignore 中排除
- API密钥等敏感数据请存放在 `models/config/` 目录

## 使用方法

配置文件应通过相应的工具脚本加载，避免硬编码路径。