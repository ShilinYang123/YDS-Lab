#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品高ISO流程图质量检查工具
检查生成的流程图文件是否符合命名规范、目录结构要求，验证流程图内容准确性和可读性

作者：杨世林 雨俊 3AI工作室
版本: 1.0.0
更新日期: 2024-12-19
"""

import os
import re
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
import logging

# 配置日志
logger = logging.getLogger(__name__)


class FlowchartQualityChecker:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.report_data = {
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'naming_issues': [],
            'content_issues': [],
            'file_details': []
        }
    
    def check_file_naming(self, file_path):
        """检查文件命名规范"""
        filename = file_path.name
        issues = []
        
        # 检查文件扩展名
        if not filename.endswith('.drawio'):
            issues.append(f"文件扩展名不正确: {filename}")
        
        # 检查是否包含"流程图"字样
        if "流程图" not in filename:
            issues.append(f"文件名缺少'流程图'标识: {filename}")
        
        # 检查是否以HQ-QP-开头
        base_name = filename.replace('_流程图.drawio', '')
        if not base_name.startswith('HQ-QP-'):
            issues.append(f"文件名不符合HQ-QP-开头规范: {filename}")
        
        return issues
    
    def check_drawio_content(self, file_path):
        """检查Draw.io文件内容"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否为有效的XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                issues.append(f"XML格式错误: {str(e)}")
                return issues
            
            # 检查是否包含mxGraphModel
            if 'mxGraphModel' not in content:
                issues.append("缺少mxGraphModel元素")
            
            # 检查是否包含基本的流程图元素
            if 'mxCell' not in content:
                issues.append("缺少mxCell元素")
            
            # 检查是否包含流程图节点
            node_count = content.count('mxCell')
            if node_count < 3:  # 至少应该有开始、处理、结束节点
                issues.append(f"流程图节点数量过少: {node_count}")
            
            # 检查是否包含连接线
            edge_count = content.count('edge="1"')
            if edge_count < 1:
                issues.append("缺少连接线")
            
        except Exception as e:
            issues.append(f"文件读取错误: {str(e)}")
        
        return issues
    
    def check_single_file(self, file_path):
        """检查单个文件"""
        file_info = {
            'filename': file_path.name,
            'path': str(file_path),
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'naming_issues': [],
            'content_issues': [],
            'is_valid': True
        }
        
        # 检查文件是否存在
        if not file_path.exists():
            file_info['content_issues'].append("文件不存在")
            file_info['is_valid'] = False
            return file_info
        
        # 检查文件大小
        if file_info['size'] == 0:
            file_info['content_issues'].append("文件为空")
            file_info['is_valid'] = False
        elif file_info['size'] < 500:  # Draw.io文件通常至少几百字节
            file_info['content_issues'].append("文件过小，可能内容不完整")
        
        # 检查命名规范
        naming_issues = self.check_file_naming(file_path)
        file_info['naming_issues'] = naming_issues
        if naming_issues:
            file_info['is_valid'] = False
        
        # 检查内容
        content_issues = self.check_drawio_content(file_path)
        file_info['content_issues'].extend(content_issues)
        if content_issues:
            file_info['is_valid'] = False
        
        return file_info
    
    def run_quality_check(self):
        """运行质量检查"""
        logger.info(f"开始质量检查: {self.output_dir}")
        
        # 获取所有.drawio文件
        drawio_files = list(self.output_dir.glob('*.drawio'))
        self.report_data['total_files'] = len(drawio_files)
        
        logger.info(f"找到 {len(drawio_files)} 个流程图文件")
        
        # 检查每个文件
        for i, file_path in enumerate(drawio_files, 1):
            logger.info(f"[{i}/{len(drawio_files)}] 检查: {file_path.name}")
            
            file_info = self.check_single_file(file_path)
            self.report_data['file_details'].append(file_info)
            
            if file_info['is_valid']:
                self.report_data['valid_files'] += 1
                logger.info(f"  ✅ 通过")
            else:
                self.report_data['invalid_files'] += 1
                logger.warning(f"  ❌ 发现问题:")
                for issue in file_info['naming_issues'] + file_info['content_issues']:
                    logger.warning(f"    - {issue}")
                    if issue not in self.report_data['naming_issues'] + self.report_data['content_issues']:
                        if '命名' in issue or '文件名' in issue:
                            self.report_data['naming_issues'].append(issue)
                        else:
                            self.report_data['content_issues'].append(issue)
        
        return self.report_data
    
    def generate_quality_report(self):
        """生成质量检查报告"""
        report_path = self.output_dir / "质量检查报告.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 品高ISO流程图质量检查报告\n\n")
            f.write(f"检查时间: {self.report_data['check_time']}\n\n")
            
            # 总体统计
            f.write("## 检查统计\n\n")
            f.write(f"- **总文件数**: {self.report_data['total_files']}\n")
            f.write(f"- **通过检查**: {self.report_data['valid_files']}\n")
            f.write(f"- **存在问题**: {self.report_data['invalid_files']}\n")
            if self.report_data['total_files'] > 0:
                f.write(f"- **通过率**: {(self.report_data['valid_files']/self.report_data['total_files']*100):.1f}%\n\n")
            else:
                f.write("- **通过率**: 0%\n\n")
            
            # 问题汇总
            if self.report_data['naming_issues'] or self.report_data['content_issues']:
                f.write("## 问题汇总\n\n")
                
                if self.report_data['naming_issues']:
                    f.write("### 命名规范问题\n\n")
                    for issue in set(self.report_data['naming_issues']):
                        f.write(f"- {issue}\n")
                    f.write("\n")
                
                if self.report_data['content_issues']:
                    f.write("### 内容质量问题\n\n")
                    for issue in set(self.report_data['content_issues']):
                        f.write(f"- {issue}\n")
                    f.write("\n")
            
            # 详细检查结果
            f.write("## 详细检查结果\n\n")
            f.write("| 序号 | 文件名 | 状态 | 文件大小 | 问题描述 |\n")
            f.write("|------|--------|------|----------|----------|\n")
            
            for i, file_info in enumerate(self.report_data['file_details'], 1):
                status = "✅ 通过" if file_info['is_valid'] else "❌ 问题"
                size_kb = f"{file_info['size']/1024:.1f}KB" if file_info['size'] > 0 else "0KB"
                issues = file_info['naming_issues'] + file_info['content_issues']
                issue_text = "; ".join(issues) if issues else "无"
                
                f.write(f"| {i} | {file_info['filename']} | {status} | {size_kb} | {issue_text} |\n")
            
            f.write("\n## 建议\n\n")
            if self.report_data['invalid_files'] == 0:
                f.write("🎉 所有流程图文件均通过质量检查，符合规范要求。\n")
            else:
                f.write("请根据上述问题描述修复相关文件，确保所有流程图符合质量标准。\n")
            
            f.write("\n## 使用说明\n\n")
            f.write("所有通过检查的流程图文件均可：\n")
            f.write("1. 在 https://app.diagrams.net 中直接打开\n")
            f.write("2. 使用Draw.io桌面版编辑\n")
            f.write("3. 在VS Code中安装Draw.io插件后查看\n")
        
        logger.info(f"📊 质量检查报告已生成: {report_path}")
        return report_path


def main():
    """主函数"""
    # 默认检查目录，可根据实际项目调整
    output_dir = "S:/YDS-Lab/Docs/流程图"
    
    # 如果目录不存在，尝试其他可能的路径
    if not Path(output_dir).exists():
        possible_paths = [
            "S:/YDS-Lab/Docs/ISO流程图",
            "S:/YDS-Lab/Output/流程图",
            "./流程图",
            "./docs/流程图"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                output_dir = path
                break
        else:
            logger.warning(f"未找到流程图目录，使用默认路径: {output_dir}")
    
    checker = FlowchartQualityChecker(output_dir)
    report_data = checker.run_quality_check()
    report_path = checker.generate_quality_report()
    
    print(f"\n=== 质量检查完成 ===")
    print(f"📁 检查目录: {output_dir}")
    print(f"📊 总文件数: {report_data['total_files']}")
    print(f"✅ 通过检查: {report_data['valid_files']}")
    print(f"❌ 存在问题: {report_data['invalid_files']}")
    if report_data['total_files'] > 0:
        print(f"📈 通过率: {(report_data['valid_files']/report_data['total_files']*100):.1f}%")
    print(f"📋 详细报告: {report_path}")
    
    return report_data


if __name__ == "__main__":
    main()