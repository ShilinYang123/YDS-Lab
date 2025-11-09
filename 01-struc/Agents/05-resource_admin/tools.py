def review_contract(contract_text: str) -> str:
    """合同初审（模拟）"""
    if "无限责任" in contract_text or "数据所有权" in contract_text:
        return "⚠️ 合规风险：建议删除'无限责任'条款，明确数据归属YDS公司"
    return "✅ 合同无重大风险，可推进"

def check_compliance(doc_type: str) -> list:
    """合规检查清单"""
    if doc_type == "desktop_app":
        return [
            "✅ 用户数据本地处理（不上传）",
            "✅ 隐私政策弹窗",
            "✅ 软著登记完成"
        ]
    return ["ℹ️ 未定义该类型合规要求"]

def allocate_resource(request: str, device: str = "guiyang-pc") -> str:
    """资源调度"""
    return f"📅 已为'{request}'分配设备：{device}，使用时段：今日 14:00-18:00"