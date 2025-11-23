#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 全员智能体大会系统
支持多智能体有序发言、讨论、会议纪要生成
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # s:\YDS-Lab\03-dev\002-meetingroom -> s:\YDS-Lab
sys.path.insert(0, str(PROJECT_ROOT))

# 导入会议协作工具
try:
    from tools.agents.run_collab import call_agent, _summarize_actions, _meeting_meta_block
except ImportError:
    # 备用实现
    def call_agent(system_prompt: str, user_instruction: str, model: str = None) -> str:
        return f"【备用响应】系统提示: {system_prompt[:50]}...\n用户指示: {user_instruction[:50]}..."

    def _summarize_actions(all_sections_md: str, model: str = None) -> str:
        return "| 编号 | 事项 | 责任部门/人 | 优先级 | 截止日期 | 依赖 | 风险与应对 | 下一步 |\n|------|------|-------------|-------|-----------|------|-----------|--------|"

    def _meeting_meta_block(meeting_type: str, project: str, participants: List[str], 
                           agenda: List[str], extra_meta_lines: Optional[List[str]] = None) -> str:
        now = datetime.now()
        human_time = now.strftime("%Y-%m-%d %H:%M")
        lines = [
            "【会议信息】",
            f"- 会议类型：{meeting_type}",
            f"- 项目：{project}",
            f"- 时间：{human_time}",
            f"- 参会角色：{', '.join(participants)}",
        ]
        if agenda:
            lines.append(f"- 议程：{', '.join(agenda)}")
        if extra_meta_lines:
            lines.extend(extra_meta_lines)
        return "\n".join(lines) + "\n"

