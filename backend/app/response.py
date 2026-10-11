"""统一响应结构（论文 2.4 可维护性：接口返回结构统一）。"""
from typing import Any


def ok(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(message: str, code: int = 1, data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}
