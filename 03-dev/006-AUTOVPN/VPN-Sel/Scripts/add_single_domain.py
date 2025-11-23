from typing import Set
import platform
import configparser
import logging
import paramiko
import ipaddress
import tempfile
from typing import List, Tuple, Optional
from datetime import datetime
import subprocess
import shutil
import socket
import sys
import os
import json
{
    "ssh": {
        "hostname": "your.remote.server",
        "username": "your_username",
        "password": "your_password"
    }
}
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
境外域名添加并完成全流程处理脚本
功能：解析境外域名IP → 更新hosts → 强制刷新DNS缓存
"""


# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 项目根目录定义
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加hosts文件路径定义
HOSTS_FILE = r'C:\Windows\System32\drivers\etc\hosts'

# 读取配置文件
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'config.json')


def load_config():
    """读取配置文件"""
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"配置文件未找到: {CONFIG_FILE}")
        logger.info("请先创建配置文件，示例格式:")
        logger.info(
            "{\n    \"ssh\": {\n        \"hostname\": \"your.remote.server\",\n        \"username\": \"your_username\",\n        \"password\": \"your_password\"\n    }\n}"
        )
        return None

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('ssh', {})
    except Exception as e:
        logger.error(f"配置文件读取失败: {e}")
        return None

# 新增hosts更新函数（直接参照update_hosts.py逻辑）


def resolve_domain_ip(ssh: paramiko.SSHClient, domain: str) -> Optional[str]:
    """通过境外服务器解析域名获取IP地址"""
    try:
        # 创建并上传执行脚本
        script_content = f"dig +short {domain} | awk 'NR == 1 {{print; exit}}'"
        tmpfile_path, remote_script_path = _create_and_upload_script(
            ssh, script_content, domain)

        # 执行脚本
        stdin, stdout, stderr = ssh.exec_command(f"bash {remote_script_path}")
        result = stdout.read().decode('utf-8', errors='ignore').strip()
        error = stderr.read().decode('utf-8', errors='ignore').strip()

        # 清理远程脚本
        ssh.exec_command(f"rm -f {remote_script_path}")

        # 处理结果
        if result:
            ip = result.split('\n')[0]
            print(f"[INFO] Remote resolved: {domain} -> {ip}")
            return ip
        else:
            print(f"[WARNING] 境外解析失败，尝试本地解析")
            return get_ip_by_domain(domain)

    except Exception as e:
        print(f"[ERROR] 远程DNS错误: {e}")
        return None


def _create_and_upload_script(
        ssh: paramiko.SSHClient, script_content: str, domain: str) -> Tuple[str, str]:
    """创建临时脚本文件并上传到服务器"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as tmpfile:
        tmpfile.write(script_content)
        tmpfile_path = tmpfile.name

    # 生成远程脚本路径
    remote_script_path = f"/tmp/dig_{domain.replace('.', '_')}.sh"

    # 上传脚本
    sftp = ssh.open_sftp()
    sftp.put(tmpfile_path, remote_script_path)
    sftp.chmod(remote_script_path, 0o755)
    sftp.close()

    return tmpfile_path, remote_script_path


def get_ip_by_domain(domain: str) -> Optional[str]:
    """通过域名获取IP地址"""
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        print(f"无法解析域名: {domain}")
        return None


def is_foreign_ip(ip: str) -> bool:
    """判断IP是否为境外IP（简单实现，可根据需求扩展）"""
    # 中国IP段参考：https://ip.istef.info/
    china_ip_ranges = [
        '1.0.1.0/24', '1.0.2.0/23', '1.0.8.0/21', '1.1.0.0/24',
        # ...可以添加更多中国IP段...
    ]

    # 使用第三方库ipaddress进行IP范围检查
    try:
        import ipaddress
        ip_obj = ipaddress.ip_address(ip)

        for network in china_ip_ranges:
            if ip_obj in ipaddress.ip_network(network):
                return False  # 是中国IP

        return True  # 不在中国IP范围内，视为境外IP
    except ImportError:
        print("缺少必要依赖: pip install ipaddress")
        return True  # 缺少依赖时默认视为境外IP


