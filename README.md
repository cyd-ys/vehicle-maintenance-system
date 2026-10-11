# 汽车养护预约服务系统

> 毕业设计《汽车养护预约服务系统设计与开发》配套实现
> 学院：信息技术学院 ｜ 专业：软件技术 ｜ 作者：雷优 ｜ 学号：2423730122

面向中小型汽车养护门店的在线预约平台，采用**前后端分离的 B/S 架构**，覆盖普通用户、门店工作人员、系统管理员三类角色的完整业务闭环：
**浏览项目 → 选择门店 → 提交预约 → 门店受理 → 状态查询**。

> **在线演示**：<https://vehicle-maintenance-60338.app.workbuddy.host/>
> （单端口部署，演示账号见 §五；本地运行方式见 §四）

## 一、技术栈

| 层次 | 技术选型 | 说明 |
| --- | --- | --- |
| 表现层 | Vue 3 + Vite + Vue Router + Pinia + Element Plus + Axios | 页面渲染、表单校验、路由守卫 |
| 业务层 | Python 3 + FastAPI + Pydantic + PyJWT | REST 接口、参数校验、权限控制、预约规则 |
| 数据层 | SQLAlchemy 2.0 + MySQL 8.0 | ORM 映射、事务控制、索引与完整性约束 |

## 二、目录结构

```
汽车养护预约系统/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 应用入口（路由注册 / 跨域 / 统一异常）
│   │   ├── config.py            # 配置（读取 .env）
│   │   ├── database.py          # 数据库连接与会话（MySQL，可降级 SQLite）
│   │   ├── models.py            # ORM 模型 + 订单状态机定义
│   │   ├── schemas.py           # 请求参数校验模型
│   │   ├── serializers.py       # ORM -> dict 序列化
│   │   ├── security.py          # 密码加盐哈希 + JWT 签发校验
│   │   ├── deps.py              # 当前用户解析 + 角色权限依赖
│   │   ├── utils.py             # 订单号 / 操作日志 / 分页
│   │   ├── email_service.py     # SMTP 发信（验证码邮件）
│   │   ├── files.py             # 头像文件落盘 / 魔数校验 / 旧文件清理
│   │   ├── seed.py              # 演示数据初始化
│   │   └── routers/             # 认证 / 车辆 / 门店 / 预约 / 门店端 / 管理端
│   ├── migrate.py               # 增量迁移（旧库补 email / avatar 列、email_code 表）
│   ├── uploads/avatars/         # 用户上传的头像（不进版本库）
│   ├── requirements.txt
│   ├── .env.example             # 配置模板
│   ├── init-db.bat              # 初始化数据库 + 演示数据
│   ├── run.py                   # 单端口部署入口（读 PORT，绑定 0.0.0.0）
│   └── start-backend.bat        # 启动后端
├── build-deploy.py              # 打包 deploy/ 单端口部署包（发布用，见 §4.4）
├── deploy/                      # ↑ 生成的部署包（不进版本库）
└── frontend/                    # Vue 3 前端
    ├── src/
    │   ├── api/                 # axios 封装 + 接口清单
    │   ├── store/               # Pinia 登录态
    │   ├── router/              # 路由与角色守卫
    │   ├── layouts/             # 用户端 / 门店端 / 管理端布局
    │   ├── components/          # 通用组件（状态标签 / 主题开关 / 头像 / 头像裁剪 / 账号面板）
    │   ├── utils/crop.js        # 头像裁剪几何纯函数（可单测）
    │   └── views/               # 页面（user / store / admin）
    ├── vite.config.js           # 开发代理 /api、/uploads -> 127.0.0.1:8000
    └── start-frontend.bat       # 启动前端
```

## 三、运行环境

- Node.js ≥ 18（推荐 20+）
- Python ≥ 3.10（推荐 3.11+）
- MySQL 8.0（若未安装，后端会自动降级为本地 SQLite，便于快速体验）

## 四、快速启动

> **最快的方式**：双击项目根目录的 `start-all.bat`，
> 它会自动打开两个窗口分别启动后端（8000）和前端（5173），无需手动敲命令。

### 1. 准备数据库配置

复制 `backend/.env.example` 为 `backend/.env`，按本机 MySQL 修改连接串：

```ini
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/vehicle_maintenance?charset=utf8mb4
```

