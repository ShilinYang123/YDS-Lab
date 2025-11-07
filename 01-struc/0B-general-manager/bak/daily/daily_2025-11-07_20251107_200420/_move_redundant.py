#!/usr/bin/env python3
import shutil
from pathlib import Path

bak_dir = Path('s:/YDS-Lab/bak/20251107_cleanup')
bak_dir.mkdir(parents=True, exist_ok=True)

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
    src = Path('s:/YDS-Lab') / name
    if src.exists():
        dst = bak_dir / name
        shutil.move(str(src), str(dst))
        print(f'✔ moved {name} -> {dst}')
    else:
        print(f'⚠️  {name} 不存在，跳过')
print('冗余文件清理完成！')