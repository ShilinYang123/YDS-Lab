#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS AI公司RBAC权限控制验证脚本
部署版本: V5.1-架构适配版
测试时间: 2025-11-14
作者: 雨俊
"""

import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rbac_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RBACValidator:
    """RBAC权限控制验证器"""
    
    def __init__(self, config_path: str = "s:/YDS-Lab/config/rbac_system_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.validation_results = {}
        
    def load_config(self) -> Dict:
        """加载RBAC配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载RBAC配置失败: {e}")
            return {}
    
    def validate_permissions(self) -> Dict:
        """验证权限定义"""
        logger.info("开始验证权限定义...")
        
        permissions = self.config.get('rbac_config', {}).get('permissions', {})
        results = {}
        
        if not permissions:
            logger.error("未找到权限定义")
            return {'status': 'failed', 'error': '权限定义缺失'}
        
        required_permission_fields = ['description', 'actions', 'resources']
        
        for perm_name, perm_config in permissions.items():
            logger.info(f"验证权限: {perm_name}")
            
            # 检查必需字段
            missing_fields = [field for field in required_permission_fields if field not in perm_config]
            
            if missing_fields:
                results[perm_name] = {
                    'status': 'failed',
                    'error': f"缺少必需字段: {missing_fields}",
                    'config': perm_config
                }
                continue
            
            # 验证actions
            actions = perm_config.get('actions', [])
            if not actions or not isinstance(actions, list):
                results[perm_name] = {
                    'status': 'failed',
                    'error': 'actions必须是有效的列表',
                    'config': perm_config
                }
                continue
            
            # 验证resources
            resources = perm_config.get('resources', [])
            if not resources or not isinstance(resources, list):
                results[perm_name] = {
                    'status': 'failed',
                    'error': 'resources必须是有效的列表',
                    'config': perm_config
                }
                continue
            
            results[perm_name] = {
                'status': 'success',
                'message': f"权限定义完整: actions={len(actions)}, resources={len(resources)}",
                'config': perm_config
            }
        
        return results
    
    def validate_roles(self) -> Dict:
        """验证角色定义"""
        logger.info("开始验证角色定义...")
        
        roles = self.config.get('rbac_config', {}).get('roles', {})
        results = {}
        
        if not roles:
            logger.error("未找到角色定义")
            return {'status': 'failed', 'error': '角色定义缺失'}
        
        required_role_fields = ['name', 'display_name', 'description', 'permissions', 'resource_access']
        
        for role_name, role_config in roles.items():
            logger.info(f"验证角色: {role_name}")
            
            # 检查必需字段
            missing_fields = [field for field in required_role_fields if field not in role_config]
            
            if missing_fields:
                results[role_name] = {
                    'status': 'failed',
                    'error': f"缺少必需字段: {missing_fields}",
                    'config': role_config
                }
                continue
            
            # 验证权限列表
            permissions = role_config.get('permissions', [])
            if not permissions or not isinstance(permissions, list):
                results[role_name] = {
                    'status': 'failed',
                    'error': 'permissions必须是有效的列表',
                    'config': role_config
                }
                continue
            
            # 验证资源访问配置
            resource_access = role_config.get('resource_access', {})
            if not resource_access or not isinstance(resource_access, dict):
                results[role_name] = {
                    'status': 'failed',
                    'error': 'resource_access必须是有效的字典',
                    'config': role_config
                }
                continue
            
            # 验证优先级
            priority = role_config.get('priority', 'medium')
            valid_priorities = ['critical', 'high', 'medium', 'low']
            if priority not in valid_priorities:
                results[role_name] = {
                    'status': 'warning',
                    'warning': f"优先级 '{priority}' 不是标准值，应为: {valid_priorities}",
                    'config': role_config
                }
                continue
            
            results[role_name] = {
                'status': 'success',
                'message': f"角色定义完整: permissions={len(permissions)}, priority={priority}",
                'config': role_config
            }
        
        return results
    
    def validate_user_role_mappings(self) -> Dict:
        """验证用户角色映射"""
        logger.info("开始验证用户角色映射...")
        
        user_mappings = self.config.get('user_role_mappings', {})
        results = {}
        
        if not user_mappings:
            logger.error("未找到用户角色映射")
            return {'status': 'failed', 'error': '用户角色映射缺失'}
        
        required_mapping_fields = ['roles', 'effective_date', 'status']
        
        for user_id, mapping_config in user_mappings.items():
            logger.info(f"验证用户角色映射: {user_id}")
            
            # 检查必需字段
            missing_fields = [field for field in required_mapping_fields if field not in mapping_config]
            
            if missing_fields:
                results[user_id] = {
                    'status': 'failed',
                    'error': f"缺少必需字段: {missing_fields}",
                    'config': mapping_config
                }
                continue
            
            # 验证角色列表
            roles = mapping_config.get('roles', [])
            if not roles or not isinstance(roles, list):
                results[user_id] = {
                    'status': 'failed',
                    'error': 'roles必须是有效的列表',
                    'config': mapping_config
                }
                continue
            
            # 验证状态
            status = mapping_config.get('status', 'inactive')
            valid_statuses = ['active', 'inactive', 'suspended', 'standby']
            if status not in valid_statuses:
                results[user_id] = {
                    'status': 'warning',
                    'warning': f"状态 '{status}' 不是标准值，应为: {valid_statuses}",
                    'config': mapping_config
                }
                continue
            
            results[user_id] = {
                'status': 'success',
                'message': f"用户角色映射完整: roles={len(roles)}, status={status}",
                'config': mapping_config
            }
        
        return results
    
    def validate_resource_access_control(self) -> Dict:
        """验证资源访问控制"""
        logger.info("开始验证资源访问控制...")
        
        resource_control = self.config.get('resource_access_control', {})
        results = {}
        
        if not resource_control:
            logger.error("未找到资源访问控制定义")
            return {'status': 'failed', 'error': '资源访问控制缺失'}
        
        required_resource_fields = ['paths', 'access_levels']
        
        for resource_name, resource_config in resource_control.items():
            logger.info(f"验证资源访问控制: {resource_name}")
            
            # 检查必需字段
            missing_fields = [field for field in required_resource_fields if field not in resource_config]
            
            if missing_fields:
                results[resource_name] = {
                    'status': 'failed',
                    'error': f"缺少必需字段: {missing_fields}",
                    'config': resource_config
                }
                continue
            
            # 验证路径
            paths = resource_config.get('paths', [])
            if not paths or not isinstance(paths, list):
                results[resource_name] = {
                    'status': 'failed',
                    'error': 'paths必须是有效的列表',
                    'config': resource_config
                }
                continue
            
            # 验证访问级别
            access_levels = resource_config.get('access_levels', [])
            if not access_levels or not isinstance(access_levels, list):
                results[resource_name] = {
                    'status': 'failed',
                    'error': 'access_levels必须是有效的列表',
                    'config': resource_config
                }
                continue
            
            # 验证路径格式
            invalid_paths = []
            for path in paths:
                if not isinstance(path, str) or not path.strip():
                    invalid_paths.append(path)
            
            if invalid_paths:
                results[resource_name] = {
                    'status': 'warning',
                    'warning': f"发现无效路径: {invalid_paths}",
                    'config': resource_config
                }
                continue
            
            results[resource_name] = {
                'status': 'success',
                'message': f"资源访问控制完整: paths={len(paths)}, access_levels={len(access_levels)}",
                'config': resource_config
            }
        
        return results
    
    def validate_audit_compliance(self) -> Dict:
        """验证审计与合规配置"""
        logger.info("开始验证审计与合规配置...")
        
        audit_config = self.config.get('audit_compliance', {})
        results = {}
        
        if not audit_config:
            logger.error("未找到审计与合规配置")
            return {'status': 'failed', 'error': '审计与合规配置缺失'}
        
        # 验证基本配置
        enabled = audit_config.get('enabled', False)
        log_all_access = audit_config.get('log_all_access', False)
        retention_days = audit_config.get('retention_days', 0)
        
        if not enabled:
            results['basic_config'] = {
                'status': 'warning',
                'warning': '审计与合未启用',
                'config': audit_config
            }
        else:
            results['basic_config'] = {
                'status': 'success',
                'message': f"审计与合规已启用: log_all_access={log_all_access}, retention={retention_days}天",
                'config': audit_config
            }
        
        # 验证合规规则
        compliance_rules = audit_config.get('compliance_rules', [])
        if not compliance_rules:
            results['compliance_rules'] = {
                'status': 'warning',
                'warning': '未配置合规规则',
                'config': audit_config
            }
        else:
            enabled_rules = sum(1 for rule in compliance_rules if rule.get('enabled', False))
            results['compliance_rules'] = {
                'status': 'success',
                'message': f"合规规则配置: 总数={len(compliance_rules)}, 启用={enabled_rules}",
                'config': compliance_rules
            }
        
        return results
    
    def check_permission_consistency(self) -> Dict:
        """检查权限一致性"""
        logger.info("开始检查权限一致性...")
        
        permissions = self.config.get('rbac_config', {}).get('permissions', {})
        roles = self.config.get('rbac_config', {}).get('roles', {})
        
        results = {
            'orphaned_permissions': [],
            'undefined_permissions': [],
            'inconsistent_priorities': []
        }
        
        # 获取所有定义的权限
        defined_permissions = set(permissions.keys())
        
        # 检查角色中使用的权限是否在权限定义中存在
        for role_name, role_config in roles.items():
            role_permissions = role_config.get('permissions', [])
            
            for perm in role_permissions:
                if isinstance(perm, str) and perm not in defined_permissions:
                    results['undefined_permissions'].append({
                        'role': role_name,
                        'permission': perm
                    })
        
        # 检查权限优先级一致性
        valid_priorities = ['critical', 'high', 'medium', 'low']
        for role_name, role_config in roles.items():
            priority = role_config.get('priority', 'medium')
            if priority not in valid_priorities:
                results['inconsistent_priorities'].append({
                    'role': role_name,
                    'priority': priority
                })
        
        # 检查未使用的权限
        used_permissions = set()
        for role_config in roles.values():
            role_permissions = role_config.get('permissions', [])
            for perm in role_permissions:
                if isinstance(perm, str):
                    used_permissions.add(perm)
        
        orphaned_permissions = defined_permissions - used_permissions
        results['orphaned_permissions'] = list(orphaned_permissions)
        
        return results
    
    def run_full_validation(self) -> Dict:
        """运行完整的RBAC验证"""
        logger.info("开始完整的RBAC权限控制验证...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'config_file': str(self.config_path),
            'overall_status': 'success',
            'validations': {},
            'consistency_check': {},
            'summary': {}
        }
        
        # 运行各项验证
        results['validations']['permissions'] = self.validate_permissions()
        results['validations']['roles'] = self.validate_roles()
        results['validations']['user_role_mappings'] = self.validate_user_role_mappings()
        results['validations']['resource_access_control'] = self.validate_resource_access_control()
        results['validations']['audit_compliance'] = self.validate_audit_compliance()
        
        # 运行一致性检查
        results['consistency_check'] = self.check_permission_consistency()
        
        # 计算总体状态
        all_validations_passed = True
        validation_summary = {}
        
        for validation_name, validation_results in results['validations'].items():
            if isinstance(validation_results, dict) and validation_results.get('status') in ['failed', 'error']:
                all_validations_passed = False
            else:
                # 统计成功/失败/警告数量
                success_count = sum(1 for r in validation_results.values() if r.get('status') == 'success')
                failed_count = sum(1 for r in validation_results.values() if r.get('status') in ['failed', 'error'])
                warning_count = sum(1 for r in validation_results.values() if r.get('status') == 'warning')
                
                validation_summary[validation_name] = {
                    'success': success_count,
                    'failed': failed_count,
                    'warning': warning_count,
                    'total': success_count + failed_count + warning_count
                }
        
        results['overall_status'] = 'success' if all_validations_passed else 'warning'
        results['summary'] = validation_summary
        
        return results
    
    def generate_validation_report(self, results: Dict) -> str:
        """生成验证报告"""
        report = f"""
# YDS AI公司RBAC权限控制验证报告

生成时间: {results['timestamp']}
配置文件: {results['config_file']}

## 验证摘要
- **总体状态**: {results['overall_status'].upper()}
- **验证类别**: {len(results['validations'])} 个

## 详细验证结果

"""
        
        for validation_name, validation_results in results['validations'].items():
            report += f"### {validation_name.replace('_', ' ').title()}\n\n"
            
            if isinstance(validation_results, dict) and validation_results.get('status') in ['failed', 'error']:
                report += f"❌ **状态**: 失败\n"
                report += f"- **错误**: {validation_results.get('error', '未知错误')}\n\n"
            else:
                success_count = sum(1 for r in validation_results.values() if r.get('status') == 'success')
                failed_count = sum(1 for r in validation_results.values() if r.get('status') in ['failed', 'error'])
                warning_count = sum(1 for r in validation_results.values() if r.get('status') == 'warning')
                total = len(validation_results)
                
                report += f"- **通过率**: {success_count}/{total} ({success_count/total*100:.1f}%)\n"
                report += f"- **失败**: {failed_count}, **警告**: {warning_count}\n\n"
                
                # 显示详细结果
                for item_name, item_result in validation_results.items():
                    status_icon = "✅" if item_result.get('status') == 'success' else "⚠️" if item_result.get('status') == 'warning' else "❌"
                    report += f"#### {item_name} {status_icon}\n"
                    
                    if item_result.get('status') == 'success':
                        report += f"- **消息**: {item_result.get('message', '无消息')}\n"
                    elif item_result.get('status') == 'warning':
                        report += f"- **警告**: {item_result.get('warning', '无警告消息')}\n"
                    else:
                        report += f"- **错误**: {item_result.get('error', '无错误消息')}\n"
                    
                    report += "\n"
        
        # 一致性检查结果
        report += "### 一致性检查\n\n"
        consistency_results = results['consistency_check']
        
        if consistency_results.get('orphaned_permissions'):
            report += f"⚠️ **孤立权限**: {len(consistency_results['orphaned_permissions'])} 个\n"
            for perm in consistency_results['orphaned_permissions'][:5]:  # 只显示前5个
                report += f"  - {perm}\n"
            if len(consistency_results['orphaned_permissions']) > 5:
                report += f"  ... 还有 {len(consistency_results['orphaned_permissions']) - 5} 个\n"
        else:
            report += "✅ **孤立权限**: 无\n"
        
        if consistency_results.get('undefined_permissions'):
            report += f"❌ **未定义权限**: {len(consistency_results['undefined_permissions'])} 个\n"
            for item in consistency_results['undefined_permissions'][:5]:  # 只显示前5个
                report += f"  - 角色 {item['role']} 使用了未定义权限 {item['permission']}\n"
            if len(consistency_results['undefined_permissions']) > 5:
                report += f"  ... 还有 {len(consistency_results['undefined_permissions']) - 5} 个\n"
        else:
            report += "✅ **未定义权限**: 无\n"
        
        if consistency_results.get('inconsistent_priorities'):
            report += f"⚠️ **不一致优先级**: {len(consistency_results['inconsistent_priorities'])} 个\n"
            for item in consistency_results['inconsistent_priorities'][:5]:  # 只显示前5个
                report += f"  - 角色 {item['role']} 使用了非标准优先级 {item['priority']}\n"
            if len(consistency_results['inconsistent_priorities']) > 5:
                report += f"  ... 还有 {len(consistency_results['inconsistent_priorities']) - 5} 个\n"
        else:
            report += "✅ **不一致优先级**: 无\n"
        
        report += """
## 建议措施

"""
        
        if results['overall_status'] == 'success':
            report += "✅ RBAC权限控制配置验证通过，可以正常启用权限控制。\n"
        else:
            report += "⚠️ 发现配置问题，建议修复后再启用权限控制。\n"
            
        return report

def main():
    """主函数"""
    validator = RBACValidator()
    
    # 运行验证
    results = validator.run_full_validation()
    
    # 生成报告
    report = validator.generate_validation_report(results)
    
    # 保存结果
    with open('rbac_validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    with open('rbac_validation_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info("RBAC权限控制验证完成")
    logger.info(f"验证结果已保存到: rbac_validation_results.json")
    logger.info(f"验证报告已保存到: rbac_validation_report.md")
    
    return results

if __name__ == "__main__":
    main()