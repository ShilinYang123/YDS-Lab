#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能双栈分流系统 - Smart Dual-Stack Routing System
根据连接质量智能选择IPv4或IPv6路径
"""

import socket
import time
import json
import logging
import concurrent.futures
import subprocess
import os
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# 配置常量
CONNECTION_TIMEOUT = 5  # 连接超时时间（秒）
TEST_PORT_HTTP = 80
TEST_PORT_HTTPS = 443
MAX_CONCURRENT_TESTS = 10  # 最大并发测试数
QUALITY_THRESHOLD_MS = 500  # 质量阈值（毫秒）
RETRY_COUNT = 2  # 重试次数

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_dual_stack.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IPVersion(Enum):
    """IP版本枚举"""
    IPV4 = "IPv4"
    IPV6 = "IPv6"
    DUAL_STACK = "Dual Stack"

@dataclass
class ConnectionTestResult:
    """连接测试结果数据类"""
    ip_version: IPVersion
    host: str
    ip_address: str
    port: int
    success: bool
    response_time_ms: float
    error_message: Optional[str] = None
    is_preferred: bool = False

@dataclass
class DualStackDecision:
    """双栈决策结果"""
    recommended_version: IPVersion
    ipv4_quality: Optional[float] = None
    ipv6_quality: Optional[float] = None
    decision_reason: str = ""
    test_results: List[ConnectionTestResult] = None
    
    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []

class SmartDualStackRouter:
    """智能双栈路由器"""
    
    def __init__(self):
        self.test_results: List[ConnectionTestResult] = []
        self.ipv6_enabled = self._check_ipv6_availability()
        
    def _check_ipv6_availability(self) -> bool:
        """检查系统IPv6可用性"""
        try:
            # 检查系统是否有IPv6地址
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=10)
            has_ipv6 = 'IPv6' in result.stdout and '2001:' in result.stdout
            
            if has_ipv6:
                logger.info("系统支持IPv6，检测到IPv6地址")
            else:
                logger.info("系统未检测到IPv6地址")
            
            return has_ipv6
            
        except Exception as e:
            logger.warning(f"检查IPv6可用性失败: {e}")
            return False
    
    def _test_single_connection(self, host: str, port: int, ip_version: IPVersion, 
                               timeout: int = CONNECTION_TIMEOUT) -> ConnectionTestResult:
        """测试单个连接"""
        start_time = time.time()
        
        try:
            # 根据IP版本选择地址族
            if ip_version == IPVersion.IPV4:
                family = socket.AF_INET
                # 获取IPv4地址
                addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
            elif ip_version == IPVersion.IPV6:
                family = socket.AF_INET6
                addr_info = socket.getaddrinfo(host, port, socket.AF_INET6, socket.SOCK_STREAM)
            else:
                # 双栈模式，让系统自动选择
                addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            
            if not addr_info:
                return ConnectionTestResult(
                    ip_version=ip_version,
                    host=host,
                    ip_address="",
                    port=port,
                    success=False,
                    response_time_ms=0,
                    error_message="无法解析地址"
                )
            
            # 使用第一个可用的地址
            family, socktype, proto, canonname, sockaddr = addr_info[0]
            
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect(sockaddr)
                
                response_time = (time.time() - start_time) * 1000  # 转换为毫秒
                
                # 获取实际连接的IP地址
                if ip_version == IPVersion.IPV4:
                    ip_address = sockaddr[0]
                elif ip_version == IPVersion.IPV6:
                    ip_address = sockaddr[0]
                else:
                    # 双栈模式，根据实际使用的地址族判断
                    if family == socket.AF_INET:
                        ip_address = sockaddr[0]
                        actual_version = IPVersion.IPV4
                    else:
                        ip_address = sockaddr[0]
                        actual_version = IPVersion.IPV6
                    ip_version = actual_version
                
                logger.info(f"连接成功: {host}:{port} ({ip_version.value}) - {ip_address} - {response_time:.1f}ms")
                
                return ConnectionTestResult(
                    ip_version=ip_version,
                    host=host,
                    ip_address=ip_address,
                    port=port,
                    success=True,
                    response_time_ms=response_time
                )
                
        except socket.timeout:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"连接超时: {host}:{port} ({ip_version.value}) - {response_time:.1f}ms")
            return ConnectionTestResult(
                ip_version=ip_version,
                host=host,
                ip_address="",
                port=port,
                success=False,
                response_time_ms=response_time,
                error_message="连接超时"
            )
            
        except socket.gaierror as e:
            logger.warning(f"地址解析失败: {host}:{port} ({ip_version.value}) - {str(e)}")
            return ConnectionTestResult(
                ip_version=ip_version,
                host=host,
                port=port,
                success=False,
                response_time_ms=0,
                ip_address="",
                error_message=f"地址解析失败: {str(e)}"
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.warning(f"连接失败: {host}:{port} ({ip_version.value}) - {str(e)} - {response_time:.1f}ms")
            return ConnectionTestResult(
                ip_version=ip_version,
                host=host,
                ip_address="",
                port=port,
                success=False,
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    def test_host_dual_stack(self, host: str, ports: List[int] = None) -> DualStackDecision:
        """测试主机的双栈连接质量"""
        if ports is None:
            ports = [TEST_PORT_HTTP, TEST_PORT_HTTPS]
        
        logger.info(f"开始测试主机 {host} 的双栈连接质量...")
        
        all_results = []
        
        # 准备测试任务
        test_tasks = []
        for port in ports:
            # IPv4测试
            test_tasks.append((host, port, IPVersion.IPV4))
            
            # IPv6测试（仅在系统支持IPv6时）
            if self.ipv6_enabled:
                test_tasks.append((host, port, IPVersion.IPV6))
        
        # 使用线程池并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_TESTS) as executor:
            future_to_task = {
                executor.submit(self._test_single_connection, host, port, ip_version): (host, port, ip_version)
                for host, port, ip_version in test_tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"测试任务执行失败: {e}")
        
        # 分析结果并做出决策
        decision = self._analyze_results(all_results)
        decision.test_results = all_results
        
        return decision
    
    def _analyze_results(self, results: List[ConnectionTestResult]) -> DualStackDecision:
        """分析测试结果并做出双栈选择决策"""
        
        # 分离IPv4和IPv6结果
        ipv4_results = [r for r in results if r.ip_version == IPVersion.IPV4]
        ipv6_results = [r for r in results if r.ip_version == IPVersion.IPV6]
        
        # 计算IPv4质量分数
        ipv4_quality = self._calculate_quality_score(ipv4_results)
        
        # 计算IPv6质量分数
        ipv6_quality = self._calculate_quality_score(ipv6_results) if ipv6_results else None
        
        logger.info(f"IPv4质量分数: {ipv4_quality:.2f}" if ipv4_quality is not None else "IPv4质量分数: 无数据")
        logger.info(f"IPv6质量分数: {ipv6_quality:.2f}" if ipv6_quality is not None else "IPv6质量分数: 无数据")
        
        # 决策逻辑
        if ipv6_quality is None or ipv6_quality == 0:
            # 没有IPv6或IPv6完全不可用
            decision = DualStackDecision(
                recommended_version=IPVersion.IPV4,
                ipv4_quality=ipv4_quality,
                ipv6_quality=ipv6_quality,
                decision_reason="IPv6不可用或测试失败，推荐使用IPv4"
            )
        elif ipv4_quality == 0:
            # IPv4完全不可用，IPv6可用
            decision = DualStackDecision(
                recommended_version=IPVersion.IPV6,
                ipv4_quality=ipv4_quality,
                ipv6_quality=ipv6_quality,
                decision_reason="IPv4不可用，IPv6可用，推荐使用IPv6"
            )
        elif ipv6_quality > ipv4_quality * 1.2:
            # IPv6质量明显优于IPv4（20%以上）
            decision = DualStackDecision(
                recommended_version=IPVersion.IPV6,
                ipv4_quality=ipv4_quality,
                ipv6_quality=ipv6_quality,
                decision_reason=f"IPv6质量({ipv6_quality:.0f})明显优于IPv4({ipv4_quality:.0f})，推荐使用IPv6"
            )
        elif ipv4_quality > ipv6_quality * 1.2:
            # IPv4质量明显优于IPv6
            decision = DualStackDecision(
                recommended_version=IPVersion.IPV4,
                ipv4_quality=ipv4_quality,
                ipv6_quality=ipv6_quality,
                decision_reason=f"IPv4质量({ipv4_quality:.0f})明显优于IPv6({ipv6_quality:.0f})，推荐使用IPv4"
            )
        else:
            # 两者质量相近，优先选择IPv6（更现代的协议）
            if ipv6_quality >= 70:  # IPv6质量足够好
                decision = DualStackDecision(
                    recommended_version=IPVersion.IPV6,
                    ipv4_quality=ipv4_quality,
                    ipv6_quality=ipv6_quality,
                    decision_reason=f"IPv6和IPv4质量相近({ipv6_quality:.0f} vs {ipv4_quality:.0f})，优先选择IPv6"
                )
            else:
                # IPv6质量不够好，选择更稳定的IPv4
                decision = DualStackDecision(
                    recommended_version=IPVersion.IPV4,
                    ipv4_quality=ipv4_quality,
                    ipv6_quality=ipv6_quality,
                    decision_reason=f"IPv6质量不够理想({ipv6_quality:.0f})，选择更稳定的IPv4"
                )
        
        # 标记推荐的结果
        for result in results:
            if result.ip_version == decision.recommended_version and result.success:
                result.is_preferred = True
        
        logger.info(f"双栈决策: {decision.decision_reason}")
        return decision
    
    def _calculate_quality_score(self, results: List[ConnectionTestResult]) -> Optional[float]:
        """计算连接质量分数（0-100）"""
        if not results:
            return None
        
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return 0.0
        
        # 计算成功率（权重：40%）
        success_rate = len(successful_results) / len(results) * 100
        
        # 计算平均响应时间分数（权重：60%）
        avg_response_time = sum(r.response_time_ms for r in successful_results) / len(successful_results)
        
        # 响应时间评分（越快分数越高）
        if avg_response_time <= 100:  # 优秀
            response_score = 100
        elif avg_response_time <= 200:  # 良好
            response_score = 90
        elif avg_response_time <= 300:  # 一般
            response_score = 75
        elif avg_response_time <= 500:  # 较差
            response_score = 50
        else:  # 很差
            response_score = 25
        
        # 综合质量分数
        quality_score = success_rate * 0.4 + response_score * 0.6
        
        return quality_score
    
    def batch_test_hosts(self, hosts: List[str], ports: List[int] = None) -> Dict[str, DualStackDecision]:
        """批量测试多个主机的双栈连接质量"""
        if ports is None:
            ports = [TEST_PORT_HTTP, TEST_PORT_HTTPS]
        
        results = {}
        
        logger.info(f"开始批量测试 {len(hosts)} 个主机的双栈连接质量...")
        
        for i, host in enumerate(hosts, 1):
            try:
                logger.info(f"正在测试第 {i}/{len(hosts)} 个主机: {host}")
                decision = self.test_host_dual_stack(host, ports)
                results[host] = decision
                
                # 记录测试结果摘要
                ipv4_score = decision.ipv4_quality if decision.ipv4_quality is not None else 0
                ipv6_score = decision.ipv6_quality if decision.ipv6_quality is not None else 0
                logger.info(f"{host}: 推荐 {decision.recommended_version.value}, IPv4={ipv4_score:.0f}, IPv6={ipv6_score:.0f}")
                
            except Exception as e:
                logger.error(f"测试主机 {host} 失败: {e}")
                results[host] = DualStackDecision(
                    recommended_version=IPVersion.IPV4,
                    decision_reason=f"测试失败: {str(e)}"
                )
        
        return results
    
    def generate_routing_recommendations(self, test_results: Dict[str, DualStackDecision]) -> Dict:
        """生成路由推荐配置"""
        recommendations = {
            "summary": {
                "total_hosts": len(test_results),
                "ipv4_preferred": sum(1 for d in test_results.values() if d.recommended_version == IPVersion.IPV4),
                "ipv6_preferred": sum(1 for d in test_results.values() if d.recommended_version == IPVersion.IPV6),
                "dual_stack_available": sum(1 for d in test_results.values() if d.ipv4_quality is not None and d.ipv6_quality is not None and d.ipv4_quality > 0 and d.ipv6_quality > 0)
            },
            "ipv6_recommended_hosts": [],
            "ipv4_recommended_hosts": [],
            "quality_statistics": {}
        }
        
        # 分类推荐的主机
        for host, decision in test_results.items():
            if decision.recommended_version == IPVersion.IPV6:
                recommendations["ipv6_recommended_hosts"].append({
                    "host": host,
                    "quality": decision.ipv6_quality,
                    "reason": decision.decision_reason
                })
            else:
                recommendations["ipv4_recommended_hosts"].append({
                    "host": host,
                    "quality": decision.ipv4_quality,
                    "reason": decision.decision_reason
                })
        
        # 计算质量统计
        all_ipv4_scores = [d.ipv4_quality for d in test_results.values() if d.ipv4_quality is not None]
        all_ipv6_scores = [d.ipv6_quality for d in test_results.values() if d.ipv6_quality is not None]
        
        if all_ipv4_scores:
            recommendations["quality_statistics"]["ipv4"] = {
                "average": sum(all_ipv4_scores) / len(all_ipv4_scores),
                "max": max(all_ipv4_scores),
                "min": min(all_ipv4_scores)
            }
        
        if all_ipv6_scores:
            recommendations["quality_statistics"]["ipv6"] = {
                "average": sum(all_ipv6_scores) / len(all_ipv6_scores),
                "max": max(all_ipv6_scores),
                "min": min(all_ipv6_scores)
            }
        
        return recommendations

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能双栈分流系统")
    parser.add_argument("--hosts", nargs="+", help="要测试的主机列表")
    parser.add_argument("--file", help="包含主机列表的文件")
    parser.add_argument("--ports", nargs="+", type=int, default=[80, 443], help="测试端口")
    parser.add_argument("--output", help="输出结果到文件")
    parser.add_argument("--ipv6-only", action="store_true", help="仅测试IPv6")
    parser.add_argument("--ipv4-only", action="store_true", help="仅测试IPv4")
    
    args = parser.parse_args()
    
    # 获取主机列表
    hosts = []
    if args.hosts:
        hosts = args.hosts
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                hosts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            logger.error(f"文件 {args.file} 不存在")
            return 1
    else:
        # 默认测试一些常用网站
        hosts = [
            "google.com", "youtube.com", "facebook.com", "twitter.com",
            "instagram.com", "linkedin.com", "wikipedia.org", "amazon.com",
            "github.com", "stackoverflow.com", "reddit.com", "netflix.com"
        ]
    
    if not hosts:
        logger.error("没有要测试的主机")
        return 1
    
    logger.info(f"开始智能双栈测试，主机数量: {len(hosts)}")
    
    # 创建路由器实例
    router = SmartDualStackRouter()
    
    # 执行测试
    if args.ipv6_only:
        logger.info("IPv6-only模式，仅测试IPv6连接")
        # 这里可以添加IPv6-only测试逻辑
    elif args.ipv4_only:
        logger.info("IPv4-only模式，仅测试IPv4连接")
        # 这里可以添加IPv4-only测试逻辑
    else:
        # 完整双栈测试
        test_results = router.batch_test_hosts(hosts, args.ports)
        recommendations = router.generate_routing_recommendations(test_results)
        
        # 输出结果
        logger.info("=" * 60)
        logger.info("智能双栈测试结果摘要:")
        logger.info(f"总测试主机数: {recommendations['summary']['total_hosts']}")
        logger.info(f"推荐IPv6: {recommendations['summary']['ipv6_preferred']}")
        logger.info(f"推荐IPv4: {recommendations['summary']['ipv4_preferred']}")
        logger.info(f"双栈可用: {recommendations['summary']['dual_stack_available']}")
        
        # 质量统计
        if "ipv4" in recommendations["quality_statistics"]:
            ipv4_stats = recommendations["quality_statistics"]["ipv4"]
            logger.info(f"IPv4平均质量: {ipv4_stats['average']:.1f}")
        
        if "ipv6" in recommendations["quality_statistics"]:
            ipv6_stats = recommendations["quality_statistics"]["ipv6"]
            logger.info(f"IPv6平均质量: {ipv6_stats['average']:.1f}")
        
        # 保存结果到文件
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(recommendations, f, ensure_ascii=False, indent=2, default=str)
                logger.info(f"结果已保存到: {args.output}")
            except Exception as e:
                logger.error(f"保存结果失败: {e}")
        
        logger.info("=" * 60)
        logger.info("智能双栈测试完成!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())