#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JS001 Meetingroom 可视化后端（Flask + WebSocket）

- 提供会议记录浏览 API
- 提供触发会议生成的 API（调用 tools/agents/run_collab.py）
- 同域托管前端静态页面（projects/JS001-meetingroom/ui）
- 实时日志传输到浏览器（WebSocket）

启动：
  python tools/servers/meetingroom_server.py --host 127.0.0.1 --port 8020

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
from flask import stream_with_context, request
from flask_socketio import SocketIO, emit


REPO_ROOT = Path(__file__).resolve().parents[2]
# 确保可以导入仓库根路径下的模块（如 models.services.llm_router）
root_str = str(REPO_ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
MEETINGS_DIR = REPO_ROOT / "Struc" / "GeneralOffice" / "meetings"
UI_DIR = REPO_ROOT / "projects" / "JS001-meetingroom" / "ui"

app = Flask(
    __name__
)

# 添加WebSocket支持
socketio = SocketIO(
    app, 
    cors_allowed_origins="*"
)

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
    print(f"[WebSocket] 客户端连接: {request.sid}")
    emit('log_message', {
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
    emit('log_message', {
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
    global _SHIMMY_PROC, _SHIMMY_PROCS
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
                creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP") else 0),
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
    # 进一步健康检查：仅当能实际完成一次最小推理时，才认为 Shimmy 可用于默认模型
    def _shimmy_can_infer(base_url: str, model_id: str) -> bool:
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
    def _first_present(candidates: List[str], pool: List[str], default_fallback: str) -> str:
        s = set(pool)
        for c in candidates:
            if c in s:
                return c
        return default_fallback

    if PREFERRED_BACKEND == "shimmy":
        return {
            # 只有当 Shimmy 存在且能实际推理时才优先选择，否则回退到 Ollama
            "offline": (_first_present(offline_shimmy_priority, (shimmy_ready_models or []), offline_ollama) if shimmy_ok else offline_ollama),
            "rtm": (_first_present(rtm_shimmy_priority, (shimmy_ready_models or []), rtm_ollama) if shimmy_ok else rtm_ollama),
        }
    else:
        # 如果用户指定 Ollama 为首选，则优先使用 Ollama；当其不可达再降级到 Shimmy
        # 这里不额外探测 Ollama，可交给路由层回退；仅在 Shimmy 不可达时不选其模型。
        return {
            "offline": offline_ollama if PREFERRED_BACKEND == "ollama" else (offline_shimmy_priority[0] if offline_shimmy_priority else offline_ollama),
            "rtm": rtm_ollama if PREFERRED_BACKEND == "ollama" else (rtm_shimmy_priority[0] if rtm_shimmy_priority else rtm_ollama),
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
                "项目目录": "projects/JS001-meetingroom",
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
        q: queue.Queue = sess["queue"]
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
    # 再兜底：根据“项目”名称映射到已知目录（例如 DeWatermark AI -> projects/001-dewatermark-ai）
    if not project_dir:
        proj_name = (info.get("项目") or "").strip()
        name_map = {
            "DeWatermark AI": "projects/001-dewatermark-ai",
            "JS001-meetingroom": "projects/JS001-meetingroom",
            "YDS-Playground": "projects/YDS-Playground",
        }
        if proj_name in name_map:
            expected = name_map[proj_name]
            # 校验目录是否存在
            expected_path = REPO_ROOT / expected.replace("/", os.sep)
            if expected_path.exists():
                project_dir = expected
            else:
                project_dir = f"未找到（期望：{expected}）"
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
    # 前端静态页面
    index_file = UI_DIR / "index.html"
    if not index_file.exists():
        return (
            "前端页面不存在：projects/JS001-meetingroom/ui/index.html。\n"
            "请先创建 UI（我也可以为你生成初版）。",
            200,
            {"Content-Type": "text/plain; charset=utf-8"},
        )
    return send_from_directory(str(UI_DIR), "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    """提供静态文件服务"""
    # 检查文件是否存在于UI目录中
    file_path = UI_DIR / filename
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(UI_DIR), filename)
    # 如果文件不存在，返回404
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


def _load_external_models_cfg() -> Dict[str, Any]:
    cfg_path = REPO_ROOT / "models" / "config" / "external_models.json"
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f).get("external_models_config", {})
    except Exception:
        return {}

def _load_external_env_vars() -> Dict[str, str]:
    """读取 external_models.json 中的 environment_variables（若存在）。"""
    cfg_path = REPO_ROOT / "models" / "config" / "external_models.json"
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
        import requests
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


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
        for h in ("http://127.0.0.1:11434/v1", "http://127.0.0.1:11434", "http://localhost:11434/v1", "http://localhost:11434"):
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
            default_host = (oll.get("host") or os.environ.get("OLLAMA_HOST") or env_vars.get("OLLAMA_HOST") or "").rstrip("/")
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
                return jsonify({"ok": True, "endpoint": path, "host": h, "raw": data})
    return jsonify({"ok": False, "error": "unreachable or unknown schema", "hosts_tried": hosts_to_try, "paths": candidates}), 502


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
    oll_host = (oll.get("host") or os.environ.get("OLLAMA_HOST") or env_vars.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
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


@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "meetingroom_server", "ui": UI_DIR.exists()})


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JS001 Meetingroom 后端服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8020)
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
    
    # 使用SocketIO运行应用
    socketio.run(app, host=args.host, port=args.port, debug=False, allow_unsafe_werkzeug=True, use_reloader=False)


if __name__ == "__main__":
    main()