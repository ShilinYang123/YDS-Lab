def generate_social_copy(platform: str, product_name: str) -> str:
    """生成社交媒体文案"""
    templates = {
        "xiaohongshu": f"✨{product_name}｜学生党必备！完全离线去水印，保护隐私又免费～\n#AI工具 #视频剪辑",
        "bilibili": f"【神器推荐】不用上传也能去水印？{product_name}实测！",
        "wechat": f"还在为视频水印烦恼？这款国产工具彻底解决你的痛点"
    }
    return templates.get(platform, f"推广文案：{product_name}")

def analyze_user_feedback(feedback_list: list) -> dict:
    """分析用户反馈"""
    keywords = ["批量", "速度", "界面", "价格"]
    insights = {k: sum(k in fb for fb in feedback_list) for k in keywords}
    return {"top_requests": sorted(insights, key=insights.get, reverse=True)[:2]}

def estimate_conversion_rate(channel: str) -> float:
    """预估转化率"""
    rates = {"bilibili": 0.06, "xiaohongshu": 0.05, "zhihu": 0.04}
    return rates.get(channel, 0.03)