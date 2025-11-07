#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将一条测试提醒写入 LongMemory 的持久化文件，用于端到端验证。
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# 保证 tools/LongMemory 在 import 路径中（支持从仓库根或本目录执行）
try:
    repo_root = Path(__file__).resolve().parents[2]
    lm_dir = repo_root / 'tools' / 'LongMemory'
    if str(lm_dir) not in sys.path:
        sys.path.insert(0, str(lm_dir))
except Exception:
    pass

from proactive_reminder import ProactiveReminder

# 引入文件锁，避免测试脚本在并发场景下破坏持久化文件
try:
    from file_lock import FileLock
except Exception:
    try:
        from .file_lock import FileLock
    except Exception:
        FileLock = None


def ensure_dir(p):
    d = os.path.dirname(p)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _resolve_memory_path() -> str:
    """解析测试写入的持久化路径：
    优先环境变量 YDS_LONGMEMORY_STORAGE_PATH/LONGMEMORY_PATH，其次仓库默认路径 logs/longmemory/lm_records.json。
    支持相对路径（相对仓库根目录）。
    """
    env_path = os.environ.get("YDS_LONGMEMORY_STORAGE_PATH") or os.environ.get("LONGMEMORY_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            try:
                base = Path.cwd()
            except Exception:
                base = Path(__file__).resolve().parents[2]
            p = base / p
        return str(p)
    try:
        base = Path.cwd()
    except Exception:
        base = Path(__file__).resolve().parents[2]
    return str(base / 'logs' / 'longmemory' / 'lm_records.json')


def main():
    # 统一使用新的长记忆持久化文件，已与 Trae Memory MCP 的 memory.json 解耦
    memory_path = _resolve_memory_path()
    ensure_dir(memory_path)

    pr = ProactiveReminder()
    pr.memory_path = memory_path

    # 构造一条测试提醒
    reminder = {
        "id": "unit-test-" + datetime.now().strftime("%H%M%S"),
        "title": "单元测试提醒",
        "message": "用于验证 LongMemory 持久化写入",
        "type": "best_practice",
        "context": {"file_path": "tools/LongMemory/test_best_practice.py"},
        "timestamp": datetime.now().isoformat(),
        "acknowledged": False,
        "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
    }

    # 加锁并原子写入，避免并发破坏
    try:
        if FileLock:
            with FileLock(memory_path):
                if os.path.exists(memory_path):
                    with open(memory_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    # 使用 LongMemory 标准结构
                    data = {"general": {}, "memories": []}

                key = f"proactive_reminder_test_{int(datetime.now().timestamp())}"
                data["general"][key] = {"timestamp": reminder["timestamp"], "type": "proactive_reminder", "data": reminder}

                tmp_path = f"{memory_path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, memory_path)
        else:
            if os.path.exists(memory_path):
                with open(memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"general": {}, "memories": []}
            key = f"proactive_reminder_test_{int(datetime.now().timestamp())}"
            data["general"][key] = {"timestamp": reminder["timestamp"], "type": "proactive_reminder", "data": reminder}
            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        print("ok: true")
        print("path:", memory_path)
    except Exception as e:
        print("ok: false")
        print("error:", str(e))


if __name__ == "__main__":
    main()