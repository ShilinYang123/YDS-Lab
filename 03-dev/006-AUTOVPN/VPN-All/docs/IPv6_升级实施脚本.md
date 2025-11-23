# IPv6 升级实施脚本

## 1. 自动备份脚本

### 1.1 完整备份脚本
```python
# backup_system.py
#!/usr/bin/env python3
"""
AUTOVPN IPv6升级备份系统
在升级前自动创建完整备份
"""

import os
import shutil
import datetime
import json
import psutil
import subprocess
from pathlib import Path

class BackupManager:
    def __init__(self, base_path="s:/AUTOVPN"):
        self.base_path = Path(base_path)
        self.backup_base = self.base_path / "backups"
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.backup_base / f"pre_ipv6_upgrade_{self.timestamp}"
        
    def create_backup(self):
        """创建完整备份"""
        print(f"🔄 开始创建备份: {self.backup_dir}")
        
        # 创建备份目录
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. 备份代码文件
        self.backup_code()
        
        # 2. 备份配置文件
        self.backup_configs()
        
        # 3. 备份服务状态
        self.backup_service_status()
        
        # 4. 创建备份清单
        self.create_backup_manifest()
        
        print(f"✅ 备份完成: {self.backup_dir}")
        return str(self.backup_dir)
    
    def backup_code(self):
        """备份代码文件"""
        print("📁 备份代码文件...")
        
        code_dirs = ["Scripts", "config", "routes"]
        
        for code_dir in code_dirs:
            src_path = self.base_path / code_dir
            if src_path.exists():
                dst_path = self.backup_dir / "code" / code_dir
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                print(f"  ✅ {code_dir}")
    
    def backup_configs(self):
        """备份配置文件"""
        print("⚙️  备份配置文件...")
        
        config_files = [
            "Scripts/config.env",
            "config/wireguard/wg0.conf",
            "Scripts/recommended_domains.txt",
            "routes/常用境外IP.txt"
        ]
        
        config_backup_dir = self.backup_dir / "configs"
        config_backup_dir.mkdir(exist_ok=True)
        
        for config_file in config_files:
            src_path = self.base_path / config_file
            if src_path.exists():
                dst_path = config_backup_dir / Path(config_file).name
                if src_path.is_file():
                    shutil.copy2(src_path, dst_path)
                else:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                print(f"  ✅ {config_file}")
    
    def backup_service_status(self):
        """备份服务状态"""
        print("🔍 备份服务状态...")
        
        status = {
            'timestamp': datetime.datetime.now().isoformat(),
            'processes': {},
            'network_connections': [],
            'system_info': {}
        }
        
        # 备份进程状态
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if any(keyword in proc.info['name'].lower() for keyword in ['wstunnel', 'wireguard', 'python']):
                    status['processes'][proc.info['pid']] = {
                        'name': proc.info['name'],
                        'cmdline': proc.info['cmdline'],
                        'create_time': proc.info['create_time']
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 备份网络连接
        for conn in psutil.net_connections():
            if hasattr(conn, 'laddr') and conn.laddr:
                if conn.laddr.port in [1081, 1082, 8081, 443, 53]:
                    status['network_connections'].append({
                        'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'status': conn.status,
                        'pid': conn.pid
                    })
        
        # 系统信息
        status['system_info'] = {
            'boot_time': psutil.boot_time(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total
        }
        
        # 保存状态文件
        status_file = self.backup_dir / "service_status.json"
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, default=str)
        
        print(f"  ✅ 服务状态备份完成")
    
    def create_backup_manifest(self):
        """创建备份清单"""
        manifest = {
            'backup_timestamp': datetime.datetime.now().isoformat(),
            'backup_version': '1.0',
            'backup_contents': {
                'code_files': list((self.backup_dir / "code").rglob("*")),
                'config_files': list((self.backup_dir / "configs").rglob("*")),
                'service_status': 'service_status.json'
            },
            'restore_instructions': self.get_restore_instructions()
        }
        
        manifest_file = self.backup_dir / "backup_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, default=str)
    
    def get_restore_instructions(self):
        """生成恢复说明"""
        return """
恢复说明:
1. 停止所有AUTOVPN服务
2. 运行 restore_system.py 脚本
3. 选择备份目录: {backup_dir}
4. 验证服务状态
5. 测试连接
""".format(backup_dir=self.backup_dir)

if __name__ == "__main__":
    backup_manager = BackupManager()
    backup_path = backup_manager.create_backup()
    print(f"🎯 备份路径: {backup_path}")
```

