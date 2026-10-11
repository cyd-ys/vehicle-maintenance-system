"""请求/响应 Pydantic 模型（论文 4.x 接口字段校验）。"""
import re
from datetime import date, time
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# 邮箱格式（不引入额外依赖，自行校验）
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


# ---------------- 认证 ----------------
class EmailCodeIn(BaseModel):
    """发送邮箱验证码。"""

    email: str = Field(min_length=5, max_length=120)
    purpose: str = Field(default="register", pattern="^(register|reset)$")

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v


class RegisterIn(BaseModel):
    """邮箱注册：需先通过 /api/auth/email/code 获取验证码。"""

    email: str = Field(min_length=5, max_length=120)
    code: str = Field(min_length=4, max_length=8)
    password: str = Field(min_length=6, max_length=64)
    username: Optional[str] = Field(default=None, max_length=50)
    real_name: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("username")
    @classmethod
    def _username_ok(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{3,50}", v):
            raise ValueError("用户名只能包含字母、数字和下划线，长度 3-50 位")
        return v

    @field_validator("phone")
    @classmethod
    def _phone_ok(cls, v: Optional[str]) -> Optional[str]:
        if v in (None, ""):
            return None
        v = v.strip()
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v


class ResetPasswordIn(BaseModel):
    """通过邮箱验证码重置密码。"""

    email: str = Field(min_length=5, max_length=120)
    code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=6, max_length=64)

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v


class ChangeEmailCodeIn(BaseModel):
    """更换绑定邮箱：向「新邮箱」发送验证码。"""

    email: str = Field(min_length=5, max_length=120)

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v


class ChangeEmailIn(BaseModel):
    """更换绑定邮箱：校验新邮箱收到的验证码后生效。"""

    email: str = Field(min_length=5, max_length=120)
    code: str = Field(min_length=4, max_length=8)

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("邮箱格式不正确")
        return v


class LoginIn(BaseModel):
    """登录凭证：username 字段同时支持「用户名」或「邮箱」。"""

    username: str = Field(min_length=3, max_length=120)
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=64)


class UpdateProfileIn(BaseModel):
    """个人资料：用户名是登录标识，允许修改但需保证全局唯一。"""

    username: Optional[str] = Field(default=None, max_length=50)
    real_name: Optional[str] = Field(default=None, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("username")
    @classmethod
    def _username_ok(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip()
        if not re.fullmatch(r"[A-Za-z0-9_]{3,50}", v):
            raise ValueError("用户名只能包含字母、数字和下划线，长度 3-50 位")
        return v


# ---------------- 车辆 ----------------
class VehicleIn(BaseModel):
    plate_no: str = Field(min_length=2, max_length=20)
    brand: Optional[str] = Field(default=None, max_length=50)
    model: Optional[str] = Field(default=None, max_length=50)
    mileage: Optional[int] = Field(default=None, ge=0, le=2_000_000)
    remark: Optional[str] = Field(default=None, max_length=200)


# ---------------- 门店 ----------------
class StoreCreateIn(BaseModel):
    """管理员新增门店并为其创建门店账号。"""
    name: str = Field(min_length=2, max_length=100)
    address: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = Field(default=None, max_length=500)
    open_time: Optional[str] = Field(default="09:00", max_length=10)
    close_time: Optional[str] = Field(default="18:00", max_length=10)
    status: int = Field(default=1, ge=0, le=2)
    # 门店工作人员账号
    username: Optional[str] = Field(default=None, max_length=50)
    password: Optional[str] = Field(default=None, max_length=64)


class StoreUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = Field(default=None, max_length=500)
    open_time: Optional[str] = Field(default=None, max_length=10)
    close_time: Optional[str] = Field(default=None, max_length=10)


class StoreReviewIn(BaseModel):
    status: int = Field(ge=0, le=2)


# ---------------- 养护项目 ----------------
class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    duration: int = Field(default=60, ge=10, le=1440)
    price: float = Field(default=0, ge=0, le=9_999_999)
    description: Optional[str] = Field(default=None, max_length=255)
    status: int = Field(default=1, ge=0, le=1)


# ---------------- 服务时段 ----------------
class SlotIn(BaseModel):
    slot_date: date
    start_time: time
    end_time: time
    capacity: int = Field(default=1, ge=1, le=999)


class SlotTimeRange(BaseModel):
    start_time: time
    end_time: time


class SlotGenerateIn(BaseModel):
    start_date: date
    end_date: date
    capacity: int = Field(default=2, ge=1, le=999)
    ranges: List[SlotTimeRange] = Field(default_factory=list)


# ---------------- 预约订单 ----------------
class ReservationCreateIn(BaseModel):
    vehicle_id: int
    store_id: int
    item_id: int
    slot_id: int
    contact_name: Optional[str] = Field(default=None, max_length=50)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    remark: Optional[str] = Field(default=None, max_length=255)


class OrderStatusIn(BaseModel):
    status: str
    reason: Optional[str] = Field(default=None, max_length=255)
    service_note: Optional[str] = Field(default=None, max_length=255)


# ---------------- 管理端 ----------------
class UserStatusIn(BaseModel):
    status: int = Field(ge=0, le=1)


class ItemStatusIn(BaseModel):
    status: int = Field(ge=0, le=1)


class StoreSelfRegisterIn(BaseModel):
    """门店自助入驻申请（生成待审核门店）。"""
    store_name: str = Field(min_length=2, max_length=100)
    address: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = Field(default=None, max_length=500)
