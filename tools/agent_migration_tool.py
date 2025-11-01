#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体迁移工具
功能：将V1.0 CrewAI智能体配置迁移到Trae平台格式
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from datetime import datetime
import importlib.util

class AgentMigrationTool:
    """智能体迁移工具"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.v1_agents_path = self.project_root / "Struc" / "Agents"
        self.v2_agents_path = self.project_root / "Struc" / "TraeAgents"
        
        # 智能体映射关系
        self.agent_mapping = {
            "ceo": "CEO",
            "planning_director": "PlanningDirector", 
            "finance_director": "FinanceDirector",
            "dev_team": "DevTeamLead",
            "marketing_director": "MarketingDirector",
            "resource_admin": "ResourceAdmin"
        }
        
    def migrate_all_agents(self):
        """迁移所有智能体"""
        print("🚀 开始迁移智能体到Trae平台...")
        
        migration_results = {}
        
        for v1_name, v2_name in self.agent_mapping.items():
            print(f"\n📋 迁移 {v1_name} -> {v2_name}...")
            
            try:
                result = self._migrate_single_agent(v1_name, v2_name)
                migration_results[v2_name] = result
                
                if result["success"]:
                    print(f"   ✅ {v2_name} 迁移成功")
                else:
                    print(f"   ❌ {v2_name} 迁移失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ {v2_name} 迁移出错: {e}")
                migration_results[v2_name] = {"success": False, "error": str(e)}
                
        # 生成迁移报告
        self._generate_migration_report(migration_results)
        
        success_count = sum(1 for r in migration_results.values() if r["success"])
        total_count = len(migration_results)
        
        print(f"\n🎉 迁移完成！成功: {success_count}/{total_count}")
        return migration_results
        
    def _migrate_single_agent(self, v1_name: str, v2_name: str):
        """迁移单个智能体"""
        v1_path = self.v1_agents_path / v1_name
        v2_path = self.v2_agents_path / v2_name
        
        if not v1_path.exists():
            return {"success": False, "error": f"V1智能体目录不存在: {v1_path}"}
            
        # 1. 解析V1配置
        v1_config = self._parse_v1_agent(v1_path)
        if not v1_config["success"]:
            return v1_config
            
        # 2. 转换为V2格式
        v2_config = self._convert_to_v2_format(v1_config["data"], v2_name)
        
        # 3. 创建V2目录结构
        self._create_v2_structure(v2_path, v2_config)
        
        # 4. 迁移文件和配置
        self._migrate_files(v1_path, v2_path, v1_config["data"])
        
        return {"success": True, "v1_config": v1_config["data"], "v2_config": v2_config}
        
    def _parse_v1_agent(self, v1_path: Path):
        """解析V1智能体配置"""
        try:
            config = {
                "name": v1_path.name,
                "path": str(v1_path),
                "files": {},
                "role": None,
                "goal": None,
                "backstory": None,
                "tools": [],
                "prompt": None
            }
            
            # 解析define.py
            define_file = v1_path / "define.py"
            if define_file.exists():
                config["files"]["define"] = self._extract_agent_definition(define_file)
                
            # 解析prompt.py
            prompt_file = v1_path / "prompt.py"
            if prompt_file.exists():
                config["files"]["prompt"] = self._extract_prompt_content(prompt_file)
                config["prompt"] = config["files"]["prompt"]
                
            # 解析tools.py
            tools_file = v1_path / "tools.py"
            if tools_file.exists():
                config["files"]["tools"] = self._extract_tools_info(tools_file)
                
            return {"success": True, "data": config}
            
        except Exception as e:
            return {"success": False, "error": f"解析V1配置失败: {e}"}
            
    def _extract_agent_definition(self, define_file: Path):
        """提取智能体定义信息"""
        try:
            with open(define_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 简单的文本解析，提取关键信息
            definition = {
                "role": self._extract_field(content, "role="),
                "goal": self._extract_field(content, "goal="),
                "backstory": self._extract_field(content, "backstory="),
                "tools": self._extract_tools_list(content),
                "verbose": "verbose=True" in content,
                "allow_delegation": "allow_delegation=True" in content
            }
            
            return definition
            
        except Exception as e:
            return {"error": f"解析define.py失败: {e}"}
            
    def _extract_prompt_content(self, prompt_file: Path):
        """提取prompt内容"""
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找prompt变量
            lines = content.split('\n')
            prompt_content = ""
            in_prompt = False
            
            for line in lines:
                if "_PROMPT = \"\"\"" in line:
                    in_prompt = True
                    continue
                elif in_prompt and line.strip() == '""".strip()':
                    break
                elif in_prompt:
                    prompt_content += line + "\n"
                    
            return prompt_content.strip()
            
        except Exception as e:
            return f"解析prompt.py失败: {e}"
            
    def _extract_tools_info(self, tools_file: Path):
        """提取工具信息"""
        try:
            with open(tools_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找函数定义
            tools = []
            lines = content.split('\n')
            
            for line in lines:
                if line.strip().startswith('def ') and not line.strip().startswith('def _'):
                    func_name = line.split('def ')[1].split('(')[0].strip()
                    tools.append(func_name)
                    
            return tools
            
        except Exception as e:
            return {"error": f"解析tools.py失败: {e}"}
            
    def _extract_field(self, content: str, field_name: str):
        """从内容中提取字段值"""
        try:
            start_idx = content.find(field_name)
            if start_idx == -1:
                return None
                
            start_idx += len(field_name)
            
            # 查找引号开始
            quote_start = content.find('"', start_idx)
            if quote_start == -1:
                return None
                
            # 查找引号结束
            quote_end = content.find('"', quote_start + 1)
            if quote_end == -1:
                return None
                
            return content[quote_start + 1:quote_end]
            
        except Exception:
            return None
            
    def _extract_tools_list(self, content: str):
        """提取工具列表"""
        try:
            tools = []
            start_idx = content.find("tools=[")
            if start_idx == -1:
                return tools
                
            end_idx = content.find("]", start_idx)
            if end_idx == -1:
                return tools
                
            tools_section = content[start_idx + 7:end_idx]
            
            # 简单解析工具名称
            for line in tools_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    tool_name = line.replace(',', '').strip()
                    if tool_name:
                        tools.append(tool_name)
                        
            return tools
            
        except Exception:
            return []
            
    def _convert_to_v2_format(self, v1_config: dict, v2_name: str):
        """转换为V2格式"""
        v2_config = {
            "agent_info": {
                "name": v2_name,
                "version": "2.0.0",
                "platform": "Trae",
                "migrated_from": v1_config["name"],
                "migration_date": datetime.now().isoformat(),
                "original_role": v1_config["files"].get("define", {}).get("role"),
                "original_goal": v1_config["files"].get("define", {}).get("goal")
            },
            "capabilities": self._get_trae_capabilities(v2_name),
            "workspace": {
                "root": f"Struc/TraeAgents/{v2_name}",
                "documents": f"Struc/TraeAgents/{v2_name}/documents",
                "templates": f"Struc/TraeAgents/{v2_name}/templates", 
                "logs": f"Struc/TraeAgents/{v2_name}/logs",
                "config": f"Struc/TraeAgents/{v2_name}/config"
            },
            "trae_prompt": self._convert_prompt_to_trae(v1_config.get("prompt", ""), v2_name),
            "tools": {
                "migrated_tools": v1_config["files"].get("tools", []),
                "trae_tools": self._get_trae_tools(v2_name),
                "mcp_integrations": self._get_mcp_integrations(v2_name)
            },
            "collaboration": {
                "reports_to": ["CEO"] if v2_name != "CEO" else [],
                "collaborates_with": self._get_collaboration_partners(v2_name),
                "communication_channels": ["trae_workspace", "shared_documents", "meeting_system"]
            },
            "performance": {
                "response_time_target": "< 3s",
                "accuracy_target": "> 95%",
                "availability_target": "99.9%"
            }
        }
        
        return v2_config
        
    def _create_v2_structure(self, v2_path: Path, v2_config: dict):
        """创建V2目录结构"""
        # 创建主目录
        v2_path.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        subdirs = ["documents", "templates", "logs", "config", "tools", "prompts"]
        for subdir in subdirs:
            (v2_path / subdir).mkdir(exist_ok=True)
            
        # 保存配置文件
        config_file = v2_path / "config" / "agent_config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(v2_config, f, default_flow_style=False, allow_unicode=True)
            
    def _migrate_files(self, v1_path: Path, v2_path: Path, v1_config: dict):
        """迁移文件"""
        # 复制原始文件到documents目录
        docs_dir = v2_path / "documents" / "v1_backup"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        for file_name in ["define.py", "prompt.py", "tools.py"]:
            src_file = v1_path / file_name
            if src_file.exists():
                dst_file = docs_dir / file_name
                shutil.copy2(src_file, dst_file)
                
        # 创建Trae格式的prompt文件
        prompt_content = v1_config.get("prompt", "")
        if prompt_content:
            trae_prompt_file = v2_path / "prompts" / "main_prompt.md"
            with open(trae_prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"# {v2_path.name} Trae智能体Prompt\n\n")
                f.write("## 原始Prompt（来自V1.0）\n\n")
                f.write(prompt_content)
                f.write("\n\n## Trae平台适配说明\n\n")
                f.write("此prompt已适配Trae平台的协作机制和工作流程。\n")
                
    def _convert_prompt_to_trae(self, v1_prompt: str, agent_name: str):
        """将V1 prompt转换为Trae格式"""
        if not v1_prompt:
            return f"你是{agent_name}智能体，在Trae平台上协作工作。"
            
        # 基本的prompt适配
        trae_prompt = v1_prompt.replace("CrewAI", "Trae")
        trae_prompt = trae_prompt.replace("crewai", "trae")
        
        # 添加Trae平台特定的协作指令
        trae_additions = f"""

### 🔄 Trae平台协作机制
- 使用Trae共享工作空间进行文档协作
- 通过MCP服务器集群访问外部工具
- 遵循Trae智能体协作协议
- 实时同步工作状态和进展

### 📊 性能指标
- 响应时间: < 3秒
- 准确率: > 95%
- 可用性: 99.9%
"""
        
        return trae_prompt + trae_additions
        
    def _get_trae_capabilities(self, agent_name: str):
        """获取Trae平台能力"""
        capabilities_map = {
            "CEO": ["战略决策", "团队协调", "业务规划", "风险管理", "会议主持"],
            "PlanningDirector": ["项目规划", "需求分析", "方案设计", "进度管理", "资源协调"],
            "FinanceDirector": ["财务分析", "预算管理", "成本控制", "投资决策", "财务报告"],
            "DevTeamLead": ["技术架构", "代码审查", "团队管理", "技术选型", "开发规划"],
            "MarketingDirector": ["市场分析", "推广策略", "用户研究", "品牌管理", "渠道管理"],
            "ResourceAdmin": ["资源管理", "行政支持", "文档管理", "流程优化", "合规管理"]
        }
        return capabilities_map.get(agent_name, [])
        
    def _get_trae_tools(self, agent_name: str):
        """获取Trae平台工具"""
        tools_map = {
            "CEO": ["meeting_scheduler", "decision_tracker", "performance_monitor"],
            "PlanningDirector": ["project_planner", "requirement_analyzer", "timeline_manager"],
            "FinanceDirector": ["budget_calculator", "cost_analyzer", "financial_reporter"],
            "DevTeamLead": ["code_reviewer", "architecture_designer", "team_coordinator"],
            "MarketingDirector": ["market_analyzer", "campaign_manager", "user_researcher"],
            "ResourceAdmin": ["resource_tracker", "document_manager", "process_optimizer"]
        }
        return tools_map.get(agent_name, [])
        
    def _get_mcp_integrations(self, agent_name: str):
        """获取MCP集成"""
        mcp_map = {
            "CEO": ["GitHub", "Excel", "FileSystem"],
            "PlanningDirector": ["GitHub", "Figma", "Excel"],
            "FinanceDirector": ["Excel", "Database", "FileSystem"],
            "DevTeamLead": ["GitHub", "Builder", "Database"],
            "MarketingDirector": ["Figma", "Excel", "FileSystem"],
            "ResourceAdmin": ["FileSystem", "Database", "Excel"]
        }
        return mcp_map.get(agent_name, [])
        
    def _get_collaboration_partners(self, agent_name: str):
        """获取协作伙伴"""
        collab_map = {
            "CEO": ["PlanningDirector", "FinanceDirector", "DevTeamLead", "MarketingDirector", "ResourceAdmin"],
            "PlanningDirector": ["DevTeamLead", "MarketingDirector", "FinanceDirector"],
            "FinanceDirector": ["PlanningDirector", "ResourceAdmin"],
            "DevTeamLead": ["PlanningDirector", "ResourceAdmin"],
            "MarketingDirector": ["PlanningDirector", "ResourceAdmin"],
            "ResourceAdmin": ["FinanceDirector", "DevTeamLead", "MarketingDirector"]
        }
        return collab_map.get(agent_name, [])
        
    def _generate_migration_report(self, results: dict):
        """生成迁移报告"""
        report = {
            "migration_summary": {
                "date": datetime.now().isoformat(),
                "total_agents": len(results),
                "successful_migrations": sum(1 for r in results.values() if r["success"]),
                "failed_migrations": sum(1 for r in results.values() if not r["success"])
            },
            "agent_details": results,
            "next_steps": [
                "配置智能体协作流程",
                "测试智能体功能",
                "集成MCP工具",
                "性能优化调整"
            ]
        }
        
        report_file = self.project_root / "tools" / "migration_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"\n📊 迁移报告已保存: {report_file}")

def main():
    """主函数"""
    print("🚀 YDS-Lab 智能体迁移工具")
    print("=" * 50)
    
    migrator = AgentMigrationTool()
    results = migrator.migrate_all_agents()
    
    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)
    
    if success_count == total_count:
        print(f"\n🎉 所有智能体迁移成功！({success_count}/{total_count})")
        print("📋 下一步可以配置智能体协作流程")
    else:
        print(f"\n⚠️ 部分智能体迁移失败 ({success_count}/{total_count})")
        print("📋 请检查失败原因并重新迁移")
        
    return results

if __name__ == "__main__":
    main()