def update_hosts_with_domains(domains: List[str]) -> int:
    """更新hosts文件，返回实际写入的条目数"""
    # 收集有效域名-IP对
    domain_ip_pairs = []
    for domain in domains:
        ip = resolve_domain_ip(domain)
        if ip and is_valid_ip(ip):
            domain_ip_pairs.append((domain, ip))

    if not domain_ip_pairs:
        print("[ERROR] 没有有效的域名-IP对")
        return 0

    temp_hosts = os.path.join(PROJECT_ROOT, 'temp_hosts.txt')
    try:
        # 读取现有hosts内容
        original_hosts = []
        if os.path.exists(HOSTS_FILE):
            with open(HOSTS_FILE, 'r', encoding='utf-8') as f:
                original_hosts = f.readlines()

        # 创建域名IP映射
        domain_ip_map = {}
        for domain, ip in domain_ip_pairs:
            if domain not in domain_ip_map or is_global_ip(ip):
                domain_ip_map[domain] = ip

        # 生成域名变体
        processed_lines = []
        for domain, ip in domain_ip_map.items():
            add_domain_variants(processed_lines, ip, domain)

        # 去重排序
        unique_items = deduplicate_and_sort(processed_lines)

        # 写入临时文件
        with open(temp_hosts, 'w', encoding='utf-8') as f:
            # 写入非AUTOVPN管理的内容
            for line in original_hosts:
                if not line.startswith('# AUTOVPN') and not is_relevant_line(
                        line, domain_ip_map):
                    if line.strip():
                        f.write(line)

            # 写入新记录
            f.write('\n# AUTOVPN自动写入\n')
            for entry in unique_items:
                f.write(entry + '\n')
                logger.info(f"写入记录: {entry}")

        # 创建备份
        bak = HOSTS_FILE + '.' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.bak'
        shutil.copy(HOSTS_FILE, bak)
        logger.info(f"已备份原hosts到 {bak}")

        # 强制更新hosts文件
        if force_update_hosts(temp_hosts):
            # 验证写入结果
            if verify_hosts_update(unique_items):
                logger.info(f"[SUCCESS] 实际写入 {len(unique_items)} 条记录")
                return len(unique_items)
            else:
                logger.error("[ERROR] 文件内容验证失败")
                return 0
        else:
            return 0

    except Exception as e:
        logger.error(f"[CRITICAL] 主机文件更新异常: {e}", exc_info=True)
        return 0
    finally:
        cleanup_temp_file(temp_hosts)


def is_relevant_line(line: str, domain_map: dict) -> bool:
    """检查行是否包含相关域名"""
    return any(domain in line for domain in domain_map.keys())


def force_update_hosts(temp_path: str) -> bool:
    """强制更新hosts文件"""
    try:
        # 获取管理员权限
        import platform
        if platform.system() == "Windows":
            os.system(
                f'icacls "{HOSTS_FILE}" /grant administrators:F /t /c >nul 2>&1')

        os.chmod(HOSTS_FILE, 0o666)
        shutil.copy(temp_path, HOSTS_FILE)
        os.system('ipconfig /flushdns')
        return True
    except Exception as e:
        logger.error(f"[ERROR] 文件操作失败: {e}", exc_info=True)
        logger.info("[SYSTEM] 文件锁定状态:")
        os.system(f'handle.exe \"{HOSTS_FILE}\" 2>nul')
        return False


