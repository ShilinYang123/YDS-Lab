#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 会议纪要生成工具

功能：
- 自动生成会议纪要模板
- 解析会议记录
- 格式化会议内容
- 生成行动项清单
- 导出多种格式

适配YDS-Lab项目会议管理需求
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import re

class YDSLabMeetingLogGenerator:
    """YDS-Lab会议纪要生成器"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.meetings_dir = self.project_root / "Struc" / "GeneralOffice" / "logs" / "meetings"
        self.docs_dir = self.project_root / "Docs"
        
        # 确保目录存在
        self.meetings_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 会议类型配置
        self.meeting_types = {
            'daily': {
                'name': '每日站会',
                'duration': 30,
                'template': 'daily_standup'
            },
            'weekly': {
                'name': '周会',
                'duration': 60,
                'template': 'weekly_review'
            },
            'planning': {
                'name': '规划会议',
                'duration': 120,
                'template': 'planning_meeting'
            },
            'review': {
                'name': '评审会议',
                'duration': 90,
                'template': 'review_meeting'
            },
            'retrospective': {
                'name': '回顾会议',
                'duration': 90,
                'template': 'retrospective'
            }
        }
        
        # 参与者角色
        self.participant_roles = [
            'CEO', '规划总监', '财务总监', '资源管理员', 
            '开发总监', '开发架构师', '开发工程师', '测试工程师',
            '市场总监', '产品经理', '项目经理'
        ]
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            logs_dir = self.project_root / "Struc" / "GeneralOffice" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = logs_dir / "meeting_log_generator.log"
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("会议纪要生成器初始化")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            self.logger = logging.getLogger(__name__)
    
    def create_meeting_template(self, meeting_type: str, title: str, 
                              date: str = None, participants: List[str] = None) -> Dict:
        """创建会议纪要模板"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if participants is None:
            participants = []
        
        meeting_config = self.meeting_types.get(meeting_type, self.meeting_types['weekly'])
        
        template = {
            'meeting_info': {
                'title': title,
                'type': meeting_type,
                'type_name': meeting_config['name'],
                'date': date,
                'start_time': '',
                'end_time': '',
                'duration_minutes': meeting_config['duration'],
                'location': '线上/线下',
                'organizer': '',
                'recorder': ''
            },
            'participants': {
                'attendees': participants,
                'absent': [],
                'guests': []
            },
            'agenda': [
                {
                    'item': '会议开场',
                    'duration': 5,
                    'presenter': '',
                    'description': '会议目标和议程介绍'
                }
            ],
            'discussion_points': [
                {
                    'topic': '',
                    'discussion': '',
                    'decisions': [],
                    'action_items': []
                }
            ],
            'action_items': [
                {
                    'id': 1,
                    'description': '',
                    'assignee': '',
                    'due_date': '',
                    'priority': 'medium',
                    'status': 'pending'
                }
            ],
            'decisions': [
                {
                    'decision': '',
                    'rationale': '',
                    'impact': '',
                    'responsible': ''
                }
            ],
            'next_steps': [],
            'next_meeting': {
                'date': '',
                'agenda_preview': []
            },
            'attachments': [],
            'notes': ''
        }
        
        return template
    
    def generate_meeting_log(self, template: Dict, output_format: str = 'markdown') -> str:
        """生成会议纪要"""
        if output_format == 'markdown':
            return self._generate_markdown_log(template)
        elif output_format == 'json':
            return json.dumps(template, indent=2, ensure_ascii=False)
        elif output_format == 'yaml':
            return yaml.dump(template, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _generate_markdown_log(self, template: Dict) -> str:
        """生成Markdown格式的会议纪要"""
        meeting_info = template['meeting_info']
        participants = template['participants']
        
        md_content = f"""# {meeting_info['title']}

## 会议信息
- **会议类型**: {meeting_info['type_name']}
- **日期**: {meeting_info['date']}
- **时间**: {meeting_info.get('start_time', 'TBD')} - {meeting_info.get('end_time', 'TBD')}
- **时长**: {meeting_info['duration_minutes']} 分钟
- **地点**: {meeting_info['location']}
- **组织者**: {meeting_info.get('organizer', 'TBD')}
- **记录者**: {meeting_info.get('recorder', 'TBD')}

## 参与者
### 出席人员
"""
        
        # 参与者信息
        if participants['attendees']:
            for attendee in participants['attendees']:
                md_content += f"- {attendee}\n"
        else:
            md_content += "- TBD\n"
        
        if participants['absent']:
            md_content += "\n### 缺席人员\n"
            for absent in participants['absent']:
                md_content += f"- {absent}\n"
        
        if participants['guests']:
            md_content += "\n### 特邀嘉宾\n"
            for guest in participants['guests']:
                md_content += f"- {guest}\n"
        
        # 议程
        md_content += "\n## 会议议程\n"
        for i, agenda_item in enumerate(template['agenda'], 1):
            md_content += f"{i}. **{agenda_item['item']}** ({agenda_item['duration']}分钟)\n"
            md_content += f"   - 主讲人: {agenda_item.get('presenter', 'TBD')}\n"
            md_content += f"   - 描述: {agenda_item.get('description', '')}\n\n"
        
        # 讨论要点
        md_content += "## 讨论要点\n"
        for i, point in enumerate(template['discussion_points'], 1):
            if point['topic']:
                md_content += f"### {i}. {point['topic']}\n"
                md_content += f"**讨论内容**: {point.get('discussion', 'TBD')}\n\n"
                
                if point.get('decisions'):
                    md_content += "**决策**:\n"
                    for decision in point['decisions']:
                        md_content += f"- {decision}\n"
                    md_content += "\n"
                
                if point.get('action_items'):
                    md_content += "**行动项**:\n"
                    for action in point['action_items']:
                        md_content += f"- {action}\n"
                    md_content += "\n"
        
        # 行动项
        md_content += "## 行动项清单\n"
        md_content += "| ID | 描述 | 负责人 | 截止日期 | 优先级 | 状态 |\n"
        md_content += "|----|----|----|----|----|----|\\n"
        
        for action in template['action_items']:
            md_content += f"| {action.get('id', '')} | {action.get('description', 'TBD')} | "
            md_content += f"{action.get('assignee', 'TBD')} | {action.get('due_date', 'TBD')} | "
            md_content += f"{action.get('priority', 'medium')} | {action.get('status', 'pending')} |\n"
        
        # 决策记录
        if template['decisions'] and any(d.get('decision') for d in template['decisions']):
            md_content += "\n## 决策记录\n"
            for i, decision in enumerate(template['decisions'], 1):
                if decision.get('decision'):
                    md_content += f"### 决策 {i}\n"
                    md_content += f"**决策内容**: {decision['decision']}\n"
                    md_content += f"**决策依据**: {decision.get('rationale', 'TBD')}\n"
                    md_content += f"**影响范围**: {decision.get('impact', 'TBD')}\n"
                    md_content += f"**负责人**: {decision.get('responsible', 'TBD')}\n\n"
        
        # 下一步计划
        if template['next_steps']:
            md_content += "## 下一步计划\n"
            for step in template['next_steps']:
                md_content += f"- {step}\n"
        
        # 下次会议
        next_meeting = template['next_meeting']
        if next_meeting.get('date'):
            md_content += f"\n## 下次会议\n"
            md_content += f"- **日期**: {next_meeting['date']}\n"
            if next_meeting.get('agenda_preview'):
                md_content += "- **预期议程**:\n"
                for agenda in next_meeting['agenda_preview']:
                    md_content += f"  - {agenda}\n"
        
        # 附件
        if template['attachments']:
            md_content += "\n## 附件\n"
            for attachment in template['attachments']:
                md_content += f"- {attachment}\n"
        
        # 备注
        if template.get('notes'):
            md_content += f"\n## 备注\n{template['notes']}\n"
        
        # 生成信息
        md_content += f"\n---\n*会议纪要生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return md_content
    
    def save_meeting_log(self, content: str, filename: str, 
                        output_format: str = 'markdown') -> Path:
        """保存会议纪要"""
        # 确定文件扩展名
        extensions = {
            'markdown': '.md',
            'json': '.json',
            'yaml': '.yaml'
        }
        
        ext = extensions.get(output_format, '.md')
        if not filename.endswith(ext):
            filename += ext
        
        # 保存到会议目录
        file_path = self.meetings_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"会议纪要已保存: {file_path}")
        return file_path
    
    def create_quick_meeting_log(self, title: str, meeting_type: str = 'weekly',
                               participants: List[str] = None,
                               output_format: str = 'markdown') -> Path:
        """快速创建会议纪要"""
        # 生成文件名
        date_str = datetime.now().strftime('%Y%m%d')
        safe_title = re.sub(r'[^\w\-_\.]', '_', title)
        filename = f"{date_str}_{safe_title}"
        
        # 创建模板
        template = self.create_meeting_template(
            meeting_type=meeting_type,
            title=title,
            participants=participants or []
        )
        
        # 生成内容
        content = self.generate_meeting_log(template, output_format)
        
        # 保存文件
        return self.save_meeting_log(content, filename, output_format)
    
    def list_meeting_types(self) -> Dict:
        """列出可用的会议类型"""
        return self.meeting_types
    
    def list_participant_roles(self) -> List[str]:
        """列出可用的参与者角色"""
        return self.participant_roles
    
    def get_recent_meetings(self, days: int = 30) -> List[Dict]:
        """获取最近的会议记录"""
        if not self.meetings_dir.exists():
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_meetings = []
        
        for file_path in self.meetings_dir.glob('*.md'):
            try:
                # 从文件名提取日期
                date_match = re.search(r'(\d{8})', file_path.stem)
                if date_match:
                    file_date = datetime.strptime(date_match.group(1), '%Y%m%d')
                    if file_date >= cutoff_date:
                        recent_meetings.append({
                            'file': file_path.name,
                            'date': file_date.strftime('%Y-%m-%d'),
                            'title': file_path.stem.replace(date_match.group(1) + '_', '').replace('_', ' ')
                        })
            except:
                continue
        
        return sorted(recent_meetings, key=lambda x: x['date'], reverse=True)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab会议纪要生成工具')
    parser.add_argument('title', help='会议标题')
    parser.add_argument('--type', '-t', default='weekly', 
                       help='会议类型 (daily, weekly, planning, review, retrospective)')
    parser.add_argument('--format', '-f', default='markdown',
                       help='输出格式 (markdown, json, yaml)')
    parser.add_argument('--participants', '-p', nargs='*',
                       help='参与者列表')
    parser.add_argument('--list-types', action='store_true',
                       help='列出可用的会议类型')
    parser.add_argument('--list-roles', action='store_true',
                       help='列出可用的参与者角色')
    parser.add_argument('--recent', type=int, metavar='DAYS',
                       help='显示最近N天的会议记录')
    
    args = parser.parse_args()
    
    generator = YDSLabMeetingLogGenerator()
    
    if args.list_types:
        print("可用的会议类型:")
        for key, meeting_type in generator.list_meeting_types().items():
            print(f"  {key}: {meeting_type['name']} ({meeting_type['duration']}分钟)")
        return
    
    if args.list_roles:
        print("可用的参与者角色:")
        for role in generator.list_participant_roles():
            print(f"  - {role}")
        return
    
    if args.recent:
        meetings = generator.get_recent_meetings(args.recent)
        if meetings:
            print(f"最近{args.recent}天的会议记录:")
            for meeting in meetings:
                print(f"  {meeting['date']}: {meeting['title']}")
        else:
            print(f"最近{args.recent}天没有会议记录")
        return
    
    # 创建会议纪要
    try:
        file_path = generator.create_quick_meeting_log(
            title=args.title,
            meeting_type=args.type,
            participants=args.participants,
            output_format=args.format
        )
        
        print(f"会议纪要已创建: {file_path}")
        
    except Exception as e:
        print(f"创建会议纪要失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()