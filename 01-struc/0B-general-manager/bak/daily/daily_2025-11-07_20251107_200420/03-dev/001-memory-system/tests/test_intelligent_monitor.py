#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能监控系统测试脚本
测试智能错误检测和主动提醒功能的实际效果
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path

# 适配生产脚本位置，确保导入正常
current_file = Path(__file__).resolve()
repo_root = current_file.parents[3]  # S:\YDS-Lab
scripts_dir = repo_root / '04-prod' / '001-memory-system' / 'scripts'
monitoring_dir = scripts_dir / 'monitoring'

for p in [scripts_dir, monitoring_dir]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    from intelligent_monitor import IntelligentMonitor
    from smart_error_detector import SmartErrorDetector
    # 主动提醒模块在生产中命名为 start_proactive_reminder.py
    from start_proactive_reminder import ProactiveReminder
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

class MonitorTester:
    """智能监控系统测试器"""
    
    def __init__(self):
        # 使用仓库内 tmp 目录作为测试工作区，避免硬编码盘符路径
        self.repo_root = Path(__file__).resolve().parents[3]
        self.test_dir = self.repo_root / "tmp" / "memory_tests"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.monitor = None
        self.test_results = []
        
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 创建测试文件夹
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建包含错误的测试文件
        test_files = {
            "syntax_error.py": '''
# 这个文件包含语法错误
def test_function()  # 缺少冒号
    print("Hello World")
    return True
''',
            "logic_error.py": '''
# 这个文件包含逻辑错误
def divide_numbers(a, b):
    # 没有检查除零错误
    result = a / b
    return result

def process_list(items):
    # 可能的索引越界错误
    first_item = items[0]  # 没有检查列表是否为空
    return first_item
''',
            "import_error.py": '''
# 这个文件包含导入错误
import non_existent_module
from another_missing_module import some_function

def main():
    some_function()
''',
            "good_code.py": '''
# 这个文件是正确的代码
def safe_divide(a, b):
    """安全的除法函数"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

def safe_get_first(items):
    """安全获取列表第一个元素"""
    if not items:
        return None
    return items[0]

if __name__ == "__main__":
    print("测试代码运行正常")
'''
        }
        
        for filename, content in test_files.items():
            test_file = self.test_dir / filename
            test_file.write_text(content, encoding='utf-8')
            
        print(f"✅ 测试环境设置完成，创建了 {len(test_files)} 个测试文件")
        
    def test_error_detection(self):
        """测试错误检测功能"""
        print("\n🔍 测试错误检测功能...")
        
        try:
            detector = SmartErrorDetector()
            detector.load_config()
            
            # 扫描测试目录
            issues = detector.scan_project_files(str(self.test_dir))
            
            print(f"📊 检测到 {len(issues)} 个潜在问题:")
            for issue in issues:
                print(f"   - {issue['type']}: {issue['message']} (文件: {issue['file']})")
                
            self.test_results.append({
                "test": "error_detection",
                "status": "success",
                "issues_found": len(issues),
                "details": issues
            })
            
            return len(issues) > 0
            
        except Exception as e:
            print(f"❌ 错误检测测试失败: {e}")
            self.test_results.append({
                "test": "error_detection",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    def test_proactive_reminders(self):
        """测试主动提醒功能"""
        print("\n💡 测试主动提醒功能...")
        
        try:
            reminder = ProactiveReminder()
            reminder.load_knowledge_base()
            
            # 模拟一些开发活动
            activities = [
                {"type": "file_edit", "file": "syntax_error.py", "action": "modify"},
                {"type": "error_occurred", "error": "SyntaxError", "file": "syntax_error.py"},
                {"type": "file_edit", "file": "logic_error.py", "action": "create"},
            ]
            
            reminders_generated = 0
            for activity in activities:
                reminder.record_activity(activity)
                
                # 分析当前情况并生成提醒
                context = reminder.analyze_current_context()
                if context.get("should_remind", False):
                    reminder_msg = reminder.generate_reminder("coding", context)
                    if reminder_msg:
                        print(f"   📝 提醒: {reminder_msg}")
                        reminders_generated += 1
                        
            self.test_results.append({
                "test": "proactive_reminders",
                "status": "success",
                "reminders_generated": reminders_generated
            })
            
            return reminders_generated > 0
            
        except Exception as e:
            print(f"❌ 主动提醒测试失败: {e}")
            self.test_results.append({
                "test": "proactive_reminders",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    def test_integrated_monitoring(self):
        """测试集成监控功能"""
        print("\n🎯 测试集成监控功能...")
        
        try:
            # 初始化智能监控器
            self.monitor = IntelligentMonitor()
            
            # 启动监控（短时间测试）
            print("   🚀 启动监控系统...")
            self.monitor.start_monitoring()
            
            # 等待一段时间让系统检测
            time.sleep(5)
            
            # 获取系统状态
            status = self.monitor.get_system_status()
            print(f"   📊 系统状态: {status}")
            
            # 停止监控
            self.monitor.stop_monitoring()
            
            self.test_results.append({
                "test": "integrated_monitoring",
                "status": "success",
                "system_status": status
            })
            
            return True
            
        except Exception as e:
            print(f"❌ 集成监控测试失败: {e}")
            self.test_results.append({
                "test": "integrated_monitoring",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    def test_memory_integration(self):
        """测试与长记忆系统的集成"""
        print("\n🧠 测试长记忆系统集成...")
        
        try:
            # 适配统一后的 LongMemory 存储路径：logs/longmemory/lm_records.json（仓库根）
            repo_root = Path(__file__).resolve().parents[3]
            memory_file = repo_root / "logs" / "longmemory" / "lm_records.json"
            
            if not memory_file.exists():
                print("   ⚠️ 长记忆文件不存在，跳过集成测试")
                return False
                
            # 读取记忆文件（LongMemory 标准结构：{"general": {}, "memories": []}）
            with open(memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)

            # 查找智能监控相关记录：从 general 中筛选 type 包含 monitor 或 error 的条目
            general = memory_data.get('general', {})
            monitor_entries = [
                v for v in general.values()
                if isinstance(v, dict) and any(s in str(v.get('type', '')).lower() for s in ['monitor', 'error'])
            ]
            
            print(f"   📝 找到 {len(monitor_entries)} 条监控相关记录")
            
            self.test_results.append({
                "test": "memory_integration",
                "status": "success",
                "monitor_entries": len(monitor_entries),
                "memory_path": str(memory_file)
            })
            
            return len(monitor_entries) > 0
            
        except Exception as e:
            print(f"❌ 长记忆集成测试失败: {e}")
            self.test_results.append({
                "test": "memory_integration",
                "status": "failed",
                "error": str(e)
            })
            return False
            
    def generate_test_report(self):
        """生成测试报告"""
        print("\n📋 生成测试报告...")
        
        report = {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed_tests": len([r for r in self.test_results if r["status"] == "success"]),
                "failed_tests": len([r for r in self.test_results if r["status"] == "failed"])
            },
            "test_results": self.test_results,
            "conclusions": []
        }
        
        # 添加结论
        if report["test_summary"]["passed_tests"] == report["test_summary"]["total_tests"]:
            report["conclusions"].append("✅ 所有测试通过，智能监控系统运行正常")
        else:
            report["conclusions"].append("⚠️ 部分测试失败，需要进一步调试")
            
        # 保存报告
        report_file = Path("s:/3AI/logs/intelligent_monitor_test_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"📄 测试报告已保存到: {report_file}")
        return report
        
    def cleanup(self):
        """清理测试环境"""
        print("\n🧹 清理测试环境...")
        
        try:
            # 停止监控器
            if self.monitor:
                self.monitor.stop_monitoring()
                
            # 清理测试文件（可选）
            # import shutil
            # shutil.rmtree(self.test_dir, ignore_errors=True)
            
            print("✅ 清理完成")
            
        except Exception as e:
            print(f"⚠️ 清理过程中出现错误: {e}")
            
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始智能监控系统测试")
        print("=" * 50)
        
        try:
            # 设置测试环境
            self.setup_test_environment()
            
            # 运行各项测试
            tests = [
                self.test_error_detection,
                self.test_proactive_reminders,
                self.test_integrated_monitoring,
                self.test_memory_integration
            ]
            
            for test in tests:
                try:
                    test()
                except Exception as e:
                    print(f"❌ 测试执行失败: {e}")
                    
            # 生成报告
            report = self.generate_test_report()
            
            # 显示总结
            print("\n" + "=" * 50)
            print("📊 测试总结:")
            print(f"   总测试数: {report['test_summary']['total_tests']}")
            print(f"   通过测试: {report['test_summary']['passed_tests']}")
            print(f"   失败测试: {report['test_summary']['failed_tests']}")
            
            for conclusion in report["conclusions"]:
                print(f"   {conclusion}")
                
        finally:
            self.cleanup()

def main():
    """主函数"""
    tester = MonitorTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()