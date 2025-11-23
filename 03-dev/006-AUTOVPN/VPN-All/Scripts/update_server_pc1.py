#!/usr/bin/env python3
"""
AUTOVPN - 更新服务器PC1配置
用于替换原有的PC1公钥为新的公钥
"""

import os
import sys
import paramiko
import time
from datetime import datetime

def get_script_dir():
    """获取脚本所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """加载配置文件"""
    config_path = os.path.join(get_script_dir(), 'config.env')
    config = {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        return None
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return None
    return config

def main():
    """主函数"""
    print("AUTOVPN - 更新服务器PC1配置")
    print("=" * 60)
    
    # 新的PC1公钥
    new_public_key = "b/eDelTz6t3EppfUXIXFnrO3C6zzAKf/WGO71StUGHo="
    pc1_ip = "10.9.0.2/32"
    
    # 加载配置
    config = load_config()
    if not config:
        return False
    
    server_ip = config.get('SERVER_IP')
    ssh_port = int(config.get('SSH_PORT', 22))
    ssh_user = config.get('SSH_USER', 'root')
    
    if not server_ip:
        print("❌ 服务器IP未配置")
        return False
    
    print(f"服务器: {server_ip}:{ssh_port}")
    print(f"新的PC1公钥: {new_public_key}")
    print(f"PC1 IP: {pc1_ip}")
    print()
    
    # 建立SSH连接
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 使用私钥连接
        key_path = os.path.join(get_script_dir(), '..', 'config', 'id_rsa')
        if not os.path.exists(key_path):
            print(f"❌ SSH私钥文件不存在: {key_path}")
            return False
            
        ssh.connect(server_ip, port=ssh_port, username=ssh_user, key_filename=key_path, timeout=10)
        print("✅ SSH连接成功")
        
        # 备份当前配置
        print("正在备份当前配置...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_cmd = f"cp /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.backup.{timestamp}"
        stdin, stdout, stderr = ssh.exec_command(backup_cmd)
        if stdout.channel.recv_exit_status() == 0:
            print(f"✅ 配置已备份到: /etc/wireguard/wg0.conf.backup.{timestamp}")
        else:
            print("⚠️  备份可能失败，继续操作...")
        
        # 查找并替换PC1配置
        print("正在查找PC1配置...")
        
        # 首先查看当前配置
        stdin, stdout, stderr = ssh.exec_command("cat /etc/wireguard/wg0.conf")
        current_config = stdout.read().decode('utf-8')
        
        # 查找包含10.9.0.2的peer配置
        lines = current_config.split('\n')
        peer_start = -1
        peer_end = -1
        
        for i, line in enumerate(lines):
            if line.strip() == '[Peer]':
                # 检查这个peer是否包含10.9.0.2
                for j in range(i+1, len(lines)):
                    if lines[j].strip().startswith('AllowedIPs'):
                        if '10.9.0.2' in lines[j]:
                            peer_start = i
                            # 找到这个peer的结束位置
                            for k in range(j+1, len(lines)):
                                if lines[k].strip() == '[Peer]' or lines[k].strip() == '[Interface]':
                                    peer_end = k
                                    break
                            if peer_end == -1:
                                peer_end = len(lines)
                            break
                        break
        
        if peer_start == -1:
            print("❌ 未找到PC1 (10.9.0.2) 的配置")
            return False
        
        print(f"找到PC1配置，位于第 {peer_start+1} 到 {peer_end} 行")
        
        # 构建新的peer配置
        new_peer_config = f"""[Peer]
PublicKey = {new_public_key}
AllowedIPs = {pc1_ip}"""
        
        # 替换配置
        new_config = '\n'.join(lines[:peer_start] + [new_peer_config] + lines[peer_end:])
        
        # 写入新配置
        print("正在更新配置...")
        stdin, stdout, stderr = ssh.exec_command("cat > /etc/wireguard/wg0.conf << 'EOF'\n" + new_config + "\nEOF")
        if stdout.channel.recv_exit_status() != 0:
            error = stderr.read().decode('utf-8')
            print(f"❌ 写入配置失败: {error}")
            return False
        
        print("✅ 配置已更新")
        
        # 重启WireGuard服务
        print("正在重启WireGuard服务...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart wg-quick@wg0")
        time.sleep(2)
        
        # 检查服务状态
        stdin, stdout, stderr = ssh.exec_command("systemctl status wg-quick@wg0 --no-pager")
        status_output = stdout.read().decode('utf-8')
        if 'active (running)' in status_output:
            print("✅ WireGuard服务运行正常")
        else:
            print("⚠️  WireGuard服务状态异常")
            print(status_output)
        
        # 验证新配置
        print("正在验证新配置...")
        stdin, stdout, stderr = ssh.exec_command("wg show wg0 peers")
        peers_output = stdout.read().decode('utf-8')
        if new_public_key in peers_output:
            print("✅ 新的PC1公钥已在服务器配置中")
        else:
            print("❌ 新的PC1公钥未找到")
        
        ssh.close()
        print("\n" + "=" * 60)
        print("✅ 服务器PC1配置更新完成")
        print("请重新连接PC1以使用新的密钥")
        return True
        
    except paramiko.AuthenticationException:
        print("❌ SSH认证失败，请检查私钥文件")
        return False
    except paramiko.SSHException as e:
        print(f"❌ SSH连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)