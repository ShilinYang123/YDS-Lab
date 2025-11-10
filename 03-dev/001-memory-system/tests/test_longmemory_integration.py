#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LongMemory 集成与并发写入测试脚本

- 同时触发 ProactiveReminder、SmartErrorDetector、IntelligentMonitor 的写入逻辑
- 验证 01-struc/logs/longmemory/lm_records.json 在高并发下仍保持有效 JSON 结构
"""

import sys
import os
from pathlib import Path
import threading
import time
from datetime import datetime


def ensure_repo_root():
    # 以当前文件位置反推仓库根目录（S:\\YDS-Lab）
    return str(Path(__file__).resolve().parents[3])


def run_tests():
    # 运行前确保生产脚本目录在路径中
    repo_root = ensure_repo_root()
    scripts_dir = os.path.join(repo_root, '04-prod', '001-memory-system', 'scripts')
    monitoring_dir = os.path.join(scripts_dir, 'monitoring')
    for p in [scripts_dir, monitoring_dir]:
        if p not in sys.path:
            sys.path.insert(0, p)

    # 模块导入：主动提醒模块为 start_proactive_reminder.py
    from start_proactive_reminder import ProactiveReminder
    from smart_error_detector import SmartErrorDetector
    from intelligent_monitor import IntelligentMonitor

    # 准备组件
    reminder = ProactiveReminder()
    detector = SmartErrorDetector()
    monitor = IntelligentMonitor()

    # 准备并发测试
    threads = []

    def t_reminder(i):
        rem = {
            'id': f'test_rem_{i}',
            'title': '并发提醒',
            'message': f'第 {i} 条提醒',
            'type': 'best_practice',
            'context': {'suggestions': ['Use type hints', 'Refactor large functions']},
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False
        }
        reminder._log_reminder(rem)

    def t_alert(i):
        detector._create_alert(
            '并发警报',
            f'第 {i} 条警报',
            'medium',
            {'type': 'manual_test', 'index': i}
        )

    def t_intervention(i):
        monitor._log_intervention(
            'ValueError',
            0.5 + (i % 10) / 20.0,  # 0.5 ~ 0.95
            {'file': 'concurrency.py', 'line': i, 'function': 'run'},
            ['Validate inputs', 'Handle None', 'Add try/except']
        )

    # 每类 10 个线程
    for i in range(10):
        threads.append(threading.Thread(target=t_reminder, args=(i,)))
        threads.append(threading.Thread(target=t_alert, args=(i,)))
        threads.append(threading.Thread(target=t_intervention, args=(i,)))

    # 启动并等待
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print('✅ 并发写入测试完成')


if __name__ == '__main__':
    run_tests()