## 2. 一键回滚脚本

### 2.1 快速回滚脚本
```batch
# rollback_ipv6_upgrade.bat
@echo off
echo ========================================
echo AUTOVPN IPv6升级回滚工具
echo ========================================

set "backup_dir="
set "autovpn_path=s:\YDS-Lab\03-dev\006-AUTOVPN\allout"

:: 查找最新的备份
echo 正在查找最新的备份...
for /f "delims=" %%i in ('dir /b /ad /o-d "%autovpn_path%\backups\pre_ipv6_upgrade_*" 2^>nul') do (
    set "backup_dir=%autovpn_path%\backups\%%i"
    goto :found_backup
)

echo ❌ 未找到备份目录！
echo 请手动指定备份目录路径。
set /p "backup_dir=请输入备份目录路径: "
if not exist "%backup_dir%" (
    echo ❌ 指定的备份目录不存在！
    pause
    exit /b 1
)

:found_backup
echo ✅ 找到备份目录: %backup_dir%
echo.
echo ⚠️  警告: 回滚将停止当前服务并恢复到备份状态！
echo.
set /p "confirm=是否继续回滚? (y/N): "
if /i not "%confirm%"=="y" (
    echo 回滚已取消。
    pause
    exit /b 0
)

echo.
echo ========================================
echo 开始回滚过程...
echo ========================================

:: 1. 停止所有相关服务
echo 🔴 停止服务...
taskkill /F /IM wstunnel.exe 2>nul
taskkill /F /IM WireGuard.exe 2>nul
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak > nul

:: 2. 备份当前状态（以防需要恢复）
echo 📁 备份当前状态...
set "current_backup=%autovpn_path%\backups\pre_rollback_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
mkdir "%current_backup%" 2>nul
xcopy "%autovpn_path%\Scripts" "%current_backup%\Scripts\" /E /I /Y > nul
xcopy "%autovpn_path%\config" "%current_backup%\config\" /E /I /Y > nul

:: 3. 恢复备份文件
echo 📤 恢复备份文件...
xcopy "%backup_dir%\code\Scripts" "%autovpn_path%\Scripts\" /E /I /Y > nul
xcopy "%backup_dir%\code\config" "%autovpn_path%\config\" /E /I /Y > nul

:: 4. 恢复配置文件
echo ⚙️  恢复配置文件...
if exist "%backup_dir%\configs\config.env" (
    copy /Y "%backup_dir%\configs\config.env" "%autovpn_path%\Scripts\" > nul
)

:: 5. 验证恢复
echo 🔍 验证恢复...
if exist "%autovpn_path%\Scripts\autovpn_menu.py" (
    echo ✅ 主程序文件恢复成功
) else (
    echo ❌ 主程序文件恢复失败！
    pause
    exit /b 1
)

:: 6. 重启服务
echo 🔄 重启服务...
cd /d "%autovpn_path%\Scripts"
start python autovpn_menu.py

echo.
echo ========================================
echo ✅ 回滚完成！
echo 📍 备份路径: %backup_dir%
echo ⚠️  请验证服务是否正常运行
echo ========================================
pause
```

