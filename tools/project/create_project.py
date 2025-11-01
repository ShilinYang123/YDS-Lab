#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YDS-Lab 项目创建工具

功能：
- 创建新项目目录结构
- 初始化项目配置文件
- 设置项目模板
- 生成项目文档
- 配置开发环境

适配YDS-Lab项目管理需求
"""

import os
import sys
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

class YDSLabProjectCreator:
    """YDS-Lab项目创建器"""
    
    def __init__(self, project_root: str = "s:/YDS-Lab"):
        self.project_root = Path(project_root)
        self.projects_dir = self.project_root / "projects"
        self.templates_dir = self.projects_dir / "templates"
        
        # 设置日志
        self.setup_logging()
        
        # 项目模板配置
        self.project_templates = {
            'basic': {
                'name': '基础项目',
                'description': '基本的Python项目结构',
                'directories': ['src', 'tests', 'docs', 'config'],
                'files': ['README.md', 'requirements.txt', '.gitignore']
            },
            'ai': {
                'name': 'AI项目',
                'description': 'AI/机器学习项目结构',
                'directories': ['src', 'data', 'models', 'notebooks', 'tests', 'docs'],
                'files': ['README.md', 'requirements.txt', 'config.yaml', '.gitignore']
            },
            'web': {
                'name': 'Web应用',
                'description': 'Web应用项目结构',
                'directories': ['src', 'static', 'templates', 'tests', 'docs'],
                'files': ['app.py', 'requirements.txt', 'config.py', '.gitignore']
            }
        }
        
    def setup_logging(self):
        """设置日志系统"""
        try:
            logs_dir = self.project_root / "Struc" / "GeneralOffice" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = logs_dir / "project_creator.log"
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("项目创建器初始化")
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            self.logger = logging.getLogger(__name__)
    
    def create_project(self, project_name: str, template: str = 'basic', 
                      description: str = "", author: str = "") -> bool:
        """创建新项目"""
        try:
            self.logger.info(f"开始创建项目: {project_name}")
            
            # 验证项目名称
            if not self.validate_project_name(project_name):
                return False
            
            # 检查模板是否存在
            if template not in self.project_templates:
                self.logger.error(f"未知的项目模板: {template}")
                return False
            
            # 创建项目目录
            project_path = self.projects_dir / project_name
            if project_path.exists():
                self.logger.error(f"项目目录已存在: {project_path}")
                return False
            
            project_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建项目目录: {project_path}")
            
            # 根据模板创建结构
            template_config = self.project_templates[template]
            self.create_project_structure(project_path, template_config)
            
            # 创建项目配置文件
            self.create_project_config(project_path, {
                'name': project_name,
                'description': description,
                'author': author,
                'template': template,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0'
            })
            
            self.logger.info(f"项目 {project_name} 创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建项目失败: {e}")
            return False
    
    def validate_project_name(self, name: str) -> bool:
        """验证项目名称"""
        if not name or not name.strip():
            self.logger.error("项目名称不能为空")
            return False
        
        if not name.replace('-', '').replace('_', '').isalnum():
            self.logger.error("项目名称只能包含字母、数字、连字符和下划线")
            return False
        
        return True
    
    def create_project_structure(self, project_path: Path, template_config: Dict):
        """创建项目目录结构"""
        # 创建目录
        for directory in template_config['directories']:
            dir_path = project_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"创建目录: {dir_path}")
        
        # 创建文件
        for file_name in template_config['files']:
            file_path = project_path / file_name
            if not file_path.exists():
                file_path.touch()
                self.logger.info(f"创建文件: {file_path}")
    
    def create_project_config(self, project_path: Path, config: Dict):
        """创建项目配置文件"""
        config_file = project_path / "project.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        self.logger.info(f"创建配置文件: {config_file}")
    
    def list_templates(self) -> Dict:
        """列出可用的项目模板"""
        return self.project_templates
    
    def list_projects(self) -> List[str]:
        """列出已创建的项目"""
        if not self.projects_dir.exists():
            return []
        
        projects = []
        for item in self.projects_dir.iterdir():
            if item.is_dir() and item.name != 'templates':
                projects.append(item.name)
        
        return sorted(projects)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab项目创建工具')
    parser.add_argument('name', help='项目名称')
    parser.add_argument('--template', '-t', default='basic', 
                       help='项目模板 (basic, ai, web)')
    parser.add_argument('--description', '-d', default='', 
                       help='项目描述')
    parser.add_argument('--author', '-a', default='', 
                       help='项目作者')
    parser.add_argument('--list-templates', action='store_true',
                       help='列出可用模板')
    parser.add_argument('--list-projects', action='store_true',
                       help='列出已创建的项目')
    
    args = parser.parse_args()
    
    creator = YDSLabProjectCreator()
    
    if args.list_templates:
        print("可用的项目模板:")
        for key, template in creator.list_templates().items():
            print(f"  {key}: {template['name']} - {template['description']}")
        return
    
    if args.list_projects:
        projects = creator.list_projects()
        if projects:
            print("已创建的项目:")
            for project in projects:
                print(f"  - {project}")
        else:
            print("暂无已创建的项目")
        return
    
    # 创建项目
    success = creator.create_project(
        project_name=args.name,
        template=args.template,
        description=args.description,
        author=args.author
    )
    
    if success:
        print(f"项目 '{args.name}' 创建成功!")
    else:
        print(f"项目 '{args.name}' 创建失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()