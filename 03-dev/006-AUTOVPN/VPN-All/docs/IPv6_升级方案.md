# AUTOVPN IPv6 升级技术方案

## 1. 升级目标与范围

### 1.1 升级目标
- 实现客户端IPv4/IPv6双栈支持
- 保持现有IPv4服务完全兼容
- 支持IPv6隧道传输和代理服务
- 提供完整的回滚机制

### 1.2 升级范围
- 客户端网络连接模块
- 域名解析系统
- Hosts文件管理
- 代理服务配置
- 服务器端网络配置（需要服务器支持）

## 2. 现状分析

### 2.1 当前限制
1. **WebSocket隧道**: 仅支持IPv4连接 (`ws://192.210.206.52:443`)
2. **代理服务**: 仅监听IPv4地址 (`127.0.0.1`)
3. **域名解析**: 仅处理A记录(IPv4)，忽略AAAA记录(IPv6)
4. **Hosts文件**: 仅写入IPv4地址映射
5. **服务器配置**: 无IPv6监听端口

### 2.2 系统架构现状
```
客户端(IPv4 only) → WebSocket隧道(IPv4) → 服务器(IPv4) → 目标网站
     ↓                                              ↓
Hosts文件(IPv4)                              代理服务(IPv4)
```

## 3. 升级方案设计

### 3.1 总体架构
```
客户端(双栈) → WebSocket隧道(IPv4/IPv6) → 服务器(双栈) → 目标网站
     ↓                                                ↓
Hosts文件(IPv4/IPv6)                        代理服务(IPv4/IPv6)
```

### 3.2 技术路线
采用**渐进式升级**策略，分四个阶段实施：

#### 阶段一：客户端IPv6连接支持（低风险）
**目标**: 支持通过IPv6网络连接服务器
**时间**: 1-2天
**风险等级**: 🟢 低风险

**修改内容**:
1. 配置文件增加IPv6服务器地址选项
2. WebSocket客户端支持IPv6地址格式
3. 保持所有现有IPv4功能不变

**代码修改**:
```python
# config.env 新增
SERVER_IP_V6=2001:db8::1  # 服务器IPv6地址
PREFER_IPV6=false         # 优先使用IPv6

# wstunnel_combined.py 修改
server_ip_v6 = config.get('SERVER_IP_V6', '')
prefer_ipv6 = config.get('PREFER_IPV6', 'false').lower() == 'true'

if prefer_ipv6 and server_ip_v6:
    ws_url = f"ws://[{server_ip_v6}]:{server_port}"
else:
    ws_url = f"ws://{server_ip}:{server_port}"
```

#### 阶段二：代理服务双栈监听（中风险）
**目标**: 代理服务同时支持IPv4和IPv6
**时间**: 2-3天
**风险等级**: 🟡 中风险

**修改内容**:
1. SOCKS5/HTTP代理监听IPv6地址
2. 端口管理支持IPv6
3. 测试代理连接支持IPv6

**代码修改**:
```python
# wstunnel_combined.py 修改
# 原IPv4监听
"socks5://127.0.0.1:{socks5_port}",
"http://127.0.0.1:{http_port}"

# 新增IPv6监听
"socks5://[::1]:{socks5_port}",
"http://[::1]:{http_port}"
```

#### 阶段三：域名解析IPv6支持（中风险）
**目标**: 支持AAAA记录解析和IPv6地址验证
**时间**: 3-5天
**风险等级**: 🟡 中风险

**修改内容**:
1. 域名解析支持AAAA记录查询
2. IPv6地址格式验证
3. 地理位置验证支持IPv6
4. Hosts文件支持IPv6地址

#### 阶段四：完整双栈支持（高风险）
**目标**: 实现完整的IPv4/IPv6智能分流
**时间**: 5-7天
**风险等级**: 🔴 高风险

**修改内容**:
1. 智能选择IPv4/IPv6路径
2. 完整的错误处理和回退机制
3. 性能优化和测试

## 4. 备份与回滚方案

### 4.1 备份策略

