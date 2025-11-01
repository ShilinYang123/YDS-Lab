import os
import shutil
import sys

def create_project(name, template="tauri-python-ai"):
    base_dir = f"S:/YDS-Lab/projects/{name}"
    if os.path.exists(base_dir):
        print(f"❌ 项目 {name} 已存在，请更换名称")
        return
    
    os.makedirs(base_dir, exist_ok=True)
    print(f"📁 创建项目目录: {base_dir}")
    
    # 创建子目录
    subdirs = ["docs", "src", "scripts", "models", "assets", "output", "debug", "backups"]
    for d in subdirs:
        os.makedirs(os.path.join(base_dir, d), exist_ok=True)
    
    # 创建 servers 配置
    servers = ["local-pc", "guiyang-server"]
    for server in servers:
        os.makedirs(os.path.join(base_dir, "servers", server), exist_ok=True)
    
    # 创建默认文档
    spec_path = os.path.join(base_dir, "docs", "SPEC.md")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(f"# {name} 产品需求文档\n\n> 请在此填写项目说明\n")
    
    print(f"✅ 项目 {name} 创建成功！路径: {base_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 3 or not sys.argv[1].startswith("--name="):
        print("用法: python create_project.py --name=项目名")
        sys.exit(1)
    
    name = sys.argv[1].split("=")[1]
    create_project(name)