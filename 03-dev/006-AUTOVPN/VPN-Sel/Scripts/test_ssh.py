#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SSH密钥认证连接
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
    key_filename = "S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-Sel/config/id_rsa"  # 使用新生成的RSA格式的密钥
    
    # 检查密钥文件是否存在
    if not os.path.exists(key_filename):
        print(f"[错误] SSH私钥文件不存在: {key_filename}")
        return False
    
    # 建立SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"[信息] 正在使用密钥认证连接到服务器 {hostname}:{port}...")
        # 使用RSAKey.from_private_key_file方法直接加载RSA密钥
        private_key = paramiko.RSAKey.from_private_key_file(key_filename)
        ssh.connect(hostname, port=port, username=username, pkey=private_key, timeout=10)
        print("[信息] SSH连接成功建立")
        
        # 执行简单命令测试
        stdin, stdout, stderr = ssh.exec_command("echo 'SSH密钥认证测试成功'")
        result = stdout.read().decode('utf-8').strip()
        print(f"[结果] {result}")
        
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
        print("\n[完成] SSH密钥认证测试成功")
    else:
        print("\n[失败] SSH密钥认证测试失败")
        exit(1)