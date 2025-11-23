#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将RSA格式的私钥转换为OPENSSH格式
"""

import paramiko
import os

def convert_rsa_to_openssh(private_key_path, output_path):
    """将RSA格式的私钥转换为OPENSSH格式"""
    try:
        # 加载RSA私钥
        private_key = paramiko.RSAKey(filename=private_key_path)
        
        # 保存为OPENSSH格式
        private_key.write_private_key_file(output_path)
        
        print(f"[成功] 已将私钥转换为OPENSSH格式并保存到: {output_path}")
        return True
    except Exception as e:
        print(f"[错误] 转换私钥失败: {e}")
        return False

def main():
    # 定义路径
    rsa_key_path = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\config\id_rsa"
openssh_key_path = r"S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\config\id_rsa_openssh"
    
    # 检查原始私钥文件是否存在
    if not os.path.exists(rsa_key_path):
        print(f"[错误] 原始私钥文件不存在: {rsa_key_path}")
        return False
    
    # 转换密钥格式
    if convert_rsa_to_openssh(rsa_key_path, openssh_key_path):
        print("[信息] 密钥格式转换完成")
        return True
    else:
        print("[错误] 密钥格式转换失败")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[完成] 密钥格式转换成功")
    else:
        print("\n[失败] 密钥格式转换失败")
        exit(1)