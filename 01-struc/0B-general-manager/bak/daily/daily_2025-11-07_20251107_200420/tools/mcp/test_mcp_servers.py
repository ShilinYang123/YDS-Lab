#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab MCP服务器测试工具
功能：测试Excel、Word、PowerPoint等MCP服务器的功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import sys
import importlib.util
from pathlib import Path

def test_import(module_path, module_name):
    """测试模块导入"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            return False, f"无法创建模块规范: {module_path}"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, f"成功导入 {module_name}"
    except Exception as e:
        return False, f"导入失败 {module_name}: {str(e)}"

def test_dependencies():
    """测试依赖包"""
    dependencies = ['openpyxl', 'python-docx', 'python-pptx', 'pandas']
    results = {}
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            results[dep] = (True, "已安装")
        except ImportError:
            results[dep] = (False, "未安装")
    
    return results

def main():
    """主测试函数"""
    print("=== YDS-Lab MCP服务器测试 ===")
    print()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    mcp_dir = project_root / "tools2" / "MCP"
    
    print(f"项目根目录: {project_root}")
    print(f"MCP目录: {mcp_dir}")
    print()
    
    # 测试依赖包
    print("1. 测试依赖包...")
    dep_results = test_dependencies()
    for dep, (success, message) in dep_results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {dep}: {message}")
    print()
    
    # 定义要测试的MCP服务器
    mcp_servers = {
        "Excel MCP Server": mcp_dir / "office" / "excel_mcp_server.py",
        "Word MCP Server": mcp_dir / "office" / "word-mcp" / "word_mcp_server.py", 
        "PowerPoint MCP Server": mcp_dir / "office" / "powerpoint-mcp" / "ppt_mcp_server.py",
        "Photoshop MCP Server": mcp_dir / "graphics" / "adobe-mcp-unified" / "adobe_mcp" / "photoshop" / "server.py",
        "AutoCAD MCP Server": mcp_dir / "cad" / "autocad-mcp" / "server_lisp.py",
        "General CAD MCP Server": mcp_dir / "cad" / "cad-mcp" / "src" / "server.py",
        "Illustrator MCP Server": mcp_dir / "graphics" / "illustrator-mcp-windows" / "src" / "illustrator" / "illustrator" / "server.py",
        "ModelScope Windows MCP Server": mcp_dir / "graphics" / "mcp-windows" / "server.py"
    }
    
    # 测试MCP服务器导入
    print("2. 测试MCP服务器导入...")
    import_results = {}
    
    for server_name, server_path in mcp_servers.items():
        if server_path.exists():
            success, message = test_import(server_path, server_name.replace(" ", "_"))
            import_results[server_name] = (success, message)
            status = "[OK]" if success else "[FAIL]"
            print(f"  {status} {server_name}: {message}")
        else:
            import_results[server_name] = (False, f"文件不存在: {server_path}")
            print(f"  [FAIL] {server_name}: 文件不存在")
    print()
    
    # 生成测试总结
    print("=== 测试总结 ===")
    
    # 依赖包总结
    dep_success = sum(1 for success, _ in dep_results.values() if success)
    dep_total = len(dep_results)
    print(f"依赖包测试: {dep_success}/{dep_total} 通过")
    
    # MCP服务器总结
    import_success = sum(1 for success, _ in import_results.values() if success)
    import_total = len(import_results)
    print(f"MCP服务器测试: {import_success}/{import_total} 通过")
    
    # 整体状态
    overall_success = dep_success == dep_total and import_success > 0
    if overall_success:
        print("✅ 测试基本通过，MCP服务器环境可用")
    else:
        print("❌ 测试发现问题，请检查依赖和MCP服务器文件")
        
        # 提供修复建议
        print("\n修复建议:")
        for dep, (success, _) in dep_results.items():
            if not success:
                print(f"  安装依赖: pip install {dep}")
        
        missing_servers = [name for name, (success, _) in import_results.items() if not success]
        if missing_servers:
            print(f"  检查MCP服务器文件是否存在于: {mcp_dir}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)