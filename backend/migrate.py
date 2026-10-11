"""增量迁移：为既有数据库补充后续新增的表结构。

当前覆盖：
  1. sys_user.email 列（唯一索引）—— 邮箱注册 / 邮箱登录 / 找回密码
  2. sys_user.avatar 列 —— 头像上传
  3. email_code 表 —— 邮箱验证码存储
  4. 为演示账号回填邮箱

用法（在 backend 目录下）：
    .venv\\Scripts\\python.exe migrate.py

脚本**可重复执行**：已存在的结构会自动跳过。
（`Base.metadata.create_all` 只会新建缺失的表，不会给旧表加列，所以加列必须显式 ALTER。）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import inspect, text  # noqa: E402

from app import models  # noqa: E402,F401
from app.database import DATABASE_URL, IS_SQLITE, Base, engine  # noqa: E402

# 需要保证存在的列：表名 -> [(列名, DDL 片段, 唯一索引名或 None)]
REQUIRED_COLUMNS = {
    "sys_user": [
        ("email", "VARCHAR(120) NULL", "ix_sys_user_email"),
        ("avatar", "VARCHAR(255) NULL", None),
    ],
}

DEMO_ACCOUNTS = ["admin", "store1", "store2", "user1", "user2", "user3"]


def main() -> None:
    print(f"[migrate] 目标数据库：{DATABASE_URL}")
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    for table, columns in REQUIRED_COLUMNS.items():
        if table not in tables:
            print(f"[migrate] 未找到 {table} 表（首次初始化将由 create_all 建表）")
            continue
        existing = {c["name"] for c in inspector.get_columns(table)}
        for name, ddl, index_name in columns:
            if name in existing:
                print(f"[migrate] {table}.{name} 已存在，跳过")
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                if index_name and not IS_SQLITE:
                    conn.execute(text(f"CREATE UNIQUE INDEX {index_name} ON {table} ({name})"))
            print(f"[migrate] 已为 {table} 添加 {name} 列")

    # 创建缺失的表（email_code 等）
    Base.metadata.create_all(engine)
    missing = [t for t in ("email_code",) if t not in set(inspect(engine).get_table_names())]
    print(f"[migrate] email_code 表{'就绪' if not missing else '建表失败：' + str(missing)}")

    # 为演示账号回填邮箱（仅当 email 为空时）
    with engine.begin() as conn:
        for name in DEMO_ACCOUNTS:
            conn.execute(
                text(
                    "UPDATE sys_user SET email = :email "
                    "WHERE username = :name AND (email IS NULL OR email = '')"
                ),
                {"email": f"{name}@carcare.cn", "name": name},
            )
    print("[migrate] 演示账号邮箱回填完成")

    print("[migrate] 完成")


if __name__ == "__main__":
    main()