> 首次启动若目标库不存在，请先创建：`CREATE DATABASE vehicle_maintenance DEFAULT CHARACTER SET utf8mb4;`
> （`init-db.bat` 与 `app/seed.py` 会在库存在的前提下自动建表并写入演示数据）

> **已有旧库升级**：若数据库是邮箱功能之前创建的，执行一次
> `cd backend && .venv\Scripts\python.exe migrate.py`
> 即可补上 `sys_user.email` 列与 `email_code` 表，并为演示账号回填邮箱（脚本可重复执行）。

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m app.seed --reset          # 建表 + 演示数据
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

或直接双击 `backend/init-db.bat` 与 `backend/start-backend.bat`。

- 服务地址：<http://127.0.0.1:8000>
- 交互式接口文档（Swagger）：<http://127.0.0.1:8000/docs>

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

或直接双击 `frontend/start-frontend.bat`。访问 <http://localhost:5173>。

### 4. 部署到线上（单端口打包）

本仓库开发时是**两个进程**（后端 8000 + 前端 Vite 5173），而发布环境只提供一个 HTTP 端口、
且**不提供 MySQL**。`build-deploy.py` 会把它组装成一个自包含的单端口应用：

```bash
python build-deploy.py     # 生成 deploy/
cd deploy && python run.py # 本地先自测，再发布
```

```
deploy/
├── app/              后端源码（backend/app 的副本）
├── run.py            启动入口（读 PORT 环境变量，绑定 0.0.0.0）
├── static/           前端构建产物（frontend/dist）
├── requirements.txt  依赖清单（不含 PyMySQL —— 线上用 SQLite）
└── .env              SQLite + SERVE_SPA=true + AUTO_SEED=true + 随机 JWT 密钥
```

三个开关都在 `backend/app/config.py`，**默认关闭**，所以本地开发行为完全不变：

| 配置 | 作用 |
| --- | --- |
| `SERVE_SPA=true` | 后端直接在 `/` 上提供 `static/` 里的前端页面（含 SPA 深链接回退），于是「一个端口 = 整个应用」，也没有跨域问题 |
| `AUTO_SEED=true` | 空库时自动写入演示数据，否则线上没有账号可登录 |
| `ALLOW_SQLITE_FALLBACK` | MySQL 连不上时自动降级为本地 SQLite（本地无 MySQL 也能跑） |

> **SQLite 兼容踩坑**：原先所有主键都是 `BigInteger`，而 SQLite 只对
> `INTEGER PRIMARY KEY` 自增，`BIGINT PRIMARY KEY` 会导致插入报
> `NOT NULL constraint failed: sys_user.id`。现改为
> `BigInteger().with_variant(Integer, "sqlite")`，MySQL 仍是 `BIGINT`、SQLite 是 `INTEGER`。

### 5. 线上环境的令牌传递（重要）

线上站点的访问要经过发布平台的网关。该网关会在转发时**补写 `Authorization` 请求头**
（实测：客户端一个头都不发，服务端仍收到一个 386 字节的 `authorization`），
客户端真正携带的令牌会被盖掉 —— 表现为**登录成功、但随后所有鉴权接口都返回 401**。

因此本项目**不依赖单一请求头**，`backend/app/deps.py` 按优先级依次尝试：

```
X-Auth-Token  →  Authorization  →  ?access_token= 查询参数
   （主用）         （兼容本地/Swagger）      （兜底）
```

并且取的是**第一个「能解开」的令牌**而不是「第一个非空的」——否则网关塞进来的那个
解不开的令牌会把后面所有可用通道全部挡住。前端 `src/api/request.js` 同时挂
`X-Auth-Token` 与 `Authorization`，并在收到 401 时自动换载体重试一次。

相关约定：

- 本地开发、Swagger 调试直接用标准的 `Authorization: Bearer <token>`，**无需改动**；
- 自定义令牌头固定为 `X-Auth-Token`（备选 `X-Token`），改动请同步 `deps.py` 与 `request.js`；
- `GET /api/diagnostic/headers`（**仅 `DEBUG=true` 时开放**）会回显服务端实际收到的
  请求头名称与各载体的「指纹」（是否存在 / 长度 / 是否形如 JWT），用于排查代理改写问题；
  **它绝不回显任何请求头的原始值**。

## 五、演示账号


