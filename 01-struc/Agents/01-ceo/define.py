# -*- coding: utf-8 -*-
"""
统一 define.py 骨架（最小可运行注册） - 首席执行官
说明：读取 role.meta.json，返回可用的 AgentStub 实例。
"""

import os
import json


class AgentStub:
    def __init__(self, meta: dict):
        self.meta = meta

    def info(self) -> dict:
        return self.meta


def _meta_path() -> str:
    return os.path.join(os.path.dirname(__file__), "role.meta.json")


def load_meta() -> dict:
    with open(_meta_path(), "r", encoding="utf-8") as f:
        return json.load(f)


def register() -> AgentStub:
    return AgentStub(load_meta())