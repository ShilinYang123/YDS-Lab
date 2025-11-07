import os
import json
import re
from datetime import datetime

def schedule_emergency_meeting(reason: str) -> str:
    """触发紧急会议"""
    return f"🚨【紧急会议】因 {reason}，立即召开临时会议"

def approve_budget(amount: float, purpose: str) -> str:
    """审批预算（>¥500）"""
    return f"✅ 总经理批准预算：¥{amount:.2f}，用途：{purpose}"

def archive_meeting(content: str) -> str:
    """归档会议记录（同时生成 Markdown 与 JSON 结构化文件，容错优先）"""
    base_ts = datetime.now().strftime('%Y%m%d-%H%M')
    base_dir = "Struc/GeneralOffice/meetings"
    os.makedirs(base_dir, exist_ok=True)

    base_name = f"MTG-{base_ts}"
    md_path = os.path.join(base_dir, f"{base_name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    # 解析辅助函数
    def _extract_block(title: str) -> str | None:
        pattern = rf"【{re.escape(title)}】\s*(.*?)(?=\n【|\Z)"
        m = re.search(pattern, content, flags=re.S)
        return m.group(1).strip() if m else None

    def _parse_meeting_info(block: str) -> dict:
        info = {}
        if not block:
            return info
        lines = [ln.strip("\r") for ln in block.splitlines()]
        for ln in lines:
            if not ln.startswith("-"):
                continue
            try:
                key, val = ln[1:].split("：", 1)
                key = key.strip()
                val = val.strip()
            except ValueError:
                continue
            info[key] = val
        if "参会角色" in info:
            info["参会角色"] = [x.strip() for x in info["参会角色"].split(",") if x.strip()]
        if "议程" in info:
            info["议程"] = [x.strip() for x in info["议程"].split(",") if x.strip()]
        return info

    def _parse_md_table(block: str) -> list[dict]:
        if not block:
            return []
        lines = [ln.rstrip() for ln in block.splitlines() if ln.strip()]
        table_lines = [ln for ln in lines if "|" in ln]
        if len(table_lines) < 2:
            return []
        header_line = table_lines[0].strip()
        # 解析表头，去掉行首/行尾空单元
        raw_heads = [h.strip() for h in header_line.split("|")]
        if raw_heads and raw_heads[0] == "":
            raw_heads = raw_heads[1:]
        if raw_heads and raw_heads[-1] == "":
            raw_heads = raw_heads[:-1]
        headers = [h for h in raw_heads if h]

        # 跳过分隔线，并收集数据行
        body_lines = []
        for ln in table_lines[1:]:
            # 典型分隔线：|---|---| 或 :---: 等
            chk = ln.replace("|", "").replace("-", "").replace(":", "").strip()
            if chk == "":
                # 分隔线，跳过
                continue
            body_lines.append(ln)

        rows = []
        for ln in body_lines:
            raw_cols = [c.strip() for c in ln.split("|")]
            if raw_cols and raw_cols[0] == "":
                raw_cols = raw_cols[1:]
            if raw_cols and raw_cols[-1] == "":
                raw_cols = raw_cols[:-1]
            cols = raw_cols
            if not cols or not headers:
                continue
            # 对齐列数（多余列截断，缺少列补空）
            if len(cols) < len(headers):
                cols = cols + [""] * (len(headers) - len(cols))
            elif len(cols) > len(headers):
                cols = cols[:len(headers)]
            row = {headers[i]: cols[i] for i in range(len(headers))}
            rows.append(row)
        return rows

    meeting_info_block = _extract_block("会议信息")
    actions_block = _extract_block("行动项与决策")
    dept_block = _extract_block("部门汇报摘要") or _extract_block("关键部门汇报")
    opening_block = _extract_block("晨会开场") or _extract_block("会议开场")
    meeting_time_block = _extract_block("会议时间")

    json_obj = {
        "base_name": base_name,
        "markdown_path": md_path,
        "created_at": base_ts,
        "sections": {
            "会议信息": _parse_meeting_info(meeting_info_block or ""),
            "晨会开场/会议开场": opening_block or "",
            "部门汇报": dept_block or "",
            "行动项与决策_raw": actions_block or "",
            "行动项与决策": _parse_md_table(actions_block or ""),
            "会议时间": meeting_time_block or "",
        },
        "markdown": content,
    }

    json_path = os.path.join(base_dir, f"{base_name}.json")
    try:
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(json_obj, jf, ensure_ascii=False, indent=2)
        # 避免 Windows 控制台编码问题（例如 cp936 无法输出 emoji）
        result = f"已归档至：{md_path}；JSON：{json_path}"
    except Exception:
        result = f"已归档至：{md_path}（JSON 归档失败）"
    return result