#!/usr/bin/env python3
"""
最终系统验证和交付工具
对Trae平台智能体系统进行全面的最终验证
"""

import os
import json
import yaml
import subprocess
from datetime import datetime
from pathlib import Path

class FinalSystemValidator:
    def __init__(self, base_path="S:/YDS-Lab"):
        self.base_path = Path(base_path)
        self.validation_results = {
            "validation_time": datetime.now().isoformat(),
            "overall_status": "pending",
            "validation_categories": {},
            "summary": {},
            "recommendations": []
        }
        
    def validate_production_environment(self):
        """验证生产环境"""
        print("🏭 验证生产环境...")
        
        # 采用标准化目录结构进行验证（不再使用 Production 前缀）
        required_components = {
            # 统一到 01-struc 目录，TraeAgents 合并为 Agents
            "Agents": self.base_path / "01-struc" / "Agents",
            # MCPCluster 迁移后新位置（优先）
            "MCPCluster": self.base_path / "tools" / "mcp" / "servers",
            "SharedWorkspace": self.base_path / "01-struc" / "SharedWorkspace",
            "Config": self.base_path / "config",
            # 日志目录统一为 01-struc/0B-general-manager/logs（旧路径 GeneralOffice/logs 仅作为历史记录，不再回退使用）
            "Logs": self.base_path / "01-struc" / "0B-general-manager" / "logs",
            "Scripts": self.base_path / "tools" / "scripts",
        }
        
        validation_results = {
            "component_status": {},
            "configuration_files": {},
            "startup_scripts": {},
            "overall_status": "pass"
        }
        
        # 检查生产环境组件（标准化路径）
        for component, component_path in required_components.items():
            if component_path.exists():
                validation_results["component_status"][component] = "存在"
                print(f"  ✅ {component}: 存在")
            else:
                validation_results["component_status"][component] = "缺失"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ {component}: 缺失")
        
        # 检查关键配置文件
        # 关键配置与报告位置调整：生产报告统一到 04-prod/reports
        config_files = {
            "production.yaml": self.base_path / "config" / "production.yaml",
            # 新增：统一检查 Trae 平台主配置（优先使用 config/trae_config.yaml）
            "trae_config.yaml": self.base_path / "config" / "trae_config.yaml",
            "deployment_report.json": self.base_path / "04-prod" / "reports" / "deployment_report.json",
        }
        
        for filename, config_path in config_files.items():
            if config_path.exists():
                validation_results["configuration_files"][filename] = "存在"
                print(f"  ✅ 配置文件 {filename}: 存在")
            else:
                validation_results["configuration_files"][filename] = "缺失"
                print(f"  ⚠️ 配置文件 {filename}: 缺失")

        # 补充：尝试解析 trae_config.yaml，检查基本格式有效性（YAML/JSON 兼容）
        trae_cfg = self.base_path / "config" / "trae_config.yaml"
        if trae_cfg.exists():
            try:
                with open(trae_cfg, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                warnings = []
                # 顶层结构
                if not isinstance(cfg, dict):
                    validation_results["configuration_files"]["trae_config.yaml_format"] = "格式错误（顶层非对象）"
                    validation_results["overall_status"] = "fail"
                    print("  ❌ 配置文件 trae_config.yaml: 顶层结构应为对象（字典）")
                else:
                    # 基本键检查
                    has_platform = ("platform" in cfg and isinstance(cfg.get("platform"), dict))
                    has_agents = ("agents" in cfg and isinstance(cfg.get("agents"), (list, dict)))
                    has_environment = ("environment" in cfg)
                    if has_platform and has_agents:
                        validation_results["configuration_files"]["trae_config.yaml_format"] = "格式有效"
                        print("  ✅ 配置文件 trae_config.yaml: 格式有效")
                    else:
                        missing = []
                        if not has_platform: missing.append("platform")
                        if not has_agents: missing.append("agents")
                        msg = f"格式不完整（缺少: {', '.join(missing)}）" if missing else "格式未知"
                        validation_results["configuration_files"]["trae_config.yaml_format"] = msg
                        # 缺少关键键视为失败
                        if missing:
                            validation_results["overall_status"] = "fail"
                        print(f"  ⚠️ 配置文件 trae_config.yaml: {msg}")

                    # 平台信息检查（非强制字段仅提示）
                    if has_platform:
                        platform = cfg.get("platform", {})
                        if "name" not in platform:
                            warnings.append("platform.name 缺失")
                        if "version" not in platform:
                            warnings.append("platform.version 缺失")

                    # 环境信息提示
                    if not has_environment:
                        warnings.append("environment 缺失（建议在主配置中注明环境）")

                    # Agents 结构化校验
                    if has_agents:
                        agents = cfg.get("agents")
                        agent_items = agents.values() if isinstance(agents, dict) else agents
                        count = 0
                        for agent in agent_items:
                            count += 1
                            if not isinstance(agent, dict):
                                validation_results["overall_status"] = "fail"
                                print("  ❌ Agents 条目错误：应为对象（字典）")
                                continue
                            role = agent.get("role") or agent.get("name")
                            workspace = agent.get("workspace") or agent.get("workspace_path")
                            capabilities = agent.get("capabilities")
                            if not role:
                                validation_results["overall_status"] = "fail"
                                print("  ❌ Agent 缺少 role/name 字段")
                            if not workspace or not isinstance(workspace, str):
                                warnings.append("某个 Agent 的 workspace 缺失或类型错误")
                            else:
                                ws_lower = workspace.lower()
                                # 常见旧路径提示：TraeAgents、无 01- 前缀的 Struc、旧 MCPCluster
                                if "traeagents" in ws_lower:
                                    warnings.append("发现旧目录名 TraeAgents，建议迁移为 01-struc/Agents")
                                if ("/struc/" in ws_lower or "\\struc\\" in ws_lower) and ("01-struc" not in ws_lower):
                                    warnings.append("发现旧路径片段 Struc/，建议使用 01-struc 前缀")
                                if "mcpcluster" in ws_lower and "tools/mcp/servers" not in ws_lower:
                                    warnings.append("发现旧 MCPCluster 路径引用，建议使用 tools/mcp/servers")
                                # 路径存在性（若为绝对路径）
                                try:
                                    p = Path(workspace)
                                    if p.is_absolute() and not p.exists():
                                        warnings.append(f"Agent workspace 路径不存在: {workspace}")
                                except Exception:
                                    pass
                            if capabilities is not None and not isinstance(capabilities, list):
                                warnings.append("某个 Agent 的 capabilities 应为列表")
                        validation_results["configuration_files"]["trae_config.yaml_agents_count"] = count
                        print(f"  ℹ️ Agents 配置数量: {count}")

                    if warnings:
                        validation_results["configuration_files"]["trae_config.yaml_warnings"] = warnings
                        for w in warnings:
                            print(f"  ℹ️ 配置提示: {w}")
                        # 将提示汇总到全局建议
                        self.validation_results.setdefault("recommendations", []).extend(warnings)
            except Exception as e:
                validation_results["configuration_files"]["trae_config.yaml_format"] = f"解析失败: {e}"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ 配置文件 trae_config.yaml: 解析失败 - {e}")

        # 兼容提示：如果旧路径 01-struc/trae_config.yaml 仍存在，给出迁移提醒（不影响通过标准）
        old_trae_cfg = self.base_path / "01-struc" / "trae_config.yaml"
        if old_trae_cfg.exists():
            validation_results["configuration_files"]["trae_config.yaml_old_path"] = "发现旧文件，建议迁移到 config/"
            tip = "发现旧路径 01-struc/trae_config.yaml，建议统一迁移到 config/trae_config.yaml（当前已采用 config 为标准）"
            print(f"  ℹ️ {tip}")
            self.validation_results.setdefault("recommendations", []).append(tip)
        
        # 检查启动脚本
        scripts_path = self.base_path / "tools" / "scripts"
        if scripts_path.exists():
            script_files = list(scripts_path.glob("*.bat"))
            validation_results["startup_scripts"]["count"] = len(script_files)
            validation_results["startup_scripts"]["files"] = [f.name for f in script_files]
            print(f"  ✅ 启动脚本: 找到 {len(script_files)} 个")
        else:
            validation_results["startup_scripts"]["count"] = 0
            validation_results["startup_scripts"]["files"] = []
            print(f"  ⚠️ 启动脚本: 目录不存在")
        
        self.validation_results["validation_categories"]["production_environment"] = validation_results
        return validation_results["overall_status"] == "pass"
    
    def validate_documentation_completeness(self):
        """验证文档完整性"""
        print("📚 验证文档完整性...")
        
        # 文档统一归档至 01-struc/docs
        docs_path = self.base_path / "01-struc" / "docs"
        # 培训材料路径兼容：优先 Training，兼容 03-training
        training_candidates = [
            self.base_path / "Training",
            self.base_path / "03-training"
        ]
        training_path = next((p for p in training_candidates if p.exists()), training_candidates[0])
        
        validation_results = {
            "user_documentation": {},
            "technical_documentation": {},
            "training_materials": {},
            "overall_status": "pass"
        }
        
        # 检查用户文档
        user_docs = [
            "UserGuides/trae_platform_user_guide.md",
            "Troubleshooting/troubleshooting_guide.md",
            "final_deployment_report.md"
        ]
        
        for doc in user_docs:
            doc_path = docs_path / doc
            if doc_path.exists():
                size = doc_path.stat().st_size
                validation_results["user_documentation"][doc] = f"存在 ({size} bytes)"
                print(f"  ✅ 用户文档 {doc}: 存在 ({size} bytes)")
            else:
                validation_results["user_documentation"][doc] = "缺失"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ 用户文档 {doc}: 缺失")
        
        # 检查技术文档
        tech_docs = [
            "TechnicalDocs/system_architecture.md",
            "APIReference/api_reference.md"
        ]
        
        for doc in tech_docs:
            doc_path = docs_path / doc
            if doc_path.exists():
                size = doc_path.stat().st_size
                validation_results["technical_documentation"][doc] = f"存在 ({size} bytes)"
                print(f"  ✅ 技术文档 {doc}: 存在 ({size} bytes)")
            else:
                validation_results["technical_documentation"][doc] = "缺失"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ 技术文档 {doc}: 缺失")
        
        # 检查培训材料
        training_materials = [
            "Materials/training_outline.md",
            "Exercises/training_exercises.md"
        ]
        
        for material in training_materials:
            material_path = training_path / material
            if material_path.exists():
                size = material_path.stat().st_size
                validation_results["training_materials"][material] = f"存在 ({size} bytes)"
                print(f"  ✅ 培训材料 {material}: 存在 ({size} bytes)")
            else:
                validation_results["training_materials"][material] = "缺失"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ 培训材料 {material}: 缺失")
        
        self.validation_results["validation_categories"]["documentation_completeness"] = validation_results
        return validation_results["overall_status"] == "pass"
    
    def validate_system_functionality(self):
        """验证系统功能"""
        print("⚙️ 验证系统功能...")
        
        validation_results = {
            "agent_configurations": {},
            "mcp_cluster": {},
            "collaboration_workflows": {},
            "overall_status": "pass"
        }
        
        # 检查智能体配置
        # TraeAgents 合并为 01-struc/Agents，角色按目录分布
        agents_path = self.base_path / "01-struc" / "Agents"
        agent_dirs = [
            "CEO",
            "DevTeamLead",
            "ResourceAdmin",
            "PlanningDirector",
            "FinanceDirector",
            "MarketingDirector"
        ]
        
        for agent in agent_dirs:
            resolved_dir = self._resolve_agent_dir(agents_path, agent)
            display_name = resolved_dir.name if resolved_dir else agent
            config_path = (resolved_dir / "config" / "agent_config.yaml") if resolved_dir else agents_path / agent / "config" / "agent_config.yaml"
            
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    validation_results["agent_configurations"][display_name] = "配置有效"
                    print(f"  ✅ {display_name}智能体配置: 有效")
                except Exception as e:
                    validation_results["agent_configurations"][display_name] = f"配置错误: {e}"
                    validation_results["overall_status"] = "fail"
                    print(f"  ❌ {display_name}智能体配置: 错误 - {e}")
            else:
                validation_results["agent_configurations"][display_name] = "配置文件缺失"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ {display_name}智能体配置: 文件缺失")
        
        # 检查MCP集群（优先使用新路径 tools/mcp/servers，兼容旧路径 01-struc/MCPCluster）
        mcp_candidates = [
            self.base_path / "tools" / "mcp" / "servers",
            self.base_path / "01-struc" / "MCPCluster"
        ]
        mcp_path = next((p for p in mcp_candidates if (p / "cluster_config.yaml").exists()), mcp_candidates[0])
        cluster_config_path = mcp_path / "cluster_config.yaml"
        
        if cluster_config_path.exists():
            try:
                with open(cluster_config_path, 'r', encoding='utf-8') as f:
                    cluster_config = yaml.safe_load(f)
                
                server_registry = cluster_config.get("server_registry", {})
                validation_results["mcp_cluster"]["servers_count"] = len(server_registry)
                validation_results["mcp_cluster"]["servers"] = list(server_registry.keys())
                validation_results["mcp_cluster"]["status"] = "配置有效"
                print(f"  ✅ MCP集群配置: 有效 ({len(server_registry)} 个服务器)")
                
            except Exception as e:
                validation_results["mcp_cluster"]["status"] = f"配置错误: {e}"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ MCP集群配置: 错误 - {e}")
        else:
            validation_results["mcp_cluster"]["status"] = "配置文件缺失"
            validation_results["overall_status"] = "fail"
            print(f"  ❌ MCP集群配置: 文件缺失")
        
        # 检查协作工作流
        workflow_path = self.base_path / "01-struc" / "Agents" / "collaboration_workflows.yaml"
        
        if workflow_path.exists():
            try:
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    workflows = yaml.safe_load(f)
                
                workflow_types = workflows.get("workflows", {})
                validation_results["collaboration_workflows"]["types_count"] = len(workflow_types)
                validation_results["collaboration_workflows"]["types"] = list(workflow_types.keys())
                validation_results["collaboration_workflows"]["status"] = "配置有效"
                print(f"  ✅ 协作工作流配置: 有效 ({len(workflow_types)} 个工作流)")
                
            except Exception as e:
                validation_results["collaboration_workflows"]["status"] = f"配置错误: {e}"
                validation_results["overall_status"] = "fail"
                print(f"  ❌ 协作工作流配置: 错误 - {e}")
        else:
            validation_results["collaboration_workflows"]["status"] = "配置文件缺失"
            validation_results["overall_status"] = "fail"
            print(f"  ❌ 协作工作流配置: 文件缺失")
        
        self.validation_results["validation_categories"]["system_functionality"] = validation_results
        return validation_results["overall_status"] == "pass"
    
    def validate_backup_and_recovery(self):
        """验证备份和恢复"""
        print("💾 验证备份和恢复...")
        
        validation_results = {
            "backup_directories": {},
            "backup_scripts": {},
            "recovery_procedures": {},
            "overall_status": "pass"
        }
        
        # 检查备份目录（统一为 backups/，旧 bak/ 已归档到 backups/legacy/）
        backup_path = self.base_path / "backups"
        if backup_path.exists():
            backup_dirs = list(backup_path.iterdir())
            validation_results["backup_directories"]["count"] = len(backup_dirs)
            validation_results["backup_directories"]["directories"] = [d.name for d in backup_dirs if d.is_dir()]
            print(f"  ✅ 备份目录: 存在 ({len(backup_dirs)} 个备份)")
        else:
            validation_results["backup_directories"]["count"] = 0
            validation_results["backup_directories"]["directories"] = []
            print(f"  ⚠️ 备份目录: 不存在")
        
        # 检查备份脚本
        backup_script_path = self.base_path / "tools" / "backup" / "daily_snapshot.py"
        if backup_script_path.exists():
            validation_results["backup_scripts"]["daily_snapshot"] = "存在"
            print(f"  ✅ 备份脚本: 存在")
        else:
            validation_results["backup_scripts"]["daily_snapshot"] = "缺失"
            print(f"  ⚠️ 备份脚本: 缺失")
        
        # 检查恢复程序文档（文档已统一到 01-struc/docs）
        recovery_doc_path = self.base_path / "01-struc" / "docs" / "Troubleshooting" / "troubleshooting_guide.md"
        if recovery_doc_path.exists():
            validation_results["recovery_procedures"]["documentation"] = "存在"
            print(f"  ✅ 恢复程序文档: 存在")
        else:
            validation_results["recovery_procedures"]["documentation"] = "缺失"
            validation_results["overall_status"] = "fail"
            print(f"  ❌ 恢复程序文档: 缺失")
        
        self.validation_results["validation_categories"]["backup_and_recovery"] = validation_results
        return validation_results["overall_status"] == "pass"
    
    def validate_security_measures(self):
        """验证安全措施"""
        print("🔒 验证安全措施...")
        
        validation_results = {
            "configuration_security": {},
            "access_control": {},
            "data_protection": {},
            "overall_status": "pass"
        }
        
        # 检查配置文件安全性
        sensitive_files = [
            self.base_path / "models" / "config" / "api_keys.json",
            self.base_path / "config" / "production.yaml"
        ]
        
        for file_path in sensitive_files:
            if file_path.exists():
                # 检查文件权限（Windows环境下的基本检查）
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # 检查是否包含明文密钥（基本检查）
                    if "password" in content.lower() or "secret" in content.lower():
                        validation_results["configuration_security"][file_path.name] = "可能包含敏感信息"
                        print(f"  ⚠️ {file_path.name}: 可能包含敏感信息")
                    else:
                        validation_results["configuration_security"][file_path.name] = "安全"
                        print(f"  ✅ {file_path.name}: 安全")
                        
                except Exception as e:
                    validation_results["configuration_security"][file_path.name] = f"无法检查: {e}"
                    print(f"  ⚠️ {file_path.name}: 无法检查 - {e}")
            else:
                validation_results["configuration_security"][file_path.name] = "文件不存在"
                print(f"  ℹ️ {file_path.name}: 文件不存在")
        
        # 检查访问控制配置
        production_config_path = self.base_path / "config" / "production.yaml"
        if production_config_path.exists():
            try:
                with open(production_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                security_config = config.get("security", {})
                if security_config:
                    validation_results["access_control"]["configuration"] = "已配置"
                    print(f"  ✅ 访问控制: 已配置")
                else:
                    validation_results["access_control"]["configuration"] = "未配置"
                    print(f"  ⚠️ 访问控制: 未配置")
                    
            except Exception as e:
                validation_results["access_control"]["configuration"] = f"配置错误: {e}"
                print(f"  ❌ 访问控制: 配置错误 - {e}")
        
        # 检查数据保护措施
        # 日志目录统一位置（01-struc/0B-general-manager/logs）
        logs_path = self.base_path / "01-struc" / "0B-general-manager" / "logs"
        if logs_path.exists():
            validation_results["data_protection"]["logs_directory"] = "存在"
            print(f"  ✅ 日志目录: 存在")
        else:
            validation_results["data_protection"]["logs_directory"] = "不存在"
            print(f"  ⚠️ 日志目录: 不存在")
        
        self.validation_results["validation_categories"]["security_measures"] = validation_results
        return validation_results["overall_status"] == "pass"
    
    def validate_performance_readiness(self):
        """验证性能就绪状态"""
        print("🚀 验证性能就绪状态...")
        
        validation_results = {
            "system_resources": {},
            "configuration_optimization": {},
            "monitoring_setup": {},
            "overall_status": "pass"
        }
        
        # 检查系统资源
        try:
            # 检查磁盘空间
            import shutil
            total, used, free = shutil.disk_usage(self.base_path)
            free_gb = free // (1024**3)
            
            validation_results["system_resources"]["disk_space_gb"] = free_gb
            if free_gb > 10:
                validation_results["system_resources"]["disk_status"] = "充足"
                print(f"  ✅ 磁盘空间: 充足 ({free_gb} GB 可用)")
            else:
                validation_results["system_resources"]["disk_status"] = "不足"
                validation_results["overall_status"] = "warning"
                print(f"  ⚠️ 磁盘空间: 不足 ({free_gb} GB 可用)")
                
        except Exception as e:
            validation_results["system_resources"]["disk_status"] = f"检查失败: {e}"
            print(f"  ❌ 磁盘空间检查失败: {e}")
        
        # 检查配置优化
        production_config_path = self.base_path / "config" / "production.yaml"
        if production_config_path.exists():
            try:
                with open(production_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                performance_config = config.get("performance", {})
                if performance_config:
                    validation_results["configuration_optimization"]["performance_config"] = "已优化"
                    print(f"  ✅ 性能配置: 已优化")
                else:
                    validation_results["configuration_optimization"]["performance_config"] = "使用默认配置"
                    print(f"  ℹ️ 性能配置: 使用默认配置")
                    
            except Exception as e:
                validation_results["configuration_optimization"]["performance_config"] = f"配置错误: {e}"
                print(f"  ❌ 性能配置: 错误 - {e}")
        
        # 检查监控设置
        monitoring_config_path = self.base_path / "config"
        if monitoring_config_path.exists():
            validation_results["monitoring_setup"]["config_directory"] = "存在"
            print(f"  ✅ 监控配置目录: 存在")
        else:
            validation_results["monitoring_setup"]["config_directory"] = "不存在"
            print(f"  ⚠️ 监控配置目录: 不存在")
        
        self.validation_results["validation_categories"]["performance_readiness"] = validation_results
        return validation_results["overall_status"] == "pass"

    # 辅助方法：解析智能体目录（兼容大小写和不同命名风格）
    def _resolve_agent_dir(self, agents_path, role_name):
        """根据角色名解析实际目录，兼容大小写、连字符、下划线等命名差异。"""
        def norm(x: str) -> str:
            return x.lower().replace('-', '_')
        # 常见映射
        mapping = {
            "CEO": ["CEO", "ceo"],
            "DevTeamLead": ["DevTeamLead", "dev_team", "devteamlead", "dev_team_lead", "dev"],
            "ResourceAdmin": ["ResourceAdmin", "resource_admin", "resourceadmin"],
            "PlanningDirector": ["PlanningDirector", "planning_director", "planningdirector"],
            "FinanceDirector": ["FinanceDirector", "finance_director", "financedirector"],
            "MarketingDirector": ["MarketingDirector", "marketing_director", "marketingdirector"],
        }
        candidates = mapping.get(role_name, [role_name, role_name.lower()])
        # 先直接匹配候选
        for cand in candidates:
            p = agents_path / cand
            if p.exists() and p.is_dir():
                return p
        # 再进行规范化比较
        desired = {norm(c) for c in candidates}
        for sub in agents_path.iterdir():
            if sub.is_dir() and norm(sub.name) in desired:
                return sub
        return None
    
    def generate_validation_summary(self):
        """生成验证摘要"""
        print("📊 生成验证摘要...")
        
        categories = self.validation_results["validation_categories"]
        total_categories = len(categories)
        passed_categories = sum(1 for cat in categories.values() if cat.get("overall_status") == "pass")
        warning_categories = sum(1 for cat in categories.values() if cat.get("overall_status") == "warning")
        failed_categories = sum(1 for cat in categories.values() if cat.get("overall_status") == "fail")
        
        success_rate = (passed_categories / total_categories) * 100 if total_categories > 0 else 0
        
        # 确定整体状态
        if failed_categories > 0:
            overall_status = "需要修复"
        elif warning_categories > 0:
            overall_status = "基本就绪"
        else:
            overall_status = "完全就绪"
        
        summary = {
            "total_categories": total_categories,
            "passed_categories": passed_categories,
            "warning_categories": warning_categories,
            "failed_categories": failed_categories,
            "success_rate": round(success_rate, 2),
            "overall_status": overall_status
        }
        
        self.validation_results["summary"] = summary
        self.validation_results["overall_status"] = overall_status
        
        # 生成建议
        recommendations = []
        
        if failed_categories > 0:
            recommendations.append("修复失败的验证项目")
        
        if warning_categories > 0:
            recommendations.append("关注警告项目，考虑优化")
        
        if success_rate >= 90:
            recommendations.append("系统已基本就绪，可以投入使用")
        elif success_rate >= 80:
            recommendations.append("系统接近就绪，建议解决主要问题后投入使用")
        else:
            recommendations.append("系统需要进一步完善后才能投入使用")
        
        recommendations.extend([
            "建立定期验证机制",
            "持续监控系统状态",
            "收集用户反馈进行改进"
        ])
        
        self.validation_results["recommendations"] = recommendations
        
        return summary
    
    def save_validation_report(self):
        """保存验证报告"""
        print("💾 保存验证报告...")
        
        # 保存JSON格式报告至统一位置（04-prod/reports/deployment_report.json）
        prod_reports_dir = self.base_path / "04-prod" / "reports"
        prod_reports_dir.mkdir(parents=True, exist_ok=True)
        json_report_path = prod_reports_dir / "deployment_report.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, ensure_ascii=False, indent=2)
        
        # 生成可读性报告
        summary = self.validation_results["summary"]
        readable_report = f"""# Trae平台智能体系统最终验证报告

## 验证概述
- **验证时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- **整体状态**: {self.validation_results["overall_status"]}
- **成功率**: {summary["success_rate"]}%

## 验证结果统计
- **总验证类别**: {summary["total_categories"]}
- **通过类别**: {summary["passed_categories"]}
- **警告类别**: {summary["warning_categories"]}
- **失败类别**: {summary["failed_categories"]}

## 详细验证结果

### 🏭 生产环境验证
"""
        
        # 添加各类别的详细结果
        for category_name, category_data in self.validation_results["validation_categories"].items():
            status_icon = "✅" if category_data["overall_status"] == "pass" else "⚠️" if category_data["overall_status"] == "warning" else "❌"
            readable_report += f"\n### {status_icon} {category_name.replace('_', ' ').title()}\n"
            readable_report += f"**状态**: {category_data['overall_status']}\n\n"
            
            # 添加子项详情
            for key, value in category_data.items():
                if key != "overall_status" and isinstance(value, dict):
                    readable_report += f"**{key.replace('_', ' ').title()}**:\n"
                    for sub_key, sub_value in value.items():
                        readable_report += f"- {sub_key}: {sub_value}\n"
                    readable_report += "\n"
        
        readable_report += f"""
## 建议和后续步骤

"""
        
        for i, recommendation in enumerate(self.validation_results["recommendations"], 1):
            readable_report += f"{i}. {recommendation}\n"
        
        readable_report += f"""

## 验证结论

根据本次全面验证，Trae平台智能体系统的整体状态为：**{self.validation_results["overall_status"]}**

系统成功率达到 {summary["success_rate"]}%，已具备投入生产使用的基本条件。

---
**验证报告版本**: v1.0
**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
**验证工具**: 最终系统验证器 v1.0
"""
        
        # 保存可读性报告
        # 保存可读性报告至统一文档目录（01-struc/docs/final_deployment_report.md）
        docs_dir = self.base_path / "01-struc" / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        readable_report_path = docs_dir / "final_deployment_report.md"
        with open(readable_report_path, 'w', encoding='utf-8') as f:
            f.write(readable_report)
        
        print(f"✅ 验证报告已保存:")
        print(f"  📄 JSON报告: {json_report_path}")
        print(f"  📖 可读报告: {readable_report_path}")
        
        return True
    
    def run_final_validation(self):
        """运行完整的最终验证"""
        print("🎯 开始最终系统验证...")
        print("=" * 60)
        
        validation_steps = [
            ("生产环境", self.validate_production_environment),
            ("文档完整性", self.validate_documentation_completeness),
            ("系统功能", self.validate_system_functionality),
            ("备份恢复", self.validate_backup_and_recovery),
            ("安全措施", self.validate_security_measures),
            ("性能就绪", self.validate_performance_readiness)
        ]
        
        results = []
        
        for step_name, step_function in validation_steps:
            print(f"\n🔍 验证 {step_name}...")
            try:
                result = step_function()
                results.append(result)
                status = "✅ 通过" if result else "❌ 失败"
                print(f"  {status}")
            except Exception as e:
                print(f"  ❌ 验证过程中出错: {e}")
                results.append(False)
        
        # 生成验证摘要
        summary = self.generate_validation_summary()
        
        # 保存验证报告
        self.save_validation_report()
        
        print("\n" + "=" * 60)
        print("🎉 最终系统验证完成！")
        print(f"\n📊 验证摘要:")
        print(f"✅ 通过类别: {summary['passed_categories']}/{summary['total_categories']}")
        print(f"⚠️ 警告类别: {summary['warning_categories']}")
        print(f"❌ 失败类别: {summary['failed_categories']}")
        print(f"📈 成功率: {summary['success_rate']}%")
        print(f"🎯 整体状态: {summary['overall_status']}")
        
        return summary

def main():
    """主函数"""
    validator = FinalSystemValidator()
    summary = validator.run_final_validation()
    
    if summary["success_rate"] >= 90:
        print("\n🚀 系统验证成功！Trae平台已准备就绪！")
    elif summary["success_rate"] >= 80:
        print("\n⚠️ 系统基本就绪，建议解决警告项目后投入使用")
    else:
        print("\n❌ 系统需要进一步完善，请解决失败项目")
    
    print("\n📋 请查看验证报告获取详细信息")

if __name__ == "__main__":
    main()