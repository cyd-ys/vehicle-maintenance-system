"""ORM 数据模型（对应论文 3.4 数据库设计）。

核心实体：用户、车辆、门店、养护项目、服务时段、预约订单、操作日志。
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# 主键 / 外键统一使用这个类型。
# ⚠️ 不能直接写 BigInteger：**SQLite 的自增只对 `INTEGER PRIMARY KEY` 生效**，
# `BIGINT PRIMARY KEY` 不是 rowid 的别名，插入时不写 id 会直接报
# `NOT NULL constraint failed: xxx.id`。项目允许在无 MySQL 环境降级到 SQLite，
# 所以这里用 with_variant 在 SQLite 方言下降级为 INTEGER，
# MySQL 等其它方言仍保持 BIGINT（不影响既有表结构）。
ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


# ---- 角色枚举（论文 2.2）----
class Role:
    USER = "user"      # 普通用户
    STORE = "store"    # 门店工作人员
    ADMIN = "admin"    # 系统管理员


# ---- 通用状态 ----
class CommonStatus:
    DISABLED = 0
    ENABLED = 1


# ---- 门店状态 ----
class StoreStatus:
    PENDING = 0    # 待审核
    ACTIVE = 1     # 正常营业
    DISABLED = 2   # 已停用


# ---- 订单状态（论文 4.5 有限状态机）----
class OrderStatus:
    PENDING = "pending"        # 待受理
    CONFIRMED = "confirmed"    # 已确认
    IN_SERVICE = "in_service"  # 服务中
    COMPLETED = "completed"    # 已完成
    CANCELLED = "cancelled"    # 已取消
    REJECTED = "rejected"      # 已拒绝


ORDER_STATUS_TEXT = {
    OrderStatus.PENDING: "待受理",
    OrderStatus.CONFIRMED: "已确认",
    OrderStatus.IN_SERVICE: "服务中",
    OrderStatus.COMPLETED: "已完成",
    OrderStatus.CANCELLED: "已取消",
    OrderStatus.REJECTED: "已拒绝",
}

# 合法状态流转：当前状态 -> 允许流转到的状态集合
ORDER_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.REJECTED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.IN_SERVICE, OrderStatus.CANCELLED},
    OrderStatus.IN_SERVICE: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.REJECTED: set(),
}


class SysUser(Base):
    """用户表：通过 role 区分普通用户、门店工作人员和管理员。"""

    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str | None] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, index=True)
    # 头像访问路径（如 /uploads/avatars/u8_ab12cd.png），为空时前端退化为「首字母头像」
    avatar: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=Role.USER)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=CommonStatus.ENABLED)
    # 门店工作人员所属门店
    store_id: Mapped[int | None] = mapped_column(ID_TYPE, ForeignKey("store.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Vehicle(Base):
    """车辆档案表：一个用户可拥有多辆车。"""

    __tablename__ = "vehicle"
    __table_args__ = (UniqueConstraint("user_id", "plate_no", name="uq_vehicle_user_plate"),)

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("sys_user.id"), nullable=False, index=True)
    plate_no: Mapped[str] = mapped_column(String(20), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(50))
    model: Mapped[str | None] = mapped_column(String(50))
    mileage: Mapped[int | None] = mapped_column(Integer)
    remark: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["SysUser"] = relationship(back_populates="vehicles")


class Store(Base):
    """养护门店表。"""

    __tablename__ = "store"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)
    open_time: Mapped[str | None] = mapped_column(String(10), default="09:00")
    close_time: Mapped[str | None] = mapped_column(String(10), default="18:00")
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=StoreStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    items: Mapped[list["ServiceItem"]] = relationship(back_populates="store", cascade="all, delete-orphan")
    slots: Mapped[list["ServiceSlot"]] = relationship(back_populates="store", cascade="all, delete-orphan")


class ServiceItem(Base):
    """养护服务项目表。"""

    __tablename__ = "service_item"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("store.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=60)  # 预计服务时长（分钟）
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=CommonStatus.ENABLED)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    store: Mapped["Store"] = relationship(back_populates="items")


class ServiceSlot(Base):
    """服务时段表：门店可预约时段及容量。"""

    __tablename__ = "service_slot"
    __table_args__ = (
        UniqueConstraint("store_id", "slot_date", "start_time", name="uq_slot_store_date_start"),
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("store.id"), nullable=False, index=True)
    slot_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    booked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 已占用容量
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    store: Mapped["Store"] = relationship(back_populates="slots")


class Reservation(Base):
    """预约订单表：保留下单时的项目名称与价格快照。"""

    __tablename__ = "reservation"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("sys_user.id"), nullable=False, index=True)
    vehicle_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("vehicle.id"), nullable=False)
    store_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("store.id"), nullable=False, index=True)
    item_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("service_item.id"), nullable=False)
    slot_id: Mapped[int] = mapped_column(ID_TYPE, ForeignKey("service_slot.id"), nullable=False, index=True)

    # 快照字段：避免项目调整影响历史订单
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    item_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    slot_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime] = mapped_column(Time, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=OrderStatus.PENDING, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(50))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    remark: Mapped[str | None] = mapped_column(String(255))
    reject_reason: Mapped[str | None] = mapped_column(String(255))
    service_note: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["SysUser"] = relationship()
    vehicle: Mapped["Vehicle"] = relationship()
    store: Mapped["Store"] = relationship()
    item: Mapped["ServiceItem"] = relationship()
    slot: Mapped["ServiceSlot"] = relationship()


class OperationLog(Base):
    """关键操作日志表（论文 3.5 操作审计）。"""

    __tablename__ = "operation_log"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    operator_id: Mapped[int | None] = mapped_column(ID_TYPE)
    operator_name: Mapped[str | None] = mapped_column(String(50))
    role: Mapped[str | None] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[int | None] = mapped_column(ID_TYPE)
    detail: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EmailCode(Base):
    """邮箱验证码表：用于邮箱注册 / 找回密码等场景。"""

    __tablename__ = "email_code"

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), nullable=False, default="register")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

