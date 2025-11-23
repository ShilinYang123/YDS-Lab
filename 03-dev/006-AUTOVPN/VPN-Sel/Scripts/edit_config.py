import os
import platform
import subprocess
import sys

CONFIG_PATH = r'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts\config.env'
SCRIPT_DIR = r'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\Scripts'


def run_sync_scripts():
    """运行配置同步脚本"""
    print("\n开始同步配置到其他文件...")

    # 运行客户端配置同步
    try:
        print("正在同步客户端配置...")
        result = subprocess.run([sys.executable, os.path.join(
            SCRIPT_DIR, 'sync_config.py')], capture_output=True, text=True, cwd=SCRIPT_DIR)
        if result.returncode == 0:
            print("✅ 客户端配置同步完成")
        else:
            print(f"⚠️ 客户端配置同步警告: {result.stderr}")
    except Exception as e:
        print(f"❌ 客户端配置同步失败: {e}")

    # 运行服务器端配置同步
    try:
        print("正在同步服务器端配置...")
        result = subprocess.run([sys.executable,
                                 os.path.join(SCRIPT_DIR,
                                              'update_server_wstunnel_config.py')],
                                capture_output=True,
                                text=True,
                                cwd=SCRIPT_DIR)
        if result.returncode == 0:
            print("✅ 服务器端配置同步完成")
        else:
            print(f"⚠️ 服务器端配置同步警告: {result.stderr}")
    except Exception as e:
        print(f"❌ 服务器端配置同步失败: {e}")

    print("\n配置同步完成！")


def main():
    print("\n编辑配置文件...")
    try:
        if platform.system() == "Windows":
            subprocess.Popen(['notepad', CONFIG_PATH])
        else:
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.Popen([editor, CONFIG_PATH])
        print(f"✅ 已打开配置文件: {CONFIG_PATH}")

        # 等待用户确认是否同步
        print("\n请在记事本中修改配置参数，修改完成后保存并关闭记事本。")
        input("修改完成后，请按回车键继续...")

        # 询问是否同步配置
        while True:
            choice = input("\n是否将修改的参数同步到其他文件？(y/n): ").strip().lower()
            if choice in ['y', 'yes', '是', '1']:
                run_sync_scripts()
                break
            elif choice in ['n', 'no', '否', '0']:
                print("配置修改完成，未进行同步。")
                print("如需同步，请手动运行 sync_config.py 和 update_server_wstunnel_config.py")
                break
            else:
                print("请输入 y(是) 或 n(否)")

    except Exception as e:
        print(f"❌ 打开配置文件时发生错误: {e}")


if __name__ == "__main__":
    main()
