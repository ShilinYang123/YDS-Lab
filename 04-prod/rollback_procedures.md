# YDS-Lab 系统回滚操作手册

## 🚨 紧急回滚流程

### 触发条件
- 系统服务不可用超过5分钟
- 关键功能出现严重错误
- 性能指标严重下降（响应时间>10秒）
- 安全漏洞或数据泄露
- 用户投诉激增

### 快速回滚（5分钟内）

#### 1. 立即停止服务
```bash
# 停止所有生产服务
cd 04-prod
npm run emergency-stop

# 或者分别停止各个服务
cd 001-memory-system && npm stop
cd 002-mcp-service && npm stop
cd 003-monitoring && npm stop
```

#### 2. 恢复配置备份
```bash
# 找到最新的配置备份
latest_backup=$(ls -t config/backup/yds_ai_config.yaml.* | head -1)

# 恢复配置文件
cp "$latest_backup" config/yds_ai_config.yaml

# 验证配置文件
python tools/config_validator.py
```

#### 3. 恢复数据备份
```bash
# 恢复长记忆数据
cp 01-struc/backup/data/lm_records.json.backup \
   01-struc/logs/longmemory/lm_records.json

# 验证数据完整性
python tools/LongMemory/validate_data.py
```

#### 4. 重启服务
```bash
# 启动核心服务
cd 04-prod/001-memory-system && npm start
cd 04-prod/002-mcp-service && npm start

# 等待服务启动
sleep 30

# 验证服务状态
curl http://localhost:3000/health
curl http://localhost:8080/health
```

## 🔄 完整回滚流程

### 版本回滚

#### 1. 确定回滚版本
```bash
# 查看可用版本
git tag -l | grep -E "^v[0-9]"

# 查看版本历史
git log --oneline -10

# 选择稳定版本（通常是上一个标签）
rollback_version="v1.0.0"  # 根据实际情况修改
```

#### 2. 代码回滚
```bash
# 创建回滚分支
git checkout -b rollback/$rollback_version

# 回滚到指定版本
git reset --hard $rollback_version

# 强制推送到远程（谨慎操作）
git push origin rollback/$rollback_version --force
```

#### 3. 依赖回滚
```bash
# 恢复requirements.txt备份
cp requirements.txt.backup requirements.txt

# 重新安装依赖
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# Node.js依赖回滚
cd 04-prod/001-memory-system
rm -rf node_modules package-lock.json
cp package-lock.json.backup package-lock.json
npm install
```

#### 4. 数据库回滚
```bash
# 如果有数据库变更，需要回滚
# 执行数据库回滚脚本
python tools/db_rollback.py --version $rollback_version

# 验证数据库状态
python tools/db_validator.py
```

### 配置回滚

#### 1. 配置版本管理
```bash
# 查看配置历史
ls -la config/backup/

# 选择回滚配置版本
config_backup="config/backup/yds_ai_config.yaml.20241201_120000"

# 恢复配置
cp "$config_backup" config/yds_ai_config.yaml
```

#### 2. 环境变量回滚
```bash
# 恢复环境变量配置
cp .env.backup .env

# 重新加载环境变量
source .env

# 验证环境变量
printenv | grep -E "(MEMORY|MCP|LOG)"
```

#### 3. 服务配置回滚
```bash
# 恢复服务配置
cd 04-prod/001-memory-system
cp config/app.json.backup config/app.json

cd ../002-mcp-service
cp config/mcp.json.backup config/mcp.json
```

## 📊 数据回滚

### 长记忆数据回滚

#### 1. 数据备份检查
```bash
# 查看可用数据备份
ls -la 01-struc/backup/data/

# 检查备份文件完整性
file 01-struc/backup/data/lm_records.json.backup
```

#### 2. 数据回滚执行
```bash
# 备份当前数据（以防万一）
cp 01-struc/logs/longmemory/lm_records.json \
   01-struc/logs/longmemory/lm_records.json.failed.$(date +%Y%m%d_%H%M%S)

# 恢复备份数据
cp 01-struc/backup/data/lm_records.json.backup \
   01-struc/logs/longmemory/lm_records.json

# 验证数据格式
python tools/LongMemory/validate_data.py
```

#### 3. 数据一致性检查
```bash
# 检查数据完整性
python tools/LongMemory/check_data_integrity.py

# 验证索引文件
python tools/LongMemory/validate_indexes.py

# 测试数据访问
python tools/LongMemory/test_data_access.py
```

