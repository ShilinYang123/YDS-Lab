"""
性能基准分析（Shimmy 与 Ollama）
- 依据项目架构设计文档，将性能工具放置于 tools/performance/
- 统一使用 /api/generate 进行对比，以便获得 eval_count/eval_duration_ms 等可计算 TPS 的指标
- 结果输出至 Struc/GeneralOffice/logs/bench_local_llm.json

注意：
1) 若两端模型名称不同（如 shimmy=deepseek-1.5b-chat-q4_0, ollama=tinyllama:latest），仅输出各自指标，不自动生成路由偏好；
2) 若两端模型名称相同，且测试成功，将根据耗时/TPS综合给出偏好建议（可选写入 models/config/router_preference.json）。
3) 若 /api/generate 初次调用返回 502（常见于未预热），会自动进行一次健康检查和重试；若仍失败，自动回退到 OpenAI 兼容端点 /v1/chat/completions，仅以总耗时进行评分。
"""

import time
import json
import argparse
import re
from pathlib import Path
from typing import Dict, Any, Optional

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = PROJECT_ROOT / "Struc" / "GeneralOffice" / "logs"
CONFIG_DIR = PROJECT_ROOT / "models" / "config"
PREF_FILE = CONFIG_DIR / "router_preference.json"


def get_health(base_url: str, timeout: int = 10) -> bool:
    """检查 /health，作为预热与可用性探测。"""
    url = f"{base_url.rstrip('/')}/health"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def post_generate(base_url: str, model: str, prompt: str, stream: bool = False, timeout: int = 120, retries: int = 2, retry_wait_s: float = 0.8) -> Dict[str, Any]:
    """调用 /api/generate 并收集统一的计量指标，带重试与端点标记。"""
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # 统一使用非流式，便于总耗时统计
    }
    attempt = 0
    t0_all = time.time()
    while attempt <= retries:
        t0 = time.time()
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            t1 = time.time()
            resp.raise_for_status()
            data = resp.json()
            metrics = {
                "load_ms": data.get("load_ms") or data.get("load_duration_ms"),
                "prompt_eval_count": data.get("prompt_eval_count"),
                "prompt_eval_duration_ms": data.get("prompt_eval_duration_ms") or data.get("prompt_eval_ms"),
                "eval_count": data.get("eval_count"),
                "eval_duration_ms": data.get("eval_duration_ms") or data.get("eval_ms"),
                "total_duration_ms": int((t1 - t0) * 1000),
                "response_len": len((data.get("response") or data.get("content") or "")),
            }
            tps = None
            try:
                if metrics.get("eval_count") and metrics.get("eval_duration_ms") and metrics["eval_duration_ms"] > 0:
                    tps = metrics["eval_count"] / (metrics["eval_duration_ms"] / 1000.0)
            except Exception:
                tps = None
            metrics["tps"] = tps

            return {
                "ok": True,
                "metrics": metrics,
                "raw": data,
                "endpoint": "generate"
            }
        except Exception as e:
            # 若是首次失败，先进行健康检查与短暂等待后重试
            attempt += 1
            if attempt <= retries:
                get_health(base_url)
                time.sleep(retry_wait_s)
                continue
            # 重试后仍失败
            return {
                "ok": False,
                "error": str(e),
                "total_duration_ms": int((time.time() - t0_all) * 1000),
                "endpoint": "generate"
            }


def post_chat_completions(base_url: str, model: str, prompt: str, timeout: int = 120) -> Dict[str, Any]:
    """回退到 OpenAI 兼容端点 /v1/chat/completions（仅统计总耗时、响应长度）。"""
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    t0 = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        t1 = time.time()
        resp.raise_for_status()
        data = resp.json()
        # 兼容 OpenAI 格式取出内容
        content = None
        try:
            choices = data.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                content = msg.get("content")
        except Exception:
            content = None

        metrics = {
            "load_ms": None,
            "prompt_eval_count": None,
            "prompt_eval_duration_ms": None,
            "eval_count": None,
            "eval_duration_ms": None,
            "total_duration_ms": int((t1 - t0) * 1000),
            "response_len": len(content or ""),
            "tps": None,
        }
        return {
            "ok": True,
            "metrics": metrics,
            "raw": data,
            "endpoint": "chat"
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "total_duration_ms": int((time.time() - t0) * 1000),
            "endpoint": "chat"
        }


