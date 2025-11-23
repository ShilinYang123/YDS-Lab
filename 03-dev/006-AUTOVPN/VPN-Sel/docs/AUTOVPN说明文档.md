# AUTOVPN 说明文档

## 1. 系统概述

### 1.1 什么是AUTOVPN

AUTOVPN是一款基于WebSocket隧道技术的网络分流工具，专为需要同时访问国内外网络资源的用户设计。它通过智能路由规则实现国内外网络流量的精准分离，确保国内网站直连访问，国外网站通过隧道访问，从而提供流畅、稳定的上网体验。

### 1.2 核心特性

- **多模式支持**：提供WireGuard模式、代理模式和综合模式三种运行方式，满足不同场景需求
- **智能分流机制**：基于域名和IP地址的精准分流，只有国外网站流量通过隧道传输
- **安全连接**：采用WireGuard协议提供端到端加密，保障数据传输安全
- **易于使用**：简洁的菜单界面，一键式操作，无需复杂配置
- **自动化管理**：自动更新域名解析、Hosts文件和配置同步
- **高性能**：低延迟、高吞吐量的网络连接，适合各类网络应用

### 1.3 工作原理

AUTOVPN通过以下核心技术实现网络分流：

1. **WebSocket隧道**：使用wstunnel建立WebSocket隧道，绕过网络限制
2. **WireGuard VPN**：通过高性能的WireGuard协议提供安全的VPN连接
3. **Hosts文件管理**：自动更新Hosts文件，实现域名到IP的直接映射
4. **代理服务**：提供SOCKS5和HTTP代理，支持应用级分流
5. **域名解析**：通过远程服务器获取干净的DNS解析结果

## 2. 系统要求

### 2.1 硬件要求

- **处理器**：双核处理器或更高
- **内存**：至少2GB RAM
- **存储空间**：至少100MB可用空间
- **网络**：稳定的互联网连接

### 2.2 软件要求

- **操作系统**：Windows 10/11 64位
- **Python**：Python 3.8或更高版本
- **WireGuard**：最新版本的WireGuard客户端
- **其他依赖**：系统会自动安装所需的Python包

### 2.3 依赖组件

- **wstunnel**：WebSocket隧道客户端
- **Privoxy**：HTTP代理服务器（代理模式需要）
- **NSSM**：Windows服务管理工具
- **Paramiko**：Python SSH客户端库
- **dnspython**：DNS解析库

## 3. 安装配置

### 3.1 下载安装

1. 下载AUTOVPN安装包并解压到本地目录（推荐路径：`S:\YDS-Lab\03-dev\006-AUTOVPN\allout`）
2. 确保已安装WireGuard客户端
3. 运行`setup.bat`脚本安装必要的依赖

### 3.2 初始配置

1. 编辑`Scripts/config.env`文件，设置以下关键参数：
   - `SERVER_IP`：服务器IP地址
   - `SERVER_PORT`：服务器端口
   - `PREFIX`：WebSocket路径前缀
   - `USER`和`PASS`：代理认证信息（如需）

2. 将WireGuard配置文件放置在`config/wireguard/client/`目录下

3. 编辑`config.json`文件，配置SSH连接信息（用于远程域名解析）

4. **SSH连接信息（用于远程域名解析）**：
   - **服务器地址**：`192.210.206.52`
   - **用户名**：`root`
   - **密码**：`pH9t0Zy938ASy6wGZh`
   - **端口**：`22`
   
   这些信息已配置在`Scripts/resolve_ip_remote.py`脚本中，用于批量域名解析功能。

5. 编辑`routes/需要获取IP的域名列表.txt`，添加需要通过隧道访问的域名

## 4. 使用指南

### 4.1 启动系统

1. 运行`Scripts/autovpn_menu.py`脚本启动主菜单
2. 系统将显示16个功能选项

### 4.2 主要功能

#### 4.2.1 测试服务器连通性（选项1）

检查与服务器的连接状态，确认服务器是否可达。

#### 4.2.2 加载配置文件（选项2）

重新加载配置文件，应用最新设置。

#### 4.2.3 检查进程运行状态（选项4）

查看wstunnel和相关进程的运行状态。

#### 4.2.4 运行WireGuard模式（选项9）

启动WireGuard模式，适合需要全局VPN的场景：

1. 系统将启动wstunnel建立WebSocket隧道
2. 自动配置并启动WireGuard连接
3. 更新Hosts文件实现精准分流

#### 4.2.5 运行代理模式（选项10）

启动代理模式，适合需要应用级分流的场景：

1. 系统将启动wstunnel建立WebSocket隧道
2. 配置SOCKS5和HTTP代理服务
3. 生成PAC文件用于浏览器自动配置

#### 4.2.6 运行综合模式（选项11）

同时启动WireGuard和代理模式，提供最大灵活性。

#### 4.2.7 停止所有服务（选项12）

关闭所有运行的服务和进程。

#### 4.2.8 添加和管理域名（选项14）

管理需要通过隧道访问的域名列表：

1. 添加新域名到列表
2. 从远程服务器解析域名IP
3. 更新Hosts文件和WireGuard配置

