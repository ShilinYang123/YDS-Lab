#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JS001 Meetingroom 可视化后端（Flask + WebSocket）

- 提供会议记录浏览 API
- 提供触发会议生成的 API（调用 tools/agents/run_collab.py）
- 同域托管前端静态页面（仅 03-dev/002-meetingroom/ui）
- 实时日志传输到浏览器（WebSocket）

启动：
  python 03-dev/002-meetingroom/servers/meetingroom_server.py --host 127.0.0.1 --port 8020

依赖：Flask, Flask-SocketIO（requirements.txt 已包含）
"""

import os
import sys
import json
import time
import subprocess
import uuid
import threading
import queue
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
from flask import Flask, jsonify, request, send_from_directory, abort, Response
from flask import stream_with_context
from flask_socketio import SocketIO
import fnmatch
import requests
try:
    import yaml  # 权限配置解析（permission.yaml）
except Exception:
    yaml = None

# 导入新的系统组件
from mcp_message_model import (
    MCPMessage,
    MCPMessageBuilder,
    MCPMessageValidator,
    ChannelType,
    EventType,
    AgentInfo,
    VotePayload,
)
from agent_roles import AgentRoleManager
from meeting_levels import MeetingLevelManager
from intelligent_agenda import IntelligentAgendaGenerator
from document_governance import DocumentGovernanceManager
from rbac_system import RBACSystem
from voice_service import VoiceServiceManager


# 仓库根目录（注意：本文件位于 03-dev/002-meetingroom/servers 下，根目录为 parents[3]）
REPO_ROOT = Path(__file__).resolve().parents[3]
# 确保可以导入仓库根路径下的模块（如 models.services.llm_router）
root_str = str(REPO_ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
# 会议纪要归档目录：仅允许 01-struc/0B-general-manager/meetings
MEETINGS_DIR = REPO_ROOT / "01-struc" / "0B-general-manager" / "meetings"
# 前端目录：仅 03-dev/002-meetingroom/ui（不再兼容 projects 或其他旧路径）
UI_DIR_PRIMARY_03DEV = REPO_ROOT / "03-dev" / "002-meetingroom" / "ui"

# LongMemory 模块所在目录（统一到 04-prod/001-memory-system/scripts/monitoring，回退到市场部补丁包）
LM_PRIMARY_DIR = REPO_ROOT / "04-prod" / "001-memory-system" / "scripts" / "monitoring"
# 路径更新：旧路径 01-struc/05-marketing/Task/005-Trae长记忆功能实施/智能监控系统补丁包v1.0/src/tools/LongMemory
# 新路径统一至 02-task/001-长记忆系统开发/智能监控系统补丁包v1.0/src/tools/LongMemory
LM_FALLBACK_PATCH_DIR = REPO_ROOT / "02-task" / "001-长记忆系统开发" / "智能监控系统补丁包v1.0" / "src" / "tools" / "LongMemory"
LM_DIR = LM_PRIMARY_DIR if LM_PRIMARY_DIR.exists() else LM_FALLBACK_PATCH_DIR
START_TIME = time.time()

# 选择可用的 UI 目录（强制 03-dev 存在）
UI_DIR = UI_DIR_PRIMARY_03DEV

# 统一‘项目目录’显示：仅 03-dev
PROJECT_DIR_JS001 = REPO_ROOT / "03-dev" / "002-meetingroom"
PROJECT_DIR_JS001_DISPLAY = "03-dev/002-meetingroom"

# 调试输出：在启动时打印与前端目录相关的信息，便于定位路径问题
try:
    sys.stdout.write("[UI] REPO_ROOT: " + str(REPO_ROOT) + "\n")
    sys.stdout.write(
        "[UI] UI_DIR_PRIMARY_03DEV: "
        + str(UI_DIR_PRIMARY_03DEV)
        + " (exists: "
        + str(UI_DIR_PRIMARY_03DEV.exists())
        + ")\n"
    )
    sys.stdout.write("[UI] PROJECT_DIR_JS001_DISPLAY: " + str(PROJECT_DIR_JS001_DISPLAY) + "\n")
    idx_03 = UI_DIR_PRIMARY_03DEV / "index.html"
    sys.stdout.write(
        "[UI] Selected UI_DIR: "
        + str(UI_DIR)
        + " (exists: "
        + str(UI_DIR.exists())
        + ")\n"
    )
    sys.stdout.write("[UI] Index exists (03-dev): " + str(idx_03.exists()) + "\n")
except Exception:
    pass

app = Flask(
    __name__
)

# 添加WebSocket支持
socketio = SocketIO(
    app, 
    cors_allowed_origins="*"
)

# WebSocket握手JWT强制策略（默认关闭，避免影响现有客户端；可通过环境变量开启）
# 设置 WS_JWT_REQUIRED=true/1/yes/on 即可强制在握手阶段校验JWT
WS_JWT_REQUIRED: bool = (
    str(os.environ.get("WS_JWT_REQUIRED", "false")).strip().lower()
    in ("1", "true", "yes", "on")
)

# 统一的 MCP 消息模型封装（MVP）


def emit_mcp_event(
    event: str,
    data: Dict[str, Any],
    level: Optional[str] = None,
    channel: Optional[str] = None,
    broadcast: bool = True,
) -> None:
    """通过 WebSocket 广播统一的 MCP 消息模型。
    不改变历史事件名称的兼容性（仍保留原事件），新增 mcp_event 聚合事件供新版前端订阅。
    """
    try:
        envelope = {
            "model": "MCP-UNIFIED-0.1",
            "event": event,
            "ts": time.time(),
            "source": "meetingroom_server",
            "level": level or "info",
            "channel": channel or "mcp",
            "data": data or {},
        }
        socketio.emit("mcp_event", envelope, broadcast=broadcast)
    except Exception:
        pass

# 新增：严格版MCP消息事件通道（与兼容版并行）


def emit_mcp_message(message: MCPMessage, broadcast: bool = True) -> None:
    """通过 WebSocket 广播严格版 MCP 消息模型（mcp_message）。
    该事件负载为 MCPMessage.to_dict()，包含 room_id、event_type、topic、sender 等字段，便于前端基于 room_id+channel 路由。
    """
    try:
        payload = message.to_dict()
        socketio.emit("mcp_message", payload, broadcast=broadcast)
    except Exception:
        pass

# 认证辅助：从请求中解析JWT令牌并校验


def _get_jwt_payload_from_request() -> Optional[Dict[str, Any]]:
    try:
        auth = request.headers.get("Authorization") or ""
        token = None
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1].strip()
        # 兼容query或body传递token
        token = token or (request.args.get("token") or "").strip()
        try:
            body = request.get_json(force=False, silent=True) or {}
        except Exception:
            body = {}
        token = token or (body.get("token") or "").strip()
        if not token:
            return None
        return rbac_system.verify_jwt_token(token)
    except Exception:
        return None


def _resolve_effective_role(explicit_role: str) -> str:
    """优先使用JWT中的角色；无JWT时回退到显式role参数。"""
    payload = _get_jwt_payload_from_request()
    if payload:
        roles = payload.get("roles") or []
        if isinstance(roles, list) and roles:
            return roles[0]
    return (explicit_role or "").strip()


# LongMemory 模块动态加载与实例管理
_LM_INSTANCES: Dict[str, Any] = {"reminder": None, "monitor": None}

# 初始化YDS AI系统管理器
agent_role_manager = AgentRoleManager()
meeting_level_manager = MeetingLevelManager()
agenda_generator = IntelligentAgendaGenerator()
document_governance = DocumentGovernanceManager()
rbac_system = RBACSystem()
voice_service = VoiceServiceManager()

# MCP消息验证器
mcp_validator = MCPMessageValidator()


def _load_module_from_file(mod_name: str, file_path: Path):
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        sys.stdout.write(f"[LM] 动态加载失败: {file_path} -> {e}\n")
        return None


def _ensure_lm_loaded() -> Dict[str, Any]:
    """确保LM模块已加载，返回{'reminder': module, 'monitor': module}
    新版策略：
    - 仅从 LM_DIR（04-prod/001-memory-system/scripts/monitoring 或补丁包目录）加载
    - 不再使用 tools/LongMemory 旧目录回退
    - 通过文件路径+sys.modules 注册的方式，保证其内部相互导入（smart_error_detector、proactive_reminder、intelligent_monitor）
    """
    result = {"reminder": None, "monitor": None}
    try:
        # 保障路径可导入
        if LM_DIR and LM_DIR.exists():
            lm_str = str(LM_DIR)
            if lm_str not in sys.path:
                sys.path.insert(0, lm_str)
            lm_parent = str(LM_DIR.parent)
            if lm_parent not in sys.path:
                sys.path.insert(0, lm_parent)
            # 若生产结构为 .../scripts/monitoring，补充 scripts 目录，便于某些入口脚本互相引用
            scripts_dir = LM_DIR.parent if LM_DIR.name == "monitoring" else None
            if scripts_dir:
                scripts_str = str(scripts_dir)
                if scripts_str not in sys.path:
                    sys.path.insert(0, scripts_str)

        # 预加载依赖模块，避免相对导入失败
        dep_path = LM_DIR / "smart_error_detector.py"
        if dep_path.exists():
            mod_dep = _load_module_from_file("smart_error_detector", dep_path)
            if mod_dep:
                sys.modules["smart_error_detector"] = mod_dep
        rem_path = LM_DIR / "proactive_reminder.py"
        if rem_path.exists():
            mod_rem = _load_module_from_file("proactive_reminder", rem_path)
            if mod_rem:
                sys.modules["proactive_reminder"] = mod_rem
                result["reminder"] = mod_rem
        mon_path = LM_DIR / "intelligent_monitor.py"
        if mon_path.exists():
            mod_mon = _load_module_from_file("intelligent_monitor", mon_path)
            if mod_mon:
                sys.modules["intelligent_monitor"] = mod_mon
                result["monitor"] = mod_mon
        # 顶层导入兜底（在 LM_DIR 已加入 sys.path 的前提下）
        if not result.get("reminder"):
            try:
                import importlib
                result["reminder"] = importlib.import_module("proactive_reminder")
            except Exception as e:
                sys.stdout.write(f"[LM] 顶层导入 proactive_reminder 失败: {e}\n")
        if not result.get("monitor"):
            try:
                import importlib
                result["monitor"] = importlib.import_module("intelligent_monitor")
            except Exception as e:
                sys.stdout.write(f"[LM] 顶层导入 intelligent_monitor 失败: {e}\n")
    except Exception as e:
        try:
            sys.stdout.write(f"[LM] 加载模块异常: {e}\n")
        except Exception:
            pass
    return result


def _get_longmemory_storage_path() -> Path:
    """解析 LongMemory 持久化存储路径：优先环境变量 LONGMEMORY_PATH，其次配置文件 config/yds_ai_config.yaml 的 longmemory.storage_path。
    返回绝对路径并确保父目录存在。"""
    # 1) 环境变量优先
    env_path = os.environ.get("LONGMEMORY_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = REPO_ROOT / p
        return p

    # 2) 配置文件（仅使用统一路径：config/yds_ai_config.yaml）
    cfg_candidates = [REPO_ROOT / "config" / "yds_ai_config.yaml"]
    for cfg_file in cfg_candidates:
        try:
            if yaml and cfg_file.exists():
                with open(cfg_file, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                lm_cfg = (cfg.get("longmemory") or {})
                storage_path = (lm_cfg.get("storage_path") or "").strip()
                if storage_path:
                    p = Path(storage_path)
                    if not p.is_absolute():
                        p = REPO_ROOT / p
                    return p
        except Exception as e:
            try:
                sys.stdout.write(f"[LM] 读取 yds_ai_config.yaml 失败: {e}\n")
            except Exception:
                pass

    # 3) 默认路径（统一至公司级 01-struc/logs/longmemory，避免与 Trae IDE 的 Memory MCP 的 memory.json 混淆）
    return REPO_ROOT / "01-struc" / "logs" / "longmemory" / "lm_records.json"


def _ensure_longmemory_storage_file(path: Path) -> None:
    """确保持久化文件存在；若不存在则创建空结构。"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            with open(path, "w", encoding="utf-8") as f:
                # 初始化为LongMemory内部使用的结构，避免后续写入失败
                json.dump({"general": {}, "memories": []}, f, ensure_ascii=False)
                f.write("\n")
    except Exception as e:
        try:
            sys.stdout.write(f"[LM] 创建持久化文件失败: {e}\n")
        except Exception:
            pass


# 初始化 LongMemory 的持久化文件与配置路径（供 /mcp/lm/* 端点使用）

try:
    storage_path: Path = _get_longmemory_storage_path()
    _ensure_longmemory_storage_file(storage_path)
