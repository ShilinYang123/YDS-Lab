# YDS-Lab 生产部署标准规范

## 🎯 目标与原则

### 部署目标
- 确保系统稳定、安全、高效运行
- 实现快速部署和回滚
- 保证数据完整性和服务可用性
- 支持自动化部署和监控

### 设计原则
- **标准化**：统一部署流程和配置规范
- **自动化**：减少人工操作，降低错误率
- **可观测**：完整的监控和日志记录
- **可回滚**：支持快速回滚到稳定版本
- **安全性**：遵循安全最佳实践

## 📁 目录结构规范

### 生产环境目录结构
```
04-prod/
├── 001-memory-system/          # 长记忆系统生产版本
│   ├── src/                    # 源代码
│   ├── config/                 # 配置文件
│   ├── logs/                   # 运行日志
│   ├── backup/                 # 备份文件
│   └── scripts/                # 部署脚本
├── 002-mcp-service/            # MCP服务生产版本
├── 003-monitoring/             # 监控系统
├── deployment_checklist.md     # 部署检查清单
├── deployment_standards.md     # 本规范文档
├── rollback_procedures.md      # 回滚流程
└── maintenance_guide.md        # 维护指南
```

### 数据存储路径规范
```
01-struc/
├── 0B-general-manager/
│   └── logs/
│       ├── longmemory/         # 长记忆数据
│       │   └── lm_records.json
│       ├── errors/             # 错误日志
│       ├── audit/              # 审计日志
│       └── performance/        # 性能日志
└── backup/                     # 系统备份
    ├── config/                 # 配置备份
    ├── data/                   # 数据备份
    └── logs/                   # 日志备份
```

## 🔧 配置管理规范

### 环境变量配置
```bash
# 长记忆系统
export LONGMEMORY_PATH="01-struc/logs/longmemory/lm_records.json"
export MEMORY_SYSTEM_PORT=3000
export MEMORY_SYSTEM_HOST="localhost"

# MCP服务
export MCP_SERVICE_PORT=8080
export MCP_SERVICE_HOST="localhost"

# 监控系统
export MONITORING_ENABLED=true
export MONITORING_PORT=9090

# 日志配置
export LOG_LEVEL="INFO"
export LOG_MAX_SIZE="100MB"
export LOG_BACKUP_COUNT=10
```

### 配置文件规范
- 使用YAML格式进行配置
- 配置文件必须包含版本信息
- 支持环境变量覆盖
- 包含完整的注释说明

```yaml
# config/yds_ai_config.yaml
version: "1.0.0"
environment: "production"

long_memory:
  path: "${LONGMEMORY_PATH:01-struc/logs/longmemory/lm_records.json}"
  max_size: "${MEMORY_MAX_SIZE:100MB}"
  backup_count: "${BACKUP_COUNT:10}"

services:
  memory_system:
    host: "${MEMORY_SYSTEM_HOST:localhost}"
    port: "${MEMORY_SYSTEM_PORT:3000}"
  
  mcp_service:
    host: "${MCP_SERVICE_HOST:localhost}"
    port: "${MCP_SERVICE_PORT:8080}"

logging:
  level: "${LOG_LEVEL:INFO}"
  format: "json"
  rotation:
    max_size: "${LOG_MAX_SIZE:100MB}"
    backup_count: "${LOG_BACKUP_COUNT:10}"
```

## 🚀 部署流程规范

### 预部署检查
1. **环境验证**
   - 检查操作系统兼容性
   - 验证依赖版本
   - 确认网络连接
   - 检查磁盘空间

2. **配置验证**
   - 验证配置文件格式
   - 检查环境变量设置
   - 确认权限配置
   - 验证备份策略

3. **依赖检查**
   - 安装Python依赖
   - 安装Node.js依赖
   - 验证关键依赖版本
   - 检查依赖安全性

### 部署执行
1. **代码部署**
   ```bash
   # 拉取最新代码
   git pull origin main
   
   # 安装依赖
   pip install -r requirements.txt
   npm install
   
   # 运行测试
   python st.py
   ```

2. **配置部署**
   ```bash
   # 备份现有配置
   cp config/yds_ai_config.yaml config/backup/yds_ai_config.yaml.$(date +%Y%m%d_%H%M%S)
   
   # 部署新配置
   cp deployment/config/yds_ai_config.yaml config/
   
   # 验证配置
   python tools/config_validator.py
   ```

3. **服务启动**
   ```bash
   # 启动长记忆系统
   cd 04-prod/001-memory-system
   npm start
   
   # 启动MCP服务
   cd 04-prod/002-mcp-service
   npm start
   
   # 启动监控系统
   cd 04-prod/003-monitoring
   npm start
   ```

### 部署验证
1. **功能验证**
   - 检查长记忆系统状态
   - 验证MCP服务响应
   - 测试智能监控功能
   - 验证会议管理功能

2. **性能验证**
   - 检查响应时间
   - 验证内存使用率
   - 检查CPU使用率
   - 确认磁盘空间

3. **安全验证**
   - 检查访问权限
   - 验证数据加密
   - 确认审计日志
   - 检查备份策略

## 📊 监控与告警

### 监控指标
- **系统指标**：CPU、内存、磁盘、网络
- **应用指标**：响应时间、错误率、吞吐量
- **业务指标**：长记忆命中率、MCP调用次数
- **安全指标**：登录失败、异常访问、数据变更

### 告警规则
```yaml
alerts:
  - name: "high_cpu_usage"
    condition: "cpu_usage > 80%"
    duration: "5m"
    severity: "warning"
    
  - name: "service_down"
    condition: "service_status != 'running'"
    duration: "1m"
    severity: "critical"
    
  - name: "memory_leak"
    condition: "memory_usage > 90%"
    duration: "10m"
    severity: "critical"
```

## 🔒 安全规范

### 访问控制
- 使用最小权限原则
- 实施多因素认证
- 定期轮换访问密钥
- 记录所有访问操作

### 数据安全
- 敏感数据加密存储
- 传输数据加密
- 定期备份重要数据
- 实施数据脱敏

### 审计要求
- 记录所有配置变更
- 记录用户操作日志
- 保留审计日志至少6个月
- 定期审计安全事件

## 🔄 回滚策略

### 自动回滚触发条件
- 部署失败率超过阈值
- 关键服务不可用
- 性能指标严重下降
- 安全事件检测

### 回滚流程
1. **快速回滚**
   - 停止新服务
   - 恢复备份配置
   - 重启旧服务
   - 验证回滚结果

2. **完整回滚**
   - 恢复代码版本
   - 恢复配置文件
   - 恢复数据状态
   - 重新验证系统

## 📋 文档要求

### 部署文档
- 详细的部署步骤
- 完整的配置说明
- 故障排查指南
- 性能优化建议

### 变更记录
- 记录所有配置变更
- 记录版本升级历史
- 记录问题修复过程
- 记录性能优化措施

### 维护记录
- 定期维护日志
- 故障处理记录
- 性能监控报告
- 安全审计报告

---

**文档版本：** v1.0.0  
**最后更新：** 2024年12月  
**维护人员：** 雨俊 (高级软件专家)