#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab迁移状态跟踪器
功能：帮助在"突然忘记"时快速恢复工作状态和上下文
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

class MigrationStatusTracker:
    """迁移状态跟踪和恢复系统"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        # 统一状态文件路径至 04-prod/reports
        reports_dir = self.project_root / "04-prod" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = reports_dir / "migration_status.json"
# 日志目录统一到 01-struc/0B-general-manager/logs
        self.log_dir = self.project_root / "logs"  # 按照三级存储规范：系统维护类日志存储在logs/
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def save_current_status(self, phase: str, task: str, details: dict = None):
        """保存当前工作状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "current_phase": phase,
            "current_task": task,
            "details": details or {},
            "project_structure_verified": self._verify_project_structure(),
            "backup_status": self._check_backup_status(),
            "trae_env_status": self._check_trae_environment()
        }
        
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
            
        # 同时写入日志
        self._write_log(f"状态保存: {phase} - {task}")
        
    def recover_status(self):
        """恢复工作状态 - 在"忘记"时使用"""
        if not self.status_file.exists():
            return self._create_initial_status()
            
        with open(self.status_file, 'r', encoding='utf-8') as f:
            status = json.load(f)
            
        print("🔄 正在恢复工作状态...")
        print(f"📅 最后更新时间: {status['timestamp']}")
        print(f"🎯 当前阶段: {status['current_phase']}")
        print(f"📋 当前任务: {status['current_task']}")
        
        if status['details']:
            print("📝 任务详情:")
            for key, value in status['details'].items():
                print(f"   - {key}: {value}")
                
        print("\n🔍 系统状态检查:")
        print(f"   - 项目结构: {'✅' if status['project_structure_verified'] else '❌'}")
        print(f"   - 备份状态: {'✅' if status['backup_status'] else '❌'}")
        print(f"   - Trae环境: {'✅' if status['trae_env_status'] else '❌'}")
        
        return status
        
    def get_next_steps(self):
        """获取下一步建议"""
        status = self.recover_status()
        
        # 基于当前状态提供下一步建议
        next_steps = {
            "第一阶段：基础架构搭建": [
                "检查V1.0系统备份完整性",
                "创建Trae适配目录结构", 
                "配置MCP服务器基础设施",
                "搭建总经理智能体"
            ],
            "第二阶段：智能体团队构建": [
                "迁移企划总监智能体配置",
                "迁移财务总监智能体配置", 
                "构建开发团队智能体群",
                "建立智能体协作机制"
            ],
            "第三阶段：工具生态集成": [
                "开发GitHub MCP服务器",
                "开发Excel MCP服务器",
                "集成Figma设计工具",
                "建立MCP工具健康检查"
            ]
        }
        
        current_phase = status.get('current_phase', '第一阶段：基础架构搭建')
        steps = next_steps.get(current_phase, [])
        
        print(f"\n📋 {current_phase} 的下一步建议:")
        for i, step in enumerate(steps, 1):
            print(f"   {i}. {step}")
            
        return steps
        
    def _verify_project_structure(self):
        """验证项目结构完整性"""
        required_dirs = [
            "01-struc",
            "tools", 
            "projects",
            "models"
        ]
        
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                return False
        return True
        
    def _check_backup_status(self):
        """检查备份状态"""
        backup_dir = self.project_root / "Struc_V1_Backup"
        return backup_dir.exists() and any(backup_dir.iterdir())
        
    def _check_trae_environment(self):
        """检查Trae环境状态"""
        trae_dirs = [
            "01-struc/Agents",
            "01-struc/SharedWorkspace"
        ]
        
        for dir_path in trae_dirs:
            if not (self.project_root / dir_path).exists():
                return False
        return True
        
    def _create_initial_status(self):
        """创建初始状态"""
        initial_status = {
            "timestamp": datetime.now().isoformat(),
            "current_phase": "第一阶段：基础架构搭建",
            "current_task": "备份V1.0系统完整数据和配置",
            "details": {
                "migration_plan": "YDS-Lab目录结构迁移计划（V1.0到V2.0-Trae适配版）",
                "total_phases": 5,
                "estimated_weeks": 16
            },
            "project_structure_verified": self._verify_project_structure(),
            "backup_status": self._check_backup_status(),
            "trae_env_status": self._check_trae_environment()
        }
        
        self.save_current_status(
            initial_status["current_phase"],
            initial_status["current_task"], 
            initial_status["details"]
        )
        
        return initial_status
        
    def _write_log(self, message: str):
        """写入工作日志"""
        log_file = self.log_dir / f"migration_log_{datetime.now().strftime('%Y%m%d')}.txt"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")

def main():
    """主函数 - 快速状态恢复"""
    tracker = MigrationStatusTracker()
    
    print("🚀 YDS-Lab迁移状态恢复系统")
    print("=" * 50)
    
    # 恢复状态
    status = tracker.recover_status()
    
    # 获取下一步建议
    tracker.get_next_steps()
    
    print("\n💡 使用建议:")
    print("   - 每完成一个重要任务后，调用 save_current_status() 保存状态")
    print("   - 在'忘记'当前状态时，运行此脚本快速恢复")
    print("   - 查看 migration_log_*.txt 了解详细工作记录")

if __name__ == "__main__":
    main()