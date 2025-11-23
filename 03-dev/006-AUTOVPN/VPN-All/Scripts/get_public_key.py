#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从私钥生成公钥
"""

import subprocess
import os

def get_public_key_from_private(private_key):
    """从私钥生成公钥"""
    try:
        # WireGuard安装路径
        wireguard_path = r'C:\Program Files\WireGuard\wg.exe'
        
        # 生成公钥
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
        
    except FileNotFoundError:
        print("❌ 未找到WireGuard命令行工具 'wg'。请确保已安装WireGuard客户端并将其添加到系统PATH中。")
        return None
    except Exception as e:
        print(f"❌ 生成公钥失败: {e}")
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("AUTOVPN - 从私钥生成公钥工具")
    print("=" * 60)
    
    # 读取PC1的私钥
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
            return
            
        print(f"找到私钥: {private_key}")
        
        # 生成公钥
        public_key = get_public_key_from_private(private_key)
        
        if public_key:
            print(f"✅ 生成的公钥: {public_key}")
            
            # 检查是否在服务器peer列表中
            server_peers = [
                "1AVPJiqQtUD15RstWDr4O+SuDrQkPx1z+aiK7IQ46Ak=",
                "KMTPpesa6idoed6XD+6BUS501FIUTej7CACTaAdQahk=", 
                "ZG2P6mVpS4UEfJodm6D9rBUq3sJrZkAVHWoYnysgZBg=",
                "ydqUAOJSBFDNBhsV0JDmOdUBHxf4Ymdx/DCGEtu7zQM=",
                "bb0YxoDxgR4hhiUm4ZdvQ9LsSYjjTlCAfxJJe/uLp1U=",
                "DIxDPVLj9TtnqJ8mWaa7oNWOt+p5YT8OIXSXOmr0NGM="
            ]
            
            if public_key in server_peers:
                print(f"✅ 客户端公钥在服务器peer列表中")
            else:
                print(f"❌ 客户端公钥不在服务器peer列表中")
                print(f"需要联系服务器管理员添加以下公钥:")
                print(f"Public Key: {public_key}")
                print(f"Allowed IPs: 10.9.0.8/32")  # 假设使用下一个可用IP
                
        else:
            print("❌ 公钥生成失败")
            
    except FileNotFoundError:
        print(f"❌ 密钥文件不存在: {key_file_path}")
    except Exception as e:
        print(f"❌ 读取密钥文件失败: {e}")
    
    print("\n" + "=" * 60)
    print("操作完成")
    print("=" * 60)

if __name__ == "__main__":
    main()