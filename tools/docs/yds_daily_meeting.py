# yds_daily_meeting.py
# YDS AI 公司每日晨会自动化流程（CrewAI 格式）
# 适用于 CrewAI Studio "Deploy from Code" 功能

from crewai import Agent, Task, Crew
from Struc.Agents.ceo.define import general_manager
from Struc.Agents.planning_director.define import planning_director
from Struc.Agents.finance_director.define import finance_director
from Struc.Agents.resource_admin.define import resource_admin
from Struc.Agents.marketing_director.define import marketing_director
from Struc.Agents.dev_team.dev_director.define import dev_director

# 创建 YDS AI 公司晨会 Crew
yds_daily_meeting = Crew(
    agents=[
        general_manager,
        planning_director,
        finance_director,
        resource_admin,
        marketing_director,
        dev_director
    ],
    tasks=[
        Task(
            description="作为总经理，主持今日晨会，听取各部门汇报 DeWatermark AI 项目进展",
            expected_output="结构化晨会纪要，包含各部门摘要、风险项与行动项",
            agent=general_manager,
            human_input=False
        ),
        Task(
            description="作为企划总监，汇报 DeWatermark AI 的市场分析、用户反馈与产品定位建议",
            expected_output="中文市场分析摘要，含用户画像与竞品对比",
            agent=planning_director,
            human_input=False
        ),
        Task(
            description="作为财务总监，汇报当前收支、成本结构与首月收入预测",
            expected_output="财务简报，含盈亏平衡点与定价建议",
            agent=finance_director,
            human_input=False
        ),
        Task(
            description="作为资源与行政总监，汇报合同状态、设备资源使用情况与合规检查结果",
            expected_output="资源与法务状态摘要",
            agent=resource_admin,
            human_input=False
        ),
        Task(
            description="作为市场总监，汇报推广内容产出、用户增长数据与转化策略",
            expected_output="推广计划与用户反馈摘要",
            agent=marketing_director,
            human_input=False
        ),
        Task(
            description="作为开发总监，汇报 DeWatermark AI 的开发进度、技术风险与下一步计划",
            expected_output="开发状态报告，含延迟风险与资源需求",
            agent=dev_director,
            human_input=False
        )
    ],
    verbose=True,
    memory=False,  # 暂不启用长期记忆，避免干扰
    cache=False,   # 每日内容不同，禁用缓存
    max_rpm=100
)

# 主执行入口（可选）
if __name__ == "__main__":
    print("🚀 启动 YDS AI 公司每日晨会...")
    result = yds_daily_meeting.kickoff()
    print("\n✅ 晨会结束，完整纪要如下：\n")
    print(result)