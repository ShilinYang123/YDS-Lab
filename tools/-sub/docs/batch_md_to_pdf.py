#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量Markdown转PDF工具
将指定目录下的Markdown文件批量转换为PDF格式
作者：杨世林 雨俊 3AI工作室
日期：2025-10-12
"""

import os
import sys
import glob
from pathlib import Path
import argparse
import logging
from .markdown_to_pdf_converter import MarkdownToPDFConverter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def batch_convert_md_to_pdf(source_dir, output_dir=None, file_pattern="*.md"):
    """
    批量将指定目录下的Markdown文件转换为PDF
    
    Args:
        source_dir: 源文件目录
        output_dir: 输出目录（可选）
        file_pattern: 文件匹配模式（默认为"*.md"）
        
    Returns:
        转换结果统计信息
    """
    # 确保目录路径格式正确
    source_dir = Path(source_dir)
    
    # 如果未指定输出目录，则使用源目录
    if output_dir is None:
        output_dir = source_dir
    else:
        output_dir = Path(output_dir)
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找所有匹配的Markdown文件
    md_files = list(source_dir.glob(file_pattern))
    
    if not md_files:
        logger.warning(f"在 {source_dir} 中未找到匹配的Markdown文件")
        return {"success": 0, "failed": 0, "total": 0}
    
    logger.info(f"找到 {len(md_files)} 个Markdown文件")
    
    # 初始化转换器
    converter = MarkdownToPDFConverter()
    
    # 统计信息
    stats = {"success": 0, "failed": 0, "total": len(md_files)}
    
    # 批量转换
    for md_file in md_files:
        # 确定输出PDF文件路径
        relative_path = md_file.relative_to(source_dir) if md_file.is_relative_to(source_dir) else md_file.name
        output_pdf = output_dir / relative_path.with_suffix('.pdf')
        
        # 确保输出目录存在
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"正在转换: {md_file} -> {output_pdf}")
        
        # 执行转换
        result = converter.convert_markdown_to_pdf(str(md_file), str(output_pdf))
        
        if result["status"] == "success":
            stats["success"] += 1
            logger.info(f"✅ 转换成功: {output_pdf}")
        else:
            stats["failed"] += 1
            logger.error(f"❌ 转换失败: {md_file} - {result['message']}")
    
    # 打印统计信息
    logger.info(f"转换完成: 成功 {stats['success']}/{stats['total']}, 失败 {stats['failed']}/{stats['total']}")
    
    return stats

def main():
    """
    主函数，处理命令行参数并执行批量转换
    """
    parser = argparse.ArgumentParser(description="批量将Markdown文件转换为PDF")
    parser.add_argument("source_dir", help="源Markdown文件目录")
    parser.add_argument("-o", "--output-dir", help="输出PDF文件目录（默认与源目录相同）")
    parser.add_argument("-p", "--pattern", default="*.md", help="文件匹配模式（默认为'*.md'）")
    
    args = parser.parse_args()
    
    # 执行批量转换
    stats = batch_convert_md_to_pdf(args.source_dir, args.output_dir, args.pattern)
    
    # 根据转换结果设置退出码
    if stats["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

# 便捷函数，用于直接从其他脚本调用
def convert_md_files(source_dir, output_dir=None, file_pattern="*.md"):
    """
    便捷函数，用于从其他脚本调用批量转换功能
    
    Args:
        source_dir: 源文件目录
        output_dir: 输出目录（可选）
        file_pattern: 文件匹配模式（默认为"*.md"）
        
    Returns:
        转换结果统计信息
    """
    return batch_convert_md_to_pdf(source_dir, output_dir, file_pattern)

# 便捷函数，用于转换指定范围的文件
def convert_md_files_range(source_dir, start_file, end_file, output_dir=None):
    """
    转换指定范围内的Markdown文件为PDF
    
    Args:
        source_dir: 源文件目录
        start_file: 起始文件名（包含）
        end_file: 结束文件名（包含）
        output_dir: 输出目录（可选）
        
    Returns:
        转换结果统计信息
    """
    source_dir = Path(source_dir)
    
    # 获取目录中的所有md文件
    all_files = sorted([f for f in source_dir.glob("*.md")])
    
    # 找到起始和结束文件的索引
    start_idx = None
    end_idx = None
    
    for i, file in enumerate(all_files):
        if start_file in str(file) and start_idx is None:
            start_idx = i
        if end_file in str(file):
            end_idx = i
    
    if start_idx is None or end_idx is None:
        logger.error(f"无法找到指定的起始或结束文件")
        return {"success": 0, "failed": 0, "total": 0}
    
    # 获取范围内的文件
    files_to_convert = all_files[start_idx:end_idx+1]
    
    if not files_to_convert:
        logger.warning(f"在指定范围内未找到Markdown文件")
        return {"success": 0, "failed": 0, "total": 0}
    
    logger.info(f"找到 {len(files_to_convert)} 个Markdown文件在指定范围内")
    
    # 初始化转换器和统计信息
    converter = MarkdownToPDFConverter()
    stats = {"success": 0, "failed": 0, "total": len(files_to_convert)}
    
    # 如果未指定输出目录，则使用源目录
    if output_dir is None:
        output_dir = source_dir
    else:
        output_dir = Path(output_dir)
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 批量转换
    for md_file in files_to_convert:
        # 确定输出PDF文件路径
        output_pdf = output_dir / md_file.with_suffix('.pdf').name
        
        logger.info(f"正在转换: {md_file} -> {output_pdf}")
        
        # 执行转换
        result = converter.convert_markdown_to_pdf(str(md_file), str(output_pdf))
        
        if result["status"] == "success":
            stats["success"] += 1
            logger.info(f"✅ 转换成功: {output_pdf}")
        else:
            stats["failed"] += 1
            logger.error(f"❌ 转换失败: {md_file} - {result['message']}")
    
    # 打印统计信息
    logger.info(f"转换完成: 成功 {stats['success']}/{stats['total']}, 失败 {stats['failed']}/{stats['total']}")
    
    return stats

if __name__ == "__main__":
    main()