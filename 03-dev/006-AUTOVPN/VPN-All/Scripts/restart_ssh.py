#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用密码认证连接到服务器并重启SSH服务
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
    
    hostname = config.get('SERVER_IP', '192.210.206.52')
    port = 22
    username = config.get('SERVER_USER', 'root')
    password = 'pH9t0Zy938ASy6wGZh'  # 使用正确的密码
    
    # 建立SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"[信息] 正在使用密码认证连接到服务器 {hostname}:{port}...")
        ssh.connect(hostname, port=port, username=username, password=password, timeout=10)
        print("[信息] SSH连接成功建立")
        
        # 重启SSH服务
        print("\n[执行] 重启SSH服务")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart ssh")
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("[结果] SSH服务重启成功")
        else:
            print(f"[错误] SSH服务重启失败，退出状态: {exit_status}")
            error = stderr.read().decode('utf-8').strip()
            if error:
                print(f"[错误详情] {error}")
        
        return True
        
    except Exception as e:
        print(f"[错误] SSH连接失败: {e}")
        return False
    finally:
        ssh.close()
        print("[信息] SSH连接已关闭")

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[完成] SSH服务重启完成")
    else:
        print("\n[失败] SSH服务重启失败")
        exit(1)