#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 集成验证器
用途：在统一迁移到 tools/mcp/servers 后，验证集群配置、服务器目录、端口唯一性与依赖安装状态（仅新路径）。
输出：JSON 与 Markdown 报告，位于 tools/mcp/mcp_integration_report.*
"""

import os
import json
import yaml
import importlib
from pathlib import Path
from datetime import datetime


BUILTIN_DEPS = {"sqlite3", "pathlib", "shutil"}
ALTERNATE_IMPORT_NAMES = {
    # 常见包名到导入名映射
    "pillow": ["PIL"],
    "PyGithub": ["github"],
    "gitpython": ["git"],
    # Figma 生态的可能导入名（社区包差异较大）
    "figma-api": ["figma", "figma_api", "figma_python", "pyfigma", "figmapi", "figma_client"],
}


class MCPIntegrationValidator:
    def __init__(self, project_root: Path | None = None):
        if project_root is None:
            # tools/mcp/mcp_integration_validator.py -> tools/mcp -> tools -> project root
            project_root = Path(__file__).parents[2]
        self.project_root = Path(project_root)
        self.new_mcp_dir = self.project_root / "tools" / "mcp" / "servers"

        # 报告输出位置
        self.report_json = self.project_root / "tools" / "mcp" / "mcp_integration_report.json"
        self.report_md = self.project_root / "tools" / "mcp" / "mcp_integration_report.md"

    def resolve_cluster_config(self) -> Path:
        p = self.new_mcp_dir / "cluster_config.yaml"
        return p

    def load_config(self) -> dict:
        cfg_path = self.resolve_cluster_config()
        if not cfg_path.exists():
            raise FileNotFoundError(f"未找到 MCP 集群配置文件：{cfg_path}（仅支持 tools/mcp/servers）")
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def validate_server_paths_and_executables(self, cfg: dict) -> dict:
        results = {"success": True, "details": []}
        registry = cfg.get("server_registry", {})
        for key, server in registry.items():
            rel_path = server.get("path")
            exe_name = server.get("executable")
            server_dir = self.project_root / rel_path if rel_path else None

            dir_ok = server_dir and server_dir.exists()
            exe_ok = dir_ok and exe_name and (server_dir / exe_name).exists()

            results["details"].append({
                "server": key,
                "path": str(server_dir) if server_dir else None,
                "executable": exe_name,
                "dir_exists": bool(dir_ok),
                "executable_exists": bool(exe_ok),
            })

            if not dir_ok or not exe_ok:
                results["success"] = False

        return results

    def validate_ports_unique(self, cfg: dict) -> dict:
        results = {"success": True, "details": []}
        registry = cfg.get("server_registry", {})
        used_ports = {}
        for key, server in registry.items():
            port = server.get("port")
            if port is None:
                results["details"].append({"server": key, "issue": "缺少端口配置"})
                results["success"] = False
                continue
            if port in used_ports:
                results["details"].append({"server": key, "issue": f"端口 {port} 与 {used_ports[port]} 冲突"})
                results["success"] = False
            else:
                used_ports[port] = key
        return results

    def _try_import(self, name: str) -> bool:
        try:
            importlib.import_module(name)
            return True
        except Exception:
            return False

    def validate_dependencies(self, cfg: dict) -> dict:
        results = {"success": True, "details": []}
        registry = cfg.get("server_registry", {})
        for key, server in registry.items():
            deps = server.get("dependencies", []) or []
            missing = []
            for dep in deps:
                if dep in BUILTIN_DEPS:
                    continue  # 内置模块不做安装校验

                # 直接尝试导入
                if self._try_import(dep):
                    continue

                # 尝试别名导入
                aliases = ALTERNATE_IMPORT_NAMES.get(dep, [])
                alias_ok = False
                for alias in aliases:
                    if self._try_import(alias):
                        alias_ok = True
                        break
                if not alias_ok:
                    missing.append(dep)

            results["details"].append({
                "server": key,
                "missing_dependencies": missing,
            })
            if missing:
                results["success"] = False

        return results

    def run(self) -> dict:
        summary = {
            "start_time": datetime.now().isoformat(),
            "checks": {},
            "success": True,
        }

        try:
            cfg = self.load_config()
            summary["config_path"] = str(self.resolve_cluster_config())
        except Exception as e:
            summary["success"] = False
            summary["error"] = f"加载配置失败: {e}"
            return summary

        checks = {
            "paths_and_executables": self.validate_server_paths_and_executables(cfg),
            "ports_unique": self.validate_ports_unique(cfg),
            "dependencies": self.validate_dependencies(cfg),
        }
        summary["checks"] = checks
        summary["success"] = all(c.get("success", False) for c in checks.values())
        summary["end_time"] = datetime.now().isoformat()

        # 写入报告
        self._write_reports(summary)
        return summary

    def _write_reports(self, summary: dict) -> None:
        # JSON
        self.report_json.parent.mkdir(parents=True, exist_ok=True)
        with open(self.report_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Markdown
        lines = []
        lines.append("# MCP 集成验证报告")
        lines.append("")
        lines.append(f"- 开始时间: {summary.get('start_time')}")
        lines.append(f"- 结束时间: {summary.get('end_time')}")
        lines.append(f"- 配置文件: {summary.get('config_path')}")
        lines.append(f"- 总体结果: {'✅ 通过' if summary.get('success') else '❌ 未通过'}")
        lines.append("")

        checks = summary.get("checks", {})
        # 路径与可执行文件
        pae = checks.get("paths_and_executables", {})
        lines.append("## 服务器路径与可执行文件")
        lines.append(f"- 结果: {'✅ 通过' if pae.get('success') else '❌ 未通过'}")
        for d in pae.get("details", []):
            lines.append(f"  - {d['server']}: 目录={'✅' if d['dir_exists'] else '❌'} 可执行={'✅' if d['executable_exists'] else '❌'} ({d['executable']})")
        lines.append("")

        # 端口唯一性
        pu = checks.get("ports_unique", {})
        lines.append("## 端口唯一性")
        lines.append(f"- 结果: {'✅ 通过' if pu.get('success') else '❌ 未通过'}")
        for d in pu.get("details", []):
            lines.append(f"  - {d}")
        lines.append("")

        # 依赖安装状态
        deps = checks.get("dependencies", {})
        lines.append("## 依赖安装状态")
        lines.append(f"- 结果: {'✅ 通过' if deps.get('success') else '❌ 未通过'}")
        for d in deps.get("details", []):
            miss = d.get("missing_dependencies", [])
            if miss:
                lines.append(f"  - {d['server']}: 缺失依赖 -> {', '.join(miss)}")
            else:
                lines.append(f"  - {d['server']}: 依赖完整")
        lines.append("")

        with open(self.report_md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main():
    print("🔍 运行 MCP 集成验证器（新路径优先，兼容旧路径）...")
    validator = MCPIntegrationValidator()
    result = validator.run()
    print(f"✅ 验证完成，结果: {'通过' if result.get('success') else '未通过'}")
    print(f"📄 报告(JSON): {validator.report_json}")
    print(f"📄 报告(MD):   {validator.report_md}")


if __name__ == "__main__":
    main()