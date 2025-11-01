"""
运行基准套件，并合并写入 router_preference.json（按后端来源映射）。
- 读取 tools/performance/benchmark_suite.json
- 对每个任务调用 performance_analyzer.py
- 汇总结果写入 Struc/GeneralOffice/logs/bench_suite_local_llm.json
- 将套件中涉及的模型各自映射到其所在后端（shimmy/ollama），合并更新 models/config/router_preference.json
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List

# 新增：质量聚合辅助函数（global / aligned_subset / pair_groups）
def merge_quality_aggregate(aggregate, all_results):
    def _init_quality_accum():
        return {
            'shimmy': {'sum_lp': 0.0, 'sum_conc': 0.0, 'sum_fc': 0.0, 'sum_overall': 0.0, 'count': 0, 'wins': 0},
            'ollama': {'sum_lp': 0.0, 'sum_conc': 0.0, 'sum_fc': 0.0, 'sum_overall': 0.0, 'count': 0, 'wins': 0},
            'ties': 0,
        }

    def _accumulate(acc, task_result):
        res = task_result.get('result', {})
        for backend in ('shimmy', 'ollama'):
            q = res.get('quality', {}).get(backend)
            if not isinstance(q, dict):
                continue
            a = acc[backend]
            a['sum_lp'] += float(q.get('length_penalty', 0.0))
            a['sum_conc'] += float(q.get('conciseness', 0.0))
            a['sum_fc'] += float(q.get('format_compliance', 0.0))
            a['sum_overall'] += float(q.get('overall', 0.0))
            a['count'] += 1

    def _accumulate_compare(acc, task_result):
        res = task_result.get('result', {})
        sh = res.get('quality', {}).get('shimmy') or {}
        ol = res.get('quality', {}).get('ollama') or {}
        if not sh or not ol:
            return
        sh_o = float(sh.get('overall', 0.0))
        ol_o = float(ol.get('overall', 0.0))
        if sh_o > ol_o:
            acc['shimmy']['wins'] += 1
        elif sh_o < ol_o:
            acc['ollama']['wins'] += 1
        else:
            acc['ties'] += 1

    def _finalize(acc):
        out = {}
        comparisons = acc['shimmy']['wins'] + acc['ollama']['wins'] + acc['ties']
        for backend in ('shimmy', 'ollama'):
            c = acc[backend]['count']
            out[backend] = {
                'avg_length_penalty': (acc[backend]['sum_lp'] / c) if c else None,
                'avg_conciseness': (acc[backend]['sum_conc'] / c) if c else None,
                'avg_format_compliance': (acc[backend]['sum_fc'] / c) if c else None,
                'avg_overall': (acc[backend]['sum_overall'] / c) if c else None,
                'count': c,
                'win_rate': (acc[backend]['wins'] / comparisons) if comparisons else None,
                'tie_rate': (acc['ties'] / comparisons) if comparisons else None,
            }
        out['comparisons'] = comparisons
        return out

    # 全局质量聚合
    overall = _init_quality_accum()
    for r in all_results:
        _accumulate(overall, r)
        _accumulate_compare(overall, r)
    aggregate['quality'] = _finalize(overall)

    # 对齐子集（aligned=true）
    aligned = _init_quality_accum()
    for r in all_results:
        if r.get('tags', {}).get('aligned', False):
            _accumulate(aligned, r)
            _accumulate_compare(aligned, r)
    aggregate.setdefault('aligned_subset', {})
    aggregate['aligned_subset']['quality'] = _finalize(aligned)

    # 按 family + quantization 的分组
    aggregate.setdefault('pair_groups', {})
    groups = {}
    for r in all_results:
        tags = r.get('tags', {})
        key = f"{tags.get('family', 'unknown')}.{tags.get('quantization', 'unknown')}"
        if key not in groups:
            groups[key] = _init_quality_accum()
        _accumulate(groups[key], r)
        _accumulate_compare(groups[key], r)

    for k, acc in groups.items():
        aggregate['pair_groups'].setdefault(k, {})
        aggregate['pair_groups'][k]['quality'] = _finalize(acc)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SUITE_CONFIG = PROJECT_ROOT / "tools" / "performance" / "benchmark_suite.json"
LOGS_DIR = PROJECT_ROOT / "Struc" / "GeneralOffice" / "logs"
ANALYZER = PROJECT_ROOT / "tools" / "performance" / "performance_analyzer.py"
SUITE_OUT = LOGS_DIR / "bench_suite_local_llm.json"
PREF_FILE = PROJECT_ROOT / "models" / "config" / "router_preference.json"


# 新增：聚合统计函数（平均耗时、平均响应长度、端点分布、持续时间胜率）
def compute_aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """在原有总体聚合基础上，增加：
    - aligned_subset：仅统计带 aligned=true 的任务子集
    - pair_groups：按 family+quantization（如 qwen2.Q4_0）分组统计
    """
    agg = {
        "shimmy": {
            "count": 0,
            "sum_duration_ms": 0,
            "sum_response_len": 0,
            "avg_duration_ms": None,
            "avg_response_len": None,
            "endpoint_counts": {}
        },
        "ollama": {
            "count": 0,
            "sum_duration_ms": 0,
            "sum_response_len": 0,
            "avg_duration_ms": None,
            "avg_response_len": None,
            "endpoint_counts": {}
        },
        "comparisons": {
            "shimmy_faster": 0,
            "ollama_faster": 0,
            "ties": 0,
            "win_rate_shimmy": None,
            "win_rate_ollama": None
        }
    }

    aligned = {
        "shimmy": {"count": 0, "sum_duration_ms": 0, "sum_response_len": 0, "avg_duration_ms": None, "avg_response_len": None, "endpoint_counts": {}},
        "ollama": {"count": 0, "sum_duration_ms": 0, "sum_response_len": 0, "avg_duration_ms": None, "avg_response_len": None, "endpoint_counts": {}},
        "comparisons": {"shimmy_faster": 0, "ollama_faster": 0, "ties": 0, "win_rate_shimmy": None, "win_rate_ollama": None}
    }
    pair_groups: Dict[str, Any] = {}

    def _ensure_pair(key: str):
        if key not in pair_groups:
            pair_groups[key] = {
                "shimmy": {"count": 0, "sum_duration_ms": 0, "sum_response_len": 0, "avg_duration_ms": None, "avg_response_len": None, "endpoint_counts": {}},
                "ollama": {"count": 0, "sum_duration_ms": 0, "sum_response_len": 0, "avg_duration_ms": None, "avg_response_len": None, "endpoint_counts": {}},
                "comparisons": {"shimmy_faster": 0, "ollama_faster": 0, "ties": 0, "win_rate_shimmy": None, "win_rate_ollama": None}
            }

    for item in results:
        res = item.get("result", {})
        tags = item.get("tags", {})
        family = tags.get("family")
        quant = tags.get("quantization")
        pair_key = f"{family or 'unknown'}.{quant or 'unknown'}"

        # 总体后端统计
        for backend in ["shimmy", "ollama"]:
            b = res.get(backend)
            if not isinstance(b, dict):
                continue
            metrics = b.get("metrics", {})
            d = metrics.get("total_duration_ms")
            rl = metrics.get("response_len")
            if isinstance(d, (int, float)):
                agg[backend]["count"] += 1
                agg[backend]["sum_duration_ms"] += d
            if isinstance(rl, (int, float)):
                agg[backend]["sum_response_len"] += rl
            ep = b.get("endpoint")
            if isinstance(ep, str) and ep:
                agg[backend]["endpoint_counts"][ep] = agg[backend]["endpoint_counts"].get(ep, 0) + 1

        # 总体持续时间胜负
        shimmy_d = res.get("shimmy", {}).get("metrics", {}).get("total_duration_ms")
        ollama_d = res.get("ollama", {}).get("metrics", {}).get("total_duration_ms")
        if isinstance(shimmy_d, (int, float)) and isinstance(ollama_d, (int, float)):
            if shimmy_d < ollama_d:
                agg["comparisons"]["shimmy_faster"] += 1
            elif shimmy_d > ollama_d:
                agg["comparisons"]["ollama_faster"] += 1
            else:
                agg["comparisons"]["ties"] += 1

        # 对齐子集统计
        if tags.get("aligned"):
            for backend in ["shimmy", "ollama"]:
                b = res.get(backend)
                if not isinstance(b, dict):
                    continue
                metrics = b.get("metrics", {})
                d = metrics.get("total_duration_ms")
                rl = metrics.get("response_len")
                if isinstance(d, (int, float)):
                    aligned[backend]["count"] += 1
                    aligned[backend]["sum_duration_ms"] += d
                if isinstance(rl, (int, float)):
                    aligned[backend]["sum_response_len"] += rl
                ep = b.get("endpoint")
                if isinstance(ep, str) and ep:
                    aligned[backend]["endpoint_counts"][ep] = aligned[backend]["endpoint_counts"].get(ep, 0) + 1
            if isinstance(shimmy_d, (int, float)) and isinstance(ollama_d, (int, float)):
                if shimmy_d < ollama_d:
                    aligned["comparisons"]["shimmy_faster"] += 1
                elif shimmy_d > ollama_d:
                    aligned["comparisons"]["ollama_faster"] += 1
                else:
                    aligned["comparisons"]["ties"] += 1

        # 按家族+量化分组
        _ensure_pair(pair_key)
        pg = pair_groups[pair_key]
        for backend in ["shimmy", "ollama"]:
            b = res.get(backend)
            if not isinstance(b, dict):
                continue
            metrics = b.get("metrics", {})
            d = metrics.get("total_duration_ms")
            rl = metrics.get("response_len")
            if isinstance(d, (int, float)):
                pg[backend]["count"] += 1
                pg[backend]["sum_duration_ms"] += d
            if isinstance(rl, (int, float)):
                pg[backend]["sum_response_len"] += rl
            ep = b.get("endpoint")
            if isinstance(ep, str) and ep:
                pg[backend]["endpoint_counts"][ep] = pg[backend]["endpoint_counts"].get(ep, 0) + 1
        if isinstance(shimmy_d, (int, float)) and isinstance(ollama_d, (int, float)):
            if shimmy_d < ollama_d:
                pg["comparisons"]["shimmy_faster"] += 1
            elif shimmy_d > ollama_d:
                pg["comparisons"]["ollama_faster"] += 1
            else:
                pg["comparisons"]["ties"] += 1

    # 总体平均与胜率
    for backend in ["shimmy", "ollama"]:
        cnt = agg[backend]["count"]
        if cnt > 0:
            agg[backend]["avg_duration_ms"] = agg[backend]["sum_duration_ms"] / cnt
            agg[backend]["avg_response_len"] = agg[backend]["sum_response_len"] / cnt
        else:
            agg[backend]["avg_duration_ms"] = None
            agg[backend]["avg_response_len"] = None

    total_duel = agg["comparisons"]["shimmy_faster"] + agg["comparisons"]["ollama_faster"] + agg["comparisons"]["ties"]
    if total_duel > 0:
        agg["comparisons"]["win_rate_shimmy"] = agg["comparisons"]["shimmy_faster"] / total_duel
        agg["comparisons"]["win_rate_ollama"] = agg["comparisons"]["ollama_faster"] / total_duel
    else:
        agg["comparisons"]["win_rate_shimmy"] = None
        agg["comparisons"]["win_rate_ollama"] = None

    # 对齐子集平均与胜率
    for backend in ["shimmy", "ollama"]:
        cnt = aligned[backend]["count"]
        if cnt > 0:
            aligned[backend]["avg_duration_ms"] = aligned[backend]["sum_duration_ms"] / cnt
            aligned[backend]["avg_response_len"] = aligned[backend]["sum_response_len"] / cnt
    total_duel_al = aligned["comparisons"]["shimmy_faster"] + aligned["comparisons"]["ollama_faster"] + aligned["comparisons"]["ties"]
    if total_duel_al > 0:
        aligned["comparisons"]["win_rate_shimmy"] = aligned["comparisons"]["shimmy_faster"] / total_duel_al
        aligned["comparisons"]["win_rate_ollama"] = aligned["comparisons"]["ollama_faster"] / total_duel_al

    # 分组平均与胜率
    for key, pg in pair_groups.items():
        for backend in ["shimmy", "ollama"]:
            cnt = pg[backend]["count"]
            if cnt > 0:
                pg[backend]["avg_duration_ms"] = pg[backend]["sum_duration_ms"] / cnt
                pg[backend]["avg_response_len"] = pg[backend]["sum_response_len"] / cnt
        total_duel_pg = pg["comparisons"]["shimmy_faster"] + pg["comparisons"]["ollama_faster"] + pg["comparisons"]["ties"]
        if total_duel_pg > 0:
            pg["comparisons"]["win_rate_shimmy"] = pg["comparisons"]["shimmy_faster"] / total_duel_pg
            pg["comparisons"]["win_rate_ollama"] = pg["comparisons"]["ollama_faster"] / total_duel_pg

    # 纳入聚合结果
    agg["aligned_subset"] = aligned
    agg["pair_groups"] = pair_groups

    # 新增：质量统计汇总（global / aligned_subset / pair_groups）
    merge_quality_aggregate(agg, results)

    return agg


def run_task(task: Dict[str, Any], shimmy_url: str, ollama_url: str) -> Dict[str, Any]:
    out_path = LOGS_DIR / "bench_local_llm.json"
    cmd = [
        "python", str(ANALYZER),
        "--shimmy-url", shimmy_url,
        "--shimmy-model", task["shimmy_model"],
        "--ollama-url", ollama_url,
        "--ollama-model", task["ollama_model"],
        "--prompt", task["prompt"],
        "--out", str(out_path)
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    with out_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "name": task.get("name"),
        "env": {
            "shimmy_model": task.get("shimmy_model"),
            "ollama_model": task.get("ollama_model"),
        },
        "tags": {
            "aligned": task.get("aligned", False),
            "family": task.get("family"),
            "quantization": task.get("quantization")
        },
        "result": data,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def merge_preference(shimmy_models: List[str], ollama_models: List[str]) -> Path:
    PREF_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing: Dict[str, Any] = {}
    try:
        if PREF_FILE.exists():
            with PREF_FILE.open("r", encoding="utf-8") as f:
                existing = json.load(f) or {}
    except Exception:
        existing = {}

    for m in shimmy_models:
        existing[m] = "shimmy"
    for m in ollama_models:
        existing[m] = "ollama"

    with PREF_FILE.open("w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    return PREF_FILE


def main():
    with SUITE_CONFIG.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    shimmy_url = cfg.get("shimmy_url")
    ollama_url = cfg.get("ollama_url")
    tasks = cfg.get("tasks", [])

    results = []
    used_shimmy = []
    used_ollama = []

    for t in tasks:
        # 允许任务级别覆盖后端 URL，以便在同一套件中使用多个 Shimmy/Ollama 实例
        t_shimmy_url = t.get("shimmy_url", shimmy_url)
        t_ollama_url = t.get("ollama_url", ollama_url)
        results.append(run_task(t, t_shimmy_url, t_ollama_url))
        sm = t.get("shimmy_model")
        om = t.get("ollama_model")
        if sm and sm not in used_shimmy:
            used_shimmy.append(sm)
        if om and om not in used_ollama:
            used_ollama.append(om)

    # 新增：聚合统计
    aggregate = compute_aggregate(results)

    pref_path = merge_preference(used_shimmy, used_ollama)

    suite_out = {
        "meta": {
            "timestamp": int(time.time()),
            "shimmy_url": shimmy_url,
            "ollama_url": ollama_url,
            "tasks_count": len(tasks)
        },
        "tasks": results,
        "aggregate": aggregate,
        "preference_updates": {
            "shimmy_models": used_shimmy,
            "ollama_models": used_ollama
        },
        "pref_file": str(pref_path)
    }

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with SUITE_OUT.open("w", encoding="utf-8") as f:
        json.dump(suite_out, f, ensure_ascii=False, indent=2)

    print(f"Suite results written to: {SUITE_OUT}")
    print(f"router_preference.json updated at: {pref_path}")


if __name__ == "__main__":
    main()