"""门店端接口（论文 2.3.2 / 4.5）：门店资料、项目管理、时段配置、订单受理与统计。"""
from datetime import date as date_cls
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, serializers
from ..database import get_db
from ..deps import require_store
from ..response import ok
from ..schemas import ItemIn, OrderStatusIn, SlotGenerateIn, SlotIn, StoreUpdateIn
from ..utils import paginate, write_log

router = APIRouter(prefix="/api/store", tags=["门店端"])

# 门店端允许执行的订单状态流转
STORE_ALLOWED_TARGETS = {
    models.OrderStatus.CONFIRMED,
    models.OrderStatus.REJECTED,
    models.OrderStatus.IN_SERVICE,
    models.OrderStatus.COMPLETED,
}


def _current_store(user: models.SysUser = Depends(require_store), db: Session = Depends(get_db)) -> models.Store:
    if not user.store_id:
        raise HTTPException(status_code=400, detail="当前账号未绑定门店，请联系管理员")
    store = db.get(models.Store, user.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    return store


# ---------------- 门店资料 ----------------
@router.get("/profile", summary="获取本门店资料")
def get_profile(store: models.Store = Depends(_current_store)):
    return ok(serializers.store_dict(store))


@router.put("/profile", summary="维护本门店资料")
def update_profile(
    payload: StoreUpdateIn,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    for field in ("name", "address", "phone", "description", "open_time", "close_time"):
        value = getattr(payload, field)
        if value is not None:
            setattr(store, field, value)
    write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
              action="维护门店资料", target_type="store", target_id=store.id)
    db.commit()
    db.refresh(store)
    return ok(serializers.store_dict(store), "门店资料已更新")


# ---------------- 养护项目 ----------------
@router.get("/items", summary="查询本门店养护项目")
def list_items(store: models.Store = Depends(_current_store), db: Session = Depends(get_db)):
    rows = db.execute(
        select(models.ServiceItem).where(models.ServiceItem.store_id == store.id).order_by(models.ServiceItem.id.desc())
    ).scalars().all()
    return ok([serializers.item_dict(i) for i in rows])


@router.post("/items", summary="新增养护项目")
def create_item(
    payload: ItemIn,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    item = models.ServiceItem(store_id=store.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok(serializers.item_dict(item), "项目已新增")


@router.put("/items/{item_id}", summary="编辑养护项目")
def update_item(
    item_id: int,
    payload: ItemIn,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    item = db.get(models.ServiceItem, item_id)
    if not item or item.store_id != store.id:
        raise HTTPException(status_code=404, detail="项目不存在或无权操作")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return ok(serializers.item_dict(item), "项目已更新")


@router.delete("/items/{item_id}", summary="删除养护项目")
def delete_item(
    item_id: int,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    item = db.get(models.ServiceItem, item_id)
    if not item or item.store_id != store.id:
        raise HTTPException(status_code=404, detail="项目不存在或无权操作")
    item.status = models.CommonStatus.DISABLED  # 软删除，保留历史订单快照可读
    db.commit()
    return ok(message="项目已停用（历史订单不受影响）")


# ---------------- 服务时段 ----------------
@router.get("/slots", summary="查询本门店服务时段")
def list_slots(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    store: models.Store = Depends(_current_store),
    db: Session = Depends(get_db),
):
    stmt = select(models.ServiceSlot).where(models.ServiceSlot.store_id == store.id)
    if start_date:
        stmt = stmt.where(models.ServiceSlot.slot_date >= date_cls.fromisoformat(start_date))
    if end_date:
        stmt = stmt.where(models.ServiceSlot.slot_date <= date_cls.fromisoformat(end_date))
    rows = db.execute(stmt.order_by(models.ServiceSlot.slot_date.asc(), models.ServiceSlot.start_time.asc())).scalars().all()
    return ok([serializers.slot_dict(s) for s in rows])


@router.post("/slots", summary="新增服务时段")
def create_slot(
    payload: SlotIn,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    if payload.start_time >= payload.end_time:
        raise HTTPException(status_code=400, detail="开始时间必须早于结束时间")
    dup = db.execute(
        select(models.ServiceSlot).where(
            models.ServiceSlot.store_id == store.id,
            models.ServiceSlot.slot_date == payload.slot_date,
            models.ServiceSlot.start_time == payload.start_time,
        )
    ).scalars().first()
    if dup:
        raise HTTPException(status_code=400, detail="该时段已存在")

    slot = models.ServiceSlot(store_id=store.id, **payload.model_dump())
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return ok(serializers.slot_dict(slot), "时段已新增")


@router.delete("/slots/{slot_id}", summary="删除服务时段")
def delete_slot(
    slot_id: int,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    slot = db.get(models.ServiceSlot, slot_id)
    if not slot or slot.store_id != store.id:
        raise HTTPException(status_code=404, detail="时段不存在或无权操作")
    active = db.execute(
        select(models.Reservation).where(
            models.Reservation.slot_id == slot_id,
            models.Reservation.status.in_((
                models.OrderStatus.PENDING, models.OrderStatus.CONFIRMED, models.OrderStatus.IN_SERVICE
            )),
        )
    ).scalars().first()
    if active:
        raise HTTPException(status_code=400, detail="该时段存在有效预约，暂不能删除")
    db.delete(slot)
    db.commit()
    return ok(message="时段已删除")


@router.post("/slots/generate", summary="批量生成服务时段")
def generate_slots(
    payload: SlotGenerateIn,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")
    if not payload.ranges:
        raise HTTPException(status_code=400, detail="请至少配置一个时段区间")

    created = 0
    day = payload.start_date
    while day <= payload.end_date:
        for rng in payload.ranges:
            if rng.start_time >= rng.end_time:
                continue
            dup = db.execute(
                select(models.ServiceSlot).where(
                    models.ServiceSlot.store_id == store.id,
                    models.ServiceSlot.slot_date == day,
                    models.ServiceSlot.start_time == rng.start_time,
                )
            ).scalars().first()
            if dup:
                continue
            db.add(models.ServiceSlot(
                store_id=store.id, slot_date=day, start_time=rng.start_time,
                end_time=rng.end_time, capacity=payload.capacity,
            ))
            created += 1
        day += timedelta(days=1)
    db.commit()
    return ok({"created": created}, f"已生成 {created} 个时段")


# ---------------- 订单处理 ----------------
@router.get("/orders", summary="分页查询本门店预约订单")
def list_orders(
    status: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    store: models.Store = Depends(_current_store),
    db: Session = Depends(get_db),
):
    stmt = select(models.Reservation).where(models.Reservation.store_id == store.id)
    if status:
        stmt = stmt.where(models.Reservation.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(models.Reservation.order_no.like(like) | models.Reservation.item_name.like(like))
    stmt = stmt.order_by(models.Reservation.id.desc())
    result = paginate(db, stmt, page, page_size)
    result["items"] = [serializers.reservation_dict(r) for r in result["items"]]
    return ok(result)


@router.patch("/orders/{order_id}/status", summary="门店处理订单（确认/拒绝/开始服务/完成）")
def update_order_status(
    order_id: int,
    payload: OrderStatusIn,
    store: models.Store = Depends(_current_store),
    user: models.SysUser = Depends(require_store),
    db: Session = Depends(get_db),
):
    reservation = db.get(models.Reservation, order_id)
    if not reservation or reservation.store_id != store.id:
        raise HTTPException(status_code=404, detail="订单不存在或无权操作")

    target = payload.status
    if target not in STORE_ALLOWED_TARGETS:
        raise HTTPException(status_code=403, detail="门店端不支持该状态操作")
    if target not in models.ORDER_TRANSITIONS[reservation.status]:
        raise HTTPException(
            status_code=400,
            detail=f"非法状态流转：{models.ORDER_STATUS_TEXT[reservation.status]} → {models.ORDER_STATUS_TEXT.get(target, target)}",
        )
    if target == models.OrderStatus.REJECTED and not (payload.reason and payload.reason.strip()):
        raise HTTPException(status_code=400, detail="拒绝订单时必须填写拒绝原因")

    try:
        now = datetime.now()
        reservation.status = target
        if target == models.OrderStatus.CONFIRMED:
            reservation.confirmed_at = now
        elif target == models.OrderStatus.COMPLETED:
            reservation.completed_at = now
            if payload.service_note:
                reservation.service_note = payload.service_note
        elif target == models.OrderStatus.REJECTED:
            reservation.reject_reason = payload.reason
            # 拒绝后释放时段容量
            slot = db.get(models.ServiceSlot, reservation.slot_id)
            if slot:
                slot.booked = max(0, (slot.booked or 1) - 1)

        write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
                  action=f"订单{models.ORDER_STATUS_TEXT.get(target, target)}",
                  target_type="reservation", target_id=reservation.id,
                  detail=f"订单 {reservation.order_no}")
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"操作失败：{exc}")

    db.refresh(reservation)
    return ok(serializers.reservation_dict(reservation), "订单状态已更新")


@router.get("/stats", summary="门店经营数据统计")
def stats(store: models.Store = Depends(_current_store), db: Session = Depends(get_db)):
    base = select(func.count()).select_from(models.Reservation).where(models.Reservation.store_id == store.id)
    total = int(db.execute(base).scalar_one())

    by_status = {}
    for st in [models.OrderStatus.PENDING, models.OrderStatus.CONFIRMED, models.OrderStatus.IN_SERVICE,
               models.OrderStatus.COMPLETED, models.OrderStatus.CANCELLED, models.OrderStatus.REJECTED]:
        by_status[st] = int(db.execute(
            select(func.count()).select_from(models.Reservation).where(
                models.Reservation.store_id == store.id, models.Reservation.status == st
            )
        ).scalar_one())

    today = date_cls.today()
    today_count = int(db.execute(
        select(func.count()).select_from(models.Reservation).where(
            models.Reservation.store_id == store.id, models.Reservation.slot_date == today
        )
    ).scalar_one())

    revenue = db.execute(
        select(func.coalesce(func.sum(models.Reservation.total_price), 0)).where(
            models.Reservation.store_id == store.id,
            models.Reservation.status == models.OrderStatus.COMPLETED,
        )
    ).scalar_one()

    item_count = int(db.execute(
        select(func.count()).select_from(models.ServiceItem).where(models.ServiceItem.store_id == store.id)
    ).scalar_one())

    return ok({
        "total_orders": total,
        "today_orders": today_count,
        "by_status": by_status,
        "completed_revenue": float(revenue or 0),
        "item_count": item_count,
        "order_status_text": models.ORDER_STATUS_TEXT,
    })
