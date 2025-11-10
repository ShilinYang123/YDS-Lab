#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 文档维护自动化系统
用于定期检查和维护项目文档的完整性和一致性
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class DocumentMaintenanceSystem:
    """文档维护系统"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初始化文档维护系统"""
        self.project_root = project_root or Path.cwd()
        self.docs_dir = self.project_root / "docs"
        self.reports_dir = self.project_root / "reports"
        self.config_file = self.project_root / "config" / "doc_maintenance_config.json"
        
        # 确保必要的目录存在
        self.reports_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "required_docs": [
                "project_structure.md",
                "README.md",
                "api_documentation.md",
                "configuration.md",
                "deployment_guide.md"
            ],
            "check_intervals": {
                "daily": ["project_structure.md"],
                "weekly": ["README.md"],
                "monthly": ["api_documentation.md", "configuration.md"]
            },
            "doc_standards": {
                "min_word_count": 100,
                "required_sections": ["简介", "安装", "使用", "文档"],
                "max_file_age_days": 30
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置
                    default_config.update(loaded_config)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
                
        return default_config
        
    def check_document_completeness(self) -> Dict[str, Any]:
        """检查文档完整性"""
        print("正在检查文档完整性...")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "missing_docs": [],
            "outdated_docs": [],
            "invalid_docs": [],
            "total_docs": 0,
            "valid_docs": 0
        }
        
        # 检查必需文档
        for doc_name in self.config["required_docs"]:
            doc_path = self.docs_dir / doc_name
            
            if not doc_path.exists():
                result["missing_docs"].append(doc_name)
                print(f"[缺失] 缺失文档: {doc_name}")
            else:
                result["total_docs"] += 1
                
                # 检查文档有效性
                validation_result = self._validate_document(doc_path)
                if validation_result["valid"]:
                    result["valid_docs"] += 1
                    print(f"[有效] 有效文档: {doc_name}")
                else:
                    result["invalid_docs"].append({
                        "name": doc_name,
                        "issues": validation_result["issues"]
                    })
                    print(f"[警告] 无效文档: {doc_name} - {validation_result['issues']}")
                    
                # 检查文档是否过期
                if self._is_document_outdated(doc_path):
                    result["outdated_docs"].append(doc_name)
                    print(f"[过期] 过期文档: {doc_name}")
                    
        return result
        
    def _validate_document(self, doc_path: Path) -> Dict[str, Any]:
        """验证文档"""
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            issues = []
            
            # 检查字数
            word_count = len(content.split())
            if word_count < self.config["doc_standards"]["min_word_count"]:
                issues.append(f"字数不足: {word_count} < {self.config['doc_standards']['min_word_count']}")
                
            # 检查必需章节
            for section in self.config["doc_standards"]["required_sections"]:
                if section not in content:
                    issues.append(f"缺少章节: {section}")
                    
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "word_count": word_count
            }
            
        except Exception as e:
            return {
                "valid": False,
                "issues": [f"读取失败: {str(e)}"],
                "word_count": 0
            }
            
    def _is_document_outdated(self, doc_path: Path) -> bool:
        """检查文档是否过期"""
        try:
            file_age = datetime.now() - datetime.fromtimestamp(doc_path.stat().st_mtime)
            return file_age.days > self.config["doc_standards"]["max_file_age_days"]
        except OSError:
            return True
            
    def generate_missing_documents(self, check_result: Dict[str, Any]) -> List[str]:
        """生成缺失的文档"""
        print("正在生成缺失文档...")
        generated_files = []
        
        for doc_name in check_result["missing_docs"]:
            if doc_name == "project_structure.md":
                self._generate_project_structure_doc()
                generated_files.append("project_structure.md")
                print(f"[成功] 生成项目结构文档")
                
            elif doc_name == "README.md":
                self._generate_readme_doc()
                generated_files.append("README.md")
                print(f"[成功] 生成README文档")
                
            elif doc_name == "api_documentation.md":
                self._generate_api_doc()
                generated_files.append("api_documentation.md")
                print(f"[成功] 生成API文档")
                
            elif doc_name == "configuration.md":
                self._generate_config_doc()
                generated_files.append("configuration.md")
                print(f"[成功] 生成配置文档")
                
            elif doc_name == "deployment_guide.md":
                self._generate_deployment_doc()
                generated_files.append("deployment_guide.md")
                print(f"[成功] 生成部署指南")
                
        return generated_files
        
    def _generate_project_structure_doc(self):
        """生成项目结构文档"""
        try:
            subprocess.run([
                "python", "-m", "tools.scripts.doc_generator",
                "--type", "structure"
            ], cwd=self.project_root, check=True)
        except subprocess.CalledProcessError:
            print("[错误] 项目结构文档生成失败")
            
    def _generate_readme_doc(self):
        """生成README文档"""
        try:
            subprocess.run([
                "python", "-m", "tools.scripts.doc_generator",
                "--type", "readme"
            ], cwd=self.project_root, check=True)
        except subprocess.CalledProcessError:
            print("[错误] README文档生成失败")
            
    def _generate_api_doc(self):
        """生成API文档"""
        content = """# API 文档

## 概述

YDS-Lab API 提供了一套完整的接口用于管理多智能体系统。

## 认证

所有API请求都需要包含认证信息。

## 端点

### 智能体管理

- `GET /api/agents` - 获取智能体列表
- `POST /api/agents` - 创建新智能体
- `GET /api/agents/{id}` - 获取智能体详情
- `PUT /api/agents/{id}` - 更新智能体
- `DELETE /api/agents/{id}` - 删除智能体

### 任务管理

- `GET /api/tasks` - 获取任务列表
- `POST /api/tasks` - 创建新任务
- `GET /api/tasks/{id}` - 获取任务详情
- `PUT /api/tasks/{id}` - 更新任务状态

## 错误处理

API使用标准的HTTP状态码表示请求结果。

---
*本文档由自动化工具生成*
"""
        
        api_doc_path = self.docs_dir / "api_documentation.md"
        with open(api_doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def _generate_config_doc(self):
        """生成配置文档"""
        content = """# 配置文档

## 概述

YDS-Lab 使用多种配置文件来管理系统行为。

## 主要配置

### 主配置文件

- `config/yds_ai_config.yaml` - 主系统配置
- `config/production.yaml` - 生产环境配置
- `config/trae_config.yaml` - Trae平台配置

### 智能体配置

- `config/rbac_config.json` - 权限配置
- `config/long_memory_config.json` - 长记忆配置

### 服务配置

- `config/meetingroom_config.json` - 会议室服务配置
- `config/voice_service_config.json` - 语音服务配置

## 配置格式

所有配置文件都使用标准的格式（YAML、JSON）。

---
*本文档由自动化工具生成*
"""
        
        config_doc_path = self.docs_dir / "configuration.md"
        with open(config_doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def _generate_deployment_doc(self):
        """生成部署文档"""
        content = """# 部署指南

## 系统要求

- Python 3.8+
- 8GB RAM
- 10GB 可用磁盘空间

## 安装步骤

1. **环境准备**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\\Scripts\\activate     # Windows
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置系统**
   ```bash
   python ch.py --setup
   ```

4. **启动服务**
   ```bash
   python ch.py --start
   ```

## 验证部署

访问 `http://localhost:8080` 验证系统是否正常运行。

## 故障排除

查看日志文件 `logs/system.log` 获取详细的错误信息。

---
*本文档由自动化工具生成*
"""
        
        deployment_doc_path = self.docs_dir / "deployment_guide.md"
        with open(deployment_doc_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def run_maintenance(self) -> Dict[str, Any]:
        """运行完整的维护流程"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始文档维护任务")
        
        # 检查文档完整性
        check_result = self.check_document_completeness()
        
        # 生成缺失文档
        generated_files = []
        if check_result["missing_docs"]:
            generated_files = self.generate_missing_documents(check_result)
            
        # 生成维护报告
        maintenance_report = {
            "timestamp": datetime.now().isoformat(),
            "check_result": check_result,
            "generated_files": generated_files,
            "total_actions": len(generated_files) + len(check_result["invalid_docs"]),
            "status": "completed"
        }
        
        # 保存报告
        report_path = self.reports_dir / f"doc_maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(maintenance_report, f, ensure_ascii=False, indent=2)
            
        # 输出摘要
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 文档维护完成")
        print(f"检查文档: {check_result['total_docs']} 个")
        print(f"缺失文档: {len(check_result['missing_docs'])}")
        print(f"生成文档: {len(generated_files)} 个")
        print(f"无效文档: {len(check_result['invalid_docs'])} 个")
        print(f"过期文档: {len(check_result['outdated_docs'])} 个")
        print(f"维护报告: {report_path}")
        
        # 返回结果
        return maintenance_report
        
        return maintenance_report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 文档维护系统')
    parser.add_argument('--check-only', action='store_true', 
                       help='仅检查，不生成缺失文档')
    parser.add_argument('--generate-missing', action='store_true',
                       help='生成缺失的文档')
    parser.add_argument('--config', type=str,
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 创建维护系统
    maintenance_system = DocumentMaintenanceSystem()
    
    try:
        if args.check_only:
            # 仅检查模式
            result = maintenance_system.check_document_completeness()
            print(f"\n文档完整性检查结果:")
            print(f"总文档数: {result['total_docs']}")
            print(f"缺失文档: {len(result['missing_docs'])}")
            print(f"无效文档: {len(result['invalid_docs'])}")
            print(f"过期文档: {len(result['outdated_docs'])}")
            return 0 if len(result['missing_docs']) == 0 else 1
            
        elif args.generate_missing:
            # 生成缺失文档模式
            check_result = maintenance_system.check_document_completeness()
            if check_result['missing_docs']:
                generated = maintenance_system.generate_missing_documents(check_result)
                print(f"生成了 {len(generated)} 个文档")
                return 0
            else:
                print("没有缺失的文档需要生成")
                return 0
                
        else:
            # 完整维护模式
            result = maintenance_system.run_maintenance()
            return 0 if len(result['check_result']['missing_docs']) == 0 else 1
            
    except Exception as e:
        print(f"文档维护失败: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())