#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LongMemory 事件记录命令行工具（双通道：本地JSON + 可选HTTP）

用途：
- 将关键工作流事件统一写入到仓库根 logs/longmemory/lm_records.json（统一路径）
- 可选将事件通过 HTTP 上报到服务端（需提供 --http 或环境变量 LM_HTTP_ENDPOINT）

事件模型（示例）：
{
  "event_id": "uuid",
  "type": "structure_publish",
  "topic": "yds.structure",
  "source": "tools/up.py",
  "timestamp": "2025-11-07T20:58:00Z",
  "actor": "YDS-AI-Agent",
  "payload": { ... }
}

写入策略：
- 文件结构为 {"general": {}, "memories": []}
- 事件统一追加至 memories 数组，必要时初始化文件结构
- 发生结构损坏时尝试自动修复，否则重建为默认结构
"""

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yaml  # 用于读取 yds_ai_config.yaml
except Exception:
    yaml = None


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_project_root(cli_root: Optional[str] = None) -> Path:
    if cli_root:
        return Path(cli_root)
    # 通过脚本位置反推仓库根：tools/LongMemory -> tools -> repo root
    try:
        return Path(__file__).resolve().parents[2]
    except Exception:
        # 兜底：常用默认盘符路径
        return Path(os.environ.get('LM_PROJECT_ROOT', 'S:/YDS-Lab'))


def resolve_storage_path(repo_root: Path) -> Path:
    # 优先环境变量
    env_path = os.environ.get('YDS_LONGMEMORY_STORAGE_PATH') or os.environ.get('LONGMEMORY_PATH')
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = (repo_root / p).resolve()
        return p
    # 其次读取仓库配置 config/yds_ai_config.yaml
    cfg = repo_root / 'config' / 'yds_ai_config.yaml'
    if yaml and cfg.exists():
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            lm = data.get('longmemory') or {}
            storage_rel = lm.get('storage_path')
            if storage_rel:
                p = Path(storage_rel)
                if not p.is_absolute():
                    p = (repo_root / p).resolve()
                return p
        except Exception:
            pass
    # 最后兜底统一路径（仓库根 logs/longmemory/lm_records.json）
    return (repo_root / 'logs' / 'longmemory' / 'lm_records.json').resolve()


def ensure_parent_dir(path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def load_records(path: Path) -> Dict[str, Any]:
    """加载现有记录；若损坏尝试修复；若不存在则初始化。"""
    default_obj: Dict[str, Any] = {"general": {}, "memories": []}
    if not path.exists():
        ensure_parent_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_obj, f, ensure_ascii=False, indent=2)
        return default_obj
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # 尝试轻量修复：截取到最后一个右括号
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            last_brace = content.rfind('}')
            if last_brace != -1:
                trimmed = content[:last_brace+1]
                obj = json.loads(trimmed)
                # 写回修复后的内容
                with open(path, 'w', encoding='utf-8') as fw:
                    json.dump(obj, fw, ensure_ascii=False, indent=2)
                return obj
        except Exception:
            pass
        # 仍失败则重置为默认结构
        ensure_parent_dir(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_obj, f, ensure_ascii=False, indent=2)
        return default_obj


def safe_write(path: Path, obj: Dict[str, Any]) -> None:
    tmp = path.with_suffix('.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    # Windows 上用替换模式确保原子性尽可能好
    try:
        os.replace(str(tmp), str(path))
    except Exception:
        # 兜底：直接写回
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)


def post_http(endpoint: str, payload: Dict[str, Any]) -> bool:
    try:
        import urllib.request
        req = urllib.request.Request(endpoint, data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            code = resp.getcode()
            return 200 <= code < 300
    except Exception:
        return False


def build_event(
    event_type: str,
    topic: str,
    source: str,
    actor: Optional[str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "topic": topic,
        "source": source,
        "timestamp": _iso_now(),
        "actor": actor or os.environ.get('YDS_ACTOR', 'YDS-AI-Agent'),
        "payload": payload,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="LongMemory 事件记录工具")
    parser.add_argument('--type', required=True, help='事件类型，例如 structure_publish / git_commit / git_push')
    parser.add_argument('--topic', default='yds.longmemory', help='事件主题，例如 yds.structure / yds.git')
    parser.add_argument('--source', default='tools/LongMemory/record_event.py', help='事件来源，如 tools/up.py')
    parser.add_argument('--payload', help='事件载荷（JSON字符串）')
    parser.add_argument('--payload-file', help='事件载荷文件路径（JSON）')
    parser.add_argument('--http', help='可选HTTP上报端点，例如 http://127.0.0.1:8021/api/memory')
    parser.add_argument('--project-root', help='仓库根路径（可选，默认自动识别）')
    args = parser.parse_args()

    repo_root = resolve_project_root(args.project_root)
    storage = resolve_storage_path(repo_root)
    ensure_parent_dir(storage)

    # 解析载荷
    payload_obj: Dict[str, Any] = {}
    if args.payload:
        try:
            payload_obj = json.loads(args.payload)
        except Exception:
            payload_obj = {"raw": args.payload, "parse_error": True}
    elif args.payload_file:
        try:
            with open(args.payload_file, 'r', encoding='utf-8') as pf:
                payload_obj = json.load(pf)
        except Exception as e:
            payload_obj = {"payload_file": args.payload_file, "error": str(e)}

    # 构造事件
    evt = build_event(args.type, args.topic, args.source, os.environ.get('YDS_ACTOR'), payload_obj)

    # 写入本地JSON
    records = load_records(storage)
    memories = records.get('memories')
    if not isinstance(memories, list):
        records['memories'] = []
    records['memories'].append(evt)
    # 更新general元数据
    g = records.get('general') or {}
    g['last_updated'] = _iso_now()
    g['last_event_type'] = args.type
    records['general'] = g
    safe_write(storage, records)

    # 可选HTTP上报
    endpoint = args.http or os.environ.get('LM_HTTP_ENDPOINT')
    if endpoint:
        post_http(endpoint, evt)

    print(f"事件已记录: type={args.type}, storage={storage}")


if __name__ == '__main__':
    main()