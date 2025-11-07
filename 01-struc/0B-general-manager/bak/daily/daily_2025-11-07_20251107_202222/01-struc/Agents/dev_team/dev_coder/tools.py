
"""
Tools for Dev Coder Agent

This module provides helper functions that the dev_coder agent can call to:
- generate a sample Tauri React UI
- generate a sample Python backend script
- perform a simple static security check on code snippets
"""

from typing import Dict


def generate_tauri_ui(spec: Dict) -> str:
    """Generate a sample Tauri front-end code (React).

    Args:
        spec: Arbitrary spec dict (unused for now, reserved for future templates)
    Returns:
        A multi-line string representing a simple React component.
    """
    return """
// frontend/src/App.jsx
import React, { useState } from 'react';
const VideoUploader = () => {
  const [file, setFile] = useState(null);
  return (
    <div>
      <input type="file" accept=".mp4,.mov" onChange={(e) => setFile(e.target.files[0])} />
      {file && <video src={URL.createObjectURL(file)} controls width="600" />}
    </div>
  );
};
export default VideoUploader;
"""


def generate_python_backend(mode: str) -> str:
    """Generate a sample Python backend processing script.

    Args:
        mode: "local" for local execution example; otherwise returns a placeholder.
    Returns:
        A multi-line string containing sample Python backend code or a placeholder.
    """
    if mode == "local":
        return """
# backend/process.py
import subprocess

def remove_watermark_local(video_path):
    result = subprocess.run(["python", "models/shimmy/infer.py", video_path], capture_output=True)
    if result.returncode == 0:
        return "✅ 处理成功"
    else:
        return f"❌ 失败: {result.stderr.decode()}"
"""
    else:
        return "# 云加速模式待对接阿里云百炼API"


def validate_code_security(code: str) -> str:
    """Perform a simple static security check on the given code snippet.

    Flags risky functions that should not be used in production without sandboxing.
    """
    risky_patterns = ("os.system", "__import__")
    if any(p in code for p in risky_patterns):
        return "⚠️ 安全风险：禁止使用危险函数"
    return "✅ 代码安全"