except Exception as e:
    try:
        sys.stdout.write(f"[LM] 初始化持久化文件失败: {e}\n")
    except Exception:
        pass

# 配置文件路径：优先 04-prod/001-memory-system/config/LongMemory，回退到补丁包或 LM_DIR
LM_CONFIG_PRIMARY = REPO_ROOT / "04-prod" / "001-memory-system" / "config" / "LongMemory"
# 路径更新：旧路径 01-struc/05-marketing/Task/005-Trae长记忆功能实施/智能监控系统补丁包v1.0/config/LongMemory
# 新路径 02-task/001-长记忆系统开发/智能监控系统补丁包v1.0/config/LongMemory
LM_CONFIG_FALLBACK_PATCH = REPO_ROOT / "02-task" / "001-长记忆系统开发" / "智能监控系统补丁包v1.0" / "config" / "LongMemory"
try:
    if LM_CONFIG_PRIMARY.exists():
        LM_CONFIG_DIR: Path = LM_CONFIG_PRIMARY
    elif LM_CONFIG_FALLBACK_PATCH.exists():
        LM_CONFIG_DIR = LM_CONFIG_FALLBACK_PATCH
    else:
        LM_CONFIG_DIR = LM_DIR
except Exception:
    LM_CONFIG_DIR = LM_DIR
reminder_cfg: Path = LM_CONFIG_DIR / "reminder_config.json"
monitor_cfg: Path = LM_CONFIG_DIR / "intelligent_monitor_config.json"


def _lm_status() -> Dict[str, Any]:
    """聚合返回LM实例状态"""
    status: Dict[str, Any] = {"reminder": None, "monitor": None}
    try:
        r = _LM_INSTANCES.get("reminder")
        m = _LM_INSTANCES.get("monitor")
        if r and hasattr(r, "get_statistics"):
            status["reminder"] = r.get_statistics()
        else:
            status["reminder"] = {"monitoring_status": "stopped"}
        if m and hasattr(m, "get_system_status"):
            status["monitor"] = m.get_system_status()
        else:
            status["monitor"] = {"monitoring_active": False}
    except Exception as e:
        status["error"] = str(e)
    return status


# 启动时打印路由映射，便于调试 405/404 问题


def _print_routes_summary():
    try:
        sys.stdout.write("[Routes] Registered URL rules:\n")
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            methods = ",".join(sorted((rule.methods or set()) - {"HEAD"}))
            sys.stdout.write(f"  - {rule.rule} [{methods}] -> {rule.endpoint}\n")
        sys.stdout.write("\n")
    except Exception:
        pass

# 日志重定向类


class LogCapture:
    def __init__(self):
        self.buffer = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        # 写入原始输出
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        # 发送到WebSocket客户端
        if text.strip():  # 只发送非空内容
            socketio.emit('log_message', {
                'message': text.strip(),
                'timestamp': time.time(),
                'type': 'stdout'
            })
        
        return len(text)
    
    def flush(self):
        self.original_stdout.flush()


# 全局日志捕获器
log_capture = LogCapture()


# WebSocket事件处理器
@socketio.on('connect')
def handle_connect():
    # 可选：在握手阶段强制JWT校验，确保仅授权用户可建立WebSocket连接
    if WS_JWT_REQUIRED:
        payload = _get_jwt_payload_from_request()
        if not payload:
            try:
                print(f"[WebSocket] 拒绝连接（缺少或无效JWT）: {request.sid}")
            except Exception:
                pass
            return False  # 拒绝连接
        else:
            try:
                uid = payload.get('user_id') or payload.get('username') or 'unknown'
                roles = payload.get('roles') or []
                print(f"[WebSocket] 客户端连接: {request.sid} 用户: {uid} 角色: {roles}")
            except Exception:
                pass
    else:
        print(f"[WebSocket] 客户端连接: {request.sid}")

    socketio.emit('log_message', {
        'message': 'WebSocket连接已建立',
        'timestamp': time.time(),
        'level': 'info'
    })


@socketio.on('disconnect')
def handle_disconnect():
    print(f"[WebSocket] 客户端断开: {request.sid}")


@socketio.on('request_logs')
def handle_request_logs():
    print(f"[WebSocket] 客户端请求日志: {request.sid}")
    socketio.emit('log_message', {
        'message': '开始接收服务器日志',
        'timestamp': time.time(),
        'level': 'info'
    })


# 简易实时会议会话管理（SSE）
RTM_SESSIONS: Dict[str, Dict[str, Any]] = {}

# =====================
#   后端首选策略与Shimmy自启动
# =====================

# 首选后端：默认“shimmy”（以效果与资源效率为先）；可通过环境变量切换
PREFERRED_BACKEND = os.environ.get("MEETINGROOM_PREFERRED_BACKEND", "shimmy").strip().lower() or "shimmy"

# Shimmy 进程句柄（可选）
_SHIMMY_PROC: Optional[subprocess.Popen] = None
# 新增：多实例进程句柄映射（key: "host:port"）
_SHIMMY_PROCS: Dict[str, subprocess.Popen] = {}


def _get_cfg() -> Dict[str, Any]:
    return _load_external_models_cfg() or {}


def _get_shimmy_base_and_v1() -> (Optional[str], Optional[str]):
    cfg = _get_cfg()
    shim = (cfg.get("models") or {}).get("shimmy") or {}
    base = (shim.get("host") or "").rstrip("/")  # e.g. http://127.0.0.1:11436
    if not base:
        return None, None
    v1 = base + ("/v1" if not base.endswith("/v1") else "")
    return base, v1


def _check_host_ok(base: str) -> bool:
    """检查 Shimmy/Ollama 主机是否可达。优先 /health，其次 /v1/models。"""
    for path in ("/health", "/v1/models", "/models", "/api/tags"):
        data = _http_get_json(base.rstrip("/") + path, timeout=1.2)
        if data:
            return True
    return False


def _ensure_shimmy_running(wait_secs: float = 10.0) -> bool:
    """确保 Shimmy 及其实例运行：
    - 读取 external_models.json，尝试启动默认 host 与所有已配置的实例（如 11435/11437）；
    - 即便默认 host 已就绪，也会检查实例状态并在必要时自启动；
    - 返回默认 host 的可达性（保持原有语义）。
    """
    global _SHIMMY_PROC
    base, v1 = _get_shimmy_base_and_v1()
    if not base:
        return False

    # 读取可执行路径与工作目录
    cfg_path = REPO_ROOT / "models" / "config" / "external_models.json"
    exec_path: Optional[str] = None
    work_dir: Optional[str] = None
    instances: Dict[str, str] = {}
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        shim = (raw.get("external_models_config") or {}).get("models", {}).get("shimmy") or {}
        exec_path = shim.get("executable_path")
        work_dir = os.path.dirname(exec_path) if exec_path else None
        instances = (shim.get("instances") or {})
    except Exception:
        exec_path = None
        work_dir = None
        instances = {}

    # 兜底：从 utils.model_path_resolver 获取
    if not exec_path:
        try:
            from utils.model_path_resolver import get_shimmy_path  # type: ignore
            exec_path = get_shimmy_path()
            work_dir = os.path.dirname(exec_path) if exec_path else work_dir
        except Exception:
            pass

    if not exec_path or not os.path.exists(exec_path):
        return False

    # 收集需确保运行的主机（默认 + 实例）
    ensure_hosts: List[str] = [base]
    for _, h in (instances or {}).items():
        if not h:
            continue
        hh = h.rstrip("/")
        if hh not in ensure_hosts:
            ensure_hosts.append(hh)

    # 启动不可达的主机
    def _bind_from_host(h: str) -> str:
        try:
            from urllib.parse import urlparse
            u = urlparse(h)
            return f"{u.hostname}:{u.port or 11436}"
        except Exception:
            return "127.0.0.1:11436"

    any_started = False
    for h in ensure_hosts:
        ok = _check_host_ok(h)
        if ok:
            continue
        bind = _bind_from_host(h)
        # 避免重复启动同一绑定地址
        proc = _SHIMMY_PROCS.get(bind)
        if proc and (proc.poll() is None):
            continue
        try:
            p = subprocess.Popen(
                [exec_path, "serve", "--bind", bind],
                cwd=work_dir or REPO_ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP")
                    else 0
                ),
            )
            _SHIMMY_PROCS[bind] = p
            # 兼容旧字段，记录默认 host 的进程句柄
            if h.rstrip("/") == base.rstrip("/"):
                _SHIMMY_PROC = p
            any_started = True
        except Exception:
            continue

    # 等待默认 host 与新启动实例就绪（默认主机等待 wait_secs，其它实例简短等待）
    deadline_default = time.time() + max(0.0, float(wait_secs))
    while time.time() < deadline_default:
        if _check_host_ok(base):
            break
        time.sleep(0.5)

    # 对刚启动的其它实例给予简短等待（最多 1/3 * wait_secs）
    if any_started:
        deadline_instances = time.time() + max(0.0, float(wait_secs) / 3.0)
        while time.time() < deadline_instances:
            # 若所有实例均已就绪则提前退出
            if all(_check_host_ok(h) for h in ensure_hosts):
                break
            time.sleep(0.5)

    return _check_host_ok(base)


def _shimmy_can_infer(base_url: str, model_id: str) -> bool:
    """探测 Shimmy 是否能对指定模型完成一次最小推理。"""
    if not base_url or not model_id:
        return False
    url_base = base_url.rstrip('/')
    payload = {
        "model": model_id,
        # 使用极简提示，限制输出，降低检查开销
        "prompt": "ping",
        "max_tokens": 8,
        "temperature": 0.2,
    }
    try:
        # 尝试 OpenAI /v1/completions
        r = requests.post(f"{url_base}/v1/completions", json=payload, timeout=2)
        if 200 <= r.status_code < 300:
            return True
    except Exception:
        pass
    try:
        # 尝试非 /v1 前缀
        r = requests.post(f"{url_base}/completions", json=payload, timeout=2)
        if 200 <= r.status_code < 300:
            return True
    except Exception:
        pass
    try:
        # 尝试 /api/generate（如同 Ollama）
        r = requests.post(f"{url_base}/api/generate", json=payload, timeout=3)
        if 200 <= r.status_code < 300:
            return True
    except Exception:
        pass
    return False


def _list_models(base_url: str) -> List[str]:
    """获取远端可用模型列表 ID。"""
    base_url = (base_url or "").rstrip("/")
    ids: List[str] = []
    for path in ("/v1/models", "/models", "/api/models"):
        data = _http_get_json(base_url + path, timeout=1.5)
        if not data:
            continue
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            ids.extend([m.get("id") for m in data.get("data") if isinstance(m, dict) and m.get("id")])
            break
    return [i for i in ids if i]


def _first_present(candidates: List[str], pool: List[str], default_fallback: str) -> str:
    """返回候选集中第一个在池中出现的 ID，否则返回默认值。"""
    s = set(pool)
    for c in candidates:
        if c in s:
            return c
    return default_fallback


def _pick_default_models() -> Dict[str, str]:
    """根据首选后端与可达性，确定离线与实时默认模型。"""
    # Shimmy 首选模型（GGUF ID）
    offline_shimmy_priority = [
        "qwen2-0_5b-instruct-q4_0",
        "qwen2-1_5b-instruct-q4_0",
        "phi3-lora",
    ]
    rtm_shimmy_priority = [
        "tinyllama-1.1b-chat-q4_0",
        "phi3-lora",
    ]
    # Ollama 兜底模型（拉取门槛低）
    offline_ollama = "qwen2:0.5b"
    rtm_ollama = "tinyllama:latest"

    base, _v1 = _get_shimmy_base_and_v1()
    shimmy_ok = _check_host_ok(base) if base else False
    shimmy_models: List[str] = _list_models(base) if shimmy_ok else []
    # 仅筛选可真正推理成功的模型 ID，用于默认候选
    shimmy_ready_models: List[str] = []
    if shimmy_ok and shimmy_models:
        # 最多探测前若干个，避免首启阻塞过久
        for mid in shimmy_models[:5]:
            try:
                if _shimmy_can_infer(base, mid):
                    shimmy_ready_models.append(mid)
            except Exception:
                continue

    if PREFERRED_BACKEND == "shimmy":
        return {
            # 只有当 Shimmy 存在且能实际推理时才优先选择，否则回退到 Ollama
            "offline": (
                _first_present(offline_shimmy_priority, (shimmy_ready_models or []), offline_ollama)
                if shimmy_ok else offline_ollama
            ),
            "rtm": (
                _first_present(rtm_shimmy_priority, (shimmy_ready_models or []), rtm_ollama)
                if shimmy_ok else rtm_ollama
            ),
        }
    else:
        # 如果用户指定 Ollama 为首选，则优先使用 Ollama；当其不可达再降级到 Shimmy
        # 这里不额外探测 Ollama，可交给路由层回退；仅在 Shimmy 不可达时不选其模型。
        return {
            "offline": (
                offline_ollama if PREFERRED_BACKEND == "ollama"
                else (offline_shimmy_priority[0] if offline_shimmy_priority else offline_ollama)
            ),
            "rtm": (
                rtm_ollama if PREFERRED_BACKEND == "ollama"
                else (rtm_shimmy_priority[0] if rtm_shimmy_priority else rtm_ollama)
            ),
        }


