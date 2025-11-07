def generate_architecture_diagram(spec: dict) -> str:
    """生成架构图描述（实际可对接 Mermaid）"""
    return f"```mermaid\ngraph TD\n    A[Tauri App] --> B[Python Backend]\n    B --> C[ONNX Model]\n```"

def define_module_interface(module_name: str) -> dict:
    """定义模块接口"""
    interfaces = {
        "video_uploader": {"input": "file_path", "output": "temp_path"},
        "onnx_processor": {"input": "temp_path", "output": "output_path"}
    }
    return interfaces.get(module_name, {})

def evaluate_tech_stack(comparison: list) -> str:
    """技术选型评估"""
    return "✅ 推荐 Shimmy + FFmpeg：轻量、离线、社区活跃"