### 2.2 Python回滚管理器
```python
# rollback_manager.py
#!/usr/bin/env python3
"""
AUTOVPN IPv6升级回滚管理器
提供交互式回滚界面
"""

import os
import shutil
import json
import datetime
from pathlib import Path

class RollbackManager:
    def __init__(self, base_path="s:/YDS-Lab/03-dev/006-AUTOVPN/allout"):
        self.base_path = Path(base_path)
        self.backup_base = self.base_path / "backups"
        
    def list_backups(self):
        """列出所有可用的备份"""
        backups = []
        
        if not self.backup_base.exists():
            return backups
        
        for backup_dir in self.backup_base.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith("pre_ipv6_upgrade_"):
                manifest_file = backup_dir / "backup_manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                        
                        backups.append({
                            'path': str(backup_dir),
                            'name': backup_dir.name,
                            'timestamp': manifest.get('backup_timestamp', 'Unknown'),
                            'size': self.get_dir_size(backup_dir)
                        })
                    except Exception as e:
                        print(f"⚠️  读取备份清单失败: {backup_dir.name} - {e}")
        
        # 按时间排序
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def get_dir_size(self, path):
        """获取目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
        return self.format_size(total_size)
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def interactive_rollback(self):
        """交互式回滚"""
        print("🔄 AUTOVPN IPv6升级回滚工具")
        print("=" * 50)
        
        # 列出备份
        backups = self.list_backups()
        
        if not backups:
            print("❌ 未找到任何备份！")
            return False
        
        print("📋 可用的备份:")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup['name']}")
            print(f"   时间: {backup['timestamp']}")
            print(f"   大小: {backup['size']}")
            print()
        
        # 选择备份
        while True:
            try:
                choice = input("请选择要恢复的备份 (输入数字或q退出): ").strip()
                if choice.lower() == 'q':
                    return False
                
                backup_index = int(choice) - 1
                if 0 <= backup_index < len(backups):
                    selected_backup = backups[backup_index]
                    break
                else:
                    print("❌ 无效的选择，请重试")
            except ValueError:
                print("❌ 请输入有效的数字")
        
        # 确认回滚
        print(f"\n⚠️  您选择恢复备份: {selected_backup['name']}")
        print("⚠️  警告: 回滚将停止当前服务并恢复到备份状态！")
        
        confirm = input("是否继续回滚? (yes/NO): ").strip().lower()
        if confirm != 'yes':
            print("回滚已取消")
            return False
        
        # 执行回滚
        return self.perform_rollback(selected_backup['path'])
    
    def perform_rollback(self, backup_path):
        """执行回滚"""
        print("\n🔄 开始回滚过程...")
        
        try:
            # 1. 停止服务
            print("🔴 停止服务...")
            self.stop_services()
            
            # 2. 创建当前状态备份
            print("📁 备份当前状态...")
            current_backup = self.backup_current_state()
            
            # 3. 恢复文件
            print("📤 恢复备份文件...")
            self.restore_files(backup_path)
            
            # 4. 验证恢复
            print("🔍 验证恢复...")
            if self.verify_restore():
                print("✅ 文件验证成功")
            else:
                print("❌ 文件验证失败，尝试恢复当前状态...")
                self.restore_files(current_backup)
                return False
            
            # 5. 重启服务
            print("🔄 重启服务...")
            self.restart_services()
            
            print("\n✅ 回滚完成！")
            print(f"📍 备份路径: {backup_path}")
            print("⚠️  请验证服务是否正常运行")
            return True
            
        except Exception as e:
            print(f"\n❌ 回滚失败: {e}")
            return False
    
    def stop_services(self):
        """停止服务"""
        try:
            # Windows系统
            os.system("taskkill /F /IM wstunnel.exe 2>nul")
            os.system("taskkill /F /IM WireGuard.exe 2>nul") 
            os.system("taskkill /F /IM python.exe 2>nul")
            import time
            time.sleep(3)
        except Exception as e:
            print(f"⚠️  停止服务时出错: {e}")
    
    def backup_current_state(self):
        """备份当前状态"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = self.backup_base / f"pre_rollback_{timestamp}"
        current_backup.mkdir(parents=True, exist_ok=True)
        
        # 备份当前文件
        for item in ['Scripts', 'config']:
            src_path = self.base_path / item
            dst_path = current_backup / item
            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
        
        return str(current_backup)
    
    def restore_files(self, backup_path):
        """恢复文件"""
        backup_path = Path(backup_path)
        
        # 恢复代码文件
        code_backup = backup_path / "code"
        if code_backup.exists():
            for item in ['Scripts', 'config']:
                src_path = code_backup / item
                dst_path = self.base_path / item
                if src_path.exists():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
        
        # 恢复配置文件
        config_backup = backup_path / "configs"
        if config_backup.exists():
            for config_file in config_backup.iterdir():
                if config_file.is_file():
                    dst_path = self.base_path / "Scripts" / config_file.name
                    shutil.copy2(config_file, dst_path)
    
    def verify_restore(self):
        """验证恢复"""
        required_files = [
            "Scripts/autovpn_menu.py",
            "Scripts/config.env"
        ]
        
        for file_path in required_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                print(f"❌ 缺少文件: {file_path}")
                return False
        
        return True
    
    def restart_services(self):
        """重启服务"""
        try:
            scripts_path = self.base_path / "Scripts"
            os.chdir(scripts_path)
            
            # 启动主程序
            os.startfile("autovpn_menu.py")
            
        except Exception as e:
            print(f"⚠️  重启服务时出错: {e}")
            print("请手动重启AUTOVPN服务")

if __name__ == "__main__":
    rollback_manager = RollbackManager()
    rollback_manager.interactive_rollback()
```

