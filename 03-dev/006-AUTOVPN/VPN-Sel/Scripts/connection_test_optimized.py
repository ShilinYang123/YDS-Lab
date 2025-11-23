#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的连接测试模块 - 增强的失败处理和重试机制
"""

import socket
import time
import logging
import concurrent.futures
import random
import json
import os
import sys
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import threading
import queue

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('connection_test_optimized.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestResult(Enum):
    """测试结果枚举"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    CONNECTION_REFUSED = "connection_refused"
    DNS_FAILED = "dns_failed"
    NETWORK_UNREACHABLE = "network_unreachable"
    UNKNOWN_ERROR = "unknown_error"

class RetryStrategy(Enum):
    """重试策略枚举"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_INTERVAL = "fixed_interval"
    ADAPTIVE = "adaptive"

@dataclass
class ConnectionTestConfig:
    """连接测试配置"""
    timeout: float = 5.0
    retry_count: int = 3
    retry_delay: float = 1.0
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_concurrent_tests: int = 20
    connection_pool_size: int = 5
    enable_keepalive: bool = True
    keepalive_interval: float = 30.0
    failure_threshold: int = 5
    success_rate_threshold: float = 0.6
    adaptive_timeout_min: float = 1.0
    adaptive_timeout_max: float = 10.0

@dataclass
class TestAttempt:
    """测试尝试记录"""
    attempt_number: int
    start_time: float
    end_time: float
    result: TestResult
    response_time: float
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None

@dataclass
class OptimizedConnectionResult:
    """优化的连接测试结果"""
    host: str
    port: int
    ip_version: str
    final_result: TestResult
    success: bool
    best_response_time: float
    average_response_time: float
    attempts: List[TestAttempt]
    total_attempts: int
    successful_attempts: int
    failure_rate: float
    recommended_action: str
    timestamp: str
    error_pattern: Optional[str] = None

class ConnectionPool:
    """连接池管理器"""
    
    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self.pools: Dict[str, queue.Queue] = {}
        self.lock = threading.Lock()
        self.connection_stats: Dict[str, Dict] = {}
    
    def get_connection(self, host: str, port: int, timeout: float) -> Optional[socket.socket]:
        """从连接池获取连接"""
        pool_key = f"{host}:{port}"
        
        with self.lock:
            if pool_key not in self.pools:
                self.pools[pool_key] = queue.Queue(maxsize=self.max_size)
                self.connection_stats[pool_key] = {"created": 0, "reused": 0, "failed": 0}
            
            pool = self.pools[pool_key]
            
            try:
                # 尝试从池中获取连接
                conn = pool.get_nowait()
                
                # 检查连接是否仍然有效
                if self._is_connection_valid(conn):
                    self.connection_stats[pool_key]["reused"] += 1
                    return conn
                else:
                    # 连接无效，关闭它
                    try:
                        conn.close()
                    except:
                        pass
                    self.connection_stats[pool_key]["failed"] += 1
            except queue.Empty:
                pass
            
            # 创建新连接
            try:
                conn = self._create_connection(host, port, timeout)
                if conn:
                    self.connection_stats[pool_key]["created"] += 1
                    return conn
            except Exception as e:
                logger.warning(f"创建连接失败 {host}:{port} - {e}")
            
            return None
    
    def return_connection(self, host: str, port: int, conn: socket.socket, is_valid: bool = True):
        """将连接返回到连接池"""
        if not is_valid:
            try:
                conn.close()
            except:
                pass
            return
        
        pool_key = f"{host}:{port}"
        
        with self.lock:
            if pool_key in self.pools:
                pool = self.pools[pool_key]
                try:
                    pool.put_nowait(conn)
                except queue.Full:
                    # 池已满，关闭连接
                    try:
                        conn.close()
                    except:
                        pass
    
    def _create_connection(self, host: str, port: int, timeout: float) -> Optional[socket.socket]:
        """创建新连接"""
        try:
            # 获取地址信息
            addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            
            if not addr_info:
                return None
            
            # 尝试连接第一个可用的地址
            family, socktype, proto, canonname, sockaddr = addr_info[0]
            
            sock = socket.socket(family, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # 启用TCP keepalive
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            return sock
            
        except Exception as e:
            logger.warning(f"创建连接失败 {host}:{port} - {e}")
            return None
    
    def _is_connection_valid(self, conn: socket.socket) -> bool:
        """检查连接是否仍然有效"""
        try:
            # 尝试非阻塞读取
            conn.settimeout(0)
            try:
                data = conn.recv(1, socket.MSG_PEEK)
                return True
            except socket.error:
                # 没有数据可读，连接可能仍然有效
                return True
        except:
            return False
    
    def get_stats(self) -> Dict[str, Dict]:
        """获取连接池统计信息"""
        return self.connection_stats.copy()

class OptimizedConnectionTester:
    """优化的连接测试器"""
    
    def __init__(self, config: Optional[ConnectionTestConfig] = None):
        self.config = config or ConnectionTestConfig()
        self.connection_pool = ConnectionPool(self.config.connection_pool_size)
        self.failure_history: Dict[str, List[TestAttempt]] = {}
        self.success_rate_tracker: Dict[str, float] = {}
        self.adaptive_timeout = self.config.timeout
        
    def test_connection_with_retry(self, host: str, port: int, ip_version: str = "auto") -> OptimizedConnectionResult:
        """带重试机制的连接测试"""
        logger.info(f"开始测试 {host}:{port} (IP版本: {ip_version})")
        
        attempts = []
        final_result = TestResult.UNKNOWN_ERROR
        best_response_time = float('inf')
        total_response_time = 0
        successful_attempts = 0
        
        # 自适应超时调整
        current_timeout = self._get_adaptive_timeout(host, port)
        
        for attempt_num in range(1, self.config.retry_count + 1):
            logger.debug(f"第 {attempt_num} 次尝试测试 {host}:{port}")
            
            start_time = time.time()
            
            try:
                # 执行单次测试
                test_result = self._perform_single_test(host, port, current_timeout, ip_version)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                # 创建尝试记录
                attempt = TestAttempt(
                    attempt_number=attempt_num,
                    start_time=start_time,
                    end_time=end_time,
                    result=test_result.result,
                    response_time=response_time,
                    error_message=test_result.error_message,
                    ip_address=test_result.ip_address,
                    port=port
                )
                
                attempts.append(attempt)
                
                # 更新统计信息
                if test_result.result == TestResult.SUCCESS:
                    successful_attempts += 1
                    total_response_time += response_time
                    if response_time < best_response_time:
                        best_response_time = response_time
                    
                    logger.info(f"第 {attempt_num} 次尝试成功: {response_time:.1f}ms")
                    
                    # 如果成功，可以选择继续测试或停止
                    if attempt_num == 1 or response_time < 200:  # 第一次或响应很快
                        final_result = TestResult.SUCCESS
                        break
                    
                else:
                    logger.warning(f"第 {attempt_num} 次尝试失败: {test_result.error_message}")
                    
                    # 根据失败类型决定是否重试
                    if not self._should_retry_for_error(test_result.result, attempt_num):
                        final_result = test_result.result
                        break
                
                # 计算重试延迟
                if attempt_num < self.config.retry_count:
                    retry_delay = self._calculate_retry_delay(attempt_num, test_result.result)
                    logger.debug(f"等待 {retry_delay:.1f} 秒后重试")
                    time.sleep(retry_delay)
                    
                    # 自适应调整超时时间
                    current_timeout = self._adjust_timeout_for_retry(current_timeout, test_result.result)
                
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                logger.error(f"第 {attempt_num} 次尝试异常: {str(e)}")
                
                attempt = TestAttempt(
                    attempt_number=attempt_num,
                    start_time=start_time,
                    end_time=end_time,
                    result=TestResult.UNKNOWN_ERROR,
                    response_time=response_time,
                    error_message=str(e)
                )
                
                attempts.append(attempt)
                
                if attempt_num == self.config.retry_count:
                    final_result = TestResult.UNKNOWN_ERROR
        
        # 计算最终结果
        if not attempts:
            final_result = TestResult.UNKNOWN_ERROR
        elif final_result == TestResult.UNKNOWN_ERROR:
            # 根据最后一次尝试确定最终结果
            final_result = attempts[-1].result
        
        # 计算平均响应时间
        avg_response_time = (total_response_time / successful_attempts) if successful_attempts > 0 else 0
        
        # 计算失败率
        failure_rate = (len(attempts) - successful_attempts) / len(attempts) if attempts else 1.0
        
        # 错误模式分析
        error_pattern = self._analyze_error_pattern(attempts)
        
        # 生成推荐动作
        recommended_action = self._generate_recommendation(final_result, failure_rate, avg_response_time)
        
        # 更新历史记录和成功率
        self._update_failure_history(host, port, attempts)
        self._update_success_rate_tracker(host, port, successful_attempts, len(attempts))
        
        result = OptimizedConnectionResult(
            host=host,
            port=port,
            ip_version=ip_version,
            final_result=final_result,
            success=final_result == TestResult.SUCCESS,
            best_response_time=best_response_time if best_response_time != float('inf') else 0,
            average_response_time=avg_response_time,
            attempts=attempts,
            total_attempts=len(attempts),
            successful_attempts=successful_attempts,
            failure_rate=failure_rate,
            recommended_action=recommended_action,
            timestamp=datetime.now().isoformat(),
            error_pattern=error_pattern
        )
        
        logger.info(f"测试完成 {host}:{port} - 结果: {final_result.value}, "
                   f"成功率: {successful_attempts}/{len(attempts)}, "
                   f"最佳响应: {result.best_response_time:.1f}ms")
        
        return result
    
    def _perform_single_test(self, host: str, port: int, timeout: float, ip_version: str) -> NamedTuple:
        """执行单次连接测试"""
        
        class SingleTestResult(NamedTuple):
            result: TestResult
            error_message: Optional[str] = None
            ip_address: Optional[str] = None
        
        try:
            # 从连接池获取连接
            conn = self.connection_pool.get_connection(host, port, timeout)
            
            if conn is None:
                return SingleTestResult(TestResult.UNKNOWN_ERROR, "无法创建连接")
            
            try:
                # 获取地址信息并连接
                if ip_version == "ipv4":
                    addr_info = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
                elif ip_version == "ipv6":
                    addr_info = socket.getaddrinfo(host, port, socket.AF_INET6, socket.SOCK_STREAM)
                else:
                    addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                
                if not addr_info:
                    return SingleTestResult(TestResult.DNS_FAILED, "无法解析地址")
                
                # 使用第一个地址
                family, socktype, proto, canonname, sockaddr = addr_info[0]
                
                # 如果是新连接，执行连接
                if conn.fileno() == -1:  # 文件描述符无效，需要重新连接
                    conn.connect(sockaddr)
                
                # 获取IP地址
                ip_address = sockaddr[0]
                
                # 连接成功
                self.connection_pool.return_connection(host, port, conn, True)
                return SingleTestResult(TestResult.SUCCESS, ip_address=ip_address)
                
            except socket.timeout:
                self.connection_pool.return_connection(host, port, conn, False)
                return SingleTestResult(TestResult.TIMEOUT, "连接超时")
                
            except socket.gaierror as e:
                self.connection_pool.return_connection(host, port, conn, False)
                return SingleTestResult(TestResult.DNS_FAILED, f"DNS解析失败: {str(e)}")
                
            except ConnectionRefusedError:
                self.connection_pool.return_connection(host, port, conn, False)
                return SingleTestResult(TestResult.CONNECTION_REFUSED, "连接被拒绝")
                
            except OSError as e:
                self.connection_pool.return_connection(host, port, conn, False)
                if e.errno == 51:  # Network is unreachable
                    return SingleTestResult(TestResult.NETWORK_UNREACHABLE, "网络不可达")
                else:
                    return SingleTestResult(TestResult.UNKNOWN_ERROR, f"网络错误: {str(e)}")
                    
            except Exception as e:
                self.connection_pool.return_connection(host, port, conn, False)
                return SingleTestResult(TestResult.UNKNOWN_ERROR, f"未知错误: {str(e)}")
                
        except socket.gaierror as e:
            return SingleTestResult(TestResult.DNS_FAILED, f"DNS解析失败: {str(e)}")
        except Exception as e:
            return SingleTestResult(TestResult.UNKNOWN_ERROR, f"连接创建失败: {str(e)}")
    
    def _calculate_retry_delay(self, attempt_num: int, last_result: TestResult) -> float:
        """计算重试延迟"""
        base_delay = self.config.retry_delay
        
        if self.config.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            # 指数退避
            delay = base_delay * (2 ** (attempt_num - 1))
            
            # 根据错误类型调整
            if last_result == TestResult.CONNECTION_REFUSED:
                delay *= 0.5  # 连接被拒绝，可以快速重试
            elif last_result == TestResult.NETWORK_UNREACHABLE:
                delay *= 2.0  # 网络不可达，等待更长时间
            
            # 添加随机抖动
            delay = delay * (0.5 + random.random())
            
        elif self.config.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            # 线性退避
            delay = base_delay * attempt_num
            
        elif self.config.retry_strategy == RetryStrategy.FIXED_INTERVAL:
            # 固定间隔
            delay = base_delay
            
        elif self.config.retry_strategy == RetryStrategy.ADAPTIVE:
            # 自适应策略
            delay = self._adaptive_retry_delay(attempt_num, last_result)
            
        else:
            delay = base_delay
        
        # 限制最大延迟
        return min(delay, 30.0)  # 最大30秒
    
    def _adaptive_retry_delay(self, attempt_num: int, last_result: TestResult) -> float:
        """自适应重试延迟"""
        base_delay = self.config.retry_delay
        
        # 基于历史成功率调整
        # 这里简化处理，实际可以更复杂
        if last_result == TestResult.SUCCESS:
            return base_delay * 0.5
        elif last_result == TestResult.TIMEOUT:
            return base_delay * 2.0
        elif last_result == TestResult.CONNECTION_REFUSED:
            return base_delay * 1.5
        else:
            return base_delay * attempt_num
    
    def _should_retry_for_error(self, error_result: TestResult, attempt_num: int) -> bool:
        """根据错误类型决定是否重试"""
        # 某些错误不应该重试
        if error_result == TestResult.NETWORK_UNREACHABLE:
            return attempt_num <= 1  # 只重试一次
        elif error_result == TestResult.DNS_FAILED:
            return attempt_num <= 2  # 最多重试2次
        elif error_result == TestResult.CONNECTION_REFUSED:
            return True  # 可以重试
        elif error_result == TestResult.TIMEOUT:
            return attempt_num <= self.config.retry_count - 1  # 可以重试，但限制次数
        else:
            return True  # 其他错误默认重试
    
    def _adjust_timeout_for_retry(self, current_timeout: float, last_result: TestResult) -> float:
        """为重试调整超时时间"""
        if last_result == TestResult.TIMEOUT:
            # 如果上次超时，增加超时时间
            return min(current_timeout * 1.5, self.config.adaptive_timeout_max)
        elif last_result == TestResult.SUCCESS:
            # 如果上次成功，可以尝试减少超时时间
            return max(current_timeout * 0.8, self.config.adaptive_timeout_min)
        else:
            return current_timeout
    
    def _get_adaptive_timeout(self, host: str, port: int) -> float:
        """获取自适应超时时间"""
        # 基于历史成功率调整超时时间
        key = f"{host}:{port}"
        success_rate = self.success_rate_tracker.get(key, 1.0)
        
        if success_rate < 0.5:  # 成功率低
            return min(self.config.timeout * 1.5, self.config.adaptive_timeout_max)
        elif success_rate > 0.9:  # 成功率高
            return max(self.config.timeout * 0.7, self.config.adaptive_timeout_min)
        else:
            return self.config.timeout
    
    def _analyze_error_pattern(self, attempts: List[TestAttempt]) -> Optional[str]:
        """分析错误模式"""
        if not attempts:
            return None
        
        error_types = [attempt.result for attempt in attempts]
        
        # 检查是否都是同一种错误
        if len(set(error_types)) == 1:
            return f"consistent_{error_types[0].value}"
        
        # 检查错误趋势
        if len(error_types) >= 3:
            if error_types[-3:] == [TestResult.TIMEOUT, TestResult.TIMEOUT, TestResult.TIMEOUT]:
                return "timeout_escalation"
            elif error_types[-2:] == [TestResult.CONNECTION_REFUSED, TestResult.CONNECTION_REFUSED]:
                return "persistent_refusal"
        
        # 检查成功模式
        success_count = sum(1 for attempt in attempts if attempt.result == TestResult.SUCCESS)
        if success_count > len(attempts) / 2:
            return "intermittent_success"
        
        return "mixed_errors"
    
    def _generate_recommendation(self, final_result: TestResult, failure_rate: float, avg_response_time: float) -> str:
        """生成推荐动作"""
        if final_result == TestResult.SUCCESS:
            if failure_rate > 0.3:
                return "connection_unstable_consider_alternative"
            elif avg_response_time > 1000:
                return "connection_slow_consider_optimization"
            else:
                return "connection_healthy"
        elif final_result == TestResult.TIMEOUT:
            return "check_network_latency_increase_timeout"
        elif final_result == TestResult.CONNECTION_REFUSED:
            return "service_may_be_down_check_service_status"
        elif final_result == TestResult.NETWORK_UNREACHABLE:
            return "check_network_configuration"
        elif final_result == TestResult.DNS_FAILED:
            return "check_dns_configuration_try_alternative_dns"
        else:
            return "investigate_network_connectivity"
    
    def _update_failure_history(self, host: str, port: int, attempts: List[TestAttempt]):
        """更新失败历史记录"""
        key = f"{host}:{port}"
        
        if key not in self.failure_history:
            self.failure_history[key] = []
        
        # 保留最近10次测试记录
        self.failure_history[key].extend(attempts)
        self.failure_history[key] = self.failure_history[key][-10:]
    
    def _update_success_rate_tracker(self, host: str, port: int, successful: int, total: int):
        """更新成功率跟踪器"""
        key = f"{host}:{port}"
        current_rate = successful / total if total > 0 else 0
        
        if key not in self.success_rate_tracker:
            self.success_rate_tracker[key] = current_rate
        else:
            # 使用滑动平均
            old_rate = self.success_rate_tracker[key]
            self.success_rate_tracker[key] = (old_rate * 0.7 + current_rate * 0.3)
    
    def batch_test_with_optimization(self, targets: List[Tuple[str, int, str]]) -> List[OptimizedConnectionResult]:
        """批量优化测试"""
        logger.info(f"开始批量优化测试 {len(targets)} 个目标")
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_concurrent_tests) as executor:
            # 提交所有测试任务
            future_to_target = {
                executor.submit(self.test_connection_with_retry, host, port, ip_version): (host, port, ip_version)
                for host, port, ip_version in targets
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_target):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 记录进度
                    host, port, ip_version = future_to_target[future]
                    logger.info(f"完成测试 {host}:{port} - 成功率: {result.successful_attempts}/{result.total_attempts}")
                    
                except Exception as e:
                    logger.error(f"测试任务失败: {e}")
        
        # 生成测试报告
        self._generate_test_report(results)
        
        return results
    
    def _generate_test_report(self, results: List[OptimizedConnectionResult]):
        """生成测试报告"""
        if not results:
            return
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.success)
        total_attempts = sum(r.total_attempts for r in results)
        successful_attempts = sum(r.successful_attempts for r in results)
        
        logger.info("=" * 60)
        logger.info("优化连接测试报告")
        logger.info("=" * 60)
        logger.info(f"总测试目标数: {total_tests}")
        logger.info(f"成功测试数: {successful_tests}")
        logger.info(f"总尝试次数: {total_attempts}")
        logger.info(f"成功尝试次数: {successful_attempts}")
        logger.info(f"整体成功率: {successful_tests/total_tests*100:.1f}%")
        logger.info(f"尝试成功率: {successful_attempts/total_attempts*100:.1f}%")
        
        # 按结果类型统计
        result_counts = {}
        for result in results:
            result_type = result.final_result.value
            result_counts[result_type] = result_counts.get(result_type, 0) + 1
        
        logger.info("\n结果分布:")
        for result_type, count in result_counts.items():
            logger.info(f"  {result_type}: {count}")
        
        # 响应时间统计
        response_times = [r.best_response_time for r in results if r.success]
        if response_times:
            logger.info(f"\n响应时间统计:")
            logger.info(f"  平均响应时间: {sum(response_times)/len(response_times):.1f}ms")
            logger.info(f"  最快响应时间: {min(response_times):.1f}ms")
            logger.info(f"  最慢响应时间: {max(response_times):.1f}ms")
        
        # 连接池统计
        pool_stats = self.connection_pool.get_stats()
        if pool_stats:
            logger.info(f"\n连接池统计:")
            total_created = sum(stats["created"] for stats in pool_stats.values())
            total_reused = sum(stats["reused"] for stats in pool_stats.values())
            logger.info(f"  创建连接数: {total_created}")
            logger.info(f"  重用连接数: {total_reused}")
            if total_created + total_reused > 0:
                reuse_rate = total_reused / (total_created + total_reused) * 100
                logger.info(f"  连接重用率: {reuse_rate:.1f}%")
        
        logger.info("=" * 60)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="优化的连接测试工具")
    parser.add_argument("--hosts", nargs="+", help="要测试的主机列表")
    parser.add_argument("--file", help="包含主机列表的文件")
    parser.add_argument("--ports", nargs="+", type=int, default=[80, 443], help="测试端口")
    parser.add_argument("--timeout", type=float, default=5.0, help="连接超时时间")
    parser.add_argument("--retry-count", type=int, default=3, help="重试次数")
    parser.add_argument("--max-concurrent", type=int, default=20, help="最大并发数")
    parser.add_argument("--retry-strategy", choices=["exponential", "linear", "fixed", "adaptive"], 
                       default="exponential", help="重试策略")
    parser.add_argument("--output", help="输出结果到文件")
    parser.add_argument("--detailed", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.detailed:
        logger.setLevel(logging.DEBUG)
    
    # 获取测试目标
    targets = []
    if args.hosts:
        for host in args.hosts:
            for port in args.ports:
                targets.append((host, port, "auto"))
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if parts:
                            host = parts[0]
                            for port in args.ports:
                                targets.append((host, port, "auto"))
        except FileNotFoundError:
            logger.error(f"文件 {args.file} 不存在")
            return 1
    else:
        # 默认测试一些常用网站
        default_hosts = [
            "google.com", "youtube.com", "facebook.com", "twitter.com",
            "github.com", "stackoverflow.com", "reddit.com", "netflix.com"
        ]
        for host in default_hosts:
            for port in args.ports:
                targets.append((host, port, "auto"))
    
    if not targets:
        logger.error("没有要测试的目标")
        return 1
    
    logger.info(f"开始优化连接测试，目标数量: {len(targets)}")
    
    # 创建测试配置
    strategy_map = {
        "exponential": RetryStrategy.EXPONENTIAL_BACKOFF,
        "linear": RetryStrategy.LINEAR_BACKOFF,
        "fixed": RetryStrategy.FIXED_INTERVAL,
        "adaptive": RetryStrategy.ADAPTIVE
    }
    
    config = ConnectionTestConfig(
        timeout=args.timeout,
        retry_count=args.retry_count,
        retry_strategy=strategy_map[args.retry_strategy],
        max_concurrent_tests=args.max_concurrent
    )
    
    # 创建测试器
    tester = OptimizedConnectionTester(config)
    
    # 执行测试
    start_time = time.time()
    results = tester.batch_test_with_optimization(targets)
    end_time = time.time()
    
    logger.info(f"测试完成，总耗时: {end_time - start_time:.1f}秒")
    
    # 保存结果
    if args.output:
        try:
            output_data = []
            for result in results:
                output_data.append({
                    "host": result.host,
                    "port": result.port,
                    "ip_version": result.ip_version,
                    "success": result.success,
                    "final_result": result.final_result.value,
                    "best_response_time": result.best_response_time,
                    "average_response_time": result.average_response_time,
                    "failure_rate": result.failure_rate,
                    "recommended_action": result.recommended_action,
                    "timestamp": result.timestamp
                })
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结果已保存到: {args.output}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())