# IPv6 使用指南

## 概述

本指南详细介绍了 AUTOVPN 项目中 IPv6 支持的实现、配置和使用方法。IPv6 作为下一代互联网协议，提供了更大的地址空间、更好的安全性和更高的网络效率。

## 功能特性

### 1. 智能双栈支持
- **自动检测**: 自动检测系统 IPv6 支持情况
- **智能切换**: 根据连接质量智能选择 IPv4 或 IPv6
- **质量评估**: 基于响应时间和成功率评估连接质量
- **故障转移**: 自动故障检测和协议切换

### 2. AAAA 记录解析
- **多DNS服务器**: 支持多个 DNS 服务器的 AAAA 记录查询
- **质量验证**: 验证 DNS 服务器的 IPv6 解析能力
- **智能选择**: 选择最佳的 DNS 服务器
- **缓存优化**: 智能缓存机制提高解析效率

### 3. 连接质量检测
- **多维度测试**: 响应时间、成功率、稳定性
- **自适应重试**: 智能重试机制，支持多种策略
- **连接池管理**: 连接复用，提高测试效率
- **错误分析**: 详细的错误模式分析

## 配置说明

### 基本配置

在 `dual_stack_config.json` 文件中配置 IPv6 功能：

```json
{
  "smart_dual_stack": {
    "enabled": true,
    "auto_switch": true,
    "quality_threshold": {
      "response_time_ms": 500,
      "success_rate": 0.8,
      "stability_score": 0.9
    },
    "ipv6_priority": {
      "enabled": true,
      "bonus_score": 0.1
    }
  },
  "connection_test": {
    "timeout_seconds": 5,
    "retry_count": 3,
    "retry_strategy": "exponential_backoff",
    "max_concurrent": 20
  }
}
```

### 高级配置

#### IPv6 启用条件
```json
{
  "ipv6_enable_conditions": {
    "require_global_ipv6": true,
    "check_dns_aaaa": true,
    "min_success_rate": 0.6,
    "max_response_time_ms": 2000
  }
}
```

#### 质量评估权重
```json
{
  "quality_weights": {
    "success_rate": 0.5,
    "response_time": 0.3,
    "stability": 0.2
  }
}
```

#### 重试策略配置
```json
{
  "retry_config": {
    "strategy": "adaptive",
    "base_delay": 1.0,
    "max_delay": 30.0,
    "backoff_multiplier": 2.0,
    "jitter_enabled": true
  }
}
```

## 使用方法

### 1. 基本使用

#### 智能双栈测试
```bash
python smart_dual_stack.py --config dual_stack_config.json --test-domains domains.txt
```

#### 连接质量检测
```bash
python connection_test_optimized.py --hosts google.com youtube.com --ports 80 443 --detailed
```

#### IPv6 DNS 验证
```bash
python resolve_ip_remote.py --domain example.com --enable-ipv6 --validate-dns
```

### 2. 批量测试

#### 批量域名测试
```bash
# 从文件读取域名列表
python dual_stack_integration.py --input-domains domains.txt --output results.json --batch-size 50

# 指定测试参数
python dual_stack_integration.py --input-domains domains.txt --timeout 10 --retry-count 5 --concurrent 10
```

#### 结果分析
```bash
# 生成详细报告
python dual_stack_integration.py --analyze-results results.json --output-report report.html

# 质量统计
python dual_stack_integration.py --quality-stats --output-stats stats.json
```

### 3. 系统集成

#### 与 VPN 集成
```python
from dual_stack_integration import DualStackIntegration

# 创建集成实例
integration = DualStackIntegration(config_file='dual_stack_config.json')

# 分析域名
routing_config = integration.analyze_domain('example.com')

# 生成智能 hosts
hosts_content = integration.generate_smart_hosts(domains)

# 更新系统路由
integration.update_system_routing(routing_config)
```

#### 实时监控
```python
from smart_dual_stack import SmartDualStackRouter

# 创建路由器
router = SmartDualStackRouter(config_file='dual_stack_config.json')

# 持续监控
router.start_monitoring(interval=300)  # 每5分钟检查一次

# 获取实时状态
status = router.get_current_status()
print(f"IPv6可用性: {status.ipv6_availability}")
print(f"当前推荐协议: {status.recommended_protocol}")
```

## 故障排除

### 常见问题

#### 1. IPv6 不可用
**症状**: 所有 IPv6 测试失败
**可能原因**:
- 系统未启用 IPv6
- 网络不支持 IPv6
- DNS 服务器不支持 AAAA 记录

**解决方案**:
```bash
# 检查系统 IPv6 支持
python -c "import socket; print(socket.has_ipv6)"

# 检查网络接口
ip -6 addr show

# 测试 DNS 解析
nslookup -type=AAAA google.com
```

#### 2. 连接超时
**症状**: 连接测试频繁超时
**可能原因**:
- 网络延迟高
- 防火墙限制
- 目标服务器响应慢

**解决方案**:
```bash
# 增加超时时间
python connection_test_optimized.py --timeout 10 --retry-count 5

# 使用自适应重试策略
python connection_test_optimized.py --retry-strategy adaptive
```

