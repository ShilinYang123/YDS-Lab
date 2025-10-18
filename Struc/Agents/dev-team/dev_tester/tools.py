def run_functional_test(test_case: dict) -> dict:
    """执行功能测试（模拟）"""
    filename = test_case["file"]
    if "1GB" in filename:
        return {"status": "fail", "error": "界面无响应", "severity": "high"}
    return {"status": "pass", "time_sec": 42}

def measure_performance(video_size_mb: int, mode: str) -> float:
    """测量处理时间"""
    base_time = video_size_mb * 0.4  # 本地模式
    if mode == "cloud":
        return base_time * 0.2
    return base_time

def generate_test_report(results: list) -> str:
    """生成测试报告"""
    passed = sum(1 for r in results if r["status"] == "pass")
    total = len(results)
    return f"✅ 通过率：{passed}/{total}\n⚠️ 发现{total-passed}个问题，详见报告。"