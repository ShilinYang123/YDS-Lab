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
        # 统一到标准目录结构 01-struc
        self.struc_root = self.project_root / "01-struc"
        
    def initialize_environment(self):
        """初始化完整的Trae环境"""
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
        """验证目录结构"""
        required_dirs = [
            "01-struc/Agents",
            "01-struc/SharedWorkspace", 
            "tools/mcp/servers",
            "01-struc/Agents/CEO",
            "01-struc/Agents/PlanningDirector",
            "01-struc/Agents/FinanceDirector",
            "01-struc/Agents/DevTeamLead",
            "01-struc/Agents/MarketingDirector",
            "01-struc/Agents/ResourceAdmin",
            "01-struc/SharedWorkspace/Projects",
            "01-struc/SharedWorkspace/Documents",
            "01-struc/SharedWorkspace/Templates",
            "01-struc/SharedWorkspace/Collaboration",
            "01-struc/SharedWorkspace/KnowledgeBase",
            "tools/mcp/servers/GitHub",
            "tools/mcp/servers/Excel",
            "tools/mcp/servers/Figma",
            "tools/mcp/servers/Builder",
            "tools/mcp/servers/FileSystem",
            "tools/mcp/servers/Database"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
                
        if missing_dirs:
            print(f"   缺少目录: {missing_dirs}")
            return False
            
        return True
        
    def _initialize_agents(self):
        """初始化智能体配置"""
        agents = ["CEO", "PlanningDirector", "FinanceDirector", "DevTeamLead", "MarketingDirector", "ResourceAdmin"]
        
        for agent in agents:
            agent_dir = self.struc_root / "Agents" / agent
            
            # 创建智能体配置文件
            config = {
                "agent_info": {
                    "name": agent,
                    "version": "2.0.0",
                    "created": datetime.now().isoformat(),
                    "platform": "Trae"
                },
                "capabilities": self._get_agent_capabilities(agent),
                "workspace": {
                    "root": str(agent_dir),
                    "documents": str(agent_dir / "documents"),
                    "templates": str(agent_dir / "templates"),
                    "logs": str(agent_dir / "logs")
                },
                "collaboration": {
                    "reports_to": self._get_reporting_structure(agent),
                    "collaborates_with": self._get_collaboration_partners(agent)
                }
            }
            
            # 创建子目录
            for subdir in ["documents", "templates", "logs", "config"]:
                (agent_dir / subdir).mkdir(exist_ok=True)
                
            # 保存配置文件
            config_file = agent_dir / "config" / "agent_config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
        return True
        
    def _setup_shared_workspace(self):
        """配置共享工作空间"""
        workspace_root = self.struc_root / "SharedWorkspace"
        
        # 创建项目模板
        templates_dir = workspace_root / "Templates"
        
        project_template = {
            "name": "标准项目模板",
            "structure": {
                "docs": "项目文档",
                "src": "源代码",
                "tests": "测试文件",
                "config": "配置文件"
            },
            "workflow": [
                "需求分析",
                "设计方案",
                "开发实现",
                "测试验证",
                "部署上线"
            ]
        }
        
        template_file = templates_dir / "project_template.yaml"
        with open(template_file, 'w', encoding='utf-8') as f:
            yaml.dump(project_template, f, default_flow_style=False, allow_unicode=True)
            
        # 创建协作指南
        collab_dir = workspace_root / "Collaboration"
        
        collab_guide = {
            "communication_guidelines": {
                "daily_standup": "每日9:00晨会",
                "urgent_matters": "即时消息",
                "documentation": "共享文档系统"
            },
            "decision_process": {
                "consensus_items": ["项目启动", "技术选型", "预算调整"],
                "ceo_authority": ["战略决策", "人事变动", "紧急事项"],
                "department_authority": ["日常运营", "技术细节", "执行计划"]
            }
        }
        
        guide_file = collab_dir / "collaboration_guide.yaml"
        with open(guide_file, 'w', encoding='utf-8') as f:
            yaml.dump(collab_guide, f, default_flow_style=False, allow_unicode=True)
            
        return True
        
    def _initialize_mcp_cluster(self):
        """初始化MCP集群"""
        # 新路径：tools/mcp/servers
        mcp_root = self.project_root / "tools" / "mcp" / "servers"
        
        servers = ["GitHub", "Excel", "Figma", "Builder", "FileSystem", "Database"]
        
        for server in servers:
            server_dir = mcp_root / server
            
            # 创建服务器配置
            server_config = {
                "server_info": {
                    "name": f"{server} MCP Server",
                    "version": "1.0.0",
                    "protocol": "stdio",
                    "capabilities": self._get_mcp_capabilities(server)
                },
                "runtime": {
                    "python_version": "3.11+",
                    "dependencies": self._get_mcp_dependencies(server),
                    "environment": "development"
                }
            }
            
            # 创建子目录
            for subdir in ["src", "config", "logs", "tests"]:
                (server_dir / subdir).mkdir(exist_ok=True)
                
            # 保存配置
            config_file = server_dir / "config" / "server_config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(server_config, f, default_flow_style=False, allow_unicode=True)
                
        return True
        
    def _create_collaboration_templates(self):
        """创建协作模板"""
        templates_dir = self.struc_root / "SharedWorkspace" / "Templates"
        
        # 会议纪要模板
        meeting_template = """# 会议纪要模板

## 会议信息
- **日期**: {date}
- **时间**: {time}
- **参与者**: {participants}
- **主持人**: {host}

## 议程
1. 上次会议回顾
2. 当前进展汇报
3. 问题讨论
4. 决策事项
5. 下步计划

## 讨论内容
### 进展汇报
- CEO: 
- 企划总监: 
- 财务总监: 
- 开发负责人: 
- 市场总监: 
- 资源行政: 

### 问题和决策
| 问题 | 讨论结果 | 负责人 | 截止时间 |
|------|----------|--------|----------|
|      |          |        |          |

## 行动项
- [ ] 任务1 - 负责人 - 截止时间
- [ ] 任务2 - 负责人 - 截止时间

## 下次会议
- **时间**: 
- **议题**: 
"""
        
        with open(templates_dir / "meeting_template.md", 'w', encoding='utf-8') as f:
            f.write(meeting_template)
            
        return True
        
    def _setup_monitoring(self):
        """设置监控系统"""
        monitoring_config = {
            "system_monitoring": {
                "agents_health": True,
                "mcp_servers_status": True,
                "resource_usage": True,
                "performance_metrics": True
            },
            "alerts": {
                "agent_offline": "immediate",
                "mcp_server_down": "immediate", 
                "high_resource_usage": "warning",
                "collaboration_bottleneck": "info"
            },
            "reporting": {
                "daily_summary": True,
                "weekly_report": True,
                "monthly_analysis": True
            }
        }
        
        # 监控配置文件：统一至 01-struc/0B-general-manager/config
        config_file = self.struc_root / "0B-general-manager" / "config" / "monitoring_config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(monitoring_config, f, default_flow_style=False, allow_unicode=True)
            
        return True
        
    def _verify_environment(self):
        """验证环境完整性"""
        verification_results = {
            "directory_structure": self._verify_directory_structure(),
            "config_files": self._verify_config_files(),
            "agent_setup": self._verify_agent_setup(),
            "mcp_cluster": self._verify_mcp_cluster()
        }
        
        all_passed = all(verification_results.values())
        
        print(f"\n📊 环境验证结果:")
        for check, result in verification_results.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
            
        return all_passed
        
    def _verify_config_files(self):
        """验证配置文件"""
        required_configs = [
            "01-struc/0B-general-manager/config/startup_config.yaml",
            "01-struc/Agents/collaboration_workflows.yaml",
            "tools/mcp/servers/cluster_config.yaml"
        ]
        
        for config_path in required_configs:
            if not (self.project_root / config_path).exists():
                return False
                
        return True
        
    def _verify_agent_setup(self):
        """验证智能体设置"""
        agents = ["CEO", "PlanningDirector", "FinanceDirector", "DevTeamLead", "MarketingDirector", "ResourceAdmin"]
        
        for agent in agents:
            config_file = self.struc_root / "Agents" / agent / "config" / "agent_config.yaml"
            if not config_file.exists():
                return False
                
        return True
        
    def _verify_mcp_cluster(self):
        """验证MCP集群设置"""
        servers = ["GitHub", "Excel", "Figma", "Builder", "FileSystem", "Database"]
        
        for server in servers:
            config_file = self.project_root / "tools" / "mcp" / "servers" / server / "config" / "server_config.yaml"
            if not config_file.exists():
                return False
                
        return True
        
    def _get_agent_capabilities(self, agent):
        """获取智能体能力配置"""
        capabilities_map = {
            "CEO": ["战略决策", "团队协调", "业务规划", "风险管理"],
            "PlanningDirector": ["项目规划", "需求分析", "方案设计", "进度管理"],
            "FinanceDirector": ["财务分析", "预算管理", "成本控制", "投资决策"],
            "DevTeamLead": ["技术架构", "代码审查", "团队管理", "技术选型"],
            "MarketingDirector": ["市场分析", "推广策略", "用户研究", "品牌管理"],
            "ResourceAdmin": ["资源管理", "行政支持", "文档管理", "流程优化"]
        }
        return capabilities_map.get(agent, [])
        
    def _get_reporting_structure(self, agent):
        """获取汇报关系"""
        if agent == "CEO":
            return []
        else:
            return ["CEO"]
            
    def _get_collaboration_partners(self, agent):
        """获取协作伙伴"""
        collab_map = {
            "CEO": ["PlanningDirector", "FinanceDirector", "DevTeamLead", "MarketingDirector", "ResourceAdmin"],
            "PlanningDirector": ["DevTeamLead", "MarketingDirector", "FinanceDirector"],
            "FinanceDirector": ["PlanningDirector", "ResourceAdmin"],
            "DevTeamLead": ["PlanningDirector", "ResourceAdmin"],
            "MarketingDirector": ["PlanningDirector", "ResourceAdmin"],
            "ResourceAdmin": ["FinanceDirector", "DevTeamLead", "MarketingDirector"]
        }
        return collab_map.get(agent, [])
        
    def _get_mcp_capabilities(self, server):
        """获取MCP服务器能力"""
        capabilities_map = {
            "GitHub": ["repository_management", "code_collaboration", "version_control"],
            "Excel": ["spreadsheet_processing", "data_analysis", "report_generation"],
            "Figma": ["design_collaboration", "prototype_management", "asset_export"],
            "Builder": ["code_generation", "automated_building", "deployment_management"],
            "FileSystem": ["file_operations", "directory_management", "backup_services"],
            "Database": ["data_storage", "query_services", "data_migration"]
        }
        return capabilities_map.get(server, [])
        
    def _get_mcp_dependencies(self, server):
        """获取MCP服务器依赖"""
        deps_map = {
            "GitHub": ["github", "requests", "mcp"],
            "Excel": ["openpyxl", "pandas", "mcp"],
            "Figma": ["figma-api", "requests", "mcp"],
            "Builder": ["jinja2", "docker", "mcp"],
            "FileSystem": ["pathlib", "shutil", "mcp"],
            "Database": ["sqlalchemy", "sqlite3", "mcp"]
        }
        return deps_map.get(server, ["mcp"])

def main():
    """主函数"""
    print("🚀 YDS-Lab Trae环境初始化器")
    print("=" * 50)
    
    initializer = TraeEnvironmentInitializer()
    success = initializer.initialize_environment()
    
    if success:
        print("\n🎉 Trae环境初始化成功！")
        print("📋 下一步可以开始迁移智能体配置")
    else:
        print("\n❌ Trae环境初始化失败，请检查错误信息")
        
    return success

if __name__ == "__main__":
    main()