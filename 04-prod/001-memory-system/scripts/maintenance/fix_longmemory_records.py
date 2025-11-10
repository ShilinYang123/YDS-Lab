#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速修复 01-struc/logs/longmemory/lm_records.json 的结构问题：
    - 当出现尾部多余的闭括号导致 json.load 报错时，移除多余字符并重新保存。
"""
import json
import os
from pathlib import Path

def resolve_lm_path() -> str:
    """解析长记忆持久化文件路径。
    优先使用环境变量，其次使用公司级默认路径 01-struc/logs/longmemory/lm_records.json。
    支持相对路径（相对仓库根目录）。
    """
    # 支持两种环境变量名（文档与服务兼容）
    env_path = os.environ.get("YDS_LONGMEMORY_STORAGE_PATH") or os.environ.get("LONGMEMORY_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            # 相对路径基于当前进程工作目录（通常为仓库根）
            p = Path.cwd() / p
        return str(p)

    # 回退到公司级默认路径
    repo_root = Path.cwd()
    return str(repo_root / "01-struc" / "logs" / "longmemory" / "lm_records.json")

LM_PATH = resolve_lm_path()

def fix_lm_records(path: str) -> bool:
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()
    try:
        json.loads(txt)
        print('✅ 文件已是有效 JSON，无需修复')
        return True
    except Exception as e:
        print(f'⚠️ 检测到 JSON 解析错误：{e}. 尝试自动修复...')
        # 计算多余的闭括号数量
        opens = txt.count('{')
        closes = txt.count('}')
        # 如果闭括号多于开括号，尝试从尾部删除多余闭括号
        if closes > opens:
            to_remove = closes - opens
            s = list(txt)
            i = len(s) - 1
            while to_remove > 0 and i >= 0:
                if s[i] == '}':
                    del s[i]
                    to_remove -= 1
                    i = len(s) - 1
                else:
                    i -= 1
            txt = ''.join(s)
        # 再次验证并写回
        try:
            data = json.loads(txt)
        except Exception as e2:
            print(f'❌ 自动修复失败：{e2}')
            return False
        # 备份并写入
        with open(path + '.bak', 'w', encoding='utf-8') as f:
            f.write(txt)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('✅ 修复完成并已保存')
        return True

if __name__ == '__main__':
    try:
        path = LM_PATH
        # 确保目录存在
        dirname = os.path.dirname(path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        # 文件不存在则初始化为标准结构
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({"general": {}, "memories": []}, f, ensure_ascii=False, indent=2)
            print(f'✅ 已初始化长记忆文件：{path}')
            raise SystemExit(0)

        ok = fix_lm_records(path)
        raise SystemExit(0 if ok else 1)
    except Exception as e:
        print(f"❌ 脚本执行失败：{e}")
        raise SystemExit(1)