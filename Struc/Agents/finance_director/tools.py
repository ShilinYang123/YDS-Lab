def calculate_budget(items: list) -> dict:
    """计算项目预算"""
    total = sum(item['cost'] for item in items)
    return {"items": items, "total": total}

def predict_revenue(users: int, conversion_rate: float, price: float) -> float:
    """预测收入"""
    return users * conversion_rate * price

def check_break_even(fixed_cost: float, price: float, cost_per_unit: float) -> int:
    """计算盈亏平衡点（用户数）"""
    if price <= cost_per_unit:
        return float('inf')  # 无法盈利
    return int(fixed_cost / (price - cost_per_unit)) + 1