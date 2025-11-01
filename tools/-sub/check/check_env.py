import os
import shutil
import psutil
import subprocess
from datetime import datetime

def log(msg):
    log_file = "S:/YDS-Lab/logs/health_check.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

log("🔍 YDS-Lab 环境健康检查开始...")

# 检查关键工具
for cmd in ["python", "ffmpeg", "git"]:
    if shutil.which(cmd) or os.path.exists(cmd):
        log(f"✅ {cmd} 已安装")
    else:
        log(f"❌ {cmd} 未找到，请安装并加入 PATH")

# Shimmy 特殊处理（exe 文件）
if os.path.exists("shimmy.exe") or shutil.which("shimmy"):
    log("✅ Shimmy 可用")
else:
    log("⚠️ Shimmy 未检测到，AI 协作功能受限")

# 磁盘空间
usage = psutil.disk_usage("S:/")
gb_free = usage.free / (1024**3)
log(f"💾 S:盘 使用率: {usage.percent}% (剩余 {gb_free:.1f} GB)")
if gb_free < 20:
    log("❗ 剩余空间不足 20GB，请清理")

# GPU 检测（GTX1060）
try:
    result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
    if "NVIDIA" in result.stdout and "1060" in result.stdout:
        log("🎮 GTX1060 GPU 可用")
    else:
        log("⚠️ 未检测到 GTX1060")
except Exception as e:
    log(f"❌ nvidia-smi 执行失败: {e}")

log("✅ 环境检查完成\n")