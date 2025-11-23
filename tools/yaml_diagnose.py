#!/usr/bin/env python3
"""
YAML文件语法诊断工具
"""

import yaml
import sys
import os

def diagnose_yaml_file(file_path):
    """诊断YAML文件语法问题"""
    print(f"🔍 诊断文件: {file_path}")
    print("="*50)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📊 文件统计信息:")
        print(f"  总字符数: {len(content)}")
        print(f"  总行数: {len(content.splitlines())}")
        print(f"  文件编码: UTF-8")
        
        # 尝试解析
        try:
            data = yaml.safe_load(content)
            print("✅ YAML语法正确!")
            return True
        except yaml.YAMLError as e:
            print(f"❌ YAML语法错误:")
            print(f"  错误类型: {type(e).__name__}")
            print(f"  错误信息: {e}")
            
            # 显示错误位置
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                print(f"  错误位置: 行 {mark.line + 1}, 列 {mark.column + 1}")
                
                # 显示错误行及其上下文
                lines = content.splitlines()
                if 0 <= mark.line < len(lines):
                    print(f"  错误行内容:")
                    start_line = max(0, mark.line - 2)
                    end_line = min(len(lines), mark.line + 3)
                    
                    for i in range(start_line, end_line):
                        prefix = ">>> " if i == mark.line else "    "
                        print(f"{prefix}行 {i+1}: {lines[i]}")
                        if i == mark.line:
                            print(f"     {' ' * (len(str(i+1)) + 2)}{' ' * mark.column}^")
            
            return False
            
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return False
    except Exception as e:
        print(f"❌ 文件读取错误: {e}")
        return False

def check_common_yaml_issues(content):
    """检查常见的YAML问题"""
    print("\n🔍 检查常见YAML问题:")
    lines = content.splitlines()
    issues = []
    
    for i, line in enumerate(lines, 1):
        # 检查缩进问题
        if line.strip() and not line.startswith('#'):
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 2 != 0 and leading_spaces > 0:
                issues.append(f"行 {i}: 缩进可能不一致 (空格数: {leading_spaces})")
        
        # 检查制表符
        if '\t' in line:
            issues.append(f"行 {i}: 包含制表符，应该使用空格")
        
        # 检查特殊字符
        if '\u2028' in line or '\u2029' in line:  # Unicode行分隔符
            issues.append(f"行 {i}: 包含Unicode行分隔符")
    
    if issues:
        print("⚠️  发现潜在问题:")
        for issue in issues[:5]:  # 只显示前5个问题
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... 还有 {len(issues) - 5} 个问题")
    else:
        print("✅ 未发现明显的格式问题")

if __name__ == "__main__":
    file_path = r"S:\YDS-Lab\01-struc\Agents\01-ceo\config\agent_config.yaml"
    
    print("🔧 YAML文件诊断工具")
    print("="*50)
    
    # 主要诊断
    success = diagnose_yaml_file(file_path)
    
    # 如果文件存在，进行详细检查
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        check_common_yaml_issues(content)
    
    print("\n" + "="*50)
    if success:
        print("✅ 文件诊断完成 - 未发现语法错误")
    else:
        print("❌ 文件诊断完成 - 发现语法错误需要修复")
        
    sys.exit(0 if success else 1)