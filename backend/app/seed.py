"""初始化演示数据（对应论文 5.1 测试数据：用户、门店、项目、时段、订单）。

用法：
    python -m app.seed           # 若数据库为空则写入演示数据
    python -m app.seed --reset   # 清空并重建所有表后写入演示数据
"""
import random
import sys
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from .database import Base, SessionLocal, engine
from . import models
from .security import hash_password
from .utils import gen_order_no

random.seed(20261010)

STORES = [
    {
        "name": "星光汽车养护中心",
        "address": "海口市龙华区滨海大道 128 号",
        "phone": "0898-6688-1001",
        "description": "专注中小型乘用车常规保养与快修，技师持证上岗。",
        "open_time": "09:00",
        "close_time": "18:00",
        "staff": ("store1", "store123"),
        "items": [
            ("机油机滤更换", "常规保养", 60, 380.00, "含全合成机油 4L 与机油滤芯更换"),
            ("四轮定位", "底盘服务", 60, 200.00, "进口四轮定位仪精准调校"),
            ("刹车片更换", "制动系统", 90, 480.00, "前轮刹车片更换并检测制动液"),
            ("空调清洗除菌", "空调系统", 45, 168.00, "蒸发箱清洗与臭氧除菌"),
        ],
    },
    {
        "name": "极速汽车养护服务站",
        "address": "海口市美兰区海甸三西路 66 号",
        "phone": "0898-6688-2002",
        "description": "连锁快保门店，提供小保养、深度养护与美容服务。",
        "open_time": "08:30",
        "close_time": "19:00",
        "staff": ("store2", "store123"),
        "items": [
            ("小保养套餐", "常规保养", 60, 298.00, "机油机滤更换 + 20 项安全检测"),
            ("发动机深度养护", "动力系统", 120, 680.00, "积碳清理与燃油系统养护"),
            ("轮胎动平衡", "轮胎服务", 40, 120.00, "四轮动平衡检测与配重"),
            ("全车打蜡美容", "外观美容", 90, 260.00, "清洗、去污、封体打蜡"),
        ],
    },
]

USERS = [
    ("user1", "user123", "雷优", "13800000001"),
    ("user2", "user123", "张伟", "13800000002"),
    ("user3", "user123", "李娜", "13800000003"),
]

VEHICLES = [
    ("琼A12345", "大众", "朗逸", 38000),
    ("琼A66688", "丰田", "卡罗拉", 52000),
    ("琼B88899", "本田", "雅阁", 21000),
    ("琼C23333", "比亚迪", "秦PLUS", 12000),
]

SLOT_RANGES = [
    (time(9, 0), time(10, 30)),
    (time(10, 30), time(12, 0)),
    (time(14, 0), time(15, 30)),
    (time(15, 30), time(17, 0)),
]

# 订单状态分布（论文 5.1：约 30 条订单）
STATUS_POOL = (
    [models.OrderStatus.COMPLETED] * 10
    + [models.OrderStatus.PENDING] * 7
    + [models.OrderStatus.CONFIRMED] * 6
    + [models.OrderStatus.IN_SERVICE] * 3
    + [models.OrderStatus.CANCELLED] * 2
    + [models.OrderStatus.REJECTED] * 2
)
OCCUPYING = (models.OrderStatus.PENDING, models.OrderStatus.CONFIRMED, models.OrderStatus.IN_SERVICE)


