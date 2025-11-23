#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enc.py - 编码分析工具 (安全版本)
只读分析，绝不修改文件
"""

import os
import sys
import json
import chardet
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

def safe_detect_encoding(file_path: Path, max_size: int = 10*1024*1024) -> Dict:
    """安全检测文件编码 - 只读操作"""
    result = {
        "file": str(file_path),
        "file_size": 0,
        "encoding": "unknown",
        "confidence": 0.0,
        "has_bom": False,
        "is_utf8": False,
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
            
        if file_size > max_size:
            result["warnings"].append(f"文件过大({file_size}字节)，跳过检测")
            result["status"] = "skipped_oversized"
            return result
        
        # 只读打开文件
        with open(file_path, 'rb') as f:
            # 检查BOM头
            first_bytes = f.read(4)
            if first_bytes.startswith(b'\xef\xbb\xbf'):
                result["has_bom"] = True
                result["warnings"].append("检测到UTF-8 BOM头")
            
            # 重置文件指针
            f.seek(0)
            
            # 读取适量内容进行检测 (最多100KB)
            sample_size = min(file_size, 100 * 1024)
            raw_data = f.read(sample_size)
        
        # 使用chardet检测
        detection = chardet.detect(raw_data)
        if detection:
            result["encoding"] = detection.get('encoding', 'unknown') or 'unknown'
            result["confidence"] = detection.get('confidence', 0.0) or 0.0
        
        # 验证UTF-8兼容性（只验证，不修改）
        try:
            # 读取整个文件验证UTF-8（但限制大小）
            if file_size <= 1024 * 1024:  # 1MB以下文件完整验证
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read()
            else:
                # 大文件抽样验证
                with open(file_path, 'r', encoding='utf-8') as f:
                    chunk_size = 8192
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
            result["is_utf8"] = True
            if result["encoding"] == "unknown":
                result["encoding"] = "utf-8"
                result["confidence"] = 1.0
        except UnicodeDecodeError:
            result["is_utf8"] = False
        
        # 确定状态 - 保守判断
        if result["encoding"] == "utf-8" and not result["has_bom"] and result["is_utf8"]:
            result["status"] = "optimal"
        elif result["encoding"] in ["utf-8", "utf-8-sig"]:
            result["status"] = "acceptable"
        elif result["confidence"] > 0.8:
            result["status"] = "detected"
        elif result["confidence"] > 0.5:
            result["status"] = "uncertain"
        else:
            result["status"] = "unknown"
            result["warnings"].append("编码检测置信度低")
            
    except PermissionError:
        result["error"] = "没有文件读取权限"
        result["status"] = "error"
    except FileNotFoundError:
        result["error"] = "文件不存在"
        result["status"] = "error"
    except Exception as e:
        result["error"] = f"检测异常: {str(e)}"
        result["status"] = "error"
    
    return result

def safe_analyze_directory(directory_path: Path, 
                         supported_extensions: Optional[set] = None,
                         exclude_dirs: Optional[set] = None,
                         max_file_size: int = 10*1024*1024) -> Dict:
    """安全分析目录编码状况"""
    
    if supported_extensions is None:
        supported_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.vue', '.json', '.yml', '.yaml',
            '.md', '.txt', '.sh', '.bash', '.bat', '.cmd', '.css', '.html', '.htm',
            '.xml', '.ini', '.cfg', '.conf', '.properties', '.java', '.cpp', '.c',
            '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
            '.dockerfile', '.gitignore', '.env'
        }
    
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', 'node_modules', '.vscode', '.idea', 'bak'}
    
    results = {
        "scan_time": None,
        "directory": str(directory_path),
        "total_files": 0,
        "analyzed_files": 0,
        "encoding_stats": {
            "optimal": 0,        # UTF-8无BOM且兼容
            "acceptable": 0,     # UTF-8有BOM
            "detected": 0,       # 高置信度检测
            "uncertain": 0,      # 低置信度检测
            "unknown": 0,        # 未知编码
            "empty": 0,          # 空文件
            "skipped_oversized": 0,  # 过大跳过
            "error": 0           # 检测错误
        },
        "encoding_types": {},
        "problem_files": [],      # 需要关注的文件
        "errors": [],             # 检测错误详情
        "summary": {}
    }
    
    try:
        if not directory_path.exists():
            results["errors"].append(f"目录不存在: {directory_path}")
            return results
            
        if not directory_path.is_dir():
            results["errors"].append(f"路径不是目录: {directory_path}")
            return results
        
        start_time = datetime.now()
        
        for file_path in directory_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # 跳过排除目录
            if any(excluded in file_path.parts for excluded in exclude_dirs):
                continue
            
            # 检查文件扩展名
            if file_path.suffix.lower() not in supported_extensions:
                continue
            
            results["total_files"] += 1
            
            # 安全检测文件编码
            file_result = safe_detect_encoding(file_path, max_file_size)
            
            if file_result["status"] not in ["empty", "skipped_oversized"]:
                results["analyzed_files"] += 1
            
            # 统计编码状态
            status = file_result["status"]
            if status in results["encoding_stats"]:
                results["encoding_stats"][status] += 1
            
            # 统计编码类型
            encoding = file_result["encoding"]
            if encoding not in results["encoding_types"]:
                results["encoding_types"][encoding] = 0
            results["encoding_types"][encoding] += 1
            
            # 记录问题文件（保守判断）
            if (status in ["uncertain", "unknown", "error"] or 
                not file_result["is_utf8"] or 
                file_result["has_bom"]):
                problem_info = {
                    "file": str(file_path.relative_to(directory_path)),
                    "status": status,
                    "encoding": encoding,
                    "confidence": file_result["confidence"],
                    "is_utf8": file_result["is_utf8"],
                    "has_bom": file_result["has_bom"],
                    "warnings": file_result["warnings"],
                    "error": file_result["error"]
                }
                results["problem_files"].append(problem_info)
            
            # 记录错误
            if file_result["error"]:
                results["errors"].append({
                    "file": str(file_path),
                    "error": file_result["error"]
                })
            
            # 进度显示
            if results["total_files"] % 50 == 0:
                print(f"   已分析 {results['total_files']} 个文件...")
        
        # 生成摘要
        scan_time = datetime.now() - start_time
        results["scan_time"] = str(scan_time)
        
        total_analyzed = results["analyzed_files"]
        optimal_rate = (results["encoding_stats"]["optimal"] / max(total_analyzed, 1)) * 100
        problem_rate = (len(results["problem_files"]) / max(results["total_files"], 1)) * 100
        
        results["summary"] = {
            "scan_duration": str(scan_time),
            "total_files": results["total_files"],
            "analyzed_files": total_analyzed,
            "optimal_rate_percent": round(optimal_rate, 1),
            "problem_files_count": len(results["problem_files"]),
            "problem_rate_percent": round(problem_rate, 1),
            "errors_count": len(results["errors"]),
            "overall_health": "优秀" if optimal_rate > 90 else "良好" if optimal_rate > 80 else "一般" if optimal_rate > 60 else "需改进"
        }
        
    except Exception as e:
        results["errors"].append({
            "file": "扫描过程",
            "error": f"扫描异常: {str(e)}"
        })
        # 异常时也要确保有基本的summary
        if "summary" not in results:
            results["summary"] = {
                "scan_duration": "0:00:00",
                "total_files": results.get("total_files", 0),
                "analyzed_files": results.get("analyzed_files", 0),
                "optimal_rate_percent": 0.0,
                "problem_files_count": len(results.get("problem_files", [])),
                "problem_rate_percent": 0.0,
                "errors_count": len(results.get("errors", [])),
                "overall_health": "异常"
            }
    
    return results

def main():
    """主函数 - 安全第一"""
    try:
        # 参数处理
        if len(sys.argv) > 2:
            print("❌ 参数过多，使用方法: python enc.py [目录路径]")
            return 1
        
        if len(sys.argv) == 2:
            target_path = Path(sys.argv[1])
        else:
            target_path = Path.cwd()
        
        # 验证目标路径
        if not target_path.exists():
            print(f"❌ 路径不存在: {target_path}")
            return 1
        
        if not target_path.is_dir():
            print(f"❌ 路径不是目录: {target_path}")
            return 1
        
        # 安全检查：确保在合理范围内
        try:
            # 确保路径在项目目录内，防止扫描系统目录
            project_root = Path.cwd()
            target_path.relative_to(project_root)
        except ValueError:
            print(f"⚠️  警告: 扫描路径在项目目录外: {target_path}")
            response = input("是否继续扫描? (y/N): ")
            if response.lower() != 'y':
                return 0
        
        print("🔍 YDS-Lab 安全编码分析工具 (enc.py)")
        print("=" * 50)
        print(f"📁 扫描目录: {target_path}")
        print("⚠️  本工具为只读分析，不会修改任何文件")
        print("=" * 50)
        
        # 执行安全扫描
        results = safe_analyze_directory(target_path)
        
        # 输出结果
        # 确保有summary数据
        if "summary" not in results:
            print(f"\n❌ 扫描失败: 无法生成分析结果")
            return 1
        
        print(f"\n📊 扫描完成 ({results['summary'].get('scan_duration', '0:00:00')})")
        print(f"   总文件数: {results.get('total_files', 0)}")
        print(f"   已分析: {results.get('analyzed_files', 0)}")
        print(f"   UTF-8最优: {results.get('encoding_stats', {}).get('optimal', 0)}")
        print(f"   问题文件: {results['summary'].get('problem_files_count', 0)}")
        print(f"   错误数: {results['summary'].get('errors_count', 0)}")
        print(f"   健康状态: {results['summary'].get('overall_health', '异常')}")
        
        # 显示问题文件（最多10个）
        if results["problem_files"]:
            print(f"\n⚠️  发现 {len(results['problem_files'])} 个问题文件:")
            for problem in results["problem_files"][:10]:
                status_icon = "🚨" if problem["status"] == "error" else "⚠️"
                print(f"   {status_icon} {problem['file']}")
                if problem["error"]:
                    print(f"      错误: {problem['error']}")
                elif problem["warnings"]:
                    print(f"      警告: {'; '.join(problem['warnings'])}")
                else:
                    print(f"      状态: {problem['status']} (编码: {problem['encoding']})")
            
            if len(results["problem_files"]) > 10:
                print(f"   ... 还有 {len(results['problem_files']) - 10} 个问题文件")
        
        # 显示错误详情
        if results["errors"]:
            print(f"\n❌ 检测错误 ({len(results['errors'])}个):")
            for error in results["errors"][:5]:
                print(f"   📄 {error['file']}")
                print(f"      ❌ {error['error']}")
            
            if len(results["errors"]) > 5:
                print(f"   ... 还有 {len(results['errors']) - 5} 个错误")
        
        # 编码类型分布
        if results["encoding_types"]:
            print(f"\n🎯 编码类型分布:")
            for encoding, count in sorted(results["encoding_types"].items(), key=lambda x: x[1], reverse=True)[:5]:
                percentage = (count / max(results["analyzed_files"], 1)) * 100
                print(f"   {encoding}: {count} ({percentage:.1f}%)")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = Path.cwd() / "rep" / "encoding_analysis"
        out_dir.mkdir(parents=True, exist_ok=True)
        result_path = out_dir / f"encoding_safe_analysis_{timestamp}.json"
        
        try:
            with open(result_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 分析结果已保存: {result_path}")
        except Exception as e:
            print(f"\n⚠️  保存结果失败: {e}")
        
        # 返回码：0=成功，1=发现严重问题
        if results.get("summary", {}).get("overall_health", "异常") in ["需改进"] or results.get("summary", {}).get("errors_count", 0) > 0:
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        return 130
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
