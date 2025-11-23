# AUTOVPN 技术文档

## 1. 系统架构概述

### 1.1 整体架构

AUTOVPN是一个基于WebSocket隧道技术的网络分流工具，旨在通过智能路由规则实现国内外网络流量的精准分离。系统采用模块化设计，支持多种运行模式和智能分流。

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTOVPN 系统架构                          │
├─────────────────────────────────────────────────────────────┤
│  用户界面层                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 主菜单界面   │  │ 配置编辑器   │  │ 系统报告器   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  业务逻辑层                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 域名管理器   │  │ IP解析器    │  │ 代理控制器   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Hosts管理器  │  │ 服务管理器   │  │ 配置同步器   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  网络传输层                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ WireGuard   │  │ wstunnel    │  │ Privoxy     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 分层结构

1. **用户界面层**：提供统一的用户交互界面，包括主菜单系统、配置编辑器和状态监控器
2. **业务逻辑层**：实现核心业务功能，包括域名管理、IP解析、代理控制、Hosts管理、服务管理和配置同步
3. **网络传输层**：负责网络数据传输，包括WireGuard VPN、wstunnel WebSocket隧道和代理服务
4. **系统基础层**：提供基础支持，包括文件系统操作、网络接口管理和进程控制

## 2. 核心组件

### 2.1 主控制器 (autovpn_menu.py)

- **功能**: 系统主入口，提供统一的用户界面
- **职责**: 菜单管理、功能调度、状态监控
- **接口**: 16个主要功能选项

#### 2.1.1 核心功能
```python
class AutoVPNMenu:
    def __init__(self):
        self.config = self.load_config()
        self.logger = self.setup_logging()
    
    def main_menu(self):
        """主菜单循环"""
        while True:
            self.display_menu()
            choice = input("请选择功能: ")
            self.handle_choice(choice)
```

#### 2.1.2 功能映射
| 选项 | 功能 | 对应模块 |
|------|------|----------|
| 1 | 测试服务器连通性 | test_server_connectivity() |
| 2 | 加载配置文件 | load_config_file() |
| 3 | 清屏 | clear_screen() |
| 4 | 检查进程运行状态 | check_process_status() |
| 5 | 终止所有进程 | terminate_all_processes() |
| 6 | 检查服务状态 | check_service_status() |
| 7 | 检查网络状态 | check_network_status() |
| 8 | 测试代理连接 | test_proxy_connection() |
| 9 | 运行WireGuard模式 | run_wireguard_mode() |
| 10 | 运行代理模式 | run_proxy_mode() |
| 11 | 运行综合模式 | run_combined_mode() |
| 12 | 停止所有服务 | stop_all_services() |
| 13 | 编辑配置文件 | edit_config_files() |
| 14 | 添加和管理域名 | manage_domains() |
| 15 | 配置同步 | sync_configurations() |
| 16 | 添加单个域名 | add_single_domain() |

### 2.2 域名管理模块

#### 2.2.1 域名列表管理器
- **add_single_domain.py**: 单域名快速添加
- **resolve_domain_list.py**: 批量域名解析
- **resolve_ip_remote.py**: 远程IP解析

#### 2.2.2 域名解析与IP获取机制

AUTOVPN 通过 SSH 连接远程服务器获取"干净"的 IP 地址，以避免本地 DNS 污染问题。具体实现如下：

1. **域名列表管理**：
   - 域名列表存储在 `需要获取IP的域名列表.txt` 文件中
   - 支持通配符域名格式（如 `*.example.com`）
   - 系统会自动去重和排序

2. **远程解析流程**：
   - 通过 SSH 连接到境外服务器
   - 在服务器上创建 Python 虚拟环境
   - 安装 dnspython 和 requests 依赖包
   - 执行域名解析脚本获取干净 IP
   - 将结果保存到 `常用境外IP.txt`

3. **IP 地址处理**：
   - 对获取的 IP 地址进行验证，确保格式正确
   - 自动添加 `/32` 后缀用于 WireGuard 配置
   - 支持 IPv4 和 IPv6 地址

### 2.3 Hosts文件管理模块

- **update_hosts.py**: Hosts文件更新
- **clear_hosts.py**: Hosts文件清理

#### 2.3.1 Hosts 文件管理机制

Hosts 文件管理是 AUTOVPN 实现精准分流的核心技术之一：