| 角色 | 用户名 | 密码 | 演示邮箱 | 可访问入口 |
| --- | --- | --- | --- | --- |
| 系统管理员 | `admin` | `admin123` | `admin@carcare.cn` | `/admin` 平台管理后台 |
| 门店工作人员 | `store1` / `store2` | `store123` | `store1@carcare.cn` | `/store` 门店管理后台 |
| 普通用户 | `user1` / `user2` / `user3` | `user123` | `user1@carcare.cn` | `/user` 用户端 |

登录框同时支持**用户名**或**注册邮箱**登录（如 `user1` 与 `user1@carcare.cn` 等价）。
演示数据包含：2 家门店、8 个养护项目、未来 7 天服务时段，以及约 30 条覆盖各状态的预约订单。

## 六、核心机制说明

### 1. 预约时段容量校验与事务控制（论文 4.4）

`POST /api/reservations` 在数据库事务中先对目标服务时段加行锁（`SELECT ... FOR UPDATE`），
再统计该时段有效订单数并与容量比较，容量不足直接返回 409；订单写入与容量扣减在同一事务内完成，
任一步失败整体回滚，避免并发导致超额预约。

### 2. 订单有限状态机（论文 4.5）

```
待受理 pending ──▶ 已确认 confirmed ──▶ 服务中 in_service ──▶ 已完成 completed
      │                   │
      ├──▶ 已拒绝 rejected │
      └──▶ 已取消 cancelled ◀──┘
```

- 仅允许上述合法流转，非法跳转返回 400；
- 门店拒绝必须填写原因；
- 用户取消 / 门店拒绝时同步恢复对应时段剩余容量。

### 3. 权限与安全（论文 3.5）

- 密码使用 PBKDF2-HMAC-SHA256（12 万次迭代）加盐哈希存储，不存明文；
- 登录签发带有效期的 JWT，前端优先以请求头 `X-Auth-Token` 携带（同时附带标准的
  `Authorization: Bearer <token>` 以兼容本地开发与 Swagger；两种载体都可单独使用，
  原因见 §4.5）；
- 后端依赖注入执行角色校验（用户 / 门店 / 管理员），订单查询按本人或所属门店限定数据范围；
- 门店受理、拒绝、完成及管理员关键操作写入 `operation_log` 操作日志。

### 4. 邮箱验证码注册（真实邮件）

注册不再只依赖用户名，而是走「邮箱 + 验证码」验证，防止无效 / 重复注册：

```
① POST /api/auth/email/code   提交邮箱 → 后端生成 6 位验证码并写库 → 通过 SMTP 发送 HTML 邮件
② POST /api/auth/register     提交 邮箱 + 验证码 + 密码 → 校验验证码 → 创建账号（验证码标记为已用）
```

- 验证码规则：6 位数字，默认 **5 分钟**有效、**一次性**使用，同邮箱 **60 秒**内不可重发，
  且每小时最多 10 次（防止恶意刷邮件），超限返回 `429`；
- 邮箱格式在前后端双重校验（Pydantic 校验器 + Element Plus 表单规则）；
- 用户名可留空，系统按邮箱前缀自动生成一个不冲突的用户名；
- 同一套验证码机制同时支撑**忘记密码**：`POST /api/auth/password/reset`；
- 邮件发送封装在 `app/email_service.py`，支持 465 + SSL 与 587 + STARTTLS 两种模式。

### 5. 用户名与绑定邮箱的可维护性

用户名和邮箱都是**账号身份标识**，因此不能像姓名、手机号那样直接改，两者采用不同的安全策略：

| 字段 | 能否修改 | 约束与流程 |
| --- | --- | --- |
| 用户名 | ✅ 可以直接改 | 全局唯一（`sys_user.username` 唯一索引）＋ 3-50 位字母 / 数字 / 下划线；改完写操作日志 |
| 注册邮箱 | ✅ 需验证后改 | 向**新邮箱**发验证码，验证通过才生效；禁止改成「自己当前邮箱」或「他人已注册邮箱」 |
| 真实姓名 / 手机号 | ✅ 可以直接改 | 手机号需全局唯一 |

更换邮箱之所以要求「先验证新邮箱」，是为了防止账号被劫持：如果允许直接改邮箱，
攻击者拿到一次登录态就能把找回密码的通道换成自己的邮箱，从而永久接管账号。
校验通过后旧邮箱立即失效（旧邮箱不能再用于登录与找回密码）。