class AIGentConferenceSystem:
    """AI智能体全员大会系统"""
    
    def __init__(self):
        self.conference_id = f"CONF-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.project = "YDS-Lab AI公司战略规划"
        self.meeting_type = "全员智能体大会"
        
        # 3个发言频道（虚拟麦克风）
        self.microphones = {
            "麦克风1": {"status": "available", "current_speaker": None, "queue": []},
            "麦克风2": {"status": "available", "current_speaker": None, "queue": []},
            "麦克风3": {"status": "available", "current_speaker": None, "queue": []}
        }
        
        # 所有智能体角色
        self.agents = self._load_all_agents()
        
        # 会议参与者
        self.participants = self._define_participants()
        
        # 会议议程
        self.agenda = [
            "董事会战略决策指示",
            "各部门工作汇报与协同",
            "技术开发进展与挑战",
            "资源分配与预算审核",
            "风险控制与合规要求",
            "行动项确认与责任分工"
        ]
        
        self.recordings = []
        self.decisions = []
        self.action_items = []
        
    def _load_all_agents(self) -> Dict[str, Dict]:
        """加载所有智能体角色配置"""
        agents_root = Path(PROJECT_ROOT) / "01-struc" / "Agents"
        
        agents = {}
        for agent_dir in agents_root.iterdir():
            if agent_dir.is_dir() and agent_dir.name != "__pycache__":
                role_meta_file = agent_dir / "role.meta.json"
                if role_meta_file.exists():
                    try:
                        role_meta = json.loads(role_meta_file.read_text(encoding='utf-8'))
                        agents[role_meta['role_id']] = {
                            'name_cn': role_meta['name_cn'],
                            'description_cn': role_meta['description_cn'],
                            'responsibilities': role_meta.get('responsibilities', []),
                            'module_dir': role_meta['module_dir'],
                            'role_id': role_meta['role_id']
                        }
                    except Exception as e:
                        print(f"加载 {agent_dir.name} 角色元数据失败: {e}")
        
        return agents
    
    def _define_participants(self) -> List[str]:
        """定义会议参与者列表"""
        return [
            "首席执行官",  # AGENT-01-CEO (董事长)
            "董事会助理",
            "企划总监",
            "财务总监", 
            "资源管理员",
            "开发团队代表",
            "营销总监",
            "文档治理",
            "知识库",
            "MCP管理",
            "发布/CI-CD",
            "工作区协调",
            "工程审计",
            "安全与合规",
            "RBAC治理",
            "质量指标/KPI",
            "监控与告警",
            "备份与恢复",
            "长记忆健康",
            "会议室主持"
        ]
    
    def start_conference(self):
        """启动全员大会"""
        print(f"\n🚀 {self.meeting_type} 启动")
        print(f"📋 会议ID: {self.conference_id}")
        print(f"👥 参会智能体: {len(self.participants)}名")
        print(f"🎤 可用发言频道: 3个")
        print("=" * 60)
        
        # 生成会议信息块
        meta_block = _meeting_meta_block(
            meeting_type=self.meeting_type,
            project=self.project,
            participants=self.participants,
            agenda=self.agenda
        )
        
        self.recordings.append(meta_block)
        self._conduct_agenda_phases()
        self._generate_final_summary()
        
        return self._save_conference_records()
    
    def _conduct_agenda_phases(self):
        """执行会议各阶段"""
        for i, agenda_item in enumerate(self.agenda, 1):
            print(f"\n📌 阶段 {i}: {agenda_item}")
            self._handle_agenda_phase(agenda_item, i)
    
    def _handle_agenda_phase(self, agenda_item: str, phase_num: int):
        """处理单个议程阶段"""
        phase_record = f"\n## 阶段 {phase_num}: {agenda_item}\n\n"
        
        if "董事会" in agenda_item:
            # 董事会阶段 - 董事长发言
            ceo_speech = self._invoke_ceo_speech(agenda_item)
            phase_record += f"### 🎯 战略决策指示\n{ceo_speech}\n"
            
            # 其他角色理解确认
            self._phase_confirmation_responses(phase_record, "CEO指示确认")
            
        elif "各部门" in agenda_item:
            # 各部门汇报
            phase_record += self._conduct_departmental_reports()
            
        elif "技术开发" in agenda_item:
            # 技术团队汇报
            phase_record += self._conduct_tech_reports()
            
        elif "资源" in agenda_item:
            # 资源与预算审核
            phase_record += self._conduct_resource_review()
            
        elif "风险控制" in agenda_item:
            # 风险与合规
            phase_record += self._conduct_risk_compliance()
            
        elif "行动项" in agenda_item:
            # 行动项确认
            phase_record += self._conduct_action_confirmation()
        
        self.recordings.append(phase_record)
        print(f"✅ 阶段 {phase_num} 完成")
    
    def _invoke_ceo_speech(self, agenda_item: str) -> str:
        """董事长（CEO）发言"""
        ceo_agent = self.agents.get("AGENT-01-CEO")
        if not ceo_agent:
            return "CEO角色未配置，使用默认发言模板。"
        
        # CEO战略发言
        system_prompt = f"""你是YDS-Lab的首席执行官（董事长），具有全局战略视野和决策权威。

基于以下信息进行战略指示：
- 会议主题：{agenda_item}
- 目标：确保项目成功、部门协同、风险可控

请以董事长的身份，提供具体的战略指示和决策要点，体现领导力和前瞻性。发言控制在150-200字之间。"""
        
        user_instruction = f"请就'{agenda_item}'发表战略指示，为各部门的具体工作提供明确的方向和标准。"
        
        return call_agent(system_prompt, user_instruction)
    
    def _phase_confirmation_responses(self, phase_record: str, topic: str):
        """阶段确认和理解响应"""
        confirm_agents = [
            "董事会助理", "企划总监", "财务总监", "开发团队代表"
        ]
        
        for agent_name in confirm_agents:
            agent = self._find_agent_by_name(agent_name)
            if agent:
                response = self._get_agent_response(agent, f"对'{topic}'的理解和确认", "确认理解")
                phase_record += f"#### ✅ {agent_name}确认\n{response}\n\n"
    
    def _conduct_departmental_reports(self) -> str:
        """部门汇报阶段"""
        reports = []
        
        dept_agents = [
            ("企划总监", "战略规划与项目计划"),
            ("财务总监", "财务状况与预算执行"), 
            ("营销总监", "市场推广与客户反馈"),
            ("资源管理员", "资源配置与管理")
        ]
        
        for agent_name, topic in dept_agents:
            agent = self._find_agent_by_name(agent_name)
            if agent:
                report = self._get_agent_response(agent, f"当前'{topic}'的进展、挑战和建议", "汇报")
                reports.append(f"#### 📊 {agent_name}汇报\n{report}\n")
        
        return "\n".join(reports) + "\n"
    
    def _conduct_tech_reports(self) -> str:
        """技术团队汇报"""
        tech_reports = []
        
        tech_agents = [
            ("开发团队代表", "开发进展、架构优化、技术创新"),
            ("工程审计", "工程质量、代码审查、技术标准"),
            ("发布/CI-CD", "部署流程、持续集成、质量保证"),
            ("文档治理", "技术文档、版本管理、知识传承")
        ]
        
        for agent_name, topic in tech_agents:
            agent = self._find_agent_by_name(agent_name)
            if agent:
                report = self._get_agent_response(agent, f"'{topic}'相关的技术情况", "技术汇报")
                tech_reports.append(f"#### ⚙️ {agent_name}汇报\n{report}\n")
        
        return "\n".join(tech_reports) + "\n"
    
    def _conduct_resource_review(self) -> str:
        """资源与预算审核"""
        resource_reviews = []
        
        # 资源管理员汇报
        resource_agent = self._find_agent_by_name("资源管理员")
        if resource_agent:
            report = self._get_agent_response(resource_agent, "当前资源配置状况、使用效率和优化建议", "资源汇报")
            resource_reviews.append(f"#### 💰 资源管理员汇报\n{report}\n")
        
        # 财务总监审核
        finance_agent = self._find_agent_by_name("财务总监")
        if finance_agent:
            review = self._get_agent_response(finance_agent, "预算执行情况、成本控制和财务合规", "财务审核")
            resource_reviews.append(f"#### 🏦 财务总监审核\n{review}\n")
        
        return "\n".join(resource_reviews) + "\n"
    
    def _conduct_risk_compliance(self) -> str:
        """风险控制与合规"""
        risk_reviews = []
        
        risk_agents = [
            ("安全与合规", "安全风险、合规要求、风险缓解措施"),
            ("RBAC治理", "权限管理、访问控制、数据安全"),
            ("监控与告警", "系统监控、异常检测、预警机制"),
            ("备份与恢复", "数据备份、灾难恢复、业务连续性")
        ]
        
        for agent_name, topic in risk_agents:
            agent = self._find_agent_by_name(agent_name)
            if agent:
                report = self._get_agent_response(agent, f"'{topic}'的现状评估和改进建议", "风险汇报")
                risk_reviews.append(f"#### 🛡️ {agent_name}风险评估\n{report}\n")
        
        return "\n".join(risk_reviews) + "\n"
    
    def _conduct_action_confirmation(self) -> str:
        """行动项确认与责任分工"""
        # 基于前面各阶段内容，生成行动项
        all_sections = "\n".join(self.recordings)
        
        action_summary = _summarize_actions(all_sections)
        
        self.action_items_table = action_summary
        
        return f"#### 📋 会议行动项与责任分工\n\n{action_summary}\n\n"
    
    def _find_agent_by_name(self, name_cn: str) -> Optional[Dict]:
        """根据中文名称查找智能体"""
        for agent in self.agents.values():
            if agent['name_cn'] == name_cn:
                return agent
        return None
    
    def _get_agent_response(self, agent: Dict, topic: str, report_type: str) -> str:
        """获取智能体发言/汇报"""
        system_prompt = f"""你是{agent['name_cn']}，职责：{', '.join(agent.get('responsibilities', []))}。

基于你的专业职责，请就以下主题提供{report_type}：
{topic}

要求：
- 体现专业性和责任感
- 内容具体、有建设性
- 考虑与其他部门的协同
- 字数控制在100-150字"""

        user_instruction = f"请针对'{topic}'进行{report_type}。"
        
        return call_agent(system_prompt, user_instruction)
    
    def _generate_final_summary(self):
        """生成会议总结"""
        summary = f"""
# {self.meeting_type} 总结

## 会议概况
- 会议ID: {self.conference_id}
- 参会智能体: {len(self.participants)}名
- 会议时长: 基于议程完成的动态时长
- 发言频道: 3个虚拟麦克风

## 关键决策
{chr(10).join(self.decisions)}

## 行动项跟踪
{self.action_items_table}

## 后续跟进
1. 各部门按责任分工执行行动项
2. 定期汇报进展和风险
3. 下次全员大会评估执行效果

---
*本会议纪要由YDS-Lab AI全员大会系统自动生成*
"""
        self.final_summary = summary
    
    def _save_conference_records(self) -> Dict:
        """保存会议记录"""
        # 创建会议记录目录
        meeting_dir = Path(PROJECT_ROOT) / "01-struc" / "docs" / "meetings"
        meeting_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        conf_filename = f"YDS-Lab全员大会-{timestamp}.md"
        conf_file_path = meeting_dir / conf_filename
        
        # 完整会议记录
        full_record = "\n".join(self.recordings) + "\n" + self.final_summary
        
        # 保存到文件
        conf_file_path.write_text(full_record, encoding='utf-8')
        
        conference_summary = {
            'conference_id': self.conference_id,
            'timestamp': timestamp,
            'meeting_type': self.meeting_type,
            'participants': self.participants,
            'agenda': self.agenda,
            'recordings_file': str(conf_file_path),
            'summary': self.final_summary,
            'status': 'completed'
        }
        
        print(f"\n📝 会议记录已保存: {conf_file_path}")
        return conference_summary

def main():
    """主程序入口"""
    print("🤖 YDS-Lab 全员智能体大会系统")
    print("=" * 50)
    
    # 创建会议系统
    conference = AIGentConferenceSystem()
    
    # 启动会议
    try:
        result = conference.start_conference()
        
        print(f"\n🎉 全员大会圆满结束！")
        print(f"📋 会议记录: {result['recordings_file']}")
        print(f"🔍 会议ID: {result['conference_id']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 会议执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()