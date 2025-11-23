import os
import platform
import subprocess
import time
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入公共函数
from Scripts.common.utils import is_process_running, kill_process_by_name


if __name__ == "__main__":
    stopped = False
    if is_process_running('wstunnel.exe'):
        print("正在终止wstunnel进程...")
        if kill_process_by_name('wstunnel.exe'):
            stopped = True
    if stopped:
        print("✅ 所有服务已停止")
    else:
        print("⚠️ 没有发现正在运行的服务")