## 3. 升级实施脚本

### 3.1 阶段一实施脚本
```python
# stage1_implement.py
#!/usr/bin/env python3
"""
IPv6升级阶段一实施脚本
支持IPv6连接
"""

import os
import shutil
import json
from pathlib import Path

class Stage1Implementer:
    def __init__(self, base_path="s:/AUTOVPN"):
        self.base_path = Path(base_path)
        self.scripts_path = self.base_path / "Scripts"
        self.config_path = self.scripts_path / "config.env"
        
    def implement_stage1(self):
        """实施阶段一"""
        print("🚀 IPv6升级阶段一实施")
        print("=" * 40)
        
        try:
            # 1. 备份当前配置
            print("📁 备份当前配置...")
            self.backup_config()
            
            # 2. 修改配置文件
            print("⚙️  修改配置文件...")
            self.modify_config()
            
            # 3. 修改wstunnel_combined.py
            print("📝 修改wstunnel_combined.py...")
            self.modify_wstunnel_combined()
            
            # 4. 验证修改
            print("🔍 验证修改...")
            if self.verify_modifications():
                print("✅ 阶段一实施成功！")
                return True
            else:
                print("❌ 验证失败，回滚修改...")
                self.rollback_config()
                return False
                
        except Exception as e:
            print(f"❌ 实施失败: {e}")
            self.rollback_config()
            return False
    
    def backup_config(self):
        """备份配置文件"""
        if self.config_path.exists():
            backup_path = self.config_path.with_suffix('.env.backup_stage1')
            shutil.copy2(self.config_path, backup_path)
            print(f"  ✅ 配置已备份到: {backup_path}")
    
    def modify_config(self):
        """修改配置文件"""
        config_lines = []
        
        # 读取现有配置
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_lines = f.readlines()
        
        # 添加IPv6配置
        ipv6_config_added = False
        new_config_lines = []
        
        for line in config_lines:
            new_config_lines.append(line)
            if line.strip() == "# WebSocket隧道基本配置" and not ipv6_config_added:
                new_config_lines.extend([
                    "\n# IPv6配置 (阶段一)\n",
                    "SERVER_IP_V6=2001:db8::1\n",
                    "PREFER_IPV6=false\n",
                    "ENABLE_IPV6=true\n"
                ])
                ipv6_config_added = True
        
        # 如果配置文件不存在，创建新配置
        if not config_lines:
            new_config_lines = [
                "# AUTOVPN配置文件\n",
                "# WebSocket隧道基本配置\n",
                "SERVER_IP=192.210.206.52\n",
                "SERVER_PORT=443\n",
                "\n# IPv6配置 (阶段一)\n",
                "SERVER_IP_V6=2001:db8::1\n",
                "PREFER_IPV6=false\n",
                "ENABLE_IPV6=true\n"
            ]
        
        # 写入配置文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.writelines(new_config_lines)
        
        print("  ✅ 配置修改完成")
    
    def modify_wstunnel_combined(self):
        """修改wstunnel_combined.py"""
        wstunnel_path = self.scripts_path / "wstunnel_combined.py"
        
        if not wstunnel_path.exists():
            print("  ⚠️  wstunnel_combined.py 不存在，跳过修改")
            return
        
        # 读取文件内容
        with open(wstunnel_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加IPv6支持代码
        if "SERVER_IP_V6" not in content:
            # 找到配置读取部分
            old_code = """    server_ip = config.get('SERVER_IP', '192.210.206.52')
    server_port = int(config.get('SERVER_PORT', '443'))"""
            
            new_code = """    server_ip = config.get('SERVER_IP', '192.210.206.52')
    server_port = int(config.get('SERVER_PORT', '443'))
    
    # IPv6支持 (阶段一)
    server_ip_v6 = config.get('SERVER_IP_V6', '')
    prefer_ipv6 = config.get('PREFER_IPV6', 'false').lower() == 'true'
    enable_ipv6 = config.get('ENABLE_IPV6', 'false').lower() == 'true'"""
            
            content = content.replace(old_code, new_code)
        
        # 修改WebSocket URL构建
        if "ws://{server_ip}" in content:
            old_url_code = "ws_url = f\"ws://{server_ip}:{server_port}\""
            new_url_code = """# IPv6支持 (阶段一)
    if enable_ipv6 and server_ip_v6 and prefer_ipv6:
        ws_url = f\"ws://[{server_ip_v6}]:{server_port}\"
    else:
        ws_url = f\"ws://{server_ip}:{server_port}\"""
            
            content = content.replace(old_url_code, new_url_code)
        
        # 写入修改后的内容
        with open(wstunnel_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("  ✅ wstunnel_combined.py 修改完成")
    
    def verify_modifications(self):
        """验证修改"""
        # 检查配置文件
        if not self.config_path.exists():
            print("  ❌ 配置文件不存在")
            return False
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        required_configs = ['SERVER_IP_V6', 'PREFER_IPV6', 'ENABLE_IPV6']
        for config in required_configs:
            if config not in config_content:
                print(f"  ❌ 缺少配置项: {config}")
                return False
        
        # 检查代码文件
        wstunnel_path = self.scripts_path / "wstunnel_combined.py"
        if wstunnel_path.exists():
            with open(wstunnel_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            
            if "SERVER_IP_V6" not in code_content:
                print("  ❌ wstunnel_combined.py 未正确修改")
                return False
        
        print("  ✅ 所有修改验证通过")
        return True
    
    def rollback_config(self):
        """回滚配置"""
        backup_path = self.config_path.with_suffix('.env.backup_stage1')
        if backup_path.exists():
            shutil.copy2(backup_path, self.config_path)
            print("  ✅ 配置已回滚")

if __name__ == "__main__":
    implementer = Stage1Implementer()
    success = implementer.implement_stage1()
    
    if success:
        print("\n🎉 阶段一实施完成！")
        print("下一步: 测试IPv6连接功能")
    else:
        print("\n❌ 阶段一实施失败，已回滚到原始状态")
```

