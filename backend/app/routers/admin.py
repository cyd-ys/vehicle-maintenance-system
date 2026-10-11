"""管理端接口（论文 2.3.3 / 4.6）：用户、门店审核、项目管理、订单查询、操作日志。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, serializers
from ..database import get_db
from ..deps import require_admin
from ..response import ok
from ..schemas import ItemStatusIn, StoreCreateIn, StoreReviewIn, UserStatusIn
from ..security import hash_password
from ..utils import paginate, write_log

router = APIRouter(prefix="/api/admin", tags=["管理端"])


# ---------------- 用户管理 ----------------
@router.get("/users", summary="分页查询用户")
def list_users(
    role: str | None = Query(default=None),
    status: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(models.SysUser)
    if role:
        stmt = stmt.where(models.SysUser.role == role)
    if status is not None:
        stmt = stmt.where(models.SysUser.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(models.SysUser.username.like(like) | models.SysUser.real_name.like(like))
    stmt = stmt.order_by(models.SysUser.id.desc())
    result = paginate(db, stmt, page, page_size)
    result["items"] = [serializers.user_dict(u) for u in result["items"]]
    return ok(result)


@router.put("/users/{user_id}/status", summary="启用/停用用户")
def set_user_status(
    user_id: int,
    payload: UserStatusIn,
    admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(models.SysUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能停用当前登录的管理员账号")
    user.status = payload.status
    write_log(db, operator_id=admin.id, operator_name=admin.username, role=admin.role,
              action="停用账号" if payload.status == 0 else "启用账号",
              target_type="user", target_id=user.id, detail=f"账号 {user.username}")
    db.commit()
    return ok(serializers.user_dict(user), "操作成功")


# ---------------- 门店管理 ----------------
@router.get("/stores", summary="分页查询门店")
def list_stores(
    status: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(models.Store)
    if status is not None:
        stmt = stmt.where(models.Store.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(models.Store.name.like(like) | models.Store.address.like(like))
    stmt = stmt.order_by(models.Store.id.desc())
    result = paginate(db, stmt, page, page_size)
    result["items"] = [serializers.store_dict(s) for s in result["items"]]
    return ok(result)


@router.post("/stores", summary="新增门店并创建门店账号")
def create_store(
    payload: StoreCreateIn,
    admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    store = models.Store(
        name=payload.name, address=payload.address, phone=payload.phone,
        description=payload.description, open_time=payload.open_time or "09:00",
        close_time=payload.close_time or "18:00", status=payload.status,
    )
    db.add(store)
    db.flush()

    staff_username = None
    if payload.username and payload.password:
        dup = db.execute(select(models.SysUser).where(models.SysUser.username == payload.username)).scalars().first()
        if dup:
            db.rollback()
            raise HTTPException(status_code=400, detail="门店账号用户名已存在")
        staff = models.SysUser(
            username=payload.username,
            password_hash=hash_password(payload.password),
            real_name=payload.name + "管理员",
            role=models.Role.STORE,
            status=models.CommonStatus.ENABLED,
            store_id=store.id,
        )
        db.add(staff)
        staff_username = payload.username

    write_log(db, operator_id=admin.id, operator_name=admin.username, role=admin.role,
              action="新增门店", target_type="store", target_id=store.id,
              detail=f"门店 {store.name}" + (f"，账号 {staff_username}" if staff_username else ""))
    db.commit()
    db.refresh(store)
    return ok(serializers.store_dict(store), "门店创建成功")


@router.put("/stores/{store_id}/review", summary="审核门店（通过/停用）")
def review_store(
    store_id: int,
    payload: StoreReviewIn,
    admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    store = db.get(models.Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")
    store.status = payload.status
    label = {0: "待审核", 1: "审核通过", 2: "已停用"}.get(payload.status, str(payload.status))
    write_log(db, operator_id=admin.id, operator_name=admin.username, role=admin.role,
              action="门店审核", target_type="store", target_id=store.id, detail=f"门店 {store.name} → {label}")
    db.commit()
    db.refresh(store)
    return ok(serializers.store_dict(store), "门店状态已更新")


# ---------------- 项目管理 ----------------
@router.get("/items", summary="分页查询养护项目")
def list_items(
    store_id: int | None = Query(default=None),
    status: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(models.ServiceItem)
    if store_id:
        stmt = stmt.where(models.ServiceItem.store_id == store_id)
    if status is not None:
        stmt = stmt.where(models.ServiceItem.status == status)
    stmt = stmt.order_by(models.ServiceItem.id.desc())
    result = paginate(db, stmt, page, page_size)
    result["items"] = [serializers.item_dict(i) for i in result["items"]]
    return ok(result)


@router.put("/items/{item_id}/status", summary="启用/停用养护项目")
def set_item_status(
    item_id: int,
    payload: ItemStatusIn,
    admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    item = db.get(models.ServiceItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="项目不存在")
    item.status = payload.status
    write_log(db, operator_id=admin.id, operator_name=admin.username, role=admin.role,
              action="停用项目" if payload.status == 0 else "启用项目",
              target_type="service_item", target_id=item.id, detail=f"项目 {item.name}")
    db.commit()
    return ok(serializers.item_dict(item), "项目状态已更新")


# ---------------- 订单查询 ----------------
@router.get("/orders", summary="管理员分页查询预约订单")
def list_orders(
    status: str | None = Query(default=None),
    store_id: int | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    _admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(models.Reservation)
    if status:
        stmt = stmt.where(models.Reservation.status == status)
    if store_id:
        stmt = stmt.where(models.Reservation.store_id == store_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(models.Reservation.order_no.like(like) | models.Reservation.item_name.like(like))
    stmt = stmt.order_by(models.Reservation.id.desc())
    result = paginate(db, stmt, page, page_size)
    result["items"] = [serializers.reservation_dict(r) for r in result["items"]]
    return ok(result)


# ---------------- 操作日志 ----------------
@router.get("/logs", summary="分页查询操作日志")
def list_logs(
    action: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _admin: models.SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    stmt = select(models.OperationLog)
    if action:
        stmt = stmt.where(models.OperationLog.action.like(f"%{action}%"))
    stmt = stmt.order_by(models.OperationLog.id.desc())
    result = paginate(db, stmt, page, page_size)
    result["items"] = [serializers.log_dict(x) for x in result["items"]]
    return ok(result)


@router.get("/stats", summary="平台总览统计")
def stats(_admin: models.SysUser = Depends(require_admin), db: Session = Depends(get_db)):
    def count(model, *where):
        stmt = select(func.count()).select_from(model)
        for w in where:
            stmt = stmt.where(w)
        return int(db.execute(stmt).scalar_one())

    by_status = {}
    for st in [models.OrderStatus.PENDING, models.OrderStatus.CONFIRMED, models.OrderStatus.IN_SERVICE,
               models.OrderStatus.COMPLETED, models.OrderStatus.CANCELLED, models.OrderStatus.REJECTED]:
        by_status[st] = count(models.Reservation, models.Reservation.status == st)

    return ok({
        "user_count": count(models.SysUser, models.SysUser.role == models.Role.USER),
        "store_count": count(models.Store),
        "pending_store_count": count(models.Store, models.Store.status == models.StoreStatus.PENDING),
        "item_count": count(models.ServiceItem),
        "order_count": count(models.Reservation),
        "by_status": by_status,
        "order_status_text": models.ORDER_STATUS_TEXT,
    })
