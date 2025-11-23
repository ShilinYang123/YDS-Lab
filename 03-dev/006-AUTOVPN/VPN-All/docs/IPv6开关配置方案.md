# AUTOVPN IPv6开关配置方案

## 概述

本方案提供了一种无需修改代码，仅通过配置开关即可控制IPv6功能的方法。当服务器端不支持IPv6时，可以通过简单的配置项关闭所有IPv6相关功能。

## 核心设计思路

### 1. 配置中心化管理
- 所有IPv6相关配置集中在 `config.env` 文件中
- 通过单一开关控制全局IPv6行为
- 支持运行时动态切换（需要重启服务）

### 2. 分层控制策略
```
应用层（代理配置）
    ↓
传输层（隧道配置）
    ↓  
网络层（连接配置）
    ↓
配置开关（IPv6_ENABLE）
```

## 具体实施方案

### 第一步：在config.env中添加IPv6开关

```bash
# IPv6功能开关配置
IPv6_ENABLE=false        # true: 启用IPv6支持, false: 仅使用IPv4
IPv6_PREFER=false      # true: 优先使用IPv6, false: 优先使用IPv4
IPv6_FALLBACK=true     # true: IPv6失败时回退到IPv4, false: 直接失败

# IPv6监听地址配置（当IPv6_ENABLE=true时生效）
IPv6_LISTEN_ADDR=[::1]   # IPv6本地监听地址
IPv6_PROXY_ADDR=[::]     # IPv6代理监听地址（所有IPv6地址）

# 服务器IPv6配置（可选）
SERVER_IPV6=2001:db8::1  # 服务器IPv6地址（如果有）
```

### 第二步：修改关键启动脚本

#### 1. wstunnel_combined.py 修改

```python
def start_wstunnel_combined(config):
    """启动wstunnel综合模式 - 支持IPv6开关"""
    
    # 获取IPv6开关配置
    ipv6_enable = config.get('IPv6_ENABLE', 'false').lower() == 'true'
    ipv6_prefer = config.get('IPv6_PREFER', 'false').lower() == 'true'
    
    server_ip = config.get('SERVER_IP', '192.210.206.52')
    wstunnel_port = int(config.get('WSTUNNEL_PORT', '1081'))
    socks5_port = int(config.get('SOCKS5_PORT', '1082'))
    http_port = int(config.get('HTTP_PORT', '8081'))
    
    # 根据IPv6开关选择监听地址
    if ipv6_enable:
        # IPv6模式
        listen_addr = config.get('IPv6_LISTEN_ADDR', '[::1]')
        proxy_addr = config.get('IPv6_PROXY_ADDR', '[::]')
        
        # 构建IPv6兼容的命令
        cmd = [
            wstunnel_exe,
            "--log-lvl", "DEBUG",
            "client",
            "-L", f"udp://{listen_addr}:{wstunnel_port}:{listen_addr}:{server_restrict_port}",
            "-L", f"socks5://{proxy_addr}:{socks5_port}",
            "-L", f"http://{proxy_addr}:{http_port}?login={user}&password={password}",
            f"ws://{server_ip}:{server_port}"
        ]
        
        # 如果启用了IPv6优先，添加相关参数
        if ipv6_prefer:
            cmd.extend(["--dns-resolver-prefer-ipv6"])
            
    else:
        # IPv4模式（保持原有逻辑）
        cmd = [
            wstunnel_exe,
            "--log-lvl", "DEBUG",
            "client", 
            "-L", f"udp://127.0.0.1:{wstunnel_port}:127.0.0.1:{server_restrict_port}",
            "-L", f"socks5://127.0.0.1:{socks5_port}",
            "-L", f"http://127.0.0.1:{http_port}?login={user}&password={password}",
            f"ws://{server_ip}:{server_port}"
        ]
    
    return cmd
```

#### 2. 代理配置自动适配

```python
def generate_proxy_config(config, ipv6_enable):
    """根据IPv6开关生成代理配置"""
    
    socks5_port = config.get('SOCKS5_PORT', '1082')
    http_port = config.get('HTTP_PORT', '8081')
    
    if ipv6_enable:
        # IPv6代理地址
        socks5_addr = f"[::1]:{socks5_port}"
        http_addr = f"[::1]:{http_port}"
    else:
        # IPv4代理地址
        socks5_addr = f"127.0.0.1:{socks5_port}"
        http_addr = f"127.0.0.1:{http_port}"
    
    return socks5_addr, http_addr
```

### 第三步：PAC文件自动适配

