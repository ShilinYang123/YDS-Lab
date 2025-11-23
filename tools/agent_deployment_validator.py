#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS AI公司智能体部署验证脚本
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
        logging.FileHandler('agent_deployment_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentDeploymentValidator:
    """智能体部署验证器"""
    
    def __init__(self, base_path: str = "s:/YDS-Lab"):
        self.base_path = Path(base_path)
        self.agents_config_path = self.base_path / "config" / "agents_deployment_config.yaml"
        self.agents_dir = self.base_path / "01-struc" / "Agents"
        self.validation_results = {}
        
    def load_agents_config(self) -> Dict:
        """加载智能体配置"""
        try:
            with open(self.agents_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载智能体配置失败: {e}")
            return {}
    
    def validate_agent_structure(self, agent_id: str, agent_config: Dict) -> bool:
        """验证智能体目录结构"""
        agent_dir = self.agents_dir / agent_config.get('directory', '')
        
        if not agent_dir.exists():
            logger.error(f"智能体目录不存在: {agent_dir}")
            return False
            
        # 检查必需文件
        required_files = [
            "role.meta.json",
            "define.py",
            "说明.md"
        ]
        
        missing_files = []
        for file in required_files:
            file_path = agent_dir / file
            if not file_path.exists():
                missing_files.append(file)
                
        if missing_files:
            logger.error(f"智能体 {agent_id} 缺少必需文件: {missing_files}")
            return False
            
        return True
    
    def validate_agent_permissions(self, agent_id: str, agent_config: Dict) -> bool:
        """验证智能体权限配置"""
        permissions = agent_config.get('permissions', [])
        
        # 检查权限配置是否合理
        if not permissions:
            logger.warning(f"智能体 {agent_id} 没有配置权限")
            return False
            
        # 检查关键权限
        critical_permissions = ['document_access', 'data_read', 'system_access']
        has_critical = any(perm in ' '.join(permissions) for perm in critical_permissions)
        
        if not has_critical:
            logger.warning(f"智能体 {agent_id} 缺少关键权限配置")
            return False
            
        return True
    
    def validate_agent_tools(self, agent_id: str, agent_config: Dict) -> bool:
        """验证智能体工具配置"""
        tools = agent_config.get('tools', [])
        
        if not tools:
            logger.warning(f"智能体 {agent_id} 没有配置工具")
            return False
            
        # 检查工具配置是否与角色匹配
        role_type = agent_config.get('role_type', '')
        expected_tools = self.get_expected_tools(role_type)
        
        if expected_tools:
            missing_tools = set(expected_tools) - set(tools)
            if missing_tools:
                logger.warning(f"智能体 {agent_id} 缺少期望的工具: {missing_tools}")
                
        return True
    
    def get_expected_tools(self, role_type: str) -> List[str]:
        """获取角色类型期望的工具"""
        tool_mapping = {
            'leadership': ['decision_support', 'strategic_analysis'],
            'department_head': ['management_tools', 'coordination_tools'],
            'technical_support': ['technical_tools', 'monitoring_tools'],
            'governance': ['compliance_tools', 'audit_tools']
        }
        return tool_mapping.get(role_type, [])
    
    def validate_collaboration_setup(self, config: Dict) -> bool:
        """验证协作配置"""
        collaboration = config.get('collaboration', {})
        
        # 检查消息模型
        message_models = collaboration.get('message_models', {})
        required_models = ['voice', 'stream', 'docs', 'vote']
        
        for model in required_models:
            if model not in message_models:
                logger.error(f"缺少消息模型配置: {model}")
                return False
                
        # 检查工作流配置
        workflows = collaboration.get('workflows', {})
        required_workflows = ['daily_operations', 'project_development', 'emergency_response']
        
        for workflow in required_workflows:
            if workflow not in workflows:
                logger.error(f"缺少工作流配置: {workflow}")
                return False
                
        return True
    
    def validate_system_configuration(self, config: Dict) -> bool:
        """验证系统配置"""
        system_config = config.get('system', {})
        
        # 检查部署信息
        deployment = system_config.get('deployment', {})
        required_fields = ['version', 'date', 'environment', 'location']
        
        for field in required_fields:
            if field not in deployment:
                logger.error(f"系统配置缺少必要字段: {field}")
                return False
                
        # 检查安全配置
        security = system_config.get('security', {})
        if not security.get('rbac_enabled', False):
            logger.error("RBAC权限控制未启用")
            return False
            
        if not security.get('audit_logging', False):
            logger.error("审计日志未启用")
            return False
            
        return True
    
    def run_full_validation(self) -> Dict:
        """运行完整的部署验证"""
        logger.info("开始智能体部署验证...")
        
        config = self.load_agents_config()
        if not config:
            logger.error("无法加载智能体配置")
            return {'status': 'failed', 'error': '配置加载失败'}
            
        results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'agents': {},
            'collaboration': {},
            'system': {},
            'summary': {}
        }
        
        # 验证智能体
        agents = config.get('agents', [])
        total_agents = len(agents)
        valid_agents = 0
        
        for agent in agents:
            agent_id = agent.get('id', '')
            if not agent_id:
                continue
                
            agent_results = {
                'structure': self.validate_agent_structure(agent_id, agent),
                'permissions': self.validate_agent_permissions(agent_id, agent),
                'tools': self.validate_agent_tools(agent_id, agent),
                'overall': True
            }
            
            # 总体评估
            agent_results['overall'] = all([
                agent_results['structure'],
                agent_results['permissions'],
                agent_results['tools']
            ])
            
            if agent_results['overall']:
                valid_agents += 1
                
            results['agents'][agent_id] = agent_results
            
        # 验证协作配置
        collaboration_valid = self.validate_collaboration_setup(config)
        results['collaboration'] = {
            'valid': collaboration_valid,
            'message_models': list(config.get('collaboration', {}).get('message_models', {}).keys()),
            'workflows': list(config.get('collaboration', {}).get('workflows', {}).keys())
        }
        
        # 验证系统配置
        system_valid = self.validate_system_configuration(config)
        results['system'] = {
            'valid': system_valid,
            'deployment': config.get('system', {}).get('deployment', {}),
            'security': config.get('system', {}).get('security', {})
        }
        
        # 生成摘要
        results['summary'] = {
            'total_agents': total_agents,
            'valid_agents': valid_agents,
            'success_rate': f"{(valid_agents/total_agents*100):.1f}%" if total_agents > 0 else "0%",
            'collaboration_status': 'valid' if collaboration_valid else 'invalid',
            'system_status': 'valid' if system_valid else 'invalid',
            'overall_status': 'success' if valid_agents == total_agents and collaboration_valid and system_valid else 'warning'
        }
        
        return results
    
    def generate_validation_report(self, results: Dict) -> str:
        """生成验证报告"""
        report = f"""
# YDS AI公司智能体部署验证报告
生成时间: {results['timestamp']}

## 部署摘要
- **总体状态**: {results['summary']['overall_status'].upper()}
- **智能体总数**: {results['summary']['total_agents']}
- **有效智能体**: {results['summary']['valid_agents']}
- **成功率**: {results['summary']['success_rate']}
- **协作配置**: {results['summary']['collaboration_status']}
- **系统配置**: {results['summary']['system_status']}

## 智能体验证详情
"""
        
        for agent_id, agent_results in results['agents'].items():
            status_icon = "✅" if agent_results['overall'] else "❌"
            report += f"""
### {agent_id} {status_icon}
- 结构验证: {"✅" if agent_results['structure'] else "❌"}
- 权限验证: {"✅" if agent_results['permissions'] else "❌"}
- 工具验证: {"✅" if agent_results['tools'] else "❌"}
"""
        
        report += f"""
## 协作配置
- **状态**: {"✅ 有效" if results['collaboration']['valid'] else "❌ 无效"}
- **消息模型**: {', '.join(results['collaboration']['message_models'])}
- **工作流**: {', '.join(results['collaboration']['workflows'])}

## 系统配置
- **状态**: {"✅ 有效" if results['system']['valid'] else "❌ 无效"}
- **部署版本**: {results['system']['deployment'].get('version', 'N/A')}
- **部署环境**: {results['system']['deployment'].get('environment', 'N/A')}
- **RBAC启用**: {"✅" if results['system']['security'].get('rbac_enabled') else "❌"}
- **审计日志**: {"✅" if results['system']['security'].get('audit_logging') else "❌"}

## 建议措施
"""
        
        if results['summary']['overall_status'] == 'success':
            report += "✅ 所有智能体配置验证通过，系统可以正常启动。\n"
        else:
            report += "⚠️ 发现配置问题，建议修复后再进行部署。\n"
            
        return report

def main():
    """主函数"""
    validator = AgentDeploymentValidator()
    
    # 运行验证
    results = validator.run_full_validation()
    
    # 生成报告
    report = validator.generate_validation_report(results)
    
    # 保存结果
    with open('agent_deployment_validation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    with open('agent_deployment_validation_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info("智能体部署验证完成")
    logger.info(f"验证结果已保存到: agent_deployment_validation_results.json")
    logger.info(f"验证报告已保存到: agent_deployment_validation_report.md")
    
    return results

if __name__ == "__main__":
    main()