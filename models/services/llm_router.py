# LLM Router Service
import os
import json
from pathlib import Path
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "models" / "config"

LOCAL_SECRET_FILES = [
    CONFIG_DIR / "secret_vars.local.json",
    CONFIG_DIR / "api_keys.local.json",
]

DEFAULT_CONFIG_FILE = CONFIG_DIR / "api_keys.json"


def _load_json(path: Path) -> Dict:
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def load_api_keys() -> Dict[str, str]:
    """加载API密钥：优先读取本地秘密文件，其次读取默认配置文件，最后读取环境变量。
    注意：本地秘密文件已被加入.gitignore，不会上传到仓库。
    """
    keys: Dict[str, str] = {}

    # 1) 本地秘密文件（优先级最高）
    for p in LOCAL_SECRET_FILES:
        keys.update(_load_json(p))

    # 2) 默认配置文件（可提交，仅存放占位符或公开信息）
    default_keys = _load_json(DEFAULT_CONFIG_FILE)
    for k, v in default_keys.items():
        keys.setdefault(k, v)

    # 3) 环境变量（如果前两者没有，则从环境变量读取）
    for env_key in [
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "ANTHROPIC_API_KEY",
        "OTHER_SERVICE_KEY",
    ]:
        if env_key not in keys and os.environ.get(env_key):
            keys[env_key] = os.environ[env_key]

    return keys


def get_key(name: str) -> Optional[str]:
    return load_api_keys().get(name)


def get_github_token() -> Optional[str]:
    return get_key("GITHUB_TOKEN")


def get_openai_key() -> Optional[str]:
    return get_key("OPENAI_API_KEY")


# 供其他服务调用示例
if __name__ == "__main__":
    keys = load_api_keys()
    masked = {k: ("***" if v else None) for k, v in keys.items()}
    print("Loaded API keys:", masked)