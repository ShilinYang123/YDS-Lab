#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown转PDF工具
高效办公助手系统 - Markdown文档转PDF工具
作者：杨世林 雨俊 3AI工作室
日期：2025-10-12
"""

import os
import sys
import time
import subprocess
from pathlib import Path
import markdown
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarkdownToPDFConverter:
    """Markdown转PDF转换器类"""
    
    def __init__(self):
        self.name = "Markdown转PDF工具"
        self.version = "1.0.0"
        
    def convert_markdown_to_html(self, markdown_file: str, output_html: str = None) -> dict:
        """
        将Markdown文件转换为HTML
        
        Args:
            markdown_file: Markdown文件路径
            output_html: 输出HTML文件路径（可选）
            
        Returns:
            包含操作结果的字典
        """
        try:
            # 检查输入文件
            if not Path(markdown_file).exists():
                return {
                    "status": "error",
                    "message": f"Markdown文件不存在: {markdown_file}"
                }
            
            # 确定输出文件路径
            if output_html is None:
                output_html = str(Path(markdown_file).with_suffix('.html'))
            
            # 读取Markdown文件
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 转换为HTML
            html_content = markdown.markdown(
                markdown_content,
                extensions=['tables', 'fenced_code', 'toc', 'codehilite']
            )
            
            # 添加基本的HTML结构和样式
            full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{Path(markdown_file).stem}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 0;
            padding-left: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
            
            # 写入HTML文件
            with open(output_html, 'w', encoding='utf-8') as f:
                f.write(full_html)
            
            return {
                "status": "success",
                "message": f"HTML文件已生成: {output_html}",
                "input_file": markdown_file,
                "output_file": output_html
            }
            
        except Exception as e:
            logger.error(f"Markdown转HTML失败: {e}")
            return {
                "status": "error",
                "message": f"转换失败: {str(e)}"
            }
    
    def convert_html_to_pdf_chrome(self, html_file: str, output_pdf: str = None) -> dict:
        """
        使用Chrome浏览器的无头模式将HTML转换为PDF
        
        Args:
            html_file: HTML文件路径
            output_pdf: 输出PDF文件路径（可选）
            
        Returns:
            包含操作结果的字典
        """
        try:
            # 检查输入文件
            if not Path(html_file).exists():
                return {
                    "status": "error",
                    "message": f"HTML文件不存在: {html_file}"
                }
            
            # 确定输出文件路径
            if output_pdf is None:
                output_pdf = str(Path(html_file).with_suffix('.pdf'))
            
            # 将路径转换为绝对路径和file://协议
            html_path = Path(html_file).resolve()
            pdf_path = Path(output_pdf).resolve()
            file_url = f"file:///{str(html_path).replace(os.sep, '/')}"
            
            # Chrome命令行参数
            chrome_args = [
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--print-to-pdf=" + str(pdf_path),
                "--print-to-pdf-no-header",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=5000",
                file_url
            ]
            
            # 尝试找到Chrome可执行文件
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
                "chrome",  # 如果在PATH中
                "google-chrome",  # Linux
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # macOS
            ]
            
            chrome_exe = None
            for path in chrome_paths:
                if os.path.exists(path) or path in ["chrome", "google-chrome"]:
                    chrome_exe = path
                    break
            
            if not chrome_exe:
                return {
                    "status": "error",
                    "message": "未找到Chrome浏览器，请确保已安装Chrome"
                }
            
            # 执行Chrome命令
            cmd = [chrome_exe] + chrome_args
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and Path(output_pdf).exists():
                return {
                    "status": "success",
                    "message": f"PDF文件已生成: {output_pdf}",
                    "input_file": html_file,
                    "output_file": output_pdf
                }
            else:
                return {
                    "status": "error",
                    "message": f"PDF生成失败。返回码: {result.returncode}\n错误信息: {result.stderr}"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Chrome执行超时，请检查HTML文件是否过大或复杂"
            }
        except Exception as e:
            logger.error(f"转换失败: {e}")
            return {
                "status": "error",
                "message": f"转换失败: {str(e)}"
            }
    
    def convert_markdown_to_pdf(self, markdown_file: str, output_pdf: str = None, keep_html: bool = False) -> dict:
        """
        将Markdown文件直接转换为PDF
        
        Args:
            markdown_file: Markdown文件路径
            output_pdf: 输出PDF文件路径（可选）
            keep_html: 是否保留中间HTML文件
            
        Returns:
            包含操作结果的字典
        """
        try:
            # 确定输出文件路径
            if output_pdf is None:
                output_pdf = str(Path(markdown_file).with_suffix('.pdf'))
            
            # 生成临时HTML文件
            temp_html = str(Path(markdown_file).with_suffix('.temp.html'))
            
            # 第一步：Markdown转HTML
            html_result = self.convert_markdown_to_html(markdown_file, temp_html)
            if html_result["status"] != "success":
                return html_result
            
            # 第二步：HTML转PDF
            pdf_result = self.convert_html_to_pdf_chrome(temp_html, output_pdf)
            
            # 清理临时HTML文件（如果不需要保留）
            if not keep_html and Path(temp_html).exists():
                try:
                    os.remove(temp_html)
                except Exception as e:
                    logger.warning(f"删除临时HTML文件失败: {e}")
            
            if pdf_result["status"] == "success":
                return {
                    "status": "success",
                    "message": f"PDF文件已生成: {output_pdf}",
                    "input_file": markdown_file,
                    "output_file": output_pdf,
                    "temp_html": temp_html if keep_html else None
                }
            else:
                return pdf_result
                
        except Exception as e:
            logger.error(f"Markdown转PDF失败: {e}")
            return {
                "status": "error",
                "message": f"转换失败: {str(e)}"
            }

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python markdown_to_pdf_converter.py <markdown_file> [output_pdf]")
        print("  python markdown_to_pdf_converter.py <markdown_file> --keep-html")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    output_pdf = None
    keep_html = False
    
    if len(sys.argv) > 2:
        if sys.argv[2] == "--keep-html":
            keep_html = True
        else:
            output_pdf = sys.argv[2]
    
    if len(sys.argv) > 3 and sys.argv[3] == "--keep-html":
        keep_html = True
    
    converter = MarkdownToPDFConverter()
    result = converter.convert_markdown_to_pdf(markdown_file, output_pdf, keep_html)
    
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        if result.get("temp_html"):
            print(f"📄 HTML文件已保留: {result['temp_html']}")
    else:
        print(f"❌ {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    main()