1. **自动更新**：
   - 读取 `常用境外IP.txt` 文件获取域名-IP 映射
   - 自动生成 www 和非 www 版本的映射条目
   - 在 Hosts 文件中创建专用管理区域（以 `# AUTOVPN自动写入` 为标识）

2. **备份与恢复**：
   - 每次更新前自动备份原 Hosts 文件
   - 备份文件名包含时间戳，便于追溯
   - 出现问题时可手动恢复备份

3. **去重与排序**：
   - 自动去除重复条目
   - 按 IP 地址和域名进行排序，便于查看和管理

### 2.4 网络隧道模块

- **wstunnel_wireguard.py**: WireGuard模式隧道
- **wstunnel_proxy.py**: 代理模式隧道
- **wstunnel_combined.py**: 综合模式隧道

#### 2.4.1 WireGuard 配置同步机制

AUTOVPN 通过配置同步脚本确保 WireGuard 配置与最新的域名 IP 保持一致：

1. **AllowedIPs 更新**：
   - 读取 `常用境外IP.txt` 获取最新的 IP 列表
   - 自动更新 WireGuard 配置文件中的 AllowedIPs 参数
   - 添加必要的内网 IP 地址以支持内网通信

2. **Endpoint 配置**：
   - 自动更新 Endpoint 为本地 wstunnel 服务地址
   - 支持动态端口分配和冲突解决

3. **其他参数优化**：
   - MTU 参数优化网络性能
   - DNS 参数配置隧道内 DNS 服务器
   - PersistentKeepalive 参数维持连接稳定性

#### 2.4.2 代理模式与 PAC 脚本

代理模式提供灵活的应用层分流方案：

1. **SOCKS5/HTTP 代理**：
   - 提供 SOCKS5 和 HTTP 两种代理协议
   - 支持用户名密码认证
   - 自动处理端口冲突和进程管理

2. **PAC 脚本生成**：
   - 自动生成多种分流策略的 PAC 文件
   - 支持国内直连、全部走代理、智能分流等模式
   - 可自定义规则满足特殊需求

3. **浏览器集成**：
   - 提供详细的浏览器配置指南
   - 推荐使用 SwitchyOmega 扩展实现更灵活的代理控制

### 2.5 服务管理模块

- **nssm_manage_wstunnel.py**: Windows服务管理
- **stop_all_services.py**: 服务停止控制

## 3. 工作流程

### 3.1 初始化配置

1. **编辑 `config.env` 文件设置基本参数**
   - 服务器IP和端口
   - 本地监听端口
   - 代理认证信息
   - MTU和保活间隔

2. **配置 `config.json` 中的 SSH 连接信息**
   - 服务器地址
   - 用户名和密码/密钥
   - 连接超时设置

3. **导入 WireGuard 客户端配置文件**
   - 放置到 `config/wireguard/client/` 目录
   - 确保包含正确的私钥和公钥

### 3.2 域名解析流程

1. **系统读取 `需要获取IP的域名列表.txt` 获取需要解析的域名**
   - 支持手动添加和批量导入
   - 自动处理格式和去重

2. **通过 SSH 连接远程服务器解析域名获取干净 IP**
   - 使用 dnspython 库进行 DNS 查询
   - 支持多种 DNS 服务器配置
   - 错误处理和重试机制

3. **将结果保存到 `常用境外IP.txt`**
   - 格式化为 `域名 IP` 对
   - 添加时间戳和版本信息
   - 备份历史版本

### 3.3 Hosts 文件更新流程

1. **读取 IP 列表文件**
   - 解析 `常用境外IP.txt` 中的域名-IP映射
   - 验证格式和有效性

2. **更新本地 Hosts 文件，添加 DNS 防污染规则**
   - 在专用区域添加或更新条目
   - 保留文件其他部分不变
   - 自动生成 www 和非 www 版本

3. **自动备份原 Hosts 文件**
   - 创建带时间戳的备份
   - 提供恢复选项

### 3.4 服务启动流程

#### 3.4.1 WireGuard 模式

1. **启动 wstunnel 客户端**
   ```
   wstunnel.exe client --http-upgrade-path-prefix=PREFIX -L udp://127.0.0.1:1081:127.0.0.1:8443 ws://SERVER_IP:SERVER_PORT
   ```

