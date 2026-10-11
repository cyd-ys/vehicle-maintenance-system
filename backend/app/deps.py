"""依赖注入：当前用户解析与角色权限校验。"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.SysUser:
    """从 Authorization: Bearer <token> 解析当前用户。"""
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或令牌缺失")

    payload = decode_access_token(credentials.credentials)
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
