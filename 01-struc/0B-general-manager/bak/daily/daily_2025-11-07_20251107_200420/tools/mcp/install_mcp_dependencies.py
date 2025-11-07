#!/usr/bin/env python3
"""
MCP 依赖安装管理脚本
- 读取 tools/mcp/servers/master_requirements.txt（由健康检查生成）或 cluster_config.yaml
- 汇总依赖并过滤内置模块
- 支持 dry-run（默认）：仅输出安装计划，不执行安装
- 可通过 --install 执行实际安装
"""

import argparse
import subprocess
import sys
from pathlib import Path
import yaml

BASE_PATH = Path("S:/YDS-Lab")
SERVERS_DIR = BASE_PATH / "tools" / "mcp" / "servers"
MASTER_REQ = SERVERS_DIR / "master_requirements.txt"
CONFIG_YAML = SERVERS_DIR / "cluster_config.yaml"

# 过滤内置/不需要通过 pip 安装的包
BUILTIN_SKIP = {
    "sqlite3", "pathlib", "shutil"
}

# 特殊包的导入名与安装名映射（导入测试使用左侧，pip 安装使用右侧）
IMPORT_NAME_MAP = {
    "PyGithub": "github",
    "pillow": "PIL",
    "gitpython": "git",
    "pyyaml": "yaml"
}

# 安装名称的候选映射（某些生态包存在命名差异）
INSTALL_FALLBACKS = {
    "figma-api": ["figma-api", "figma-python", "pyfigma"],
}

def parse_requirements() -> list[str]:
    deps: set[str] = set()
    if MASTER_REQ.exists():
        for line in MASTER_REQ.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                deps.add(line)
    elif CONFIG_YAML.exists():
        cfg = yaml.safe_load(CONFIG_YAML.read_text(encoding="utf-8"))
        servers = (cfg or {}).get("server_registry", {})
        for srv in servers.values():
            for dep in srv.get("dependencies", []):
                deps.add(dep)
    else:
        print("⚠️ 未找到依赖来源（master_requirements.txt 或 cluster_config.yaml）")
    # 过滤内置
    deps = {d for d in deps if d.lower() not in BUILTIN_SKIP}
    return sorted(deps)

def is_importable(dep_name: str) -> bool:
    # 根据映射选择导入名
    import_name = IMPORT_NAME_MAP.get(dep_name, dep_name)
    try:
        __import__(import_name)
        return True
    except Exception:
        return False

def pip_install(package: str) -> bool:
    print(f"➡️ 安装: {package}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {package} - {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="MCP 依赖安装管理")
    parser.add_argument("--install", action="store_true", help="执行实际安装（默认仅展示计划）")
    args = parser.parse_args()

    deps = parse_requirements()
    if not deps:
        print("ℹ️ 无待安装依赖。")
        return

    print("\n📦 依赖安装计划（基于 master_requirements.txt）：")
    for d in deps:
        status = "已安装" if is_importable(d) else "未安装"
        print(f"- {d}: {status}")

    if not args.install:
        print("\n🔎 Dry-run 模式：不执行安装。若需要安装，请添加 --install 参数。")
        return

    print("\n🔧 开始安装缺失依赖...")
    for d in deps:
        if is_importable(d):
            continue
        # 常规安装
        if pip_install(d):
            continue
        # 尝试候选安装名
        for alt in INSTALL_FALLBACKS.get(d, []):
            if pip_install(alt):
                break
        else:
            print(f"⚠️ 依赖安装未完成，请手动确认包名：{d}")

    print("\n✅ 依赖安装流程结束。建议重新运行 mcp_health_checker 验证健康状态。")

if __name__ == "__main__":
    main()