# -*- coding: utf-8 -*-
"""统一 define.py 骨架（最小可运行注册） - 备份与恢复"""
import os
import json


class AgentStub:
    def __init__(self, meta: dict):
        self.meta = meta
    def info(self) -> dict:
        return self.meta


def register() -> AgentStub:
    meta_path = os.path.join(os.path.dirname(__file__), "role.meta.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return AgentStub(meta)