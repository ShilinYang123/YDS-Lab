"""
外部模型目录设置脚本
用于配置S:\LLm目录并创建必要的符号链接
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def create_llm_directory_structure():
    """创建S:\LLm目录结构"""
    llm_root = Path("S:/LLm")
    
    # 创建目录结构
    directories = [
        llm_root / "shimmy",
        llm_root / "models" / "shimmy", 
        llm_root / "models" / "lama",
        llm_root / "cache"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")
    
    return llm_root

def create_shimmy_config(llm_root):
    """创建Shimmy配置文件"""
    config_path = llm_root / "shimmy" / "config.yaml"
    
    config_content = """# Shimmy配置文件
server:
  host: "127.0.0.1"
  port: 8080
  
models:
  default_model: "shimmy_model.onnx"
  model_path: "../models/shimmy"
  
inference:
  batch_size: 1
  max_length: 512
  device: "cpu"  # 贵阳机使用CPU推理
  
logging:
  level: "INFO"
  file: "shimmy.log"
"""
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ 创建Shimmy配置: {config_path}")

def create_lama_config(llm_root):
    """创建LaMa配置文件"""
    config_path = llm_root / "models" / "lama" / "lama_config.yaml"
    
    config_content = """# LaMa模型配置
model:
  name: "LaMa-256px"
  file: "lama_256.pth"
  input_size: [256, 256]
  
inference:
  device: "cuda"  # 江门机使用GPU推理
  batch_size: 1
  
preprocessing:
  normalize: true
  resize_method: "bilinear"
"""
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ 创建LaMa配置: {config_path}")

def setup_environment_variables():
    """设置环境变量（用户级别）"""
    env_vars = {
        "LLM_ROOT": "S:\\LLm",
        "SHIMMY_HOME": "S:\\LLm\\shimmy", 
        "MODELS_PATH": "S:\\LLm\\models"
    }
    
    for var_name, var_value in env_vars.items():
        try:
            # 使用setx命令设置用户环境变量
            subprocess.run([
                "setx", var_name, var_value
            ], check=True, capture_output=True)
            print(f"✅ 设置环境变量: {var_name}={var_value}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 设置环境变量失败: {var_name} - {e}")

def create_symbolic_links():
    """创建符号链接（需要管理员权限）"""
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "projects" / "001-dewatermark-ai" / "assets" / "models"
    
    # 确保项目模型目录存在
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # 符号链接映射
    links = {
        "shimmy": "S:/LLm/models/shimmy",
        "lama": "S:/LLm/models/lama"
    }
    
    for link_name, target_path in links.items():
        link_path = models_dir / link_name
        
        # 如果链接已存在，跳过
        if link_path.exists():
            print(f"⚠️  符号链接已存在: {link_path}")
            continue
        
        try:
            # 创建目录符号链接
            subprocess.run([
                "mklink", "/D", str(link_path), target_path
            ], shell=True, check=True, capture_output=True)
            print(f"✅ 创建符号链接: {link_path} -> {target_path}")
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建符号链接失败 (可能需要管理员权限): {link_name}")
            print(f"   手动命令: mklink /D \"{link_path}\" \"{target_path}\"")

def create_installation_guide():
    """创建安装指南"""
    guide_path = Path("S:/LLm/INSTALLATION_GUIDE.md")
    
    guide_content = """# S:\\LLm 外部模型目录安装指南

## 📁 目录结构
```
S:\\LLm\\
├── shimmy\\                    # Shimmy可执行文件
│   ├── shimmy.exe             # 需要手动下载
│   └── config.yaml            # ✅ 已创建
├── models\\                   # 统一模型库
│   ├── shimmy\\              # Shimmy模型文件
│   │   └── shimmy_model.onnx  # 需要手动下载
│   └── lama\\                # LaMa模型文件
│       ├── lama_256.pth       # 需要手动下载
│       └── lama_config.yaml   # ✅ 已创建
└── cache\\                    # 模型缓存
```

## 🚀 安装步骤

### 1. 下载Shimmy
```bash
# 从官方仓库下载Shimmy可执行文件
# 放置到: S:\\LLm\\shimmy\\shimmy.exe
```

### 2. 下载模型文件
```bash
# LaMa模型 (约200MB)
# 下载到: S:\\LLm\\models\\lama\\lama_256.pth

# Shimmy模型 (约500MB) 
# 下载到: S:\\LLm\\models\\shimmy\\shimmy_model.onnx
```

### 3. 创建符号链接 (管理员权限)
```cmd
# 以管理员身份运行命令提示符
cd /d S:\\YDS-Lab
python scripts\\setup_external_models.py --create-links
```

### 4. 验证配置
```bash
# 运行测试脚本
python scripts\\test_external_models.py
```

## 🔧 环境变量 (已自动设置)
- `LLM_ROOT=S:\\LLm`
- `SHIMMY_HOME=S:\\LLm\\shimmy`
- `MODELS_PATH=S:\\LLm\\models`

## 📝 注意事项
1. 符号链接需要管理员权限
2. 环境变量重启后生效
3. 模型文件需要手动下载
4. 配置文件已自动生成
"""
    
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✅ 创建安装指南: {guide_path}")

def main():
    """主函数"""
    print("🚀 开始设置外部模型目录...")
    
    # 创建目录结构
    llm_root = create_llm_directory_structure()
    
    # 创建配置文件
    create_shimmy_config(llm_root)
    create_lama_config(llm_root)
    
    # 设置环境变量
    setup_environment_variables()
    
    # 创建安装指南
    create_installation_guide()
    
    # 检查是否需要创建符号链接
    if "--create-links" in sys.argv:
        print("\n🔗 创建符号链接...")
        create_symbolic_links()
    else:
        print("\n⚠️  跳过符号链接创建 (需要管理员权限)")
        print("   如需创建符号链接，请以管理员身份运行:")
        print("   python scripts\\setup_external_models.py --create-links")
    
    print("\n✅ 外部模型目录设置完成!")
    print("📖 详细说明请查看: S:\\LLm\\INSTALLATION_GUIDE.md")

if __name__ == "__main__":
    main()