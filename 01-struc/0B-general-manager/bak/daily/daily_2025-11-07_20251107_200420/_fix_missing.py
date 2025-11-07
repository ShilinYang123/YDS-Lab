#!/usr/bin/env python3
import os
from pathlib import Path

items = [
    ('file', 's:/YDS-Lab/DEPLOYMENT_STATUS.md'),
    ('dir',  's:/YDS-Lab/01-struc/0B-general-manager/GeneralOffice'),
    ('file', 's:/YDS-Lab/01-struc/0B-general-manager/Docs/DEPLOYMENT_STATUS.md'),
    ('file', 's:/YDS-Lab/01-struc/0B-general-manager/meetings/DEPLOYMENT_STATUS.md'),
    ('file', 's:/YDS-Lab/01-struc/0B-general-manager/tools/DEPLOYMENT_STATUS.md'),
]

for t, p in items:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    if t == 'file':
        Path(p).write_text('# Deployment Status\n\n> Auto-generated placeholder.\n', encoding='utf-8')
    else:
        Path(p).mkdir(parents=True, exist_ok=True)
    print(f'✔ Created {p}')
print('缺失项补齐完成！')