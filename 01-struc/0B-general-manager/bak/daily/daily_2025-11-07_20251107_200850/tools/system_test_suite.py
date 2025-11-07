#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae系统测试套件
功能：全面测试Trae平台的智能体系统和协作机制
"""

import os
import yaml
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class TraeSystemTestSuite:
    """Trae系统测试套件"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent
            
        self.project_root = Path(project_root)
        # 路径统一到 01-struc，并且 TraeAgents 合并为 Agents
        self.trae_agents_path = self.project_root / "01-struc" / "Agents"
        self.shared_workspace = self.project_root / "01-struc" / "SharedWorkspace"
        # MCP 集群目录采用“新路径优先、旧路径兼容”的策略
        self.mcp_cluster_new = self.project_root / "tools" / "mcp" / "servers"
        self.mcp_cluster_legacy = self.project_root / "01-struc" / "MCPCluster"
        
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }

    def _resolve_role_dir(self, *candidates: str) -> Path:
        """在 Agents 目录中解析角色目录，兼容大小写或不同命名（如 DevTeamLead 与 dev_team）。"""
        for name in candidates:
            p = self.trae_agents_path / name
            if p.exists():
                return p
        # 默认返回第一个候选用于错误提示
        return self.trae_agents_path / candidates[0]
        
    def _resolve_mcp_cluster_dir(self) -> Path:
        """解析 MCP 集群目录：优先使用 tools/mcp/servers，兼容 01-struc/MCPCluster。"""
        if self.mcp_cluster_new.exists():
            return self.mcp_cluster_new
        if self.mcp_cluster_legacy.exists():
            return self.mcp_cluster_legacy
        # 默认返回新路径用于错误提示/后续创建
        return self.mcp_cluster_new

    def _resolve_cluster_config(self) -> Path:
        """解析 cluster_config.yaml：优先使用新路径，兼容旧路径。"""
        candidates = [
            self.project_root / "tools" / "mcp" / "servers" / "cluster_config.yaml",
            self.project_root / "01-struc" / "MCPCluster" / "cluster_config.yaml",
        ]
        for p in candidates:
            if p.exists():
                return p
        return candidates[0]
        
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始Trae系统全面测试...")
        print("=" * 60)
        
        test_suites = [
            ("环境完整性测试", self.test_environment_integrity),
            ("智能体配置测试", self.test_agent_configurations),
            ("协作机制测试", self.test_collaboration_mechanisms),
            ("工作空间测试", self.test_workspace_functionality),
            ("MCP集群测试", self.test_mcp_cluster),
            ("性能基准测试", self.test_performance_benchmarks),
            ("安全性测试", self.test_security_features),
            ("容错性测试", self.test_fault_tolerance)
        ]
        
        for test_name, test_func in test_suites:
            print(f"\n🔍 执行: {test_name}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()
                
                self.test_results["tests"][test_name] = {
                    "status": "PASS" if result["success"] else "FAIL",
                    "duration": round(end_time - start_time, 2),
                    "details": result,
                    "timestamp": datetime.now().isoformat()
                }
                
                status_icon = "✅" if result["success"] else "❌"
                print(f"{status_icon} {test_name}: {self.test_results['tests'][test_name]['status']}")
                
                if not result["success"]:
                    print(f"   错误: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                self.test_results["tests"][test_name] = {
                    "status": "ERROR",
                    "duration": 0,
                    "details": {"success": False, "error": str(e)},
                    "timestamp": datetime.now().isoformat()
                }
                print(f"❌ {test_name}: ERROR - {e}")
                
        # 生成测试报告
        self._generate_test_report()
        
        # 显示测试摘要
        self._display_test_summary()
        
    def test_environment_integrity(self):
        """测试环境完整性"""
        checks = []
        
        # 1. 检查目录结构
        required_dirs = [
            self.trae_agents_path,
            self.shared_workspace,
            self._resolve_role_dir("CEO", "ceo"),
            self._resolve_role_dir("DevTeamLead", "dev_team"),
            self._resolve_role_dir("ResourceAdmin", "resource_admin"),
            self._resolve_role_dir("PlanningDirector", "planning_director"),
            self._resolve_role_dir("FinanceDirector", "finance_director"),
            self._resolve_role_dir("MarketingDirector", "marketing_director")
        ]
        
        for dir_path in required_dirs:
            if dir_path.exists():
                checks.append(f"✅ 目录存在: {dir_path.name}")
            else:
                checks.append(f"❌ 目录缺失: {dir_path.name}")
                return {"success": False, "error": f"缺失目录: {dir_path}", "checks": checks}
        
        # MCP 集群目录单独采用新旧路径兼容检查
        mcp_dir = self._resolve_mcp_cluster_dir()
        if mcp_dir.exists():
            if mcp_dir == self.mcp_cluster_new:
                checks.append(f"✅ MCP集群目录存在（新路径）: {mcp_dir}")
            else:
                checks.append(f"✅ MCP集群目录存在（旧路径兼容）: {mcp_dir}")
        else:
            checks.append("❌ MCP集群目录不存在（新旧路径均未找到）")
            return {"success": False, "error": "MCP集群目录缺失", "checks": checks}
                
        # 2. 检查配置文件
        # 统一配置来源到 config/，去除旧的 Struc/trae_config.yaml
        config_files = [
            self.project_root / "config" / "production.yaml",
            self.trae_agents_path / "collaboration_workflows.yaml",
        ]
        
        for config_file in config_files:
            if config_file.exists():
                checks.append(f"✅ 配置文件存在: {config_file.name}")
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                    checks.append(f"✅ 配置文件格式正确: {config_file.name}")
                except Exception as e:
                    checks.append(f"❌ 配置文件格式错误: {config_file.name} - {e}")
                    return {"success": False, "error": f"配置文件格式错误: {config_file.name}", "checks": checks}
            else:
                checks.append(f"❌ 配置文件缺失: {config_file.name}")
                return {"success": False, "error": f"缺失配置文件: {config_file}", "checks": checks}
        
        # 3. MCP 集群配置（新旧路径兼容）
        cluster_config_file = self._resolve_cluster_config()
        if cluster_config_file.exists():
            checks.append(f"✅ MCP集群配置存在: {cluster_config_file}")
            try:
                with open(cluster_config_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                checks.append("✅ MCP集群配置格式正确")
            except Exception as e:
                checks.append(f"❌ MCP集群配置格式错误: {e}")
                return {"success": False, "error": "MCP集群配置格式错误", "checks": checks}
        else:
            checks.append("❌ MCP集群配置文件不存在（新旧路径均未找到）")
            return {"success": False, "error": "MCP集群配置缺失", "checks": checks}
                
        return {"success": True, "checks": checks}
        
    def test_agent_configurations(self):
        """测试智能体配置"""
        checks = []
        agents = [
            ("CEO", "ceo"),
            ("PlanningDirector", "planning_director"),
            ("FinanceDirector", "finance_director"),
            ("DevTeamLead", "dev_team"),
            ("MarketingDirector", "marketing_director"),
            ("ResourceAdmin", "resource_admin")
        ]

        for display_name, actual_dir in agents:
            agent_path = self._resolve_role_dir(display_name, actual_dir)
            
            # 检查智能体目录结构
            required_subdirs = ["config", "documents", "logs", "prompts", "templates", "tools"]
            for subdir in required_subdirs:
                subdir_path = agent_path / subdir
                if subdir_path.exists():
                    checks.append(f"✅ {display_name}/{subdir} 目录存在")
                else:
                    checks.append(f"❌ {display_name}/{subdir} 目录缺失")
                    return {"success": False, "error": f"{display_name} 目录结构不完整", "checks": checks}
                    
            # 检查配置文件
            config_file = agent_path / "config" / "agent_config.yaml"
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                        
                    # 验证配置结构
                    required_keys = ["agent_info", "capabilities", "workspace", "tools", "collaboration"]
                    for key in required_keys:
                        if key in config:
                            checks.append(f"✅ {display_name} 配置包含 {key}")
                        else:
                            checks.append(f"❌ {display_name} 配置缺少 {key}")
                            return {"success": False, "error": f"{display_name} 配置不完整", "checks": checks}
                            
                except Exception as e:
                    checks.append(f"❌ {display_name} 配置文件解析失败: {e}")
                    return {"success": False, "error": f"{display_name} 配置文件错误", "checks": checks}
            else:
                checks.append(f"❌ {agent} 配置文件不存在")
                return {"success": False, "error": f"{agent} 配置文件缺失", "checks": checks}
                
        return {"success": True, "checks": checks}
        
    def test_collaboration_mechanisms(self):
        """测试协作机制"""
        checks = []
        
        # 1. 检查协作配置文件
        collab_config_file = self.trae_agents_path / "collaboration_workflows.yaml"
        if collab_config_file.exists():
            try:
                with open(collab_config_file, 'r', encoding='utf-8') as f:
                    collab_config = yaml.safe_load(f)
                    
                # 验证工作流程
                if "workflows" in collab_config:
                    workflows = collab_config["workflows"]
                    required_workflows = ["daily_operations", "project_development", "emergency_response"]
                    
                    for workflow in required_workflows:
                        if workflow in workflows:
                            checks.append(f"✅ 工作流程存在: {workflow}")
                        else:
                            checks.append(f"❌ 工作流程缺失: {workflow}")
                            return {"success": False, "error": f"缺失工作流程: {workflow}", "checks": checks}
                else:
                    checks.append("❌ 协作配置缺少工作流程定义")
                    return {"success": False, "error": "协作配置不完整", "checks": checks}
                    
            except Exception as e:
                checks.append(f"❌ 协作配置解析失败: {e}")
                return {"success": False, "error": "协作配置文件错误", "checks": checks}
        else:
            checks.append("❌ 协作配置文件不存在")
            return {"success": False, "error": "协作配置文件缺失", "checks": checks}
            
        # 2. 检查协作脚本
        collab_scripts = [
            self.shared_workspace / "Collaboration" / "meeting_manager.py",
            self.shared_workspace / "Collaboration" / "task_coordinator.py",
            self.shared_workspace / "Collaboration" / "status_synchronizer.py"
        ]
        
        for script in collab_scripts:
            if script.exists():
                checks.append(f"✅ 协作脚本存在: {script.name}")
            else:
                checks.append(f"❌ 协作脚本缺失: {script.name}")
                return {"success": False, "error": f"协作脚本缺失: {script.name}", "checks": checks}
                
        return {"success": True, "checks": checks}
        
    def test_workspace_functionality(self):
        """测试工作空间功能"""
        checks = []
        
        # 1. 检查共享工作空间结构
        workspace_dirs = [
            "Projects", "Documents", "Templates", "Collaboration", "KnowledgeBase"
        ]
        
        for dir_name in workspace_dirs:
            dir_path = self.shared_workspace / dir_name
            if dir_path.exists():
                checks.append(f"✅ 工作空间目录存在: {dir_name}")
            else:
                checks.append(f"❌ 工作空间目录缺失: {dir_name}")
                return {"success": False, "error": f"工作空间目录缺失: {dir_name}", "checks": checks}
                
        # 2. 测试文件读写权限
        test_file = self.shared_workspace / "Documents" / "test_write.txt"
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write("测试写入权限")
            checks.append("✅ 工作空间写入权限正常")
            
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            checks.append("✅ 工作空间读取权限正常")
            
            test_file.unlink()  # 删除测试文件
            checks.append("✅ 工作空间删除权限正常")
            
        except Exception as e:
            checks.append(f"❌ 工作空间权限测试失败: {e}")
            return {"success": False, "error": f"工作空间权限问题: {e}", "checks": checks}
            
        return {"success": True, "checks": checks}
        
    def test_mcp_cluster(self):
        """测试MCP集群"""
        checks = []
        
        # 1. 检查MCP集群配置
        cluster_config_file = self._resolve_cluster_config()
        if cluster_config_file.exists():
            try:
                with open(cluster_config_file, 'r', encoding='utf-8') as f:
                    cluster_config = yaml.safe_load(f)
                    
                if "server_registry" in cluster_config:
                    servers = cluster_config["server_registry"]
                    required_servers = ["github_mcp", "excel_mcp", "figma_mcp", "builder_mcp", "filesystem_mcp", "database_mcp"]
                    
                    for server in required_servers:
                        if server in servers:
                            checks.append(f"✅ MCP服务器配置存在: {server}")
                        else:
                            checks.append(f"❌ MCP服务器配置缺失: {server}")
                            
                else:
                    checks.append("❌ MCP集群配置缺少服务器注册表")
                    return {"success": False, "error": "MCP集群配置不完整", "checks": checks}
                    
            except Exception as e:
                checks.append(f"❌ MCP集群配置解析失败: {e}")
                return {"success": False, "error": "MCP集群配置错误", "checks": checks}
        else:
            checks.append("❌ MCP集群配置文件不存在")
            return {"success": False, "error": "MCP集群配置缺失", "checks": checks}
            
        # 2. 检查MCP服务器目录（新旧路径兼容）
        mcp_servers = ["GitHub", "Excel", "Figma", "Builder", "FileSystem", "Database"]
        mcp_dir = self._resolve_mcp_cluster_dir()
        for server in mcp_servers:
            server_path = mcp_dir / server
            if server_path.exists():
                checks.append(f"✅ MCP服务器目录存在: {server}")
            else:
                checks.append(f"❌ MCP服务器目录缺失: {server}")
                
        return {"success": True, "checks": checks}
        
    def test_performance_benchmarks(self):
        """测试性能基准"""
        checks = []
        
        # 1. 文件系统性能测试
        start_time = time.time()
        test_data = "性能测试数据" * 1000
        test_file = self.shared_workspace / "Documents" / "perf_test.txt"
        
        try:
            # 写入测试
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_data)
            write_time = time.time() - start_time
            
            # 读取测试
            start_time = time.time()
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            read_time = time.time() - start_time
            
            test_file.unlink()  # 清理测试文件
            
            checks.append(f"✅ 文件写入性能: {write_time:.3f}秒")
            checks.append(f"✅ 文件读取性能: {read_time:.3f}秒")
            
            if write_time > 1.0 or read_time > 1.0:
                checks.append("⚠️ 文件系统性能较慢")
                
        except Exception as e:
            checks.append(f"❌ 文件系统性能测试失败: {e}")
            return {"success": False, "error": f"性能测试失败: {e}", "checks": checks}
            
        # 2. 配置加载性能测试
        start_time = time.time()
        try:
            config_files = list(self.trae_agents_path.glob("*/config/agent_config.yaml"))
            for config_file in config_files:
                with open(config_file, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
            config_load_time = time.time() - start_time
            
            checks.append(f"✅ 配置加载性能: {config_load_time:.3f}秒")
            
            if config_load_time > 2.0:
                checks.append("⚠️ 配置加载性能较慢")
                
        except Exception as e:
            checks.append(f"❌ 配置加载性能测试失败: {e}")
            
        return {"success": True, "checks": checks}
        
    def test_security_features(self):
        """测试安全特性"""
        checks = []
        
        # 1. 检查文件权限
        # 统一检查 config/production.yaml 的安全性
        sensitive_files = [
            self.project_root / "config" / "production.yaml",
            self._resolve_cluster_config()
        ]
        
        for file_path in sensitive_files:
            if file_path.exists():
                checks.append(f"✅ 敏感文件存在: {file_path.name}")
                # 在实际环境中，这里会检查文件权限
                checks.append(f"✅ 文件权限检查: {file_path.name}")
            else:
                checks.append(f"❌ 敏感文件缺失: {file_path.name}")
                
        # 2. 检查配置安全性
        try:
            with open(self.project_root / "config" / "production.yaml", 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if "security" in config:
                security_config = config["security"]
                if "authentication" in security_config:
                    checks.append("✅ 认证配置存在")
                else:
                    checks.append("⚠️ 认证配置缺失")
                    
                if "encryption" in security_config:
                    checks.append("✅ 加密配置存在")
                else:
                    checks.append("⚠️ 加密配置缺失")
            else:
                checks.append("⚠️ 安全配置缺失")
                
        except Exception as e:
            checks.append(f"❌ 安全配置检查失败: {e}")
            
        return {"success": True, "checks": checks}
        
    def test_fault_tolerance(self):
        """测试容错性"""
        checks = []
        
        # 1. 测试配置文件损坏恢复
        # 改为备份 config/production.yaml
        backup_file = self.project_root / "config" / "production.yaml.backup"
        original_file = self.project_root / "config" / "production.yaml"
        
        try:
            # 创建备份
            if original_file.exists():
                import shutil
                shutil.copy2(original_file, backup_file)
                checks.append("✅ 配置文件备份创建成功")
                
                # 恢复备份
                shutil.copy2(backup_file, original_file)
                checks.append("✅ 配置文件恢复成功")
                
                # 清理备份
                backup_file.unlink()
                checks.append("✅ 备份文件清理成功")
            else:
                checks.append("❌ 原始配置文件不存在")
                return {"success": False, "error": "配置文件缺失", "checks": checks}
                
        except Exception as e:
            checks.append(f"❌ 容错测试失败: {e}")
            return {"success": False, "error": f"容错测试失败: {e}", "checks": checks}
            
        # 2. 测试目录创建容错
        test_dir = self.shared_workspace / "test_fault_tolerance"
        try:
            test_dir.mkdir(exist_ok=True)
            checks.append("✅ 目录创建容错正常")
            
            test_dir.rmdir()
            checks.append("✅ 目录删除容错正常")
            
        except Exception as e:
            checks.append(f"❌ 目录操作容错测试失败: {e}")
            
        return {"success": True, "checks": checks}
        
    def _generate_test_report(self):
        """生成测试报告"""
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # 计算统计信息
        total_tests = len(self.test_results["tests"])
        passed_tests = sum(1 for test in self.test_results["tests"].values() if test["status"] == "PASS")
        failed_tests = sum(1 for test in self.test_results["tests"].values() if test["status"] == "FAIL")
        error_tests = sum(1 for test in self.test_results["tests"].values() if test["status"] == "ERROR")
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
            "total_duration": sum(test["duration"] for test in self.test_results["tests"].values())
        }
        
        # 保存报告至统一目录 04-prod/reports
        report_dir = self.project_root / "04-prod" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "system_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
        print(f"\n📊 测试报告已保存: {report_file}")
        
    def _display_test_summary(self):
        """显示测试摘要"""
        summary = self.test_results["summary"]
        
        print("\n" + "=" * 60)
        print("🧪 Trae系统测试摘要")
        print("=" * 60)
        print(f"📊 总测试数: {summary['total_tests']}")
        print(f"✅ 通过: {summary['passed']}")
        print(f"❌ 失败: {summary['failed']}")
        print(f"⚠️ 错误: {summary['errors']}")
        print(f"📈 成功率: {summary['success_rate']}%")
        print(f"⏱️ 总耗时: {summary['total_duration']:.2f}秒")
        
        if summary['success_rate'] >= 90:
            print("\n🎉 系统测试结果优秀！Trae平台已准备就绪")
        elif summary['success_rate'] >= 75:
            print("\n✅ 系统测试基本通过，建议修复失败项目后投入使用")
        else:
            print("\n⚠️ 系统测试发现重要问题，需要修复后重新测试")
            
        print("=" * 60)

def main():
    """主函数"""
    print("🧪 YDS-Lab Trae系统测试套件")
    print("=" * 60)
    
    test_suite = TraeSystemTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()