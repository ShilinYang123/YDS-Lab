#!/usr/bin/env python3
"""
数字员工项目 - 简化HTTP服务器
绕过依赖问题，提供基础API功能
"""

import http.server
import socketserver
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

class DigitalEmployeeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_homepage()
        elif path == '/health':
            self.serve_health()
        elif path == '/api/tasks':
            self.serve_tasks()
        elif path == '/api/stats':
            self.serve_stats()
        else:
            self.serve_404()
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/upload':
            self.handle_upload()
        elif path == '/api/tasks':
            self.handle_create_task()
        else:
            self.serve_404()
    
    def serve_homepage(self):
        """服务主页"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>数字员工项目 - API服务器</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .method { color: #007acc; font-weight: bold; }
                .path { color: #28a745; font-weight: bold; }
                .status { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 数字员工项目 API服务器</h1>
                <p>服务器运行正常！以下是可用的API端点：</p>
                
                <div class="endpoint">
                    <span class="method">GET</span> 
                    <span class="path">/health</span> - 
                    <span class="status">健康检查</span>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> 
                    <span class="path">/api/tasks</span> - 
                    <span class="status">获取任务列表</span>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> 
                    <span class="path">/api/stats</span> - 
                    <span class="status">获取统计信息</span>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> 
                    <span class="path">/api/upload</span> - 
                    <span class="status">文件上传</span>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> 
                    <span class="path">/api/tasks</span> - 
                    <span class="status">创建新任务</span>
                </div>
                
                <h2>📊 服务器信息</h2>
                <ul>
                    <li>服务器时间: {time}</li>
                    <li>Python版本: {python_version}</li>
                    <li>工作目录: {work_dir}</li>
                    <li>服务器端口: {port}</li>
                </ul>
                
                <h2>🎯 快速测试</h2>
                <p>您可以使用以下命令测试API：</p>
                <pre>
# 健康检查
curl http://localhost:8000/health

# 获取任务列表
curl http://localhost:8000/api/tasks

# 获取统计信息
curl http://localhost:8000/api/stats
                </pre>
                
                <p style="margin-top: 30px; color: #666;">
                    💡 提示：此服务器绕过了复杂的依赖问题，提供基础的API功能用于测试。
                </p>
            </div>
        </body>
        </html>
        """.format(
            time=time.strftime("%Y-%m-%d %H:%M:%S"),
            python_version=f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            work_dir=os.getcwd(),
            port=8000
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_health(self):
        """健康检查"""
        health_data = {
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "service": "digital-employee-api",
            "version": "1.0.0",
            "uptime": time.time()
        }
        
        self.send_json_response(health_data)
    
    def serve_tasks(self):
        """获取任务列表"""
        tasks = [
            {
                "id": 1,
                "name": "示例任务1",
                "status": "completed",
                "created_at": "2024-01-01 10:00:00",
                "progress": 100
            },
            {
                "id": 2,
                "name": "示例任务2", 
                "status": "processing",
                "created_at": "2024-01-01 11:00:00",
                "progress": 75
            },
            {
                "id": 3,
                "name": "示例任务3",
                "status": "pending",
                "created_at": "2024-01-01 12:00:00",
                "progress": 0
            }
        ]
        
        self.send_json_response({"tasks": tasks, "total": len(tasks)})
    
    def serve_stats(self):
        """获取统计信息"""
        stats = {
            "total_tasks": 3,
            "completed_tasks": 1,
            "processing_tasks": 1,
            "pending_tasks": 1,
            "total_files": 5,
            "total_size": "125.6 MB",
            "server_uptime": "2小时15分钟"
        }
        
        self.send_json_response(stats)
    
    def handle_upload(self):
        """处理文件上传"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length > 100 * 1024 * 1024:  # 100MB限制
                self.send_error_response(413, "文件太大")
                return
            
            # 模拟文件处理
            upload_info = {
                "status": "success",
                "message": "文件上传成功",
                "file_size": content_length,
                "upload_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.send_json_response(upload_info)
            
        except Exception as e:
            self.send_error_response(500, f"上传失败: {str(e)}")
    
    def handle_create_task(self):
        """创建新任务"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                task_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_error_response(400, "无效的JSON数据")
                return
            
            # 模拟任务创建
            new_task = {
                "id": 4,
                "name": task_data.get("name", "新任务"),
                "status": "pending",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "progress": 0,
                "message": "任务创建成功"
            }
            
            self.send_json_response(new_task, status=201)
            
        except Exception as e:
            self.send_error_response(500, f"任务创建失败: {str(e)}")
    
    def serve_404(self):
        """404错误"""
        self.send_error_response(404, "页面不存在")
    
    def send_json_response(self, data, status=200):
        """发送JSON响应"""
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_error_response(self, status, message):
        """发送错误响应"""
        error_data = {
            "error": message,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.send_json_response(error_data, status)
    
    def log_message(self, format, *args):
        """重写日志方法"""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def main():
    """主函数"""
    PORT = 8000
    
    print("="*60)
    print("🚀 数字员工项目 - 简化API服务器")
    print("="*60)
    print(f"📡 服务器端口: {PORT}")
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🕐 启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print("🔗 API端点:")
    print(f"   主页:     http://localhost:{PORT}/")
    print(f"   健康检查: http://localhost:{PORT}/health")
    print(f"   任务列表: http://localhost:{PORT}/api/tasks")
    print(f"   统计信息: http://localhost:{PORT}/api/stats")
    print("="*60)
    print("✅ 服务器启动成功！按 Ctrl+C 停止")
    print("="*60)
    
    try:
        with socketserver.TCPServer(("", PORT), DigitalEmployeeHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器正在停止...")
        print("✅ 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器错误: {e}")

if __name__ == "__main__":
    main()