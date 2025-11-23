#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量域名解析脚本
用于处理大量域名的解析，避免单次解析超时
"""

import os
import sys
import time
import shutil
import logging
import subprocess
import traceback
from datetime import datetime

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# 配置文件路径
DOMAIN_LIST_PATH = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
IP_LIST_PATH = os.path.join(PROJECT_ROOT, "routes", "常用境外IP.txt")
HOSTS_FILE_PATH = "C:/Windows/System32/drivers/etc/hosts"
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE_NAME = "batch_domain_resolver.log"

# 批处理配置
BATCH_SIZE = 20  # 每批处理的域名数量
BATCH_DELAY = 5  # 批次间延迟（秒）

# 设置日志
def setup_logging():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    log_file_path = os.path.join(LOG_DIR, LOG_FILE_NAME)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# 读取域名列表
def read_domain_list(file_path):
    domains = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    domains.append(line)
        return domains
    except Exception as e:
        logger.error(f"读取域名列表失败: {e}")
        return []

# 创建临时域名列表文件
def create_temp_domain_file(domains, batch_index):
    temp_file_path = os.path.join(PROJECT_ROOT, "routes", f"temp_domain_list_{batch_index}.txt")
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write("# 需要获取IP的域名列表\n")
            f.write("# 每行一个域名，支持通配符格式（如 *.example.com）\n")
            f.write("# 自动清理：去除协议、路径、端口、注释等\n\n")
            for domain in domains:
                f.write(f"{domain}\n")
        return temp_file_path
    except Exception as e:
        logger.error(f"创建临时域名文件失败: {e}")
        return None

# 处理单批域名
def process_batch(domains, batch_index, total_batches):
    logger.info(f"处理批次 {batch_index+1}/{total_batches}，包含 {len(domains)} 个域名")
    
    # 只在第一批次时备份原始域名列表
    backup_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表_backup.txt")
    if batch_index == 0:  # 只在第一批次时备份
        try:
            if os.path.exists(DOMAIN_LIST_PATH):
                shutil.copy2(DOMAIN_LIST_PATH, backup_path)
                logger.info(f"已备份原始域名列表到 {backup_path}")
        except Exception as e:
            logger.error(f"备份域名列表失败: {e}")
            return False
    
    # 创建临时域名文件
    temp_file_path = create_temp_domain_file(domains, batch_index)
    if not temp_file_path:
        return False
    
    # 替换原始域名列表
    try:
        shutil.copy2(temp_file_path, DOMAIN_LIST_PATH)
        logger.info(f"已替换域名列表为批次 {batch_index+1} 的 {len(domains)} 个域名")
    except Exception as e:
        logger.error(f"替换域名列表失败: {e}")
        return False
    
    # 调用解析脚本
    resolve_script = os.path.join(SCRIPT_DIR, "resolve_ip_remote.py")
    if not os.path.exists(resolve_script):
        logger.error(f"解析脚本不存在: {resolve_script}")
        return False
    
    try:
        logger.info(f"开始执行解析脚本处理批次 {batch_index+1}...")
        result = subprocess.run(
            [sys.executable, resolve_script],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )
        
        if result.returncode == 0:
            logger.info(f"批次 {batch_index+1} 解析完成")
            # 记录输出信息
            if result.stdout:
                for line in result.stdout.splitlines():
                    if "[INFO]" in line or "成功" in line:
                        logger.info(f"解析输出: {line}")
            return True
        else:
            logger.error(f"批次 {batch_index+1} 解析失败，返回码: {result.returncode}")
            if result.stderr:
                logger.error(f"错误信息: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"执行解析脚本失败: {e}")
        return False
    finally:
        # 清理临时文件
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

# 恢复原始域名列表
def restore_domain_list(backup_path):
    try:
        if os.path.exists(backup_path):
            # 先检查备份文件是否有效
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_domains = [line.strip() for line in f if line.strip()]
            
            if not backup_domains:
                logger.error(f"备份文件内容为空: {backup_path}")
                return False
                
            logger.info(f"备份文件包含 {len(backup_domains)} 个域名")
            
            # 复制备份文件到原始文件
            shutil.copy2(backup_path, DOMAIN_LIST_PATH)
            logger.info("已恢复原始域名列表")
            
            # 验证恢复是否成功
            if os.path.exists(DOMAIN_LIST_PATH):
                with open(DOMAIN_LIST_PATH, 'r', encoding='utf-8') as f:
                    restored_domains = [line.strip() for line in f if line.strip()]
                
                if len(restored_domains) == len(backup_domains):
                    logger.info(f"恢复后的域名列表包含 {len(restored_domains)} 个域名，恢复成功")
                    # 恢复成功后可以删除备份文件
                    try:
                        os.remove(backup_path)
                        logger.info(f"已删除备份文件: {backup_path}")
                    except Exception as e:
                        logger.warning(f"删除备份文件失败: {e}")
                    return True
                else:
                    logger.error(f"恢复后的域名数量不匹配: 备份 {len(backup_domains)} 个，恢复后 {len(restored_domains)} 个")
                    return False
            else:
                logger.error(f"恢复后域名列表文件不存在: {DOMAIN_LIST_PATH}")
                return False
        else:
            logger.error(f"备份文件不存在: {backup_path}")
            return False
    except Exception as e:
        logger.error(f"恢复域名列表失败: {e}")
        logger.error(traceback.format_exc())
        return False

# 合并IP列表结果
def merge_ip_results():
    # 创建一个字典来存储所有批次的解析结果
    all_results = {}
    
    # 读取当前IP列表文件
    try:
        if os.path.exists(IP_LIST_PATH):
            with open(IP_LIST_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('\t', 1)
                        if len(parts) == 2:
                            # 格式是 IP\t域名
                            ip, domain = parts
                            all_results[domain] = ip
            logger.info(f"已读取现有IP列表，包含 {len(all_results)} 个域名的IP")
    except Exception as e:
        logger.error(f"读取IP列表失败: {e}")
    
    # 从日志中提取所有批次的解析结果
    try:
        log_file_path = os.path.join(LOG_DIR, LOG_FILE_NAME)
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()
                
                # 使用正则表达式提取所有包含Selected for的行
                import re
                # 匹配格式: "==> Selected for domain.com (after connectivity check): 123.456.789.10"
                selected_ips = re.findall(r"==> Selected for ([\w\.-]+) \(after connectivity check\): ([\d\.]+)", log_content)
                
                logger.info(f"从日志中找到了 {len(selected_ips)} 个域名的IP地址")
                for domain, ip in selected_ips:
                    all_results[domain] = ip
                    logger.debug(f"从日志提取: 域名 {domain} -> IP {ip}")
                    
                logger.info(f"成功从日志中提取并合并了 {len(selected_ips)} 个域名的IP地址")
    except Exception as e:
        logger.error(f"从日志中提取IP地址失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # 保存合并后的结果
    try:
        with open(IP_LIST_PATH, 'w', encoding='utf-8') as f:
            for domain, ip in all_results.items():
                f.write(f"{ip}\t{domain}\n")
        logger.info(f"所有批次处理完成，IP列表已更新，共 {len(all_results)} 个域名")
        return True
    except Exception as e:
        logger.error(f"保存合并后的IP列表失败: {e}")
        return False

# 主函数
def main():
    print("\n===== 批量域名解析工具 =====\n")
    
    # 检查是否有备份文件，如果有，先恢复
    backup_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表_backup.txt")
    if os.path.exists(backup_path):
        logger.info("发现上次的备份文件，先恢复原始域名列表")
        restore_domain_list(backup_path)
    
    # 读取域名列表
    domains = read_domain_list(DOMAIN_LIST_PATH)
    if not domains:
        logger.error("域名列表为空或读取失败")
        return
    
    total_domains = len(domains)
    logger.info(f"共读取到 {total_domains} 个域名")
    
    # 计算批次数
    total_batches = (total_domains + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"将分为 {total_batches} 个批次处理，每批 {BATCH_SIZE} 个域名")
    
    # 备份原始域名列表
    backup_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表_backup.txt")
    if os.path.exists(DOMAIN_LIST_PATH):
        try:
            # 读取原始域名列表
            with open(DOMAIN_LIST_PATH, 'r', encoding='utf-8') as f:
                original_domains = [line.strip() for line in f if line.strip()]
            
            if not original_domains:
                logger.warning("原始域名列表为空，无需备份")
            else:
                # 创建备份
                shutil.copy2(DOMAIN_LIST_PATH, backup_path)
                
                # 验证备份是否成功
                if os.path.exists(backup_path):
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        backup_domains = [line.strip() for line in f if line.strip()]
                    
                    if len(backup_domains) == len(original_domains):
                        logger.info(f"已成功备份原始域名列表到 {backup_path}，包含 {len(backup_domains)} 个域名")
                    else:
                        logger.error(f"备份域名数量不匹配: 原始 {len(original_domains)} 个，备份 {len(backup_domains)} 个")
                else:
                    logger.error(f"备份文件创建失败: {backup_path}")
        except Exception as e:
            logger.error(f"备份原始域名列表失败: {e}")
            logger.error(traceback.format_exc())
    
    # 批量处理
    success_count = 0
    for i in range(total_batches):
        start_idx = i * BATCH_SIZE
        end_idx = min((i + 1) * BATCH_SIZE, total_domains)
        batch_domains = domains[start_idx:end_idx]
        
        print(f"\n[批次 {i+1}/{total_batches}] 处理 {len(batch_domains)} 个域名 ({start_idx+1}-{end_idx}/{total_domains})")
        
        if process_batch(batch_domains, i, total_batches):
            success_count += 1
        
        # 最后一批次不需要延迟
        if i < total_batches - 1:
            print(f"等待 {BATCH_DELAY} 秒后处理下一批次...")
            time.sleep(BATCH_DELAY)
    
    # 恢复原始域名列表
    if not restore_domain_list(backup_path):
        logger.error("恢复原始域名列表失败，尝试重新恢复")
        # 如果第一次恢复失败，再尝试一次
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, DOMAIN_LIST_PATH)
                logger.info("第二次尝试恢复原始域名列表")
                if os.path.exists(DOMAIN_LIST_PATH):
                    with open(DOMAIN_LIST_PATH, 'r', encoding='utf-8') as f:
                        restored_domains = [line.strip() for line in f if line.strip()]
                    logger.info(f"第二次恢复后的域名列表包含 {len(restored_domains)} 个域名")
            except Exception as e:
                logger.error(f"第二次恢复域名列表失败: {e}")
                logger.error(traceback.format_exc())
    
    # 合并所有批次的结果
    merge_ip_results()
    
    # 输出结果
    print("\n===== 批量解析完成 =====")
    print(f"总批次: {total_batches}, 成功: {success_count}, 失败: {total_batches - success_count}")
    print(f"解析结果已保存到: {IP_LIST_PATH}")
    print("\n批量解析完成，自动返回主菜单...")

if __name__ == "__main__":
    logger = setup_logging()
    backup_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表_backup.txt")
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断操作")
        # 恢复原始域名列表
        if os.path.exists(backup_path):
            logger.info("用户中断，尝试恢复原始域名列表")
            restore_domain_list(backup_path)
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        print(f"\n程序执行出错: {e}")
        # 确保在异常时也恢复原始域名列表
        if os.path.exists(backup_path):
            logger.info("程序异常，尝试恢复原始域名列表")
            restore_domain_list(backup_path)
        import traceback
        logger.error(traceback.format_exc())
        print("程序异常退出...")