## 4. 使用说明

### 4.1 升级前准备
```bash
# 1. 创建完整备份
python backup_system.py

# 2. 验证当前服务状态
python -c "import psutil; print('服务运行正常' if any('wstunnel' in p.name().lower() for p in psutil.process_iter()) else '服务未运行')"
```

### 4.2 分阶段升级
```bash
# 阶段一: IPv6连接支持
python stage1_implement.py

# 验证阶段一
python -c "
import socket
try:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    print('✅ IPv6 socket支持正常')
    sock.close()
except Exception as e:
    print(f'❌ IPv6 socket错误: {e}')
"
```

### 4.3 回滚操作
```bash
# 快速回滚（批处理）
double-click rollback_ipv6_upgrade.bat

# 交互式回滚（Python）
python rollback_manager.py
```

### 4.4 验证升级
```python
# 验证脚本 verify_upgrade.py
#!/usr/bin/env python3
"""
IPv6升级验证脚本
"""

import socket
import configparser
from pathlib import Path

def verify_ipv6_upgrade():
    """验证IPv6升级"""
    print("🔍 IPv6升级验证")
    print("=" * 30)
    
    # 1. 验证IPv6 socket支持
    print("1. 验证IPv6 socket支持...")
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.close()
        print("   ✅ IPv6 socket支持正常")
    except Exception as e:
        print(f"   ❌ IPv6 socket错误: {e}")
        return False
    
    # 2. 验证配置文件
    print("2. 验证配置文件...")
    config_path = Path("s:/YDS-Lab/03-dev/006-AUTOVPN/allout/Scripts/config.env")
    if config_path.exists():
        config = configparser.ConfigParser()
        try:
            # 读取为INI格式（处理没有section的情况）
            with open(config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            if 'SERVER_IP_V6' in config_content:
                print("   ✅ 配置文件包含IPv6设置")
            else:
                print("   ❌ 配置文件缺少IPv6设置")
                return False
        except Exception as e:
            print(f"   ❌ 配置文件读取错误: {e}")
            return False
    else:
        print("   ❌ 配置文件不存在")
        return False
    
    # 3. 验证代码修改
    print("3. 验证代码修改...")
    wstunnel_path = Path("s:/YDS-Lab/03-dev/006-AUTOVPN/allout/Scripts/wstunnel_combined.py")
    if wstunnel_path.exists():
        with open(wstunnel_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'SERVER_IP_V6' in content:
            print("   ✅ 代码文件包含IPv6支持")
        else:
            print("   ❌ 代码文件缺少IPv6支持")
            return False
    else:
        print("   ⚠️  wstunnel_combined.py 不存在，跳过验证")
    
    print("\n✅ IPv6升级验证通过！")
    return True

if __name__ == "__main__":
    verify_ipv6_upgrade()
```

