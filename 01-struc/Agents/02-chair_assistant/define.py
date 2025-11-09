# -*- coding: utf-8 -*-
"""
统一 define.py 骨架（最小可运行注册） - 董事会助理
"""

import os
import json


class AgentStub:
    def __init__(self, meta: dict):
        self.meta = meta
    def info(self) -> dict:
        return self.meta


def load_meta() -> dict:
    meta_path = os.path.join(os.path.dirname(__file__), "role.meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def register() -> AgentStub:
    return AgentStub(load_meta())