#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将新生成的SSH公钥添加到远程服务器
"""

import paramiko
import os

def load_config():
    """加载config.env配置文件"""
    config = {}
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.env")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # 移除注释部分
                        if '#' in value:
                            value = value.split('#')[0]
                        config[key.strip()] = value.strip()
        return config
    except FileNotFoundError:
        print(f"[警告] 配置文件不存在: {config_path}")
        return {}
    except Exception as e:
        print(f"[错误] 读取配置文件失败: {e}")
        return {}

def main():
    # 加载配置
    config = load_config()
    
    # 使用脚本参数中提供的正确密码
    hostname = config.get('SERVER_IP', '192.210.206.52')
    port = 22
    username = config.get('SERVER_USER', 'root')
    password = 'pH9t0Zy938ASy6wGZh'  # 使用您提供的正确密码
    
    # 本地公钥路径
    local_public_key_path = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-All\config\id_rsa.pub"
    
    # 检查本地公钥文件是否存在
    if not os.path.exists(local_public_key_path):
        print(f"[错误] 本地公钥文件不存在: {local_public_key_path}")
        return False
    
    # 读取本地公钥内容
    try:
        with open(local_public_key_path, 'r') as f:
            public_key = f.read().strip()
    except Exception as e:
        print(f"[错误] 读取本地公钥文件失败: {e}")
        return False
    
    # 建立SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"[信息] 正在连接到服务器 {hostname}:{port}...")
        ssh.connect(hostname, port=port, username=username, password=password, timeout=10)
        print("[信息] SSH连接成功建立")
        
        # 创建.ssh目录（如果不存在）
        stdin, stdout, stderr = ssh.exec_command("mkdir -p ~/.ssh")
        stdout.channel.recv_exit_status()  # 等待命令执行完成
        
        # 添加公钥到authorized_keys文件（使用追加模式）
        command = f"echo '{public_key} autovpn@local' >> ~/.ssh/authorized_keys"
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("[成功] 公钥已添加到服务器")
        else:
            print(f"[错误] 添加公钥到服务器失败，退出状态: {exit_status}")
            print(f"STDERR: {stderr.read().decode()}")
            return False
        
        # 设置正确的权限
        chmod_commands = [
            "chmod 700 ~/.ssh",
            "chmod 600 ~/.ssh/authorized_keys"
        ]
        
        for cmd in chmod_commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                print(f"[警告] 设置权限失败: {cmd}")
        
        print("[信息] SSH密钥权限已设置")
        return True
        
    except Exception as e:
        print(f"[错误] SSH连接或操作失败: {e}")
        return False
    finally:
        ssh.close()
        print("[信息] SSH连接已关闭")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[完成] SSH密钥已成功配置到服务器")
        print("现在您可以使用密钥认证连接到服务器了")
    else:
        print("\n[失败] SSH密钥配置到服务器失败")
        exit(1)