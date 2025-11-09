#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LongMemory 周期性健康快照工具

功能：
- 读取 lm_records.json 的核心指标（事件总数、最后事件类型/时间）
- 写入 LongMemory 事件（lm_health_snapshot）到同一存储文件

可结合 Windows 计划任务每30分钟执行：
schtasks /Create /SC MINUTE /MO 30 /TN "YDSLab_LongMemory_Health" \
         /TR "python S:\\YDS-Lab\\tools\\LongMemory\\health_check.py" /RL LIMITED
"""

import os
from datetime import datetime

from record_event import resolve_project_root, resolve_storage_path, load_records


def main():
    repo_root = resolve_project_root()
    storage = resolve_storage_path(repo_root)
    records = load_records(storage)
    memories = records.get('memories') or []
    general = records.get('general') or {}

    last_type = general.get('last_event_type')
    last_updated = general.get('last_updated')
    count = len(memories)

    payload = {
        'memories_count': count,
        'last_event_type': last_type,
        'last_updated': last_updated,
        'snapshot_time': datetime.now().isoformat(),
    }

    # 直接调用同目录下的 record_event.py（作为模块使用）
    from record_event import build_event, safe_write
    evt = build_event(
        'lm_health_snapshot',
        'yds.longmemory',
        'tools/LongMemory/health_check.py',
        os.environ.get('YDS_ACTOR'),
        payload,
    )
    memories.append(evt)
    general['last_event_type'] = 'lm_health_snapshot'
    general['last_updated'] = payload['snapshot_time']
    records['general'] = general
    records['memories'] = memories
    safe_write(storage, records)
    print(f"LongMemory 健康快照已记录: {storage}（总事件数: {count}）")


if __name__ == '__main__':
    main()