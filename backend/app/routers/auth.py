"""认证接口：邮箱验证码注册、登录、当前用户、资料与密码维护。

邮箱注册流程（论文 4.2 用户注册的增强实现）：
  1. 前端调用 POST /api/auth/email/code 获取验证码（60s 冷却 + 每小时次数上限）；
  2. 后端生成 6 位验证码写入 email_code 表，并通过 SMTP 发送 HTML 邮件；
  3. 前端携带 email + code + password 调用 POST /api/auth/register；
  4. 后端校验验证码（存在 / 未过期 / 未使用 / 匹配）后创建账号，验证码置为已使用。
"""
import random
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .. import email_service, files, models, serializers
from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..response import ok
from ..schemas import (
    ChangeEmailCodeIn,
    ChangeEmailIn,
    ChangePasswordIn,
    EmailCodeIn,
    LoginIn,
    RegisterIn,
    ResetPasswordIn,
    UpdateProfileIn,
)
from ..security import create_access_token, hash_password, verify_password
from ..utils import write_log

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 同一邮箱在同一小时内最多可获取的验证码数量（防止恶意刷邮件）
MAX_CODES_PER_HOUR = 10


# ---------------------------------------------------------------- 内部工具
def _load_duplicate(db: Session, email: str) -> models.SysUser | None:
    return db.execute(select(models.SysUser).where(models.SysUser.email == email)).scalars().first()


def _find_user_by_identifier(db: Session, identifier: str) -> models.SysUser | None:
    """支持用「用户名」或「邮箱」登录。"""
    ident = (identifier or "").strip()
    if not ident:
        return None
    return db.execute(
        select(models.SysUser).where(
            or_(models.SysUser.username == ident, func.lower(models.SysUser.email) == ident.lower())
        )
    ).scalars().first()


def _gen_username(db: Session, email: str) -> str:
    """未填写用户名时，由邮箱前缀自动生成一个不冲突的用户名。"""
    base = re.sub(r"[^A-Za-z0-9_]", "", (email or "").split("@")[0])[:20]
    if len(base) < 3:
        base = f"user{base}" if base else "user"
    candidate, i = base, 1
    while db.execute(select(models.SysUser.id).where(models.SysUser.username == candidate)).first():
        i += 1
        candidate = f"{base}{i}"[:50]
    return candidate


def _issue_code(db: Session, email: str, purpose: str) -> str:
    """生成验证码并落库，返回验证码明文（未提交事务）。"""
    now = datetime.now()

    latest = db.execute(
        select(models.EmailCode)
        .where(models.EmailCode.email == email, models.EmailCode.purpose == purpose)
        .order_by(models.EmailCode.id.desc())
    ).scalars().first()
    if latest and latest.created_at:
        elapsed = (now - latest.created_at).total_seconds()
        if elapsed < settings.EMAIL_CODE_COOLDOWN_SECONDS:
            wait = int(settings.EMAIL_CODE_COOLDOWN_SECONDS - elapsed) + 1
            raise HTTPException(status_code=429, detail=f"验证码发送过于频繁，请 {wait} 秒后再试")

    sent_last_hour = db.execute(
        select(func.count())
        .select_from(models.EmailCode)
        .where(
            models.EmailCode.email == email,
            models.EmailCode.purpose == purpose,
            models.EmailCode.created_at >= now - timedelta(hours=1),
        )
    ).scalar_one()
    if sent_last_hour >= MAX_CODES_PER_HOUR:
        raise HTTPException(status_code=429, detail="该邮箱获取验证码次数过多，请稍后再试")

    code = f"{random.randint(0, 999999):06d}"
    db.add(
        models.EmailCode(
            email=email,
            code=code,
            purpose=purpose,
            expires_at=now + timedelta(minutes=settings.EMAIL_CODE_EXPIRE_MINUTES),
            used=0,
            created_at=now,
        )
    )
    return code


def _consume_code(db: Session, email: str, purpose: str, code: str) -> None:
    """校验并消费验证码（标记为已使用）。"""
    record = db.execute(
        select(models.EmailCode)
        .where(
            models.EmailCode.email == email,
            models.EmailCode.purpose == purpose,
            models.EmailCode.used == 0,
        )
        .order_by(models.EmailCode.id.desc())
    ).scalars().first()
    if not record:
        raise HTTPException(status_code=400, detail="请先获取邮箱验证码")
    if record.expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if record.code != (code or "").strip():
        raise HTTPException(status_code=400, detail="验证码不正确，请核对后重新输入")
    record.used = 1


