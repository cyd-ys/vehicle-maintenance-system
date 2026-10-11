"""在线预约核心接口（论文 4.4 / 4.5）：时段容量校验 + 事务控制 + 状态机。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, serializers
from ..database import get_db
from ..deps import require_user
from ..response import ok
from ..schemas import OrderStatusIn, ReservationCreateIn
from ..utils import gen_order_no, paginate, write_log

router = APIRouter(prefix="/api/reservations", tags=["预约订单"])

# 占用时段的订单状态集合
OCCUPYING_STATUS = (
    models.OrderStatus.PENDING,
    models.OrderStatus.CONFIRMED,
    models.OrderStatus.IN_SERVICE,
)


def _count_occupying(db: Session, slot_id: int) -> int:
    return int(
        db.execute(
            select(func.count()).select_from(models.Reservation).where(
                models.Reservation.slot_id == slot_id,
                models.Reservation.status.in_(OCCUPYING_STATUS),
            )
        ).scalar_one()
    )


@router.post("", summary="提交预约订单")
def create_reservation(
    payload: ReservationCreateIn,
    user: models.SysUser = Depends(require_user),
    db: Session = Depends(get_db),
):
    # 1) 车辆归属校验
    vehicle = db.get(models.Vehicle, payload.vehicle_id)
    if not vehicle or vehicle.user_id != user.id:
        raise HTTPException(status_code=400, detail="车辆不存在或不属于当前用户")

    # 2) 门店校验
    store = db.get(models.Store, payload.store_id)
    if not store or store.status != models.StoreStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="门店不存在或已停用")

    # 3) 项目归属与状态校验
    item = db.get(models.ServiceItem, payload.item_id)
    if not item or item.store_id != store.id:
        raise HTTPException(status_code=400, detail="养护项目不存在或不属于该门店")
    if item.status != models.CommonStatus.ENABLED:
        raise HTTPException(status_code=400, detail="该养护项目已停止预约")

    # 4) 时段校验
    slot = db.get(models.ServiceSlot, payload.slot_id)
    if not slot or slot.store_id != store.id:
        raise HTTPException(status_code=400, detail="服务时段不存在或不属于该门店")

    try:
        # 事务开始：行锁住目标时段，避免并发写入导致超额预约
        if not db.bind.dialect.name == "sqlite":
            slot = db.execute(
                select(models.ServiceSlot).where(models.ServiceSlot.id == payload.slot_id).with_for_update()
            ).scalars().first()

        booked = _count_occupying(db, slot.id)
        if booked >= slot.capacity:
            raise HTTPException(status_code=409, detail="该时段预约名额已满，请选择其他时段")
        slot.booked = booked + 1  # 容量扣减

        reservation = models.Reservation(
            order_no=gen_order_no(),
            user_id=user.id,
            vehicle_id=vehicle.id,
            store_id=store.id,
            item_id=item.id,
            slot_id=slot.id,
            item_name=item.name,
            item_price=item.price,
            duration=item.duration,
            total_price=item.price,
            slot_date=slot.slot_date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status=models.OrderStatus.PENDING,
            contact_name=payload.contact_name or user.real_name,
            contact_phone=payload.contact_phone or user.phone,
            remark=payload.remark,
        )
        db.add(reservation)
        db.flush()
        write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
                  action="提交预约", target_type="reservation", target_id=reservation.id,
                  detail=f"订单 {reservation.order_no} 门店:{store.name} 项目:{item.name}")
        db.commit()  # 订单写入与容量扣减同一事务，任一步失败整体回滚
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"预约提交失败：{exc}")

    db.refresh(reservation)
    return ok(serializers.reservation_dict(reservation), "预约提交成功，等待门店受理")


@router.get("", summary="查询我的预约订单")
def list_my_reservations(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    user: models.SysUser = Depends(require_user),
    db: Session = Depends(get_db),
):
    stmt = select(models.Reservation).where(models.Reservation.user_id == user.id)
    if status:
        stmt = stmt.where(models.Reservation.status == status)
    stmt = stmt.order_by(models.Reservation.id.desc())

    result = paginate(db, stmt, page, page_size)
    result["items"] = [serializers.reservation_dict(r) for r in result["items"]]
    return ok(result)


@router.get("/{reservation_id}", summary="查询预约订单详情")
def get_reservation(reservation_id: int, user: models.SysUser = Depends(require_user), db: Session = Depends(get_db)):
    reservation = db.get(models.Reservation, reservation_id)
    if not reservation or reservation.user_id != user.id:
        raise HTTPException(status_code=404, detail="订单不存在或无权查看")
    return ok(serializers.reservation_dict(reservation))


@router.patch("/{reservation_id}/status", summary="更新订单状态（用户取消）")
def update_reservation_status(
    reservation_id: int,
    payload: OrderStatusIn,
    user: models.SysUser = Depends(require_user),
    db: Session = Depends(get_db),
):
    reservation = db.get(models.Reservation, reservation_id)
    if not reservation or reservation.user_id != user.id:
        raise HTTPException(status_code=404, detail="订单不存在或无权操作")

    # 用户仅可取消，且仅在门店受理前（待受理 / 已确认）
    if payload.status != models.OrderStatus.CANCELLED:
        raise HTTPException(status_code=403, detail="用户端仅支持取消订单")
    if models.OrderStatus.CANCELLED not in models.ORDER_TRANSITIONS[reservation.status]:
        raise HTTPException(status_code=400, detail="当前订单状态不允许取消")

    try:
        slot = db.execute(
            select(models.ServiceSlot).where(models.ServiceSlot.id == reservation.slot_id).with_for_update()
        ).scalars().first() if db.bind.dialect.name != "sqlite" else db.get(models.ServiceSlot, reservation.slot_id)

        reservation.status = models.OrderStatus.CANCELLED
        reservation.cancelled_at = datetime.now()
        if slot:
            slot.booked = max(0, (slot.booked or 1) - 1)  # 取消时恢复时段容量
        write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
                  action="取消预约", target_type="reservation", target_id=reservation.id,
                  detail=f"订单 {reservation.order_no} 已取消")
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"取消失败：{exc}")

    db.refresh(reservation)
    return ok(serializers.reservation_dict(reservation), "订单已取消")