JWT 中只保存用户 ID（`sub`），`get_current_user` 按 ID 回查数据库，
因此**改名不会使已签发的令牌失效**，用户无需重新登录。

三端（用户端 `/user/profile`、门店端 `/store/account`、管理端 `/admin/account`）
共用同一个组件 `src/components/AccountPanel.vue`，
所以三端的「用户名可改、邮箱需验证后改、密码需原密码」规则完全一致，不会出现某一端口径不同。

### 6. 个人资料与密码的边界

- `PUT /api/auth/me` 只接受 `username / real_name / phone`，**不接受 email**，
  邮箱必须走 `/api/auth/me/email*` 的验证码流程，从接口层面杜绝绕过验证。
- 修改密码需要提供原密码（`PUT /api/auth/me/password`），
  而忘记密码则走邮箱验证码（`POST /api/auth/password/reset`），两条路径互不干扰。

### 7. 头像上传（含上传前裁剪）

头像是**真实的文件上传**，不是只存一个外链字符串；并且**上传前先在浏览器端裁剪**，
用户可以把非方形的照片拖正、缩放，最终统一输出 400×400 的圆形头像：

```
选择本地图片（<input type="file">）
      ↓ 前端先校验：MIME ∈ {jpeg,png,webp,gif} 且原图 ≤ 8MB
AvatarCropper 弹窗（Vue 组件，纯 Canvas，无第三方裁剪库）
      ↓ 拖动平移 + 滚轮/滑杆缩放 → canvas.drawImage → toBlob 输出 400×400 PNG
File(avatar_<时间戳>.png)          ← 此时体积通常 < 200KB，远低于后端 2MB 上限
      ↓ multipart/form-data
POST /api/auth/me/avatar
      ↓ 服务端按「文件头魔数」二次校验真实格式
backend/uploads/avatars/u{用户id}_{随机6字节}.{ext}
      ↓ 记录 /uploads/avatars/xxx.png 到 sys_user.avatar
GET /uploads/avatars/xxx.png   ← FastAPI StaticFiles 挂载
```

- **裁剪算法与几何**：全部抽成纯函数放在 `frontend/src/utils/crop.js`（不碰 DOM，便于单测）。
  - `coverScale()` 保证图片始终**铺满**方形视口（不会露底）；
  - `clampOffset()` 把拖动限制在边界内（图片边缘不会被拖进视口内部）；
  - `anchorZoom()` 保证缩放时**以视口中心为锚点**，不会把用户刚摆正的主体甩出画面；
  - `cropParams()` 把「显示坐标」的裁剪框换算成 `canvas.drawImage` 的参数。
  - `aspectOk()` 拒绝长宽比超过 8:1 的极端图（如全景截图），并友好提示换图。
- **大图降采样**：原图长边超过 1600px 时先等比压到 1600，避免 DOM 元素过大导致拖动卡顿；
  输出仍是 400×400，肉眼无差别。
- **双重校验**：前端按 MIME 类型和 8MB 上限先拦一道；服务端不信任 MIME，
  再用**文件头魔数**（`\xff\xd8\xff` / `\x89PNG` / `GIF8x` / `RIFF....WEBP`）判断真实格式，
  所以把 `.txt` 改名成 `.png` 上传也会被拒。**不允许 SVG**（避免 XSS）。
- **文件命名**：`u{用户id}_{随机串}.{ext}`，天然避免同名冲突与路径穿越。
- **旧文件清理**：换头像 / 恢复默认时，提交成功后删除旧文件，避免磁盘堆积；
  删除前会校验目标确实位于 `uploads/avatars` 目录内。
- **降级表现**：未上传头像时，前端 `UserAvatar` 组件退化为「姓名首字母 + 品牌渐变圆底」，
  三端顶栏（用户端 / 门店端 / 管理端）与个人中心共用同一组件。
- 开发期 `/uploads` 由 Vite 代理转发到后端；该目录已加入 `.gitignore`。

**SMTP 配置**（在 `backend/.env` 中填写，改完重启后端）：

```ini
SMTP_HOST=smtp.qq.com          # QQ邮箱；163 用 smtp.163.com；企业邮用 smtp.exmail.qq.com
SMTP_PORT=465
SMTP_USE_SSL=true              # 587 端口请改为 false（走 STARTTLS）
SMTP_USER=your@qq.com
SMTP_PASSWORD=邮箱SMTP授权码    # 注意不是邮箱登录密码，需在邮箱设置中单独开启并生成
SMTP_FROM=                     # 留空则使用 SMTP_USER
```

