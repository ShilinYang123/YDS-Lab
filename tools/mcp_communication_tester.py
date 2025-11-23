#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS AI公司MCP协议通信测试脚本
部署版本: V5.1-架构适配版
测试时间: 2025-11-14
作者: 雨俊
"""

import json
import yaml
import time
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# 配置日志 - 按照三级存储规范：系统维护类日志存储在logs/
project_root = Path(__file__).parent.parent
logs_dir = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'mcp_communication_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """消息类型枚举"""
    VOICE = "voice"
    STREAM = "stream"
    DOCS = "docs"
    VOTE = "vote"

class MessagePriority(Enum):
    """消息优先级枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class MCPMessage:
    """MCP消息数据结构"""
    id: str
    type: MessageType
    sender: str
    recipients: List[str]
    content: Any
    priority: MessagePriority
    timestamp: datetime
    encryption: bool = False
    signature: Optional[str] = None

class MCPCommunicationTester:
    """MCP通信测试器"""
    
    def __init__(self, config_path: str = "s:/YDS-Lab/config/mcp_communication_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.test_results = {}
        
    def load_config(self) -> Dict:
        """加载MCP配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载MCP配置失败: {e}")
            return {}
    
    def test_message_models(self) -> Dict:
        """测试消息模型"""
        logger.info("开始测试消息模型...")
        
        message_models = self.config.get('message_models', {})
        results = {}
        
        for model_name, model_config in message_models.items():
            if not model_config.get('enabled', False):
                logger.warning(f"消息模型 {model_name} 未启用，跳过测试")
                continue
                
            logger.info(f"测试消息模型: {model_name}")
            
            try:
                # 测试基本配置
                required_fields = ['format', 'enabled']
                missing_fields = [field for field in required_fields if field not in model_config]
                
                if missing_fields:
                    results[model_name] = {
                        'status': 'failed',
                        'error': f"缺少必需字段: {missing_fields}",
                        'config': model_config
                    }
                    continue
                
                # 测试特定模型配置
                if model_name == 'voice':
                    voice_fields = ['max_duration', 'sample_rate', 'channels', 'compression']
                    missing_voice_fields = [field for field in voice_fields if field not in model_config]
                    
                    if missing_voice_fields:
                        results[model_name] = {
                            'status': 'warning',
                            'warning': f"缺少语音模型字段: {missing_voice_fields}",
                            'config': model_config
                        }
                    else:
                        results[model_name] = {
                            'status': 'success',
                            'message': '语音模型配置完整',
                            'config': model_config
                        }
                        
                elif model_name == 'stream':
                    stream_fields = ['real_time', 'buffer_size', 'keep_alive', 'heartbeat_interval']
                    missing_stream_fields = [field for field in stream_fields if field not in model_config]
                    
                    if missing_stream_fields:
                        results[model_name] = {
                            'status': 'warning',
                            'warning': f"缺少流模型字段: {missing_stream_fields}",
                            'config': model_config
                        }
                    else:
                        results[model_name] = {
                            'status': 'success',
                            'message': '流模型配置完整',
                            'config': model_config
                        }
                        
                elif model_name == 'docs':
                    docs_fields = ['versioning', 'max_size', 'compression', 'diff_support']
                    missing_docs_fields = [field for field in docs_fields if field not in model_config]
                    
                    if missing_docs_fields:
                        results[model_name] = {
                            'status': 'warning',
                            'warning': f"缺少文档模型字段: {missing_docs_fields}",
                            'config': model_config
                        }
                    else:
                        results[model_name] = {
                            'status': 'success',
                            'message': '文档模型配置完整',
                            'config': model_config
                        }
                        
                elif model_name == 'vote':
                    vote_fields = ['consensus_required', 'timeout', 'quorum_percentage', 'vote_types']
                    missing_vote_fields = [field for field in vote_fields if field not in model_config]
                    
                    if missing_vote_fields:
                        results[model_name] = {
                            'status': 'warning',
                            'warning': f"缺少投票模型字段: {missing_vote_fields}",
                            'config': model_config
                        }
                    else:
                        results[model_name] = {
                            'status': 'success',
                            'message': '投票模型配置完整',
                            'config': model_config
                        }
                        
            except Exception as e:
                results[model_name] = {
                    'status': 'error',
                    'error': str(e),
                    'config': model_config
                }
                
        return results
    
    def test_communication_modes(self) -> Dict:
        """测试通信模式"""
        logger.info("开始测试通信模式...")
        
        comm_modes = self.config.get('mcp_protocol', {}).get('communication_modes', {})
        results = {}
        
        for mode_name, mode_config in comm_modes.items():
            if not mode_config.get('enabled', False):
                logger.warning(f"通信模式 {mode_name} 未启用，跳过测试")
                continue
                
            logger.info(f"测试通信模式: {mode_name}")
            
            try:
                if mode_name == 'synchronous':
                    # 测试同步模式
                    timeout = mode_config.get('timeout', 30)
                    retry_count = mode_config.get('retry_count', 3)
                    
                    results[mode_name] = {
                        'status': 'success',
                        'message': f'同步模式配置: timeout={timeout}s, retry={retry_count}',
                        'config': mode_config
                    }
                    
                elif mode_name == 'asynchronous':
                    # 测试异步模式
                    queue_size = mode_config.get('queue_size', 1000)
                    worker_threads = mode_config.get('worker_threads', 4)
                    
                    results[mode_name] = {
                        'status': 'success',
                        'message': f'异步模式配置: queue_size={queue_size}, workers={worker_threads}',
                        'config': mode_config
                    }
                    
                elif mode_name == 'broadcast':
                    # 测试广播模式
                    ttl = mode_config.get('ttl', 300)
                    max_recipients = mode_config.get('max_recipients', 20)
                    
                    results[mode_name] = {
                        'status': 'success',
                        'message': f'广播模式配置: ttl={ttl}s, max_recipients={max_recipients}',
                        'config': mode_config
                    }
                    
            except Exception as e:
                results[mode_name] = {
                    'status': 'error',
                    'error': str(e),
                    'config': mode_config
                }
                
        return results
    
    def test_security_config(self) -> Dict:
        """测试安全配置"""
        logger.info("开始测试安全配置...")
        
        security_config = self.config.get('security', {})
        results = {}
        
        # 测试认证配置
        auth_config = security_config.get('authentication', {})
        if auth_config.get('enabled', False):
            results['authentication'] = {
                'status': 'success',
                'message': f"认证已启用，方法: {auth_config.get('method', 'unknown')}",
                'config': auth_config
            }
        else:
            results['authentication'] = {
                'status': 'warning',
                'warning': '认证未启用',
                'config': auth_config
            }
        
        # 测试加密配置
        encryption_config = security_config.get('encryption', {})
        if encryption_config.get('enabled', False):
            results['encryption'] = {
                'status': 'success',
                'message': f"加密已启用，算法: {encryption_config.get('algorithm', 'unknown')}",
                'config': encryption_config
            }
        else:
            results['encryption'] = {
                'status': 'warning',
                'warning': '加密未启用',
                'config': encryption_config
            }
        
        # 测试审计日志配置
        audit_config = security_config.get('audit_logging', {})
        if audit_config.get('enabled', False):
            results['audit_logging'] = {
                'status': 'success',
                'message': f"审计日志已启用，级别: {audit_config.get('log_level', 'unknown')}",
                'config': audit_config
            }
        else:
            results['audit_logging'] = {
                'status': 'warning',
                'warning': '审计日志未启用',
                'config': audit_config
            }
        
        return results
    
    def test_workflow_communication(self) -> Dict:
        """测试工作流通信"""
        logger.info("开始测试工作流通信...")
        
        workflows = self.config.get('workflows', {})
        results = {}
        
        for workflow_name, workflow_config in workflows.items():
            logger.info(f"测试工作流: {workflow_name}")
            
            try:
                message_types = workflow_config.get('message_types', [])
                priority = workflow_config.get('priority', 'medium')
                participants = workflow_config.get('participants', [])
                
                if not message_types:
                    results[workflow_name] = {
                        'status': 'warning',
                        'warning': '未配置消息类型',
                        'config': workflow_config
                    }
                elif not participants:
                    results[workflow_name] = {
                        'status': 'warning',
                        'warning': '未配置参与者',
                        'config': workflow_config
                    }
                else:
                    results[workflow_name] = {
                        'status': 'success',
                        'message': f'工作流配置: priority={priority}, message_types={len(message_types)}, participants={len(participants)}',
                        'config': workflow_config
                    }
                    
            except Exception as e:
                results[workflow_name] = {
                    'status': 'error',
                    'error': str(e),
                    'config': workflow_config
                }
                
        return results
    
    def test_agent_rules(self) -> Dict:
        """测试智能体规则"""
        logger.info("开始测试智能体规则...")
        
        agent_rules = self.config.get('agent_rules', {})
        results = {}
        
        for rule_name, rule_configs in agent_rules.items():
            logger.info(f"测试智能体规则: {rule_name}")
            
            try:
                for rule_config in rule_configs:
                    agents = rule_config.get('agents', [])
                    priority = rule_config.get('priority', 'medium')
                    encryption = rule_config.get('encryption', False)
                    audit_level = rule_config.get('audit_level', 'basic')
                    
                    if not agents:
                        results[rule_name] = {
                            'status': 'warning',
                            'warning': '未配置智能体列表',
                            'config': rule_config
                        }
                    else:
                        results[rule_name] = {
                            'status': 'success',
                            'message': f'规则配置: agents={len(agents)}, priority={priority}, encryption={encryption}, audit={audit_level}',
                            'config': rule_config
                        }
                        
            except Exception as e:
                results[rule_name] = {
                    'status': 'error',
                    'error': str(e),
                    'config': rule_configs
                }
                
        return results
    
    def run_full_test(self) -> Dict:
        """运行完整测试"""
        logger.info("开始MCP通信完整测试...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'config_file': str(self.config_path),
            'overall_status': 'success',
            'tests': {}
        }
        
        # 运行各项测试
        results['tests']['message_models'] = self.test_message_models()
        results['tests']['communication_modes'] = self.test_communication_modes()
        results['tests']['security_config'] = self.test_security_config()
        results['tests']['workflow_communication'] = self.test_workflow_communication()
        results['tests']['agent_rules'] = self.test_agent_rules()
        
        # 计算总体状态
        all_tests_passed = True
        for test_category, test_results in results['tests'].items():
            for test_name, test_result in test_results.items():
                if test_result.get('status') in ['failed', 'error']:
                    all_tests_passed = False
                    break
            if not all_tests_passed:
                break
        
        results['overall_status'] = 'success' if all_tests_passed else 'warning'
        
        return results
    
    def generate_test_report(self, results: Dict) -> str:
        """生成测试报告"""
        report = f"""
# YDS AI公司MCP协议通信测试报告

生成时间: {results['timestamp']}
配置文件: {results['config_file']}

## 测试摘要
- **总体状态**: {results['overall_status'].upper()}
- **测试类别**: {len(results['tests'])} 个

## 详细测试结果

"""
        
        for test_category, test_results in results['tests'].items():
            report += f"### {test_category.replace('_', ' ').title()}\n\n"
            
            passed = sum(1 for r in test_results.values() if r.get('status') == 'success')
            total = len(test_results)
            
            report += f"- **通过率**: {passed}/{total} ({passed/total*100:.1f}%)\n\n"
            
            for test_name, test_result in test_results.items():
                status_icon = "✅" if test_result.get('status') == 'success' else "⚠️" if test_result.get('status') == 'warning' else "❌"
                
                report += f"#### {test_name} {status_icon}\n"
                
                if test_result.get('status') == 'success':
                    report += f"- **状态**: ✅ 通过\n"
                    report += f"- **消息**: {test_result.get('message', '无消息')}\n"
                elif test_result.get('status') == 'warning':
                    report += f"- **状态**: ⚠️ 警告\n"
                    report += f"- **警告**: {test_result.get('warning', '无警告消息')}\n"
                else:
                    report += f"- **状态**: ❌ 失败\n"
                    report += f"- **错误**: {test_result.get('error', '无错误消息')}\n"
                
                report += "\n"
        
        report += """
## 建议措施

"""
        
        if results['overall_status'] == 'success':
            report += "✅ MCP协议通信配置验证通过，可以正常启动通信服务。\n"
        else:
            report += "⚠️ 发现配置问题，建议修复后再启动通信服务。\n"
            
        return report

def main():
    """主函数"""
    tester = MCPCommunicationTester()
    
    # 运行测试
    results = tester.run_full_test()
    
    # 生成报告
    report = tester.generate_test_report(results)
    
    # 保存结果 - 按照三级存储规范：系统维护类报告存储在logs/
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = logs_dir / 'mcp_communication_test_results.json'
    report_file = logs_dir / 'mcp_communication_test_report.md'
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info("MCP通信测试完成")
    logger.info(f"测试结果已保存到: {results_file}")
    logger.info(f"测试报告已保存到: {report_file}")
    
    return results

if __name__ == "__main__":
    main()