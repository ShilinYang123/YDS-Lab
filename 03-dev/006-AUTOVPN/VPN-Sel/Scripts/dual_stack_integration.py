#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双栈集成模块 - 将智能双栈路由集成到现有VPN系统
"""

import json
import logging
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# 添加脚本目录到Python路径
scripts_dir = Path(__file__).parent
sys.path.append(str(scripts_dir))

from smart_dual_stack import SmartDualStackRouter, IPVersion

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dual_stack_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DomainRoutingConfig:
    """域名路由配置"""
    domain: str
    recommended_ip_version: str
    ipv4_addresses: List[str]
    ipv6_addresses: List[str]
    quality_score: float
    last_updated: str
    routing_priority: int

class DualStackIntegration:
    """双栈集成管理器"""
    
    def __init__(self, config_file: str = "dual_stack_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.router = SmartDualStackRouter()
        self.routing_cache: Dict[str, DomainRoutingConfig] = {}
        self.cache_file = "routing_cache.json"
        self.load_routing_cache()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            config_path = scripts_dir / self.config_file
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"配置文件 {self.config_file} 不存在，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "smart_dual_stack": {
                "enabled": True,
                "auto_switch": True,
                "quality_threshold_ms": 500,
                "update_interval_hours": 24
            },
            "routing_rules": {
                "prefer_ipv6_when_better": True,
                "minimum_ipv6_quality": 60,
                "fallback_to_ipv4": True
            }
        }
    
    def load_routing_cache(self):
        """加载路由缓存"""
        try:
            cache_path = scripts_dir / self.cache_file
            if cache_path.exists():
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    for domain, config_data in cache_data.items():
                        self.routing_cache[domain] = DomainRoutingConfig(**config_data)
                logger.info(f"加载了 {len(self.routing_cache)} 个域名的路由缓存")
            else:
                logger.info("路由缓存文件不存在，创建新的缓存")
        except Exception as e:
            logger.error(f"加载路由缓存失败: {e}")
    
    def save_routing_cache(self):
        """保存路由缓存"""
        try:
            cache_path = scripts_dir / self.cache_file
            cache_data = {}
            for domain, config in self.routing_cache.items():
                cache_data[domain] = {
                    "domain": config.domain,
                    "recommended_ip_version": config.recommended_ip_version,
                    "ipv4_addresses": config.ipv4_addresses,
                    "ipv6_addresses": config.ipv6_addresses,
                    "quality_score": config.quality_score,
                    "last_updated": config.last_updated,
                    "routing_priority": config.routing_priority
                }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"保存了 {len(self.routing_cache)} 个域名的路由缓存")
        except Exception as e:
            logger.error(f"保存路由缓存失败: {e}")
    
    def analyze_domain_list(self, domain_file: str = "常用境外IP.txt") -> Dict[str, DomainRoutingConfig]:
        """分析域名列表的双栈路由配置"""
        try:
            domain_file_path = scripts_dir / domain_file
            if not domain_file_path.exists():
                logger.error(f"域名文件 {domain_file} 不存在")
                return {}
            
            # 读取域名列表
            domains = []
            with open(domain_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # 提取域名（假设格式是：域名 IP地址...）
                        parts = line.split()
                        if parts:
                            domain = parts[0]
                            if domain not in domains:
                                domains.append(domain)
            
            logger.info(f"分析 {len(domains)} 个域名的双栈路由配置")
            
            # 使用智能双栈路由器测试
            test_domains = domains[:50]  # 限制测试数量，避免过多请求
            logger.info(f"实际测试 {len(test_domains)} 个域名")
            
            test_results = self.router.batch_test_hosts(test_domains)
            
            # 获取IP地址（这里需要调用现有的解析脚本）
            domain_ips = self._get_domain_ips(test_domains)
            
            # 生成路由配置
            routing_configs = {}
            for domain in test_domains:
                if domain in test_results:
                    decision = test_results[domain]
                    ips = domain_ips.get(domain, {"ipv4": [], "ipv6": []})
                    
                    quality_score = (decision.ipv6_quality if decision.recommended_version == IPVersion.IPV6 
                                   else decision.ipv4_quality) or 0
                    
                    config = DomainRoutingConfig(
                        domain=domain,
                        recommended_ip_version=decision.recommended_version.value,
                        ipv4_addresses=ips["ipv4"],
                        ipv6_addresses=ips["ipv6"],
                        quality_score=quality_score,
                        last_updated=time.strftime("%Y-%m-%d %H:%M:%S"),
                        routing_priority=self._calculate_priority(quality_score, decision)
                    )
                    
                    routing_configs[domain] = config
                    self.routing_cache[domain] = config
            
            # 保存缓存
            self.save_routing_cache()
            
            logger.info(f"完成 {len(routing_configs)} 个域名的双栈路由分析")
            return routing_configs
            
        except Exception as e:
            logger.error(f"分析域名列表失败: {e}")
            return {}
    
    def _get_domain_ips(self, domains: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """获取域名的IP地址"""
        domain_ips = {}
        
        try:
            # 调用现有的解析脚本获取IP地址
            for domain in domains:
                ipv4_ips = []
                ipv6_ips = []
                
                try:
                    # 使用nslookup获取IPv4地址
                    result = subprocess.run(['nslookup', domain], 
                                          capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('***') and '.' in line:
                                # 简单的IPv4检测
                                parts = line.split()
                                for part in parts:
                                    if self._is_ipv4(part):
                                        ipv4_ips.append(part)
                                    elif self._is_ipv6(part):
                                        ipv6_ips.append(part)
                
                except Exception as e:
                    logger.warning(f"获取 {domain} 的IP地址失败: {e}")
                
                domain_ips[domain] = {
                    "ipv4": list(set(ipv4_ips)),
                    "ipv6": list(set(ipv6_ips))
                }
                
        except Exception as e:
            logger.error(f"批量获取域名IP失败: {e}")
        
        return domain_ips
    
    def _is_ipv4(self, address: str) -> bool:
        """检查是否为IPv4地址"""
        try:
            parts = address.split('.')
            if len(parts) == 4:
                return all(0 <= int(part) <= 255 for part in parts)
        except:
            pass
        return False
    
    def _is_ipv6(self, address: str) -> bool:
        """检查是否为IPv6地址"""
        try:
            return ':' in address and not self._is_ipv4(address)
        except:
            pass
        return False
    
    def _calculate_priority(self, quality_score: float, decision) -> int:
        """计算路由优先级"""
        base_priority = int(quality_score / 10)  # 质量分数转换为优先级
        
        # IPv6额外加分
        if decision.recommended_version == IPVersion.IPV6:
            base_priority += 2
        
        return min(base_priority, 10)  # 最高优先级为10
    
    def generate_smart_hosts_file(self, output_file: str = "smart_hosts.txt") -> bool:
        """生成智能双栈hosts文件"""
        try:
            output_path = scripts_dir / output_file
            
            # 按优先级排序
            sorted_configs = sorted(self.routing_cache.values(), 
                                  key=lambda x: (x.routing_priority, x.quality_score), 
                                  reverse=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# 智能双栈hosts文件 - 根据连接质量自动选择IPv4/IPv6\n")
                f.write(f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总域名数: {len(sorted_configs)}\n\n")
                
                # 按推荐版本分组
                ipv6_domains = [c for c in sorted_configs if c.recommended_ip_version == "IPv6"]
                ipv4_domains = [c for c in sorted_configs if c.recommended_ip_version == "IPv4"]
                
                if ipv6_domains:
                    f.write("# ===== IPv6推荐域名 =====\n")
                    for config in ipv6_domains:
                        if config.ipv6_addresses:
                            f.write(f"{config.ipv6_addresses[0]} {config.domain}")
                            f.write(f"  # 质量: {config.quality_score:.1f}, 优先级: {config.routing_priority}\n")
                        else:
                            f.write(f"# {config.domain} - 推荐IPv6但无IPv6地址\n")
                    f.write("\n")
                
                if ipv4_domains:
                    f.write("# ===== IPv4推荐域名 =====\n")
                    for config in ipv4_domains:
                        if config.ipv4_addresses:
                            f.write(f"{config.ipv4_addresses[0]} {config.domain}")
                            f.write(f"  # 质量: {config.quality_score:.1f}, 优先级: {config.routing_priority}\n")
                        else:
                            f.write(f"# {config.domain} - 推荐IPv4但无IPv4地址\n")
                    f.write("\n")
                
                # 统计信息
                f.write(f"\n# ===== 统计信息 =====\n")
                f.write(f"# IPv6推荐: {len(ipv6_domains)} 个域名\n")
                f.write(f"# IPv4推荐: {len(ipv4_domains)} 个域名\n")
                f.write(f"# 总质量分数: {sum(c.quality_score for c in sorted_configs):.1f}\n")
            
            logger.info(f"生成智能双栈hosts文件: {output_file}")
            logger.info(f"IPv6推荐: {len(ipv6_domains)} 个域名")
            logger.info(f"IPv4推荐: {len(ipv4_domains)} 个域名")
            
            return True
            
        except Exception as e:
            logger.error(f"生成智能双栈hosts文件失败: {e}")
            return False
    
    def update_system_routing(self) -> bool:
        """更新系统路由配置"""
        try:
            logger.info("开始更新系统双栈路由配置...")
            
            # 生成智能hosts文件
            if self.generate_smart_hosts_file():
                logger.info("智能hosts文件生成成功")
            else:
                logger.error("智能hosts文件生成失败")
                return False
            
            # 这里可以添加更多系统路由更新逻辑
            # 例如：更新路由表、DNS配置等
            
            logger.info("系统双栈路由配置更新完成")
            return True
            
        except Exception as e:
            logger.error(f"更新系统路由配置失败: {e}")
            return False
    
    def run_periodic_update(self):
        """运行定期更新"""
        try:
            logger.info("开始定期双栈路由更新...")
            
            # 分析域名列表
            routing_configs = self.analyze_domain_list()
            
            if routing_configs:
                # 更新系统路由
                if self.update_system_routing():
                    logger.info("定期双栈路由更新完成")
                else:
                    logger.error("系统路由更新失败")
            else:
                logger.warning("没有获取到有效的路由配置")
            
        except Exception as e:
            logger.error(f"定期更新失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="双栈集成管理器")
    parser.add_argument("--analyze", action="store_true", help="分析域名列表")
    parser.add_argument("--update", action="store_true", help="更新系统路由")
    parser.add_argument("--domain-file", default="常用境外IP.txt", help="域名文件")
    parser.add_argument("--config-file", default="dual_stack_config.json", help="配置文件")
    parser.add_argument("--output", default="smart_hosts.txt", help="输出文件")
    parser.add_argument("--periodic", action="store_true", help="运行定期更新")
    
    args = parser.parse_args()
    
    # 创建集成管理器
    integration = DualStackIntegration(args.config_file)
    
    if args.analyze:
        # 分析域名列表
        routing_configs = integration.analyze_domain_list(args.domain_file)
        logger.info(f"分析了 {len(routing_configs)} 个域名的双栈配置")
        
    elif args.update:
        # 更新系统路由
        if integration.update_system_routing():
            logger.info("系统双栈路由更新成功")
        else:
            logger.error("系统双栈路由更新失败")
            return 1
            
    elif args.periodic:
        # 运行定期更新
        integration.run_periodic_update()
        
    else:
        # 默认运行完整流程
        logger.info("运行完整的双栈集成流程...")
        
        # 1. 分析域名列表
        routing_configs = integration.analyze_domain_list(args.domain_file)
        
        # 2. 更新系统路由
        if routing_configs:
            if integration.update_system_routing():
                logger.info("双栈集成流程完成")
            else:
                logger.error("系统路由更新失败")
                return 1
        else:
            logger.warning("没有有效的路由配置")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())