2. **配置 WireGuard 连接**
   - 更新 Endpoint 为 `127.0.0.1:1081`
   - 同步 AllowedIPs 列表
   - 启动 WireGuard 接口

#### 3.4.2 代理模式

1. **启动 wstunnel 客户端**
   ```
   wstunnel.exe client --http-upgrade-path-prefix=PREFIX -L socks://127.0.0.1:1080 ws://SERVER_IP:SERVER_PORT
   ```

2. **启动 HTTP 代理转发**
   - 配置 Privoxy 转发 SOCKS5 到 HTTP
   - 生成 PAC 文件
   - 提供浏览器配置指南

#### 3.4.3 综合模式

1. **同时启动 WireGuard 和代理服务**
   - 配置不同端口避免冲突
   - 共享域名解析结果
   - 统一管理服务进程

## 4. 性能优化

### 4.1 网络性能优化

1. **MTU 优化**
   - 默认设置为 1420 字节
   - 提供自动 MTU 测试脚本
   - 根据网络环境动态调整

2. **连接保活**
   - 使用 PersistentKeepalive 参数（默认 25 秒）
   - 防止 NAT 超时断连
   - 自动重连机制

3. **多路复用**
   - wstunnel 支持多连接复用
   - 提高并发性能
   - 负载均衡策略

### 4.2 系统性能优化

1. **进程管理优化**
   - 避免重复启动相同服务
   - 及时终止无用进程
   - 使用进程池管理并发任务

2. **文件操作优化**
   - 使用文件锁机制防止并发冲突
   - 缓存频繁访问的文件内容
   - 定期清理临时文件

3. **域名解析优化**
   - 缓存解析结果减少重复查询
   - 设置合理的缓存过期时间
   - 使用 LRU 算法管理缓存

## 5. 安全机制

### 5.1 数据传输安全

1. **wstunnel 协议限制**：
   - 由于使用租用 VPN 服务器，无法获得域名和 SSL 证书
   - wstunnel 只能使用 `ws://`（WebSocket）协议，而非 `wss://`（WebSocket Secure）
   - 但整体安全性依然很高，因为 WireGuard 协议本身具有强加密

2. **数据保护机制**：
   - 第一层：wstunnel 的 WebSocket 伪装（绕过 ISP 检测）
   - 第二层：WireGuard 的 ChaCha20-Poly1305 加密（端到端安全）

3. **认证机制**：
   - WebSocket 路径前缀认证
   - WireGuard 密钥对认证
   - 代理用户名密码认证（可选）

### 5.2 配置安全

1. **敏感信息保护**：
   - 密码和密钥存储加密
   - 日志中敏感信息脱敏
   - 配置文件权限控制

2. **备份与恢复**：
   - 自动备份关键配置
   - 版本控制和历史追踪
   - 灾难恢复机制

## 6. 故障排除

### 6.1 wstunnel服务启动问题

**症状**：wstunnel服务无法启动或启动后立即退出

**排查步骤**：

1. **检查端口占用**
   ```
   netstat -ano | findstr 1081
   netstat -ano | findstr 8081
   ```
   如果端口已被占用，可以在`config.env`中修改端口配置，或终止占用端口的进程。

2. **检查wstunnel版本**
   ```
   S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\wstunnel.exe --version
   ```
   确认版本是否为10.1.11或更高版本。

3. **检查wstunnel.exe是否存在**
   确认`S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\wstunnel.exe`文件存在且未被防病毒软件隔离。

4. **检查日志**
   查看`S:\YDS-Lab\03-dev\006-AUTOVPN\allout\logs`目录下的相关日志文件，了解具体错误信息。

5. **手动运行wstunnel**
   ```
   cd /d S:\AUTOVPN\Scripts
   wstunnel.exe client --http-upgrade-path-prefix=xYz123AbC -L udp://127.0.0.1:1081:127.0.0.1:8443 ws://192.210.206.52:443
   ```
   查看命令行输出的错误信息。

### 6.2 WireGuard连接问题

**症状**：WireGuard无法连接或连接后无法访问网络

**排查步骤**：

1. **检查wstunnel是否运行**
   ```
   tasklist | findstr wstunnel
   ```
   确认wstunnel进程正在运行。

2. **检查WireGuard配置**
   确认`S:\YDS-Lab\03-dev\006-AUTOVPN\allout\config\wireguard\client\PC1.conf`中的`Endpoint`设置为`127.0.0.1:1080`或与wstunnel实际监听的端口一致。

