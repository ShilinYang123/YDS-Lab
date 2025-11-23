#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试域名解析功能
"""

import sys
import os
import paramiko

def resolve_domain_via_server(hostname, domain):
    """通过服务器解析域名"""
    try:
        print(f"[信息] 正在建立到 {hostname} 的SSH连接...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 使用密钥认证
        private_key = paramiko.RSAKey.from_private_key_file("S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-Sel/config/id_rsa")
        ssh.connect(hostname, port=22, username='root', pkey=private_key, timeout=10)
        
        print("[成功] SSH连接建立成功")
        
        # 直接执行Python命令来解析域名
        print(f"[信息] 正在解析域名 {domain}...")
        command = f"python3 -c \"import socket; print(socket.gethostbyname('{domain}'))\""
        stdin, stdout, stderr = ssh.exec_command(command)
        
        result = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        exit_status = stdout.channel.recv_exit_status()
        
        # 关闭连接
        ssh.close()
        print("[信息] SSH连接已关闭")
        
        if exit_status == 0:
            if result:
                print(f"[结果] 域名 {domain} 解析到IP: {result}")
                return result
            else:
                print(f"[错误] 域名解析返回空结果")
                return None
        else:
            print(f"[错误] 域名解析失败，退出状态: {exit_status}")
            if error:
                print("[错误详情]", error)
            return None
        
    except Exception as e:
        print(f"[错误] 域名解析失败: {e}")
        return None

def main():
    # 测试解析ip.sb域名
    domain = "ip.sb"
    server_ip = "192.210.206.52"
    
    ip = resolve_domain_via_server(server_ip, domain)
    
    if ip:
        print(f"\n[完成] 域名 {domain} 成功解析到IP: {ip}")
        return True
    else:
        print(f"\n[失败] 域名 {domain} 解析失败")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[完成] 域名解析功能测试成功")
    else:
        print("\n[失败] 域名解析功能测试失败")
        exit(1)