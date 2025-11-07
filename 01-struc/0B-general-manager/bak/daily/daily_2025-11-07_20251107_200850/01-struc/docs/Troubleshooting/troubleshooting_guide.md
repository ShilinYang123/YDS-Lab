# Trae平台故障排除指南

## 快速诊断检查清单

### 系统启动问题
- [ ] 检查Python环境是否正确
- [ ] 验证依赖包是否完整安装
- [ ] 确认配置文件格式正确
- [ ] 检查端口是否被占用
- [ ] 验证文件权限设置

### 智能体无响应
- [ ] 检查智能体进程状态
- [ ] 查看智能体日志文件
- [ ] 验证配置文件完整性
- [ ] 检查内存和CPU使用率
- [ ] 测试网络连接

### MCP服务故障
- [ ] 检查MCP服务进程
- [ ] 验证MCP配置文件
- [ ] 测试MCP连接
- [ ] 检查依赖服务状态
- [ ] 查看MCP日志

## 详细故障排除

### 1. 系统启动失败

#### 症状描述
- 系统无法启动
- 启动过程中出现错误
- 服务启动后立即退出

#### 可能原因
1. **Python环境问题**
   - Python版本不兼容
   - 虚拟环境未激活
   - 路径配置错误

2. **依赖包问题**
   - 必需包未安装
   - 包版本冲突
   - 包损坏

3. **配置文件问题**
   - 配置文件格式错误
   - 必需配置项缺失
   - 路径配置错误

#### 解决步骤

**步骤1: 检查Python环境**
```bash
# 检查Python版本
python --version

# 检查虚拟环境
which python
pip list

# 激活虚拟环境
cd S:/YDS-Lab
.venv/Scripts/activate
```

**步骤2: 验证依赖包**
```bash
# 检查依赖包
pip check

# 重新安装依赖
pip install -r requirements.txt

# 检查特定包
pip show package_name
```

**步骤3: 验证配置文件**
```bash
# 检查配置文件语法
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 验证配置完整性
python tools/check_config.py
```

### 2. 智能体无响应

#### 症状描述
- 智能体不响应请求
- 操作界面无反应
- 任务执行卡住

#### 可能原因
1. **进程问题**
   - 智能体进程崩溃
   - 进程僵死
   - 内存不足

2. **配置问题**
   - 智能体配置错误
   - 权限设置问题
   - 网络配置错误

3. **资源问题**
   - CPU使用率过高
   - 内存不足
   - 磁盘空间不足

#### 解决步骤

**步骤1: 检查进程状态**
```bash
# 检查智能体进程
Get-Process | Where-Object {$_.ProcessName -like "*agent*"}

# 检查端口占用
netstat -ano | findstr :8000

# 检查系统资源
Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
```

**步骤2: 重启智能体**
```bash
# 停止智能体
cd S:/YDS-Lab/tools/scripts
./stop_agents.bat

# 启动智能体
./start_agents.bat

# 检查启动状态
./check_agent_status.bat
```

**步骤3: 检查日志**
```bash
# 查看智能体日志
Get-Content S:/YDS-Lab/logs/agents/ceo.log -Tail 50

# 查看系统日志
Get-Content S:/YDS-Lab/logs/system.log -Tail 50
```

### 3. MCP服务故障

#### 症状描述
- MCP工具无法使用
- 连接超时错误
- 功能执行失败

#### 可能原因
1. **服务问题**
   - MCP服务未启动
   - 服务配置错误
   - 依赖服务故障

2. **网络问题**
   - 端口被占用
   - 防火墙阻止
   - 网络连接问题

3. **认证问题**
   - API密钥错误
   - 权限不足
   - 认证过期

#### 解决步骤

**步骤1: 检查MCP服务**
```bash
# 检查MCP进程
Get-Process | Where-Object {$_.ProcessName -like "*mcp*"}

# 检查MCP配置
python tools/check_mcp_config.py

# 测试MCP连接
python tools/test_mcp_connection.py
```

**步骤2: 重启MCP服务**
```bash
# 停止MCP集群
cd S:/YDS-Lab/Struc/MCPCluster
./stop_mcp_cluster.bat

# 启动MCP集群
./start_mcp_cluster.bat

# 验证服务状态
./check_mcp_status.bat
```

**步骤3: 验证配置**
```bash
# 检查GitHub MCP配置
cd S:/YDS-Lab/Struc/MCPCluster/GitHub
python github_mcp_server.py --check-config

# 检查Excel MCP配置
cd S:/YDS-Lab/Struc/MCPCluster/Excel
python excel_mcp_server.py --check-config
```

### 4. 性能问题

#### 症状描述
- 系统响应缓慢
- 操作延迟严重
- 资源使用率高

#### 可能原因
1. **资源不足**
   - CPU使用率过高
   - 内存不足
   - 磁盘I/O瓶颈

2. **配置问题**
   - 并发设置不当
   - 缓存配置错误
   - 超时设置过短

3. **数据问题**
   - 数据量过大
   - 查询效率低
   - 缓存失效

#### 解决步骤

**步骤1: 性能监控**
```bash
# 监控系统资源
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"

# 监控进程资源
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

**步骤2: 优化配置**
```yaml
# 调整并发设置
performance:
  max_concurrent_tasks: 10
  worker_threads: 4
  connection_pool_size: 20

# 优化缓存配置
cache:
  enabled: true
  max_size: 1000
  ttl: 3600
```

**步骤3: 数据优化**
```bash
# 清理日志文件
cd S:/YDS-Lab/logs
./cleanup_logs.bat

# 优化数据库
python tools/optimize_database.py

# 重建索引
python tools/rebuild_indexes.py
```

## 常用诊断命令

### 系统状态检查
```bash
# 检查系统整体状态
python tools/system_health_check.py

# 检查服务状态
python tools/service_status_check.py

# 检查配置完整性
python tools/config_validation.py
```

### 日志分析
```bash
# 查看错误日志
Get-Content S:/YDS-Lab/logs/error.log | Select-String "ERROR"

# 分析性能日志
python tools/analyze_performance_logs.py

# 生成诊断报告
python tools/generate_diagnostic_report.py
```

### 网络诊断
```bash
# 测试网络连接
Test-NetConnection localhost -Port 8000

# 检查DNS解析
nslookup github.com

# 测试API连接
python tools/test_api_connectivity.py
```

## 紧急联系信息

### 技术支持
- **系统管理员**: admin@yds-lab.com
- **技术支持**: support@yds-lab.com
- **紧急热线**: +86-xxx-xxxx-xxxx

### 升级路径
1. **一级支持**: 现场技术人员
2. **二级支持**: 系统管理员
3. **三级支持**: 开发团队
4. **紧急支持**: 技术总监

### 服务时间
- **工作日**: 9:00-18:00
- **紧急支持**: 24/7
- **响应时间**: 
  - 紧急问题: 30分钟内
  - 一般问题: 2小时内
  - 非紧急问题: 24小时内

---
*故障排除指南版本: v1.0*
*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
