import os
import sys

# 确保可以导入项目根目录下的 models 包
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.services.llm_router import route_chat, _get_shimmy_host_for_model


def main():
    model = "tinyllama:latest"
    host = _get_shimmy_host_for_model(model)
    print("[Shimmy Host]", host)
    msgs = [
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "请用一句中文描述 TinyLlama 的特点"},
    ]
    print("[Response]")
    print(route_chat(model, messages=msgs))


if __name__ == "__main__":
    main()