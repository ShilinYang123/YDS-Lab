#!/usr/bin/env python3
import paramiko
import os

def main():
    server_ip = '192.210.206.52'
    ssh_user = 'root'
    key_path = 'S:\\YDS-Lab\\03-dev\\006-AUTOVPN\\allout\\config\\id_rsa'
    new_public_key = 'b/eDelTz6t3EppfUXIXFnrO3C6zzAKf/WGO71StUGHo='
    old_public_key = 'KMTPpesa6idoed6XD+6BUS501FIUTej7CACTaAdQahk='
    
    print("更新PC1公钥...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_ip, username=ssh_user, key_filename=key_path, timeout=10)
    print('已连接服务器')
    
    # 备份配置
    ssh.exec_command('cp /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.backup')
    print('配置已备份')
    
    # 替换公钥
    cmd = f"sed -i 's/{old_public_key}/{new_public_key}/g' /etc/wireguard/wg0.conf"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    if stdout.channel.recv_exit_status() == 0:
        print('公钥已替换')
        
        # 重启WireGuard
        ssh.exec_command('systemctl restart wg-quick@wg0')
        print('WireGuard已重启')
        
        # 验证
        stdin, stdout, stderr = ssh.exec_command('wg show wg0 peers')
        peers = stdout.read().decode('utf-8')
        if new_public_key in peers:
            print('✅ 新的PC1公钥已生效')
        else:
            print('❌ 新公钥未找到')
    else:
        print('❌ 替换失败')
    
    ssh.close()

if __name__ == "__main__":
    main()