#### 4.2.9 添加单个域名（选项16）

快速添加单个域名并立即解析其IP。

### 4.3 配置浏览器

#### 4.3.1 代理模式配置

**Firefox配置**：
1. 打开设置 → 网络设置
2. 选择"自动代理配置URL"
3. 输入`http://127.0.0.1:8081/autovpn.pac`

**Chrome配置**：
1. 安装SwitchyOmega扩展
2. 创建PAC情景模式
3. 设置PAC URL为`http://127.0.0.1:8081/autovpn.pac`

#### 4.3.2 WireGuard模式

WireGuard模式下无需配置浏览器，系统会自动通过VPN路由相应流量。

#### 4.3.3 多接口管理（新）

AUTOVPN支持配置多个WireGuard接口（如PC1、PC3等），适用于不同的网络环境：

**接口配置原则**：
- 所有接口必须使用相同的wstunnel端口（通常为1081）
- 每个接口应有独立的配置文件（PC1.conf、PC3.conf等）
- 定期检查接口状态，确保数据传输正常

**状态监控方法**：
```bash
# 查看所有接口状态
wg show

# 查看特定接口详细信息
wg show PC1
wg show PC3
```

**常见问题**：
- 如果接口显示已连接但数据不传输，检查端口配置一致性
- 如果接收数据停滞在很小值（如1.44 KiB），可能是端口不匹配问题
- 参考故障排除章节的端口不匹配解决方案

## 5. 常见问题解决

### 5.1 连接问题

#### 5.1.1 wstunnel服务启动问题

**症状**：wstunnel服务无法启动或启动后立即退出

**解决方法**：
1. 检查端口占用：
   ```
   netstat -ano | findstr 1081
   netstat -ano | findstr 8081
   ```
   如果端口已被占用，修改`config.env`中的端口配置或终止占用进程

2. 检查wstunnel版本：
   ```
   S:\YDS-Lab\03-dev\006-AUTOVPN\allout\Scripts\wstunnel.exe --version
   ```
   确认版本是否为10.1.11或更高

3. 检查wstunnel.exe是否存在且未被防病毒软件隔离

4. 查看日志文件了解具体错误信息

#### 5.1.2 WireGuard连接问题

**症状**：WireGuard无法连接或连接后无法访问网络

**解决方法**：
1. 确认wstunnel进程正在运行
2. 检查WireGuard配置中的Endpoint设置是否正确
3. 确认WireGuard网络适配器状态为"Up"
4. 测试与服务器的连接：`ping 10.9.0.1`
5. 检查AllowedIPs设置是否包含所有需要通过VPN访问的IP

#### 5.1.3 端口不匹配问题（新）

**症状**：WireGuard接口显示已连接但数据传输异常，接收数据量很小（如仅1.44 KiB）且不再增长，无法访问被墙网站

**根本原因**：WireGuard配置文件中的Endpoint端口与wstunnel实际监听的端口不一致

**诊断方法**：
1. 检查WireGuard接口状态：
   ```
   wg show PC1
   ```
   如果接收数据量很小且不增长，可能是端口不匹配

2. 确认wstunnel监听端口：
   ```
   netstat -ano | findstr wstunnel
   ```

3. 检查WireGuard配置端口：
   ```
   type S:\YDS-Lab\03-dev\006-AUTOVPN\allout\config\wireguard\client\PC1.conf | findstr Endpoint
   ```

**解决方法**：
1. 修正WireGuard配置文件中的Endpoint端口，确保与wstunnel监听端口一致（通常为1081）
2. 重新启动WireGuard服务：
   ```
   wireguard /uninstalltunnelservice PC1
   wireguard /installtunnelservice "S:\YDS-Lab\03-dev\006-AUTOVPN\allout\config\wireguard\client\PC1.conf"
   ```
3. 验证修复效果：
   ```
   wg show PC1
   ```
   确认数据传输正常，接收和发送数据量都在增长

#### 5.1.3 代理连接问题

**症状**：无法通过代理访问互联网或某些网站

**解决方法**：
1. 确认代理端口正在监听：
   ```
   netstat -ano | findstr 1080
   netstat -ano | findstr 8081
   ```
2. 测试代理连接：
   ```
   curl -v --socks5 127.0.0.1:1080 https://www.google.com
   curl -v --proxy http://127.0.0.1:8081 https://www.google.com
   ```
3. 检查代理认证信息是否正确
4. 确认PAC文件正确加载及内容正确
5. 检查浏览器代理设置

### 5.2 性能问题

#### 5.2.1 连接速度慢

**解决方法**：
1. 尝试调整MTU值（在`config.env`中修改`MTU_SIZE`）
2. 检查服务器负载和网络状况
3. 尝试使用不同的服务器或端口
4. **检查端口配置一致性**：确保WireGuard配置的Endpoint端口与wstunnel监听端口一致

#### 5.2.2 连接不稳定