def verify_hosts_update(expected_items: list) -> bool:
    """验证hosts文件更新结果"""
    try:
        with open(HOSTS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查所有预期记录是否存在
        for item in expected_items:
            if item.split()[0] not in content:
                logger.error(f"[ERROR] 验证失败 - 缺失: {item}")
                return False
        return True
    except Exception as e:
        logger.error(f"[ERROR] 文件验证失败: {e}", exc_info=True)
        return False


def is_valid_ip(ip: str) -> bool:
    """验证IP地址有效性"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.version in (4, 6)  # IPv4或IPv6
    except ValueError:
        logger.error(f"[ERROR] 无效的IP地址: {ip}")
        return False


def is_global_ip(ip: str) -> bool:
    """判断IP是否为公网IP"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return not ip_obj.is_private
    except ValueError:
        return False


def add_domain_variants(lines: list, ip: str, domain: str):
    """添加域名及其变体"""
    lines.append(f"{ip}\t{domain}")
    if not domain.startswith(('www.', '*.')):
        lines.append(f"{ip}\twww.{domain}")


def deduplicate_and_sort(items: list) -> list:
    """去重并排序"""
    unique_items = set(items)
    try:
        return sorted(
            unique_items,
            key=lambda x: (ipaddress.ip_address(x.split()[0]), x.split()[1])
        )
    except Exception as e:
        logger.error(f"[ERROR] 排序失败：{e}", exc_info=True)
        return list(unique_items)


def cleanup_temp_file(temp_path: str):
    """清理临时文件"""
    try:
        if os.path.exists(temp_path):
            os.chmod(temp_path, 0o666)
            os.unlink(temp_path)
            logger.debug("[DEBUG] 临时文件已强制删除")
    except Exception as e:
        logger.error(f"[ERROR] 清理临时文件失败: {e}", exc_info=True)


def www_domain(domain: str) -> str:
    """生成www版本域名"""
    return f"www.{domain}" if not domain.startswith('www.') else domain


def generate_domain_variants(domain: str) -> List[str]:
    """生成域名变体（包含和不包含www）"""
    variants = [domain]
    if domain.startswith('www.'):
        variants.append(domain[4:])  # 添加不带www的版本
    else:
        variants.append(f"www.{domain}")  # 添加带www的版本
    return variants


def ensure_admin_rights() -> bool:
    """确保脚本以管理员权限运行"""
    try:
        # Only works on Windows
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except BaseException:
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("📢 使用方法: python add_single_domain.py domain1.com domain2.com ...")
        sys.exit(1)

    domains_input = sys.argv[1:]
    total_domains = len(domains_input)
    success_count = 0
    failed_domains = []

    # 加载配置
    ssh_config = load_config()
    if not ssh_config:
        print("[ERROR] 配置加载失败")
        sys.exit(1)

    # 验证必要字段
    required_fields = ['hostname', 'username', 'password']
    missing_fields = [f for f in required_fields if not ssh_config.get(f)]
    if missing_fields:
        print(f"[ERROR] 缺少必要配置字段: {', '.join(missing_fields)}")
        print("请检查config.json文件中的SSH配置")
        sys.exit(1)

    # 建立SSH连接
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            hostname=ssh_config['hostname'],
            username=ssh_config['username'],
            password=ssh_config['password'],
            timeout=10
        )
        print("[INFO] SSH连接已建立")
    except socket.gaierror as e:
        print(f"[ERROR] 主机名解析失败: {e}")
        print("请检查远程服务器地址是否正确")
        sys.exit(1)
    except (paramiko.SSHException, socket.error) as e:
        print(f"[ERROR] SSH连接失败: {e}")
        print("请检查网络连接和远程服务器配置")
        sys.exit(1)

    print(f"\n=> 开始处理 {total_domains} 个域名...")

    for i, domain in enumerate(domains_input, start=1):
        print(f"{'-' * 40}")
        print(f"> 正在处理第 {i}/{total_domains} 个域名: {domain}")
        print(f"{'-' * 40}")

        # 解析域名IP
        ip = resolve_domain_ip(ssh, domain)
        if not ip:
            print(f"[❌] 域名解析失败: {domain}")
            failed_domains.append(domain)
            continue

        # 创建域名对
        domains = []
        domain_ip_map = {domain: ip}
        processed_lines = []
        for d, ip in domain_ip_map.items():
            if d.startswith('www.'):
                non_www_domain = d[4:]
                processed_lines.append(f"{ip}\t{d}")
                processed_lines.append(f"{ip}\t{non_www_domain}")
                domains.append(d)
                domains.append(non_www_domain)
            elif not d.startswith('*.'):
                processed_lines.append(f"{ip}\t{d}")
                processed_lines.append(f"{ip}\twww.{d}")
                domains.append(d)
                domains.append(f"www.{d}")
            else:
                processed_lines.append(f"{ip}\t{d}")
                domains.append(d)

        # 更新hosts文件
        result = update_hosts_with_domains(domains)
        if result > 0:
            print(f"[✅] 成功更新hosts文件，新增{result}条记录")
            success_count += 1
        else:
            print(f"[❌] Hosts文件更新失败: {domain}")
            failed_domains.append(domain)

    print("\n🎉 处理完成！")
    print(f"✅ 成功: {success_count} 个域名")
    if failed_domains:
        print(f"❌ 失败: {len(failed_domains)} 个域名")
        print("   失败列表:")
        for d in failed_domains:
            print(f"     - {d}")

    # 关闭SSH连接
    if ssh:
        ssh.close()
        print("[INFO] SSH连接已关闭")
