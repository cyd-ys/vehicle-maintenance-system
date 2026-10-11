# -*- coding: utf-8 -*-
"""生成「单端口部署包」到 deploy/ 目录。

为什么需要这一步：
  本仓库是前后端分离的两个进程（后端 8000 + 前端 5173），而发布环境只提供
  **一个 HTTP 端口、且不提供 MySQL**。本脚本把项目组装成一个自包含的单端口应用：

      deploy/
        app/              后端源码（backend/app）
        run.py            启动入口（读取 PORT，绑定 0.0.0.0）
        static/           前端构建产物（frontend/dist）
        requirements.txt  依赖清单（不含 MySQL 驱动）
        .env              使用 SQLite + 自动写入演示数据

  开发时仍然用 start-all.bat 跑原来的两个进程，本项目源码不受影响。

用法：
    python build-deploy.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
DEPLOY = ROOT / "deploy"

# 去掉 PyMySQL：发布环境用 SQLite，不需要 MySQL 驱动，
# 同时也能通过发布平台「不依赖外部数据库」的前置检查。
REQUIREMENTS = """\
fastapi>=0.115.0
uvicorn>=0.30.0
SQLAlchemy>=2.0.30
PyJWT>=2.8.0
pydantic>=2.7.0
pydantic-settings>=2.3.0
python-dotenv>=1.0.1
python-multipart>=0.0.9
"""


def log(msg: str) -> None:
    print(f"[build-deploy] {msg}")


def ignore_junk(_dir, names):
    return [n for n in names if n == "__pycache__" or n.endswith(".pyc")]


def build_frontend() -> Path:
    log("构建前端：npm run build ...")
    r = subprocess.run(
        ["cmd", "/c", "npm", "run", "build"],
        cwd=str(FRONTEND),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        print(r.stdout or "")
        print(r.stderr or "")
        sys.exit("[build-deploy] 前端构建失败，已中止")
    dist = FRONTEND / "dist"
    if not (dist / "index.html").is_file():
        sys.exit("[build-deploy] 构建产物缺少 index.html，已中止")
    return dist


def write_env(target: Path) -> str:
    """生成发布用 .env，返回 JWT 密钥（打印用）。"""
    # 每次生成都换新密钥：旧的登录令牌自动失效，避免沿用一个弱默认值
    secret = subprocess.run(
        [sys.executable, "-c", "import secrets;print(secrets.token_urlsafe(48))"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()

    target.write_text(
        f"""# 发布环境配置 —— 由 build-deploy.py 自动生成，请勿手工修改
#
# 发布沙箱只提供一个 HTTP 端口、不提供 MySQL，因此这里使用项目内置的 SQLite 方案。
# DATABASE_URL 只要不是 mysql 开头就会走 SQLite 分支，
# 实际文件由 SQLITE_PATH 决定（相对本目录），两者保持一致即可。

DEBUG=true
DATABASE_URL=sqlite
SQLITE_PATH=demo.db
ALLOW_SQLITE_FALLBACK=true

# 单端口部署：后端直接在 / 上提供 static/ 里的前端页面
SERVE_SPA=true
# 空库时自动写入演示数据（否则线上没有演示账号，无法登录）
AUTO_SEED=true

# JWT 密钥（每次重新生成发布包都会换新，已登录用户需重新登录）
JWT_SECRET_KEY={secret}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=720

APP_NAME=汽车养护预约服务系统
APP_VERSION=1.0.0

# ---------- 邮件 ----------
# 发布沙箱连不上外部 SMTP，验证码改用「本地调试模式」：
# 接口响应里回显验证码，前端自动填入，注册流程依然可以完整演示。
SMTP_HOST=
SMTP_PORT=465
SMTP_USE_SSL=true
ALLOW_EMAIL_CODE_ECHO=true
# 关键：只允许 register 回显。若把 reset 也放开，任何人都能申请重置验证码、
# 从响应里读到它，进而改掉 admin 的密码，把演示账号锁死。
ECHO_CODE_PURPOSES=["register"]
EMAIL_CODE_EXPIRE_MINUTES=5
EMAIL_CODE_COOLDOWN_SECONDS=60
""",
        encoding="utf-8",
    )
    return secret


def main() -> None:
    # 1) 清空并重建 deploy/
    if DEPLOY.exists():
        shutil.rmtree(DEPLOY)
    DEPLOY.mkdir(parents=True)
    log(f"已重建目录 {DEPLOY}")

    # 2) 后端源码 + 启动入口
    shutil.copytree(BACKEND / "app", DEPLOY / "app", ignore=ignore_junk)
    shutil.copy2(BACKEND / "run.py", DEPLOY / "run.py")
    log("已复制后端源码与 run.py")

    # 3) 前端构建产物 -> deploy/static
    dist = build_frontend()
    shutil.copytree(dist, DEPLOY / "static")
    files = sum(1 for p in (DEPLOY / "static").rglob("*") if p.is_file())
    log(f"已复制前端构建产物（{files} 个文件）")

    # 4) 依赖清单与配置
    (DEPLOY / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    write_env(DEPLOY / ".env")
    log("已写入 requirements.txt 与 .env")

    total = sum(1 for p in DEPLOY.rglob("*") if p.is_file())
    log(f"完成：{DEPLOY}")
    log(f"共 {total} 个文件。启动方式：cd deploy && python run.py")


if __name__ == "__main__":
    main()
