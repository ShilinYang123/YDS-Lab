#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 文档维护自动化运行脚本
定期执行文档维护任务
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


def run_document_maintenance():
    """运行文档维护任务"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行文档维护任务")
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    try:
        # 运行文档维护系统
        result = subprocess.run([
            sys.executable, "-m", "tools.scripts.doc_maintenance"
        ], capture_output=True, text=True, cwd=str(project_root))
        
        # 输出结果
        print("文档维护系统输出:")
        print(result.stdout)
        
        if result.stderr:
            print("错误信息:")
            print(result.stderr)
            
        # 检查返回码
        if result.returncode == 0:
            print(f"✅ 文档维护任务完成")
            return True
        else:
            print(f"❌ 文档维护任务失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"运行文档维护系统时出错: {e}")
        return False


def main():
    """主函数"""
    success = run_document_maintenance()
    
    # 生成运行日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "status": "success" if success else "failed",
        "script": "run_doc_maintenance.py"
    }
    
    # 保存运行日志
    reports_dir = Path(__file__).parent.parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    log_file = reports_dir / f"doc_maintenance_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)
        print(f"运行日志已保存: {log_file}")
    except Exception as e:
        print(f"保存运行日志失败: {e}")
    
    return 0 if success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())