def _ensure_meetings_dir() -> None:
    try:
        MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _rtm_enqueue(sess: Dict[str, Any], event: str, data: Dict[str, Any]) -> None:
    """将事件入队供 SSE 消费。"""
    try:
        q: queue.Queue = sess["queue"]
        q.put({"event": event, "data": data})
    except Exception:
        pass


def _rtm_record(sess: Dict[str, Any], event: str, data: Dict[str, Any]) -> None:
    """在会话内记录原始事件，并根据规则汇聚逐字稿。"""
    # 记录原始事件
    try:
        events: List[Dict[str, Any]] = sess.setdefault("events", [])
        events.append({"event": event, "data": data})
    except Exception:
        pass

    # 汇聚逐字稿：
    try:
        transcript: List[Dict[str, Any]] = sess.setdefault("transcript", [])
        buffers: Dict[str, List[str]] = sess.setdefault("buffers", {})
        topic = data.get("topic")
        ts = data.get("ts") or time.time()
        if event == "agent_say":
            role = data.get("role") or "assistant"
            partial = data.get("partial") or ""
            if partial:
                arr = buffers.setdefault(role, [])
                arr.append(str(partial))
                # 也记录最近 topic
                sess.setdefault("last_topic", topic)
        elif event == "agent_say_done":
            role = data.get("role") or "assistant"
            arr = buffers.pop(role, [])
            text = "".join(arr).strip()
            if text:
                transcript.append({
                    "role": role,
                    "text": text,
                    "topic": topic or sess.get("last_topic"),
                    "ts": ts,
                })
        elif event == "user_say":
            # 用户输入直接写入逐字稿
            role = data.get("role") or "user"
            text = data.get("text") or ""
            if text:
                transcript.append({
                    "role": role,
                    "text": text,
                    "topic": topic or sess.get("last_topic"),
                    "ts": ts,
                })
        elif event == "start_meeting":
            sess["started_at"] = ts
        elif event == "end_meeting":
            sess["ended_at"] = ts
    except Exception:
        pass


def _rtm_emit(sid: str, event: str, data: Dict[str, Any]) -> None:
    """统一发射：既入队 SSE，又写入会话内的事件与逐字稿。"""
    sess = RTM_SESSIONS.get(sid)
    if not sess:
        return
    # 确保基本字段
    data = dict(data or {})
    data.setdefault("sid", sid)
    data.setdefault("ts", time.time())
    _rtm_record(sess, event, data)
    _rtm_enqueue(sess, event, data)


def _build_rtm_meeting_json(sess: Dict[str, Any]) -> Dict[str, Any]:
    """将会话转为与历史会议近似的 JSON 结构，便于前端与列表复用。"""
    sid = sess.get("sid")
    roles = sess.get("roles") or []
    agenda = sess.get("agenda") or []
    model = sess.get("model") or ""
    base_name = sess.get("base_name") or f"MTG-RTM-{sid}"
    started_at = float(sess.get("started_at") or time.time())
    ended_at = float(sess.get("ended_at") or started_at)
    created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(started_at))
    return {
        "base_name": base_name,
        "created_at": created_at,
        "type": "realtime_meeting",
        "sections": {
            "会议信息": {
                "会议类型": "实时会议",
                "项目": "JS001-meetingroom",
                "参会角色": roles,
                "议程": agenda,
                # 动态项目目录：优先 03-dev，再回退 projects
                "项目目录": PROJECT_DIR_JS001_DISPLAY,
                "模型": model,
                "Sid": sid,
                "开始时间": created_at,
                "结束时间": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ended_at)) if ended_at else None,
            },
            "逐字稿": {
                "items": sess.get("transcript", []),
            },
            "行动项与决策": [],
            "markdown": "",
        },
        # 附加：原始事件（调试/审计用）
        "rtm_events": sess.get("events", []),
    }


def _save_transcript_for_session(sid: str, finalize: bool = False) -> Optional[str]:
    """将会话转为 JSON 并写入文件，返回文件路径。"""
    sess = RTM_SESSIONS.get(sid)
    if not sess:
        return None
    _ensure_meetings_dir()
    # 生成 base_name 与文件路径（首次保存时固定）
    if not sess.get("base_name"):
        ts_label = time.strftime("%Y%m%d-%H%M%S", time.localtime(float(sess.get("started_at") or time.time())))
        sess["base_name"] = f"MTG-RTM-{ts_label}-{sid[:8]}"
    base_name = sess["base_name"]
    file_path = MEETINGS_DIR / f"{base_name}.json"
    sess["file_path"] = str(file_path)
    # 如果 finalize，则补一个 end 事件，避免遗漏
    if finalize and not sess.get("ended_at"):
        sess["ended_at"] = time.time()
    data = _build_rtm_meeting_json(sess)
    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        sess["saved"] = True
        return str(file_path)
    except Exception:
        return None


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    """格式化 SSE 事件输出（UTF-8）。"""
    try:
        payload = json.dumps(data, ensure_ascii=False)
    except Exception:
        payload = json.dumps({"error": "bad json"}, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _chunk_text(txt: str, max_len: int = 60) -> List[str]:
    """将文本按句子分割，每个句子作为一个完整的片段输出，过滤空白内容。"""
    import re
    
    # 按句子分割，保留句子结束符
    sentences = re.split(r'([。.!！?？])', txt)
    
    parts: List[str] = []
    
    for i in range(0, len(sentences), 2):
        if i < len(sentences):
            sentence_content = sentences[i]
            sentence_end = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            # 清理句子内容，去除多余的空白字符
            cleaned_content = sentence_content.strip()
            
            if cleaned_content:  # 只处理有实际内容的句子
                complete_sentence = cleaned_content + sentence_end
                parts.append(complete_sentence)
    
    # 如果没有找到句子分隔符，但有实际内容，返回整个文本作为一个片段
    if not parts and txt.strip():
        parts.append(txt.strip())
    
    # 过滤掉空白或只包含标点的片段
    parts = [part for part in parts if part.strip() and not re.match(r'^[\s\n。.!！?？]*$', part)]
    
    return parts


def _start_orchestrator_async(sid: str, roles: List[str], agenda: List[str], model: str):
    """开启一个后台线程，生成模拟的发言事件，推送到队列，供 SSE 端点消费。"""
    sess = RTM_SESSIONS.get(sid)
    if not sess:
        return

    # 轻度依赖：优先使用统一 LLM 路由；如不可导入则降级为固定文案
    try:
        from models.services.llm_router import route_chat  # type: ignore
    except Exception:
        def route_chat(messages: List[Dict[str, Any]], model: str = "") -> str:  # 简易降级：拼接提示给出演示文本
            # 从消息中提取用户意图，返回两三句建议作为占位
            user_msg = ""
            for m in messages:
                if isinstance(m, dict) and m.get("role") == "user":
                    user_msg = str(m.get("content") or "")
                    break
            return (
                f"建议：1) 明确目标与交付；2) 识别瓶颈并制定缓解方案；3) 排期下一步行动。\n"
                f"（模型路由不可用，使用占位文本。提示：{user_msg[:60]}…）"
            )

    def worker():
        sess["running"] = True
        # 会议启动事件
        _rtm_emit(sid, "start_meeting", {"roles": roles, "agenda": agenda, "model": model})

        # 选择一个议题作为示范
        topic = (agenda[0] if agenda else "临时议程：项目进度与下周计划")
        system_prompt = f"你是会议参与者，请围绕议题『{topic}』进行简明发言，给出具体建议或结论。语气专业、简洁。请直接以第一人称发言，不要包含角色名称前缀。"

        for role in roles:
            if not sess.get("running"):
                break
            # 生成发言内容（优先模型；失败则降级）
            content = None
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请以『{role}』身份就议题『{topic}』发表两到三句建议，直接以第一人称发言，不要包含角色名称。"},
                ]
                content = route_chat(messages=messages, model=model) or ""
            except Exception:
                content = f"围绕『{topic}』的简要建议：1) 控制风险与带宽；2) 明确下周可交付；3) 复盘当前瓶颈。"

            if not content:
                content = f"关于『{topic}』暂无更多意见。"

            # 确保内容不包含角色名称前缀
            if content.startswith(f"{role}：") or content.startswith(f"{role}:"):
                content = content.split("：", 1)[-1].split(":", 1)[-1].strip()

            # 流式分段推送
            for part in _chunk_text(content):
                if not sess.get("running"):
                    break
                _rtm_emit(sid, "agent_say", {"role": role, "partial": part, "topic": topic})
                time.sleep(0.1)  # 减少推送间隔，提高流畅度

            # 该角色发言完成标记
            _rtm_emit(sid, "agent_say_done", {"role": role, "topic": topic})

        # 会议结束事件（初版 Demo）
        _rtm_emit(sid, "end_meeting", {})
        sess["running"] = False

    t = threading.Thread(target=worker, daemon=True, name=f"rtm-orchestrator-{sid}")
    sess["thread"] = t
    t.start()


