#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将客户端添加到服务器WireGuard配置
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

def get_client_public_key():
    """获取客户端公钥"""
    key_file_path = "S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-All/config/wireguard/client/PC1_keys.txt"
    
    try:
        with open(key_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 提取私钥
        for line in content.split('\n'):
            if line.startswith('Private Key:'):
                private_key = line.replace('Private Key:', '').strip()
                break
        else:
            print("❌ 未找到私钥")
            return None
            
        # 使用WireGuard生成公钥
        import subprocess
        wireguard_path = r'C:\Program Files\WireGuard\wg.exe'
        
        pubkey_proc = subprocess.Popen(
            [wireguard_path, 'pubkey'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        public_key, pubkey_error = pubkey_proc.communicate(input=private_key)
        
        if pubkey_proc.returncode != 0:
            print(f"❌ 生成公钥失败: {pubkey_error.strip()}")
            return None
        
        return public_key.strip()
        
    except Exception as e:
        print(f"❌ 读取密钥文件失败: {e}")
        return None

def add_client_to_server():
    """将客户端添加到服务器WireGuard配置"""
    config = load_config()
    
    hostname = config.get('SERVER_IP', '192.210.206.52')
    port = 22
    username = config.get('SERVER_USER', 'root')
    key_filename = "S:/YDS-Lab/03-dev/006-AUTOVPN/VPN-All/config/id_rsa"
    
    # 获取客户端公钥
    client_public_key = get_client_public_key()
    if not client_public_key:
        return False
    
    print(f"客户端公钥: {client_public_key}")
    
    # 检查密钥文件是否存在
    if not os.path.exists(key_filename):
        print(f"[错误] SSH私钥文件不存在: {key_filename}")
        return False
    
    # 建立SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"[信息] 正在连接到服务器 {hostname}:{port}...")
        private_key = paramiko.RSAKey.from_private_key_file(key_filename)
        ssh.connect(hostname, port=port, username=username, pkey=private_key, timeout=10)
        print("[信息] SSH连接成功建立")
        
        # 检查当前peer列表
        print("\n[信息] 检查当前peer列表...")
        stdin, stdout, stderr = ssh.exec_command("wg show wg0 peers")
        existing_peers = stdout.read().decode('utf-8').strip().split('\n')
        existing_peers = [p.strip() for p in existing_peers if p.strip()]
        
        print(f"当前peer数量: {len(existing_peers)}")
        
        if client_public_key in existing_peers:
            print("[√] 客户端已在服务器peer列表中")
            return True
        
        # 获取下一个可用的IP地址
        print("\n[信息] 获取下一个可用IP地址...")
        stdin, stdout, stderr = ssh.exec_command("wg show wg0 allowed-ips | grep -o '[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+\\.[0-9]\\+' | sort -t. -k4 -n")
        allowed_ips_output = stdout.read().decode('utf-8').strip()
        
        if allowed_ips_output:
            # 解析现有IP地址
            existing_ips = []
            for line in allowed_ips_output.split('\n'):
                if line.strip():
                    parts = line.strip().split('.')
                    if len(parts) == 4:
                        existing_ips.append(int(parts[3]))
            
            # 找到下一个可用的IP (从10.9.0.8开始)
            next_ip_num = 8
            while next_ip_num in existing_ips:
                next_ip_num += 1
            
            next_ip = f"10.9.0.{next_ip_num}/32"
        else:
            next_ip = "10.9.0.8/32"
        
        print(f"分配的IP地址: {next_ip}")
        
        # 添加peer到WireGuard
        print("\n[信息] 添加客户端到WireGuard配置...")
        add_peer_cmd = f"wg set wg0 peer {client_public_key} allowed-ips {next_ip}"
        
        stdin, stdout, stderr = ssh.exec_command(add_peer_cmd)
        error_output = stderr.read().decode('utf-8').strip()
        
        if error_output:
            print(f"[×] 添加peer失败: {error_output}")
            return False
        else:
            print("[√] 客户端已成功添加到WireGuard配置")
            
            # 保存配置到文件（可选，取决于服务器配置）
            print("\n[信息] 保存配置...")
            stdin, stdout, stderr = ssh.exec_command("wg-quick save wg0 2>/dev/null || echo 'Configuration saved or not needed'")
            save_result = stdout.read().decode('utf-8').strip()
            print(f"保存结果: {save_result}")
            
            # 验证添加结果
            print("\n[信息] 验证添加结果...")
            stdin, stdout, stderr = ssh.exec_command(f"wg show wg0 peer {client_public_key}")
            peer_info = stdout.read().decode('utf-8').strip()
            
            if peer_info:
                print("[√] 客户端peer信息:")
                print(peer_info)
                
                # 更新客户端配置文件
                print(f"\n[信息] 需要更新客户端配置文件")
                print(f"请确保客户端配置文件中:")
                print(f"- Address: 使用 {next_ip.replace('/32', '')}/24")
                print(f"- 或者保持当前配置并测试连接")
                
                return True
            else:
                print("[×] 未找到新添加的peer")
                return False
        
    except Exception as e:
        print(f"[错误] SSH连接失败: {e}")
        return False
    finally:
        ssh.close()
        print("\n[信息] SSH连接已关闭")

if __name__ == "__main__":
    print("=" * 60)
    print("AUTOVPN - 添加客户端到服务器WireGuard配置")
    print("=" * 60)
    
    success = add_client_to_server()
    if success:
        print("\n[完成] 客户端已成功添加到服务器")
    else:
        print("\n[失败] 客户端添加到服务器失败")
        exit(1)