#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WireGuard模式启动脚本
用于启动wstunnel UDP转发，供WireGuard使用
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
    print("          AUTOVPN - WireGuard模式启动工具")
    print("="*60)
    
    # 调用wstunnel_wireguard.py启动WireGuard模式
    wireguard_script = os.path.join(SCRIPT_DIR, "wstunnel_wireguard.py")
    if os.path.exists(wireguard_script):
        try:
            # 启动wstunnel_wireguard.py
            process = subprocess.Popen(
                [sys.executable, wireguard_script],
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
                print("\n❌ WireGuard模式启动失败，请检查日志")
                return 1
        except Exception as e:
            print(f"\n❌ 启动WireGuard模式时发生错误: {e}")
            return 1
    else:
        print(f"\n❌ WireGuard脚本不存在: {wireguard_script}")
        return 1

if __name__ == "__main__":
    main()