"""
TraeMate 构建脚本
用于使用 PyInstaller 打包应用程序
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)


def create_spec_file():
    """创建 PyInstaller 规格文件"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TraeMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico' if os.path.exists('resources/icon.ico') else None,
)
"""
    
    with open('TraeMate.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("创建 PyInstaller 规格文件: TraeMate.spec")


def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 使用 PyInstaller 构建
    cmd = ['pyinstaller', '--clean', 'TraeMate.spec']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("构建成功!")
        print(f"可执行文件位于: {os.path.abspath('dist/TraeMate.exe')}")
        return True
    else:
        print("构建失败!")
        print("错误信息:")
        print(result.stderr)
        return False


def create_installer():
    """创建安装程序（可选）"""
    # 这里可以添加创建安装程序的代码
    # 例如使用 NSIS 或 Inno Setup
    print("创建安装程序功能尚未实现")
    pass


def main():
    """主函数"""
    print("TraeMate 构建脚本")
    print("=" * 40)
    
    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("错误: PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False
    
    # 清理构建目录
    clean_build_dirs()
    
    # 创建规格文件
    create_spec_file()
    
    # 构建可执行文件
    success = build_executable()
    
    if success:
        # 创建安装程序（可选）
        # create_installer()
        print("\n构建完成!")
    else:
        print("\n构建失败!")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)