### 日志文件回滚

#### 1. 日志备份恢复
```bash
# 恢复系统日志
cp 01-struc/backup/logs/system.log.backup 01-struc/logs/system.log

# 恢复错误日志
cp 01-struc/backup/logs/errors.log.backup 01-struc/logs/errors.log

# 恢复审计日志
cp 01-struc/backup/logs/audit.log.backup 01-struc/logs/audit.log
```

#### 2. 日志轮转恢复
```bash
# 恢复日志轮转配置
cp tools/logrotate.conf.backup /etc/logrotate.d/yds-lab

# 重新加载日志轮转服务
sudo systemctl reload rsyslog
```

## 🧪 回滚验证

### 功能验证

#### 1. 核心功能测试
```bash
# 测试长记忆系统
curl -X POST http://localhost:3000/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"key": "test", "value": "rollback_test"}'

# 测试MCP服务
curl -X GET http://localhost:8080/api/mcp/status

# 测试智能监控
python tools/LongMemory/test_monitoring.py
```

#### 2. 性能测试
```bash
# 运行性能测试
python tools/performance_test.py

# 检查响应时间
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:3000/health
```

#### 3. 数据验证
```bash
# 验证数据完整性
python tools/data_validation.py

# 检查数据一致性
python tools/consistency_check.py

# 验证备份数据
python tools/backup_validation.py
```

### 监控验证

#### 1. 系统监控
```bash
# 检查系统状态
python tools/system_health_check.py

# 验证监控指标
curl http://localhost:9090/metrics | grep -E "(memory|cpu|disk)"
```

#### 2. 服务监控
```bash
# 检查服务状态
systemctl status yds-memory
systemctl status yds-mcp
systemctl status yds-monitoring
```

#### 3. 日志监控
```bash
# 检查错误日志
tail -f 01-struc/logs/errors.log | grep -E "(ERROR|CRITICAL)"

# 检查系统日志
tail -f 01-struc/logs/system.log | grep -E "(WARNING|ERROR)"
```

## 📋 回滚记录

### 回滚信息记录
每次回滚操作后，必须记录以下信息：

```bash
# 创建回滚记录
cat > 01-struc/logs/rollback/$(date +%Y%m%d_%H%M%S).log << EOF
回滚时间: $(date)
回滚原因: [填写具体原因]
回滚版本: [填写回滚到的版本]
回滚人员: [填写操作人员]
影响范围: [填写影响的功能模块]
回滚结果: [填写回滚是否成功]
验证结果: [填写验证测试结果]
备注信息: [填写其他重要信息]
EOF
```

### 回滚报告
回滚完成后，需要生成回滚报告：

```bash
# 生成回滚报告
python tools/generate_rollback_report.py \
  --start-time "2024-12-01 12:00:00" \
  --end-time "2024-12-01 12:30:00" \
  --output "01-struc/logs/rollback/report_$(date +%Y%m%d_%H%M%S).html"
```

## ⚠️ 注意事项

### 回滚前准备
1. **数据备份**：回滚前必须备份当前数据
2. **通知相关人员**：提前通知所有相关人员
3. **准备应急方案**：制定应急处理预案
4. **检查回滚条件**：确认回滚条件是否满足

### 回滚中监控
1. **实时监控**：密切监控系统状态
2. **记录操作**：详细记录所有操作步骤
3. **及时沟通**：及时汇报回滚进展
4. **准备中断**：准备随时中断回滚操作

### 回滚后验证
1. **全面测试**：进行全面的功能测试
2. **性能验证**：验证系统性能指标
3. **用户确认**：确认用户业务正常
4. **持续监控**：持续监控系统状态

## 🆘 紧急联系方式

### 技术支持
- **主要联系人**：雨俊 (高级软件专家)
- **备用联系人**：一丁山先生 (项目负责人)
- **紧急热线**：[填写紧急联系电话]

### 升级路径
1. **一级支持**：系统管理员
2. **二级支持**：技术负责人
3. **三级支持**：项目管理层
4. **四级支持**：外部技术支持

---

**文档版本：** v1.0.0  
**最后更新：** 2024年12月  
**维护人员：** 雨俊 (高级软件专家)  
**审核人员：** 一丁山先生 (项目负责人)