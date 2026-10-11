"""应用配置：读取 .env，集中管理数据库、JWT 与跨域等参数。"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "汽车养护预约服务系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库连接（论文 4.1：MySQL 8.0）
    DATABASE_URL: str = "mysql+pymysql://root:root@127.0.0.1:3306/vehicle_maintenance?charset=utf8mb4"
    # 当 MySQL 不可用时是否自动降级为本地 SQLite（便于无 MySQL 环境快速体验）
    ALLOW_SQLITE_FALLBACK: bool = True
    SQLITE_PATH: str = "vehicle_maintenance.db"

    # JWT 安全参数（论文 3.5）
    JWT_SECRET_KEY: str = "change-me-in-production-please-use-a-long-random-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    # 邮件发送（SMTP）——用于邮箱注册验证码
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""            # 发件地址，留空则使用 SMTP_USER
    SMTP_FROM_NAME: str = "汽车养护预约服务系统"
    SMTP_USE_SSL: bool = True      # 465 端口用 SSL；587 端口请置为 False（走 STARTTLS）
    EMAIL_CODE_EXPIRE_MINUTES: int = 5
    EMAIL_CODE_COOLDOWN_SECONDS: int = 60
    # 未配置 SMTP 且在 DEBUG 模式下，是否允许在接口响应中回显验证码（仅便于本地调试，生产务必关闭）
    ALLOW_EMAIL_CODE_ECHO: bool = True

    # 跨域
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