## 5. 注意事项

### 5.1 安全警告
- ⚠️ 升级前必须创建完整备份
- ⚠️ 每个阶段完成后都要验证功能
- ⚠️ 保留至少3个历史备份版本
- ⚠️ 生产环境升级需要维护窗口

### 5.2 性能监控
```python
# 监控脚本 monitor_performance.py
import psutil
import time

def monitor_resources():
    """监控资源使用情况"""
    print("资源使用监控:")
    print(f"CPU使用率: {psutil.cpu_percent()}%")
    print(f"内存使用: {psutil.virtual_memory().percent}%")
    print(f"网络连接数: {len(psutil.net_connections())}")
    
    # 检查特定进程
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        if 'wstunnel' in proc.info['name'].lower():
            print(f"wstunnel进程: PID={proc.info['pid']}, 内存={proc.info['memory_percent']:.2f}%")
```

### 5.3 故障排除
```bash
# 常见问题排查
# 1. IPv6连接失败
check_ipv6() {
    python -c "
import socket
try:
    socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    print('IPv6支持正常')
except:
    print('IPv6支持异常')
"
}

# 2. 服务状态检查
check_services() {
    tasklist | grep -E "(wstunnel|python)"
}

# 3. 网络连接检查
check_connections() {
    netstat -an | grep -E "(1081|1082|8081)"
}
```