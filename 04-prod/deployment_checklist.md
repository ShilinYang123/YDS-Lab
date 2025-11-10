# YDS-Lab 生产部署检查清单

## 📋 部署前检查

### 环境准备
- [ ] 确认操作系统版本兼容性
- [ ] 检查Python版本 (≥3.8)
- [ ] 检查Node.js版本 (≥16)
- [ ] 确认PowerShell版本 (≥5.1)
- [ ] 验证Git安装和配置
- [ ] 检查网络连接和防火墙设置

### 依赖检查
- [ ] 安装Python依赖包
  ```bash
  pip install -r requirements.txt
  ```
- [ ] 安装Node.js依赖包
  ```bash
  cd 04-prod/001-memory-system
  npm install
  ```
- [ ] 验证关键依赖版本

### 配置文件检查
- [ ] 检查主配置文件 `config/yds_ai_config.yaml`
- [ ] 验证长记忆系统配置
- [ ] 确认环境变量设置
- [ ] 检查权限配置

## 🚀 部署步骤

### 1. 系统初始化
```bash
# 运行环境初始化脚本
python tools/init_trae_environment.py

# 验证初始化结果
python ch.py
```

### 2. 长记忆系统部署
```bash
# 进入长记忆系统目录
cd 04-prod/001-memory-system

# 安装依赖
npm install

# 启动服务
npm start

# 验证服务状态
npm run health-check
```

### 3. 系统测试
```bash
# 运行完整测试套件
python st.py

# 检查测试结果
cat coverage/report.txt
```

### 4. 服务验证
```bash
# 检查长记忆系统状态
curl http://localhost:3000/health

# 验证MCP服务
python tools/mcp/health_check.py

# 检查智能监控
python tools/LongMemory/health_check.py
```

## 📊 部署后验证

### 功能验证
- [ ] 长记忆系统正常运行
- [ ] MCP服务响应正常
- [ ] 智能监控功能激活
- [ ] 会议管理功能可用
- [ ] 文档生成功能正常

### 性能检查
- [ ] 系统响应时间 < 2秒
- [ ] 内存使用率 < 80%
- [ ] CPU使用率 < 70%
- [ ] 磁盘空间充足 (>1GB)

### 安全检查
- [ ] 访问权限控制正常
- [ ] 数据加密配置正确
- [ ] 审计日志功能启用
- [ ] 备份策略配置完成

## 🔄 回滚方案

### 紧急回滚
```bash
# 停止所有服务
npm run stop-all

# 恢复备份配置
cp config/backup/yds_ai_config.yaml.backup config/yds_ai_config.yaml

# 重启服务
npm start
```

### 数据恢复
```bash
# 从备份恢复长记忆数据
cp 01-struc/backup/lm_records.json.backup 01-struc/logs/longmemory/lm_records.json

# 验证数据完整性
python tools/LongMemory/validate_data.py
```

## 📞 故障排查

### 常见问题
1. **长记忆系统启动失败**
   - 检查Node.js版本
   - 验证端口占用情况
   - 查看错误日志

2. **MCP服务连接异常**
   - 检查网络配置
   - 验证服务端口
   - 重启MCP服务

3. **智能监控功能异常**
   - 检查配置文件路径
   - 验证权限设置
   - 查看监控日志

### 日志位置
- 长记忆系统日志：`04-prod/001-memory-system/logs/`
- 系统运行日志：`01-struc/logs/`
- 错误日志：`01-struc/logs/errors/`
- 审计日志：`01-struc/logs/audit/`

## 📋 维护计划

### 日常维护
- [ ] 检查系统运行状态
- [ ] 清理过期日志文件
- [ ] 备份重要数据
- [ ] 监控系统性能

### 定期维护
- [ ] 更新依赖包版本
- [ ] 检查安全补丁
- [ ] 优化系统配置
- [ ] 执行完整备份

---

**部署完成确认：**
- [ ] 所有服务正常运行
- [ ] 功能测试全部通过
- [ ] 性能指标符合要求
- [ ] 安全配置正确
- [ ] 备份策略生效
- [ ] 文档更新完成

**部署人员签名：** ________________ **日期：** ________________