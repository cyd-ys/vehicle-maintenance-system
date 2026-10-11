"""FastAPI 应用入口：注册路由、跨域、统一异常响应、静态文件与建表。"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import files
from .config import settings
from .database import Base, engine
from .deps import TOKEN_HEADERS, TOKEN_QUERY_KEYS
from .routers import admin, auth, reservations, store_console, stores, vehicles
from .security import decode_access_token


def _locate_spa_dir() -> Path | None:
    """定位前端构建产物目录（发布包用 static/，本仓库用 frontend/dist）。"""
    base = Path(__file__).resolve().parent.parent  # backend/ 或发布包根目录
    if (base / "static" / "index.html").is_file():
        return base / "static"
    if (base.parent / "frontend" / "dist" / "index.html").is_file():
        return base.parent / "frontend" / "dist"
    return None


# 只有显式开启 SERVE_SPA 且确实存在构建产物时，才由后端提供前端页面
SPA_DIR = _locate_spa_dir() if settings.SERVE_SPA else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # 首次启动自动建表
    files.ensure_dirs()                    # 头像上传目录
    if settings.AUTO_SEED:
        # 空库时写入演示数据；线上没有演示账号就登录不了
        from .seed import run as seed_run
        seed_run()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="汽车养护预约服务系统后端接口（Vue 3 + FastAPI + MySQL）",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"code": exc.status_code, "message": exc.detail, "data": None})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = ".".join(str(x) for x in first.get("loc", []) if x not in ("body", "query"))
        message = f"参数校验失败：{loc} {first.get('msg', '')}"
    else:
        message = "参数校验失败"
    return JSONResponse(status_code=422, content={"code": 422, "message": message, "data": None})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"code": 500, "message": f"服务器内部错误：{exc}", "data": None})


@app.get("/", tags=["系统"], summary="健康检查 / 前端首页")
def root():
    """开启单端口部署时返回前端首页，否则返回 JSON 健康检查。"""
    if SPA_DIR is not None:
        return FileResponse(SPA_DIR / "index.html")
    return {"code": 0, "message": "success", "data": {"app": settings.APP_NAME, "version": settings.APP_VERSION}}


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    return {"code": 0, "message": "success", "data": {"app": settings.APP_NAME, "version": settings.APP_VERSION}}


@app.get("/api/diagnostic/headers", tags=["系统"], summary="请求头诊断（仅调试模式）")
def diagnostic_headers(request: Request):
    """回显请求头的「到场情况」，用于排查反向代理改写请求头导致的鉴权失败。

    只返回是否存在、长度、是否形如 JWT，以及服务端是否认得其中的令牌，
    **绝不回显任何请求头的原始值** —— 即便代理注入了凭据，也不会从这里泄露。
    仅在 DEBUG 模式下开放。
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="接口不存在")

    def probe(name: str) -> dict:
        raw = (request.headers.get(name) or "").strip()
        return {"present": bool(raw), "length": len(raw), "jwt_shaped": raw.startswith("eyJ")}

    def recognized(name: str) -> bool:
        raw = (request.headers.get(name) or "").strip()
        if not raw:
            return False
        payload = decode_access_token(raw)
        return bool(payload and payload.get("sub"))

    names = [n for n in ("Authorization", *TOKEN_HEADERS)]
    return {
        "code": 0,
        "message": "success",
        "data": {
            "received_header_names": sorted(request.headers.keys()),
            "carriers": {n: probe(n) for n in names},
            "token_recognized": {n: recognized(n) for n in names},
            "query_token_present": any(request.query_params.get(k) for k in TOKEN_QUERY_KEYS),
            "client": request.client.host if request.client else None,
        },
    }


# 用户上传的头像等静态资源（须在启动前确保目录存在）
files.ensure_dirs()
app.mount("/uploads", StaticFiles(directory=str(files.UPLOAD_ROOT)), name="uploads")

app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(stores.router)
app.include_router(reservations.router)
app.include_router(store_console.router)
app.include_router(admin.router)


# 单端口部署：前端静态资源 + SPA 路由回退。
# 必须放在最后注册 —— FastAPI 按注册顺序匹配，这样 /api、/docs、/uploads 都能先命中。
if SPA_DIR is not None:
    _SPA_ROOT = SPA_DIR.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # 未命中的 /api 或 /uploads 应返回 404，而不是把 HTML 吐给调用方
        if full_path.startswith(("api/", "uploads/")):
            return JSONResponse(status_code=404, content={"code": 404, "message": "接口不存在", "data": None})
        target = (_SPA_ROOT / full_path).resolve()
        if full_path and target.is_file() and _SPA_ROOT in target.parents:
            return FileResponse(target)
        # 其余路径交给 index.html，由 Vue Router 接管（刷新页面不会 404）
        return FileResponse(_SPA_ROOT / "index.html")