def _safe_read_json(p: Path) -> Dict[str, Any]:
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _list_meeting_json_files(limit: int = 50) -> List[Path]:
    if not MEETINGS_DIR.exists():
        return []
    files = sorted(
        MEETINGS_DIR.glob("MTG-*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    return files[:limit]


def _summarize_meeting(m: Dict[str, Any]) -> Dict[str, Any]:
    sec = m.get("sections") or {}
    info = sec.get("会议信息") or {}
    actions = sec.get("行动项与决策") or []
    # 兜底：有些历史记录未正确解析“项目目录”，尝试从原始 markdown 中回填
    project_dir = info.get("项目目录")
    if not project_dir:
        md = (sec.get("markdown") or "")
        # 查找 “- 项目目录：xxx” 的行
        for line in md.splitlines():
            line = line.strip()
            if line.startswith("- 项目目录") and "：" in line:
                try:
                    project_dir = line.split("：", 1)[1].strip()
                except Exception:
                    project_dir = None
                break
    # 再兜底：根据“项目”名称映射到已知目录（仅 03-dev）
    if not project_dir:
        proj_name = (info.get("项目") or "").strip()
        name_map = {
            "DeWatermark AI": ["03-dev/001-dewatermark-ai"],
            "JS001-meetingroom": ["03-dev/JS001-meetingroom"],
            "YDS-Playground": ["03-dev/YDS-Playground"],
        }
        candidates = name_map.get(proj_name, [])
        for cand in candidates:
            cand_path = REPO_ROOT / cand.replace("/", os.sep)
            if cand_path.exists():
                project_dir = cand
                break
        if not project_dir and candidates:
            project_dir = f"未找到（期望：{candidates[0]}）"
    pri_cnt = {"高": 0, "中": 0, "低": 0}
    for it in actions:
        pri = (it.get("优先级") or "").strip()
        if pri in pri_cnt:
            pri_cnt[pri] += 1
    return {
        "base_name": m.get("base_name"),
        "created_at": m.get("created_at"),
        "meeting_type": info.get("会议类型"),
        "project": info.get("项目"),
        "participants": info.get("参会角色") or [],
        "agenda": info.get("议程") or [],
        "project_dir": project_dir,
        "actions_count": len(actions),
        "priority_count": pri_cnt,
    }


@app.route("/")
def index():
    """返回前端主页"""
    # 强制输出到控制台
    import sys
    sys.stdout.write("=== INDEX FUNCTION CALLED ===\n")
    sys.stdout.flush()
    
    print(f"[DEBUG] 访问首页，UI_DIR: {UI_DIR}")
    index_file = UI_DIR / "index.html"
    print(f"[DEBUG] index.html 路径: {index_file}")
    print(f"[DEBUG] index.html 存在: {index_file.exists()}")
    
    if index_file.exists():
        return send_from_directory(str(UI_DIR), "index.html")
    else:
        return f"错误：找不到 {index_file}", 404


@app.route("/assets/<path:filename>")
def static_files(filename):
    """提供静态文件服务（限定在 /assets 前缀，避免与 /mcp 与 /api 路由冲突）"""
    # 直接委托给 send_from_directory；如不存在，Flask 将返回 404
    try:
        return send_from_directory(str(UI_DIR), filename)
    except Exception:
        # 记录诊断信息，便于定位路径问题
        try:
            sys.stdout.write(f"[Static] Not found: {UI_DIR} / {filename}\n")
        except Exception:
            pass
        abort(404)


@app.route("/<path:filename>")
def static_root(filename):
    """提供根级静态文件（例如 /app.js, /styles.css），规避与 /api、/mcp 路由的冲突"""
    # 避免拦截 API 或 MCP 路由
    if filename.startswith("api/") or filename.startswith("mcp/"):
        abort(404)
    # 避免与 /assets 重复处理，让 /assets 由上面的专用路由处理
    if filename.startswith("assets/"):
        abort(404)
    try:
        return send_from_directory(str(UI_DIR), filename)
    except Exception:
        try:
            sys.stdout.write(f"[StaticRoot] Not found: {UI_DIR} / {filename}\n")
        except Exception:
            pass
        abort(404)


@app.route("/api/meetings", methods=["GET"])
def api_list_meetings():
    items: List[Dict[str, Any]] = []
    for p in _list_meeting_json_files():
        data = _safe_read_json(p)
        if data:
            items.append(_summarize_meeting(data))
    return jsonify({"ok": True, "data": items})


@app.route("/api/meetings/<base>", methods=["GET"])
def api_get_meeting(base: str):
    if not base.startswith("MTG-"):
        base = f"MTG-{base}"
    p = MEETINGS_DIR / f"{base}.json"
    if not p.exists():
        return jsonify({"ok": False, "error": "not_found"}), 404
    return jsonify(_safe_read_json(p))


@app.route("/api/meetings/<base>/md", methods=["GET"])
def api_get_meeting_md(base: str):
    if not base.startswith("MTG-"):
        base = f"MTG-{base}"
    p = MEETINGS_DIR / f"{base}.md"
    if not p.exists():
        return jsonify({"ok": False, "error": "not_found"}), 404
    return send_from_directory(str(MEETINGS_DIR), f"{base}.md", mimetype="text/markdown; charset=utf-8")


# =====================
#   会议室预订 API
# =====================

# 模拟会议室数据存储
MEETING_ROOMS = [
    {
        "id": 1,
        "name": "会议室A-301",
        "capacity": 10,
        "location": "A栋3楼",
        "facilities": {
            "projector": True,
            "whiteboard": True,
            "videoConference": True,
            "wifi": True
        },
        "available": True
    },
    {
        "id": 2,
        "name": "会议室A-302", 
        "capacity": 6,
        "location": "A栋3楼",
        "facilities": {
            "projector": False,
            "whiteboard": True,
            "videoConference": False,
            "wifi": True
        },
        "available": True
    },
    {
        "id": 3,
        "name": "大会议室B-201",
        "capacity": 20,
        "location": "B栋2楼",
        "facilities": {
            "projector": True,
            "whiteboard": True,
            "videoConference": True,
            "wifi": True
        },
        "available": True
    },
    {
        "id": 4,
        "name": "小会议室C-101",
        "capacity": 4,
        "location": "C栋1楼",
        "facilities": {
            "projector": False,
            "whiteboard": True,
            "videoConference": False,
            "wifi": True
        },
        "available": True
    }
]

# 模拟预订数据存储
BOOKINGS_STORE = []


@app.route("/api/search-rooms", methods=["POST"])
def api_search_rooms():
    """搜索可用会议室"""
    try:
        data = request.get_json() or {}
        date = data.get("date")
        timezone = data.get("timezone")
        start_time = data.get("startTime")
        end_time = data.get("endTime")
        location = data.get("location")
        floor = data.get("floor")
        
        # 验证必填字段
        if not all([date, timezone, start_time, end_time, location, floor]):
            return jsonify({
                "success": False,
                "message": "请填写所有必填字段"
            }), 400
        
        # 根据条件筛选会议室
        available_rooms = []
        for room in MEETING_ROOMS:
            # 检查位置匹配
            if location and location not in room["location"]:
                continue
            
            # 检查楼层匹配
            if floor and floor not in room["location"]:
                continue
                
            # 检查时间冲突（简化版本，实际应该检查数据库）
            has_conflict = False
            for booking in BOOKINGS_STORE:
                if (
                    booking["roomId"] == room["id"]
                    and booking["date"] == date
                    and booking["status"] == "confirmed"
                ):
                    # 检查时间重叠
                    booking_start = booking["startTime"]
                    booking_end = booking["endTime"]
                    if not (end_time <= booking_start or start_time >= booking_end):
                        has_conflict = True
                        break
            
            if not has_conflict and room["available"]:
                available_rooms.append(room)
        
        return jsonify({
            "success": True,
            "rooms": available_rooms
        })
        
    except Exception as e:
        print(f"[API] 搜索会议室失败: {e}")
        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500


@app.route("/api/book-room", methods=["POST"])
def api_book_room():
    """预订会议室"""
    try:
        data = request.get_json() or {}
        
        # 验证必填字段
        required_fields = ["roomId", "roomName", "title", "date", "startTime", "endTime"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"缺少必填字段: {field}"
                }), 400
        
        # 检查会议室是否存在
        room = next((r for r in MEETING_ROOMS if r["id"] == data["roomId"]), None)
        if not room:
            return jsonify({
                "success": False,
                "message": "会议室不存在"
            }), 404
        
        # 检查时间冲突
        for booking in BOOKINGS_STORE:
            if (
                booking["roomId"] == data["roomId"]
                and booking["date"] == data["date"]
                and booking["status"] == "confirmed"
            ):
                booking_start = booking["startTime"]
                booking_end = booking["endTime"]
                if not (data["endTime"] <= booking_start or data["startTime"] >= booking_end):
                    return jsonify({
                        "success": False,
                        "message": "该时间段已被预订"
                    }), 409
        
        # 创建预订记录
        booking = {
            "id": len(BOOKINGS_STORE) + 1,
            "roomId": data["roomId"],
            "roomName": data["roomName"],
            "title": data["title"],
            "agenda": data.get("agenda", ""),
            "date": data["date"],
            "timezone": data.get("timezone", "Asia/Shanghai"),
            "startTime": data["startTime"],
            "endTime": data["endTime"],
            "location": data.get("location", ""),
            "floor": data.get("floor", ""),
            "attendees": data.get("attendees", []),
            "status": "confirmed",
            "createdAt": time.time(),
            "organizer": "current_user@example.com"  # 实际应该从认证信息获取
        }
        
        BOOKINGS_STORE.append(booking)
        
        # 通过WebSocket广播预订事件
        try:
            socketio.emit('room_booked', {
                'booking': booking,
                'timestamp': time.time()
            })
        except Exception:
            pass
        
        return jsonify({
            "success": True,
            "booking": booking,
            "message": "会议室预订成功"
        })
        
    except Exception as e:
        print(f"[API] 预订会议室失败: {e}")
        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500

 
@app.route("/api/my-bookings", methods=["GET"])
def api_my_bookings():
    """获取我的预订记录"""
    try:
        # 实际应该根据用户认证信息筛选
        user_bookings = [b for b in BOOKINGS_STORE if b.get("organizer") == "current_user@example.com"]
        
        # 按创建时间倒序排列
        user_bookings.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
        
        return jsonify({
            "success": True,
            "bookings": user_bookings
        })
        
    except Exception as e:
        print(f"[API] 获取预订记录失败: {e}")
        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500

 
@app.route("/api/room-status", methods=["GET"])
def api_room_status():
    """获取会议室状态"""
    try:
        # 此处无需 current_time，避免未使用变量警告
        room_status = []
        
        for room in MEETING_ROOMS:
            status_info = {
                "id": room["id"],
                "name": room["name"],
                "status": "available",
                "currentMeeting": None,
                "nextMeeting": None
            }
            
            # 查找当前和下一个会议
            today = time.strftime("%Y-%m-%d")
            room_bookings = [
                b for b in BOOKINGS_STORE 
                if b["roomId"] == room["id"] and b["date"] == today and b["status"] == "confirmed"
            ]
            
            # 按时间排序
            room_bookings.sort(key=lambda x: x["startTime"])
            
            current_hour = int(time.strftime("%H"))
            current_minute = int(time.strftime("%M"))
            current_time_str = f"{current_hour:02d}:{current_minute:02d}"
            
            for booking in room_bookings:
                start_time = booking["startTime"]
                end_time = booking["endTime"]
                
                # 检查是否是当前会议
                if start_time <= current_time_str <= end_time:
                    status_info["status"] = "occupied"
                    status_info["currentMeeting"] = {
                        "title": booking["title"],
                        "startTime": start_time,
                        "endTime": end_time,
                        "organizer": booking.get("organizer", "")
                    }
                # 检查是否是下一个会议
                elif start_time > current_time_str and not status_info["nextMeeting"]:
                    status_info["nextMeeting"] = {
                        "title": booking["title"],
                        "startTime": start_time,
                        "endTime": end_time
                    }
            
            # 模拟维护状态
            if room["id"] == 5:  # 假设ID为5的会议室在维护
                status_info["status"] = "maintenance"
                status_info["currentMeeting"] = None
                status_info["nextMeeting"] = None
            
            room_status.append(status_info)
        
        return jsonify({
            "success": True,
            "rooms": room_status
        })
        
    except Exception as e:
        print(f"[API] 获取会议室状态失败: {e}")
        return jsonify({
            "success": False,
            "message": "服务器内部错误"
        }), 500

 
def _load_external_models_cfg() -> Dict[str, Any]:
    """仅从新标准路径加载 external_models.json 配置。"""
    cfg_path = REPO_ROOT / "01-struc" / "0B-general-manager" / "config" / "external_models.json"
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f).get("external_models_config", {})
    except Exception:
        return {}


def _load_external_env_vars() -> Dict[str, str]:
    """读取 external_models.json 中的 environment_variables（仅新标准路径）。"""
    cfg_path = REPO_ROOT / "01-struc" / "0B-general-manager" / "config" / "external_models.json"
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        ev = data.get("environment_variables") or {}
        # 统一字符串化
        return {str(k): str(v) for k, v in ev.items() if isinstance(k, str)}
    except Exception:
        return {}

 
