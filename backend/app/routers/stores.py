"""门店与养护项目浏览、可用时段查询（用户端公开接口，论文 4.3 / 4.4）。"""
from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, serializers
from ..database import get_db
from ..deps import get_current_user
from ..response import ok
from ..utils import paginate

router = APIRouter(prefix="/api", tags=["门店与项目"])


@router.get("/stores", summary="分页查询可用门店")
def list_stores(
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(models.Store).where(models.Store.status == models.StoreStatus.ACTIVE)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(models.Store.name.like(like) | models.Store.address.like(like))
    stmt = stmt.order_by(models.Store.id.asc())

    result = paginate(db, stmt, page, page_size)
    items = []
    for s in result["items"]:
        cnt = db.execute(
            select(models.ServiceItem).where(
                models.ServiceItem.store_id == s.id,
                models.ServiceItem.status == models.CommonStatus.ENABLED,
            )
        ).scalars().all()
        items.append(serializers.store_dict(s, item_count=len(cnt)))
    result["items"] = items
    return ok(result)


@router.get("/stores/{store_id}", summary="查询门店详情")
def get_store(store_id: int, db: Session = Depends(get_db)):
    store = db.get(models.Store, store_id)
    if not store or store.status != models.StoreStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="门店不存在或未开放")
    return ok(serializers.store_dict(store))


@router.get("/stores/{store_id}/items", summary="查询指定门店的养护项目")
def list_store_items(store_id: int, db: Session = Depends(get_db)):
    store = db.get(models.Store, store_id)
    if not store or store.status != models.StoreStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="门店不存在或未开放")
    rows = db.execute(
        select(models.ServiceItem).where(
            models.ServiceItem.store_id == store_id,
            models.ServiceItem.status == models.CommonStatus.ENABLED,
        ).order_by(models.ServiceItem.id.asc())
    ).scalars().all()
    return ok([serializers.item_dict(i) for i in rows])


@router.get("/slots", summary="查询指定日期的可用服务时段")
def list_available_slots(
    store_id: int = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    try:
        slot_date = date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD")

    store = db.get(models.Store, store_id)
    if not store or store.status != models.StoreStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="门店不存在或未开放")

    rows = db.execute(
        select(models.ServiceSlot).where(
            models.ServiceSlot.store_id == store_id,
            models.ServiceSlot.slot_date == slot_date,
        ).order_by(models.ServiceSlot.start_time.asc())
    ).scalars().all()
    return ok([serializers.slot_dict(s) for s in rows])
