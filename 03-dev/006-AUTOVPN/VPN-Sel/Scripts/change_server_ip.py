#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修改服务器WireGuard本机IP地址脚本
"""

import paramiko
import time
import sys
from common.utils import load_config

def change_server_wg_ip():
    """修改服务器WireGuard接口IP地址"""
    
    print("=" * 60)
    print("AUTOVPN - 修改服务器WireGuard本机IP地址")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    server_ip = config.get('SERVER_IP', '192.210.206.52')
    ssh_port = int(config.get('SSH_PORT', '22'))
    ssh_user = config.get('SSH_USER', 'root')
    ssh_key_path = config.get('SSH_KEY_PATH', 'S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-Sel/config/id_rsa')
    
    print(f"[信息] 正在连接到服务器 {server_ip}:{ssh_port}...")
    
    try:
        # 创建SSH连接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_ip, port=ssh_port, username=ssh_user, key_filename=ssh_key_path, timeout=10)
        print("[√] SSH连接成功建立")
        
        # 检查当前配置
        print("\n[信息] 检查当前WireGuard配置...")
        stdin, stdout, stderr = ssh.exec_command("wg show wg0")
        current_config = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            print(f"[×] 获取当前配置失败: {error}")
            return False
            
        print("当前配置:")
        print(current_config)
        
        # 检查当前接口IP
        print("\n[信息] 检查当前接口IP...")
        stdin, stdout, stderr = ssh.exec_command("ip addr show wg0")
        ip_config = stdout.read().decode()
        print("当前IP配置:")
        print(ip_config)
        
        # 询问是否改为10.9.0.2
        print("\n[询问] 是否要将服务器本机IP改为 10.9.0.2/32?")
        print("⚠️  警告: 这会影响到现有的peer连接!")
        response = input("输入 'yes' 确认修改，其他键取消: ").strip().lower()
        
        if response != 'yes':
            print("[信息] 操作已取消")
            return False
            
        # 停止WireGuard服务
        print("\n[信息] 停止WireGuard服务...")
        stdin, stdout, stderr = ssh.exec_command("systemctl stop wg-quick@wg0")
        time.sleep(2)
        
        # 修改配置文件
        print("[信息] 修改WireGuard配置文件...")
        commands = [
            # 备份原配置文件
            "cp /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.backup",
            
            # 修改接口地址
            "sed -i 's/Address = .*/Address = 10.9.0.2\\/32/' /etc/wireguard/wg0.conf",
            
            # 显示修改后的配置
            "echo '修改后的配置:'",
            "grep -E 'Address|PrivateKey|ListenPort' /etc/wireguard/wg0.conf"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output:
                print(output.strip())
            if error and 'sed:' in error:
                print(f"[×] 修改配置文件失败: {error}")
                return False
        
        # 启动WireGuard服务
        print("\n[信息] 启动WireGuard服务...")
        stdin, stdout, stderr = ssh.exec_command("systemctl start wg-quick@wg0")
        time.sleep(3)
        
        # 验证新配置
        print("\n[信息] 验证新配置...")
        stdin, stdout, stderr = ssh.exec_command("ip addr show wg0")
        new_ip_config = stdout.read().decode()
        print("新的IP配置:")
        print(new_ip_config)
        
        # 检查服务状态
        stdin, stdout, stderr = ssh.exec_command("systemctl status wg-quick@wg0 --no-pager")
        status = stdout.read().decode()
        if 'active (running)' in status:
            print("[√] WireGuard服务正常运行")
        else:
            print("[×] WireGuard服务启动失败")
            print(status)
            return False
            
        # 检查接口状态
        stdin, stdout, stderr = ssh.exec_command("wg show wg0")
        final_config = stdout.read().decode()
        print("\n最终配置:")
        print(final_config)
        
        print("\n" + "=" * 60)
        print("[√] 服务器本机IP地址已成功修改为 10.9.0.2/32")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"[×] 操作失败: {str(e)}")
        return False
        
    finally:
        ssh.close()
        print("\n[信息] SSH连接已关闭")

if __name__ == "__main__":
    try:
        success = change_server_wg_ip()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[信息] 操作被用户中断")
        sys.exit(1)