def _http_get_json(url: str, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


# =====================
#   文档共享治理（RBAC + path_restrictions）
# =====================

# 权限配置路径（YAML）
# 权限配置路径（改为统一配置目录 config/security/permission.yaml）
PERMISSION_YAML_PATH = REPO_ROOT / "config" / "security" / "permission.yaml"
_PERMISSION_CACHE: Dict[str, Any] = {"mtime": None, "cfg": {}}

 
def _load_permission_cfg(force: bool = False) -> Dict[str, Any]:
    """按需加载并缓存 permission.yaml。
    - 若文件不存在或解析失败，返回空配置（默认拒绝）。
    - 使用 mtime 控制缓存刷新。
    """
    mtime = None
    try:
        mtime = PERMISSION_YAML_PATH.stat().st_mtime
    except Exception:
        pass
    cache_mtime = _PERMISSION_CACHE.get("mtime")
    if force or (mtime and mtime != cache_mtime):
        try:
            if yaml is None:
                raise RuntimeError("PyYAML not available")
            with PERMISSION_YAML_PATH.open("r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            _PERMISSION_CACHE["cfg"] = (cfg or {})
            _PERMISSION_CACHE["mtime"] = mtime
        except Exception:
            _PERMISSION_CACHE["cfg"] = {}
            _PERMISSION_CACHE["mtime"] = mtime
    return _PERMISSION_CACHE.get("cfg") or {}

 
def _ensure_audit_dir() -> Path:
    """确定审计输出目录：
    - 优先使用 permission.yaml 的 audit.output_path（支持相对仓库路径或绝对路径）；
    - 若未配置或解析失败，回退到新标准：01-struc/0B-general-manager/logs/audit_trails。
    """
    # 默认新标准目录
    default_dir = REPO_ROOT / "01-struc" / "0B-general-manager" / "logs" / "audit_trails"
    try:
        cfg = _load_permission_cfg() or {}
        audit_cfg = (cfg.get("audit") or {})
        out = (audit_cfg.get("output_path") or "").strip()
        if out:
            p = Path(out)
            # 兼容相对路径：统一相对仓库根目录
            if not p.is_absolute():
                p = REPO_ROOT / p
            d = p
        else:
            d = default_dir
    except Exception:
        d = default_dir

    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d

 
def _audit_log(event: str, detail: Dict[str, Any]) -> None:
    """写入审计日志（JSON Lines）。"""
    d = _ensure_audit_dir()
    p = d / "meetingroom_docs_share.jsonl"
    rec = dict(detail or {})
    rec.setdefault("event", event)
    rec.setdefault("ts", time.time())
    try:
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

 
def _is_role_allowed_for_endpoint(endpoint: str, role: str) -> bool:
    """检查角色是否允许访问端点。遵循 api_access.endpoint_restrictions。"""
    cfg = _load_permission_cfg()
    eperm = ((cfg.get("api_access") or {}).get("endpoint_restrictions") or {})
    rules = eperm.get(endpoint)
    if not rules:
        # 未配置端点限制时遵循默认拒绝策略
        return False
    allowed = rules.get("allowed_roles") or []
    if "*" in allowed:
        return True
    return role in allowed

 
def _match_path(pattern: str, path: str) -> bool:
    """Windows 环境下的通配符匹配。统一大小写与分隔符。"""
    pat = os.path.normcase(pattern or "")
    p = os.path.normcase(path or "")
    pat = pat.replace("/", os.sep)
    p = p.replace("/", os.sep)
    try:
        return fnmatch.fnmatch(p, pat)
    except Exception:
        return False

 
def _check_docs_share_permission(role: str, path: str) -> (bool, str):
    """检查文档共享权限：角色、白名单与黑名单。
    返回 (ok, reason)。
    """
    cfg = _load_permission_cfg()
    meetingroom = ((cfg.get("resource_permissions") or {}).get("meetingroom") or {})
    docs_cfg = (meetingroom.get("docs") or {})
    whitelist = docs_cfg.get("whitelist_paths") or []
    blacklist = docs_cfg.get("blacklist_paths") or []
    share_ops = ((docs_cfg.get("operations") or {}).get("share") or {})
    allowed_roles = share_ops.get("allowed_roles") or []
    # 角色校验
    if role not in allowed_roles:
        return False, "role_not_allowed"
    # 路径统一与校验
    abs_path = path
    try:
        abs_path = str(Path(path).resolve())
    except Exception:
        abs_path = str(path)
    for b in blacklist:
        if _match_path(b, abs_path):
            return False, "path_blacklisted"
    wh_ok = False
    for w in whitelist:
        if _match_path(w, abs_path):
            wh_ok = True
            break
    if not wh_ok:
        return False, "path_not_in_whitelist"
    return True, "ok"


@app.route("/mcp/docs/share", methods=["POST"])
def mcp_docs_share():
    """文档共享端点（MVP）：
    - 请求体：{ role, path, title?, notes? }
    - 权限：api_access.endpoint_restrictions + meetingroom.docs.operations.share + path_white/blacklist
    - 行为：仅返回共享元数据并通过 WebSocket 广播事件，不做实际文件复制。
    """
    payload = request.get_json(force=True, silent=True) or {}
    role = _resolve_effective_role(payload.get("role") or "")
    path = (payload.get("path") or "").strip()
    title = (payload.get("title") or "").strip()
    notes = (payload.get("notes") or "").strip()
    room_id = (
        payload.get("room_id")
        or request.args.get("room_id")
        or "default"
    ).strip()
    if not role or not path:
        return jsonify({"ok": False, "error": "missing_role_or_path"}), 400

    # 端点访问角色限制
    if not _is_role_allowed_for_endpoint("/mcp/docs/*", role):
        _audit_log("docs_share_denied", {"role": role, "path": path, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403

    # 资源与路径权限
    ok, reason = _check_docs_share_permission(role=role, path=path)
    if not ok:
        _audit_log("docs_share_denied", {"role": role, "path": path, "reason": reason})
        return jsonify({"ok": False, "error": reason}), 403

    share_id = uuid.uuid4().hex
    meta = {
        "id": share_id,
        "role": role,
        "path": path,
        "title": title,
        "notes": notes,
    }
    # 通知前端（如有连接）
    try:
        socketio.emit("docs_shared", {"share": meta}, broadcast=True)
    except Exception:
        pass
    try:
        emit_mcp_event("docs_shared", {"share": meta})
    except Exception:
        pass
    # 广播严格版MCP消息（docs.share）
    try:
        # 尝试提取文件元数据（如不可用则填充默认）
        file_name = Path(path).name
        file_type = (os.path.splitext(file_name)[1] or ".").lstrip(".") or "unknown"
        file_size = 0
        file_hash = ""
        msg = MCPMessageBuilder.create_docs_share(
            room_id=room_id,
            sender=AgentInfo(id=role, role=role, display_name=role),
            file_path=path,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            file_hash=file_hash,
            permissions="read"
        )
        emit_mcp_message(msg)
    except Exception:
        pass
    _audit_log("docs_share", {"role": role, "path": path, "status": "granted", "id": share_id})
    return jsonify({"ok": True, "share": meta})


@app.route("/mcp/docs/revoke", methods=["POST"])
def mcp_docs_revoke():
    """撤销共享（MVP）：
    - 请求体：{ role, id?, path? }
    - 权限：meetingroom.docs.operations.revoke.allowed_roles
    - 行为：广播撤销事件，记录审计，不做实际文件删除。
    """
    payload = request.get_json(force=True, silent=True) or {}
    role = (payload.get("role") or "").strip()
    share_id = (payload.get("id") or "").strip()
    path = (payload.get("path") or "").strip()
    if not role:
        return jsonify({"ok": False, "error": "missing_role"}), 400
    # 端点访问角色限制
    if not _is_role_allowed_for_endpoint("/mcp/docs/*", role):
        _audit_log("docs_revoke_denied", {"role": role, "path": path, "id": share_id, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    # 资源操作权限
    cfg = _load_permission_cfg()
    revoke_roles = (
        ((cfg.get("resource_permissions") or {}).get("meetingroom") or {})
        .get("docs", {})
        .get("operations", {})
        .get("revoke", {})
        .get("allowed_roles", [])
    )
    if role not in revoke_roles:
        _audit_log("docs_revoke_denied", {"role": role, "path": path, "id": share_id, "reason": "role_not_allowed"})
        return jsonify({"ok": False, "error": "role_not_allowed"}), 403
    meta = {"id": share_id, "path": path, "role": role}
    try:
        socketio.emit("docs_revoked", {"share": meta}, broadcast=True)
    except Exception:
        pass
    try:
        emit_mcp_event("docs_revoked", {"share": meta})
    except Exception:
        pass
    _audit_log("docs_revoke", {"role": role, "path": path, "status": "granted", "id": share_id})
    return jsonify({"ok": True, "revoked": meta})


# =====================
#   LM（LongMemory）接口（MVP）
# =====================

@app.route("/mcp/lm/start", methods=["POST"])
def mcp_lm_start():
    """启动LM组件：{ role, component: reminder|monitor }
    - 权限：api_access.endpoint_restrictions("/mcp/lm/*")
    - 行为：懒加载模块并启动监控线程
    """
    payload = request.get_json(force=True, silent=True) or {}
    role = (payload.get("role") or "").strip()
    component = (payload.get("component") or "").strip().lower()
    if not role or component not in ("reminder", "monitor"):
        return jsonify({"ok": False, "error": "missing_role_or_component"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/lm/*", role):
        _audit_log("lm_start_denied", {"role": role, "component": component, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403

    mods = _ensure_lm_loaded()
    if component == "reminder":
        if not mods.get("reminder"):
            return jsonify({"ok": False, "error": "module_not_found"}), 404
        if _LM_INSTANCES.get("reminder") is None:
            try:
                inst = mods["reminder"].ProactiveReminder(config_path=str(reminder_cfg))
                try:
                    inst.memory_path = str(storage_path)
                    if hasattr(inst, "load_memory_data"):
                        inst.load_memory_data()
                except Exception:
                    pass
                inst.start_monitoring()
                _LM_INSTANCES["reminder"] = inst
            except Exception as e:
                _audit_log("lm_start_failed", {"role": role, "component": component, "error": str(e)})
                return jsonify({"ok": False, "error": "start_failed", "detail": str(e)}), 500
    elif component == "monitor":
        if not mods.get("monitor"):
            return jsonify({"ok": False, "error": "module_not_found"}), 404
        if _LM_INSTANCES.get("monitor") is None:
            try:
                inst = mods["monitor"].IntelligentMonitor(config_path=str(monitor_cfg))
                try:
                    inst.memory_path = str(storage_path)
                    if hasattr(mods["monitor"], "LearningEngine"):
                        inst.learning_engine = mods["monitor"].LearningEngine(inst.memory_path)
                except Exception:
                    pass
                inst.start_monitoring()
                _LM_INSTANCES["monitor"] = inst
            except Exception as e:
                _audit_log("lm_start_failed", {"role": role, "component": component, "error": str(e)})
                return jsonify({"ok": False, "error": "start_failed", "detail": str(e)}), 500

    meta = {"component": component, "status": "running"}
    emit_mcp_event("lm_started", {"meta": meta, "by": role})
    _audit_log("lm_start", {"role": role, "component": component, "status": "granted"})
    return jsonify({"ok": True, "meta": meta, "status": _lm_status()})


@app.route("/mcp/lm/stop", methods=["POST"])
def mcp_lm_stop():
    payload = request.get_json(force=True, silent=True) or {}
    role = (payload.get("role") or "").strip()
    component = (payload.get("component") or "").strip().lower()
    if not role or component not in ("reminder", "monitor"):
        return jsonify({"ok": False, "error": "missing_role_or_component"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/lm/*", role):
        _audit_log("lm_stop_denied", {"role": role, "component": component, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    inst = _LM_INSTANCES.get(component)
    if not inst:
        return jsonify({"ok": False, "error": "not_running"}), 400
    try:
        if hasattr(inst, "stop_monitoring"):
            inst.stop_monitoring()
        _LM_INSTANCES[component] = None
    except Exception as e:
        _audit_log("lm_stop_failed", {"role": role, "component": component, "error": str(e)})
        return jsonify({"ok": False, "error": "stop_failed", "detail": str(e)}), 500
    emit_mcp_event("lm_stopped", {"component": component, "by": role})
    _audit_log("lm_stop", {"role": role, "component": component, "status": "granted"})
    return jsonify({"ok": True, "component": component, "status": _lm_status()})


@app.route("/mcp/lm/status", methods=["GET"])
def mcp_lm_status():
    role = (request.args.get("role") or "").strip()
    if not role:
        return jsonify({"ok": False, "error": "missing_role"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/lm/*", role):
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    status = _lm_status()
    return jsonify({"ok": True, "status": status, "lm_dir": str(LM_DIR)})


@app.route("/mcp/status", methods=["GET"])
def mcp_status():
    """系统聚合状态（公开）。"""
    uptime = time.time() - START_TIME
    shimmy = {
        "available": False,
        "preferred_backend": os.environ.get("PREFERRED_BACKEND") or "auto",
    }
    try:
        # 读取 external_models 配置以便报告默认模型
        base_url, v1, model_id = _get_shimmy_base_and_v1()
        shimmy["base_url"] = base_url
        shimmy["v1"] = v1
        shimmy["model_id"] = model_id
        shimmy["available"] = _shimmy_can_infer(base_url, model_id)
    except Exception:
        pass
    return jsonify({
        "ok": True,
        "uptime_sec": int(uptime),
        "ui_dir": str(UI_DIR),
        "lm": _lm_status(),
        "shimmy": shimmy,
    })


@app.route("/mcp/routes", methods=["GET"])
def mcp_routes():
    role = (request.args.get("role") or "").strip()
    if not role or not _is_role_allowed_for_endpoint("/admin/*", role):
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    routes = []
    try:
        for r in app.url_map.iter_rules():
            routes.append({
                "rule": str(r),
                "endpoint": r.endpoint,
                "methods": sorted(list(r.methods or [])),
            })
    except Exception:
        pass
    return jsonify({"ok": True, "routes": routes})


@app.route("/mcp/audit/compress", methods=["POST"])
def mcp_audit_compress():
    payload = request.get_json(force=True, silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role or not _is_role_allowed_for_endpoint("/mcp/audit/*", role):
        _audit_log("audit_compress_denied", {"role": role or "", "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    # 压缩7天前的 JSONL 文件
    base = _ensure_audit_dir()
    now = time.time()
    cutoff = now - 7 * 24 * 3600
    processed = []
    import gzip
    for p in base.glob("*.jsonl"):
        try:
            mtime = p.stat().st_mtime
            if mtime < cutoff:
                gz_path = p.with_suffix(p.suffix + ".gz")
                with p.open("rb") as fin, gzip.open(str(gz_path), "wb") as fout:
                    fout.write(fin.read())
                # 可选：压缩后删除原始文件
                try:
                    p.unlink()
                except Exception:
                    pass
                processed.append(p.name)
        except Exception:
            pass
    _audit_log("audit_compress", {"role": role, "processed": processed, "count": len(processed)})
    return jsonify({"ok": True, "processed": processed, "count": len(processed)})


@app.route("/mcp/lm/report_activity", methods=["POST"])
def mcp_lm_report_activity():
    payload = request.get_json(force=True, silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role or not _is_role_allowed_for_endpoint("/mcp/lm/*", role):
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    activity_type = (payload.get("activity_type") or "").strip()
    details = payload.get("details") or {}
    inst = _LM_INSTANCES.get("reminder")
    if not inst:
        return jsonify({"ok": False, "error": "reminder_not_running"}), 400
    try:
        inst.report_activity(activity_type, details)
        emit_mcp_event("lm_activity", {"type": activity_type, "details": details, "by": role})
        _audit_log("lm_activity", {"role": role, "activity_type": activity_type})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": "report_failed", "detail": str(e)}), 500


@app.route("/mcp/lm/report_error", methods=["POST"])
def mcp_lm_report_error():
    payload = request.get_json(force=True, silent=True) or {}
    role = (payload.get("role") or "").strip()
    if not role or not _is_role_allowed_for_endpoint("/mcp/lm/*", role):
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    error_type = (payload.get("error_type") or "").strip() or "unknown"
    error_message = (payload.get("error_message") or "").strip()
    context = payload.get("context") or {}
    inst = _LM_INSTANCES.get("reminder")
    if not inst:
        return jsonify({"ok": False, "error": "reminder_not_running"}), 400
    try:
        inst.report_error(error_type, error_message, context)
        emit_mcp_event(
            "lm_error",
            {
                "type": error_type,
                "message": error_message,
                "context": context,
                "by": role,
            },
            level="warning",
        )
        _audit_log("lm_error", {"role": role, "error_type": error_type})
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": "report_failed", "detail": str(e)}), 500


@app.route("/api/models", methods=["GET"])
def api_list_models():
    cfg = _load_external_models_cfg()
    shim = (cfg.get("models") or {}).get("shimmy") or {}
    ollama = (cfg.get("models") or {}).get("ollama") or {}
    hosts = set()
    # Shimmy 主机与实例
    if shim.get("host"):
        hosts.add(shim["host"])  # e.g. http://127.0.0.1:11436 或含 /v1
    for _, h in (shim.get("instances") or {}).items():
        if h:
            hosts.add(h)
    # Ollama 主机
    if ollama.get("host"):
        hosts.add(ollama["host"])  # e.g. http://127.0.0.1:11434 或含 /v1
    else:
        # 兜底：常见本地 Ollama 默认地址
        for h in (
            "http://127.0.0.1:11434/v1",
            "http://127.0.0.1:11434",
            "http://localhost:11434/v1",
            "http://localhost:11434",
        ):
            hosts.add(h)

    def _collect_from_host(base: str) -> List[str]:
        base = (base or "").rstrip("/")
        ids: List[str] = []
        # 统一尝试多种端点，兼容是否已带 /v1
        candidates = [
            "/v1/models",
            "/models",
            "/api/models",
            "/api/tags",  # Ollama 传统端点
        ]
        for path in candidates:
            # 避免出现 /v1/v1/models 的重复，直接拼接由服务器容错
            data = _http_get_json(base + path, timeout=2.0)
            if not data:
                continue
            if isinstance(data, dict) and isinstance(data.get("data"), list):
                ids.extend([m.get("id") for m in data.get("data") if isinstance(m, dict) and m.get("id")])
                if ids:
                    break
            # Ollama /api/tags 返回 { models: [{ name: "qwen2:0.5b" }, ...] }
            if isinstance(data, dict) and isinstance(data.get("models"), list):
                ids.extend([m.get("name") for m in data.get("models") if isinstance(m, dict) and m.get("name")])
                if ids:
                    break
        return ids

    models: List[str] = []
    for h in hosts:
        try:
            models.extend(_collect_from_host(h))
        except Exception:
            continue
    # 去重并按字母排序
    uniq = sorted(list({m for m in models if m}))
    return jsonify({"ok": True, "data": uniq})


@app.route("/api/test_llm", methods=["GET"])
def api_test_llm():
    """简单连通性测试：
    - ?host=http://127.0.0.1:11436
    - 或 ?service=shimmy/ollama（自动读取 external_models.json 的默认 host）
    """
    host = (request.args.get("host") or "").strip().rstrip("/")
    service = (request.args.get("service") or "").strip().lower()
    cfg = _load_external_models_cfg()
    env_vars = _load_external_env_vars()
    hosts_to_try: List[str] = []
    if host:
        hosts_to_try = [host]
    else:
        if service == "shimmy":
            shim = (cfg.get("models") or {}).get("shimmy") or {}
            default_host = (shim.get("host") or "").rstrip("/")
            if default_host:
                hosts_to_try.append(default_host)
            for _, h in (shim.get("instances") or {}).items():
                h = (h or "").strip().rstrip("/")
                if h:
                    hosts_to_try.append(h)
        elif service == "ollama":
            oll = (cfg.get("models") or {}).get("ollama") or {}
            default_host = (
                oll.get("host")
                or os.environ.get("OLLAMA_HOST")
                or env_vars.get("OLLAMA_HOST")
                or ""
            ).rstrip("/")
            if default_host:
                hosts_to_try.append(default_host)
            else:
                # 兜底：常见本地 Ollama 默认地址
                hosts_to_try.extend([
                    "http://127.0.0.1:11434/v1",
                    "http://127.0.0.1:11434",
                    "http://localhost:11434/v1",
                    "http://localhost:11434",
                ])

    if not hosts_to_try:
        return jsonify({"ok": False, "error": "missing host"}), 400

    # 依次尝试每个候选 host，探测常见模型列表端点
    tried: List[str] = []
    candidates = [
        "/v1/models",
        "/models",
        "/api/models",
        "/api/tags",
    ]
    for h in hosts_to_try:
        for path in candidates:
            tried.append(h + path)
            data = _http_get_json(h + path, timeout=2.0)
            if data:
                return jsonify({
                    "ok": True,
                    "endpoint": path,
                    "host": h,
                    "raw": data,
                })
    return jsonify({
        "ok": False,
        "error": "unreachable or unknown schema",
        "hosts_tried": hosts_to_try,
        "paths": candidates,
    }), 502


@app.route("/api/health_models", methods=["GET"])
def api_health_models():
    """聚合返回 Shimmy 与 Ollama 的可达状态及当前默认模型建议。"""
    cfg = _load_external_models_cfg()
    env_vars = _load_external_env_vars()

    # Shimmy
    shim_base, _ = _get_shimmy_base_and_v1()
    shim_ok = _check_host_ok(shim_base) if shim_base else False

    # Ollama
    oll = (cfg.get("models") or {}).get("ollama") or {}
    oll_host = (
        (
            oll.get("host")
            or os.environ.get("OLLAMA_HOST")
            or env_vars.get("OLLAMA_HOST")
            or "http://127.0.0.1:11434"
        )
    ).rstrip("/")
    oll_ok = _check_host_ok(oll_host)

    defaults = _pick_default_models()
    return jsonify({
        "ok": True,
        "preferredBackend": PREFERRED_BACKEND,
        "shimmy": {"ok": bool(shim_ok), "host": shim_base},
        "ollama": {"ok": bool(oll_ok), "host": oll_host},
        "defaultModels": defaults,
    })


@app.route("/api/run", methods=["POST"])
def api_run_meeting():
    payload = request.get_json(force=True, silent=True) or {}
    meeting = (payload.get("meeting") or "daily").strip()
    project = (payload.get("project") or "DeWatermark AI").strip()
    # 模型优先策略：默认走 Shimmy（更轻、更快），不可达时自动降级到 Ollama
    model = (payload.get("model") or "").strip()
    if not model:
        if PREFERRED_BACKEND == "shimmy":
            # 尝试确保 Shimmy 启动
            _ensure_shimmy_running(wait_secs=8.0)
        defaults = _pick_default_models()
        model = defaults.get("offline") or "qwen2:0.5b"
    participants = payload.get("participants") or []
    agenda = payload.get("agenda") or []
    project_id = (payload.get("projectId") or "").strip()

    # 参数组装
    cmd = [
        sys.executable,
        str(REPO_ROOT / "tools" / "agents" / "run_collab.py"),
        "--meeting", meeting,
        "--project", project,
        "--model", model,
    ]
    if participants:
        cmd += ["--participants", ", ".join(participants)]
    if agenda:
        cmd += ["--agenda", ", ".join(agenda)]
    if project_id:
        cmd += ["--project-id", project_id]

    start_ts = time.time()
    try:
        # 同步阻塞运行，返回最新会议编号
        env = os.environ.copy()
        # 避免 Windows 控制台编码问题引发 UnicodeEncodeError
        env.setdefault("PYTHONIOENCODING", "utf-8")
        # 明确指定读取编码，避免 Windows 默认控制台编码（GBK）解码 UTF-8 输出导致 UnicodeDecodeError
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=None,
            env=env,
        )
        ok = (proc.returncode == 0)
        out = (proc.stdout or "") + (proc.stderr or "")
        # 最新会议文件
        latest_json = None
        for p in _list_meeting_json_files(limit=1):
            latest_json = p.name
            break
        return jsonify({
            "ok": ok,
            "stdout": out[-2000:],
            "meeting_json": latest_json,
            "duration_sec": round(time.time() - start_ts, 2),
        }), (200 if ok else 500)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# =====================
#   实时会议（SSE）
# =====================

@app.route("/api/rtm/start", methods=["POST"])
def api_rtm_start():
    payload = request.get_json(force=True, silent=True) or {}
    # 实时会议默认：优先 Shimmy，降级 Ollaama
    model = (payload.get("model") or "").strip()
    if not model:
        if PREFERRED_BACKEND == "shimmy":
            _ensure_shimmy_running(wait_secs=8.0)
        defaults = _pick_default_models()
        model = defaults.get("rtm") or "tinyllama:latest"
    participants = payload.get("participants") or []
    agenda = payload.get("agenda") or []
    # 兜底角色
    roles = [p.strip() for p in participants if p.strip()] or ["总经理", "技术总监", "产品总监"]
    sid = uuid.uuid4().hex
    # 基础会话结构
    RTM_SESSIONS[sid] = {
        "sid": sid,
        "queue": queue.Queue(),
        "running": False,
        "roles": roles,
        "agenda": agenda,
        "model": model,
        "events": [],
        "transcript": [],
        "buffers": {},
        "started_at": time.time(),
        "ended_at": None,
        "base_name": None,
        "file_path": None,
        "saved": False,
    }
    _start_orchestrator_async(sid=sid, roles=roles, agenda=agenda, model=model)
    return jsonify({"ok": True, "sid": sid, "roles": roles, "agenda": agenda, "model": model})


@app.route("/api/rtm/stream", methods=["GET"])
def api_rtm_stream():
    sid = (request.args.get("sid") or "").strip()
    sess = RTM_SESSIONS.get(sid)
    if not sid or not sess:
        return jsonify({"ok": False, "error": "invalid_sid"}), 400

    def gen():
        # 让客户端在断线后 2s 重试连接
        yield "retry: 2000\n\n"
        q: queue.Queue = sess["queue"]
        while sess.get("running") or not q.empty():
            try:
                evt = q.get(timeout=0.5)
            except Exception:
                continue
            yield _sse_event(event=evt.get("event") or "message", data=evt.get("data") or {})
        # 尾部心跳，确保客户端正确结束
        yield _sse_event(event="stream_closed", data={"sid": sid, "ts": time.time()})

    return Response(stream_with_context(gen()), mimetype="text/event-stream")


@app.route("/api/rtm/say", methods=["POST"])
def api_rtm_say():
    payload = request.get_json(force=True, silent=True) or {}
    sid = (payload.get("sid") or "").strip()
    content = (payload.get("content") or "").strip()
    sess = RTM_SESSIONS.get(sid)
    if not sid or not sess:
        return jsonify({"ok": False, "error": "invalid_sid"}), 400
    if not content:
        return jsonify({"ok": False, "error": "empty_content"}), 400
    _rtm_emit(sid, "user_say", {"role": "user", "text": content})
    return jsonify({"ok": True})


@app.route("/api/rtm/end", methods=["POST"])
def api_rtm_end():
    payload = request.get_json(force=True, silent=True) or {}
    sid = (payload.get("sid") or "").strip()
    sess = RTM_SESSIONS.get(sid)
    if not sid or not sess:
        return jsonify({"ok": False, "error": "invalid_sid"}), 400
    sess["running"] = False
    _rtm_emit(sid, "end_meeting", {})
    # 结束后立即保存一次
    saved_path = _save_transcript_for_session(sid, finalize=True)
    return jsonify({"ok": True, "saved": bool(saved_path), "file": saved_path})


@app.route("/api/rtm/transcript", methods=["GET"])
def api_rtm_transcript():
    sid = (request.args.get("sid") or "").strip()
    sess = RTM_SESSIONS.get(sid)
    if not sid or not sess:
        return jsonify({"ok": False, "error": "invalid_sid"}), 400
    data = {
        "sid": sid,
        "roles": sess.get("roles") or [],
        "agenda": sess.get("agenda") or [],
        "model": sess.get("model") or "",
        "transcript": sess.get("transcript") or [],
        "events": sess.get("events") or [],
        "started_at": sess.get("started_at"),
        "ended_at": sess.get("ended_at"),
        "base_name": sess.get("base_name"),
        "file_path": sess.get("file_path"),
        "saved": bool(sess.get("saved")),
    }
    return jsonify({"ok": True, "data": data})


@app.route("/api/rtm/save", methods=["POST"])
def api_rtm_save():
    payload = request.get_json(force=True, silent=True) or {}
    sid = (payload.get("sid") or "").strip()
    sess = RTM_SESSIONS.get(sid)
    if not sid or not sess:
        return jsonify({"ok": False, "error": "invalid_sid"}), 400
    saved_path = _save_transcript_for_session(sid, finalize=False)
    return jsonify({"ok": bool(saved_path), "file": saved_path})


@app.route("/api/rtm/sessions", methods=["GET"])
def api_rtm_sessions():
    """列出当前会话的概要信息（调试用）。"""
    items: List[Dict[str, Any]] = []
    for sid, sess in RTM_SESSIONS.items():
        items.append({
            "sid": sid,
            "running": bool(sess.get("running")),
            "roles": sess.get("roles") or [],
            "agenda": sess.get("agenda") or [],
            "model": sess.get("model") or "",
            "saved": bool(sess.get("saved")),
            "base_name": sess.get("base_name"),
            "file_path": sess.get("file_path"),
            "started_at": sess.get("started_at"),
            "ended_at": sess.get("ended_at"),
        })
    return jsonify({"ok": True, "data": items})


# =====================
#   投票与语音（MCP）
# =====================

# 简易内存存储（演示用）：投票状态
VOTES_STORE: Dict[str, Any] = {}


def _votes_allowed_roles(op: str) -> List[str]:
    cfg = _load_permission_cfg()
    return (
        (((cfg.get("resource_permissions") or {}).get("meetingroom") or {}).get("votes") or {})
        .get("operations", {})
        .get(op, {})
        .get("allowed_roles", [])
    )


def _voice_allowed_roles(op: str) -> List[str]:
    cfg = _load_permission_cfg()
    return (
        (((cfg.get("resource_permissions") or {}).get("meetingroom") or {}).get("voice") or {})
        .get("operations", {})
        .get(op, {})
        .get("allowed_roles", [])
    )


@app.route("/mcp/votes/create", methods=["POST"])
def mcp_votes_create():
    """创建投票：
    - 请求体：{ role, title, options: [..], meeting_id? }
    - 权限：api_access.endpoint_restrictions + meetingroom.votes.operations.create
    - 行为：创建内存中的投票并广播事件。
    """
    payload = request.get_json(force=True, silent=True) or {}
    role = _resolve_effective_role(payload.get("role") or "")
    title = (payload.get("title") or "").strip()
    options = payload.get("options") or []
    meeting_id = (payload.get("meeting_id") or "").strip()
    room_id = (payload.get("room_id") or meeting_id or request.args.get("room_id") or "default").strip()
    if not role or not title or not isinstance(options, list) or len(options) < 2:
        return jsonify({"ok": False, "error": "missing_role_title_or_options"}), 400
    # 端点访问角色限制
    if not _is_role_allowed_for_endpoint("/mcp/votes/*", role):
        _audit_log("vote_create_denied", {"role": role, "title": title, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    # 操作权限
    if role not in _votes_allowed_roles("create"):
        _audit_log("vote_create_denied", {"role": role, "title": title, "reason": "role_not_allowed"})
        return jsonify({"ok": False, "error": "role_not_allowed"}), 403
    vid = uuid.uuid4().hex
    counts = {str(opt): 0 for opt in options}
    rec = {
        "id": vid,
        "title": title,
        "options": [str(opt) for opt in options],
        "counts": counts,
        "status": "open",
        "meeting_id": meeting_id,
        "created_by": role,
        "created_at": time.time(),
        "casts": [],
    }
    VOTES_STORE[vid] = rec
    try:
        socketio.emit("vote_created", {"vote": rec}, broadcast=True)
    except Exception:
        pass
    try:
        emit_mcp_event("vote_created", {"vote": rec})
    except Exception:
        pass
    # 广播严格版MCP消息（vote.create）
    try:
        msg = MCPMessageBuilder.create_vote(
            room_id=room_id,
            sender=AgentInfo(id=role, role=role, display_name=role),
            title=title,
            options=[str(opt) for opt in options],
            description=None,
            anonymous=False,
            quorum=0.5,
            expires_minutes=60
        )
        emit_mcp_message(msg)
    except Exception:
        pass
    _audit_log("vote_create", {"role": role, "title": title, "id": vid, "status": "granted"})
    return jsonify({"ok": True, "vote": rec})


@app.route("/mcp/votes/cast", methods=["POST"])
def mcp_votes_cast():
    """投票表决：
    - 请求体：{ role, vote_id, option, voter? }
    - 权限：api_access.endpoint_restrictions + meetingroom.votes.operations.cast
    - 行为：更新计数并广播事件。
    """
    payload = request.get_json(force=True, silent=True) or {}
    role = _resolve_effective_role(payload.get("role") or "")
    vid = (payload.get("vote_id") or "").strip()
    option = str(payload.get("option") or "").strip()
    voter = (payload.get("voter") or "").strip()
    room_id = (
        payload.get("room_id")
        or request.args.get("room_id")
        or "default"
    ).strip()
    if not role or not vid or not option:
        return jsonify({"ok": False, "error": "missing_role_vote_or_option"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/votes/*", role):
        _audit_log(
            "vote_cast_denied",
            {
                "role": role,
                "vote_id": vid,
                "option": option,
                "reason": "endpoint_role_denied",
            },
        )
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    if role not in _votes_allowed_roles("cast"):
        _audit_log(
            "vote_cast_denied",
            {
                "role": role,
                "vote_id": vid,
                "option": option,
                "reason": "role_not_allowed",
            },
        )
        return jsonify({"ok": False, "error": "role_not_allowed"}), 403
    rec = VOTES_STORE.get(vid)
    if not rec:
        return jsonify({"ok": False, "error": "vote_not_found"}), 404
    if rec.get("status") != "open":
        return jsonify({"ok": False, "error": "vote_closed"}), 400
    if option not in (rec.get("options") or []):
        return jsonify({"ok": False, "error": "invalid_option"}), 400
    counts = rec.get("counts") or {}
    counts[option] = int(counts.get(option) or 0) + 1
    rec.setdefault("casts", []).append({"option": option, "role": role, "voter": voter, "ts": time.time()})
    try:
        socketio.emit(
            "vote_cast",
            {"vote_id": vid, "option": option, "voter": voter, "counts": counts},
            broadcast=True,
        )
    except Exception:
        pass
    try:
        emit_mcp_event(
            "vote_cast",
            {"vote_id": vid, "option": option, "voter": voter, "counts": counts},
        )
    except Exception:
        pass
    # 广播严格版MCP消息（vote.cast）- 使用metadata携带计数
    try:
        from mcp_message_model import MCPMessage
        vp = VotePayload(
            proposal_id=vid,
            title=rec.get("title") or "",
            description=None,
            options=rec.get("options") or [],
            anonymous=False,
            quorum=rec.get("quorum") or 0.5,
            expires_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600))
        )
        msg = MCPMessage(
            id=f"vote-{int(time.time())}-{uuid.uuid4().hex[:8]}",
            room_id=room_id,
            channel=ChannelType.VOTE,
            event_type=EventType.VOTE_CAST,
            topic=f"rooms/{room_id}/vote/vote.cast",
            sender=AgentInfo(id=role, role=role, display_name=role),
            timestamp=time.time(),
            payload=vp,
            metadata={"counts": counts, "option": option, "voter": voter}
        )
        emit_mcp_message(msg)
    except Exception:
        pass
    _audit_log("vote_cast", {"role": role, "vote_id": vid, "option": option, "status": "granted"})
    return jsonify({"ok": True, "counts": counts, "vote": rec})


@app.route("/mcp/votes/status", methods=["GET"])
def mcp_votes_status():
    """查询投票状态：
    - 查询参数：vote_id, role
    - 权限：api_access.endpoint_restrictions（视为 view 权限）
    - 行为：返回当前计数与状态。
    """
    vid = (request.args.get("vote_id") or "").strip()
    role = (request.args.get("role") or "").strip()
    if not vid:
        return jsonify({"ok": False, "error": "missing_vote_id"}), 400
    if not role:
        return jsonify({"ok": False, "error": "missing_role"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/votes/*", role):
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    rec = VOTES_STORE.get(vid)
    if not rec:
        return jsonify({"ok": False, "error": "vote_not_found"}), 404
    return jsonify({"ok": True, "vote": rec})


@app.route("/mcp/votes/finalize", methods=["POST"])
def mcp_votes_finalize():
    """结束投票：
    - 请求体：{ role, vote_id }
    - 权限：api_access.endpoint_restrictions + meetingroom.votes.operations.finalize
    - 行为：关闭投票并广播最终结果。
    """
    payload = request.get_json(force=True, silent=True) or {}
    role = _resolve_effective_role(payload.get("role") or "")
    vid = (payload.get("vote_id") or "").strip()
    room_id = (payload.get("room_id") or request.args.get("room_id") or "default").strip()
    if not role or not vid:
        return jsonify({"ok": False, "error": "missing_role_or_vote_id"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/votes/*", role):
        _audit_log("vote_finalize_denied", {"role": role, "vote_id": vid, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    if role not in _votes_allowed_roles("finalize"):
        _audit_log("vote_finalize_denied", {"role": role, "vote_id": vid, "reason": "role_not_allowed"})
        return jsonify({"ok": False, "error": "role_not_allowed"}), 403
    rec = VOTES_STORE.get(vid)
    if not rec:
        return jsonify({"ok": False, "error": "vote_not_found"}), 404
    rec["status"] = "closed"
    try:
        socketio.emit("vote_finalized", {"vote": rec}, broadcast=True)
    except Exception:
        pass
    try:
        emit_mcp_event("vote_finalized", {"vote": rec})
    except Exception:
        pass
    # 广播严格版MCP消息（vote.finalize）
    try:
        vp = VotePayload(
            proposal_id=vid,
            title=rec.get("title") or "",
            description=None,
            options=rec.get("options") or [],
            anonymous=False,
            quorum=rec.get("quorum") or 0.5,
            expires_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600))
        )
        msg = MCPMessage(
            id=f"vote-{int(time.time())}-{uuid.uuid4().hex[:8]}",
            room_id=room_id,
            channel=ChannelType.VOTE,
            event_type=EventType.VOTE_FINALIZE,
            topic=f"rooms/{room_id}/vote/vote.finalize",
            sender=AgentInfo(id=role, role=role, display_name=role),
            timestamp=time.time(),
            payload=vp,
            metadata={"final_counts": rec.get("counts")}
        )
        emit_mcp_message(msg)
    except Exception:
        pass


@app.route("/mcp/voice/session/start", methods=["POST"])
def mcp_voice_session_start():
    """启动语音会话：返回session_id用于后续分片传输。"""
    payload = request.get_json(force=True, silent=True) or {}
    role = _resolve_effective_role(payload.get("role") or "")
    if not role:
        return jsonify({"ok": False, "error": "missing_role"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/voice/*", role):
        _audit_log("voice_session_start_denied", {"role": role, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    session_id = uuid.uuid4().hex
    try:
        emit_mcp_event("voice_session_start", {"session_id": session_id, "role": role})
    except Exception:
        pass
    return jsonify({"ok": True, "session_id": session_id})


# 简易内存存储：语音会话缓存
VOICE_SESSIONS: Dict[str, Any] = {}


@app.route("/mcp/voice/chunk", methods=["POST"])
def mcp_voice_chunk():
    """语音分片上传：服务端缓存并通过严格版MCP消息广播分片。"""
    payload = request.get_json(force=True, silent=True) or {}
    role = _resolve_effective_role(payload.get("role") or "")
    session_id = (payload.get("session_id") or "").strip()
    chunk_seq = int(payload.get("chunk_seq") or 0)
    audio_data = (payload.get("audio_data") or "").strip()
    room_id = (payload.get("room_id") or request.args.get("room_id") or "default").strip()
    if not all([role, session_id, audio_data]):
        return jsonify({"ok": False, "error": "missing_role_session_or_audio"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/voice/*", role):
        _audit_log("voice_chunk_denied", {"role": role, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    # 缓存分片
    VOICE_SESSIONS.setdefault(session_id, []).append({"seq": chunk_seq, "data": audio_data})
    try:
        msg = MCPMessageBuilder.create_voice_stream(
            room_id=room_id,
            sender=AgentInfo(id=role, role=role, display_name=role),
            session_id=session_id,
            chunk_seq=chunk_seq,
            audio_data=audio_data,
            sample_rate=16000,
            format="pcm16"
        )
        emit_mcp_message(msg)
    except Exception:
        pass
    _audit_log("voice_chunk", {"role": role, "session_id": session_id, "seq": chunk_seq, "status": "granted"})
    return jsonify({"ok": True, "session_id": session_id, "seq": chunk_seq})


@app.route("/mcp/voice/stream", methods=["POST"])
def mcp_voice_stream():
    """语音流（演示 Stub）：
    - 请求体：{ role, text, engine?, params? }
    - 权限：api_access.endpoint_restrictions + meetingroom.voice.operations.stream
    - 行为：广播事件与审计记录，不做实际 TTS 流。
    """
    payload = request.get_json(force=True, silent=True) or {}
    role = (payload.get("role") or "").strip()
    text = (payload.get("text") or "").strip()
    engine = (payload.get("engine") or "").strip() or "responsivevoice"
    params = payload.get("params") or {}
    if not role or not text:
        return jsonify({"ok": False, "error": "missing_role_or_text"}), 400
    if not _is_role_allowed_for_endpoint("/mcp/voice/*", role):
        _audit_log("voice_stream_denied", {"role": role, "reason": "endpoint_role_denied"})
        return jsonify({"ok": False, "error": "endpoint_role_denied"}), 403
    if role not in _voice_allowed_roles("stream"):
        _audit_log("voice_stream_denied", {"role": role, "reason": "role_not_allowed"})
        return jsonify({"ok": False, "error": "role_not_allowed"}), 403
    meta = {"role": role, "text": text, "engine": engine, "params": params, "ts": time.time()}
    try:
        socketio.emit(
            "voice_stream",
            {"meta": meta},
            broadcast=True,
        )
    except Exception:
        pass
    try:
        emit_mcp_event(
            "voice_stream",
            {"meta": meta},
        )
    except Exception:
        pass
    _audit_log("voice_stream", {"role": role, "length": len(text), "engine": engine, "status": "granted"})
    return jsonify({"ok": True, "meta": meta})


# ==================== YDS AI 系统新增API路由 ====================

@app.route("/yds/agents/roles", methods=["GET"])
def yds_agents_roles():
    """获取智能体角色配置"""
    try:
        print("[DEBUG] 开始获取智能体角色配置...")
        roles = agent_role_manager.get_all_roles()
        print(f"[DEBUG] 获取到 {len(roles)} 个角色")
        
        # 转换为可序列化的格式
        serializable_roles = {}
        for role, config in roles.items():
            print(f"[DEBUG] 处理角色: {role}")
            try:
                serializable_roles[role.value] = {
                    "display_name": config.display_name,
                    "description": config.description,
                    "capabilities": config.capabilities,
                    "created_at": (
                        getattr(config, 'created_at', None).isoformat()
                        if getattr(config, 'created_at', None)
                        else None
                    ),
                    "department": getattr(config, 'department', None),
                    "expertise": getattr(config, 'expertise', []),
                    "personality": getattr(config, 'personality', {}),
                    "tools_config": getattr(config, 'tools_config', {})
                }
            except Exception as e:
                print(f"[ERROR] 处理角色 {role} 时出错: {e}")
                # 尝试获取可用的属性
                available_attrs = [attr for attr in dir(config) if not attr.startswith('_')]
                print(f"[DEBUG] 配置对象可用属性: {available_attrs}")
                raise
                
        print(f"[DEBUG] 角色配置序列化成功: {len(serializable_roles)} 个角色")
        return jsonify({"ok": True, "roles": serializable_roles})
    except Exception as e:
        import traceback
        error_msg = f"获取智能体角色配置失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] 详细错误: {traceback.format_exc()}")
        return jsonify({"ok": False, "error": error_msg}), 500


@app.route("/yds/agents/assign", methods=["POST"])
def yds_agents_assign():
    """分配智能体到会议"""
    payload = request.get_json(force=True, silent=True) or {}
    meeting_id = payload.get("meeting_id")
    agent_role = payload.get("agent_role")
    user_id = payload.get("user_id")
    
    if not all([meeting_id, agent_role, user_id]):
        return jsonify({"ok": False, "error": "missing_required_fields"}), 400
    
    try:
        success = agent_role_manager.assign_agent_to_meeting(meeting_id, agent_role, user_id)
        if success:
            emit_mcp_event("agent_assigned", {
                "meeting_id": meeting_id, 
                "agent_role": agent_role, 
                "user_id": user_id
            })
            return jsonify({"ok": True})
        else:
            return jsonify({"ok": False, "error": "assignment_failed"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/meetings/create", methods=["POST"])
def yds_meetings_create():
    """创建分级会议"""
    payload = request.get_json(force=True, silent=True) or {}
    title = payload.get("title")
    level = payload.get("level")
    organizer = payload.get("organizer")
    participants = payload.get("participants", [])
    
    if not all([title, level, organizer]):
        return jsonify({"ok": False, "error": "missing_required_fields"}), 400
    
    try:
        meeting = meeting_level_manager.create_meeting(title, level, organizer, participants)
        emit_mcp_event("meeting_created", {"meeting": meeting})
        return jsonify({"ok": True, "meeting": meeting})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/meetings/<meeting_id>/agenda", methods=["POST"])
def yds_meetings_generate_agenda(meeting_id):
    """生成智能议程"""
    payload = request.get_json(force=True, silent=True) or {}
    meeting_type = payload.get("meeting_type", "regular")
    duration_minutes = payload.get("duration_minutes", 60)
    topics = payload.get("topics", [])
    
    try:
        agenda = agenda_generator.generate_agenda(meeting_type, duration_minutes, topics)
        emit_mcp_event("agenda_generated", {"meeting_id": meeting_id, "agenda": agenda})
        return jsonify({"ok": True, "agenda": agenda})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/documents/access", methods=["POST"])
def yds_documents_access():
    """文档访问权限检查"""
    payload = request.get_json(force=True, silent=True) or {}
    user_id = payload.get("user_id")
    path = payload.get("path")
    operation = payload.get("operation", "read")
    
    if not all([user_id, path]):
        return jsonify({"ok": False, "error": "missing_required_fields"}), 400
    
    try:
        allowed = document_governance.check_access(user_id, path, operation)
        if allowed:
            document_governance.log_access(user_id, path, operation, "granted")
            return jsonify({"ok": True, "access": "granted"})
        else:
            document_governance.log_access(user_id, path, operation, "denied")
            return jsonify({"ok": False, "access": "denied"}), 403
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/auth/login", methods=["POST"])
def yds_auth_login():
    """用户登录认证"""
    payload = request.get_json(force=True, silent=True) or {}
    username = payload.get("username")
    password = payload.get("password")
    
    if not all([username, password]):
        return jsonify({"ok": False, "error": "missing_credentials"}), 400
    
    try:
        token = rbac_system.authenticate_user(username, password)
        if token:
            return jsonify({"ok": True, "token": token})
        else:
            return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/voice/stt", methods=["POST"])
def yds_voice_stt():
    """语音转文字服务"""
    # 这里应该处理音频文件上传，简化为接收base64编码的音频
    payload = request.get_json(force=True, silent=True) or {}
    audio_data = payload.get("audio_data")
    service_type = payload.get("service_type", "shimmy")
    
    if not audio_data:
        return jsonify({"ok": False, "error": "missing_audio_data"}), 400
    
    try:
        # 模拟STT处理
        result = voice_service.speech_to_text(audio_data, service_type)
        emit_mcp_event("stt_completed", {"result": result})
        return jsonify({"ok": True, "text": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/voice/tts", methods=["POST"])
def yds_voice_tts():
    """文字转语音服务"""
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text")
    service_type = payload.get("service_type", "shimmy")
    voice_model = payload.get("voice_model", "default")
    
    if not text:
        return jsonify({"ok": False, "error": "missing_text"}), 400
    
    try:
        # 模拟TTS处理
        audio_url = voice_service.text_to_speech(text, service_type, voice_model)
        emit_mcp_event("tts_completed", {"audio_url": audio_url})
        return jsonify({"ok": True, "audio_url": audio_url})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/mcp/validate", methods=["POST"])
def yds_mcp_validate():
    """MCP消息验证"""
    payload = request.get_json(force=True, silent=True) or {}
    
    try:
        is_valid, errors = mcp_validator.validate_message(payload)
        return jsonify({"ok": True, "valid": is_valid, "errors": errors})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/yds/system/status", methods=["GET"])
def yds_system_status():
    """YDS AI系统状态检查"""
    try:
        print("[DEBUG] 开始获取系统状态...")
        
        # 逐个检查每个组件
        try:
            agent_roles_count = len(agent_role_manager.get_all_roles())
            print(f"[DEBUG] agent_roles: {agent_roles_count}")
        except Exception as e:
            print(f"[ERROR] agent_role_manager error: {e}")
            raise
            
        try:
            active_meetings_count = len(meeting_level_manager.active_meetings)
            print(f"[DEBUG] active_meetings: {active_meetings_count}")
        except Exception as e:
            print(f"[ERROR] meeting_level_manager error: {e}")
            raise
            
        try:
            voice_services_count = len(voice_service.services)
            print(f"[DEBUG] voice_services: {voice_services_count}")
        except Exception as e:
            print(f"[ERROR] voice_service error: {e}")
            raise
            
        try:
            rbac_users_count = len(rbac_system.users)
            print(f"[DEBUG] rbac_users: {rbac_users_count}")
        except Exception as e:
            print(f"[ERROR] rbac_system error: {e}")
            raise
            
        try:
            document_rules_count = len(document_governance.directory_rules)
            print(f"[DEBUG] document_rules: {document_rules_count}")
        except Exception as e:
            print(f"[ERROR] document_governance error: {e}")
            raise
        
        status = {
            "agent_roles": agent_roles_count,
            "active_meetings": active_meetings_count,
            "voice_service": {"status": "available", "services": voice_services_count},
            "rbac_users": rbac_users_count,
            "document_rules": document_rules_count
        }
        print(f"[DEBUG] 系统状态获取成功: {status}")
        return jsonify({"ok": True, "status": status})
    except Exception as e:
        import traceback
        error_msg = f"系统状态检查失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] 详细错误: {traceback.format_exc()}")
        return jsonify({"ok": False, "error": error_msg}), 500


@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "meetingroom_server", "ui": UI_DIR.exists()})


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JS001 Meetingroom 后端服务")
    # 从配置文件读取默认 host/port 与 ws_jwt_required（可被环境变量与命令行覆盖）
    cfg_host = "127.0.0.1"
    cfg_port = 8020
    cfg_jwt_required = False
    try:
        cfg_path = REPO_ROOT / "config" / "meetingroom_config.json"
        if cfg_path.exists():
            with cfg_path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg_host = str(cfg.get("host", cfg_host))
            try:
                cfg_port = int(cfg.get("port", cfg_port))
            except Exception:
                cfg_port = cfg_port
            cfg_jwt_required = bool(cfg.get("ws_jwt_required", cfg_jwt_required))
    except Exception as e:
        try:
            sys.stdout.write(f"[Config] 读取 meetingroom_config.json 失败: {e}\n")
        except Exception:
            pass

    # 若未通过环境变量显式设置，则采用配置文件中的 ws_jwt_required
    try:
        global WS_JWT_REQUIRED
        if os.environ.get("WS_JWT_REQUIRED") is None:
            WS_JWT_REQUIRED = bool(cfg_jwt_required)
    except Exception:
        pass

    # 命令行的默认值采用配置文件值（命令行传参仍然优先级最高）
    parser.add_argument("--host", default=cfg_host)
    parser.add_argument("--port", type=int, default=cfg_port)
    args = parser.parse_args()
    
    # 启用日志重定向
    sys.stdout = log_capture
    
    print(f"[Meetingroom] Server running at http://{args.host}:{args.port}/")
    print(f"[WebSocket] 日志传输已启用，连接地址: ws://{args.host}:{args.port}/socket.io/")
    
    # 后台自启动 Shimmy（仅当首选后端为 Shimmy 时）
    if PREFERRED_BACKEND == "shimmy":
        def _bg():
            try:
                print("[Shimmy] 正在启动后台服务...")
                _ensure_shimmy_running(wait_secs=15.0)
                print("[Shimmy] 后台服务启动完成")
            except Exception as e:
                print(f"[Shimmy] 启动失败: {e}")
        t = threading.Thread(target=_bg, name="shimmy-autostart", daemon=True)
        t.start()
    
    # 打印路由映射，帮助定位路由冲突与方法设置问题
    _print_routes_summary()

    # 使用SocketIO运行应用
    socketio.run(app, host=args.host, port=args.port, debug=True, allow_unsafe_werkzeug=True, use_reloader=False)


if __name__ == "__main__":
    main()