"""统一启动入口。

本地开发仍推荐 `start-backend.bat`（固定 8000 端口 + 热重载）；
**发布/容器环境**用本脚本，它会读取平台注入的 `PORT` 环境变量并绑定 `0.0.0.0`，
满足「单端口对外提供服务」的部署要求。

用法：
    python run.py              # 默认 0.0.0.0:8000
    PORT=3000 python run.py    # 由平台指定端口
"""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "").lower() in ("1", "true", "yes")
    print(f"[run] 正在启动：http://{host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
