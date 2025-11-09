#!/usr/bin/env python3
"""
冗余文件移动脚本（合规版）
- 统一移动到顶层 backups/manual 下，避免在仓库中创建 bak/backup/backups 目录。
- 目标目录命名：d_YYYYMMDD_HHMMSS_cleanup。
"""

import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path('s:/YDS-Lab')
target_root = ROOT / 'backups' / 'manual'
target_root.mkdir(parents=True, exist_ok=True)

stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
cleanup_dir = target_root / f'd_{stamp}_cleanup'
cleanup_dir.mkdir(parents=True, exist_ok=True)

files_to_move = [
    '002-meetingroom',
    '02-治理原则图示（阴阳五行协同图）.html',
    '02-治理原则图示（阴阳五行协同图）.pdf',
    '2.Trae 长效记忆系统自动记录功能全流程升级方案（终版）.md',
    '2.Trae 长效记忆系统自动记录功能全流程升级方案（终版）.pdf',
    'JS001-智能会议室系统开发任务书（本地部署优化版）.md',
    'LLM路由与后端选择（Shimmy-Ollama）使用说明.md',
    'Trae平台多智能体开发团队构建指南（最终完整版）.docx',
    'Trae平台多智能体开发团队构建指南（最终完整版）.md',
    'Trae平台多智能体开发团队构建指南（最终完整版）.pdf'
]

for name in files_to_move:
    src = ROOT / name
    if src.exists():
        dst = cleanup_dir / name
        # 若目标存在则先删除，避免移动失败
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        shutil.move(str(src), str(dst))
        print(f'✔ moved {name} -> {dst}')
    else:
        print(f'⚠️  {name} 不存在，跳过')
print('冗余文件清理完成！目标：', str(cleanup_dir))