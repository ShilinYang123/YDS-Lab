#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae环境初始化脚本
功能：初始化和验证Trae开发环境的完整性
"""

import os
import yaml
import json
import time
from pathlib import Path
from datetime import datetime

class TraeEnvironmentInitializer:
    """Trae环境初始化器"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        # 统一标准目录结构01-struc
        self.struc_root = self.project_root / "01-struc"
        
    def initialize_environment(self):
        """初始化完整的Trae开发环境"""
        print("🚀 开始初始化Trae开发环境...")
        
        steps = [
            ("验证目录结构", self._verify_directory_structure),
            ("初始化智能体配置", self._initialize_agents),
            ("配置共享工作空间", self._setup_shared_workspace),
            ("初始化MCP集群", self._initialize_mcp_cluster),
            ("创建协作模板", self._create_collaboration_templates),
            ("设置监控系统", self._setup_monitoring),
            ("验证环境完整性", self._verify_environment)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            try:
                result = step_func()
                if result:
                    print(f"   ✅ {step_name} 完成")
                else:
                    print(f"   ❌ {step_name} 失败")
                    return False
            except Exception as e:
                print(f"   ❌ {step_name} 出错: {e}")
                return False
                
        print("\n🎉 Trae环境初始化完成！")
        return True
        
    def _verify_directory_structure(self):
        """验证目录结构 - 适配V5.1架构规范"""
        # 定义目录映射，支持编号+snake_case命名规范
        required_structure = {
            # 基础目录
            "01-struc/Agents": "必须存在",
            "01-struc/SharedWorkspace": "必须存在", 
            "tools/mcp/servers": "必须存在",
            
            # 智能体目录 - 使用编号+snake_case规范
            "01-struc/Agents/01-ceo": "CEO智能体",
            "01-struc/Agents/03-planning_director": "企划部主管",
            "01-struc/Agents/04-finance_director": "财务总监", 
            "01-struc/Agents/06-dev_team": "开发团队（容器目录）",
            "01-struc/Agents/07-marketing_director": "市场总监",
            "01-struc/Agents/05-resource_admin": "资源管理员",
            
            # SharedWorkspace子目录 - 可选，用于兼容性
            "01-struc/SharedWorkspace/Templates": "模板目录",
            "01-struc/SharedWorkspace/Collaboration": "协作目录",
            
            # MCP服务器目录
            "tools/mcp/servers/GitHub": "GitHub MCP服务器",
            "tools/mcp/servers/Excel": "Excel MCP服务器",
            "tools/mcp/servers/Figma": "Figma MCP服务器",
            "tools/mcp/servers/Builder": "Builder MCP服务器",
            "tools/mcp/servers/FileSystem": "文件系统MCP服务器",
            "tools/mcp/servers/Database": "数据库MCP服务器"
        }
        
        missing_dirs = []
        warnings = []
        
        for dir_path, description in required_structure.items():
            full_path = self.project_root / dir_path
            if not full_path.exists():
                # 对于开发团队，检查替代方案
                if "06-dev_team" in dir_path:
                    # 检查是否存在开发团队子角色
                    dev_team_path = self.project_root / "01-struc/Agents/06-dev_team"
                    if dev_team_path.exists():
                        # 检查是否至少有一个开发子角色存在
                        dev_subroles = ["dev_director", "dev_coder", "dev_tester", "dev_architect"]
                        has_dev_role = any((dev_team_path / subrole).exists() for subrole in dev_subroles)
                        if has_dev_role:
                            continue  # 开发团队结构正确
                    warnings.append(f"开发团队结构不完整: {dir_path}")
                else:
                    missing_dirs.append(f"{dir_path} ({description})")
        
        # 检查可选目录
        optional_dirs = [
            "01-struc/SharedWorkspace/Projects",
            "01-struc/SharedWorkspace/Documents", 
            "01-struc/SharedWorkspace/KnowledgeBase"
        ]
        
        for opt_dir in optional_dirs:
            if not (self.project_root / opt_dir).exists():
                # 这些目录可选，将自动创建
                pass
        
        if missing_dirs:
            print(f"   缺少必要目录: {missing_dirs}")
            return False
            
        if warnings:
            print(f"   警告: {warnings}")
            # 警告不阻止继续
            
        return True
        
    def _initialize_agents(self):
        """初始化智能体配置 - 适配V5.1架构编号+snake_case命名规范"""
        # 定义智能体映射，适配实际目录结构
        agent_mappings = {
            "CEO": {
                "dir_name": "01-ceo",
                "display_name": "CEO"
            },
            "PlanningDirector": {
                "dir_name": "03-planning_director", 
                "display_name": "企划部主管"
            },
            "FinanceDirector": {
                "dir_name": "04-finance_director",
                "display_name": "财务总监"
            },
            "DevTeamLead": {
                "dir_name": "06-dev_team",  # 开发团队容器目录
                "display_name": "开发团队负责人",
                "is_container": True
            },
            "MarketingDirector": {
                "dir_name": "07-marketing_director",
                "display_name": "市场总监"
            },
            "ResourceAdmin": {
                "dir_name": "05-resource_admin",
                "display_name": "资源管理员"
            }
        }
        
        for agent_key, agent_info in agent_mappings.items():
            agent_dir = self.struc_root / "Agents" / agent_info["dir_name"]
            
            # 创建智能体配置文档
            config = {
                "agent_info": {
                    "name": agent_info["display_name"],
                    "key": agent_key,
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat(),
                    "platform": "Trae"
                },
                "capabilities": self._get_agent_capabilities(agent_key),
                "workspace": {
                    "root": str(agent_dir),
                    "documents": str(agent_dir / "documents"),
                    "templates": str(agent_dir / "templates"),
                    "logs": str(agent_dir / "logs")
                },
                "collaboration": {
                    "reporting_to": self._get_reporting_structure(agent_key),
                    "collaborates_with": self._get_collaboration_partners(agent_key)
                }
            }
            
            # 创建必要的子目录
            for subdir in ["documents", "templates", "logs", "config"]:
                (agent_dir / subdir).mkdir(parents=True, exist_ok=True)
            
            # 保存配置文件
            config_file = agent_dir / "config" / "agent_config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                
        return True
        
    def _setup_shared_workspace(self):
        """配置共享工作空间"""
        shared_workspace = self.struc_root / "SharedWorkspace"
        
        # 创建项目模板
        project_template = {
            "project_structure": {
                "docs": "项目文档目录",
                "src": "源代码目录",
                "tests": "测试文件目录",
                "config": "配置文件目录"
            },
            "workflow_stages": [
                "需求分析",
                "设计阶段",
                "开发实现",
                "测试验证",
                "部署上线",
                "运维监控"
            ]
        }
        
        templates_dir = shared_workspace / "Templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_file = templates_dir / "project_template.yaml"
        with open(template_file, 'w', encoding='utf-8') as f:
            yaml.dump(project_template, f, allow_unicode=True, default_flow_style=False)
        
        # 创建协作指南
        collaboration_guide = {
            "communication_protocols": {
                "daily_standup": "每日例会，同步进展",
                "weekly_review": "周回顾，总结经验",
                "urgent_matters": "紧急事项，立即通知"
            },
            "documentation_standards": {
                "meeting_notes": "会议记录模板",
                "project_docs": "项目文档规范",
                "code_comments": "代码注释标准"
            },
            "decision_process": {
                "consensus_items": "需要共识的事项",
                "authority_levels": "各角色权限级别",
                "escalation_path": "问题升级路径"
            }
        }
        
        collaboration_dir = shared_workspace / "Collaboration"
        collaboration_dir.mkdir(parents=True, exist_ok=True)
        
        guide_file = collaboration_dir / "collaboration_guide.yaml"
        with open(guide_file, 'w', encoding='utf-8') as f:
            yaml.dump(collaboration_guide, f, allow_unicode=True, default_flow_style=False)
            
        return True
        
    def _initialize_mcp_cluster(self):
        """初始化MCP集群"""
        servers = ["GitHub", "Excel", "Figma", "Builder", "FileSystem", "Database"]
        mcp_servers_dir = self.project_root / "tools" / "mcp" / "servers"
        
        for server in servers:
            server_dir = mcp_servers_dir / server
            
            # 创建服务器目录结构
            for subdir in ["src", "config", "logs", "tests"]:
                (server_dir / subdir).mkdir(parents=True, exist_ok=True)
            
            # 创建服务器配置
            server_config = {
                "server_info": {
                    "name": server,
                    "version": "1.0.0",
                    "protocol": "MCP",
                    "capabilities": self._get_mcp_capabilities(server)
                },
                "runtime": {
                    "python_version": "3.8+",
                    "dependencies": self._get_mcp_dependencies(server),
                    "environment": "production"
                }
            }
            
            config_file = server_dir / "config" / "server_config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(server_config, f, allow_unicode=True, default_flow_style=False)
                
        return True
        
    def _create_collaboration_templates(self):
        """创建协作模板"""
        templates_dir = self.struc_root / "SharedWorkspace" / "Templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建会议模板
        meeting_template = """# 会议记录模板

## 会议信息
- **日期**: {date}
- **时间**: {time}
- **参与者**: {participants}
- **主持人**: {host}

## 议程
1. {agenda_item_1}
2. {agenda_item_2}
3. {agenda_item_3}

## 讨论要点
### 要点1
- {discussion_point_1}

### 要点2
- {discussion_point_2}

## 决策事项
- {decision_1}
- {decision_2}

## 行动项
| 任务 | 负责人 | 截止日期 | 状态 |
|------|--------|----------|------|
| {task_1} | {owner_1} | {due_1} | {status_1} |
| {task_2} | {owner_2} | {due_2} | {status_2} |

## 下次会议
- **时间**: {next_meeting_time}
- **主要议题**: {next_meeting_topics}
"""
        
        meeting_template_file = templates_dir / "meeting_template.md"
        with open(meeting_template_file, 'w', encoding='utf-8') as f:
            f.write(meeting_template)
            
        return True
        
    def _setup_monitoring(self):
        """设置监控系统 - 兼容现有配置位置"""
        monitoring_config = {
            "system_monitoring": {
                "agents_health": {
                    "enabled": True,
                    "check_interval": 300,
                    "alert_threshold": 3
                },
                "mcp_servers_status": {
                    "enabled": True,
                    "check_interval": 60,
                    "timeout": 30
                },
                "resource_usage": {
                    "enabled": True,
                    "metrics": ["cpu", "memory", "disk"],
                    "alert_threshold": 80
                },
                "performance_metrics": {
                    "enabled": True,
                    "track_response_time": True,
                    "track_error_rate": True
                }
            },
            "alerts": {
                "system_failure": {
                    "level": "critical",
                    "notify": ["admin", "dev-team"],
                    "escalation_time": 15
                },
                "performance_degradation": {
                    "level": "warning",
                    "notify": ["dev-team"],
                    "threshold": 50
                },
                "resource_exhaustion": {
                    "level": "critical",
                    "notify": ["admin", "resource-admin"],
                    "threshold": 90
                }
            },
            "reporting": {
                "daily_reports": True,
                "weekly_reports": True,
                "monthly_reports": True,
                "report_format": "markdown"
            }
        }
        
        # 检查现有配置位置，优先使用已存在的位置
        config_locations = [
            "config/monitoring_config.yaml",  # 标准位置
            "01-struc/0B-general-manager/config/monitoring_config.yaml"  # 兼容位置
        ]
        
        # 找到第一个可用的配置目录
        config_dir = None
        for config_path in config_locations:
            config_dir = self.project_root / config_path
            config_dir.parent.mkdir(parents=True, exist_ok=True)
            if config_dir.parent.exists():
                break
        
        if config_dir:
            with open(config_dir, 'w', encoding='utf-8') as f:
                yaml.dump(monitoring_config, f, allow_unicode=True, default_flow_style=False)
            print(f"   监控配置已保存到: {config_dir}")
        else:
            print("   警告: 无法找到合适的配置目录")
            
        return True
        
    def _verify_environment(self):
        """验证环境完整性"""
        # 验证目录结构
        if not self._verify_directory_structure():
            return False
            
        # 验证配置文件
        if not self._verify_config_files():
            return False
            
        # 验证智能体设置
        if not self._verify_agent_setup():
            return False
            
        # 验证MCP集群
        if not self._verify_mcp_cluster():
            return False
            
        return True
        
    def _verify_config_files(self):
        """验证配置文件 - 适配V5.1架构"""
        # 监控配置可以存储在多个位置，检查主要位置
        monitoring_configs = [
            "config/monitoring_config.yaml",  # 首选位置
            "01-struc/0B-general-manager/config/monitoring_config.yaml"  # 兼容位置
        ]
        
        monitoring_found = False
        for config_path in monitoring_configs:
            if (self.project_root / config_path).exists():
                monitoring_found = True
                break
                
        if not monitoring_found:
            print(f"   缺少监控配置文件，应在以下位置之一: {monitoring_configs}")
            return False
        
        # 其他配置文件
        other_configs = [
            "01-struc/Agents/collaboration_workflows.yaml",
            "tools/mcp/servers/cluster_config.yaml"
        ]
        
        for file_path in other_configs:
            full_path = self.project_root / file_path
            if not full_path.exists():
                print(f"   缺少配置文件: {file_path}")
                return False
                
        return True
        
    def _verify_agent_setup(self):
        """验证智能体设置 - 适配V5.1架构"""
        agent_mappings = {
            "CEO": "01-ceo",
            "PlanningDirector": "03-planning_director",
            "FinanceDirector": "04-finance_director", 
            "DevTeamLead": "06-dev_team",
            "MarketingDirector": "07-marketing_director",
            "ResourceAdmin": "05-resource_admin"
        }
        
        for agent_key, dir_name in agent_mappings.items():
            config_file = self.struc_root / "Agents" / dir_name / "config" / "agent_config.yaml"
            if not config_file.exists():
                print(f"   智能体配置缺失: {agent_key} (目录: {dir_name})")
                return False
                
        return True
        
    def _verify_mcp_cluster(self):
        """验证MCP集群"""
        servers = ["GitHub", "Excel", "Figma", "Builder", "FileSystem", "Database"]
        
        for server in servers:
            config_file = self.project_root / "tools" / "mcp" / "servers" / server / "config" / "server_config.yaml"
            if not config_file.exists():
                print(f"   MCP服务器配置缺失: {server}")
                return False
                
        return True
        
    def _get_agent_capabilities(self, agent: str) -> list:
        """获取智能体能力"""
        capabilities = {
            "CEO": ["战略制定", "决策审批", "资源分配", "风险管理"],
            "PlanningDirector": ["项目规划", "进度管理", "需求分析", "架构设计"],
            "FinanceDirector": ["预算管理", "成本控制", "财务分析", "投资回报"],
            "DevTeamLead": ["技术架构", "代码审查", "开发管理", "技术创新"],
            "MarketingDirector": ["市场分析", "营销策略", "品牌建设", "客户关系"],
            "ResourceAdmin": ["资源调配", "设备管理", "行政支持", "后勤保障"]
        }
        return capabilities.get(agent, [])
        
    def _get_reporting_structure(self, agent: str) -> str:
        """获取汇报关系"""
        if agent == "CEO":
            return "董事会"
        return "CEO"
        
    def _get_collaboration_partners(self, agent: str) -> list:
        """获取协作伙伴"""
        partners = {
            "CEO": ["PlanningDirector", "FinanceDirector"],
            "PlanningDirector": ["DevTeamLead", "MarketingDirector", "ResourceAdmin"],
            "FinanceDirector": ["CEO", "PlanningDirector", "DevTeamLead"],
            "DevTeamLead": ["PlanningDirector", "MarketingDirector", "ResourceAdmin"],
            "MarketingDirector": ["PlanningDirector", "DevTeamLead", "ResourceAdmin"],
            "ResourceAdmin": ["PlanningDirector", "DevTeamLead", "MarketingDirector"]
        }
        return partners.get(agent, [])
        
    def _get_mcp_capabilities(self, server: str) -> list:
        """获取MCP服务器能力"""
        capabilities = {
            "GitHub": ["仓库管理", "代码协作", "版本控制", "CI/CD"],
            "Excel": ["数据处理", "报表生成", "公式计算", "图表制作"],
            "Figma": ["界面设计", "原型制作", "团队协作", "设计系统"],
            "Builder": ["代码构建", "部署管理", "环境配置", "自动化"],
            "FileSystem": ["文件管理", "目录操作", "权限控制", "备份恢复"],
            "Database": ["数据存储", "查询优化", "事务管理", "备份恢复"]
        }
        return capabilities.get(server, [])
        
    def _get_mcp_dependencies(self, server: str) -> list:
        """获取MCP服务器依赖"""
        dependencies = {
            "GitHub": ["PyGithub>=1.55", "gitpython>=3.1.0"],
            "Excel": ["openpyxl>=3.0.0", "pandas>=1.3.0"],
            "Figma": ["requests>=2.25.0", "Pillow>=8.0.0"],
            "Builder": ["docker>=5.0.0", "kubernetes>=18.0.0"],
            "FileSystem": ["pathlib", "shutil"],
            "Database": ["sqlalchemy>=1.4.0", "psycopg2-binary>=2.8.0"]
        }
        return dependencies.get(server, [])

def main():
    """主函数"""
    initializer = TraeEnvironmentInitializer()
    success = initializer.initialize_environment()
    
    if success:
        print("\n✅ 环境初始化成功！")
        return 0
    else:
        print("\n❌ 环境初始化失败！")
        return 1

if __name__ == "__main__":
    exit(main())