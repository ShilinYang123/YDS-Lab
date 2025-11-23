# AUTOVPN系统详细工作流程

## 概述

AUTOVPN系统是一个集成了多种代理技术的综合VPN解决方案，支持WireGuard隧道、SOCKS5/HTTP代理以及智能域名分流功能。系统通过wstunnel建立WebSocket隧道，将各种网络流量封装后传输到远程服务器。

## 系统架构

### 核心组件

1. **wstunnel.exe** - WebSocket隧道程序，负责建立和维护隧道连接
2. **WireGuard客户端** - 处理UDP流量转发
3. **代理服务** - 提供SOCKS5和HTTP代理服务
4. **域名解析器** - 批量解析域名IP地址
5. **智能分流系统** - 根据域名决定流量走向

### 运行模式

系统支持三种运行模式：
- **代理模式**：仅提供SOCKS5/HTTP代理服务
- **WireGuard模式**：仅转发WireGuard UDP流量
- **综合模式**：同时支持代理和WireGuard

## 数据流转详细流程

### 1. DNS解析阶段

当用户在浏览器输入网址后，系统按以下顺序进行DNS解析：

#### 1.1 本地缓存检查
```
浏览器 → 本地DNS缓存 → 系统DNS缓存
```

#### 1.2 hosts文件读取
```
系统检查 C:\Windows\System32\drivers\etc\hosts 文件
```

#### 1.3 智能域名分流判断
系统根据域名类型决定解析策略：

**代理域名列表**（290个域名）：
- Google服务：google.com、youtube.com、gmail.com等
- 社交媒体：instagram.com、facebook.com、twitter.com等
- AI服务：openai.com、anthropic.com、huggingface.co等
- 电商平台：shopify.com、amazon.com等

**直连域名列表**：
- 国内网站：baidu.com、taobao.com、qq.com等
- 本地地址：localhost、127.0.0.1、192.168.x.x等

#### 1.4 DNS服务器选择
- **代理域名**：使用8.8.8.8、1.1.1.1等公共DNS
- **直连域名**：使用本地DNS服务器

### 2. 网络连接建立阶段

根据域名类型，系统选择不同的网络路径：

#### 2.1 代理域名连接路径
```
浏览器 → 系统网络栈 → wstunnel代理端口 → WebSocket隧道 → 远程服务器 → 目标网站
```

#### 2.2 直连域名连接路径
```
浏览器 → 系统网络栈 → 本地网络 → 目标网站
```

### 3. WireGuard隧道传输阶段

对于WireGuard流量：

```
应用程序 → WireGuard虚拟网卡 → wstunnel UDP转发 → WebSocket封装 → 远程服务器 → WireGuard服务端
```

## 具体命令行参数分析

### wstunnel代理模式命令
```bash
wstunnel.exe client -L "socks5://127.0.0.1:1080" -L "http://127.0.0.1:8080" --http-proxy-username user --http-proxy-password pass wss://server:443
```

参数说明：
- `-L "socks5://127.0.0.1:1080"`：本地SOCKS5代理监听
- `-L "http://127.0.0.1:8080"`：本地HTTP代理监听
- `--http-proxy-username/password`：代理认证信息
- `wss://server:443`：WebSocket安全连接

### wstunnel WireGuard模式命令
```bash
wstunnel.exe client --udp --udp-src 127.0.0.1:51820 --udp-dst 127.0.0.1:1081 wss://server:443
```

参数说明：
- `--udp`：启用UDP转发模式
- `--udp-src 127.0.0.1:51820`：本地WireGuard客户端端口
- `--udp-dst 127.0.0.1:1081`：远程WireGuard服务端端口
- `wss://server:443`：WebSocket安全连接

### wstunnel综合模式命令
```bash
wstunnel.exe client --udp --udp-src 127.0.0.1:51820 --udp-dst 127.0.0.1:1081 -L "socks5://127.0.0.1:1080" -L "http://127.0.0.1:8080" wss://server:443
```

## 完整流转路径示例

### 示例1：访问Google搜索

1. **DNS解析**：
   ```
   浏览器输入 google.com
   → 检查本地缓存（未命中）
   → 检查hosts文件（未配置）
   → 判断为代理域名
   → 向8.8.8.8查询google.com IP
   → 返回142.250.190.78
   ```

2. **连接建立**：
   ```
   浏览器向142.250.190.78:443发起HTTPS连接
   → 系统检测到代理配置
   → 连接转向127.0.0.1:1080（SOCKS5代理）
   → wstunnel接收代理请求
   → 通过WebSocket隧道发送到远程服务器
   → 远程服务器连接google.com:443
   ```