#### 4.1.1 代码备份
```bash
# 创建完整备份
cd s:\YDS-Lab\03-dev\006-AUTOVPN\allout
mkdir backups\ipv6_upgrade_$(date +%Y%m%d_%H%M%S)
copy Scripts backups\ipv6_upgrade_$(date +%Y%m%d_%H%M%S)\Scripts /E /I
copy config backups\ipv6_upgrade_$(date +%Y%m%d_%H%M%S)\config /E /I
```

#### 4.1.2 配置备份
```python
# backup_configs.py
import shutil
import datetime
import os

def backup_configs():
    backup_dir = f"backups/config_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 备份配置文件
    configs_to_backup = [
        'Scripts/config.env',
        'config/wireguard/',
        'Scripts/recommended_domains.txt',
        'routes/常用境外IP.txt'
    ]
    
    os.makedirs(backup_dir, exist_ok=True)
    
    for config_path in configs_to_backup:
        if os.path.exists(config_path):
            if os.path.isdir(config_path):
                shutil.copytree(config_path, f"{backup_dir}/{os.path.basename(config_path)}")
            else:
                shutil.copy2(config_path, backup_dir)
            
    print(f"配置备份完成: {backup_dir}")
    return backup_dir
```

#### 4.1.3 服务状态备份
```python
# backup_service_status.py
import json
import psutil
import subprocess

def backup_service_status():
    """备份当前服务状态"""
    status = {
        'timestamp': datetime.datetime.now().isoformat(),
        'processes': {},
        'network_connections': [],
        'service_config': {}
    }
    
    # 备份进程状态
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'wstunnel' in proc.info['name'].lower():
            status['processes'][proc.info['pid']] = proc.info
    
    # 备份网络连接
    for conn in psutil.net_connections():
        if conn.laddr.port in [1081, 1082, 8081, 443]:
            status['network_connections'].append({
                'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                'status': conn.status,
                'pid': conn.pid
            })
    
    # 保存状态
    with open('service_status_backup.json', 'w') as f:
        json.dump(status, f, indent=2, default=str)
    
    return status
```

### 4.2 回滚方案

#### 4.2.1 快速回滚（紧急情况）
```bash
# 一键回滚脚本 rollback_ipv6_upgrade.bat
echo "正在执行IPv6升级回滚..."

# 停止所有相关服务
taskkill /F /IM wstunnel.exe 2>nul
taskkill /F /IM WireGuard.exe 2>nul

# 恢复备份代码
xcopy backups\ipv6_upgrade_latest\Scripts Scripts /E /Y /I
xcopy backups\ipv6_upgrade_latest\config config /E /Y /I

# 重启服务
python Scripts\wstunnel_combined.py

echo "回滚完成！"
```

#### 4.2.2 分阶段回滚
```python
# rollback_manager.py
class RollbackManager:
    def __init__(self):
        self.backup_points = []
        self.current_stage = 0
    
    def create_rollback_point(self, stage_name):
        """创建回滚点"""
        rollback_point = {
            'stage': stage_name,
            'timestamp': datetime.datetime.now(),
            'files': self.backup_stage_files(stage_name),
            'config': self.backup_stage_config(stage_name)
        }
        self.backup_points.append(rollback_point)
        return rollback_point
    
    def rollback_to_stage(self, stage_index):
        """回滚到指定阶段"""
        if stage_index >= len(self.backup_points):
            return False
        
        rollback_point = self.backup_points[stage_index]
        
        # 恢复文件
        for file_path, backup_path in rollback_point['files'].items():
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
        
        # 恢复配置
        self.restore_config(rollback_point['config'])
        
        # 重启服务
        self.restart_services()
        
        return True
```

## 5. 服务器压力分析

### 5.1 IPv6对服务器性能的影响

#### 5.1.1 网络层面影响
**内存占用**: ⬆️ 轻微增加 (~5-10%)
- IPv6地址空间更大，路由表项增加
- 连接跟踪表需要同时维护IPv4/IPv6条目

**CPU使用**: ⬆️ 轻微增加 (~3-8%)
- IPv6头部处理稍复杂
- 双栈需要额外的协议处理

**网络吞吐量**: ↔️ 基本无影响
- 实际数据传输性能取决于网络质量
- IPv6在某些情况下可能更优（更简洁的路由）

