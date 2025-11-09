#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
model_path_resolver 快速自测脚本
运行：python utils/test_model_path_resolver.py
"""

from utils.model_path_resolver import (
    list_agents,
    resolve_agent_path,
    get_shimmy_path,
    get_model_path,
    get_lama_model_path,
)

def main():
    print("=== 路径解析器自测 ===")

    # 智能体目录
    agents = list_agents()
    print(f"智能体目录数量: {len(agents)}")
    if agents:
        print("示例前3个:", agents[:3])

    try:
        mkt_dir = resolve_agent_path("07-marketing_director")
        print("营销总监目录:", mkt_dir)
    except Exception as e:
        print("解析营销总监目录失败:", e)

    # 模型路径
    print("Shimmy路径:", get_shimmy_path())
    print("LaMa模型文件:", get_lama_model_path())
    print("通用模型目录(示例=lama):", get_model_path("lama"))

    print("=== 自测完成 ===")

if __name__ == "__main__":
    main()