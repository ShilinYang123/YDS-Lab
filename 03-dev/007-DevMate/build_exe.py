import subprocess
import sys
import os

# 资源文件列表
resources = [
    ('config.json', '.'),
    ('continue_btn.png', '.'),
    ('README_使用说明.md', '.')
]

main_script = 'trae_mate.py'
exe_name = 'TraeMate.exe'

# 构建 --add-data 参数
add_data_args = []
for src, dst in resources:
    add_data_args.append(f'--add-data={src};{dst}')

# 清理旧文件


def clean():
    for d in ['dist', 'build']:
        if os.path.exists(d):
            import shutil
            shutil.rmtree(d)
    if os.path.exists(exe_name):
        os.remove(exe_name)


if __name__ == '__main__':
    clean()
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile', '--noconsole', '--clean', '-y',
        *add_data_args,
        main_script
    ]
    print('打包命令：', ' '.join(cmd))
    subprocess.run(cmd, check=True)
    # 移动exe到当前目录
    dist_exe = os.path.join('dist', 'trae_mate.exe')
    if os.path.exists(dist_exe):
        os.replace(dist_exe, exe_name)
    print(f'打包完成！只需带走 {exe_name} 即可独立运行！')
