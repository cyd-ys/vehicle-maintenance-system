"""头像文件存储：落盘、格式校验与旧文件清理。

不依赖 Pillow：通过**文件头魔数**判断真实图片类型，避免把改名的非图片文件存进来。
"""
import os
from pathlib import Path

from fastapi import HTTPException, UploadFile

# backend/uploads/avatars
BACKEND_DIR = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = BACKEND_DIR / "uploads"
AVATAR_DIR = UPLOAD_ROOT / "avatars"
AVATAR_URL_PREFIX = "/uploads/avatars"

MAX_BYTES = 2 * 1024 * 1024  # 2MB

# 魔数 -> 扩展名（只允许常见位图格式，不含 svg，避免 XSS）
_MAGIC = (
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"GIF87a", ".gif"),
    (b"GIF89a", ".gif"),
)


def _sniff_ext(data: bytes) -> str | None:
    for magic, ext in _MAGIC:
        if data.startswith(magic):
            return ext
    # WebP: RIFF....WEBP
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def ensure_dirs() -> None:
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)


async def save_avatar(file: UploadFile, user_id: int) -> str:
    """保存头像并返回可访问的相对路径。"""
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="上传的文件为空")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="头像文件不能超过 2MB")

    ext = _sniff_ext(data)
    if not ext:
        raise HTTPException(status_code=400, detail="仅支持 JPG / PNG / WebP / GIF 格式的图片")

    ensure_dirs()
    name = f"u{user_id}_{os.urandom(6).hex()}{ext}"
    (AVATAR_DIR / name).write_bytes(data)
    return f"{AVATAR_URL_PREFIX}/{name}"


def remove_avatar_file(url: str | None) -> None:
    """删除旧头像文件（仅限本服务 uploads/avatars 目录内的文件）。"""
    if not url or not url.startswith(AVATAR_URL_PREFIX + "/"):
        return
    name = url.rsplit("/", 1)[-1]
    target = AVATAR_DIR / name
    try:
        if target.is_file() and target.parent.resolve() == AVATAR_DIR.resolve():
            target.unlink()
    except OSError:
        pass  # 删除失败不影响主流程
