#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
综合模式启动脚本
用于同时启动WireGuard和代理模式
"""

import os
import sys
import subprocess
import time

# 脚本路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    """主函数"""
    print("="*60)
    print("          AUTOVPN - 综合模式启动工具")
    print("="*60)
    
    # 调用wstunnel_combined.py启动综合模式
    combined_script = os.path.join(SCRIPT_DIR, "wstunnel_combined.py")
    if os.path.exists(combined_script):
        try:
            # 启动wstunnel_combined.py
            process = subprocess.Popen(
                [sys.executable, combined_script],
                cwd=SCRIPT_DIR,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 等待进程启动
            time.sleep(2)
            
            # 检查进程是否成功启动
            if process.poll() is None:
                # 不输出成功信息，由菜单程序统一提示
                return 0
            else:
                print("\n❌ 综合模式启动失败，请检查日志")
                return 1
        except Exception as e:
            print(f"\n❌ 启动综合模式时发生错误: {e}")
            return 1
    else:
        print(f"\n❌ 综合模式脚本不存在: {combined_script}")
        return 1

if __name__ == "__main__":
    main()