**解决方法**：
1. 增加保活间隔（在`config.env`中修改`KEEPALIVE_INTERVAL`）
2. 检查本地网络稳定性
3. 尝试使用综合模式提高可靠性
4. **检查多接口配置**：如果使用多个WireGuard接口，确保所有接口使用相同的wstunnel端口

#### 5.2.3 数据传输异常

**症状**：WireGuard显示已连接但数据不传输，接收数据量很小（如1.44 KiB）且不再增长

**原因**：WireGuard配置的Endpoint端口与wstunnel实际监听端口不匹配

**解决方法**：
1. 检查wstunnel实际监听端口：
   ```
   netstat -ano | findstr wstunnel
   ```
2. 修正WireGuard配置文件中的Endpoint端口
3. 重新安装WireGuard服务：
   ```
   wireguard /uninstalltunnelservice PC1
   wireguard /installtunnelservice "S:\YDS-Lab\03-dev\006-AUTOVPN\allout\config\wireguard\client\PC1.conf"
   ```

### 5.3 其他问题

#### 5.3.1 域名解析失败

**解决方法**：
1. 检查SSH连接配置是否正确
2. 确认远程服务器能够访问干净的DNS服务器
3. 手动运行域名解析脚本查看详细错误信息

#### 5.3.2 Hosts文件更新失败

**解决方法**：
1. 以管理员权限运行程序
2. 检查Hosts文件是否被其他程序锁定
3. 手动编辑Hosts文件添加必要的条目

## 6. 高级配置

### 6.1 自定义PAC规则

可以编辑`Scripts/generate_pac.py`脚本，自定义PAC文件规则：

```python
# 添加自定义规则
PAC_TEMPLATE = '''
function FindProxyForURL(url, host) {
    // 自定义规则
    if (shExpMatch(host, "*.example.com")) {
        return "SOCKS5 127.0.0.1:1080; DIRECT";
    }
    
    // 默认规则
    if (isInDomainList(host)) {
        return "SOCKS5 127.0.0.1:1080; DIRECT";
    }
    return "DIRECT";
}
'''
```

### 6.2 配置多服务器负载均衡

可以修改`config.env`文件，配置多个服务器进行负载均衡：

```
SERVER_IP_1=192.168.1.1
SERVER_PORT_1=443
SERVER_IP_2=192.168.1.2
SERVER_PORT_2=443
LOAD_BALANCE=true
```

### 6.3 自定义路由规则

可以编辑WireGuard配置文件中的AllowedIPs参数，自定义路由规则：

```
[Interface]
PrivateKey = xxx
Address = 10.9.0.2/24
DNS = 8.8.8.8

[Peer]
PublicKey = xxx
AllowedIPs = 1.2.3.4/32, 5.6.7.8/32  # 自定义IP列表
Endpoint = 127.0.0.1:1081
PersistentKeepalive = 25
```

## 7. 维护与更新

### 7.1 日常维护

1. **定期更新域名解析**：
   - 每周运行一次域名解析脚本
   - 检查IP地址变化情况
   - 更新Hosts文件和WireGuard配置

2. **日志管理**：
   - 定期检查日志文件大小
   - 清理过期日志文件
   - 分析错误日志排查问题

### 7.2 系统更新

1. 定期检查AUTOVPN官方仓库获取最新版本
2. 备份当前配置文件
3. 下载并安装新版本
4. 恢复配置文件

## 8. 附录

### 8.1 命令行参数

主菜单脚本支持以下命令行参数：

```
python autovpn_menu.py --mode wireguard  # 直接启动WireGuard模式
python autovpn_menu.py --mode proxy      # 直接启动代理模式
python autovpn_menu.py --mode combined   # 直接启动综合模式
python autovpn_menu.py --stop            # 停止所有服务
python autovpn_menu.py --update-domains  # 更新域名解析
```

### 8.2 环境变量

可以通过设置以下环境变量覆盖配置文件中的设置：

- `AUTOVPN_SERVER_IP`：服务器IP地址
- `AUTOVPN_SERVER_PORT`：服务器端口
- `AUTOVPN_PREFIX`：WebSocket路径前缀
- `AUTOVPN_SOCKS5_PORT`：SOCKS5代理端口
- `AUTOVPN_HTTP_PORT`：HTTP代理端口

### 8.3 快捷键

主菜单中支持以下快捷键：

- `Ctrl+C`：退出程序
- `Ctrl+L`：清屏
- `F1`：显示帮助信息
- `F5`：刷新状态

### 8.4 文件结构

```
YDS-Lab/03-dev/006-AUTOVPN/allout/
├── config/                       # 配置目录
│   └── wireguard/                # WireGuard配置
│       └── client/               # 客户端配置
│           └── PC3.conf          # WireGuard配置文件
├── docs/                         # 文档目录
├── routes/                       # 路由规则目录
│   ├── 常用境外IP.txt            # 常用境外域名和IP映射列表
│   └── 需要获取IP的域名列表.txt   # 需要解析IP的域名列表
├── Scripts/                      # 脚本目录
│   ├── config.env                # 统一配置文件
│   ├── autovpn_menu.py           # 主菜单系统
│   └── ...                       # 其他脚本文件
└── logs/                         # 日志目录
```