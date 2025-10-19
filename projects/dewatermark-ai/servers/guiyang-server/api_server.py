# api_server.py
# 贵阳台式机本地推理服务（ONNX CPU 模式）
# 路径: S:\YDS-Lab\projects\dewatermark-ai\servers\guiyang-server\

import os
import sys
import subprocess
import tempfile
import shutil
from flask import Flask, request, jsonify

# 添加项目根目录到 Python 路径（确保可导入 utils）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import log_to_general_office

app = Flask(__name__)

# 模型与脚本路径（相对项目根目录）
SHIMMY_SCRIPT = os.path.join(project_root, "projects", "dewatermark-ai", "models", "shimmy", "infer.py")
LAMA_MODEL_DIR = os.path.join(project_root, "projects", "dewatermark-ai", "models", "lama")
OUTPUT_DIR = os.path.join(project_root, "projects", "dewatermark-ai", "output")

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "ok", "device": "guiyang-pc", "mode": "local-cpu"})

@app.route("/process", methods=["POST"])
def process_video():
    """
    本地去水印处理接口
    输入: {"input_path": "S:/videos/input.mp4"}
    输出: {"output_path": "S:/YDS-Lab/projects/dewatermark-ai/output/output_20251018123456.mp4"}
    """
    try:
        data = request.get_json()
        input_path = data.get("input_path")
        
        if not input_path or not os.path.exists(input_path):
            return jsonify({"error": "输入文件不存在"}), 400
        
        # 生成唯一输出文件名
        timestamp = os.path.basename(input_path).split(".")[0] + "_processed"
        output_path = os.path.join(OUTPUT_DIR, f"{timestamp}.mp4")
        
        # 调用 Shimmy + LaMa ONNX 推理脚本
        cmd = [
            sys.executable, SHIMMY_SCRIPT,
            "--input", input_path,
            "--output", output_path,
            "--model_dir", LAMA_MODEL_DIR
        ]
        
        log_to_general_office(f"贵阳机启动推理: {input_path} → {output_path}", "operations")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5分钟超时
        
        if result.returncode == 0 and os.path.exists(output_path):
            log_to_general_office(f"✅ 贵阳机处理成功: {output_path}", "operations")
            return jsonify({"output_path": output_path})
        else:
            error_msg = result.stderr or "未知错误"
            log_to_general_office(f"❌ 贵阳机处理失败: {error_msg}", "errors")
            return jsonify({"error": f"处理失败: {error_msg}"}), 500
            
    except Exception as e:
        log_to_general_office(f"⚠️ 贵阳机异常: {str(e)}", "errors")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # 默认监听 8000 端口（笔记本通过 http://guiyang-pc:8000 调用）
    app.run(host="0.0.0.0", port=8000, debug=False)