#### 5.1.2 应用层面影响
**连接数处理**: ⬆️ 增加约15-25%
```
单栈模式:  10000并发连接 → 10000文件描述符
双栈模式:  10000并发连接 → 15000-20000文件描述符
（每个连接可能需要IPv4+IPv6两个套接字）
```

**内存使用示例**:
```python
# IPv4连接内存占用估算
ipv4_connection_memory = 256 * num_connections  # 约256字节/连接

# IPv6连接内存占用估算  
ipv6_connection_memory = 320 * num_connections  # 约320字节/连接

# 双栈总内存占用
dual_stack_memory = (256 + 320) * num_connections * 0.8  # 80%的连接会同时建立
```

### 5.2 服务器配置建议

#### 5.2.1 现有服务器评估
**当前配置**: 192.210.206.52 (仅IPv4)
**推荐升级**: 添加IPv6地址支持

#### 5.2.2 硬件要求
```
最小配置（1000并发）:
- CPU: 1核 → 1核（无变化）
- 内存: 512MB → 768MB (+50%)
- 带宽: 100Mbps → 100Mbps（无变化）

推荐配置（5000并发）:
- CPU: 2核 → 2核（无变化）  
- 内存: 1GB → 1.5GB (+50%)
- 带宽: 1Gbps → 1Gbps（无变化）
```

#### 5.2.3 网络配置优化
```bash
# 服务器IPv6配置示例
# /etc/sysctl.conf
net.ipv6.conf.all.disable_ipv6 = 0
net.ipv6.conf.default.disable_ipv6 = 0
net.ipv6.conf.all.forwarding = 1
net.ipv6.conf.all.accept_ra = 2

# 连接数限制优化
net.core.somaxconn = 65535
net.ipv6.ip6table_max = 131072
```

## 6. 实施计划

### 6.1 时间规划
```
第1周: 阶段一 + 备份系统建立
第2周: 阶段二 + 测试验证  
第3周: 阶段三 + 性能调优
第4周: 阶段四 + 完整测试
```

### 6.2 测试验证
```python
# ipv6_upgrade_test.py
class IPv6UpgradeTester:
    def test_stage1(self):
        """测试阶段一: IPv6连接"""
        # 测试IPv6连接
        # 验证IPv4功能未受影响
        pass
    
    def test_stage2(self):
        """测试阶段二: 代理双栈"""
        # 测试IPv4/IPv6代理
        # 验证端口监听
        pass
    
    def test_performance(self):
        """性能测试"""
        # 内存使用测试
        # 连接数测试  
        # 吞吐量测试
        pass
```

### 6.3 风险缓解措施

#### 6.3.1 技术风险
- **兼容性问题**: 每个阶段后进行全面测试
- **性能下降**: 建立性能基线，实时监控
- **配置错误**: 自动化配置验证脚本

#### 6.3.2 业务风险  
- **服务中断**: 蓝绿部署，零停机升级
- **用户影响**: 提供降级选项，快速回滚
- **数据丢失**: 三重备份策略

## 7. 预期效果

### 7.1 技术收益
- ✅ 支持IPv6网络环境
- ✅ 提升网络兼容性
- ✅ 为未来网络发展做准备
- ✅ 减少IPv6环境下的IP泄露问题

### 7.2 性能预期
- **连接成功率**: +15%（IPv6网络环境）
- **网络延迟**: -10%（IPv6直连场景）
- **IP泄露率**: -90%（IPv6环境）

### 7.3 资源消耗
- **内存增加**: 约30-50%
- **CPU增加**: 约10-20%
- **带宽消耗**: 基本不变

## 8. 结论

IPv6升级方案**技术可行**，**风险可控**。通过分阶段实施和完善的备份回滚机制，可以确保现有服务稳定性。服务器压力在可接受范围内，建议按阶段逐步实施。

**推荐实施顺序**:
1. 🔧 立即实施：备份系统和阶段一（IPv6连接支持）
2. 📅 2周后实施：阶段二（代理双栈）
3. 📅 1个月后实施：阶段三和四（完整IPv6支持）

这个方案既保证了系统稳定性，又为未来IPv6普及做好了技术准备。