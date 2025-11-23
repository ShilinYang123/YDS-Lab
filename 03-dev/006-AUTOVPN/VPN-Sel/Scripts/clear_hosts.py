import os
import shutil
import datetime
import sys

HOSTS_FILE = r'C:\Windows\System32\drivers\etc\hosts'


def main():
    print("正在准备清空Hosts文件...")

    # 尝试读取文件以获取更详细的错误信息
    try:
        with open(HOSTS_FILE, 'r') as f:
            pass  # 仅尝试打开，不读取内容
        print(f"成功访问Hosts文件: {HOSTS_FILE}")
    except FileNotFoundError:
        print(f"错误：Hosts文件 ({HOSTS_FILE}) 未找到。")
        print("请检查文件路径是否正确。")
        sys.exit(1)
    except PermissionError:
        print(f"错误：没有足够的权限访问Hosts文件 ({HOSTS_FILE})。")
        print("请确保脚本以管理员权限运行。")
        sys.exit(1)
    except OSError as e:
        print(f"错误：访问Hosts文件 ({HOSTS_FILE}) 时发生操作系统错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误：访问Hosts文件 ({HOSTS_FILE}) 时发生未知错误: {e}")
        sys.exit(1)

    if not os.path.exists(HOSTS_FILE):  # 再次检查，理论上如果上面通过了这里也应该通过
        print(f"错误：Hosts文件 ({HOSTS_FILE}) 最终检查仍为不存在或无权访问。")
        print("请确保脚本以管理员权限运行，并检查文件状态。")
        sys.exit(1)

    try:
        print(f"准备备份和清空Hosts文件: {HOSTS_FILE}")
        bak_filename = HOSTS_FILE + '.' + \
            datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.bak'
        shutil.copy(HOSTS_FILE, bak_filename)
        print(f"已备份原Hosts文件到: {bak_filename}")

        with open(HOSTS_FILE, 'w', encoding='utf-8') as f:
            f.write('')  # Clear the file
        print("✅ Hosts文件已成功清空。")

    except PermissionError:
        print(f"错误：没有足够的权限修改Hosts文件 ({HOSTS_FILE})。")
        print("请以管理员权限运行此脚本。")
        sys.exit(1)
    except Exception as e:
        print(f"清空Hosts文件时发生未知错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