def score_backend(result: Dict[str, Any]) -> float:
    """将指标映射为分数，便于比较（简单线性打分）。"""
    if not result.get("ok"):
        return -1.0
    m = result.get("metrics", {})
    total_ms = m.get("total_duration_ms") or 0
    tps = m.get("tps") or 0.0
    # 简单打分：TPS 权重 0.7，耗时倒数权重 0.3
    # 防止除零：最小耗时设为 1ms
    inv_time = 1.0 / max(total_ms, 1)
    score = 0.7 * tps + 0.3 * inv_time
    return float(score)


def write_logs(out_path: Path, content: Dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)


def maybe_write_preference(model_name: str, shimmy_score: float, ollama_score: float, write_pref: bool) -> Optional[Path]:
    """根据分数写入路由偏好（仅当 write_pref=True 才写）。
    - 变更：不再覆盖整个文件，改为合并写入（若文件存在则读取并更新）。
    """
    if not write_pref:
        return None
    preference = "shimmy" if shimmy_score >= ollama_score else "ollama"
    PREF_FILE.parent.mkdir(parents=True, exist_ok=True)

    existing: Dict[str, Any] = {}
    try:
        if PREF_FILE.exists():
            with PREF_FILE.open("r", encoding="utf-8") as f:
                existing = json.load(f) or {}
    except Exception:
        existing = {}

    existing[model_name] = preference
    with PREF_FILE.open("w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return PREF_FILE


def extract_text(result: Dict[str, Any]) -> str:
    """从结果中提取文本内容，兼容 generate/chat 两种返回格式。"""
    try:
        raw = result.get("raw") or {}
        if result.get("endpoint") == "generate":
            return (raw.get("response") or raw.get("content") or "").strip()
        # chat/completions 兼容 OpenAI
        choices = raw.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            return (msg.get("content") or "").strip()
    except Exception:
        pass
    return ""


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def simple_quality_metrics(prompt: str, text: str) -> Dict[str, float]:
    """基于提示与文本的简易质量评分：长度惩罚、简洁度、格式合规度。
    - 长度惩罚（brevity）：线性惩罚，越短越好（设上限以避免过度偏好极短）
    - 简洁度（conciseness）：按平均句长估计（越短越好）
    - 格式合规度（format）：根据提示中的指令关键词进行规则检测
    """
    if not isinstance(text, str):
        text = ""
    # 句子切分（中英文常见标点）
    parts = [p.strip() for p in re.split(r"[。！？!?\.!]+", text) if p.strip()]
    sentence_count = len(parts) if parts else (1 if text else 0)
    length = len(text)

    # 长度惩罚：在 0~1 范围内，>800 字开始明显惩罚；保留最小得分 0.05
    brevity = _clamp(1.0 - (length / 800.0))
    brevity = max(brevity, 0.05)

    # 简洁度：平均句长越短越好（50 字为基准），保留最小得分 0.05
    avg_sent_len = (length / max(sentence_count, 1)) if sentence_count else length
    conciseness = _clamp(1.0 - (avg_sent_len / 50.0))
    conciseness = max(conciseness, 0.05)

    # 格式合规度：基于提示关键词的简单规则
    prompt_l = prompt.lower()
    text_l = text.lower()
    format_score = 0.5  # 基础分

    # 两句/两三句要求
    if ("两句" in prompt) or ("two sentences" in prompt_l):
        format_score = 1.0 if sentence_count == 2 else (0.5 if sentence_count in (1, 3) else 0.2)
    if ("两三句" in prompt) or ("two or three sentences" in prompt_l):
        format_score = 1.0 if sentence_count in (2, 3) else (0.5 if sentence_count in (1, 4) else 0.2)

    # 公式/包含公式
    if ("公式" in prompt) or ("include the formula" in prompt_l) or ("formula" in prompt_l):
        if ("f=ma" in text_l) or ("f = ma" in text_l):
            format_score = max(format_score, 1.0)
        elif "=" in text_l:
            format_score = max(format_score, 0.7)
        else:
            format_score = max(format_score, 0.2)

    # Python 代码与时间复杂度说明
    if ("python" in prompt_l) and ("function" in prompt_l) and ("reverse" in prompt_l):
        has_def = ("def " in text_l)
        has_return = ("return" in text_l)
        has_complexity = ("o(" in text_l)
        if has_def and has_return and has_complexity:
            format_score = max(format_score, 1.0)
        elif has_def and has_return:
            format_score = max(format_score, 0.8)
        elif has_def:
            format_score = max(format_score, 0.6)
        else:
            format_score = max(format_score, 0.3)

    # 中文注释/代码注释
    if ("注释" in prompt) or ("comment" in prompt_l):
        has_triple_double = '"""' in text
        has_triple_single = "'''" in text
        has_hash = ("#" in text) or has_triple_double or has_triple_single
        has_cn = bool(re.search(r"[\u4e00-\u9fff]", text))  # 是否含中文
        if has_hash and has_cn:
            format_score = max(format_score, 1.0)
        elif has_hash:
            format_score = max(format_score, 0.7)
        else:
            format_score = max(format_score, 0.3)

    overall = _clamp(0.4 * format_score + 0.3 * brevity + 0.3 * conciseness)

    return {
        "length_penalty": brevity,
        "conciseness": conciseness,
        "format_compliance": format_score,
        "overall": overall
    }


def main():
    parser = argparse.ArgumentParser(description="Shimmy 与 Ollama 本地性能对比")
    parser.add_argument("--shimmy-url", default="http://127.0.0.1:11435", help="Shimmy 基地址（不含 /api）")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434", help="Ollama 基地址（不含 /api）")
    parser.add_argument("--shimmy-model", default="deepseek-1.5b-chat-q4_0", help="Shimmy 模型名（已加载到 shimmy 服务器）")
    parser.add_argument("--ollama-model", default="tinyllama:latest", help="Ollama 模型名（已通过 ollama pull）")
    parser.add_argument("--prompt", default="请用两句中文写一首秋天的短诗。", help="测试提示词")
    parser.add_argument("--out", default=str(LOGS_DIR / "bench_local_llm.json"), help="输出日志路径")
    parser.add_argument("--write-preference", action="store_true", help="若两端模型名相同，则写入路由偏好")

    args = parser.parse_args()

    # 轻量预热，避免 /api/generate 初次 502
    get_health(args.shimmy_url)
    get_health(args.ollama_url)
    time.sleep(0.6)

    shimmy_res = post_generate(args.shimmy_url, args.shimmy_model, args.prompt)
    if (not shimmy_res.get("ok")) and ("502" in str(shimmy_res.get("error", ""))):
        # 自动回退到 OpenAI 兼容端点
        shimmy_res = post_chat_completions(args.shimmy_url, args.shimmy_model, args.prompt)

    ollama_res = post_generate(args.ollama_url, args.ollama_model, args.prompt)
    if (not ollama_res.get("ok")) and ("502" in str(ollama_res.get("error", ""))):
        ollama_res = post_chat_completions(args.ollama_url, args.ollama_model, args.prompt)

    results = {
        "shimmy": shimmy_res,
        "ollama": ollama_res,
        "meta": {
            "prompt": args.prompt,
            "timestamp": int(time.time()),
            "env": {
                "shimmy_url": args.shimmy_url,
                "ollama_url": args.ollama_url,
                "shimmy_model": args.shimmy_model,
                "ollama_model": args.ollama_model,
            }
        }
    }

    # 质量评分（长度惩罚/简洁度/格式合规度/综合）
    shimmy_text = extract_text(results["shimmy"]) if results.get("shimmy") else ""
    ollama_text = extract_text(results["ollama"]) if results.get("ollama") else ""
    results["quality"] = {
        "shimmy": simple_quality_metrics(args.prompt, shimmy_text),
        "ollama": simple_quality_metrics(args.prompt, ollama_text)
    }

    shimmy_score = score_backend(results["shimmy"])  # -1 表示失败
    ollama_score = score_backend(results["ollama"])  # -1 表示失败
    results["scores"] = {
        "shimmy": shimmy_score,
        "ollama": ollama_score,
    }

    out_path = Path(args.out)
    write_logs(out_path, results)

    # 当且仅当两端模型名相同时才允许写入偏好
    if args.write_preference and (args.shimmy_model == args.ollama_model):
        pref_path = maybe_write_preference(args.shimmy_model, shimmy_score, ollama_score, True)
        if pref_path:
            print(f"路由偏好写入: {pref_path}")
    else:
        if args.write_preference:
            print("[警告] 两端模型名不同，已跳过写入 router_preference.json。")

    print(f"基准结果已写入: {out_path}")


if __name__ == "__main__":
    main()