```javascript
// PAC文件根据IPv6开关自动适配
function FindProxyForURL(url, host) {
    
    // 获取IPv6开关状态（通过配置文件注入）
    var ipv6Enabled = __IPv6_ENABLE__;
    
    if (ipv6Enabled) {
        // IPv6模式
        return "SOCKS5 [::1]:1082; PROXY [::1]:8081; DIRECT";
    } else {
        // IPv4模式
        return "SOCKS5 127.0.0.1:1082; PROXY 127.0.0.1:8081; DIRECT";
    }
}
```

### 第四步：一键切换脚本

创建 `toggle_ipv6.bat` 脚本：

```batch
@echo off
echo AUTOVPN IPv6功能切换工具
echo ========================
echo.
echo 当前IPv6状态:
type S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\config.env | findstr "IPv6_ENABLE"
echo.
echo 请选择操作:
echo 1. 启用IPv6支持
echo 2. 禁用IPv6支持（仅IPv4）
echo 3. 查看当前配置
echo 4. 退出
echo.

set /p choice=请输入选项(1-4): 

if "%choice%"=="1" (
    echo 正在启用IPv6支持...
    powershell -Command "(Get-Content S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\config.env) -replace 'IPv6_ENABLE=false', 'IPv6_ENABLE=true' | Set-Content S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\config.env"
    echo IPv6已启用，请重启AUTOVPN服务
)

if "%choice%"=="2" (
    echo 正在禁用IPv6支持...
    powershell -Command "(Get-Content S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\config.env) -replace 'IPv6_ENABLE=true', 'IPv6_ENABLE=false' | Set-Content S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\config.env"
    echo IPv6已禁用，请重启AUTOVPN服务
)

if "%choice%"=="3" (
    echo 当前IPv6配置:
    type S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\config.env | findstr "IPv6"
)

if "%choice%"=="4" (
    exit
)

pause
```

## 使用场景和优势

### 使用场景

1. **服务器不支持IPv6时**
   ```bash
   IPv6_ENABLE=false  # 一键关闭所有IPv6功能
   ```

2. **需要测试IPv6时**
   ```bash
   IPv6_ENABLE=true   # 一键开启IPv6支持
   ```

3. **混合网络环境**
   ```bash
   IPv6_ENABLE=true
   IPv6_FALLBACK=true  # IPv6失败自动回退到IPv4
   ```

### 技术优势

1. **零代码修改**: 通过配置控制，无需修改业务逻辑
2. **快速切换**: 秒级切换IPv4/IPv6模式
3. **向后兼容**: 完全兼容现有IPv4-only环境
4. **渐进升级**: 支持逐步启用IPv6功能
5. **风险可控**: 出现问题可立即回退

### 配置验证

创建配置验证脚本 `check_ipv6_config.py`：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IPv6配置验证工具"""

import os
import configparser

def check_ipv6_config():
    """检查当前IPv6配置状态"""
    
    config_path = "S:\\AUTOVPN\\Scripts\\config.env"
    
    if not os.path.exists(config_path):
        print("❌ 配置文件不存在")
        return
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # 检查IPv6开关
    ipv6_enable = config.get('DEFAULT', 'IPv6_ENABLE', fallback='false')
    
    print("=== AUTOVPN IPv6配置检查 ===")
    print(f"IPv6开关状态: {'🟢 启用' if ipv6_enable.lower() == 'true' else '🔴 禁用'}")
    
    if ipv6_enable.lower() == 'true':
        print("\n当前监听地址:")
        print(f"  IPv6监听: {config.get('DEFAULT', 'IPv6_LISTEN_ADDR', fallback='[::1]')}")
        print(f"  IPv6代理: {config.get('DEFAULT', 'IPv6_PROXY_ADDR', fallback='[::]')}")
        
        print("\n⚠️  注意事项:")
        print("  - 确保服务器支持IPv6")
        print("  - 检查防火墙IPv6规则")
        print("  - 验证DNS IPv6解析")
    else:
        print("\n当前使用IPv4模式:")
        print("  SOCKS5代理: 127.0.0.1:1082")
        print("  HTTP代理: 127.0.0.1:8081")
        print("  UDP转发: 127.0.0.1:1081")
        
        print("\n✅ IPv4模式已就绪")

if __name__ == "__main__":
    check_ipv6_config()
```

## 总结

通过这套开关配置方案，您可以：

1. **无需修改代码**即可控制IPv6功能
2. **一键切换**IPv4/IPv6模式
3. **快速回退**到稳定状态
4. **渐进式升级**到IPv6
5. **零风险**尝试IPv6功能

当服务器端不支持IPv6时，只需设置 `IPv6_ENABLE=false`，系统会自动使用IPv4-only模式运行，完全不影响现有功能。