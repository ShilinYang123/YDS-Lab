import os
import sys
import time
import signal
import subprocess
import shutil

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 域名列表路径
DOMAIN_LIST_PATH = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
# 备份文件路径
BACKUP_PATH = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表_backup.txt")
# 测试域名列表路径
TEST_DOMAIN_LIST_PATH = os.path.join(PROJECT_ROOT, "routes", "测试用域名列表.txt")

def setup_test():
    """准备测试环境"""
    print("\n===== 准备测试环境 =====")
    
    # 确保没有残留的备份文件
    if os.path.exists(BACKUP_PATH):
        os.remove(BACKUP_PATH)
        print(f"已删除残留的备份文件: {BACKUP_PATH}")
    
    # 备份当前的域名列表
    if os.path.exists(DOMAIN_LIST_PATH):
        # 创建测试用备份
        shutil.copy2(DOMAIN_LIST_PATH, TEST_DOMAIN_LIST_PATH)
        print(f"已备份当前域名列表到: {TEST_DOMAIN_LIST_PATH}")
        
        # 统计域名数量
        with open(DOMAIN_LIST_PATH, 'r', encoding='utf-8') as f:
            domains = [line.strip() for line in f if line.strip()]
        print(f"当前域名列表包含 {len(domains)} 个域名")
    else:
        print(f"错误: 域名列表文件不存在: {DOMAIN_LIST_PATH}")
        sys.exit(1)

def run_test():
    """运行测试"""
    print("\n===== 开始测试 =====")
    print("1. 启动批量域名解析脚本")
    
    # 启动批量域名解析脚本
    process = subprocess.Popen([sys.executable, os.path.join(PROJECT_ROOT, "Scripts", "batch_domain_resolver.py")])
    
    # 等待一段时间，确保脚本已经创建了备份文件
    time.sleep(3)
    
    # 检查备份文件是否已创建
    if not os.path.exists(BACKUP_PATH):
        print(f"错误: 备份文件未创建: {BACKUP_PATH}")
        process.terminate()
        sys.exit(1)
    else:
        # 统计备份文件中的域名数量
        with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
            backup_domains = [line.strip() for line in f if line.strip()]
        print(f"备份文件已创建，包含 {len(backup_domains)} 个域名")
    
    print("2. 模拟脚本中断")
    # 发送中断信号
    process.terminate()
    
    # 等待进程结束
    try:
        process.wait(timeout=5)
        print("脚本已终止")
    except subprocess.TimeoutExpired:
        print("脚本未能及时终止，强制结束")
        process.kill()
    
    # 修改域名列表文件，模拟中断后的状态
    print("3. 模拟中断后的域名列表状态（只保留前5个域名）")
    with open(DOMAIN_LIST_PATH, 'r', encoding='utf-8') as f:
        domains = [line.strip() for line in f if line.strip()]
    
    # 只保留前5个域名
    with open(DOMAIN_LIST_PATH, 'w', encoding='utf-8') as f:
        for i in range(min(5, len(domains))):
            f.write(domains[i] + '\n')
    
    print(f"已修改域名列表，现在只包含 5 个域名")
    
    print("4. 再次运行批量域名解析脚本，检查是否能恢复域名列表")
    # 再次运行批量域名解析脚本
    process = subprocess.Popen([sys.executable, os.path.join(PROJECT_ROOT, "Scripts", "batch_domain_resolver.py")])
    
    # 等待一段时间，确保脚本已经恢复了域名列表
    time.sleep(5)
    
    # 终止脚本
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    
    # 检查域名列表是否已恢复
    if os.path.exists(DOMAIN_LIST_PATH):
        with open(DOMAIN_LIST_PATH, 'r', encoding='utf-8') as f:
            domains = [line.strip() for line in f if line.strip()]
        print(f"测试后域名列表包含 {len(domains)} 个域名")
        
        # 检查备份文件是否已删除
        if os.path.exists(BACKUP_PATH):
            print(f"备份文件仍然存在: {BACKUP_PATH}")
        else:
            print("备份文件已正确删除")
    else:
        print(f"错误: 域名列表文件不存在: {DOMAIN_LIST_PATH}")

def cleanup_test():
    """清理测试环境"""
    print("\n===== 清理测试环境 =====")
    
    # 恢复原始域名列表
    if os.path.exists(TEST_DOMAIN_LIST_PATH):
        shutil.copy2(TEST_DOMAIN_LIST_PATH, DOMAIN_LIST_PATH)
        print(f"已恢复原始域名列表")
        
        # 删除测试用备份
        os.remove(TEST_DOMAIN_LIST_PATH)
        print(f"已删除测试用备份: {TEST_DOMAIN_LIST_PATH}")
    
    # 确保没有残留的备份文件
    if os.path.exists(BACKUP_PATH):
        os.remove(BACKUP_PATH)
        print(f"已删除残留的备份文件: {BACKUP_PATH}")

def main():
    try:
        setup_test()
        run_test()
    finally:
        cleanup_test()
    
    print("\n===== 测试完成 =====")

if __name__ == "__main__":
    main()