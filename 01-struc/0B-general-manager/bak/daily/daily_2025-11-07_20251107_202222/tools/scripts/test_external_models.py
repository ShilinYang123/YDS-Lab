"""
外部模型配置测试脚本
验证S:\LLm目录配置是否正确
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "utils"))

try:
    from model_path_resolver import ModelPathResolver
except ImportError as e:
    print(f"❌ 无法导入模型路径解析器: {e}")
    sys.exit(1)

def test_directory_structure():
    """测试目录结构"""
    print("🔍 检查S:\\LLm目录结构...")
    
    required_dirs = [
        "S:/LLm",
        "S:/LLm/shimmy", 
        "S:/LLm/models",
        "S:/LLm/models/shimmy",
        "S:/LLm/models/lama",
        "S:/LLm/cache"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}")
        else:
            print(f"  ❌ {directory} (不存在)")
            all_exist = False
    
    return all_exist

def test_config_files():
    """测试配置文件"""
    print("\n🔍 检查配置文件...")
    
    config_files = [
        "S:/LLm/shimmy/config.yaml",
        "S:/LLm/models/lama/lama_config.yaml",
        "S:/LLm/models/config/external_models.json"
    ]
    
    all_exist = True
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  ✅ {config_file}")
        else:
            print(f"  ❌ {config_file} (不存在)")
            all_exist = False
    
    return all_exist

def test_environment_variables():
    """测试环境变量"""
    print("\n🔍 检查环境变量...")
    
    env_vars = ["LLM_ROOT", "SHIMMY_HOME", "MODELS_PATH"]
    all_set = True
    
    for var_name in env_vars:
        var_value = os.environ.get(var_name)
        if var_value:
            print(f"  ✅ {var_name}={var_value}")
        else:
            print(f"  ❌ {var_name} (未设置)")
            all_set = False
    
    return all_set

def test_model_path_resolver():
    """测试模型路径解析器"""
    print("\n🔍 测试模型路径解析器...")
    
    try:
        resolver = ModelPathResolver()
        
        # 测试Shimmy路径
        shimmy_path = resolver.get_shimmy_path()
        print(f"  Shimmy路径: {shimmy_path}")
        if os.path.exists(shimmy_path):
            print(f"    ✅ 文件存在")
        else:
            print(f"    ⚠️  文件不存在 (需要手动下载)")
        
        # 测试模型路径
        lama_path = resolver.get_model_path("lama")
        print(f"  LaMa模型目录: {lama_path}")
        if os.path.exists(lama_path):
            print(f"    ✅ 目录存在")
        else:
            print(f"    ❌ 目录不存在")
        
        # 测试LaMa模型文件
        lama_model_path = resolver.get_lama_model_path()
        print(f"  LaMa模型文件: {lama_model_path}")
        if os.path.exists(lama_model_path):
            print(f"    ✅ 文件存在")
        else:
            print(f"    ⚠️  文件不存在 (需要手动下载)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 路径解析器测试失败: {e}")
        return False

def test_symbolic_links():
    """测试符号链接"""
    print("\n🔍 检查符号链接...")
    
    project_models_dir = project_root / "projects" / "001-dewatermark-ai" / "assets" / "models"
    
    links = ["shimmy", "lama"]
    all_linked = True
    
    for link_name in links:
        link_path = project_models_dir / link_name
        if link_path.exists():
            if link_path.is_symlink():
                target = link_path.readlink()
                print(f"  ✅ {link_name} -> {target}")
            else:
                print(f"  ⚠️  {link_name} (普通目录，非符号链接)")
        else:
            print(f"  ❌ {link_name} (不存在)")
            all_linked = False
    
    return all_linked

def test_model_files():
    """测试模型文件"""
    print("\n🔍 检查模型文件...")
    
    model_files = [
        "S:/LLm/shimmy/shimmy.exe",
        "S:/LLm/models/shimmy/shimmy_model.onnx", 
        "S:/LLm/models/lama/lama_256.pth"
    ]
    
    files_exist = 0
    for model_file in model_files:
        if os.path.exists(model_file):
            size = os.path.getsize(model_file) / (1024 * 1024)  # MB
            print(f"  ✅ {model_file} ({size:.1f} MB)")
            files_exist += 1
        else:
            print(f"  ⚠️  {model_file} (需要手动下载)")
    
    return files_exist

def main():
    """主测试函数"""
    print("🧪 开始测试外部模型配置...\n")
    
    # 运行所有测试
    tests = [
        ("目录结构", test_directory_structure),
        ("配置文件", test_config_files), 
        ("环境变量", test_environment_variables),
        ("模型路径解析器", test_model_path_resolver),
        ("符号链接", test_symbolic_links)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # 检查模型文件
    model_files_count = test_model_files()
    
    # 汇总结果
    print("\n📊 测试结果汇总:")
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"  模型文件: {model_files_count}/3 个文件存在")
    
    # 总体评估
    all_passed = all(results.values())
    if all_passed and model_files_count > 0:
        print("\n🎉 配置测试通过！外部模型目录设置正确。")
        if model_files_count < 3:
            print("⚠️  部分模型文件需要手动下载，请参考安装指南。")
    else:
        print("\n⚠️  配置存在问题，请检查上述失败项目。")
    
    return all_passed

if __name__ == "__main__":
    main()