3. **检查WireGuard网络适配器**
   ```
   powershell -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*WireGuard*'}"
   ```
   确认WireGuard网络适配器存在且状态为"Up"。

4. **测试与服务器的连接**
   ```
   ping 10.9.0.1
   ```
   如果ping不通，可能是wstunnel UDP转发不正常或服务器端WireGuard配置问题。

5. **检查路由表**
   ```
   route print
   ```
   确认WireGuard配置的路由规则正确添加。

6. **检查AllowedIPs设置**
   确认`PC3.conf`中的`AllowedIPs`配置包含所有需要通过VPN访问的IP地址。

### 6.3 端口不匹配问题（新）

**症状**：WireGuard接口显示已连接但数据传输异常，接收数据量很小（如仅1.44 KiB）且不再增长，无法访问特定网站

**根本原因**：WireGuard配置文件中的Endpoint端口与wstunnel实际监听的端口不一致

**排查步骤**：

1. **检查WireGuard接口状态**
   ```
   wg show PC1
   ```
   观察传输数据量，如果接收数据很小且不增长，可能是端口不匹配问题

2. **确认wstunnel监听端口**
   ```
   netstat -ano | findstr wstunnel
   ```
   查看wstunnel实际监听的端口号

3. **检查WireGuard配置端口**
   ```
   type S:\YDS-Lab\03-dev\006-AUTOVPN\allout\config\wireguard\client\PC1.conf | findstr Endpoint
   ```
   对比是否与wstunnel监听端口一致

**解决方案**：

1. **修正WireGuard配置端口**
   编辑`PC1.conf`文件，将Endpoint端口修改为与wstunnel监听端口一致（通常为1081）

2. **重新启动WireGuard服务**
   ```
   wireguard /uninstalltunnelservice PC1
   wireguard /installtunnelservice "S:\YDS-Lab\03-dev\006-AUTOVPN\allout\config\wireguard\client\PC1.conf"
   ```

3. **验证修复效果**
   ```
   wg show PC1
   ```
   确认数据传输正常，接收和发送数据量都在增长

### 6.3 代理连接问题

**症状**：无法通过代理访问互联网或某些网站

**排查步骤**：

1. **检查代理端口**
   ```
   netstat -ano | findstr 1080
   netstat -ano | findstr 8081
   ```
   确认SOCKS5和HTTP代理端口正在监听。

2. **测试代理连接**
   ```
   curl -v --socks5 127.0.0.1:1080 --connect-timeout 10 https://www.google.com
   curl -v --proxy http://127.0.0.1:8081 --connect-timeout 10 https://www.google.com
   ```
   查看是否能成功连接。

3. **检查代理认证**
   确认使用代理时提供了正确的用户名和密码（如果启用了认证）。

4. **检查PAC文件**
   如果使用PAC自动配置，检查PAC文件是否正确加载及其内容是否正确。

5. **检查浏览器设置**
   确认浏览器的代理设置正确，包括代理类型、地址和端口。

## 7. 维护与监控

### 7.1 日常维护任务

1. **定期更新域名解析**：
   - 建议每周运行一次域名解析脚本
   - 检查 IP 地址变化情况
   - 更新 Hosts 文件和 WireGuard 配置

2. **日志管理**：
   - 定期检查日志文件大小
   - 清理过期日志文件
   - 分析错误日志排查问题

3. **配置文件检查**：
   - 验证配置文件完整性
   - 检查敏感信息保护
   - 备份重要配置文件

### 7.2 监控与告警

1. **服务状态监控**：
   - 监控 wstunnel 进程运行状态
   - 检查端口占用情况
   - 验证网络连接状态

2. **性能监控**：
   - 监控系统资源使用情况
   - 检查网络延迟和带宽
   - 分析连接稳定性

3. **错误监控**：
   - 实时监控错误日志
   - 设置关键错误告警
   - 自动故障恢复机制

## 8. 附录

### 8.1 文件结构说明

