"""FastAPI 应用入口：注册路由、跨域、统一异常响应、静态文件与建表。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import files
from .config import settings
from .database import Base, engine
from .routers import admin, auth, reservations, store_console, stores, vehicles


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)  # 首次启动自动建表
    files.ensure_dirs()                    # 头像上传目录
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


@app.get("/", tags=["系统"], summary="健康检查")
def root():
    return {"code": 0, "message": "success", "data": {"app": settings.APP_NAME, "version": settings.APP_VERSION}}


# 用户上传的头像等静态资源（须在启动前确保目录存在）
files.ensure_dirs()
app.mount("/uploads", StaticFiles(directory=str(files.UPLOAD_ROOT)), name="uploads")

app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(stores.router)
app.include_router(reservations.router)
app.include_router(store_console.router)
app.include_router(admin.router)
