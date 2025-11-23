#!/usr/bin/env python3
"""
综合测试报告生成器
整合所有测试结果，生成完整的稳定性评估报告
"""

import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Any

class ComprehensiveTestReporter:
    def __init__(self):
        self.test_data = {
            "stability_test": None,
            "compatibility_test": None,
            "memory_test": None,
            "performance_metrics": {},
            "test_environment": {}
        }
        
    def load_test_results(self):
        """加载所有测试结果文件"""
        result_files = {
            "stability": "preview_stability_test_*.txt",
            "compatibility": "browser_compatibility_test_*.txt", 
            "memory": "memory_management_test_*.txt"
        }
        
        for test_type, pattern in result_files.items():
            files = glob.glob(f"tests/{pattern}")
            if files:
                # 获取最新的结果文件
                latest_file = max(files, key=os.path.getctime)
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        self.test_data[f"{test_type}_test"] = f.read()
                except Exception as e:
                    print(f"加载{test_type}测试结果失败: {e}")
                    
    def parse_test_metrics(self, test_content: str) -> Dict[str, Any]:
        """解析测试内容中的指标"""
        metrics = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "score": 0,
            "key_findings": []
        }
        
        lines = test_content.split('\n')
        for line in lines:
            line = line.strip()
            if '总测试步骤:' in line:
                try:
                    metrics["total_tests"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif '通过:' in line and '总测试步骤:' not in line:
                try:
                    metrics["passed"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif '失败:' in line:
                try:
                    metrics["failed"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif '警告:' in line and '内存泄漏' not in line:
                try:
                    metrics["warnings"] = int(line.split(':')[1].strip())
                except:
                    pass
            elif '通过率:' in line or '兼容性评分:' in line or '内存管理评分:' in line:
                try:
                    score_str = line.split(':')[1].strip().replace('%', '')
                    metrics["score"] = float(score_str)
                except:
                    pass
                    
        # 提取关键发现
        for line in lines:
            if ('内存使用:' in line or '响应时间:' in line or 
                '稳定性:' in line or '错误:' in line):
                if len(metrics["key_findings"]) < 5:  # 限制关键发现数量
                    metrics["key_findings"].append(line.strip())
                    
        return metrics
        
    def generate_executive_summary(self) -> str:
        """生成执行摘要"""
        summary = []
        summary.append("执行摘要")
        summary.append("=" * 50)
        
        # 分析各项测试结果
        stability_metrics = self.parse_test_metrics(self.test_data.get("stability_test", ""))
        compatibility_metrics = self.parse_test_metrics(self.test_data.get("compatibility_test", ""))
        memory_metrics = self.parse_test_metrics(self.test_data.get("memory_test", ""))
        
        # 计算综合评分
        scores = []
        if stability_metrics["score"] > 0:
            scores.append(stability_metrics["score"])
        if compatibility_metrics["score"] > 0:
            scores.append(compatibility_metrics["score"])
        if memory_metrics["score"] > 0:
            scores.append(memory_metrics["score"])
            
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # 稳定性等级
        if overall_score >= 95:
            stability_level = "优秀"
            recommendation = "系统运行非常稳定，可以投入生产使用"
        elif overall_score >= 85:
            stability_level = "良好"
            recommendation = "系统基本稳定，建议解决少量问题后使用"
        elif overall_score >= 70:
            stability_level = "一般"
            recommendation = "系统存在稳定性问题，需要优化改进"
        else:
            stability_level = "需改进"
            recommendation = "系统稳定性较差，不建议投入生产使用"
            
        summary.append(f"综合稳定性评分: {overall_score:.1f}%")
        summary.append(f"稳定性等级: {stability_level}")
        summary.append(f"建议: {recommendation}")
        summary.append("")
        
        # 关键指标
        summary.append("关键测试指标:")
        if stability_metrics["total_tests"] > 0:
            summary.append(f"  - 稳定性测试: {stability_metrics['passed']}/{stability_metrics['total_tests']} 通过")
        if compatibility_metrics["total_tests"] > 0:
            summary.append(f"  - 兼容性测试: {compatibility_metrics['passed']}/{compatibility_metrics['total_tests']} 通过")
        if memory_metrics["total_tests"] > 0:
            summary.append(f"  - 内存管理测试: {memory_metrics['passed']}/{memory_metrics['total_tests']} 通过")
            
        return "\n".join(summary)
        
    def generate_detailed_findings(self) -> str:
        """生成详细发现"""
        findings = []
        findings.append("详细发现")
        findings.append("=" * 50)
        
        # 稳定性测试结果
        if self.test_data.get("stability_test"):
            findings.append("\n1. 稳定性测试结果:")
            stability_metrics = self.parse_test_metrics(self.test_data["stability_test"])
            for finding in stability_metrics["key_findings"]:
                findings.append(f"   {finding}")
                
        # 兼容性测试结果
        if self.test_data.get("compatibility_test"):
            findings.append("\n2. 兼容性测试结果:")
            compatibility_metrics = self.parse_test_metrics(self.test_data["compatibility_test"])
            for finding in compatibility_metrics["key_findings"]:
                findings.append(f"   {finding}")
                
        # 内存管理测试结果
        if self.test_data.get("memory_test"):
            findings.append("\n3. 内存管理测试结果:")
            memory_metrics = self.parse_test_metrics(self.test_data["memory_test"])
            for finding in memory_metrics["key_findings"]:
                findings.append(f"   {finding}")
                
        return "\n".join(findings)
        
    def generate_recommendations(self) -> str:
        """生成改进建议"""
        recommendations = []
        recommendations.append("改进建议")
        recommendations.append("=" * 50)
        
        # 基于测试结果生成建议
        stability_metrics = self.parse_test_metrics(self.test_data.get("stability_test", ""))
        compatibility_metrics = self.parse_test_metrics(self.test_data.get("compatibility_test", ""))
        memory_metrics = self.parse_test_metrics(self.test_data.get("memory_test", ""))
        
        recommendations.append("\n1. 稳定性改进建议:")
        if stability_metrics["failed"] > 0:
            recommendations.append("   - 修复失败的稳定性测试用例")
            recommendations.append("   - 检查服务器配置和网络连接")
            recommendations.append("   - 增加系统监控和告警机制")
        else:
            recommendations.append("   - 稳定性表现良好，保持现有配置")
            recommendations.append("   - 建议定期进行稳定性测试")
            
        recommendations.append("\n2. 兼容性改进建议:")
        if compatibility_metrics["warnings"] > 0:
            recommendations.append("   - 处理兼容性警告信息")
            recommendations.append("   - 测试不同浏览器环境下的表现")
            recommendations.append("   - 优化响应头配置")
        else:
            recommendations.append("   - 兼容性表现良好")
            recommendations.append("   - 建议定期更新浏览器支持列表")
            
        recommendations.append("\n3. 内存管理改进建议:")
        if memory_metrics["warnings"] > 0:
            recommendations.append("   - 优化内存使用，检查内存泄漏")
            recommendations.append("   - 增加内存监控和自动清理机制")
            recommendations.append("   - 考虑使用内存池技术")
        else:
            recommendations.append("   - 内存管理表现良好")
            recommendations.append("   - 建议设置内存使用阈值告警")
            
        recommendations.append("\n4. 通用建议:")
        recommendations.append("   - 建立定期测试机制")
        recommendations.append("   - 设置性能监控仪表板")
        recommendations.append("   - 制定应急响应预案")
        recommendations.append("   - 定期更新测试用例和测试方法")
        
        return "\n".join(recommendations)
        
    def generate_complete_report(self) -> str:
        """生成完整测试报告"""
        # 加载测试结果
        self.load_test_results()
        
        report = []
        report.append("前端预览功能全面稳定性测试报告")
        report.append("=" * 80)
        report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"测试项目: 数字员工虚拟环境前端预览功能")
        report.append(f"测试环境: Windows + Node.js + React + Vite")
        report.append("")
        
        # 执行摘要
        report.append(self.generate_executive_summary())
        report.append("")
        
        # 详细发现
        report.append(self.generate_detailed_findings())
        report.append("")
        
        # 改进建议
        report.append(self.generate_recommendations())
        report.append("")
        
        # 原始测试数据附录
        report.append("附录: 原始测试数据")
        report.append("=" * 50)
        
        if self.test_data.get("stability_test"):
            report.append("\nA. 稳定性测试详细结果:")
            report.append(self.test_data["stability_test"])
            
        if self.test_data.get("compatibility_test"):
            report.append("\nB. 兼容性测试详细结果:")
            report.append(self.test_data["compatibility_test"])
            
        if self.test_data.get("memory_test"):
            report.append("\nC. 内存管理测试详细结果:")
            report.append(self.test_data["memory_test"])
            
        report.append("\n" + "=" * 80)
        report.append("报告生成完成")
        
        return "\n".join(report)
        
    def save_report(self, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            filename = f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
        report_content = self.generate_complete_report()
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"综合测试报告已保存到: {filename}")
            return filename
        except Exception as e:
            print(f"保存报告失败: {e}")
            return None

if __name__ == "__main__":
    reporter = ComprehensiveTestReporter()
    
    # 等待所有测试完成
    print("正在等待测试完成...")
    time.sleep(5)  # 给测试一些时间完成
    
    # 生成并保存报告
    report_file = reporter.save_report()
    
    if report_file:
        print("\n" + "=" * 60)
        print("综合测试报告生成完成!")
        print("=" * 60)
        
        # 显示执行摘要
        print("\n执行摘要:")
        print(reporter.generate_executive_summary())
    else:
        print("报告生成失败，请检查测试状态")