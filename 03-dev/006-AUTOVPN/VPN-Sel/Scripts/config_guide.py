#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTOVPN 配置引导脚本
帮助用户正确配置 config.json 文件
"""

import os
import json
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Scripts.common.utils import load_config

CONFIG_FILE = 'S:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\config.json'
ENV_CONFIG_FILE = 'S:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\Scripts\\config.env'


def check_config_files():
    """检查配置文件是否存在"""
    print("正在检查配置文件...")
    
    # 检查 config.json
    if os.path.exists(CONFIG_FILE):
        print(f"✅ {CONFIG_FILE} 文件存在")
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ config.json 格式正确")
                if 'ssh' in config:
                    ssh_config = config['ssh']
                    print(f"  服务器地址: {ssh_config.get('hostname', '未设置')}")
                    print(f"  用户名: {ssh_config.get('username', '未设置')}")
                    if 'password' in ssh_config:
                        print("  密码: 已设置")
                else:
                    print("⚠️  config.json 中缺少 ssh 配置")
        except Exception as e:
            print(f"❌ config.json 格式错误: {e}")
    else:
        print(f"❌ {CONFIG_FILE} 文件不存在")
        create_default_config_json()
    
    # 检查 config.env
    if os.path.exists(ENV_CONFIG_FILE):
        print(f"✅ {ENV_CONFIG_FILE} 文件存在")
        config = load_config(ENV_CONFIG_FILE)
        if config:
            print("✅ config.env 格式正确")
            print(f"  服务器IP: {config.get('SERVER_IP', '未设置')}")
            print(f"  服务器端口: {config.get('SERVER_PORT', '未设置')}")
            print(f"  WebSocket隧道端口: {config.get('WSTUNNEL_PORT', '未设置')}")
        else:
            print("❌ config.env 格式错误")
    else:
        print(f"❌ {ENV_CONFIG_FILE} 文件不存在")


def create_default_config_json():
    """创建默认的 config.json 文件"""
    print("\n正在创建默认的 config.json 文件...")
    
    default_config = {
        "ssh": {
            "hostname": "your.remote.server",
            "username": "your_username",
            "password": "your_password"
        }
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        print(f"✅ 已创建默认配置文件: {CONFIG_FILE}")
        print("请编辑此文件，填入正确的服务器信息")
    except Exception as e:
        print(f"❌ 创建默认配置文件失败: {e}")


def guide_user_config():
    """引导用户配置"""
    print("\n" + "="*50)
    print("AUTOVPN 配置引导")
    print("="*50)
    
    print("\n1. SSH 连接配置 (用于域名解析)")
    print("   需要在 config.json 中配置远程服务器信息:")
    
    hostname = input("   请输入服务器地址 (如: 192.168.1.100): ").strip()
    if not hostname:
        print("   ⚠️  未输入服务器地址，将使用默认值")
        hostname = "your.remote.server"
    
    username = input("   请输入用户名 (如: root): ").strip()
    if not username:
        print("   ⚠️  未输入用户名，将使用默认值")
        username = "your_username"
    
    password = input("   请输入密码 (输入后不可见): ").strip()
    if not password:
        print("   ⚠️  未输入密码，将使用默认值")
        password = "your_password"
    
    # 更新 config.json
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"   ⚠️  读取现有配置文件时出错: {e}")
    
    config['ssh'] = {
        'hostname': hostname,
        'username': username,
        'password': password
    }
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("✅ SSH 配置已更新")
    except Exception as e:
        print(f"❌ 更新 SSH 配置失败: {e}")
    
    print("\n2. 环境变量配置 (用于wstunnel连接)")
    print("   需要在 Scripts/config.env 中配置以下参数:")
    print("   - SERVER_IP: 服务器IP地址")
    print("   - SERVER_PORT: 服务器端口")
    print("   - WSTUNNEL_PORT: WebSocket隧道端口")
    print("   - SERVER_RESTRICT_PORT: 服务器限制转发端口")
    
    # 检查并更新 config.env
    if os.path.exists(ENV_CONFIG_FILE):
        env_config = load_config(ENV_CONFIG_FILE)
        if env_config:
            print("\n   当前配置:")
            print(f"   SERVER_IP = {env_config.get('SERVER_IP', '未设置')}")
            print(f"   SERVER_PORT = {env_config.get('SERVER_PORT', '未设置')}")
            print(f"   WSTUNNEL_PORT = {env_config.get('WSTUNNEL_PORT', '未设置')}")
            print(f"   SERVER_RESTRICT_PORT = {env_config.get('SERVER_RESTRICT_PORT', '未设置')}")
            
            update = input("\n   是否需要更新这些配置? (y/n): ").strip().lower()
            if update == 'y':
                update_env_config(env_config)
        else:
            print("❌ 无法读取 config.env 文件")
    else:
        print(f"❌ {ENV_CONFIG_FILE} 文件不存在")


def update_env_config(env_config):
    """更新环境配置"""
    server_ip = input(f"   服务器IP地址 [{env_config.get('SERVER_IP', '未设置')}]: ").strip()
    if server_ip:
        env_config['SERVER_IP'] = server_ip
    
    server_port = input(f"   服务器端口 [{env_config.get('SERVER_PORT', '未设置')}]: ").strip()
    if server_port:
        env_config['SERVER_PORT'] = server_port
    
    wstunnel_port = input(f"   WebSocket隧道端口 [{env_config.get('WSTUNNEL_PORT', '未设置')}]: ").strip()
    if wstunnel_port:
        env_config['WSTUNNEL_PORT'] = wstunnel_port
    
    server_restrict_port = input(f"   服务器限制转发端口 [{env_config.get('SERVER_RESTRICT_PORT', '未设置')}]: ").strip()
    if server_restrict_port:
        env_config['SERVER_RESTRICT_PORT'] = server_restrict_port
    
    # 写入更新后的配置
    try:
        with open(ENV_CONFIG_FILE, 'w', encoding='utf-8') as f:
            for key, value in env_config.items():
                f.write(f"{key}={value}\n")
        print("✅ 环境配置已更新")
    except Exception as e:
        print(f"❌ 更新环境配置失败: {e}")


def main():
    print("AUTOVPN 配置检查和引导工具")
    print("="*50)
    
    check_config_files()
    
    guide = input("\n是否需要配置引导? (y/n): ").strip().lower()
    if guide == 'y':
        guide_user_config()
    
    print("\n配置检查完成!")
    print("请确保所有配置都正确无误后再运行 AUTOVPN")


if __name__ == "__main__":
    main()