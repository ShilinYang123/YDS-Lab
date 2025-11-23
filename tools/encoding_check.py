#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab文件编码检测工具
符合编码规范要求：发现第一个乱码文件立即停止并上报
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

def check_utf8_encoding(file_path):
    """检查文件是否为UTF-8编码（无BOM）"""
    try:
        # 检查文件头是否有BOM
        with open(file_path, 'rb') as f:
            first_bytes = f.read(3)
            if first_bytes == b'\xef\xbb\xbf':
                return False, "文件包含UTF-8 BOM头"
        
        # 尝试用UTF-8读取整个文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return True, "UTF-8编码正确"
        
    except UnicodeDecodeError as e:
        return False, f"UTF-8解码失败: {str(e)}"
    except Exception as e:
        return False, f"读取文件失败: {str(e)}"

def should_check_file(file_path):
    """判断是否应该检查该文件"""
    path = Path(file_path)
    
    # 只检查文本文件
    text_extensions = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.json', '.yml', '.yaml',
        '.md', '.txt', '.sh', '.bash', '.bat', '.cmd', '.css', '.html', '.htm',
        '.xml', '.ini', '.cfg', '.conf', '.properties', '.java', '.cpp', '.c',
        '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala'
    }
    
    if path.suffix.lower() not in text_extensions:
        return False
    
    # 排除目录
    exclude_dirs = {'.git', '__pycache__', 'node_modules', '.vscode', '.idea', 
                   'dist', 'build', 'target', 'venv', '.venv', 'env', '.env'}
    
    path_parts = str(path).split(os.sep)
    if any(exclude in path_parts for exclude in exclude_dirs):
        return False
    
    return True

def scan_project(project_path):
    """扫描项目目录"""
    print(f"🔍 开始扫描项目: {project_path}")
    print("=" * 60)
    
    total_files = 0
    checked_files = 0
    first_problem = None
    
    for root, dirs, files in os.walk(project_path):
        # 过滤排除目录
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules'}]
        
        for file in files:
            file_path = Path(root) / file
            
            if should_check_file(file_path):
                total_files += 1
                checked_files += 1
                
                # 显示进度
                if checked_files % 50 == 0:
                    print(f"  已检查 {checked_files} 个文件...")
                
                # 检查编码
                is_valid, message = check_utf8_encoding(file_path)
                
                if not is_valid:
                    print(f"\n❌ 发现编码问题文件！")
                    print(f"   文件路径: {file_path}")
                    print(f"   问题描述: {message}")
                    print(f"   发现时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # 记录第一个问题文件
                    if not first_problem:
                        first_problem = {
                            'file_path': str(file_path),
                            'issue': message,
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    # 立即停止扫描（符合规范要求）
                    print(f"\n🛑 根据规范要求，发现第一个乱码文件后立即停止扫描")
                    print("=" * 60)
                    return {
                        'status': 'stopped',
                        'reason': 'found_first_problem',
                        'first_problem': first_problem,
                        'total_files': total_files,
                        'checked_files': checked_files
                    }
    
    print(f"\n✅ 扫描完成，未发现编码问题")
    print(f"   总计检查 {checked_files} 个文件")
    print("=" * 60)
    
    return {
        'status': 'completed',
        'first_problem': None,
        'total_files': total_files,
        'checked_files': checked_files
    }

def generate_report(scan_results, project_path):
    """生成检测报告"""
    report = {
        'project': str(project_path),
        'scan_time': datetime.now().isoformat(),
        'status': scan_results['status'],
        'total_files': scan_results['total_files'],
        'checked_files': scan_results['checked_files'],
        'compliance_rate': 100.0 if scan_results['status'] == 'completed' else \
                          ((scan_results['checked_files'] - 1) / scan_results['checked_files'] * 100) \
                          if scan_results['checked_files'] > 0 else 0
    }
    
    if scan_results['first_problem']:
        report['first_problem'] = scan_results['first_problem']
    
    return report

def save_report(report, output_file):
    """保存检测报告"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📄 检测报告已保存: {output_file}")
    except Exception as e:
        print(f"⚠️  保存报告失败: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='YDS-Lab文件编码检测工具 - 符合编码规范要求',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python encoding_check.py                    # 检查当前目录
  python encoding_check.py /path/to/project   # 检查指定项目目录
  python encoding_check.py . --output report.json  # 生成检测报告
  python encoding_check.py . --strict          # 严格模式（发现问题立即退出）
        """
    )
    
    parser.add_argument('project_path', nargs='?', default='.',
                       help='要检查的项目目录路径（默认当前目录）')
    parser.add_argument('--output', '-o', help='输出检测报告文件（JSON格式）')
    parser.add_argument('--strict', action='store_true',
                       help='严格模式：发现问题立即退出并返回错误码')
    parser.add_argument('--no-stop', action='store_true',
                       help='继续扫描所有文件（不推荐，违反规范要求）')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='安静模式：只显示错误信息')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("=" * 60)
        print("YDS-Lab 文件编码检测工具")
        print("符合编码规范：发现第一个乱码文件立即停止并上报")
        print("=" * 60)
    
    project_path = Path(args.project_path).resolve()
    
    if not project_path.exists():
        print(f"❌ 项目路径不存在: {project_path}")
        return 1
    
    if not project_path.is_dir():
        print(f"❌ 路径不是目录: {project_path}")
        return 1
    
    # 执行扫描
    scan_results = scan_project(project_path)
    
    # 生成报告
    report = generate_report(scan_results, project_path)
    
    # 保存报告
    if args.output:
        save_report(report, args.output)
    
    # 返回结果
    if scan_results['status'] == 'stopped':
        if args.strict:
            print(f"\n🚨 严格模式：因发现编码问题，程序以错误码退出")
            return 1
        else:
            print(f"\n⚠️  发现编码问题，但继续执行（非严格模式）")
            return 0
    
    print(f"\n🎉 编码检测通过，所有文件符合UTF-8无BOM规范")
    return 0

if __name__ == '__main__':
    sys.exit(main())