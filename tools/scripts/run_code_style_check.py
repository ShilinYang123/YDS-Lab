#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码规范检查自动化脚本
用于定期运行代码规范检查
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_code_style_check():
    """运行代码规范检查"""
    print(f"[{datetime.now()}] 开始运行代码规范检查...")
    
    # 确保报告目录存在
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 生成报告文件名（带时间戳）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"code_style_report_{timestamp}.json"
    
    # 运行代码规范检查器
    cmd = [
        sys.executable,
        "tools/scripts/code_style_checker.py",
        "--output", str(report_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd="s:\\YDS-Lab")
        
        print(f"检查完成，返回码: {result.returncode}")
        
        if result.stdout:
            print("标准输出:")
            print(result.stdout)
            
        if result.stderr:
            print("标准错误:")
            print(result.stderr)
            
        # 根据返回码判断检查结果
        if result.returncode == 0:
            print("✅ 代码规范检查通过")
            return True
        elif result.returncode == 2:
            print("⚠️  代码规范检查发现警告")
            return True
        else:
            print("❌ 代码规范检查发现错误")
            return False
            
    except Exception as e:
        print(f"运行代码规范检查失败: {e}")
        return False


def main():
    """主函数"""
    print("YDS-Lab 代码规范检查自动化脚本")
    print("=" * 50)
    
    success = run_code_style_check()
    
    print("\n" + "=" * 50)
    if success:
        print("检查完成，请查看 reports 目录中的详细报告")
    else:
        print("检查失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()