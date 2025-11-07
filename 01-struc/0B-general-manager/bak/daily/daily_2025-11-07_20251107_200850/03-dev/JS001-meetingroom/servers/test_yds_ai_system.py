#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS AI 公司建设与项目实施系统 - 端到端测试脚本
版本: V3.0-Trae适配版

测试覆盖:
1. MCP统一消息模型
2. 智能体角色体系
3. 会议分级管理
4. 智能议程生成
5. 文档共享治理
6. RBAC权限系统
7. 语音服务集成
8. 系统集成测试
"""

import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, List

# 添加服务器模块路径
# 仓库根目录定位修正：本文件位于 03-dev/JS001-meetingroom/servers 下，因此为 parents[3]
REPO_ROOT = Path(__file__).resolve().parents[3]
# 使用新的开发目录路径，避免依赖旧的 tools/servers
sys.path.insert(0, str(REPO_ROOT / "03-dev" / "JS001-meetingroom" / "servers"))

from mcp_message_model import MCPMessageBuilder, MCPMessageValidator, ChannelType, EventType
from agent_roles import AgentRoleManager, AgentRole
from meeting_levels import MeetingLevelManager, MeetingLevel
from intelligent_agenda import IntelligentAgendaGenerator
from document_governance import DocumentGovernanceManager
from rbac_system import RBACSystem
from voice_service import VoiceServiceManager

class YDSAISystemTester:
    """YDS AI系统测试器"""
    
    def __init__(self, server_url: str = "http://localhost:8021"):
        self.server_url = server_url
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
    
    def test_mcp_message_model(self):
        """测试MCP统一消息模型"""
        print("\n=== 测试MCP统一消息模型 ===")
        
        try:
            # 测试消息构建
            from agent_roles import AgentRole
            from mcp_message_model import AgentInfo
            
            builder = MCPMessageBuilder()
            sender = AgentInfo(
                id="test_user",
                role=AgentRole.CEO,
                display_name="测试用户"
            )
            message = builder.create_text_message(
                room_id="test_room",
                sender=sender,
                content="测试消息"
            )
            
            # 测试消息验证
            validator = MCPMessageValidator()
            is_valid, errors = validator.validate_message(message.to_dict())
            
            self.log_test("MCP消息构建与验证", is_valid and len(errors) == 0, 
                         f"消息ID: {message.id}")
            
        except Exception as e:
            self.log_test("MCP消息模型", False, str(e))
    
    def test_agent_roles(self):
        """测试智能体角色体系"""
        print("\n=== 测试智能体角色体系 ===")
        
        try:
            manager = AgentRoleManager()
            
            # 测试获取所有角色
            roles = manager.get_all_roles()
            self.log_test("获取智能体角色", len(roles) > 0, f"发现{len(roles)}个角色")
            
            # 测试角色权限检查
            has_permission = manager.check_permission(AgentRole.CEO, "host_meeting")
            self.log_test("角色权限检查", has_permission, "CEO具有会议主持权限")
            
            # 测试智能体分配
            success = manager.assign_agent_to_meeting("test_meeting", AgentRole.CEO, "user1")
            self.log_test("智能体分配", success, "成功分配CEO到测试会议")
            
        except Exception as e:
            self.log_test("智能体角色体系", False, str(e))
    
    def test_meeting_levels(self):
        """测试会议分级管理"""
        print("\n=== 测试会议分级管理 ===")
        
        try:
            manager = MeetingLevelManager()
            
            # 测试创建会议
            meeting = manager.create_meeting(
                level=MeetingLevel.A_LEVEL,
                title="测试A级会议",
                description="测试会议描述",
                host_agent="CEO",
                participants=["CEO", "CFO", "CTO"],  # A级会议需要至少3个参与者
                organizer="CEO"
            )
            
            self.log_test("创建分级会议", meeting is not None, 
                         f"会议ID: {meeting.get('id', 'N/A')}")
            
            # 测试会议状态管理
            if meeting:
                meeting_id = meeting.get('id')
                started = manager.start_meeting(meeting_id)
                self.log_test("开始会议", started, f"会议{meeting_id}已开始")
            
        except Exception as e:
            self.log_test("会议分级管理", False, str(e))
    
    def test_intelligent_agenda(self):
        """测试智能议程生成"""
        print("\n=== 测试智能议程生成 ===")
        
        try:
            generator = IntelligentAgendaGenerator()
            
            # 测试议程生成
            agenda = generator.generate_agenda(
                meeting_level=MeetingLevel.A_LEVEL,
                meeting_title="战略规划会议",
                meeting_description="Q4战略规划讨论",
                participants=["CEO", "CFO", "CTO"],
                duration_minutes=120,
                meeting_type="strategic_planning",
                custom_topics=["Q4财务规划", "技术架构升级", "市场拓展策略"]
            )
            
            self.log_test("智能议程生成", len(agenda) > 0, 
                         f"生成{len(agenda)}个议程项")
            
            # 测试议程优化
            optimized = generator.optimize_agenda_order(agenda)
            self.log_test("议程优化", len(optimized) == len(agenda), 
                         "议程顺序优化完成")
            
        except Exception as e:
            self.log_test("智能议程生成", False, str(e))
    
    def test_document_governance(self):
        """测试文档共享治理"""
        print("\n=== 测试文档共享治理 ===")
        
        try:
            governance = DocumentGovernanceManager()
            
            # 测试访问权限检查
            allowed = governance.check_access(
                user_role="CEO",
    path="S:/YDS-Lab/01-struc/docs/YDS-AI-战略规划",
                action="read",
                user_id="CEO"
            )
            
            self.log_test("文档访问权限检查", allowed, "CEO可访问战略规划文档")
            
            # 测试审计日志
            from document_governance import AuditAction
            governance.log_access(
                user_id="CEO",
                user_role="CEO", 
                path="test_path",
                action=AuditAction.ACCESS,
                success=True
            )
            audit_logs = governance.get_audit_logs(limit=1)
            
            self.log_test("审计日志记录", len(audit_logs) > 0, "审计日志记录成功")
            
        except Exception as e:
            self.log_test("文档共享治理", False, str(e))
    
    def test_rbac_system(self):
        """测试RBAC权限系统"""
        print("\n=== 测试RBAC权限系统 ===")
        
        try:
            rbac = RBACSystem()
            
            # 测试用户认证
            token = rbac.authenticate_user("admin", "admin123")
            self.log_test("用户认证", token is not None, "管理员认证成功")
            
            # 测试权限检查
            if token:
                from rbac_system import Permission
                # 从JWT令牌中获取用户信息
                payload = rbac.verify_jwt_token(token)
                if payload:
                    user_id = payload.get('user_id')
                    has_permission = rbac.has_permission(user_id, Permission.CREATE_MEETING)
                    self.log_test("权限检查", has_permission, "管理员具有会议创建权限")
                else:
                    self.log_test("权限检查", False, "无法验证令牌")
            
            # 测试JWT令牌验证
            if token:
                payload = rbac.verify_jwt_token(token)
                self.log_test("JWT令牌验证", payload is not None, "令牌验证成功")
            
        except Exception as e:
            self.log_test("RBAC权限系统", False, str(e))
    
    def test_voice_service(self):
        """测试语音服务"""
        print("\n=== 测试语音服务 ===")
        
        try:
            voice_service = VoiceServiceManager()
            
            # 测试服务状态
            status = voice_service.get_service_status()
            self.log_test("语音服务状态", isinstance(status, dict), 
                         f"服务状态: {status}")
            
            # 测试STT配置
            stt_config = voice_service.get_stt_config("shimmy")
            self.log_test("STT配置获取", stt_config is not None, 
                         "Shimmy STT配置获取成功")
            
            # 测试TTS配置
            tts_config = voice_service.get_tts_config("shimmy")
            self.log_test("TTS配置获取", tts_config is not None, 
                         "Shimmy TTS配置获取成功")
            
        except Exception as e:
            self.log_test("语音服务", False, str(e))
    
    def test_api_endpoints(self):
        """测试API端点"""
        print("\n=== 测试API端点 ===")
        
        # 测试系统状态
        try:
            response = requests.get(f"{self.server_url}/yds/system/status", timeout=5)
            self.log_test("系统状态API", response.status_code == 200, 
                         f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("系统状态API", False, str(e))
        
        # 测试智能体角色API
        try:
            response = requests.get(f"{self.server_url}/yds/agents/roles", timeout=5)
            self.log_test("智能体角色API", response.status_code == 200, 
                         f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("智能体角色API", False, str(e))
        
        # 测试健康检查
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            self.log_test("健康检查API", response.status_code == 200, 
                         f"状态码: {response.status_code}")
        except Exception as e:
            self.log_test("健康检查API", False, str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始YDS AI系统端到端测试")
        print("=" * 50)
        
        # 组件测试
        self.test_mcp_message_model()
        self.test_agent_roles()
        self.test_meeting_levels()
        self.test_intelligent_agenda()
        self.test_document_governance()
        self.test_rbac_system()
        self.test_voice_service()
        
        # API测试
        self.test_api_endpoints()
        
        # 生成测试报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 50)
        print("📊 测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # 保存详细报告至统一目录 04-prod/reports
        report_dir = REPO_ROOT / "04-prod" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "servers_test_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "details": self.test_results,
                "timestamp": time.time()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细报告已保存到: {report_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YDS AI系统测试")
    parser.add_argument("--server", default="http://localhost:8021", 
                       help="服务器地址")
    parser.add_argument("--component", choices=[
        "mcp", "agents", "meetings", "agenda", "documents", "rbac", "voice", "api"
    ], help="测试特定组件")
    
    args = parser.parse_args()
    
    tester = YDSAISystemTester(args.server)
    
    if args.component:
        # 测试特定组件
        test_methods = {
            "mcp": tester.test_mcp_message_model,
            "agents": tester.test_agent_roles,
            "meetings": tester.test_meeting_levels,
            "agenda": tester.test_intelligent_agenda,
            "documents": tester.test_document_governance,
            "rbac": tester.test_rbac_system,
            "voice": tester.test_voice_service,
            "api": tester.test_api_endpoints
        }
        
        if args.component in test_methods:
            print(f"🎯 测试组件: {args.component}")
            test_methods[args.component]()
            tester.generate_report()
        else:
            print(f"❌ 未知组件: {args.component}")
    else:
        # 运行所有测试
        tester.run_all_tests()

if __name__ == "__main__":
    main()