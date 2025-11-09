#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae鐜鍒濆鍖栬剼鏈?鍔熻兘锛氬垵濮嬪寲鍜岄獙璇乀rae寮€鍙戠幆澧冪殑瀹屾暣鎬?"""

import os
import yaml
import json
import time
from pathlib import Path
from datetime import datetime

class TraeEnvironmentInitializer:
    """Trae鐜鍒濆鍖栧櫒"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        # 缁熶竴鍒版爣鍑嗙洰褰曠粨鏋?01-struc
        self.struc_root = self.project_root / "01-struc"
        
    def initialize_environment(self):
        """鍒濆鍖栧畬鏁寸殑Trae鐜"""
        print("馃殌 寮€濮嬪垵濮嬪寲Trae寮€鍙戠幆澧?..")
        
        steps = [
            ("楠岃瘉鐩綍缁撴瀯", self._verify_directory_structure),
            ("鍒濆鍖栨櫤鑳戒綋閰嶇疆", self._initialize_agents),
            ("閰嶇疆鍏变韩宸ヤ綔绌洪棿", self._setup_shared_workspace),
            ("鍒濆鍖朚CP闆嗙兢", self._initialize_mcp_cluster),
            ("鍒涘缓鍗忎綔妯℃澘", self._create_collaboration_templates),
            ("璁剧疆鐩戞帶绯荤粺", self._setup_monitoring),
            ("楠岃瘉鐜瀹屾暣鎬?, self._verify_environment)
        ]
        
        for step_name, step_func in steps:
            print(f"\n馃搵 {step_name}...")
            try:
                result = step_func()
                if result:
                    print(f"   鉁?{step_name} 瀹屾垚")
                else:
                    print(f"   鉂?{step_name} 澶辫触")
                    return False
            except Exception as e:
                print(f"   鉂?{step_name} 鍑洪敊: {e}")
                return False
                
        print("\n馃帀 Trae鐜鍒濆鍖栧畬鎴愶紒")
        return True
        
    def _verify_directory_structure(self):
        """楠岃瘉鐩綍缁撴瀯"""
        required_dirs = [
            "01-struc/Agents",
            "01-struc/SharedWorkspace", 
            "tools/mcp/servers",
            "01-struc/Agents/01-ceo",
            "01-struc/Agents/PlanningDirector",
            "01-struc/Agents/FinanceDirector",
            "01-struc/Agents/DevTeamLead",
            "01-struc/Agents/MarketingDirector",
            "01-struc/Agents/ResourceAdmin",
            "01-struc/SharedWorkspace/Projects",
            "01-struc/docs/07-资料库",
            "01-struc/docs/05-模板库",
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
            print(f"   缂哄皯鐩綍: {missing_dirs}")
            return False
            
        return True
        
    def _initialize_agents(self):
        """鍒濆鍖栨櫤鑳戒綋閰嶇疆"""
        agents = ["CEO", "PlanningDirector", "FinanceDirector", "DevTeamLead", "MarketingDirector", "ResourceAdmin"]
        
        for agent in agents:
            agent_dir = self.struc_root / "Agents" / agent
            
            # 鍒涘缓鏅鸿兘浣撻厤缃枃浠?            config = {
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
            
            # 鍒涘缓瀛愮洰褰?            for subdir in ["documents", "templates", "logs", "config"]:
                (agent_dir / subdir).mkdir(exist_ok=True)
                
            # 淇濆瓨閰嶇疆鏂囦欢
            config_file = agent_dir / "config" / "agent_config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
        return True
        
    def _setup_shared_workspace(self):
        """閰嶇疆鍏变韩宸ヤ綔绌洪棿"""
        workspace_root = self.struc_root / "SharedWorkspace"
        
        # 鍒涘缓椤圭洰妯℃澘
        templates_dir = workspace_root / "Templates"
        
        project_template = {
            "name": "鏍囧噯椤圭洰妯℃澘",
            "structure": {
                "docs": "椤圭洰鏂囨。",
                "src": "婧愪唬鐮?,
                "tests": "娴嬭瘯鏂囦欢",
                "config": "閰嶇疆鏂囦欢"
            },
            "workflow": [
                "闇€姹傚垎鏋?,
                "璁捐鏂规",
                "寮€鍙戝疄鐜?,
                "娴嬭瘯楠岃瘉",
                "閮ㄧ讲涓婄嚎"
            ]
        }
        
        template_file = templates_dir / "project_template.yaml"
        with open(template_file, 'w', encoding='utf-8') as f:
            yaml.dump(project_template, f, default_flow_style=False, allow_unicode=True)
            
        # 鍒涘缓鍗忎綔鎸囧崡
        collab_dir = workspace_root / "Collaboration"
        
        collab_guide = {
            "communication_guidelines": {
                "daily_standup": "姣忔棩9:00鏅ㄤ細",
                "urgent_matters": "鍗虫椂娑堟伅",
                "documentation": "鍏变韩鏂囨。绯荤粺"
            },
            "decision_process": {
                "consensus_items": ["椤圭洰鍚姩", "鎶€鏈€夊瀷", "棰勭畻璋冩暣"],
                "ceo_authority": ["鎴樼暐鍐崇瓥", "浜轰簨鍙樺姩", "绱ф€ヤ簨椤?],
                "department_authority": ["鏃ュ父杩愯惀", "鎶€鏈粏鑺?, "鎵ц璁″垝"]
            }
        }
        
        guide_file = collab_dir / "collaboration_guide.yaml"
        with open(guide_file, 'w', encoding='utf-8') as f:
            yaml.dump(collab_guide, f, default_flow_style=False, allow_unicode=True)
            
        return True
        
    def _initialize_mcp_cluster(self):
        """鍒濆鍖朚CP闆嗙兢"""
        # 鏂拌矾寰勶細tools/mcp/servers
        mcp_root = self.project_root / "tools" / "mcp" / "servers"
        
        servers = ["GitHub", "Excel", "Figma", "Builder", "FileSystem", "Database"]
        
        for server in servers:
            server_dir = mcp_root / server
            
            # 鍒涘缓鏈嶅姟鍣ㄩ厤缃?            server_config = {
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
            
            # 鍒涘缓瀛愮洰褰?            for subdir in ["src", "config", "logs", "tests"]:
                (server_dir / subdir).mkdir(exist_ok=True)
                
            # 淇濆瓨閰嶇疆
            config_file = server_dir / "config" / "server_config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(server_config, f, default_flow_style=False, allow_unicode=True)
                
        return True
        
    def _create_collaboration_templates(self):
        """鍒涘缓鍗忎綔妯℃澘"""
        templates_dir = self.struc_root / "SharedWorkspace" / "Templates"
        
        # 浼氳绾妯℃澘
        meeting_template = """# 浼氳绾妯℃澘

