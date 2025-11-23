#!/usr/bin/env python3
"""
混合hosts分区路由系统
基于hosts文件中的IP来源分区，智能配置路由策略
避免DNS污染风险的核心解决方案
"""

import os
import re
import json
import logging
import subprocess
import ipaddress
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridHostsRouter:
    """混合hosts分区路由器"""
    
    def __init__(self):
        self.hosts_file = r"C:\Windows\System32\drivers\etc\hosts"
        self.backup_dir = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-All\backups"
        self.config_file = "hybrid_routing_config.json"
        self.routes_dir = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-All\routes"
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.routes_dir, exist_ok=True)
        
        self.config = self._load_config()
        self.physical_interface = self._get_physical_interface()
        self.virtual_interface = self._get_virtual_interface()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "hosts_sections": {
                "domestic": {
                    "marker": "# [DOMESTIC_IPS] - 国内纯净IP区域",
                    "description": "确定的国内IP地址，走物理网卡",
                    "route_policy": "physical",
                    "metric": 1
                },
                "foreign_verified": {
                    "marker": "# [FOREIGN_VERIFIED_IPS] - 国外验证纯净IP区域", 
                    "description": "通过隧道验证的国外纯净IP，走虚拟网卡",
                    "route_policy": "virtual",
                    "metric": 1
                },
                "foreign_cdn": {
                    "marker": "# [FOREIGN_CDN_IPS] - 国外CDN IP区域",
                    "description": "国外CDN IP地址，走虚拟网卡",
                    "route_policy": "virtual", 
                    "metric": 1
                },
                "special": {
                    "marker": "# [SPECIAL_IPS] - 特殊服务IP区域",
                    "description": "特殊服务IP（DNS、银行等），按策略路由",
                    "route_policy": "auto",
                    "metric": 1
                }
            },
            "routing": {
                "physical_gateway": "192.168.1.1",  # 物理网关
                "virtual_gateway": "10.9.0.1",     # WireGuard网关
                "physical_metric": 10,              # 物理路由优先级
                "virtual_metric": 5                  # 虚拟路由优先级
            },
            "validation": {
                "enable_tunnel_check": True,         # 启用隧道验证
                "max_route_entries": 1000,          # 最大路由条目数
                "backup_before_change": True         # 修改前备份
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
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                return default_config
        except Exception as e:
            logger.warning(f"加载配置文件失败，使用默认配置: {e}")
            return default_config
    
    def _get_physical_interface(self) -> str:
        """获取物理网卡接口名称"""
        try:
            result = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '0.0.0.0' in line and 'Gateway' not in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            return parts[3]  # 接口索引
            
            return "1"  # 默认接口
            
        except Exception as e:
            logger.error(f"获取物理接口失败: {e}")
            return "1"
    
    def _get_virtual_interface(self) -> str:
        """获取虚拟网卡接口名称"""
        try:
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'WireGuard' in line or 'VPN' in line:
                        # 查找对应的接口信息
                        for j in range(i+1, min(i+10, len(lines))):
                            if 'Physical Address' in lines[j]:
                                # 提取接口索引（这里简化处理）
                                return "2"  # 假设虚拟接口为2
            
            return "2"  # 默认虚拟接口
            
        except Exception as e:
            logger.error(f"获取虚拟接口失败: {e}")
            return "2"
    
    def parse_hosts_file(self) -> Dict[str, List[str]]:
        """解析hosts文件，提取分区IP地址"""
        sections = {
            'domestic': [],
            'foreign_verified': [],
            'foreign_cdn': [],
            'special': []
        }
        
        try:
            with open(self.hosts_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            logger.error(f"hosts文件不存在: {self.hosts_file}")
            return sections
        except Exception as e:
            logger.error(f"读取hosts文件失败: {e}")
            return sections
        
        current_section = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # 跳过空行和注释行
            if not line or line.startswith('#') and not self._is_section_marker(line):
                continue
            
            # 检查区域标记
            section_marker = self._is_section_marker(line)
            if section_marker:
                current_section = section_marker
                logger.info(f"找到区域标记: {current_section} (第{line_num}行)")
                continue
            
            # 如果当前没有区域，跳过
            if not current_section:
                continue
            
            # 解析IP地址行 (格式: IP地址 域名)
            if ' ' in line or '\t' in line:
                parts = line.split()
                if len(parts) >= 2:
                    ip = parts[0].strip()
                    # 验证IP地址格式
                    if self._is_valid_ip(ip):
                        sections[current_section].append(ip)
                        logger.debug(f"添加IP到 {current_section}: {ip}")
                    else:
                        logger.warning(f"第{line_num}行: 无效IP格式: {ip}")
        
        # 去重并统计
        for section in sections:
            original_count = len(sections[section])
            sections[section] = list(set(sections[section]))
            unique_count = len(sections[section])
            if original_count != unique_count:
                logger.info(f"{section}: 去重 {original_count} -> {unique_count}")
        
        logger.info(f"\n=== hosts文件解析结果 ===")
        for section, ips in sections.items():
            logger.info(f"{section}: {len(ips)} 个IP")
            if ips:
                logger.info(f"  示例: {ips[:3]}...")  # 显示前3个IP
        
        return sections
    
    def _is_section_marker(self, line: str) -> Optional[str]:
        """检查是否为区域标记"""
        line = line.strip()
        if not line.startswith('#'):
            return None
        
        # 移除开头的#和空格
        content = line[1:].strip()
        
        # 检查各区域标记
        if '[DOMESTIC_IPS]' in content or '国内' in content:
            return 'domestic'
        elif '[FOREIGN_VERIFIED_IPS]' in content or '国外验证' in content:
            return 'foreign_verified'
        elif '[FOREIGN_CDN_IPS]' in content or '国外CDN' in content:
            return 'foreign_cdn'
        elif '[SPECIAL_IPS]' in content or '特殊' in content:
            return 'special'
        
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """验证IP地址格式"""
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ValueError:
            return False
    
    def backup_hosts_file(self) -> bool:
        """备份hosts文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"hosts_backup_{timestamp}")
            
            if os.path.exists(self.hosts_file):
                with open(self.hosts_file, 'r', encoding='utf-8') as src:
                    content = src.read()
                
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(content)
                
                logger.info(f"hosts文件已备份到: {backup_file}")
                return True
            else:
                logger.warning("hosts文件不存在，无法备份")
                return False
                
        except Exception as e:
            logger.error(f"备份hosts文件失败: {e}")
            return False
    
    def create_hosts_template(self) -> str:
        """创建hosts文件模板"""
        template = """# AUTOVPN混合路由hosts文件模板
# 此文件用于分区记录不同类型的纯净IP地址
# 请根据IP类型将记录添加到相应区域

127.0.0.1       localhost
::1             localhost

# ============================================================================
# [DOMESTIC_IPS] - 国内纯净IP区域
# 确定的国内IP地址，这些IP会直接走物理网卡
# 添加规则：
# - 只添加确认是国内的服务器IP
# - 主要是DNS服务器、CDN节点等基础设施
# ============================================================================

# 国内DNS服务器
223.5.5.5       dns.alidns.com
180.76.76.76    dns.baidu.com

# 国内常用服务
# 在这里添加国内服务的IP...

# ============================================================================
# [FOREIGN_VERIFIED_IPS] - 国外验证纯净IP区域  
# 通过隧道验证的国外纯净IP，这些IP会走虚拟网卡
# 添加规则：
# - 必须通过已建立的隧道验证IP有效性
# - 主要用于重要的国外服务
# ============================================================================

# 国外重要服务（示例）
# 104.16.1.1    example.com  # 通过隧道验证的IP
# 172.67.1.1    service.com  # 通过隧道验证的IP

# ============================================================================
# [FOREIGN_CDN_IPS] - 国外CDN IP区域
# 国外CDN网络IP，这些IP会走虚拟网卡
# 添加规则：
# - 主要是Cloudflare、AWS等CDN提供商的IP
# - 可以通过隧道批量验证
# ============================================================================

# Cloudflare CDN
104.16.0.0      cdn.cloudflare.com
172.67.0.0      cdn.cloudflare.com

# ============================================================================
# [SPECIAL_IPS] - 特殊服务IP区域
# 特殊服务IP，根据策略决定路由方式
# 添加规则：
# - DNS服务器、银行、政府网站等
# - 根据安全策略决定路由方式
# ============================================================================

# 特殊DNS服务器
8.8.8.8         dns.google
1.1.1.1         dns.cloudflare

"""
        return template
    
    def generate_routing_commands(self, sections: Dict[str, List[str]]) -> List[str]:
        """生成路由配置命令"""
        commands = []
        
        # 清空现有路由（保留默认路由）
        commands.append("echo 清空现有混合路由规则...")
        
        # 为每个区域生成路由命令
        for section_name, ips in sections.items():
            if not ips:
                continue
                
            section_config = self.config["hosts_sections"][section_name]
            route_policy = section_config["route_policy"]
            metric = section_config["metric"]
            
            if route_policy == "physical":
                gateway = self.config["routing"]["physical_gateway"]
                base_metric = self.config["routing"]["physical_metric"]
            elif route_policy == "virtual":
                gateway = self.config["routing"]["virtual_gateway"]  
                base_metric = self.config["routing"]["virtual_metric"]
            else:  # auto
                # 特殊处理，根据IP类型决定
                continue
            
            commands.append(f"echo 配置 {section_name} 区域路由 ({len(ips)} 个IP)...")
            
            for ip in ips:
                try:
                    # 验证IP地址
                    ipaddress.IPv4Address(ip)
                    
                    # 生成路由命令
                    route_cmd = f"route add {ip} mask 255.255.255.255 {gateway} metric {base_metric + metric}"
                    commands.append(route_cmd)
                    
                except ValueError:
                    logger.warning(f"跳过无效IP: {ip}")
        
        return commands
    
    def apply_routing_config(self, commands: List[str]) -> bool:
        """应用路由配置"""
        try:
            # 创建批处理文件
            batch_file = os.path.join(self.routes_dir, "apply_hybrid_routing.bat")
            
            batch_content = "@echo off\necho 应用混合路由配置...\necho.\n"
            
            for cmd in commands:
                batch_content += f"{cmd}\n"
                batch_content += "if %errorlevel% neq 0 echo 命令执行失败: {}\n".format(cmd)
            
            batch_content += "\necho 路由配置应用完成！\npause"
            
            with open(batch_file, 'w', encoding='utf-8') as f:
                f.write(batch_content)
            
            logger.info(f"路由配置文件已生成: {batch_file}")
            
            # 可选：直接执行路由命令
            logger.info("开始应用路由配置...")
            success_count = 0
            total_count = 0
            
            for cmd in commands:
                if cmd.startswith("route add"):
                    total_count += 1
                    try:
                        result = subprocess.run(
                            cmd,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result.returncode == 0:
                            success_count += 1
                            logger.debug(f"路由添加成功: {cmd}")
                        else:
                            logger.warning(f"路由添加失败: {cmd}, 错误: {result.stderr}")
                            
                    except Exception as e:
                        logger.error(f"执行路由命令失败: {cmd}, 错误: {e}")
            
            logger.info(f"路由配置完成: 成功 {success_count}/{total_count}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"应用路由配置失败: {e}")
            return False
    
    def validate_tunnel_status(self) -> bool:
        """验证隧道状态"""
        try:
            # 检查WireGuard接口是否存在
            result = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and 'WireGuard' in result.stdout:
                logger.info("WireGuard隧道状态正常")
                return True
            else:
                logger.warning("WireGuard隧道未检测到")
                return False
                
        except Exception as e:
            logger.error(f"验证隧道状态失败: {e}")
            return False
    
    def run_hybrid_routing(self, dry_run: bool = False) -> bool:
        """运行混合路由配置"""
        try:
            logger.info("开始混合路由配置...")
            
            # 1. 验证隧道状态
            if self.config["validation"]["enable_tunnel_check"]:
                if not self.validate_tunnel_status():
                    logger.error("隧道验证失败，中止路由配置")
                    return False
            
            # 2. 备份hosts文件
            if self.config["validation"]["backup_before_change"]:
                self.backup_hosts_file()
            
            # 3. 解析hosts文件
            logger.info("解析hosts文件分区...")
            sections = self.parse_hosts_file()
            
            if not sections:
                logger.error("hosts文件解析失败或无有效分区")
                return False
            
            # 4. 生成路由命令
            logger.info("生成路由配置命令...")
            commands = self.generate_routing_commands(sections)
            
            # 5. 保存路由配置报告
            self.save_routing_report(sections, commands)
            
            if dry_run:
                logger.info("干运行模式，仅生成配置文件")
                for cmd in commands:
                    logger.info(f"[DRY-RUN] {cmd}")
                return True
            
            # 6. 应用路由配置
            return self.apply_routing_config(commands)
            
        except Exception as e:
            logger.error(f"混合路由配置失败: {e}")
            return False
    
    def save_routing_report(self, sections: Dict[str, List[str]], commands: List[str]):
        """保存路由配置报告"""
        try:
            report_file = os.path.join(self.routes_dir, f"hybrid_routing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("AUTOVPN混合路由配置报告\n")
                f.write("=" * 50 + "\n\n")
                
                f.write("配置时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
                
                f.write("IP地址分区统计:\n")
                total_ips = 0
                for section_name, ips in sections.items():
                    total_ips += len(ips)
                    route_policy = self.config["hosts_sections"][section_name]["route_policy"]
                    f.write(f"  {section_name}: {len(ips)} 个IP -> {route_policy}\n")
                f.write(f"总计: {total_ips} 个IP地址\n\n")
                
                f.write("路由命令列表:\n")
                for i, cmd in enumerate(commands, 1):
                    f.write(f"{i:3d}. {cmd}\n")
                
                f.write(f"\n配置文件路径:\n")
                f.write(f"  hosts文件: {self.hosts_file}\n")
                f.write(f"  配置目录: {self.routes_dir}\n")
                f.write(f"  备份目录: {self.backup_dir}\n")
            
            logger.info(f"路由配置报告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"保存路由报告失败: {e}")


def main():
    """主函数"""
    router = HybridHostsRouter()
    
    # 检查是否需要创建模板
    if not os.path.exists(router.hosts_file):
        logger.info("hosts文件不存在，创建模板...")
        template = router.create_hosts_template()
        print("\n=== hosts文件模板 ===")
        print(template)
        
        response = input("\n是否创建hosts文件? (y/n): ")
        if response.lower() == 'y':
            try:
                with open(router.hosts_file, 'w', encoding='utf-8') as f:
                    f.write(template)
                logger.info("hosts文件模板已创建")
            except Exception as e:
                logger.error(f"创建hosts文件失败: {e}")
                return
    
    # 运行混合路由配置
    dry_run = input("\n是否使用干运行模式? (y/n): ").lower() == 'y'
    
    if router.run_hybrid_routing(dry_run=dry_run):
        logger.info("混合路由配置成功完成！")
    else:
        logger.error("混合路由配置失败！")


if __name__ == "__main__":
    main()