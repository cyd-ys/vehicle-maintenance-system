"""依赖注入：当前用户解析与角色权限校验。"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .security import decode_access_token

# 保留 Bearer 声明有两个作用：让 /docs 上出现 Authorize 按钮，
# 以及保证「Authorization: Bearer xxx」这种标准调用方式继续可用。
bearer_scheme = HTTPBearer(auto_error=False)

# 自定义令牌请求头（按优先级）。为什么需要它们见下面 _extract_token 的说明。
TOKEN_HEADERS = ("X-Auth-Token", "X-Token")
# 允许用查询参数传令牌的兜底键名
TOKEN_QUERY_KEYS = ("access_token", "token")


def _token_candidates(
    request: Request, credentials: HTTPAuthorizationCredentials | None
) -> list[str]:
    """按优先级收集所有候选令牌（去重后返回）。

    为什么不只用标准的 Authorization 头：
        部分反向代理（例如发布平台的网关）会在转发时补写 Authorization 请求头，
        客户端真正携带的令牌会被盖掉，表现为「登录成功但所有鉴权接口都 401」。
        因此这里优先读取代理通常不会触碰的自定义头，把 Authorization 降级为
        兼容本地开发与 Swagger 调试的兜底通道，最后再留一个查询参数通道，
        用于极少数会连自定义头一起过滤掉的网关。
    """
    values: list[str | None] = [request.headers.get(n) for n in TOKEN_HEADERS]
    if credentials is not None:
        values.append(credentials.credentials)
    values.extend(request.query_params.get(k) for k in TOKEN_QUERY_KEYS)

    candidates: list[str] = []
    for raw in values:
        token = (raw or "").strip()
        if token and token not in candidates:
            candidates.append(token)
    return candidates


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.SysUser:
    """解析当前用户：依次尝试自定义头 / Authorization / 查询参数。

    注意是「取第一个**能解开**的令牌」，而不是「第一个非空的」——
    因为被代理塞进来的那个 Authorization 往往解不开，如果按「第一个非空」
    处理，它会把后面所有可用通道全部挡住。
    """
    candidates = _token_candidates(request, credentials)
    if not candidates:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或令牌缺失")

    payload = None
    for token in candidates:
        payload = decode_access_token(token)
        if payload:
            break
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌无效或已过期")

    user = db.get(models.SysUser, int(payload.get("sub", 0)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if user.status != models.CommonStatus.ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被停用")
    return user


def require_role(*roles: str):
    """角色白名单依赖：要求当前用户属于指定角色之一。"""

    def _checker(user: models.SysUser = Depends(get_current_user)) -> models.SysUser:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限执行该操作")
        return user

    return _checker


require_user = require_role(models.Role.USER)
require_store = require_role(models.Role.STORE)
require_admin = require_role(models.Role.ADMIN)
require_store_or_admin = require_role(models.Role.STORE, models.Role.ADMIN)
