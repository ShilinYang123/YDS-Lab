# main.py
import schedule
import time
from datetime import datetime
from agents.ceo import run_daily_check
from utils.logger import log_meeting
from agents.admin import get_admin_update
from agents.dev import get_dev_update


def hold_morning_meeting():
    print("🔔【YDS AI公司晨会】开始（北京时间 09:00）")

    meeting_id = f"MTG-{datetime.now().strftime('%Y%m%d-%H%M')}"
    log_meeting(meeting_id, "# 【YDS虚拟晨会】\n\n时间：" + str(datetime.now()))

    # 总经理开场
    ceo_intro = "各位同事，早上好。现在开始今日晨会，请依次汇报。"
    print(f"[CEO] {ceo_intro}")
    log_meeting(meeting_id, "- **总经理**：" + ceo_intro)

    # 企划部汇报（模拟）
    plan_report = "AI去水印项目已完成竞品分析，用户调研显示需求强烈，建议优先开发Tauri桌面版。"
    print(f"[企划部] {plan_report}")
    log_meeting(meeting_id, "- **企划部**：" + plan_report)

    # 财务部汇报（模拟）
    finance_status = "当前账户余额 ¥1,876.43，本月支出主要用于域名与服务器，预计下月可实现盈亏平衡。"
    print(f"[财务部] {finance_status}")
    log_meeting(meeting_id, "- **财务部**：" + finance_status)

    # 市场部汇报（模拟）
    market_update = "准备发布第一条推广视频，标题为《不用上传也能去水印？》计划在B站和知乎同步发布。"
    print(f"[市场部] {market_update}")
    log_meeting(meeting_id, "- **市场部**：" + market_update)

    # 资源与行政部汇报（模拟）
    admin_update = get_admin_update()
    print(f"[资源与行政部] {admin_update}")
    log_meeting(meeting_id, "- **资源与行政部**：" + admin_update)

    # 项目开发部汇报（模拟）
    dev_update = get_dev_update()
    print(f"[项目开发部] {dev_update}")
    log_meeting(meeting_id, "- **项目开发部**：" + dev_update)

    # 总经理总结
    ceo_summary = "今日重点：推进DeWatermark AI上线。无其他事项，散会。"
    print(f"[CEO] {ceo_summary}")
    log_meeting(meeting_id, "- **总经理总结**：" + ceo_summary)

    print("✅ 晨会结束，记录已保存。")


# 设置每日9点自动运行
schedule.every().day.at("09:00").do(hold_morning_meeting)


# 也可以手动触发
if __name__ == "__main__":
    hold_morning_meeting()  # 可立即测试一次
    while True:
        schedule.run_pending()
        time.sleep(1)