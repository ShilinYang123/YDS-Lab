#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理工具包
高效办公助手系统 - 文档处理和转换工具
作者：杨世林 雨俊 3AI工作室
日期：2025-10-12
"""

__version__ = "1.0.0"
__author__ = "杨世林 雨俊 3AI工作室"
__description__ = "文档处理、转换和批量操作工具"

from .batch_docx_replacer import BatchDocxReplacer
from .batch_md_to_pdf import batch_convert_md_to_pdf
from .markdown_to_pdf_converter import MarkdownToPDFConverter
from .office_document_reader import OfficeDocumentReader

__all__ = [
    "BatchDocxReplacer",
    "batch_convert_md_to_pdf", 
    "MarkdownToPDFConverter",
    "OfficeDocumentReader"
]