#### 3. DNS 解析失败
**症状**: AAAA 记录解析失败
**可能原因**:
- DNS 服务器配置错误
- 域名没有 AAAA 记录
- 网络连接问题

**解决方案**:
```bash
# 验证 DNS 服务器
python resolve_ip_remote.py --validate-dns-servers --dns-servers 8.8.8.8 2001:4860:4860::8888

# 手动测试解析
python -c "
import dns.resolver
resolver = dns.resolver.Resolver()
resolver.nameservers = ['2001:4860:4860::8888']
result = resolver.resolve('google.com', 'AAAA')
print([str(r) for r in result])
"
```

### 高级故障排除

#### 连接池问题
```python
# 检查连接池状态
from connection_test_optimized import ConnectionPool

pool = ConnectionPool(max_size=10)
stats = pool.get_stats()
print(f"连接池统计: {stats}")
```

#### 质量评估调试
```python
# 详细质量评估
from smart_dual_stack import SmartDualStackRouter

router = SmartDualStackRouter()
quality = router.assess_connection_quality('example.com', 443)
print(f"连接质量: {quality}")
print(f"成功率: {quality.success_rate}")
print(f"平均响应时间: {quality.avg_response_time}ms")
print(f"稳定性评分: {quality.stability_score}")
```

#### 日志分析
```bash
# 查看详细日志
tail -f connection_test_optimized.log

# 分析错误模式
grep "ERROR\|WARNING" connection_test_optimized.log | sort | uniq -c

# 性能统计
grep "响应时间" connection_test_optimized.log | awk '{print $NF}' | sort -n
```

## 性能优化

### 1. 连接池优化
```python
# 调整连接池大小
config = ConnectionTestConfig(
    connection_pool_size=20,  # 增加连接池大小
    enable_keepalive=True,
    keepalive_interval=30.0
)
```

### 2. 并发控制
```python
# 优化并发设置
config = ConnectionTestConfig(
    max_concurrent_tests=50,  # 根据网络带宽调整
    retry_count=3,
    retry_strategy=RetryStrategy.ADAPTIVE
)
```

### 3. 缓存策略
```python
# 启用智能缓存
router = SmartDualStackRouter(
    cache_enabled=True,
    cache_ttl=3600,  # 1小时缓存
    cache_size=1000  # 最大缓存条目
)
```

### 4. 自适应参数
```python
# 自适应超时调整
config = ConnectionTestConfig(
    adaptive_timeout_min=1.0,
    adaptive_timeout_max=15.0,
    success_rate_threshold=0.7
)
```

## 最佳实践

### 1. 配置建议
- **生产环境**: 使用自适应重试策略，适当增加重试次数
- **测试环境**: 使用固定间隔重试，便于调试
- **高并发场景**: 增加连接池大小，优化并发数

### 2. 监控建议
- 定期检查 IPv6 可用性
- 监控连接质量变化趋势
- 记录失败模式便于分析

### 3. 维护建议
- 定期更新 DNS 服务器列表
- 清理过期缓存数据
- 分析日志优化参数

## API 参考

### SmartDualStackRouter
```python
class SmartDualStackRouter:
    def test_ipv6_availability(self) -> bool
    def assess_connection_quality(self, host: str, port: int) -> ConnectionQuality
    def make_routing_decision(self, host: str, port: int) -> DualStackDecision
    def batch_test_targets(self, targets: List[Tuple[str, int]]) -> List[TestResult]
```

### OptimizedConnectionTester
```python
class OptimizedConnectionTester:
    def test_connection_with_retry(self, host: str, port: int, ip_version: str) -> OptimizedConnectionResult
    def batch_test_with_optimization(self, targets: List[Tuple[str, int, str]]) -> List[OptimizedConnectionResult]
    def get_connection_pool_stats(self) -> Dict[str, Any]
```

### DualStackIntegration
```python
class DualStackIntegration:
    def analyze_domain(self, domain: str) -> DomainRoutingConfig
    def generate_smart_hosts(self, domains: List[str]) -> str
    def update_system_routing(self, routing_config: DomainRoutingConfig) -> bool
    def get_quality_statistics(self) -> Dict[str, Any]
```

## 更新日志

### v1.0.0 (2024-01)
- 初始版本发布
- 基础 IPv6 支持
- 智能双栈路由
- 连接质量检测

### v1.1.0 (2024-02)
- 优化连接池管理
- 增强重试机制
- 添加自适应参数
- 改进错误处理

### v1.2.0 (2024-03)
- 批量测试支持
- 详细报告生成
- 性能优化
- 文档完善

## 技术支持

如遇到问题，请按以下步骤排查：

1. **检查日志**: 查看相关日志文件获取详细错误信息
2. **验证配置**: 确保配置文件格式正确，参数合理
3. **网络测试**: 使用系统工具验证网络连接
4. **更新版本**: 确保使用最新版本的代码
5. **寻求帮助**: 在项目中提交 issue 获取支持

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。