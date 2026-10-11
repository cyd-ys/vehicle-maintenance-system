"""ORM 对象 -> 字典的序列化辅助函数。"""
from . import models


def _dt(v):
    return v.strftime("%Y-%m-%d %H:%M:%S") if v else None


def _d(v):
    return v.strftime("%Y-%m-%d") if v else None


def _t(v):
    return v.strftime("%H:%M") if v else None


def user_dict(u: models.SysUser) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "real_name": u.real_name,
        "phone": u.phone,
        "email": u.email,
        "avatar": u.avatar,
        "role": u.role,
        "status": u.status,
        "store_id": u.store_id,
        "created_at": _dt(u.created_at),
    }


def vehicle_dict(v: models.Vehicle) -> dict:
    return {
        "id": v.id,
        "user_id": v.user_id,
        "plate_no": v.plate_no,
        "brand": v.brand,
        "model": v.model,
        "mileage": v.mileage,
        "remark": v.remark,
        "created_at": _dt(v.created_at),
    }


def store_dict(s: models.Store, item_count: int | None = None) -> dict:
    data = {
        "id": s.id,
        "name": s.name,
        "address": s.address,
        "phone": s.phone,
        "description": s.description,
        "open_time": s.open_time,
        "close_time": s.close_time,
        "status": s.status,
        "created_at": _dt(s.created_at),
    }
    if item_count is not None:
        data["item_count"] = item_count
    return data


def item_dict(i: models.ServiceItem) -> dict:
    return {
        "id": i.id,
        "store_id": i.store_id,
        "name": i.name,
        "category": i.category,
        "duration": i.duration,
        "price": float(i.price or 0),
        "description": i.description,
        "status": i.status,
        "created_at": _dt(i.created_at),
    }


def slot_dict(s: models.ServiceSlot) -> dict:
    remaining = max(0, (s.capacity or 0) - (s.booked or 0))
    return {
        "id": s.id,
        "store_id": s.store_id,
        "slot_date": _d(s.slot_date),
        "start_time": _t(s.start_time),
        "end_time": _t(s.end_time),
        "capacity": s.capacity,
        "booked": s.booked,
        "remaining": remaining,
    }


def reservation_dict(r: models.Reservation) -> dict:
    return {
        "id": r.id,
        "order_no": r.order_no,
        "user_id": r.user_id,
        "vehicle_id": r.vehicle_id,
        "plate_no": r.vehicle.plate_no if r.vehicle else None,
        "store_id": r.store_id,
        "store_name": r.store.name if r.store else None,
        "item_id": r.item_id,
        "item_name": r.item_name,
        "item_price": float(r.item_price or 0),
        "duration": r.duration,
        "total_price": float(r.total_price or 0),
        "slot_id": r.slot_id,
        "slot_date": _d(r.slot_date),
        "start_time": _t(r.start_time),
        "end_time": _t(r.end_time),
        "status": r.status,
        "status_text": models.ORDER_STATUS_TEXT.get(r.status, r.status),
        "contact_name": r.contact_name,
        "contact_phone": r.contact_phone,
        "remark": r.remark,
        "reject_reason": r.reject_reason,
        "service_note": r.service_note,
        "created_at": _dt(r.created_at),
        "confirmed_at": _dt(r.confirmed_at),
        "completed_at": _dt(r.completed_at),
        "cancelled_at": _dt(r.cancelled_at),
        "customer_name": r.user.username if r.user else None,
    }


def log_dict(log: models.OperationLog) -> dict:
    return {
        "id": log.id,
        "operator_id": log.operator_id,
        "operator_name": log.operator_name,
        "role": log.role,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "detail": log.detail,
        "created_at": _dt(log.created_at),
    }