## 浼氳淇℃伅
- **鏃ユ湡**: {date}
- **鏃堕棿**: {time}
- **鍙備笌鑰?*: {participants}
- **涓绘寔浜?*: {host}

## 璁▼
1. 涓婃浼氳鍥為【
2. 褰撳墠杩涘睍姹囨姤
3. 闂璁ㄨ
4. 鍐崇瓥浜嬮」
5. 涓嬫璁″垝

## 璁ㄨ鍐呭
### 杩涘睍姹囨姤
- CEO: 
- 浼佸垝鎬荤洃: 
- 璐㈠姟鎬荤洃: 
- 寮€鍙戣礋璐ｄ汉: 
- 甯傚満鎬荤洃: 
- 璧勬簮琛屾斂: 

### 闂鍜屽喅绛?| 闂 | 璁ㄨ缁撴灉 | 璐熻矗浜?| 鎴鏃堕棿 |
|------|----------|--------|----------|
|      |          |        |          |

## 琛屽姩椤?- [ ] 浠诲姟1 - 璐熻矗浜?- 鎴鏃堕棿
- [ ] 浠诲姟2 - 璐熻矗浜?- 鎴鏃堕棿

## 涓嬫浼氳
- **鏃堕棿**: 
- **璁**: 
"""
        
        with open(templates_dir / "meeting_template.md", 'w', encoding='utf-8') as f:
            f.write(meeting_template)
            
        return True
        
    def _setup_monitoring(self):
        """璁剧疆鐩戞帶绯荤粺"""
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
        
        # 鐩戞帶閰嶇疆鏂囦欢锛氱粺涓€鑷?01-struc/0B-general-manager/config
        config_file = self.struc_root / "0B-general-manager" / "config" / "monitoring_config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(monitoring_config, f, default_flow_style=False, allow_unicode=True)
            
        return True
        
    def _verify_environment(self):
        """楠岃瘉鐜瀹屾暣鎬?""
        verification_results = {
            "directory_structure": self._verify_directory_structure(),
            "config_files": self._verify_config_files(),
            "agent_setup": self._verify_agent_setup(),
            "mcp_cluster": self._verify_mcp_cluster()
        }
        
        all_passed = all(verification_results.values())
        
        print(f"\n馃搳 鐜楠岃瘉缁撴灉:")
        for check, result in verification_results.items():
            status = "鉁? if result else "鉂?
            print(f"   {status} {check}")
            
        return all_passed
        
    def _verify_config_files(self):
        """楠岃瘉閰嶇疆鏂囦欢"""
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
        """楠岃瘉鏅鸿兘浣撹缃?""
        agents = ["CEO", "PlanningDirector", "FinanceDirector", "DevTeamLead", "MarketingDirector", "ResourceAdmin"]
        
        for agent in agents:
            config_file = self.struc_root / "Agents" / agent / "config" / "agent_config.yaml"
            if not config_file.exists():
                return False
                
        return True
        
    def _verify_mcp_cluster(self):
        """楠岃瘉MCP闆嗙兢璁剧疆"""
        servers = ["GitHub", "Excel", "Figma", "Builder", "FileSystem", "Database"]
        
        for server in servers:
            config_file = self.project_root / "tools" / "mcp" / "servers" / server / "config" / "server_config.yaml"
            if not config_file.exists():
                return False
                
        return True
        
    def _get_agent_capabilities(self, agent):
        """鑾峰彇鏅鸿兘浣撹兘鍔涢厤缃?""
        capabilities_map = {
            "CEO": ["鎴樼暐鍐崇瓥", "鍥㈤槦鍗忚皟", "涓氬姟瑙勫垝", "椋庨櫓绠＄悊"],
            "PlanningDirector": ["椤圭洰瑙勫垝", "闇€姹傚垎鏋?, "鏂规璁捐", "杩涘害绠＄悊"],
            "FinanceDirector": ["璐㈠姟鍒嗘瀽", "棰勭畻绠＄悊", "鎴愭湰鎺у埗", "鎶曡祫鍐崇瓥"],
            "DevTeamLead": ["鎶€鏈灦鏋?, "浠ｇ爜瀹℃煡", "鍥㈤槦绠＄悊", "鎶€鏈€夊瀷"],
            "MarketingDirector": ["甯傚満鍒嗘瀽", "鎺ㄥ箍绛栫暐", "鐢ㄦ埛鐮旂┒", "鍝佺墝绠＄悊"],
            "ResourceAdmin": ["璧勬簮绠＄悊", "琛屾斂鏀寔", "鏂囨。绠＄悊", "娴佺▼浼樺寲"]
        }
        return capabilities_map.get(agent, [])
        
    def _get_reporting_structure(self, agent):
        """鑾峰彇姹囨姤鍏崇郴"""
        if agent == "CEO":
            return []
        else:
            return ["CEO"]
            
    def _get_collaboration_partners(self, agent):
        """鑾峰彇鍗忎綔浼欎即"""
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
        """鑾峰彇MCP鏈嶅姟鍣ㄨ兘鍔?""
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
        """鑾峰彇MCP鏈嶅姟鍣ㄤ緷璧?""
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
    """涓诲嚱鏁?""
    print("馃殌 YDS-Lab Trae鐜鍒濆鍖栧櫒")
    print("=" * 50)
    
    initializer = TraeEnvironmentInitializer()
    success = initializer.initialize_environment()
    
    if success:
        print("\n馃帀 Trae鐜鍒濆鍖栨垚鍔燂紒")
        print("馃搵 涓嬩竴姝ュ彲浠ュ紑濮嬭縼绉绘櫤鑳戒綋閰嶇疆")
    else:
        print("\n鉂?Trae鐜鍒濆鍖栧け璐ワ紝璇锋鏌ラ敊璇俊鎭?)
        
    return success

if __name__ == "__main__":
    main()


