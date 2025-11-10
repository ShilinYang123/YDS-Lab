#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab MCP服务器管理器
功能：管理和监控Office、CAD、Graphics等MCP服务器集群
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class MCPServerManager:
    """MCP服务器集群管理器
    
    功能包括：
    - MCP服务器状态监控
    - 服务器启动和停止管理
    - 服务器配置验证
    - 服务器性能监控
    """
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            # 适配YDS-Lab项目结构
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 新路径优先：tools/mcp/servers；兼容旧路径：01-struc/MCPCluster
        new_mcp_root = self.project_root / "tools" / "mcp" / "servers"
        old_mcp_root = self.project_root / "01-struc" / "MCPCluster"
        self.mcp_dir = new_mcp_root if new_mcp_root.exists() else old_mcp_root

        # 统一日志目录至公司级 logs（修订）：01-struc/logs
        self.logs_dir = self.project_root / "01-struc" / "logs"
        
        # MCP服务器配置 - 使用实际文件路径
        # 服务器清单：以当前 MCPCluster 版本为准
        self.mcp_servers = {
            "office": {
                "excel": {
                    "name": "Excel MCP Server",
                    "path": self.mcp_dir / "Excel" / "excel_mcp_server.py",
                    "port": 8001,
                    "status": "stopped"
                }
            },
            "platform": {
                "github": {
                    "name": "GitHub MCP Server",
                    "path": self.mcp_dir / "GitHub" / "github_mcp_server.py",
                    "port": 8002,
                    "status": "stopped"
                },
                "filesystem": {
                    "name": "FileSystem MCP Server",
                    "path": self.mcp_dir / "FileSystem" / "filesystem_mcp_server.py",
                    "port": 8003,
                    "status": "stopped"
                },
                "figma": {
                    "name": "Figma MCP Server",
                    "path": self.mcp_dir / "Figma" / "figma_mcp_server.py",
                    "port": 8004,
                    "status": "stopped"
                },
                "database": {
                    "name": "Database MCP Server",
                    "path": self.mcp_dir / "Database" / "database_mcp_server.py",
                    "port": 8005,
                    "status": "stopped"
                },
                "builder": {
                    "name": "Builder MCP Server",
                    "path": self.mcp_dir / "Builder" / "builder_mcp_server.py",
                    "port": 8006,
                    "status": "stopped"
                }
            }
        }
        
        # 设置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志系统"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.logs_dir / "mcp_server_manager.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def check_server_status(self, category: str, server: str) -> bool:
        """检查指定MCP服务器状态"""
        try:
            server_config = self.mcp_servers[category][server]
            server_path = server_config["path"]
            
            if not server_path.exists():
                self.logger.warning(f"MCP服务器文件不存在: {server_path}")
                return False
                
            # 这里可以添加更复杂的状态检查逻辑
            # 比如检查端口是否被占用、进程是否运行等
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查服务器状态失败 {category}/{server}: {e}")
            return False
            
    def check_all_servers(self) -> Dict[str, Dict[str, bool]]:
        """检查所有MCP服务器状态"""
        status_report = {}
        
        for category, servers in self.mcp_servers.items():
            status_report[category] = {}
            for server_name in servers.keys():
                status_report[category][server_name] = self.check_server_status(category, server_name)
                
        return status_report
        
    def generate_status_report(self) -> str:
        """生成MCP服务器状态报告"""
        status = self.check_all_servers()
        
        report = ["\n=== YDS-Lab MCP服务器状态报告 ==="]
        report.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"MCP根目录: {self.mcp_dir}")
        report.append("")
        
        for category, servers in status.items():
            report.append(f"【{category.upper()}类MCP服务器】")
            for server_name, is_ok in servers.items():
                status_icon = "[OK]" if is_ok else "[FAIL]"
                server_info = self.mcp_servers[category][server_name]
                report.append(f"  {status_icon} {server_info['name']} (端口: {server_info['port']})")
                if not is_ok:
                    report.append(f"      路径: {server_info['path']}")
            report.append("")
            
        return "\n".join(report)
        
    def create_mcp_directories(self):
        """创建MCP服务器目录结构"""
        directories = [
            self.mcp_dir / "office",
            self.mcp_dir / "design", 
            self.mcp_dir / "cad",
            self.mcp_dir / "graphics"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建MCP目录: {directory}")
            
    def save_server_config(self):
        """保存MCP服务器配置到文件"""
        config_file = self.mcp_dir / "mcp_servers_config.json"
        
        try:
            # 确保MCP目录存在
            self.mcp_dir.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.mcp_servers, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"MCP服务器配置已保存: {config_file}")
        except Exception as e:
            self.logger.error(f"保存MCP服务器配置失败: {e}")
            
    def load_server_config(self):
        """从文件加载MCP服务器配置"""
        config_file = self.mcp_dir / "mcp_servers_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 更新路径对象
                    for category in loaded_config:
                        for server in loaded_config[category]:
                            if 'path' in loaded_config[category][server]:
                                loaded_config[category][server]['path'] = Path(loaded_config[category][server]['path'])
                    self.mcp_servers.update(loaded_config)
                self.logger.info(f"MCP服务器配置已加载: {config_file}")
            except Exception as e:
                self.logger.error(f"加载MCP服务器配置失败: {e}")
                
    def initialize_mcp_system(self):
        """初始化MCP服务器系统"""
        self.logger.info("开始初始化YDS-Lab MCP服务器集群...")
        
        # 创建目录结构
        self.create_mcp_directories()
        
        # 保存配置
        self.save_server_config()
        
        # 生成状态报告
        report = self.generate_status_report()
        print(report)
        
        # 保存状态报告
        report_file = self.logs_dir / f"mcp_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            self.logger.info(f"状态报告已保存: {report_file}")
        except Exception as e:
            self.logger.error(f"保存状态报告失败: {e}")
            
        self.logger.info("MCP服务器系统初始化完成")
        
def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab MCP服务器管理器')
    parser.add_argument('command', nargs='?', default='init', 
                       choices=['init', 'status'], 
                       help='执行的命令: init(初始化) 或 status(状态检查)')
    
    args = parser.parse_args()
    manager = MCPServerManager()
    
    if args.command == 'status':
        # 生成状态报告并输出
        report = manager.generate_status_report()
        print(report, flush=True)
    else:
        # 默认初始化
        manager.initialize_mcp_system()
    
if __name__ == "__main__":
    main()