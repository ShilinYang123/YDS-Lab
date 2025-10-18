import os
import subprocess
from datetime import datetime

REPO_PATH = "S:/YDS-Lab"
REMOTE = "origin"
BRANCH = "main"

def run(cmd):
    result = subprocess.run(cmd, cwd=REPO_PATH, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ 命令失败: {cmd}")
        print(result.stderr)
    return result

print("📤 正在推送 YDS-Lab 到 GitHub...")

# 切换目录
os.chdir(REPO_PATH)

# 检查是否有变更
result = run("git status --porcelain")
if not result.stdout.strip():
    print("✅ 无变更，无需推送")
else:
    print(f"📌 检测到变更:\n{result.stdout}")
    run("git add .")
    commit_msg = f"auto: daily sync at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    run(f'git commit -m "{commit_msg}"')
    push_result = run(f'git push {REMOTE} {BRANCH}')
    if "Everything up-to-date" not in push_result.stdout:
        print("🚀 推送成功！")
    else:
        print("✅ 已是最新的")