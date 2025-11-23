#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enco.py - 自动高级编码监测工具（安全加固版）
YDS-Lab系统维护工具，符合三级存储规范

功能：
- 自动检测项目文件编码问题
- 支持多种编码格式识别
- 生成详细的编码分析报告
- 符合YDS-Lab V5.1架构规范

存储规范：
- 检查报告 → logs/encoding_reports/
- 检测结果 → rep/encoding_analysis/
- 临时文件 → bak/encoding_temp/

安全特性：
- 只读文件检测，无修改风险
- 文件大小限制（10MB）
- 完整异常处理
- 路径验证
- 保守编码检测
"""

import os
import sys
import json
import chardet
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class AutoEncodingMonitor:
    """自动编码监测器（安全加固版）"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.report_dir = self.project_root / "logs" / "encoding_reports"
        self.result_dir = self.project_root / "rep" / "encoding_analysis"
        self.temp_dir = self.project_root / "bak" / "encoding_temp"
        
        # 安全限制
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_read_size = 1024 * 1024  # 1MB读取限制
        
        self.supported_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.json', '.yml', '.yaml',
            '.md', '.txt', '.sh', '.bash', '.bat', '.cmd', '.css', '.html', '.htm',
            '.xml', '.ini', '.cfg', '.conf', '.properties', '.java', '.cpp', '.c',
            '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
            '.dockerfile', '.gitignore', '.env'
        }
        
        self.exclude_dirs = {'.git', '__pycache__', 'node_modules', '.vscode', '.idea', 'bak', 'backup'}
        
        # 安全检查：确保项目根目录有效
        if not self.project_root.exists():
            raise ValueError(f"项目根目录不存在: {self.project_root}")
        
        if not self.project_root.is_dir():
            raise ValueError(f"项目根目录不是有效目录: {self.project_root}")
    
    def safe_detect_encoding(self, file_path: Path) -> Dict:
        """安全检测文件编码 - 只读操作"""
        result = {
            "file": str(file_path.relative_to(self.project_root)),
            "file_size": 0,
            "encoding": "unknown",
            "confidence": 0.0,
            "has_bom": False,
            "status": "unknown",
            "error": None,
            "warnings": []
        }
        
        try:
            # 安全检查：文件大小
            file_size = file_path.stat().st_size
            result["file_size"] = file_size
            
            if file_size == 0:
                result["status"] = "empty"
                return result
                
            if file_size > self.max_file_size:
                result["warnings"].append(f"文件过大({file_size}字节)，跳过检测")
                result["status"] = "skipped_oversized"
                return result
            
            # 安全检查：路径验证
            try:
                relative_path = file_path.relative_to(self.project_root)
            except ValueError:
                result["warnings"].append("文件不在项目根目录内")
                result["status"] = "skipped_path_invalid"
                return result
            
            # 检查BOM头（只读）
            try:
                with open(file_path, 'rb') as f:
                    first_bytes = f.read(4)
                    
                if first_bytes.startswith(b'\xef\xbb\xbf'):
                    result["has_bom"] = True
                    result["encoding"] = "utf-8-sig"
                    result["confidence"] = 1.0
            except Exception as e:
                result["warnings"].append(f"BOM检测失败: {e}")
            
            # 使用chardet检测（限制读取大小）
            try:
                read_size = min(self.max_read_size, file_size)
                with open(file_path, 'rb') as f:
                    raw_data = f.read(read_size)
                
                detection = chardet.detect(raw_data)
                if detection:
                    result["encoding"] = detection.get('encoding', 'unknown') or 'unknown'
                    result["confidence"] = detection.get('confidence', 0.0) or 0.0
            except Exception as e:
                result["warnings"].append(f"编码检测失败: {e}")
            
            # 验证UTF-8兼容性（保守检测）
            try:
                read_size = min(self.max_read_size, file_size)
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(read_size)
                result["utf8_compatible"] = True
                if result["encoding"] == "unknown":
                    result["encoding"] = "utf-8"
                    result["confidence"] = 1.0
            except UnicodeDecodeError:
                result["utf8_compatible"] = False
            except Exception as e:
                result["warnings"].append(f"UTF-8验证失败: {e}")
            
            # 确定状态
            if result["encoding"] == "utf-8" and not result["has_bom"] and result.get("utf8_compatible", False):
                result["status"] = "optimal"
            elif result["encoding"] in ["utf-8", "utf-8-sig"]:
                result["status"] = "acceptable"
            elif result["confidence"] > 0.8:
                result["status"] = "detected"
            else:
                result["status"] = "uncertain"
                
        except FileNotFoundError:
            result["error"] = "文件不存在"
            result["status"] = "error"
        except PermissionError:
            result["error"] = "权限不足，无法读取文件"
            result["status"] = "error"
        except Exception as e:
            result["error"] = f"检测异常: {str(e)}"
            result["status"] = "error"
        
        return result
    
    def safe_scan_project(self, target_path: str = None) -> Dict:
        """安全扫描项目编码状况"""
        if target_path:
            scan_path = Path(target_path)
            if not scan_path.is_absolute():
                scan_path = self.project_root / scan_path
        else:
            scan_path = self.project_root
        
        # 安全检查：确保扫描路径有效
        try:
            scan_path = scan_path.resolve()
            if not scan_path.exists():
                raise ValueError(f"扫描路径不存在: {scan_path}")
        except Exception as e:
            raise ValueError(f"扫描路径无效: {e}")
        
        # 确保扫描路径在项目根目录下
        try:
            relative_path = scan_path.relative_to(self.project_root)
            scan_path_display = str(relative_path)
        except ValueError:
            # 如果扫描路径不在项目根目录下，使用绝对路径但添加警告
            scan_path_display = str(scan_path)
            print(f"⚠️  警告: 扫描路径在项目根目录外: {scan_path_display}")
        
        results = {
            "scan_time": datetime.now().isoformat(),
            "scan_path": scan_path_display,
            "total_files": 0,
            "analyzed_files": 0,
            "skipped_files": 0,
            "encoding_stats": {
                "optimal": 0,      # UTF-8无BOM
                "acceptable": 0,   # UTF-8有BOM或其他可接受编码
                "detected": 0,     # 高置信度检测到编码
                "uncertain": 0,    # 低置信度检测
                "error": 0,        # 读取错误
                "empty": 0,        # 空文件
                "skipped_oversized": 0,  # 跳过的大文件
                "skipped_path_invalid": 0  # 跳过路径无效文件
            },
            "encoding_types": {},
            "files_with_issues": [],
            "skipped_files_list": [],
            "detailed_results": [],
            "safety_summary": {
                "max_file_size_mb": self.max_file_size / (1024 * 1024),
                "total_warnings": 0,
                "security_notes": []
            }
        }
        
        print(f"🔍 开始安全扫描编码状况: {scan_path}")
        print(f"   文件大小限制: {self.max_file_size / (1024 * 1024)}MB")
        
        try:
            for file_path in scan_path.rglob("*"):
                if not file_path.is_file():
                    continue
                    
                # 跳过排除目录
                try:
                    if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                        continue
                except Exception:
                    continue  # 路径解析错误，跳过
                
                # 检查文件扩展名
                if file_path.suffix.lower() not in self.supported_extensions:
                    continue
                
                results["total_files"] += 1
                
                # 安全检测文件编码
                file_result = self.safe_detect_encoding(file_path)
                results["detailed_results"].append(file_result)
                
                # 统计跳过的文件
                if file_result["status"].startswith("skipped_"):
                    results["skipped_files"] += 1
                    results["skipped_files_list"].append(file_result["file"])
                
                # 统计编码状态
                status = file_result["status"]
                if status in results["encoding_stats"]:
                    results["encoding_stats"][status] += 1
                
                # 统计警告数量
                if file_result.get("warnings"):
                    results["safety_summary"]["total_warnings"] += len(file_result["warnings"])
                
                # 统计编码类型
                encoding = file_result["encoding"]
                if encoding not in results["encoding_types"]:
                    results["encoding_types"][encoding] = 0
                results["encoding_types"][encoding] += 1
                
                # 记录有问题的文件
                if status in ["uncertain", "error"] or file_result.get("has_bom"):
                    results["files_with_issues"].append(file_result)
                
                if results["total_files"] % 100 == 0:
                    print(f"   已分析 {results['total_files']} 个文件，跳过 {results['skipped_files']} 个...")
        
        except KeyboardInterrupt:
            print(f"\n⚠️  扫描被用户中断")
            results["safety_summary"]["security_notes"].append("扫描过程被用户中断")
        except Exception as e:
            print(f"\n🚨 扫描过程发生错误: {e}")
            results["safety_summary"]["security_notes"].append(f"扫描异常: {str(e)}")
        
        results["analyzed_files"] = len([r for r in results["detailed_results"] if not r["status"].startswith("skipped_") and r["status"] != "empty"])
        
        # 安全总结
        if results["skipped_files"] > 0:
            results["safety_summary"]["security_notes"].append(f"跳过了 {results['skipped_files']} 个大文件或路径无效文件")
        
        if results["safety_summary"]["total_warnings"] > 0:
            results["safety_summary"]["security_notes"].append(f"检测到 {results['safety_summary']['total_warnings']} 个警告")
        
        return results
    
    def safe_generate_report(self, results: Dict) -> Tuple[str, str, str]:
        """安全生成分析报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 确保报告目录存在（安全创建）
            self.report_dir.mkdir(parents=True, exist_ok=True)
            self.result_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"无法创建报告目录: {e}")
        
        # 生成文本报告
        report_lines = [
            f"# YDS-Lab 自动编码监测报告（安全加固版）",
            f"> 生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
            f"> 扫描路径: {results['scan_path']}",
            f"> 监测工具: enco.py v2.0（安全版）",
            f"> 文件大小限制: {results['safety_summary']['max_file_size_mb']}MB",
            "",
            "## 🔒 安全摘要",
            "",
            f"- **总文件数**: {results['total_files']}",
            f"- **已分析文件**: {results['analyzed_files']}",
            f"- **跳过文件**: {results['skipped_files']}",
            f"- **总警告数**: {results['safety_summary']['total_warnings']}",
        ]
        
        # 安全注意事项
        if results["safety_summary"]["security_notes"]:
            report_lines.extend([
                "",
                "## ⚠️ 安全注意事项",
                ""
            ])
            for note in results["safety_summary"]["security_notes"]:
                report_lines.append(f"- {note}")
        
        # 编码统计
        report_lines.extend([
            "",
            "## 📊 编码统计",
            "",
            f"- **UTF-8无BOM (最优)**: {results['encoding_stats']['optimal']}",
            f"- **UTF-8可接受**: {results['encoding_stats']['acceptable']}",
            f"- **高置信度检测**: {results['encoding_stats']['detected']}",
            f"- **低置信度检测**: {results['encoding_stats']['uncertain']}",
            f"- **读取错误**: {results['encoding_stats']['error']}",
            f"- **空文件**: {results['encoding_stats']['empty']}",
            f"- **跳过的大文件**: {results['encoding_stats']['skipped_oversized']}",
            f"- **跳过路径无效**: {results['encoding_stats']['skipped_path_invalid']}",
            "",
            "## 🎯 编码类型分布",
            ""
        ])
        
        for encoding, count in sorted(results["encoding_types"].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / max(results["total_files"], 1)) * 100
            report_lines.append(f"- **{encoding}**: {count} ({percentage:.1f}%)")
        
        # 跳过文件列表
        if results["skipped_files_list"]:
            report_lines.extend([
                "",
                "## 📋 跳过文件列表（大文件或路径问题）",
                ""
            ])
            for skipped_file in results["skipped_files_list"][:10]:  # 只显示前10个
                report_lines.append(f"- {skipped_file}")
            if len(results["skipped_files_list"]) > 10:
                report_lines.append(f"*... 还有 {len(results['skipped_files_list']) - 10} 个被跳过的文件*")
        
        # 问题文件详情
        if results["files_with_issues"]:
            report_lines.extend([
                "",
                "## ⚠️ 问题文件详情",
                ""
            ])
            
            for issue in results["files_with_issues"][:15]:  # 只显示前15个
                status_icon = "🚨" if issue["status"] == "error" else "⚠️"
                report_lines.append(f"{status_icon} **{issue['file']}**")
                report_lines.append(f"   - 编码: {issue['encoding']} (置信度: {issue['confidence']:.2f})")
                if issue.get("has_bom"):
                    report_lines.append(f"   - 问题: 包含UTF-8 BOM头")
                if issue.get("file_size"):
                    size_kb = issue["file_size"] / 1024
                    report_lines.append(f"   - 文件大小: {size_kb:.1f}KB")
                if issue.get("warnings"):
                    for warning in issue["warnings"]:
                        report_lines.append(f"   - 警告: {warning}")
                if issue.get("error"):
                    report_lines.append(f"   - 错误: {issue['error']}")
                report_lines.append("")
            
            if len(results["files_with_issues"]) > 15:
                report_lines.append(f"*... 还有 {len(results['files_with_issues']) - 15} 个问题文件*")
        
        # 合规性评估
        analyzed_files = results["analyzed_files"]
        if analyzed_files > 0:
            optimal_rate = (results["encoding_stats"]["optimal"] / analyzed_files) * 100
            acceptable_rate = ((results["encoding_stats"]["optimal"] + results["encoding_stats"]["acceptable"]) / analyzed_files) * 100
        else:
            optimal_rate = acceptable_rate = 0
        
        compliance_level = "🟢 优秀" if optimal_rate > 90 else "🟡 良好" if acceptable_rate > 85 else "🟠 一般" if acceptable_rate > 70 else "🔴 需改进"
        
        report_lines.extend([
            "",
            "## 📊 合规性评估",
            "",
            f"- **UTF-8无BOM比例**: {optimal_rate:.1f}%",
            f"- **可接受编码比例**: {acceptable_rate:.1f}%",
            f"- **合规等级**: {compliance_level}",
            "",
            "## 💡 改进建议",
            ""
        ])
        
        if optimal_rate < 90 and analyzed_files > 0:
            report_lines.append("- 建议将更多文件转换为UTF-8无BOM编码")
        
        if results["encoding_stats"]["uncertain"] > 0:
            report_lines.append("- 存在低置信度编码检测，建议手动检查这些文件")
        
        if any(r.get("has_bom") for r in results["files_with_issues"]):
            report_lines.append("- 建议移除UTF-8 BOM头以提高兼容性")
        
        if results["skipped_files"] > 0:
            report_lines.append(f"- 有 {results['skipped_files']} 个大文件被跳过，建议单独检查")
        
        report_lines.extend([
            "",
            "---",
            f"*报告由 enco.py v2.0（安全加固版）自动生成 - YDS-Lab 自动编码监测工具*",
            "*本工具采用只读检测，确保文件安全*"
        ])
        
        report_content = "\n".join(report_lines)
        
        # 安全保存报告文件
        try:
            report_file = self.report_dir / f"encoding_report_{timestamp}.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # 验证报告文件写入成功
            if not report_file.exists():
                raise RuntimeError("报告文件创建失败")
            
        except Exception as e:
            raise RuntimeError(f"无法保存报告文件: {e}")
        
        # 安全保存详细结果
        try:
            result_file = self.result_dir / f"encoding_analysis_{timestamp}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 验证结果文件写入成功
            if not result_file.exists():
                raise RuntimeError("结果文件创建失败")
                
        except Exception as e:
            raise RuntimeError(f"无法保存结果文件: {e}")
        
        return report_content, str(report_file), str(result_file)
    
    def main(self, target_path: str = None):
        """主函数（安全版）"""
        print("🚀 YDS-Lab 自动编码监测工具 (enco.py v2.0 - 安全加固版)")
        print("=" * 60)
        print("🔒 安全特性:")
        print("   ✓ 只读文件检测，无修改风险")
        print("   ✓ 文件大小限制: 10MB")
        print("   ✓ 完整异常处理")
        print("   ✓ 路径验证")
        print("=" * 60)
        
        try:
            # 执行安全扫描
            results = self.safe_scan_project(target_path)
            
            # 生成安全报告
            report_content, report_file, result_file = self.safe_generate_report(results)
            
            # 输出安全摘要
            print(f"\n📊 安全扫描完成！")
            print(f"   总文件数: {results['total_files']}")
            print(f"   已分析: {results['analyzed_files']}")
            print(f"   跳过文件: {results['skipped_files']}")
            print(f"   UTF-8无BOM: {results['encoding_stats']['optimal']}")
            print(f"   问题文件: {len(results['files_with_issues'])}")
            print(f"   总警告: {results['safety_summary']['total_warnings']}")
            
            if results["skipped_files"] > 0:
                print(f"   ⚠️  跳过了 {results['skipped_files']} 个大文件")
            
            if results["analyzed_files"] > 0:
                compliance_rate = ((results["encoding_stats"]["optimal"] + results["encoding_stats"]["acceptable"]) / results["analyzed_files"]) * 100
                print(f"   合规率: {compliance_rate:.1f}%")
            else:
                print(f"   合规率: 0% (无文件被分析)")
            
            print(f"\n📄 报告文件: {report_file}")
            print(f"📊 结果文件: {result_file}")
            
            # 安全状态评估
            if results["safety_summary"]["total_warnings"] > 0:
                print(f"\n⚠️  检测到 {results['safety_summary']['total_warnings']} 个安全警告")
            
            # 如果有严重问题，返回错误码
            if len(results["files_with_issues"]) > 0 and results["analyzed_files"] > 0:
                compliance_rate = ((results["encoding_stats"]["optimal"] + results["encoding_stats"]["acceptable"]) / results["analyzed_files"]) * 100
                if compliance_rate < 80:
                    print(f"\n🚨 发现编码问题，建议及时处理！")
                    return 1
            
            print(f"\n✅ 安全编码监测完成！")
            return 0
            
        except KeyboardInterrupt:
            print(f"\n⚠️  操作被用户中断")
            return 130  # SIGINT
        except Exception as e:
            print(f"\n🚨 安全扫描失败: {e}")
            return 2

def main():
    """命令行入口（安全版）"""
    if len(sys.argv) > 1 and sys.argv[1] not in ['--help', '-h']:
        target_path = sys.argv[1]
    else:
        if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
            print("""
YDS-Lab 自动编码监测工具 (enco.py v2.0 - 安全加固版)

🔒 安全特性：
   ✓ 只读文件检测，无文件修改风险
   ✓ 文件大小限制：10MB
   ✓ 完整异常处理和错误恢复
   ✓ 路径验证和安全检查
   ✓ 保守编码检测算法

使用方法:
    python enco.py [路径]
    
参数:
    路径 - 可选，要扫描的目录路径，默认为当前目录
    
示例:
    python enco.py                    # 扫描当前目录
    python enco.py 03-dev              # 扫描03-dev目录
    python enco.py .                   # 扫描当前目录
    
输出:
    - 编码统计摘要
    - 安全警告和注意事项
    - 问题文件列表
    - 详细分析报告 (logs/encoding_reports/)
    - 分析结果数据 (rep/encoding_analysis/)

返回码:
    0 - 编码状况良好
    1 - 发现编码问题需要处理
    2 - 扫描过程发生错误
  130 - 操作被中断
            """)
            return 0
        target_path = None
    
    try:
        monitor = AutoEncodingMonitor()
        return monitor.main(target_path)
    except Exception as e:
        print(f"🚨 初始化失败: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())