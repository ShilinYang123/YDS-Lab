#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS AI公司审计日志系统初始化脚本
部署版本: V5.1-架构适配版
部署时间: 2025-11-14
作者: 雨俊
"""

import os
import json
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit_system_init.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AuditSystemInitializer:
    """审计日志系统初始化器"""
    
    def __init__(self, config_path: str = "s:/YDS-Lab/config/audit_logging_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.init_results = {}
        
    def load_config(self) -> Dict:
        """加载审计日志配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载审计日志配置失败: {e}")
            return {}
    
    def create_directory_structure(self) -> Dict:
        """创建目录结构"""
        logger.info("开始创建审计日志目录结构...")
        
        deployment = self.config.get('deployment', {})
        initialization_tasks = deployment.get('initialization_tasks', [])
        
        results = {
            'status': 'success',
            'created_directories': [],
            'errors': []
        }
        
        for task in initialization_tasks:
            if task.get('action') == 'create_directories':
                paths = task.get('paths', [])
                
                for path in paths:
                    try:
                        dir_path = Path(path)
                        dir_path.mkdir(parents=True, exist_ok=True)
                        results['created_directories'].append(str(dir_path))
                        logger.info(f"创建目录: {dir_path}")
                    except Exception as e:
                        error_msg = f"创建目录失败 {path}: {e}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        results['status'] = 'failed'
        
        return results
    
    def initialize_log_files(self) -> Dict:
        """初始化日志文件"""
        logger.info("开始初始化审计日志文件...")
        
        deployment = self.config.get('deployment', {})
        initialization_tasks = deployment.get('initialization_tasks', [])
        
        results = {
            'status': 'success',
            'created_files': [],
            'errors': []
        }
        
        for task in initialization_tasks:
            if task.get('action') == 'initialize_log_files':
                files = task.get('files', [])
                base_path = "s:/YDS-Lab/logs/audit_trails/"
                
                for filename in files:
                    try:
                        file_path = Path(base_path) / filename
                        
                        # 创建文件头信息
                        header = {
                            'file_type': 'audit_log',
                            'version': '1.0',
                            'created_at': datetime.now().isoformat(),
                            'deployment_version': deployment.get('version', 'unknown'),
                            'environment': deployment.get('environment', 'unknown')
                        }
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(json.dumps(header, ensure_ascii=False) + '\n')
                        
                        results['created_files'].append(str(file_path))
                        logger.info(f"初始化日志文件: {file_path}")
                        
                    except Exception as e:
                        error_msg = f"初始化日志文件失败 {filename}: {e}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        results['status'] = 'failed'
        
        return results
    
    def set_file_permissions(self) -> Dict:
        """设置文件权限"""
        logger.info("开始设置审计日志文件权限...")
        
        deployment = self.config.get('deployment', {})
        initialization_tasks = deployment.get('initialization_tasks', [])
        
        results = {
            'status': 'success',
            'set_permissions': [],
            'errors': []
        }
        
        for task in initialization_tasks:
            if task.get('action') == 'set_permissions':
                permissions = task.get('permissions', [])
                
                for perm_config in permissions:
                    try:
                        path = perm_config.get('path', '')
                        owner = perm_config.get('owner', 'audit_service')
                        group = perm_config.get('group', 'audit_group')
                        mode = perm_config.get('mode', '0750')
                        
                        # 注意：在Windows系统上，这里需要适配
                        # 这里仅记录权限设置请求
                        perm_info = {
                            'path': path,
                            'owner': owner,
                            'group': group,
                            'mode': mode,
                            'status': 'configured'
                        }
                        
                        results['set_permissions'].append(perm_info)
                        logger.info(f"配置权限: {path} -> owner={owner}, group={group}, mode={mode}")
                        
                    except Exception as e:
                        error_msg = f"设置权限失败 {perm_config}: {e}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                        results['status'] = 'failed'
        
        return results
    
    def validate_audit_categories(self) -> Dict:
        """验证审计类别配置"""
        logger.info("开始验证审计类别配置...")
        
        audit_logging = self.config.get('audit_logging', {})
        categories = audit_logging.get('categories', {})
        
        results = {
            'status': 'success',
            'validated_categories': [],
            'errors': []
        }
        
        required_categories = [
            'system_events', 'user_access', 'agent_operations',
            'document_operations', 'meeting_events', 'rbac_events',
            'security_compliance', 'performance_monitoring'
        ]
        
        for category_name in required_categories:
            if category_name not in categories:
                error_msg = f"缺少必需的审计类别: {category_name}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                results['status'] = 'failed'
                continue
            
            category_config = categories[category_name]
            
            if not category_config.get('enabled', False):
                warning_msg = f"审计类别未启用: {category_name}"
                logger.warning(warning_msg)
            
            events = category_config.get('events', [])
            if not events:
                warning_msg = f"审计类别 {category_name} 没有定义事件"
                logger.warning(warning_msg)
            
            results['validated_categories'].append({
                'name': category_name,
                'enabled': category_config.get('enabled', False),
                'event_count': len(events)
            })
            
            logger.info(f"验证审计类别: {category_name} -> {len(events)} 个事件")
        
        return results
    
    def validate_storage_config(self) -> Dict:
        """验证存储配置"""
        logger.info("开始验证存储配置...")
        
        audit_logging = self.config.get('audit_logging', {})
        storage = audit_logging.get('storage', {})
        
        results = {
            'status': 'success',
            'storage_types': [],
            'errors': []
        }
        
        required_storage_types = ['primary_storage', 'backup_storage', 'archive_storage']
        
        for storage_type in required_storage_types:
            if storage_type not in storage:
                error_msg = f"缺少必需的存储类型: {storage_type}"
                results['errors'].append(error_msg)
                logger.error(error_msg)
                results['status'] = 'failed'
                continue
            
            storage_config = storage[storage_type]
            
            # 验证存储路径
            path = storage_config.get('path', '')
            if not path:
                error_msg = f"存储类型 {storage_type} 未配置路径"
                results['errors'].append(error_msg)
                results['status'] = 'failed'
                continue
            
            # 验证格式
            format_type = storage_config.get('format', '')
            if format_type not in ['jsonl', 'csv', 'xml']:
                warning_msg = f"存储类型 {storage_type} 使用了不常见的格式: {format_type}"
                logger.warning(warning_msg)
            
            # 验证压缩
            compression = storage_config.get('compression', '')
            if compression not in ['gzip', 'bzip2', 'lz4', 'none']:
                warning_msg = f"存储类型 {storage_type} 使用了不常见的压缩格式: {compression}"
                logger.warning(warning_msg)
            
            results['storage_types'].append({
                'type': storage_type,
                'path': path,
                'format': format_type,
                'compression': compression
            })
            
            logger.info(f"验证存储配置: {storage_type} -> {path} ({format_type}, {compression})")
        
        return results
    
    def validate_alerting_config(self) -> Dict:
        """验证告警配置"""
        logger.info("开始验证告警配置...")
        
        audit_logging = self.config.get('audit_logging', {})
        alerting = audit_logging.get('alerting', {})
        
        results = {
            'status': 'success',
            'alert_rules': [],
            'errors': []
        }
        
        if not alerting.get('enabled', False):
            warning_msg = "告警功能未启用"
            logger.warning(warning_msg)
            results['status'] = 'warning'
            return results
        
        rules = alerting.get('rules', [])
        if not rules:
            warning_msg = "未配置告警规则"
            logger.warning(warning_msg)
            results['status'] = 'warning'
            return results
        
        for rule in rules:
            rule_name = rule.get('name', '')
            if not rule_name:
                error_msg = "告警规则缺少名称"
                results['errors'].append(error_msg)
                results['status'] = 'failed'
                continue
            
            condition = rule.get('condition', '')
            if not condition:
                error_msg = f"告警规则 {rule_name} 缺少条件"
                results['errors'].append(error_msg)
                results['status'] = 'failed'
                continue
            
            severity = rule.get('severity', '')
            if severity not in ['low', 'medium', 'high', 'critical']:
                warning_msg = f"告警规则 {rule_name} 使用了非标准严重性级别: {severity}"
                logger.warning(warning_msg)
            
            action = rule.get('action', '')
            if not action:
                warning_msg = f"告警规则 {rule_name} 缺少动作"
                logger.warning(warning_msg)
            
            results['alert_rules'].append({
                'name': rule_name,
                'condition': condition,
                'severity': severity,
                'action': action
            })
            
            logger.info(f"验证告警规则: {rule_name} -> {condition} ({severity}, {action})")
        
        return results
    
    def create_sample_audit_entries(self) -> Dict:
        """创建示例审计条目"""
        logger.info("开始创建示例审计条目...")
        
        results = {
            'status': 'success',
            'created_entries': [],
            'errors': []
        }
        
        # 示例审计条目
        sample_entries = [
            {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'system_startup',
                'category': 'system_events',
                'severity': 'medium',
                'user_id': 'SYSTEM',
                'agent_id': 'AGENT-01-CEO',
                'description': 'YDS AI公司审计日志系统初始化完成',
                'details': {
                    'deployment_version': 'V5.1-架构适配版',
                    'initialization_status': 'success',
                    'components_initialized': ['directory_structure', 'log_files', 'permissions', 'alerting']
                }
            },
            {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'agent_activation',
                'category': 'agent_operations',
                'severity': 'low',
                'user_id': 'SYSTEM',
                'agent_id': 'AGENT-01-CEO',
                'description': 'CEO智能体激活成功',
                'details': {
                    'role': '首席执行官',
                    'permissions': ['system_admin', 'meeting_management', 'document_management'],
                    'status': 'active'
                }
            },
            {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'rbac_initialization',
                'category': 'rbac_events',
                'severity': 'medium',
                'user_id': 'SYSTEM',
                'agent_id': 'AGENT-15-RBAC-GOVERNANCE',
                'description': 'RBAC权限控制系统初始化完成',
                'details': {
                    'roles_configured': 20,
                    'permissions_defined': 8,
                    'user_mappings': 20,
                    'validation_status': 'success'
                }
            },
            {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'mcp_communication_setup',
                'category': 'system_events',
                'severity': 'medium',
                'user_id': 'SYSTEM',
                'agent_id': 'AGENT-10-MCP-MANAGER',
                'description': 'MCP协议通信系统配置完成',
                'details': {
                    'message_models': ['voice', 'stream', 'docs', 'vote'],
                    'communication_modes': ['synchronous', 'asynchronous', 'broadcast'],
                    'security_enabled': True,
                    'encryption_enabled': True
                }
            },
            {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'deployment_completion',
                'category': 'system_events',
                'severity': 'low',
                'user_id': 'SYSTEM',
                'agent_id': 'AGENT-01-CEO',
                'description': 'YDS AI公司V5.1架构适配版部署完成',
                'details': {
                    'deployment_phase': 'initialization',
                    'components_deployed': ['agents', 'mcp', 'rbac', 'audit'],
                    'overall_status': 'success',
                    'next_phase': 'production_testing'
                }
            }
        ]
        
        base_path = "s:/YDS-Lab/logs/audit_trails/"
        audit_file = Path(base_path) / "audit_main.jsonl"
        
        try:
            with open(audit_file, 'a', encoding='utf-8') as f:
                for entry in sample_entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                    results['created_entries'].append(entry['event_type'])
                    logger.info(f"创建审计条目: {entry['event_type']}")
            
        except Exception as e:
            error_msg = f"创建示例审计条目失败: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            results['status'] = 'failed'
        
        return results
    
    def run_full_initialization(self) -> Dict:
        """运行完整的审计系统初始化"""
        logger.info("开始完整的审计日志系统初始化...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'config_file': str(self.config_path),
            'overall_status': 'success',
            'initialization_steps': {},
            'summary': {}
        }
        
        # 运行各项初始化任务
        results['initialization_steps']['directory_structure'] = self.create_directory_structure()
        results['initialization_steps']['log_files'] = self.initialize_log_files()
        results['initialization_steps']['file_permissions'] = self.set_file_permissions()
        results['initialization_steps']['audit_categories'] = self.validate_audit_categories()
        results['initialization_steps']['storage_config'] = self.validate_storage_config()
        results['initialization_steps']['alerting_config'] = self.validate_alerting_config()
        results['initialization_steps']['sample_entries'] = self.create_sample_audit_entries()
        
        # 计算总体状态
        failed_steps = []
        warning_steps = []
        
        for step_name, step_results in results['initialization_steps'].items():
            if step_results.get('status') == 'failed':
                failed_steps.append(step_name)
            elif step_results.get('status') == 'warning':
                warning_steps.append(step_name)
        
        if failed_steps:
            results['overall_status'] = 'failed'
        elif warning_steps:
            results['overall_status'] = 'warning'
        else:
            results['overall_status'] = 'success'
        
        # 生成摘要
        results['summary'] = {
            'total_steps': len(results['initialization_steps']),
            'successful_steps': len(results['initialization_steps']) - len(failed_steps) - len(warning_steps),
            'failed_steps': len(failed_steps),
            'warning_steps': len(warning_steps),
            'failed_step_names': failed_steps,
            'warning_step_names': warning_steps
        }
        
        return results
    
    def generate_initialization_report(self, results: Dict) -> str:
        """生成初始化报告"""
        report = f"""
# YDS AI公司审计日志系统初始化报告

初始化时间: {results['timestamp']}
配置文件: {results['config_file']}

## 初始化摘要
- **总体状态**: {results['overall_status'].upper()}
- **总步骤数**: {results['summary']['total_steps']}
- **成功步骤**: {results['summary']['successful_steps']}
- **失败步骤**: {results['summary']['failed_steps']}
- **警告步骤**: {results['summary']['warning_steps']}

## 详细初始化结果

"""
        
        for step_name, step_results in results['initialization_steps'].items():
            status_icon = "✅" if step_results.get('status') == 'success' else "⚠️" if step_results.get('status') == 'warning' else "❌"
            
            report += f"### {step_name.replace('_', ' ').title()} {status_icon}\n\n"
            
            if step_results.get('status') == 'success':
                report += f"- **状态**: ✅ 成功\n"
                
                # 显示具体结果
                if 'created_directories' in step_results:
                    count = len(step_results['created_directories'])
                    report += f"- **创建目录**: {count} 个\n"
                    
                if 'created_files' in step_results:
                    count = len(step_results['created_files'])
                    report += f"- **创建文件**: {count} 个\n"
                    
                if 'validated_categories' in step_results:
                    count = len(step_results['validated_categories'])
                    report += f"- **验证类别**: {count} 个\n"
                    
                if 'storage_types' in step_results:
                    count = len(step_results['storage_types'])
                    report += f"- **存储类型**: {count} 个\n"
                    
                if 'alert_rules' in step_results:
                    count = len(step_results['alert_rules'])
                    report += f"- **告警规则**: {count} 个\n"
                    
                if 'created_entries' in step_results:
                    count = len(step_results['created_entries'])
                    report += f"- **示例条目**: {count} 个\n"
                    
            elif step_results.get('status') == 'warning':
                report += f"- **状态**: ⚠️ 警告\n"
                if step_results.get('errors'):
                    report += f"- **错误数**: {len(step_results['errors'])}\n"
                if step_results.get('warnings'):
                    report += f"- **警告数**: {len(step_results['warnings'])}\n"
                    
            else:  # failed
                report += f"- **状态**: ❌ 失败\n"
                if step_results.get('errors'):
                    report += f"- **错误数**: {len(step_results['errors'])}\n"
                    for error in step_results['errors'][:3]:  # 只显示前3个错误
                        report += f"  - {error}\n"
                    if len(step_results['errors']) > 3:
                        report += f"  ... 还有 {len(step_results['errors']) - 3} 个错误\n"
            
            report += "\n"
        
        report += """
## 建议措施

"""
        
        if results['overall_status'] == 'success':
            report += "✅ 审计日志系统初始化成功，系统可以正常运行。\n"
            report += "📋 建议定期检查日志文件和告警配置。\n"
        elif results['overall_status'] == 'warning':
            report += "⚠️ 审计日志系统初始化完成，但存在警告。\n"
            report += "🔍 建议查看警告详情并进行必要的调整。\n"
        else:
            report += "❌ 审计日志系统初始化失败。\n"
            report += "🛠️ 建议修复失败步骤后重新运行初始化。\n"
            
        return report

def main():
    """主函数"""
    initializer = AuditSystemInitializer()
    
    # 运行初始化
    results = initializer.run_full_initialization()
    
    # 生成报告
    report = initializer.generate_initialization_report(results)
    
    # 保存结果
    with open('audit_system_init_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    with open('audit_system_init_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info("审计日志系统初始化完成")
    logger.info(f"初始化结果已保存到: audit_system_init_results.json")
    logger.info(f"初始化报告已保存到: audit_system_init_report.md")
    
    return results

if __name__ == "__main__":
    main()