```
YDS-Lab/03-dev/006-AUTOVPN/allout/
├── config/
│   └── wireguard/
│       └── client/
│           └── PC3.conf          # WireGuard 客户端配置
├── docs/                         # 文档目录
├── routes/                       # 路由规则目录
│   ├── 常用境外IP.txt            # 常用境外域名和 IP 映射列表
│   └── 需要获取IP的域名列表.txt   # 需要解析 IP 的域名列表
├── Scripts/                      # 脚本目录
│   ├── config.env                # 统一配置文件
│   ├── autovpn_menu.py           # 主菜单系统
│   ├── resolve_ip_remote.py      # 远程域名解析脚本
│   ├── update_hosts.py           # Hosts 文件更新脚本
│   ├── wstunnel_wireguard.py     # WireGuard 模式启动脚本
│   ├── wstunnel_proxy.py         # 代理模式启动脚本
│   ├── wstunnel_combined.py      # 综合模式启动脚本
│   ├── sync_config.py            # 配置同步脚本
│   ├── add_single_domain.py      # 单域名快速添加脚本
│   ├── stop_all_services.py      # 停止所有服务脚本
│   ├── show_help.py              # 帮助信息脚本
│   └── wstunnel.exe              # wstunnel 客户端程序
├── config.json                   # SSH 连接配置
└── logs/                         # 日志目录
```

### 8.2 配置参数说明

在 `Scripts/config.env` 文件中可以配置以下参数：

- `PREFIX`：WebSocket 路径前缀，用于认证
- `SERVER_IP`：服务器 IP 地址
- `SERVER_PORT`：服务器端口
- `SERVER_RESTRICT_PORT`：服务器限制转发端口
- `WSTUNNEL_PORT`：WebSocket 隧道端口
- `MTU_SIZE`：网络 MTU 大小
- `KEEPALIVE_INTERVAL`：连接保活间隔
- `PRIMARY_DNS`：主 DNS 服务器
- `SECONDARY_DNS`：备用 DNS 服务器
- `USER`：代理用户名
- `PASS`：代理密码
- `SERVER_USER`：服务器 SSH 用户名
- `SERVER_PASSWORD`：服务器 SSH 密码
- `SOCKS5_PORT`：SOCKS5 代理端口
- `HTTP_PORT`：HTTP 代理端口
- `WG_INTERFACE`：WireGuard 接口名称
- `WG_LOCAL_IP`：本机在 WireGuard 网络中的 IP
- `WG_CONF_PATH`：WireGuard 配置文件路径

### 8.3 远程服务器要求

远程服务器需要满足以下条件：

1. 安装 Python 3.8+
2. 安装 python3-venv 包
3. 能够访问干净的 DNS 服务器
4. 开放必要的网络端口

### 8.4 多接口配置最佳实践

AUTOVPN支持配置多个WireGuard接口（如PC1、PC3等），但在实际使用中需要注意以下最佳实践：

#### 8.4.1 端口配置一致性
**关键原则**：所有WireGuard接口的Endpoint端口必须与wstunnel实际监听端口保持一致

- 标准配置：wstunnel监听1081端口，所有WireGuard接口Endpoint设置为`127.0.0.1:1081`
- 避免混用：不要为不同接口设置不同的Endpoint端口
- 验证方法：
  ```
  netstat -ano | findstr wstunnel  # 查看wstunnel实际监听端口
  wg show                          # 查看所有接口状态
  ```

#### 8.4.2 接口状态监控
**监控指标**：
- 数据传输量：接收和发送数据应持续增长
- 最新握手时间：应显示最近的时间（如"8秒前"）
- 接口状态：应为"running"

**异常识别**：
- 接收数据停滞在很小值（如1.44 KiB）
- 长时间无握手更新
- 无法访问特定网站

#### 8.4.3 故障恢复流程
当发现接口异常时：

1. **检查端口匹配性**
   ```
   wg show PC1                      # 检查问题接口
   netstat -ano | findstr wstunnel  # 确认wstunnel端口
   ```

2. **修正配置并重启**
   ```
   # 卸载问题接口
   wireguard /uninstalltunnelservice PC1
   
   # 修正配置文件端口
   # 重新安装接口
   wireguard /installtunnelservice "S:\YDS-Lab\03-dev\006-AUTOVPN\allout\config\wireguard\client\PC1.conf"
   ```

3. **验证恢复效果**
   ```
   wg show PC1  # 确认数据传输正常
   ```

#### 8.4.4 配置管理建议
- **统一端口管理**：所有接口使用相同的wstunnel端口
- **定期状态检查**：建立监控脚本定期检查接口状态
- **配置版本控制**：保存配置文件修改历史
- **快速回滚机制**：准备已知良好的配置备份