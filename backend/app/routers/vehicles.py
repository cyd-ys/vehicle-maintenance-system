"""车辆管理接口（论文 4.3）：用户维护自己的车辆档案。"""
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, serializers
from ..database import get_db
from ..deps import require_user
from ..response import ok
from ..schemas import VehicleIn

router = APIRouter(prefix="/api/vehicles", tags=["车辆管理"])

# 车牌号格式校验（与前端 utils/plate.js 规则保持一致）
#   普通车牌 7 位：省份简称 + 发牌机关字母 + 5 位序号
#   新能源车牌 8 位：小型车第 3 位为 D/F，大型车第 8 位为 D/F
#   全车牌不使用字母 I 和 O（易与 1、0 混淆）
_PROVINCE = "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼"
_LETTER = "A-HJ-NP-Z"       # 发牌机关字母，排除 I / O
_CHAR = "A-HJ-NP-Z0-9"      # 序号字符（数字或字母），排除 I / O

PLATE_RE = re.compile(
    rf"^[{_PROVINCE}][{_LETTER}](?:"
    rf"[{_CHAR}]{{4}}[0-9A-HJ-NP-Z挂学警港澳]"      # 普通车牌
    rf"|[{_CHAR}]{{5}}[DF]"                        # 大型新能源汽车
    rf"|[DF][{_CHAR}]{{5}}"                        # 小型新能源汽车
    rf")$"
)


def _validate_plate(plate: str):
    normalized = (plate or "").strip().upper()
    if "I" in normalized or "O" in normalized:
        raise HTTPException(status_code=400, detail="车牌号不包含字母 I 和 O，请确认后重新输入")
    if len(normalized) not in (7, 8):
        raise HTTPException(status_code=400, detail="普通车牌为 7 位，新能源车牌为 8 位，请检查后重新输入")
    if not normalized or not _PROVINCE.__contains__(normalized[0]):
        raise HTTPException(status_code=400, detail="车牌号第 1 位应为省份简称，如 京 / 湘 / 琼")
    if not PLATE_RE.match(normalized):
        if len(normalized) == 8:
            raise HTTPException(status_code=400, detail="新能源车牌需第 3 位或第 8 位为 D / F，请检查后重新输入")
        raise HTTPException(status_code=400, detail="车牌号格式不正确，请检查后重新输入")
    return normalized


@router.get("", summary="查询我的车辆列表")
def list_vehicles(user: models.SysUser = Depends(require_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(models.Vehicle).where(models.Vehicle.user_id == user.id).order_by(models.Vehicle.id.desc())
    ).scalars().all()
    return ok([serializers.vehicle_dict(v) for v in rows])


@router.post("", summary="新增车辆")
def create_vehicle(payload: VehicleIn, user: models.SysUser = Depends(require_user), db: Session = Depends(get_db)):
    plate = _validate_plate(payload.plate_no)
    dup = db.execute(
        select(models.Vehicle).where(models.Vehicle.user_id == user.id, models.Vehicle.plate_no == plate)
    ).scalars().first()
    if dup:
        raise HTTPException(status_code=400, detail="该车牌号已存在，请勿重复添加")

    vehicle = models.Vehicle(
        user_id=user.id,
        plate_no=plate,
        brand=payload.brand,
        model=payload.model,
        mileage=payload.mileage,
        remark=payload.remark,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return ok(serializers.vehicle_dict(vehicle), "车辆添加成功")


@router.put("/{vehicle_id}", summary="编辑车辆")
def update_vehicle(vehicle_id: int, payload: VehicleIn, user: models.SysUser = Depends(require_user), db: Session = Depends(get_db)):
    vehicle = db.get(models.Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != user.id:
        raise HTTPException(status_code=404, detail="车辆不存在或无权操作")

    plate = _validate_plate(payload.plate_no)
    dup = db.execute(
        select(models.Vehicle).where(
            models.Vehicle.user_id == user.id,
            models.Vehicle.plate_no == plate,
            models.Vehicle.id != vehicle_id,
        )
    ).scalars().first()
    if dup:
        raise HTTPException(status_code=400, detail="该车牌号已存在，请勿重复添加")

    vehicle.plate_no = plate
    vehicle.brand = payload.brand
    vehicle.model = payload.model
    vehicle.mileage = payload.mileage
    vehicle.remark = payload.remark
    db.commit()
    db.refresh(vehicle)
    return ok(serializers.vehicle_dict(vehicle), "车辆信息已更新")


@router.delete("/{vehicle_id}", summary="删除车辆")
def delete_vehicle(vehicle_id: int, user: models.SysUser = Depends(require_user), db: Session = Depends(get_db)):
    vehicle = db.get(models.Vehicle, vehicle_id)
    if not vehicle or vehicle.user_id != user.id:
        raise HTTPException(status_code=404, detail="车辆不存在或无权操作")

    used = db.execute(
        select(models.Reservation).where(
            models.Reservation.vehicle_id == vehicle_id,
            models.Reservation.status.in_([
                models.OrderStatus.PENDING,
                models.OrderStatus.CONFIRMED,
                models.OrderStatus.IN_SERVICE,
            ]),
        )
    ).scalars().first()
    if used:
        raise HTTPException(status_code=400, detail="该车辆存在进行中的预约，暂不能删除")

    db.delete(vehicle)
    db.commit()
    return ok(message="车辆已删除")
