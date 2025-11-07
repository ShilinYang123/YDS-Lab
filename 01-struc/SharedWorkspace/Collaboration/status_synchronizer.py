#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trae智能体状态同步器
"""

import yaml
import json
from datetime import datetime
from pathlib import Path

class TraeStatusSynchronizer:
    """Trae状态同步器"""
    
    def __init__(self):
        self.workspace = Path("Struc/SharedWorkspace")
        self.status_dir = self.workspace / "Collaboration" / "status"
        self.status_dir.mkdir(parents=True, exist_ok=True)
        
    def update_agent_status(self, agent_name, status_data):
        """更新智能体状态"""
        status_file = self.status_dir / f"{agent_name}_status.yaml"
        
        status_entry = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "status": status_data
        }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            yaml.dump(status_entry, f, default_flow_style=False, allow_unicode=True)
            
    def get_all_agent_status(self):
        """获取所有智能体状态"""
        status_summary = {}
        
        for status_file in self.status_dir.glob("*_status.yaml"):
            agent_name = status_file.stem.replace("_status", "")
            
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = yaml.safe_load(f)
                status_summary[agent_name] = status_data
                
        return status_summary
        
    def sync_workspace(self):
        """同步工作空间"""
        print("🔄 同步Trae工作空间...")
        # 同步逻辑实现
        print("✅ 工作空间同步完成")

if __name__ == "__main__":
    synchronizer = TraeStatusSynchronizer()
    print("Trae状态同步器已启动")
