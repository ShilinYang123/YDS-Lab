# api_server.py
# 贵阳台式机本地推理服务（ONNX CPU 模式）
# 路径: S:\YDS-Lab\projects\001-dewatermark-ai\servers\guiyang-server\api_server.py

import os
import sys
import subprocess
import time
from flask import Flask, request, jsonify

# === 1. 正确设置项目根目录 ===
# 当前文件所在目录: .../servers/guiyang-server/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))  # 回到 YDS-Lab/
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# === 2. 安全日志导入（避免 utils.logger 不存在导致启动失败）===
try:
    from utils.logger import log_to_general_office
except ImportError:
    def log_to_general_office(msg, category="system"):
        print(f"[{category.upper()}] {msg}")

# === 3. 路径定义（使用 os.path.join 确保 Windows 兼容）===
# 导入模型路径解析器
sys.path.append(os.path.join(project_root, "utils"))
from model_path_resolver import get_shimmy_path, get_model_path

# 模型路径配置（支持外部目录）
SHIMMY_SCRIPT = get_shimmy_path()
LAMA_MODEL_DIR = get_model_path("lama")
OUTPUT_DIR = os.path.join(project_root, "projects", "001-dewatermark-ai", "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "device": "guiyang-pc",
        "mode": "local-cpu",
        "output_dir": OUTPUT_DIR
    })

@app.route("/process", methods=["POST"])  # 👈 接口名与前端示例一致
def process_video():
    """
    输入: {"video_url": "本地文件路径 或 公网URL"}
    输出: {"output_path": ".../output/xxx.mp4"}
    """
    try:
        data = request.get_json()
        input_path = data.get("video_url")  # 👈 与前端字段名一致

        if not input_path:
            return jsonify({"error": "缺少 video_url 字段"}), 400

        # 支持本地路径（不支持远程 URL，除非你实现下载逻辑）
        if not os.path.exists(input_path):
            return jsonify({"error": f"输入文件不存在: {input_path}"}), 400

        # 生成带时间戳的输出文件名
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        timestamp = time.strftime("%Y%m%d%H%M%S")
        output_filename = f"{base_name}_dewatermark_{timestamp}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # === 4. 确保 infer.py 存在 ===
        if not os.path.exists(SHIMMY_SCRIPT):
            error = f"Shimmy 脚本不存在: {SHIMMY_SCRIPT}"
            log_to_general_office(error, "errors")
            return jsonify({"error": error}), 500

        # === 5. 构建命令（使用当前 Python 环境）===
        cmd = [
            sys.executable,
            SHIMMY_SCRIPT,
            "--input", input_path,
            "--output", output_path,
            "--model_dir", LAMA_MODEL_DIR
        ]

        log_to_general_office(f"启动推理: {input_path} → {output_path}", "operations")
        
        # 执行推理（5分钟超时）
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=os.path.dirname(SHIMMY_SCRIPT)  # 👈 设置工作目录，避免相对路径问题
        )

        if result.returncode == 0 and os.path.exists(output_path):
            log_to_general_office(f"✅ 处理成功: {output_path}", "operations")
            return jsonify({"output_path": output_path})
        else:
            error_msg = result.stderr.strip() if result.stderr else "未知错误"
            log_to_general_office(f"❌ 处理失败: {error_msg}", "errors")
            return jsonify({"error": f"模型推理失败: {error_msg}"}), 500

    except subprocess.TimeoutExpired:
        error = "处理超时（超过5分钟）"
        log_to_general_office(error, "errors")
        return jsonify({"error": error}), 500
    except Exception as e:
        error = f"服务器异常: {str(e)}"
        log_to_general_office(error, "errors")
        return jsonify({"error": error}), 500

if __name__ == "__main__":
    # 👇 关键：监听 0.0.0.0，允许外部访问（包括 ngrok）
    app.run(host="0.0.0.0", port=8000, debug=False)