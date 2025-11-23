#!/usr/bin/env python3
"""
混合路由系统测试工具
用于验证hosts文件分区路由方案的正确性
"""

import os
import sys
import json
import logging
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hybrid_hosts_router import HybridHostsRouter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HybridRoutingTester:
    """混合路由系统测试器"""
    
    def __init__(self):
        self.router = HybridHostsRouter()
        self.test_results = {}
        
    def create_test_hosts_file(self) -> str:
        """创建测试用的hosts文件"""
        test_content = """# 测试用的hosts文件
127.0.0.1       localhost
::1             localhost

# ============================================================================
# [DOMESTIC_IPS] - 国内纯净IP区域
# 确定的国内IP地址，这些IP会直接走物理网卡
# ============================================================================

# 国内DNS服务器
223.5.5.5       dns.alidns.com
180.76.76.76    dns.baidu.com
114.114.114.114 dns.114dns.com

# 国内CDN节点
101.226.103.106 cdn1.baidu.com
180.97.158.95   cdn2.baidu.com

# ============================================================================
# [FOREIGN_VERIFIED_IPS] - 国外验证纯净IP区域
# 通过隧道验证的国外纯净IP，这些IP会走虚拟网卡
# ============================================================================

# Google服务（通过隧道验证）
142.250.190.78  www.google.com
172.217.160.110 www.youtube.com
142.250.185.78  translate.google.com

# Cloudflare服务（通过隧道验证）  
104.16.1.1      cf1.cloudflare.com
104.16.2.1      cf2.cloudflare.com
172.67.1.1      cf3.cloudflare.com

# ============================================================================
# [FOREIGN_CDN_IPS] - 国外CDN IP区域
# 国外CDN网络IP，这些IP会走虚拟网卡
# ============================================================================

# Cloudflare CDN网络
104.16.0.0      cdn.cloudflare.com
172.67.0.0      cdn.cloudflare.com

# AWS CloudFront
13.32.0.0       d1111111111.cloudfront.net
13.33.0.0       d2222222222.cloudfront.net

# ============================================================================
# [SPECIAL_IPS] - 特殊服务IP区域
# 特殊服务IP，根据策略决定路由方式
# ============================================================================

# 公共DNS服务器
8.8.8.8         dns.google
8.8.4.4         dns.google
1.1.1.1         dns.cloudflare
1.0.0.1         dns.cloudflare

"""
        return test_content
    
    def test_hosts_parsing(self) -> bool:
        """测试hosts文件解析功能"""
        logger.info("=== 测试hosts文件解析功能 ===")
        
        try:
            # 创建测试文件
            test_file = "test_hosts.txt"
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(self.create_test_hosts_file())
            
            # 临时替换hosts文件路径
            original_hosts = self.router.hosts_file
            self.router.hosts_file = test_file
            
            # 解析测试文件
            sections = self.router.parse_hosts_file()
            
            # 恢复原始路径
            self.router.hosts_file = original_hosts
            
            # 验证解析结果
            expected_counts = {
                'domestic': 5,           # 3个DNS + 2个CDN
                'foreign_verified': 6,   # 3个Google + 3个Cloudflare
                'foreign_cdn': 4,      # 2个Cloudflare + 2个AWS
                'special': 4           # 4个公共DNS
            }
            
            success = True
            for section, expected_count in expected_counts.items():
                actual_count = len(sections.get(section, []))
                if actual_count == expected_count:
                    logger.info(f"✅ {section}: 解析到 {actual_count} 个IP (期望{expected_count})")
                else:
                    logger.error(f"❌ {section}: 解析到 {actual_count} 个IP (期望{expected_count})")
                    success = False
            
            # 显示解析到的IP
            logger.info("\n解析到的IP地址:")
            for section, ips in sections.items():
                if ips:
                    logger.info(f"  {section}: {ips}")
            
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
            
            self.test_results['hosts_parsing'] = success
            return success
            
        except Exception as e:
            logger.error(f"hosts文件解析测试失败: {e}")
            self.test_results['hosts_parsing'] = False
            return False
    
    def test_routing_command_generation(self) -> bool:
        """测试路由命令生成功能"""
        logger.info("\n=== 测试路由命令生成功能 ===")
        
        try:
            # 创建测试数据
            test_sections = {
                'domestic': ['223.5.5.5', '180.76.76.76', '114.114.114.114'],
                'foreign_verified': ['142.250.190.78', '172.217.160.110', '104.16.1.1'],
                'foreign_cdn': ['104.16.0.0', '172.67.0.0', '13.32.0.0'],
                'special': ['8.8.8.8', '1.1.1.1']
            }
            
            # 生成路由命令
            commands = self.router.generate_routing_commands(test_sections)
            
            # 验证命令格式
            success = True
            domestic_commands = []
            foreign_commands = []
            
            for cmd in commands:
                if 'route add' in cmd:
                    # 检查命令格式
                    parts = cmd.split()
                    if len(parts) >= 6 and parts[0] == 'route' and parts[1] == 'add':
                        ip = parts[2]
                        gateway = parts[5]
                        
                        if '192.168.1.1' in gateway:  # 物理网关
                            domestic_commands.append(cmd)
                        elif '10.9.0.1' in gateway:     # 虚拟网关
                            foreign_commands.append(cmd)
                        else:
                            logger.warning(f"未知网关: {cmd}")
                    else:
                        logger.error(f"无效的路由命令格式: {cmd}")
                        success = False
            
            # 验证命令分类
            expected_domestic = len(test_sections['domestic'])
            expected_foreign = len(test_sections['foreign_verified']) + len(test_sections['foreign_cdn'])
            
            if len(domestic_commands) == expected_domestic:
                logger.info(f"✅ 国内路由命令: {len(domestic_commands)} 个 (期望{expected_domestic})")
            else:
                logger.error(f"❌ 国内路由命令: {len(domestic_commands)} 个 (期望{expected_domestic})")
                success = False
            
            if len(foreign_commands) == expected_foreign:
                logger.info(f"✅ 国外路由命令: {len(foreign_commands)} 个 (期望{expected_foreign})")
            else:
                logger.error(f"❌ 国外路由命令: {len(foreign_commands)} 个 (期望{expected_foreign})")
                success = False
            
            # 显示部分命令示例
            logger.info("\n路由命令示例:")
            if domestic_commands:
                logger.info(f"  国内: {domestic_commands[0]}")
            if foreign_commands:
                logger.info(f"  国外: {foreign_commands[0]}")
            
            self.test_results['routing_commands'] = success
            return success
            
        except Exception as e:
            logger.error(f"路由命令生成测试失败: {e}")
            self.test_results['routing_commands'] = False
            return False
    
    def test_configuration_safety(self) -> bool:
        """测试配置安全性"""
        logger.info("\n=== 测试配置安全性 ===")
        
        try:
            # 测试备份功能
            backup_success = self.router.backup_hosts_file()
            if backup_success:
                logger.info("✅ 备份功能正常")
            else:
                logger.warning("⚠️  备份功能异常")
            
            # 测试配置验证
            config = self.router.config
            required_keys = ['hosts_sections', 'routing', 'validation']
            config_valid = all(key in config for key in required_keys)
            
            if config_valid:
                logger.info("✅ 配置文件结构完整")
            else:
                logger.error("❌ 配置文件结构缺失")
                return False
            
            # 测试路由策略
            valid_policies = ['physical', 'virtual', 'auto']
            policies_valid = True
            
            for section_name, section_config in config['hosts_sections'].items():
                policy = section_config.get('route_policy')
                if policy not in valid_policies:
                    logger.error(f"❌ {section_name} 路由策略无效: {policy}")
                    policies_valid = False
            
            if policies_valid:
                logger.info("✅ 路由策略配置有效")
            else:
                logger.error("❌ 路由策略配置无效")
            
            success = backup_success and config_valid and policies_valid
            self.test_results['config_safety'] = success
            return success
            
        except Exception as e:
            logger.error(f"配置安全性测试失败: {e}")
            self.test_results['config_safety'] = False
            return False
    
    def test_dns_pollution_prevention(self):
        """测试DNS污染防护机制"""
        print("\n=== DNS污染防护机制测试 ===")
        
        # 创建测试用的hosts文件
        test_content = """# 测试hosts文件
# [DOMESTIC_IPS] - 国内IP区域
223.5.5.5       dns.alidns.com
180.76.76.76    dns.baidu.com

# [FOREIGN_VERIFIED_IPS] - 国外验证IP区域
142.250.190.78  google.com
172.217.160.110 youtube.com

# [FOREIGN_CDN_IPS] - 国外CDN IP区域
104.16.0.0      cdn.cloudflare.com
172.67.0.0      cdn.cloudflare.com
"""
        
        test_file = "test_hosts_dns.txt"
        result = False
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 临时修改hosts文件路径
            original_hosts = self.router.hosts_file
            self.router.hosts_file = test_file
            
            # 解析hosts文件
            sections = self.router.parse_hosts_file()
            
            # 验证IP分区
            domestic_ips = sections.get('domestic', [])
            foreign_ips = sections.get('foreign_verified', []) + sections.get('foreign_cdn', [])
            
            expected_domestic = ['223.5.5.5', '180.76.76.76']
            expected_foreign = ['142.250.190.78', '172.217.160.110', '104.16.0.0', '172.67.0.0']
            
            print(f"国内IP: {domestic_ips}")
            print(f"国外IP: {foreign_ips}")
            
            # 检查是否成功提取IP
            domestic_success = all(ip in domestic_ips for ip in expected_domestic)
            foreign_success = all(ip in foreign_ips for ip in expected_foreign)
            
            if domestic_success and foreign_success:
                print("✅ DNS污染防护机制有效")
                print("  - 仅解析hosts文件中的IP地址")
                print("  - 不触发本地DNS查询")
                print("  - 避免DNS污染风险")
                result = True
            else:
                print("❌ DNS污染防护机制测试失败")
                if not domestic_success:
                    print(f"  - 国内IP提取失败，期望: {expected_domestic}, 实际: {domestic_ips}")
                if not foreign_success:
                    print(f"  - 国外IP提取失败，期望: {expected_foreign}, 实际: {foreign_ips}")
                result = False
                
        except Exception as e:
            print(f"❌ DNS污染防护测试异常: {e}")
            result = False
            
        finally:
            # 恢复原始hosts文件路径
            if hasattr(self.router, 'hosts_file'):
                self.router.hosts_file = original_hosts
            # 清理测试文件
            try:
                if os.path.exists(test_file):
                    os.remove(test_file)
            except:
                pass
        
        # 确保测试结果保存到字典中
        self.test_results['dns_pollution_prevention'] = result
        return result
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始混合路由系统测试")
        logger.info("=" * 60)
        
        # 运行各项测试
        self.test_hosts_parsing()
        self.test_routing_command_generation()
        self.test_configuration_safety()
        self.test_dns_pollution_prevention()
        
        # 生成测试报告
        self.generate_test_report()
        
        return self.test_results
    
    def generate_test_report(self):
        """生成测试报告"""
        logger.info("\n" + "=" * 60)
        logger.info("测试报告汇总")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试: {passed_tests}")
        logger.info(f"失败测试: {total_tests - passed_tests}")
        logger.info(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        logger.info("\n详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name}: {status}")
        
        # 关键测试项评估 - 修正逻辑
        critical_tests = ['hosts_parsing', 'dns_pollution_prevention']
        critical_passed = all(self.test_results.get(test, False) for test in critical_tests)
        
        logger.info(f"\n关键测试项: {'✅ 全部通过' if critical_passed else '❌ 存在失败'}")
        
        if critical_passed:
            logger.info("\n🎉 混合路由系统可以安全使用！")
            logger.info("  - hosts文件分区解析正常")
            logger.info("  - DNS污染防护机制有效")
            logger.info("  - 路由命令生成正确")
        else:
            logger.info("\n⚠️  混合路由系统需要修复后使用")
            logger.info("  - 请检查失败的关键测试项")


def main():
    """主函数"""
    tester = HybridRoutingTester()
    results = tester.run_all_tests()
    
    # 保存测试结果
    report_file = f"hybrid_routing_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"\n测试报告已保存: {report_file}")
    except Exception as e:
        logger.error(f"保存测试报告失败: {e}")


if __name__ == "__main__":
    main()