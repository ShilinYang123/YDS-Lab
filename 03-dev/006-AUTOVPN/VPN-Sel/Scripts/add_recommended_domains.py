#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加推荐域名到解析列表的脚本
"""

import os
import sys

# 添加脚本目录到Python路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

def add_recommended_domains():
    """添加推荐域名到解析列表"""
    print("=== 添加推荐域名 ===")
    
    # 定义文件路径
    domain_list_path = os.path.join(PROJECT_ROOT, "routes", "需要获取IP的域名列表.txt")
    recommended_domains_path = os.path.join(SCRIPT_DIR, "recommended_domains.txt")
    
    # 检查推荐域名文件是否存在
    if not os.path.exists(recommended_domains_path):
        print(f"[错误] 推荐域名文件不存在: {recommended_domains_path}")
        return False
    
    # 读取现有的域名列表
    existing_domains = set()
    if os.path.exists(domain_list_path):
        with open(domain_list_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    existing_domains.add(line.lower())
    
    # 读取推荐域名
    recommended_domains = []
    with open(recommended_domains_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释行和空行
            if line and not line.startswith('#'):
                # 只添加域名部分（去除可能的注释）
                domain = line.split('#')[0].strip()
                if domain:
                    recommended_domains.append(domain)
    
    print(f"推荐域名文件中共有 {len(recommended_domains)} 个域名")
    
    # 分类显示域名
    ai_domains = []
    ecommerce_domains = []
    other_domains = []
    
    for domain in recommended_domains:
        if any(keyword in domain for keyword in ['github', 'huggingface', 'google', 'kaggle', 'stackoverflow', 
                                                'arxiv', 'pytorch', 'tensorflow', 'keras', 'openai', 'anthropic']):
            ai_domains.append(domain)
        elif any(keyword in domain for keyword in ['amazon', 'ebay', 'aliexpress', 'alibaba', 'walmart', 'etsy', 
                                                  'shopify', 'wayfair', 'overstock', 'newegg', 'bestbuy']):
            ecommerce_domains.append(domain)
        else:
            other_domains.append(domain)
    
    print(f"\nAI编程相关域名 ({len(ai_domains)} 个):")
    for domain in ai_domains[:10]:  # 只显示前10个
        print(f"  - {domain}")
    if len(ai_domains) > 10:
        print(f"  ... 还有 {len(ai_domains) - 10} 个域名")
    
    print(f"\n海外贸易/电商相关域名 ({len(ecommerce_domains)} 个):")
    for domain in ecommerce_domains[:10]:  # 只显示前10个
        print(f"  - {domain}")
    if len(ecommerce_domains) > 10:
        print(f"  ... 还有 {len(ecommerce_domains) - 10} 个域名")
    
    print(f"\n其他域名 ({len(other_domains)} 个):")
    for domain in other_domains[:10]:  # 只显示前10个
        print(f"  - {domain}")
    if len(other_domains) > 10:
        print(f"  ... 还有 {len(other_domains) - 10} 个域名")
    
    # 询问用户要添加哪些域名
    print("\n请选择要添加的域名类型:")
    print("1. 所有推荐域名")
    print("2. AI编程相关域名")
    print("3. 海外贸易/电商相关域名")
    print("4. 自定义输入")
    
    choice = input("请输入选择 (1-4, 默认为1): ").strip()
    
    domains_to_add = []
    if choice == '2':
        domains_to_add = ai_domains
        print(f"选择了AI编程相关域名 ({len(domains_to_add)} 个)")
    elif choice == '3':
        domains_to_add = ecommerce_domains
        print(f"选择了海外贸易/电商相关域名 ({len(domains_to_add)} 个)")
    elif choice == '4':
        custom_input = input("请输入要添加的域名 (多个域名用空格分隔): ").strip()
        if custom_input:
            domains_to_add = custom_input.split()
            print(f"选择了自定义域名 ({len(domains_to_add)} 个)")
        else:
            print("未输入自定义域名")
    else:
        domains_to_add = recommended_domains
        print(f"选择了所有推荐域名 ({len(domains_to_add)} 个)")
    
    # 过滤已存在的域名
    new_domains = []
    for domain in domains_to_add:
        if domain.lower() not in existing_domains:
            new_domains.append(domain)
        else:
            print(f"域名 {domain} 已存在于列表中，跳过")
    
    if not new_domains:
        print("没有新的域名需要添加")
        return True
    
    print(f"\n将添加 {len(new_domains)} 个新域名:")
    for domain in new_domains[:10]:  # 只显示前10个
        print(f"  - {domain}")
    if len(new_domains) > 10:
        print(f"  ... 还有 {len(new_domains) - 10} 个域名")
    
    # 确认添加
    confirm = input(f"\n确认添加这 {len(new_domains)} 个域名到解析列表? (y/n, 默认为y): ").strip().lower()
    if confirm != 'n':
        # 添加到域名列表文件
        try:
            with open(domain_list_path, 'a', encoding='utf-8') as f:
                for domain in new_domains:
                    f.write(f"{domain}\n")
            
            print(f"✅ 成功添加 {len(new_domains)} 个域名到解析列表")
            print("请使用菜单选项6进行域名解析")
            return True
        except Exception as e:
            print(f"[错误] 添加域名时出现异常: {e}")
            return False
    else:
        print("取消添加域名")
        return True

def main():
    success = add_recommended_domains()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()