# 不同场景的邮件标题
_CODE_SUBJECT = {
    "register": "【汽车养护预约服务系统】注册验证码",
    "reset": "【汽车养护预约服务系统】密码重置验证码",
    "change_email": "【汽车养护预约服务系统】更换邮箱验证码",
}


def _deliver_code(email: str, code: str, purpose: str) -> tuple[bool, str | None]:
    """投递验证码邮件。

    返回 (delivered, debug_code)：
      - 已配置 SMTP：真实发送，返回 (True, None)
      - 未配置 SMTP 且处于 DEBUG 兜底模式：返回 (False, code)
      - 其余情况抛出 HTTPException
    """
    if email_service.is_smtp_configured():
        try:
            email_service.send_email(
                email,
                _CODE_SUBJECT.get(purpose, "【汽车养护预约服务系统】邮箱验证码"),
                email_service.verification_email_html(code, settings.EMAIL_CODE_EXPIRE_MINUTES),
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"验证码邮件发送失败：{exc}") from exc
        return True, None

    if settings.DEBUG and settings.ALLOW_EMAIL_CODE_ECHO and purpose in settings.ECHO_CODE_PURPOSES:
        print(f"[email] SMTP 未配置，验证码 {code} -> {email}")
        return False, code

    raise HTTPException(status_code=503, detail="邮件服务未配置，请联系系统管理员")


# ---------------------------------------------------------------- 接口
@router.post("/email/code", summary="发送邮箱验证码")
def send_email_code(payload: EmailCodeIn, db: Session = Depends(get_db)):
    email = payload.email
    exists = _load_duplicate(db, email)

    if payload.purpose == "register" and exists:
        raise HTTPException(status_code=400, detail="该邮箱已被注册，请直接登录或更换邮箱")
    if payload.purpose == "reset" and not exists:
        raise HTTPException(status_code=400, detail="该邮箱尚未注册，请先完成注册")

    code = _issue_code(db, email, payload.purpose)
    db.commit()  # 先落库，保证冷却时间生效

    delivered, debug_code = _deliver_code(email, code, payload.purpose)

    data = {
        "email": email,
        "expire_minutes": settings.EMAIL_CODE_EXPIRE_MINUTES,
        "cooldown_seconds": settings.EMAIL_CODE_COOLDOWN_SECONDS,
        "delivered": delivered,
    }
    if debug_code:
        data["debug_code"] = debug_code
        return ok(data, "SMTP 未配置，已启用本地调试模式（验证码见下方提示）")
    return ok(data, "验证码已发送至邮箱，请查收")


@router.post("/register", summary="邮箱验证码注册")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email
    if _load_duplicate(db, email):
        raise HTTPException(status_code=400, detail="该邮箱已被注册，请直接登录")

    username = payload.username or _gen_username(db, email)
    if db.execute(select(models.SysUser.id).where(models.SysUser.username == username)).first():
        raise HTTPException(status_code=400, detail="用户名已被占用，请更换后重试")
    if payload.phone and db.execute(
        select(models.SysUser.id).where(models.SysUser.phone == payload.phone)
    ).first():
        raise HTTPException(status_code=400, detail="手机号已被注册")

    _consume_code(db, email, "register", payload.code)

    user = models.SysUser(
        username=username,
        email=email,
        password_hash=hash_password(payload.password),
        real_name=payload.real_name,
        phone=payload.phone,
        role=models.Role.USER,
        status=models.CommonStatus.ENABLED,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    write_log(
        db,
        operator_id=user.id,
        operator_name=user.username,
        role=user.role,
        action="注册",
        target_type="user",
        target_id=user.id,
        detail=f"邮箱注册：{email}",
    )
    db.commit()
    return ok(serializers.user_dict(user), "注册成功")


@router.post("/login", summary="用户登录并获取 JWT 令牌（用户名或邮箱）")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    identifier = (payload.username or "").strip()
    user = _find_user_by_identifier(db, identifier)
    if not user or not verify_password(payload.password, user.password_hash):
        # 统一提示，避免账号枚举
        raise HTTPException(status_code=400, detail="账号或密码错误")
    if user.status != models.CommonStatus.ENABLED:
        raise HTTPException(status_code=403, detail="账号已被停用，请联系管理员")

    token = create_access_token(user.id, user.role, user.username)
    write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
              action="登录", target_type="user", target_id=user.id, detail="用户登录")
    db.commit()
    return ok({"access_token": token, "token_type": "bearer", "user": serializers.user_dict(user)}, "登录成功")


