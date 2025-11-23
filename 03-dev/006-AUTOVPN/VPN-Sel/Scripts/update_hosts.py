import os
import shutil
import datetime
import logging
from typing import Optional, List, Tuple

# 配置日志记录
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 定义全局变量
IP_FILE = r'S:\YDS-Lab\03-dev\006-AUTOVPN\VPN-Sel\routes\常用境外IP.txt'
HOSTS_FILE = r'C:\Windows\System32\drivers\etc\hosts'


def update_hosts_file(
    ip_list_file_path: str,
    hosts_file_path: Optional[str] = HOSTS_FILE,
    backup: bool = True
) -> int:
    """更新hosts文件的公共函数

    Args:
        ip_list_file_path (str): IP列表文件路径
        hosts_file_path (Optional[str]): hosts文件路径，默认使用全局HOSTS_FILE
        backup (bool): 是否创建备份文件，默认True

    Returns:
        int: 更新的条目数量，失败返回0
    """
    global logger
    logger = logging.getLogger(__name__)

    # 如果未指定hosts文件路径，使用全局默认路径
    if hosts_file_path is None:
        hosts_file_path = HOSTS_FILE

    if not os.path.exists(ip_list_file_path):
        logger.error("常用境外IP.txt 不存在！")
        return 0
    with open(ip_list_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 去重、过滤无效行
    ip_set = set()
    valid_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and (' ' in line or '\t' in line):
            if line not in ip_set:
                ip_set.add(line)
                valid_lines.append(line)

    if not valid_lines:
        logger.error("没有有效的IP记录！")
        return 0

    # 处理域名对，自动补充www和非www版本
    processed_lines = process_domain_pairs(valid_lines)
    valid_entries_count = len(processed_lines)

    # 备份原hosts
    bak = hosts_file_path + '.' + \
        datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.bak'
    try:
        shutil.copy(hosts_file_path, bak)
        logger.info(f"已备份原hosts到 {bak}")
    except Exception as e:
        logger.error(f"备份hosts文件失败: {e}")
        return 0

    # 写入新hosts
    try:
        with open(hosts_file_path, 'w', encoding='utf-8') as f:
            f.write('# AUTOVPN自动写入\n')
            for entry_line in processed_lines:
                f.write(entry_line + '\n')
        success = True
        logger.info(f"已写入Hosts文件，共{valid_entries_count}条记录（已自动补充www/非www域名对）")
    except Exception as e:
        logger.error(f"写入hosts文件失败: {e}")
        success = False

    if success:
        logger.info("Local hosts file updated successfully.")
        return valid_entries_count  # 返回成功处理的条目数
    else:
        logger.error("Failed to write to hosts file")
        return 0  # 返回0表示失败


def process_domain_pairs(valid_lines):
    """处理域名对，自动补充www和非www版本"""
    domain_ip_map = {}
    processed_lines = []

    # 解析现有的IP-域名映射
    for line in valid_lines:
        parts = line.split()
        if len(parts) >= 2:
            ip = parts[0]
            domain = parts[1]

            # 跳过通配符域名和已经处理过的特殊格式
            if '*' in domain or domain.startswith('*.') or '\\*' in domain:
                processed_lines.append(line)
                continue

            domain_ip_map[domain] = ip

    # 为每个域名生成www和非www版本
    for domain, ip in domain_ip_map.items():
        if domain.startswith('www.'):
            # 如果是www域名，生成非www版本
            non_www_domain = domain[4:]  # 去掉'www.'
            processed_lines.append(f"{ip}\t{domain}")
            if non_www_domain not in domain_ip_map:
                processed_lines.append(f"{ip}\t{non_www_domain}")
        else:
            # 如果是非www域名，生成www版本
            www_domain = f"www.{domain}"
            processed_lines.append(f"{ip}\t{domain}")
            if www_domain not in domain_ip_map:
                processed_lines.append(f"{ip}\t{www_domain}")

    return processed_lines


def main():
    if not os.path.exists(IP_FILE):
        print("常用境外IP.txt 不存在！")
        return
    with open(IP_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 去重、过滤无效行
    ip_set = set()
    valid_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and (' ' in line or '\t' in line):
            if line not in ip_set:
                ip_set.add(line)
                valid_lines.append(line)

    if not valid_lines:
        print("没有有效的IP记录！")
        return

    # 处理域名对，自动补充www和非www版本
    processed_lines = process_domain_pairs(valid_lines)

    # 备份原hosts
    bak = HOSTS_FILE + '.' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.bak'
    try:
        shutil.copy(HOSTS_FILE, bak)
        print(f"已备份原hosts到 {bak}")
    except Exception as e:
        print(f"备份hosts文件失败: {e}")
        return

    # 写入新hosts
    try:
        with open(HOSTS_FILE, 'w', encoding='utf-8') as f:
            f.write('# AUTOVPN自动写入\n')
            for entry_line in processed_lines:
                f.write(entry_line + '\n')
        print(f"已写入Hosts文件，共{len(processed_lines)}条记录（已自动补充www/非www域名对）")
    except Exception as e:
        print(f"写入hosts文件失败: {e}")


if __name__ == "__main__":
    main()