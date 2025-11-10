# infer_gpu.py
# 江门台式机 GPU 加速推理服务（CUDA 模式）
# 路径: S:\YDS-Lab\projects\dewatermark-ai\servers\local-pc\

import os
import sys
import torch
import torchvision.transforms as T
from PIL import Image
from flask import Flask, request, jsonify

# 添加项目根目录到 Python 路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import log_to_general_office

app = Flask(__name__)

# 模型路径（轻量级 LaMa-256px）
LAMA_256_MODEL_PATH = os.path.join(project_root, "projects", "dewatermark-ai", "models", "lama_256", "lama_256.pth")
OUTPUT_DIR = os.path.join(project_root, "projects", "dewatermark-ai", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 初始化模型（仅加载一次）
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if not os.path.exists(LAMA_256_MODEL_PATH):
    raise FileNotFoundError(f"模型文件不存在: {LAMA_256_MODEL_PATH}")

# 简化模型加载（实际应替换为完整推理逻辑）
def load_lama_256():
    # 此处应加载实际的 LaMa 模型
    log_to_general_office("江门机加载 LaMa-256px 模型", "operations")
    return lambda x: x  # 占位符

model = load_lama_256()

@app.route("/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    gpu_info = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "无GPU"
    return jsonify({"status": "ok", "device": "jiangmen-pc", "gpu": gpu_info, "mode": "gpu-cuda"})

@app.route("/process", methods=["POST"])
def process_image():
    """
    GPU 加速图像去水印（仅支持 ≤256px 图像）
    输入: {"input_path": "S:/images/frame_001.png"}
    输出: {"output_path": "S:/YDS-Lab/projects/dewatermark-ai/output/frame_001_clean.png"}
    """
    try:
        data = request.get_json()
        input_path = data.get("input_path")
        
        if not input_path or not os.path.exists(input_path):
            return jsonify({"error": "输入文件不存在"}), 400
        
        # 限制输入尺寸（避免显存溢出）
        with Image.open(input_path) as img:
            if max(img.size) > 256:
                return jsonify({"error": "输入图像过大（>256px），请使用贵阳机处理"}), 400
        
        # 生成输出路径
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}_clean.png")
        
        # 调用 GPU 推理（此处为占位逻辑）
        log_to_general_office(f"江门机启动 GPU 推理: {input_path}", "operations")
        # 实际应调用 model(input_tensor)
        shutil.copy(input_path, output_path)  # 模拟处理
        
        log_to_general_office(f"✅ 江门机处理成功: {output_path}", "operations")
        return jsonify({"output_path": output_path})
        
    except Exception as e:
        log_to_general_office(f"⚠️ 江门机异常: {str(e)}", "errors")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # 监听 8001 端口（避免与贵阳机冲突）
    app.run(host="0.0.0.0", port=8001, debug=False)