def run(reset: bool = False):
    if reset:
        Base.metadata.drop_all(bind=engine)
        print("[seed] 已清空数据表")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.execute(select(models.SysUser)).scalars().first():
            print("[seed] 已存在数据，跳过初始化（如需重建请使用 --reset）")
            return

        # 管理员
        admin = models.SysUser(
            username="admin", password_hash=hash_password("admin123"),
            real_name="系统管理员", phone="13800000000", email="admin@carcare.cn",
            role=models.Role.ADMIN, status=models.CommonStatus.ENABLED,
        )
        db.add(admin)
        db.flush()

        # 门店与门店账号、养护项目、服务时段
        store_objs = []
        for cfg in STORES:
            store = models.Store(
                name=cfg["name"], address=cfg["address"], phone=cfg["phone"],
                description=cfg["description"], open_time=cfg["open_time"],
                close_time=cfg["close_time"], status=models.StoreStatus.ACTIVE,
            )
            db.add(store)
            db.flush()

            staff_name, staff_pwd = cfg["staff"]
            db.add(models.SysUser(
                username=staff_name, password_hash=hash_password(staff_pwd),
                real_name=f"{cfg['name']}前台", phone=cfg["phone"], email=f"{staff_name}@carcare.cn",
                role=models.Role.STORE, status=models.CommonStatus.ENABLED, store_id=store.id,
            ))

            for (name, cat, dur, price, desc) in cfg["items"]:
                db.add(models.ServiceItem(
                    store_id=store.id, name=name, category=cat, duration=dur,
                    price=price, description=desc, status=models.CommonStatus.ENABLED,
                ))

            # 未来 7 天的服务时段
            today = date.today()
            for d in range(0, 7):
                slot_date = today + timedelta(days=d)
                for (st, et) in SLOT_RANGES:
                    db.add(models.ServiceSlot(
                        store_id=store.id, slot_date=slot_date, start_time=st,
                        end_time=et, capacity=2, booked=0,
                    ))
            store_objs.append(store)
        db.commit()

        # 用户与车辆
        user_objs = []
        for (uname, pwd, real, phone) in USERS:
            u = models.SysUser(
                username=uname, password_hash=hash_password(pwd), real_name=real,
                phone=phone, email=f"{uname}@carcare.cn",
                role=models.Role.USER, status=models.CommonStatus.ENABLED,
            )
            db.add(u)
            db.flush()
            user_objs.append(u)

        vehicle_map = {}
        for idx, (plate, brand, model_name, mileage) in enumerate(VEHICLES):
            owner = user_objs[idx % len(user_objs)]
            v = models.Vehicle(user_id=owner.id, plate_no=plate, brand=brand, model=model_name, mileage=mileage)
            db.add(v)
            db.flush()
            vehicle_map[v.id] = owner
        db.commit()

        # 预约订单
        all_slots = db.execute(select(models.ServiceSlot)).scalars().all()
        all_items = db.execute(select(models.ServiceItem)).scalars().all()
        items_by_store = {}
        for it in all_items:
            items_by_store.setdefault(it.store_id, []).append(it)
        slots_by_store = {}
        for s in all_slots:
            slots_by_store.setdefault(s.store_id, []).append(s)

        vehicles_by_user = {}
        for vid, owner in vehicle_map.items():
            vehicles_by_user.setdefault(owner.id, []).append(vid)

        statuses = STATUS_POOL[:]
        random.shuffle(statuses)
        created = 0
        for status in statuses:
            user = random.choice(user_objs)
            if not vehicles_by_user.get(user.id):
                continue
            store_id = random.choice(list(items_by_store.keys()))
            item = random.choice(items_by_store[store_id])
            slot = random.choice(slots_by_store[store_id])
            if slot.booked >= slot.capacity:
                continue

            now = datetime.now()
            res = models.Reservation(
                order_no=gen_order_no() + f"{created:02d}",
                user_id=user.id,
                vehicle_id=random.choice(vehicles_by_user[user.id]),
                store_id=store_id,
                item_id=item.id,
                slot_id=slot.id,
                item_name=item.name,
                item_price=item.price,
                duration=item.duration,
                total_price=item.price,
                slot_date=slot.slot_date,
                start_time=slot.start_time,
                end_time=slot.end_time,
                status=status,
                contact_name=user.real_name,
                contact_phone=user.phone,
                remark=random.choice(["请提前电话联系", "希望使用原厂配件", "", "到店前请检查胎压"]),
            )
            if status in OCCUPYING:
                slot.booked += 1
            if status in (models.OrderStatus.CONFIRMED, models.OrderStatus.IN_SERVICE, models.OrderStatus.COMPLETED):
                res.confirmed_at = now - timedelta(days=1)
            if status == models.OrderStatus.COMPLETED:
                res.completed_at = now
                res.service_note = "已完成服务并交付车辆"
            if status == models.OrderStatus.CANCELLED:
                res.cancelled_at = now
            if status == models.OrderStatus.REJECTED:
                res.reject_reason = "当日工位已排满，建议改约其他时段"
            db.add(res)
            created += 1

        db.commit()
        print(f"[seed] 初始化完成：管理员 admin/admin123，门店 store1|store2/store123，"
              f"用户 user1~user3/user123，生成订单 {created} 条")
    finally:
        db.close()


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)