3. **数据传输**：
   ```
   浏览器HTTPS请求 → SOCKS5代理 → WebSocket封装 → 远程服务器 → Google服务器
   Google响应 → 远程服务器 → WebSocket解封装 → SOCKS5代理 → 浏览器
   ```

### 示例2：访问百度

1. **DNS解析**：
   ```
   浏览器输入 baidu.com
   → 检查本地缓存（未命中）
   → 检查hosts文件（未配置）
   → 判断为直连域名
   → 向本地DNS查询baidu.com IP
   → 返回180.101.49.12
   ```

2. **连接建立**：
   ```
   浏览器直接向180.101.49.12:443发起HTTPS连接
   → 系统检测到直连配置
   → 直接通过本地网络连接
   ```

## 智能分流机制

### PAC文件规则

系统生成三种PAC文件：

#### 全局代理模式
```javascript
function FindProxyForURL(url, host) {
    return "PROXY 127.0.0.1:8080; SOCKS5 127.0.0.1:1080; DIRECT";
}
```

#### 智能分流模式
```javascript
function FindProxyForURL(url, host) {
    // 直连本地地址
    if (isPlainHostName(host) || shExpMatch(host, "*.local")) {
        return "DIRECT";
    }
    
    // 直连国内域名
    var directDomains = ["*.baidu.com", "*.taobao.com", "*.qq.com"];
    for (var i = 0; i < directDomains.length; i++) {
        if (shExpMatch(host, directDomains[i])) {
            return "DIRECT";
        }
    }
    
    // 代理境外域名
    var proxyDomains = ["*.google.com", "*.youtube.com", "*.facebook.com"];
    for (var i = 0; i < proxyDomains.length; i++) {
        if (shExpMatch(host, proxyDomains[i])) {
            return "PROXY 127.0.0.1:8080; SOCKS5 127.0.0.1:1080";
        }
    }
    
    return "DIRECT";
}
```

#### 全部直连模式
```javascript
function FindProxyForURL(url, host) {
    return "DIRECT";
}
```

### 分流判断逻辑

系统根据以下优先级进行分流判断：

1. **本地地址**：localhost、127.0.0.1、192.168.x.x等
2. **国内域名**：baidu.com、taobao.com、qq.com等
3. **代理域名**：google.com、youtube.com、facebook.com等
4. **默认规则**：未匹配的域名按模式设置处理

## 性能优化机制

### 并发DNS解析
系统使用线程池并发解析290个域名，提高解析效率：
```python
with ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(resolve_domain, domain) for domain in domains]
```

### IP评分机制
系统对解析到的IP进行评分，选择最优IP：
- 连接成功率
- 响应时间
- 地理位置
- 历史稳定性

### 缓存机制
- **DNS缓存**：减少重复解析
- **连接池**：复用已有连接
- **PAC缓存**：避免重复生成

## 故障处理

### 连接失败处理
1. **重试机制**：自动重试3次
2. **备用IP**：使用其他解析到的IP
3. **模式切换**：切换到其他可用模式

### 端口冲突处理
1. **自动检测**：检查端口占用情况
2. **动态分配**：使用备用端口
3. **进程管理**：终止冲突进程

### 网络异常处理
1. **超时设置**：合理设置超时时间
2. **错误日志**：详细记录异常信息
3. **自动恢复**：尝试重新建立连接

## 安全配置

### 认证机制
- **代理认证**：SOCKS5/HTTP代理支持用户名密码认证
- **密钥认证**：WireGuard使用预共享密钥
- **证书验证**：WebSocket连接使用TLS证书

### 加密传输
- **TLS加密**：WebSocket使用wss协议
- **WireGuard加密**：ChaCha20加密算法
- **端到端加密**：保证数据传输安全

## 监控与日志

### 实时监控
- **连接状态**：监控隧道连接状态
- **流量统计**：记录上传下载流量
- **性能指标**：监控延迟、丢包率

### 日志记录
- **访问日志**：记录访问的域名和时间
- **错误日志**：记录连接错误和异常
- **调试日志**：详细记录系统运行状态

## 总结

AUTOVPN系统通过智能分流、多重代理模式和完善的故障处理机制，为用户提供了稳定、高效、安全的网络访问解决方案。系统能够根据目标域名自动选择最优的网络路径，既保证了访问速度，又确保了连接的稳定性。