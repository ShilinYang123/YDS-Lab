import os
import sys
import time

def unlock_git_index():
    """尝试解锁Git索引"""
    git_dir = os.path.join(os.getcwd(), ".git")
    index_lock = os.path.join(git_dir, "index.lock")
    
    if os.path.exists(index_lock):
        try:
            os.remove(index_lock)
            print(f"已删除Git索引锁定文件: {index_lock}")
            return True
        except Exception as e:
            print(f"无法删除Git索引锁定文件: {e}")
            return False
    else:
        print("Git索引锁定文件不存在")
        return True

if __name__ == "__main__":
    if unlock_git_index():
        print("Git索引已解锁")
    else:
        print("无法解锁Git索引")
        sys.exit(1)