@router.post("/password/reset", summary="通过邮箱验证码重置密码")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(get_db)):
    user = _load_duplicate(db, payload.email)
    if not user:
        raise HTTPException(status_code=400, detail="该邮箱尚未注册")

    _consume_code(db, payload.email, "reset", payload.code)

    user.password_hash = hash_password(payload.new_password)
    write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
              action="重置密码", target_type="user", target_id=user.id, detail=f"邮箱验证码重置：{payload.email}")
    db.commit()
    return ok(message="密码已重置，请使用新密码登录")


@router.post("/me/email/code", summary="更换邮箱：向新邮箱发送验证码")
def send_change_email_code(payload: ChangeEmailCodeIn, user: models.SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    email = payload.email
    if email == (user.email or "").lower():
        raise HTTPException(status_code=400, detail="新邮箱与当前绑定邮箱相同，无需更换")
    if _load_duplicate(db, email):
        raise HTTPException(status_code=400, detail="该邮箱已被其他账号注册，请更换")

    code = _issue_code(db, email, "change_email")
    db.commit()

    delivered, debug_code = _deliver_code(email, code, "change_email")
    data = {
        "email": email,
        "expire_minutes": settings.EMAIL_CODE_EXPIRE_MINUTES,
        "cooldown_seconds": settings.EMAIL_CODE_COOLDOWN_SECONDS,
        "delivered": delivered,
    }
    if debug_code:
        data["debug_code"] = debug_code
        return ok(data, "SMTP 未配置，已启用本地调试模式（验证码见下方提示）")
    return ok(data, "验证码已发送至新邮箱，请查收")


@router.put("/me/email", summary="更换绑定邮箱（需新邮箱验证码）")
def change_email(payload: ChangeEmailIn, user: models.SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    email = payload.email
    if email == (user.email or "").lower():
        raise HTTPException(status_code=400, detail="新邮箱与当前绑定邮箱相同，无需更换")
    if _load_duplicate(db, email):
        raise HTTPException(status_code=400, detail="该邮箱已被其他账号注册，请更换")

    _consume_code(db, email, "change_email", payload.code)

    old_email = user.email
    user.email = email
    write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
              action="更换邮箱", target_type="user", target_id=user.id, detail=f"{old_email} -> {email}")
    db.commit()
    db.refresh(user)
    return ok(serializers.user_dict(user), "邮箱更换成功")


@router.post("/me/avatar", summary="上传/更换头像")
async def upload_avatar(
    file: UploadFile = File(...),
    user: models.SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_url = await files.save_avatar(file, user.id)
    old_url = user.avatar
    user.avatar = new_url
    write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
              action="更换头像", target_type="user", target_id=user.id)
    db.commit()
    db.refresh(user)
    files.remove_avatar_file(old_url)  # 提交成功后再清理旧文件
    return ok(serializers.user_dict(user), "头像已更新")


@router.delete("/me/avatar", summary="恢复默认头像")
def reset_avatar(user: models.SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    old_url = user.avatar
    if not old_url:
        return ok(serializers.user_dict(user), "当前已是默认头像")
    user.avatar = None
    write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
              action="恢复默认头像", target_type="user", target_id=user.id)
    db.commit()
    db.refresh(user)
    files.remove_avatar_file(old_url)
    return ok(serializers.user_dict(user), "已恢复默认头像")


@router.get("/me", summary="获取当前登录用户信息")
def me(user: models.SysUser = Depends(get_current_user)):
    return ok(serializers.user_dict(user))


@router.put("/me", summary="修改个人资料（用户名 / 真实姓名 / 手机号）")
def update_me(payload: UpdateProfileIn, user: models.SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.username and payload.username != user.username:
        dup = db.execute(select(models.SysUser).where(models.SysUser.username == payload.username)).scalars().first()
        if dup:
            raise HTTPException(status_code=400, detail="用户名已被占用，请更换")
        old_username = user.username
        user.username = payload.username
        write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
                  action="修改用户名", target_type="user", target_id=user.id,
                  detail=f"{old_username} -> {payload.username}")
    if payload.phone and payload.phone != user.phone:
        dup = db.execute(select(models.SysUser).where(models.SysUser.phone == payload.phone)).scalars().first()
        if dup:
            raise HTTPException(status_code=400, detail="手机号已被占用")
        user.phone = payload.phone
    if payload.real_name is not None:
        user.real_name = payload.real_name
    db.commit()
    db.refresh(user)
    return ok(serializers.user_dict(user), "资料已更新")


@router.put("/me/password", summary="修改密码")
def change_password(payload: ChangePasswordIn, user: models.SysUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    user.password_hash = hash_password(payload.new_password)
    write_log(db, operator_id=user.id, operator_name=user.username, role=user.role,
              action="修改密码", target_type="user", target_id=user.id)
    db.commit()
    return ok(message="密码修改成功")