**本地调试兜底**：未填写 SMTP 且 `DEBUG=true`、`ALLOW_EMAIL_CODE_ECHO=true` 时，
接口会在响应中回显验证码（`data.debug_code`），前端自动填入并提示「本地调试模式」，
因此**无需配置邮箱也能完整跑通注册 / 找回密码流程**。
生产环境请务必配置真实 SMTP 并将 `ALLOW_EMAIL_CODE_ECHO` 置为 `false`。

## 七、主要接口清单（对应论文附录 B）

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/email/code` | 发送邮箱验证码（注册 / 找回密码） |
| POST | `/api/auth/register` | 邮箱验证码注册 |
| POST | `/api/auth/login` | 登录并获取 JWT 令牌（用户名或邮箱） |
| POST | `/api/auth/password/reset` | 邮箱验证码重置密码 |
| PUT | `/api/auth/me` | 修改个人资料（用户名 / 姓名 / 手机号） |
| POST | `/api/auth/me/email/code` | 更换邮箱：向新邮箱发送验证码 |
| PUT | `/api/auth/me/email` | 更换绑定邮箱（需新邮箱验证码） |
| POST | `/api/auth/me/avatar` | 上传 / 更换头像（multipart） |
| DELETE | `/api/auth/me/avatar` | 恢复默认头像 |
| GET | `/api/stores` | 分页查询可用门店 |
| GET | `/api/stores/{id}/items` | 查询门店养护项目 |
| GET | `/api/slots?store_id=&date=` | 查询指定日期可用时段 |
| POST | `/api/reservations` | 提交预约订单 |
| PATCH | `/api/reservations/{id}/status` | 用户取消订单 |
| GET | `/api/admin/orders` | 管理员分页查询订单 |

完整接口（含车辆、门店端、管理端）请查看 `/docs`。

## 八、测试

论文 5.2 的功能测试用例已在真实接口上验证通过（共 23 项，含正常流程与异常流程）：
登录鉴权、越权拦截、预约容量扣减与约满拦截、订单状态流转、拒绝原因校验、
管理员停用项目后从列表移除、操作日志等。

邮箱注册 / 找回密码链路另经 22 项端到端用例验证（全部通过）：
非法邮箱拦截、已注册邮箱拦截、验证码获取与冷却限流（429）、错误验证码拦截、
验证码一次性、注册成功、邮箱登录、自动生成用户名登录、重置密码后旧密码失效、
用户名 / 手机号占用检测、密码长度校验等。

用户名修改与绑定邮箱更换再经 22 项端到端用例验证（全部通过）：
用户名唯一性冲突、格式与长度校验、改名后可用新用户名登录、未登录拦截、
新邮箱与当前邮箱相同拦截、他人已注册邮箱拦截、换邮箱验证码限流（429）、
错误验证码拦截、换邮箱后新邮箱可登录 / 旧邮箱失效、未登录不能发起换邮箱等。
该组用例在独立端口启动一个关闭 SMTP 的后端实例执行，**不会真实发信**。

头像上传再经 19 项端到端用例验证（全部通过）：
PNG / GIF 上传成功、文件落盘且字节一致、静态地址可访问且内容一致、
换头像后旧文件被清理、伪装成 png 的非图片被魔数校验拦截、空文件拦截、
超过 2MB 拦截、未登录 401、恢复默认后文件清理且可重复调用、测试后无残留。

头像**裁剪**功能单独做了两层验证：

- **纯函数单测 44 项**（`utils/crop.js`，Node 直接跑，无需浏览器）：覆盖
  `coverScale` 的铺满不变式、`clampOffset` 的边界与居中、`anchorZoom` 的
  「缩放后锚点不漂移」「缩回原位可还原」、`cropParams` 在 20 组「尺寸 × 缩放」
  组合下都恰好覆盖输出方框，以及 `aspectOk` / `fitWithin` 的输入守卫。
- **几何 + 像素 + 链路端到端 14 项**：用纯 Python 生成一张 1200×800 的标记图
  （中心纯红、左上角绿、右下角黄），调用与浏览器**同一份** `crop.js` 算出裁剪矩形，
  再按该矩形真实采样出 400×400 输出图，断言
  「输出中心就是源图中心的红色」且「四角没有混入绿/黄标记」——即裁剪确实以图片中心为锚点；
  同时校验放大 2× 后仍居中，并把这 400×400 图经 Vite 代理实际上传、回读字节一致。
- 另有 **7 项前端资源校验**：确认 dev server 已下发新组件、旧 `el-upload` 分支已彻底移除、
  三端账号页均引用同一 `AccountPanel`。

**单端口部署包**再经 **31 项端到端用例**验证（全部通过）：在只有 SQLite、没有 MySQL、
没有 Vite 的干净环境下冷启动，逐项校验「单端口同时提供前端与后端」、SPA 深链接刷新不 404、
未知 `/api` 路径返回 JSON 而非 HTML、演示数据自动写入、三类账号可登录、头像上传与回读字节一致、
公开演示的安全护栏（`reset` 验证码禁止回显），以及**令牌多载体**：
仅用 `X-Auth-Token` / 仅用 `Authorization` / 仅用查询参数三种方式都能通过鉴权，
并且「`Authorization` 被网关塞入解不开的令牌」时其余通道仍然生效；
其中 1 项专门断言诊断接口**绝不回显任何令牌原文**，防止凭据泄露。
同一组鉴权场景另在**开发模式**下复测 **20 项**（直连后端 8000 与经 Vite 代理 5173 各 10 项，全部通过），
确保「多载体」改动没有破坏原有的本地开发链路。

## 九、界面与主题

前端内置**浅色 / 暗色双主题**，右上角开关一键切换，选择会持久化到浏览器：

- 主题状态由 `src/store/theme.js` 统一管理（`light` / `dark`），首次访问跟随系统
  `prefers-color-scheme`，之后记住用户选择，并在应用挂载前应用，避免首屏闪烁。
- 暗色基于 Element Plus 官方暗色变量（`element-plus/theme-chalk/dark/css-vars.css`），
  通过 `<html class="dark">` 生效；切换组件为 `src/components/ThemeToggle.vue`。
- 自定义样式全部使用 `src/styles.css` 顶部的 CSS 变量令牌（`:root` 浅色 / `html.dark` 暗色），
  因此在两种主题下都能保持一致的层次与对比度。

视觉上统一了：吸顶毛玻璃导航、深色渐变侧边栏、悬浮反馈的门店卡片、带色条的统计卡片、
统一卡片圆角与阴影，以及页面切换的淡入过渡。

## 十、常见问题排查

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 页面能打开，但一切操作都提示**无法连接后端服务**（或 Network Error） | 后端（8000）没在运行 | 双击项目根目录 `start-all.bat`，或单独跑 `backend/start-backend.bat` |
| 页面提示**服务不可用 / 空屏** | 前端 dev server（5173）没在运行 | 双击 `start-all.bat`，或跑 `frontend/start-frontend.bat` |
| 头像上传后**不显示**（404） | `vite.config.js` 改了 `server.proxy` 但没重启 dev server | 重启前端（proxy 配置**不会热更新**） |
| 注册/找回密码提示**邮件服务未配置** | `.env` 里 SMTP 为空且 `ALLOW_EMAIL_CODE_ECHO=false` | 填好 SMTP，或临时把 `ALLOW_EMAIL_CODE_ECHO` 设回 `true` 走调试回显 |
| 接口报 `参数校验失败` / 中文乱码 | 数据库连接串缺少 `?charset=utf8mb4` | 检查 `DATABASE_URL` |
| 老库启动报**字段不存在** | 旧库缺 `email` / `avatar` 列 | 执行 `cd backend && .venv\Scripts\python.exe migrate.py` |
| **登录成功，但立刻又跳回登录页**、所有鉴权接口 401 | 反向代理补写/改写了 `Authorization` 头，客户端令牌被盖掉 | 已内置多载体方案（见 §4.5），无需处理；排查时先看 `GET /api/diagnostic/headers` |
| 线上页面正常但接口全坏 | 发布包不是用 `build-deploy.py` 生成的，`SERVE_SPA` / `AUTO_SEED` 没生效 | 重新执行 `python build-deploy.py` 后再发布 |

> 快捷键速查：后端 <http://127.0.0.1:8000/docs> ／ 前端 <http://localhost:5173> ／ 数据库连接见 `backend/.env`。

## 十一、后续可扩展方向（论文结语）

在线支付、短信 / 微信通知、技师排班、基于历史订单的客流预测、移动端适配等。
