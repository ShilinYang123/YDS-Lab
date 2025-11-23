#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WireGuard密钥对生成脚本
用于为新设备生成WireGuard私钥和公钥
"""

import os
import sys
import subprocess

def generate_wireguard_key():
    """生成WireGuard密钥对"""
    try:
        # WireGuard安装路径
        wireguard_path = r'C:\Program Files\WireGuard\wg.exe'
        
        # 生成私钥
        genkey_proc = subprocess.Popen(
            [wireguard_path, 'genkey'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        private_key, genkey_error = genkey_proc.communicate()
        
        if genkey_proc.returncode != 0:
            print(f"❌ 生成私钥失败: {genkey_error.strip()}")
            return None, None
        
        private_key = private_key.strip()
        
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
            return None, None
        
        public_key = public_key.strip()
        
        return private_key, public_key
        
    except FileNotFoundError:
        print("❌ 未找到WireGuard命令行工具 'wg'。请确保已安装WireGuard客户端并将其添加到系统PATH中。")
        return None, None
    except Exception as e:
        print(f"❌ 生成密钥对失败: {e}")
        return None, None

def main():
    """主函数"""
    print("=" * 60)
    print("AUTOVPN - WireGuard密钥对生成工具")
    print("=" * 60)
    
    print("正在生成WireGuard密钥对...")
    private_key, public_key = generate_wireguard_key()
    
    if private_key and public_key:
        print(f"✅ 私钥生成成功: {private_key}")
        print(f"✅ 公钥生成成功: {public_key}")
        
        # 保存到配置文件
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config", "wireguard", "client")
        os.makedirs(config_dir, exist_ok=True)
        
        # 使用当前设备名称作为配置文件名
        device_name = "PC1"
        config_path = os.path.join(config_dir, f"{device_name}.conf")
        
        print(f"\n正在保存配置文件到: {config_path}")
        
        # 创建配置文件内容
        config_content = f"""[Interface]
PrivateKey = {private_key}
Address = 192.168.255.5/32
DNS = 8.8.8.8
PostUp = powershell -Command "Set-NetIPInterface -InterfaceAlias '{device_name}' -AddressFamily IPv4 -InterfaceMetric 5"
PostDown = powershell -Command "Set-NetIPInterface -InterfaceAlias '{device_name}' -AddressFamily IPv4 -InterfaceMetricAutoSelection Enabled"

[Peer]
PublicKey = A6H2hSPSIQccFxt4thcOp6Zz3c6TBXnQqmkOvYj98U4=
AllowedIPs = 0.0.0.0/0
Endpoint = 127.0.0.1:1081
PersistentKeepalive = 60
"""
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"✅ 配置文件已保存: {config_path}")
            
            # 保存密钥到单独的文件
            key_file_path = os.path.join(config_dir, f"{device_name}_keys.txt")
            with open(key_file_path, 'w', encoding='utf-8') as f:
                f.write(f"Private Key: {private_key}\n")
                f.write(f"Public Key: {public_key}\n")
            print(f"✅ 密钥已保存到: {key_file_path}")
            
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
    
    print("\n" + "=" * 60)
    print("操作完成")
    print("=" * 60)

if __name__ == "__main__":
    main()