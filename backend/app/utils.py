"""通用工具：订单号生成、操作日志写入、分页封装。"""
import random
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models


def gen_order_no() -> str:
    """生成订单号：MY + 年月日时分秒 + 4 位随机数。"""
    return "MY" + datetime.now().strftime("%Y%m%d%H%M%S") + f"{random.randint(0, 9999):04d}"


def write_log(
    db: Session,
    *,
    operator_id: int | None,
    operator_name: str | None,
    role: str | None,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: str | None = None,
) -> None:
    """写入关键操作日志（不提交，由调用方统一提交事务）。"""
    db.add(
        models.OperationLog(
            operator_id=operator_id,
            operator_name=operator_name,
            role=role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
        )
    )


def paginate(db: Session, stmt, page: int, page_size: int) -> dict:
    """统一分页：返回 total / page / page_size / items 结构。"""
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return {"total": int(total), "page": page, "page_size": page_size, "items": rows}
