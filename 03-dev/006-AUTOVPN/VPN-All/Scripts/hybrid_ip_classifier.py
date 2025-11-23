#!/usr/bin/env python3
"""
混合IP智能分类器
根据IP地址的地理位置、连接质量等因素智能分类路由策略
"""

import os
import json
import logging
import subprocess
import ipaddress
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class IPClassification:
    """IP分类结果"""
    ip_address: str
    category: str  # domestic, foreign_cdn, foreign_direct, special
    confidence: float  # 0-100
    reasoning: str
    recommended_route: str  # physical, virtual, auto

class HybridIPClassifier:
    """混合IP智能分类器"""
    
    def __init__(self, config_file: str = "hybrid_ip_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.china_ip_ranges = self._load_china_ip_ranges()
        self.cdn_providers = self._load_cdn_providers()
        self.special_services = self._load_special_services()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "classification_rules": {
                "china_priority": 95,  # 中国IP分类置信度
                "cdn_threshold": 0.8,  # CDN识别阈值
                "quality_threshold": 80,  # 连接质量阈值
                "latency_threshold_ms": 200  # 延迟阈值
            },
            "routing_policies": {
                "domestic": "physical",  # 国内IP走物理网卡
                "foreign_cdn": "virtual",  # 国外CDN走虚拟网卡
                "foreign_direct": "virtual",  # 国外直连走虚拟网卡
                "special": "auto"  # 特殊服务自动选择
            },
            "test_servers": {
                "china": ["223.5.5.5", "180.76.76.76"],  # 国内测试服务器
                "foreign": ["8.8.8.8", "1.1.1.1"],  # 国外测试服务器
                "cdn": ["104.16.0.0", "172.67.0.0"]  # CDN测试服务器
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # 创建默认配置文件
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                return default_config
        except Exception as e:
            logger.warning(f"加载配置文件失败，使用默认配置: {e}")
            return default_config
    
    def _load_china_ip_ranges(self) -> List[ipaddress.IPv4Network]:
        """加载中国IP地址段"""
        # 这里使用简化的中国IP段，实际应用中应该使用完整的APNIC数据
        china_ranges = [
            "1.0.1.0/24", "1.0.2.0/23", "1.0.8.0/21", "1.0.32.0/19",
            "1.1.0.0/24", "1.1.4.0/22", "1.1.8.0/21", "1.2.0.0/23",
            "1.2.4.0/22", "1.4.1.0/24", "1.4.2.0/23", "1.4.4.0/22",
            "14.0.0.0/21", "14.0.12.0/22", "14.1.0.0/22", "14.1.24.0/22",
            "14.102.128.0/22", "14.102.180.0/22", "14.103.0.0/16",
            "27.0.128.0/22", "27.0.132.0/22", "27.0.160.0/22", "27.0.164.0/22",
            "36.0.0.0/22", "36.0.8.0/21", "36.0.16.0/20", "36.0.32.0/19",
            "39.0.0.0/24", "39.0.2.0/23", "39.0.4.0/22", "39.0.8.0/21",
            "42.0.0.0/22", "42.0.16.0/22", "42.0.24.0/22", "42.0.32.0/19",
            "49.0.0.0/24", "49.0.2.0/23", "49.0.4.0/22", "49.0.8.0/21",
            "58.0.0.0/24", "58.0.2.0/23", "58.0.4.0/22", "58.0.8.0/21",
            "59.32.0.0/11", "59.64.0.0/12", "59.80.0.0/12", "59.96.0.0/12",
            "60.0.0.0/11", "60.32.0.0/12", "60.48.0.0/12", "60.64.0.0/12",
            "61.4.0.0/16", "61.8.0.0/16", "61.14.0.0/16", "61.28.0.0/16",
            "101.0.0.0/22", "101.1.0.0/22", "101.2.172.0/22", "101.16.0.0/12",
            "103.0.0.0/22", "103.4.168.0/22", "103.8.220.0/22", "103.16.108.0/22",
            "110.0.0.0/22", "110.4.0.0/14", "110.16.0.0/12", "110.32.0.0/11",
            "111.0.0.0/22", "111.4.0.0/14", "111.16.0.0/12", "111.32.0.0/11",
            "112.0.0.0/22", "112.4.0.0/14", "112.16.0.0/12", "112.32.0.0/11",
            "113.0.0.0/22", "113.4.0.0/14", "113.16.0.0/12", "113.32.0.0/11",
            "114.0.0.0/22", "114.4.0.0/14", "114.16.0.0/12", "114.32.0.0/11",
            "115.0.0.0/22", "115.4.0.0/14", "115.16.0.0/12", "115.32.0.0/11",
            "116.0.0.0/22", "116.4.0.0/14", "116.16.0.0/12", "116.32.0.0/11",
            "117.0.0.0/22", "117.4.0.0/14", "117.16.0.0/12", "117.32.0.0/11",
            "118.0.0.0/22", "118.4.0.0/14", "118.16.0.0/12", "118.32.0.0/11",
            "119.0.0.0/22", "119.4.0.0/14", "119.16.0.0/12", "119.32.0.0/11",
            "120.0.0.0/22", "120.4.0.0/14", "120.16.0.0/12", "120.32.0.0/11",
            "121.0.0.0/22", "121.4.0.0/14", "121.16.0.0/12", "121.32.0.0/11",
            "122.0.0.0/22", "122.4.0.0/14", "122.16.0.0/12", "122.32.0.0/11",
            "123.0.0.0/22", "123.4.0.0/14", "123.16.0.0/12", "123.32.0.0/11",
            "124.0.0.0/22", "124.4.0.0/14", "124.16.0.0/12", "124.32.0.0/11",
            "125.0.0.0/22", "125.4.0.0/14", "125.16.0.0/12", "125.32.0.0/11",
            "126.0.0.0/22", "126.4.0.0/14", "126.16.0.0/12", "126.32.0.0/11",
            "180.0.0.0/22", "180.4.0.0/14", "180.16.0.0/12", "180.32.0.0/11",
            "182.0.0.0/22", "182.4.0.0/14", "182.16.0.0/12", "182.32.0.0/11",
            "183.0.0.0/22", "183.4.0.0/14", "183.16.0.0/12", "183.32.0.0/11",
            "202.0.0.0/22", "202.4.128.0/22", "202.8.128.0/22", "202.12.0.0/14",
            "203.0.0.0/22", "203.4.128.0/22", "203.8.128.0/22", "203.12.0.0/14",
            "210.0.0.0/22", "210.4.0.0/14", "210.16.0.0/12", "210.32.0.0/11",
            "211.0.0.0/22", "211.4.0.0/14", "211.16.0.0/12", "211.32.0.0/11",
            "218.0.0.0/22", "218.4.0.0/14", "218.16.0.0/12", "218.32.0.0/11",
            "219.0.0.0/22", "219.4.0.0/14", "219.16.0.0/12", "219.32.0.0/11",
            "220.0.0.0/22", "220.4.0.0/14", "220.16.0.0/12", "220.32.0.0/11",
            "221.0.0.0/22", "221.4.0.0/14", "221.16.0.0/12", "221.32.0.0/11",
            "222.0.0.0/22", "222.4.0.0/14", "222.16.0.0/12", "222.32.0.0/11",
            "223.0.0.0/22", "223.4.0.0/14", "223.16.0.0/12", "223.32.0.0/11"
        ]
        
        return [ipaddress.IPv4Network(range_str) for range_str in china_ranges]
    
    def _load_cdn_providers(self) -> Dict[str, List[str]]:
        """加载CDN提供商IP段"""
        return {
            "cloudflare": ["104.16.0.0/12", "172.64.0.0/13", "173.245.48.0/20"],
            "fastly": ["151.101.0.0/16", "146.75.0.0/16"],
            "akamai": ["23.0.0.0/12", "23.32.0.0/11", "23.64.0.0/14"],
            "google": ["172.217.0.0/16", "216.58.192.0/19", "142.250.0.0/15"],
            "amazon": ["13.32.0.0/15", "13.224.0.0/14", "52.84.0.0/15"]
        }
    
    def _load_special_services(self) -> Dict[str, str]:
        """加载特殊服务配置"""
        return {
            "dns_servers": "physical",  # DNS服务器走物理网卡
            "ntp_servers": "physical",  # 时间服务器走物理网卡
            "banking": "physical",  # 银行服务走物理网卡
            "government": "physical",  # 政府网站走物理网卡
            "streaming": "virtual",  # 流媒体走虚拟网卡
            "gaming": "auto"  # 游戏服务自动选择
        }
    
    def classify_ip(self, ip_address: str) -> IPClassification:
        """智能分类IP地址"""
        try:
            ip_obj = ipaddress.IPv4Address(ip_address)
            
            # 1. 检查是否为中国IP
            if self._is_china_ip(ip_address):
                return IPClassification(
                    ip_address=ip_address,
                    category="domestic",
                    confidence=self.config["classification_rules"]["china_priority"],
                    reasoning="IP地址属于中国境内地址段",
                    recommended_route="physical"
                )
            
            # 2. 检查是否为CDN IP
            cdn_provider = self._is_cdn_ip(ip_address)
            if cdn_provider:
                return IPClassification(
                    ip_address=ip_address,
                    category="foreign_cdn",
                    confidence=90.0,
                    reasoning=f"IP地址属于{cdn_provider} CDN网络",
                    recommended_route="virtual"
                )
            
            # 3. 测试连接质量
            quality_score = self._test_ip_quality(ip_address)
            
            if quality_score >= self.config["classification_rules"]["quality_threshold"]:
                return IPClassification(
                    ip_address=ip_address,
                    category="foreign_direct",
                    confidence=quality_score,
                    reasoning=f"国外直连IP，连接质量评分{quality_score:.1f}",
                    recommended_route="virtual"
                )
            else:
                return IPClassification(
                    ip_address=ip_address,
                    category="foreign_cdn",
                    confidence=quality_score,
                    reasoning=f"国外CDN IP，连接质量评分{quality_score:.1f}",
                    recommended_route="virtual"
                )
                
        except Exception as e:
            logger.error(f"IP分类失败 {ip_address}: {e}")
            return IPClassification(
                ip_address=ip_address,
                category="unknown",
                confidence=0.0,
                reasoning=f"分类过程中发生错误: {str(e)}",
                recommended_route="virtual"  # 默认走虚拟网卡
            )
    
    def _is_china_ip(self, ip_address: str) -> bool:
        """检查是否为中国IP"""
        try:
            ip_obj = ipaddress.IPv4Address(ip_address)
            for china_range in self.china_ip_ranges:
                if ip_obj in china_range:
                    return True
            return False
        except Exception as e:
            logger.error(f"中国IP检查失败 {ip_address}: {e}")
            return False
    
    def _is_cdn_ip(self, ip_address: str) -> Optional[str]:
        """检查是否为CDN IP，返回CDN提供商名称"""
        try:
            ip_obj = ipaddress.IPv4Address(ip_address)
            for provider, ranges in self.cdn_providers.items():
                for cidr_range in ranges:
                    if ip_obj in ipaddress.IPv4Network(cidr_range):
                        return provider
            return None
        except Exception as e:
            logger.error(f"CDN IP检查失败 {ip_address}: {e}")
            return None
    
    def _test_ip_quality(self, ip_address: str) -> float:
        """测试IP连接质量，返回0-100的评分"""
        try:
            # 1. 延迟测试
            latency_score = self._test_latency(ip_address)
            
            # 2. 丢包率测试
            packet_loss_score = self._test_packet_loss(ip_address)
            
            # 3. 带宽测试（简化版）
            bandwidth_score = self._test_bandwidth(ip_address)
            
            # 综合评分
            total_score = (latency_score * 0.4 + packet_loss_score * 0.4 + bandwidth_score * 0.2)
            return min(100.0, max(0.0, total_score))
            
        except Exception as e:
            logger.error(f"IP质量测试失败 {ip_address}: {e}")
            return 50.0  # 默认中等质量
    
    def _test_latency(self, ip_address: str) -> float:
        """测试延迟，返回0-100评分"""
        try:
            # 使用ping测试延迟
            result = subprocess.run(
                ["ping", "-n", "3", "-w", "1000", ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # 解析ping输出获取平均延迟
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if '平均' in line or 'Average' in line:
                        # 提取延迟值
                        import re
                        match = re.search(r'(\d+)ms', line)
                        if match:
                            latency = int(match.group(1))
                            # 转换为0-100评分，延迟越低分数越高
                            if latency <= 50:
                                return 100.0
                            elif latency <= 100:
                                return 80.0
                            elif latency <= 200:
                                return 60.0
                            elif latency <= 500:
                                return 40.0
                            else:
                                return 20.0
            
            return 0.0  # ping失败
            
        except Exception as e:
            logger.error(f"延迟测试失败 {ip_address}: {e}")
            return 50.0  # 默认中等延迟
    
    def _test_packet_loss(self, ip_address: str) -> float:
        """测试丢包率，返回0-100评分"""
        try:
            # 使用ping测试丢包率
            result = subprocess.run(
                ["ping", "-n", "10", "-w", "1000", ip_address],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                # 解析ping输出获取丢包率
                output = result.stdout
                import re
                
                # 查找丢包率
                loss_match = re.search(r'(\d+)%', output)
                if loss_match:
                    loss_rate = int(loss_match.group(1))
                    # 转换为0-100评分，丢包率越低分数越高
                    return max(0.0, 100.0 - loss_rate)
            
            return 0.0  # ping失败
            
        except Exception as e:
            logger.error(f"丢包率测试失败 {ip_address}: {e}")
            return 70.0  # 默认较低丢包率
    
    def _test_bandwidth(self, ip_address: str) -> float:
        """测试带宽，返回0-100评分（简化版）"""
        # 这里可以实现更复杂的带宽测试
        # 目前使用基于IP段的估算
        try:
            # 根据IP段估算带宽（这里使用简化的规则）
            ip_obj = ipaddress.IPv4Address(ip_address)
            
            # CDN IP通常有较好带宽
            if self._is_cdn_ip(ip_address):
                return 90.0
            
            # 根据IP段估算
            first_octet = int(ip_address.split('.')[0])
            if first_octet in [8, 9, 104, 151, 172]:  # 常见高质量IP段
                return 80.0
            elif first_octet in [13, 23, 43, 52]:  # 中等质量IP段
                return 60.0
            else:
                return 40.0
                
        except Exception as e:
            logger.error(f"带宽测试失败 {ip_address}: {e}")
            return 50.0  # 默认中等带宽
    
    def batch_classify(self, ip_addresses: List[str]) -> List[IPClassification]:
        """批量分类IP地址"""
        results = []
        total = len(ip_addresses)
        
        for i, ip_addr in enumerate(ip_addresses):
            logger.info(f"分类进度: {i+1}/{total} - {ip_addr}")
            classification = self.classify_ip(ip_addr)
            results.append(classification)
            
        return results
    
    def generate_routing_config(self, classifications: List[IPClassification]) -> str:
        """生成路由配置脚本"""
        physical_routes = []
        virtual_routes = []
        
        for classification in classifications:
            if classification.recommended_route == "physical":
                physical_routes.append(classification.ip_address)
            else:
                virtual_routes.append(classification.ip_address)
        
        config_script = f"""# 混合IP路由配置脚本
# 生成时间: {logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", (), None))}

# 物理网卡路由（国内IP）
"""
        
        for ip in physical_routes:
            config_script += f"route add {ip} mask 255.255.255.255 192.168.1.1 metric 1\n"
        
        config_script += f"\n# 虚拟网卡路由（国外IP）\n"
        
        for ip in virtual_routes:
            config_script += f"route add {ip} mask 255.255.255.255 10.9.0.1 metric 1\n"
        
        config_script += f"""
# 统计信息
# 物理网卡路由: {len(physical_routes)} 条
# 虚拟网卡路由: {len(virtual_routes)} 条
# 总计: {len(classifications)} 个IP地址
"""
        
        return config_script


def main():
    """主函数"""
    classifier = HybridIPClassifier()
    
    # 测试IP地址
    test_ips = [
        "223.5.5.5",      # 阿里云DNS（国内）
        "180.76.76.76",   # 百度DNS（国内）
        "104.16.0.0",     # Cloudflare CDN
        "172.67.0.0",     # Cloudflare CDN
        "8.8.8.8",        # Google DNS
        "1.1.1.1",        # Cloudflare DNS
        "142.250.0.1",    # Google
        "157.148.69.74"   # 国外直连
    ]
    
    logger.info("开始测试混合IP分类器...")
    
    # 批量分类
    classifications = classifier.batch_classify(test_ips)
    
    # 输出分类结果
    logger.info("\n=== IP分类结果 ===")
    for classification in classifications:
        logger.info(f"IP: {classification.ip_address}")
        logger.info(f"  分类: {classification.category}")
        logger.info(f"  置信度: {classification.confidence:.1f}%")
        logger.info(f"  推理: {classification.reasoning}")
        logger.info(f"  推荐路由: {classification.recommended_route}")
        logger.info("")
    
    # 生成路由配置
    routing_config = classifier.generate_routing_config(classifications)
    logger.info("\n=== 生成的路由配置 ===")
    logger.info(routing_config)
    
    # 保存路由配置到文件
    config_file = "hybrid_routing_config.bat"
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(routing_config)
        logger.info(f"路由配置已保存到: {config_file}")
    except Exception as e:
        logger.error(f"保存路由配置失败: {e}")


if __name__ == "__main__":
    main()