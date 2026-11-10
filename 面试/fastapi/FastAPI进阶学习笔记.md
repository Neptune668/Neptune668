# FastAPI 进阶学习笔记

> 本篇为基础篇（`FastAPI学习笔记.md`）的进阶延伸，聚焦生产级开发中的八大核心主题。
> 每个主题结构统一：**核心概念** → **关键代码** → **常见陷阱** → **实用示例**。
>
> 环境：Python 3.10+、FastAPI 0.110+、Pydantic v2、`uvicorn[standard]`、SQLAlchemy 2.0（async）。

---

## 目录

1. [依赖注入进阶用法](#1-依赖注入进阶用法)
2. [中间件与自定义异常处理](#2-中间件与自定义异常处理)
3. [异步编程与后台任务](#3-异步编程与后台任务)
4. [数据库交互（含异步 ORM）](#4-数据库交互含异步-orm)
5. [WebSocket](#5-websocket)
6. [安全认证与权限控制](#6-安全认证与权限控制)
7. [Pydantic 模型进阶校验](#7-pydantic-模型进阶校验)
8. [性能优化与部署要点](#8-性能优化与部署要点)
9. [附录：进阶陷阱速查表](#9-附录进阶陷阱速查表)

---

## 1. 依赖注入进阶用法

### 核心概念

依赖注入（Dependency Injection, DI）是 FastAPI 的核心机制。进阶场景包括：

- **带参数的子依赖**：用类或工厂函数构造可配置的依赖
- **yield 依赖（资源管理）**：依赖函数中使用 `yield`，替代请求事件做资源获取与释放
- **依赖作用域**：默认每个请求解析一次并缓存（`request scope`）；用 `use_cache=False` 关闭缓存
- **类作为依赖**：路由参数多时，用类封装查询参数更清晰
- **全局依赖与路由级依赖**：`FastAPI(dependencies=[...])` / `APIRouter(dependencies=[...])`，用于鉴权等不返回值的场景

### 关键代码

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException

app = FastAPI()

# ---- 1. 带参数的子依赖（依赖工厂）----
class Pagination:
    def __init__(self, page: int = 1, size: int = 20, max_size: int = 100):
        self.page = max(page, 1)
        self.size = min(size, max_size)

PaginationDep = Annotated[Pagination, Depends()]

@app.get("/items")
def list_items(p: PaginationDep):
    return {"page": p.page, "size": p.size}

# ---- 2. yield 依赖：请求结束后自动清理 ----
from contextlib import asynccontextmanager

def get_db():
    db = SessionLocal()
    try:
        yield db          # 请求处理中使用
    finally:
        db.close()        # 响应发送后执行清理

DB = Annotated[Session, Depends(get_db)]

# ---- 3. use_cache=False：同一请求内每次重新解析 ----
import time

def timestamp():
    return time.time()

@app.get("/cache")
def cache_demo(
    a: Annotated[float, Depends(timestamp)],
    b: Annotated[float, Depends(timestamp)],                      # a == b（默认缓存）
    c: Annotated[float, Depends(timestamp, use_cache=False)],     # c 独立计算
):
    return {"a": a, "b": b, "c": c}

# ---- 4. 依赖中抛异常做拦截 ----
def verify_token(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "invalid token")
    return payload
```

### 常见陷阱

- **陷阱1：yield 之后的代码在响应发送后执行**，若在其中抛异常，客户端已收到响应，异常只能记录日志，无法改变响应。FastAPI 0.118+ 默认在 yield 依赖中发生异常时会回滚到请求结束前抛 HTTPException，旧版本需注意。
- **陷阱2：依赖默认每请求缓存一次**。如果依赖返回的是可变对象（如 DB session），不要在依赖之间假设它们是两个独立实例。
- **陷阱3：在依赖中使用同步阻塞调用**（如 `requests.get`）会阻塞事件循环。依赖函数可以是 `async def`，应配合异步库。
- **陷阱4：`BackgroundTasks` 不能通过 yield 依赖获取**，因为它绑定在请求生命周期内。

### 实用示例：分层鉴权依赖

```python
from fastapi import Security
from pydantic import BaseModel

class User(BaseModel):
    id: int
    scopes: list[str]

def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    user = parse_token(token)
    for scope in security_scopes.scopes:
        if scope not in user.scopes:
            raise HTTPException(403, f"需要权限: {scope}")
    return user

# OAuth2 scopes 驱动的细粒度权限
@app.get("/admin/users")
def admin_list(user: Annotated[User, Security(get_current_user, scopes=["users:read"])]):
    return {"by": user.id}
```

---

## 2. 中间件与自定义异常处理

### 核心概念

- **中间件**：包裹整个请求/响应链路（ASGI 层），适合做日志、计时、CORS、限流、请求 ID 注入
- **异常处理器**：`@app.exception_handler` 注册，将异常转换为结构化响应
- 执行顺序：请求进来时**后注册的中间件先执行**（洋葱模型，最外层的是最后添加的）

### 关键代码

```python
import time, uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# ---- 函数式中间件（推荐，基于 @app.middleware("http")）----
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = uuid.uuid4().hex[:8]
    start = time.perf_counter()
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response

# ---- 自定义异常 + 处理器 ----
class BizError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status

@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError):
    return JSONResponse(
        status_code=exc.status,
        content={"code": exc.code, "message": exc.message,
                 "request_id": getattr(request.state, "request_id", None)},
    )

# ---- 统一校验错误格式（RequestValidationError）----
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(map(str, e["loc"])), "msg": e["msg"]}
              for e in exc.errors()]
    return JSONResponse(status_code=422, content={"code": "VALIDATION_ERROR", "errors": errors})

@app.get("/order")
def create_order():
    raise BizError("STOCK_NOT_ENOUGH", "库存不足", 409)
```

### 常见陷阱

- **陷阱1：函数式中间件里 `request.body()` 只能读一次**。读取后要自己缓存或重建请求，否则下游拿不到 body。
- **陷阱2：中间件中抛出的异常不会走 `exception_handler`**（异常处理器在中间件栈内侧）。需要在中间件内自行 try/except。
- **陷阱3：`BaseHTTPMiddleware` 会引入额外开销且有已知坑**（如 StreamingResponse 缓冲、async 上下文丢失）。能用 `@app.middleware("http")` 就别写类中间件；追求性能可直接写纯 ASGI 中间件。
- **陷阱4：顺序错误**。CORS 通常应该是**最外层**（最后 `add_middleware`），确保异常响应也带 CORS 头。

### 实用示例：纯 ASGI 限流中间件

```python
from starlette.types import ASGIApp, Receive, Scope, Send
from collections import defaultdict

class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, qps: int = 100):
        self.app, self.qps = app, qps
        self.bucket: dict[str, list[float]] = defaultdict(list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        ip = scope["client"][0]
        now = time.monotonic()
        hits = [t for t in self.bucket[ip] if now - t < 1.0]
        if len(hits) >= self.qps:
            resp = JSONResponse({"detail": "Too Many Requests"}, status_code=429)
            return await resp(scope, receive, send)
        hits.append(now)
        self.bucket[ip] = hits
        await self.app(scope, receive, send)

app.add_middleware(RateLimitMiddleware, qps=50)
```

---

## 3. 异步编程与后台任务

### 核心概念

- `async def` 路由在事件循环中运行；普通 `def` 路由会被 FastAPI 丢到**线程池**执行（默认 40 线程）
- **不要把阻塞代码放进 async 路由**：`time.sleep`、同步 requests、CPU 密集计算都会卡死整个事件循环
- 阻塞 I/O 用异步库（`httpx.AsyncClient`、`aiofiles`、异步 DB 驱动）或 `anyio.to_thread.run_sync`
- **BackgroundTasks**：响应返回后执行轻量任务（发邮件、写日志）；重任务交给 Celery / ARQ / Dramatiq

### 关键代码

```python
import asyncio, httpx
from fastapi import BackgroundTasks, FastAPI

app = FastAPI()

# ---- 并发调用多个外部服务 ----
@app.get("/dashboard")
async def dashboard():
    async with httpx.AsyncClient() as client:
        user, orders, stats = await asyncio.gather(
            client.get("http://svc/user"),
            client.get("http://svc/orders"),
            client.get("http://svc/stats"),
        )
    return {"user": user.json(), "orders": orders.json(), "stats": stats.json()}

# ---- 阻塞任务正确姿势 ----
import time

@app.get("/blocking-wrong")
async def wrong():
    time.sleep(5)                     # ❌ 阻塞整个事件循环
    return {"ok": True}

from anyio import to_thread

@app.get("/blocking-right")
async def right():
    await to_thread.run_sync(time.sleep, 5)   # ✅ 丢到线程池
    return {"ok": True}

# ---- 后台任务 ----
def send_email(to: str, subject: str):
    time.sleep(2)  # 模拟慢操作
    print(f"sent to {to}")

@app.post("/register")
async def register(email: str, bg: BackgroundTasks):
    bg.add_task(send_email, email, "Welcome")  # 响应后立即返回，任务后台执行
    return {"status": "registered"}

# ---- lifespan：应用级资源管理 ----
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient()   # 启动时创建，全应用复用
    yield
    await app.state.http.aclose()          # 关闭时释放

app.router.lifespan_context = lifespan
```

### 常见陷阱

- **陷阱1：把 CPU 密集任务放进 async 路由**——应使用进程池 `ProcessPoolExecutor` 或独立 worker。
- **陷阱2：`BackgroundTasks` 没有重试、持久化与监控**。进程崩溃任务即丢失，关键任务必须走消息队列。
- **陷阱3：`asyncio.gather` 一个失败全失败**——用 `return_exceptions=True` 收集部分失败。
- **陷阱4：共享 AsyncClient 没有超时配置**——生产环境务必设 `timeout`、`limits`（连接池）。

### 实用示例：带超时的并发聚合

```python
async def fetch(client: httpx.AsyncClient, url: str) -> dict | None:
    try:
        r = await client.get(url, timeout=2.0)
        return r.json()
    except Exception:
        return None

@app.get("/agg")
async def agg():
    async with httpx.AsyncClient() as client:
        urls = ["http://svc/a", "http://svc/b", "http://svc/c"]
        results = await asyncio.gather(*(fetch(client, u) for u in urls))
    return {"data": [r for r in results if r]}
```

---

## 4. 数据库交互（含异步 ORM）

### 核心概念

- SQLAlchemy 2.0 原生支持 asyncio：`create_async_engine` + `async_sessionmaker`
- **会话生命周期 = 请求生命周期**：通过 yield 依赖注入 session，请求结束自动关闭
- 异步驱动选择：PostgreSQL → `asyncpg`；MySQL → `aiomysql`/`asyncmy`；SQLite → `aiosqlite`
- 不要用同步引擎配合 `run_in_threadpool` 凑活用，容易埋连接泄漏的雷

### 关键代码

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20, max_overflow=10, pool_pre_ping=True,  # pre_ping 剔除死连接
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True)
    price: Mapped[float]

# deps.py
from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session

# routers
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select

app = FastAPI()
DB = Annotated[AsyncSession, Depends(get_db)]

@app.post("/items", status_code=201)
async def create_item(name: str, price: float, db: DB):
    item = Item(name=name, price=price)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id}

@app.get("/items/{item_id}")
async def read_item(item_id: int, db: DB):
    item = await db.get(Item, item_id)              # 主键查询
    if not item:
        raise HTTPException(404, "item not found")
    return item

@app.get("/items")
async def list_items(db: DB, skip: int = 0, limit: int = 20):
    result = await db.execute(select(Item).offset(skip).limit(limit))
    return result.scalars().all()
```

### 常见陷阱

- **陷阱1：跨 await 使用 ORM 懒加载属性** → 触发 `MissingGreenlet` 错误。解决：`selectinload` 预加载，或设置 `expire_on_commit=False`。
- **陷阱2：事务边界不清**。推荐在依赖中统一 commit/rollback，路由只做业务：

```python
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- **陷阱3：连接池耗尽**。asyncpg 默认池较小，高并发下 `pool_size` 要按 `并发数/worker数` 估算，且数据库端 `max_connections` 要够。
- **陷阱4：把 `AsyncSession` 当全局单例**。Session 不是线程/协程安全的，必须每请求一个。

### 实用示例：N+1 查询修复

```python
from sqlalchemy.orm import selectinload

# ❌ N+1：每个 order 单独查 user
result = await db.execute(select(Order))
orders = result.scalars().all()
for o in orders:
    print(o.user.name)   # 每次访问触发一次查询（async 下直接报错）

# ✅ 一次 JOIN 预加载
result = await db.execute(
    select(Order).options(selectinload(Order.user))
)
```

---

## 5. WebSocket

### 核心概念

- `@app.websocket("/ws")` 建立长连接；协议生命周期：`accept` → 循环 `receive`/`send` → `close`
- 支持 `receive_text/json/bytes`，以及底层 `receive()` 处理断开事件
- 依赖注入在 WebSocket 路由同样可用（可用 `WebSocket` 参数、`Depends`），但**不能返回 HTTP 响应**，拒绝连接用 `await ws.close(code=1008)`
- 生产广播/多实例需要 Redis Pub/Sub 或 NATS 做消息总线

### 关键代码

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}  # room -> connections

    async def connect(self, room: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(room, []).append(ws)

    def disconnect(self, room: str, ws: WebSocket):
        self.active.get(room, []).remove(ws)

    async def broadcast(self, room: str, message: dict):
        for ws in list(self.active.get(room, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room, ws)   # 剔除死连接

manager = ConnectionManager()

@app.websocket("/ws/{room}/{username}")
async def chat(ws: WebSocket, room: str, username: str):
    await manager.connect(room, ws)
    await manager.broadcast(room, {"type": "join", "user": username})
    try:
        while True:
            data = await ws.receive_json()
            await manager.broadcast(room,
                {"type": "msg", "user": username, "text": data["text"]})
    except WebSocketDisconnect:
        manager.disconnect(room, ws)
        await manager.broadcast(room, {"type": "leave", "user": username})
```

鉴权示例：

```python
@app.websocket("/ws/secure")
async def secure_ws(ws: WebSocket, token: str | None = None):
    if not verify_token(token):
        await ws.close(code=1008, reason="unauthorized")  # 1008 = Policy Violation
        return
    await ws.accept()
    ...
```

### 常见陷阱

- **陷阱1：忘记处理 `WebSocketDisconnect`**，客户端断开后服务端报错且资源泄漏。
- **陷阱2：广播时向已断开的连接 send** 会抛异常，必须 try/except 并剔除。
- **陷阱3：多 worker 部署时内存态 ConnectionManager 失效**——进程 A 的连接收不到进程 B 的消息，需要 Redis 等外部总线。
- **陷阱4：心跳缺失**。反向代理（Nginx 默认 60s）会静默断连，需要应用层 ping/pong 或调整代理超时。

### 实用示例：客户端（测试用）

```python
# pip install websockets
import asyncio, websockets, json

async def run():
    async with websockets.connect("ws://localhost:8000/ws/lobby/alice") as ws:
        await ws.send(json.dumps({"text": "hello"}))
        print(await ws.recv())

asyncio.run(run())
```

---

## 6. 安全认证与权限控制

### 核心概念

- **OAuth2 Password Flow + JWT** 是 FastAPI 生态标准做法
- 密码哈希用 `pwdlib`（argon2/bcrypt），**禁止明文存储**
- JWT：短有效期 access token + refresh token 轮换
- 权限模型：scopes（粗粒度）→ RBAC（角色）→ ABAC（属性），按复杂度渐进
- `OAuth2PasswordBearer` 只是提取 token 的工具类，真正的校验在自己的依赖里

### 关键代码

```python
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

SECRET_KEY = "change-me-use-env"  # 生产用环境变量，openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_EXPIRE = timedelta(minutes=30)

password_hash = PasswordHash.recommended()   # 默认 argon2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class User(BaseModel):
    username: str
    disabled: bool = False
    scopes: list[str] = []

# 假用户库
USERS = {"alice": {"username": "alice",
                   "hashed": password_hash.hash("secret"),
                   "scopes": ["items:read", "items:write"]}}

def create_token(username: str, scopes: list[str]) -> str:
    payload = {"sub": username, "scopes": scopes,
               "exp": datetime.now(timezone.utc) + ACCESS_EXPIRE}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = USERS.get(form.username)
    if not user or not password_hash.verify(form.password, user["hashed"]):
        raise HTTPException(401, "用户名或密码错误",
                            headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_token(form.username, user["scopes"]))

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username or username not in USERS:
            raise ValueError
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(401, "凭证无效",
                            headers={"WWW-Authenticate": "Bearer"})
    u = USERS[username]
    return User(username=username, scopes=u["scopes"])

CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/me")
async def me(user: CurrentUser):
    return user

# scope 校验
from fastapi import Security

@app.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    user: Annotated[User, Security(get_current_user, scopes=["items:write"])],
):
    return {"deleted": item_id}
```

### 常见陷阱

- **陷阱1：`jwt.decode` 没传 `algorithms`** → 算法混淆攻击（alg=none / RS256→HS256）。
- **陷阱2：密钥硬编码进仓库**。用环境变量 / secrets manager，HS256 密钥至少 32 字节。
- **陷阱3：token 没有 `exp`** → 永久有效。也要考虑 `iat`、`iss`、`aud` 校验。
- **陷阱4：登录接口不限流** → 撞库风险。登录端点必须加频率限制，失败次数过多锁定。
- **陷阱5：logout 后 token 仍有效**。JWT 无状态，敏感系统需要服务端黑名单（Redis 存 jti 直到过期）。

### 实用示例：API Key 双轨认证（供第三方调用）

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
VALID_KEYS = {"sk-live-xxx": "partner-a"}

async def get_principal(
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
    api_key: Annotated[str | None, Depends(api_key_header)] = None,
):
    if api_key and api_key in VALID_KEYS:
        return {"type": "partner", "id": VALID_KEYS[api_key]}
    if token:
        return {"type": "user", "id": decode(token)["sub"]}
    raise HTTPException(401, "需要提供 Bearer token 或 X-API-Key")
```

---

## 7. Pydantic 模型进阶校验

### 核心概念（Pydantic v2）

- `Field(...)` 声明约束；`field_validator` / `model_validator` 自定义校验
- `Annotated[type, Field(...), ...]` 组合复用校验逻辑
- `model_config = ConfigDict(...)` 控制行为（`extra="forbid"`、`str_strip_whitespace` 等）
- `field_serializer` 自定义序列化输出
- 校验失败抛 `ValidationError`，FastAPI 转为 `RequestValidationError`（422）

### 关键代码

```python
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonEmptyStr = Annotated[str, Field(min_length=1, strip_whitespace=True)]
Price = Annotated[float, Field(gt=0, le=1_000_000)]

class ItemIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: NonEmptyStr = Field(max_length=100)
    price: Price
    tags: list[NonEmptyStr] = Field(default_factory=list, max_length=10)
    discount: float | None = Field(default=None, ge=0, le=1)

    @field_validator("name")
    @classmethod
    def name_no_admin(cls, v: str) -> str:
        if "admin" in v.lower():
            raise ValueError("名称不能包含 admin")
        return v.title()          # validator 可以转换值

    @field_validator("tags", mode="before")
    @classmethod
    def split_tags(cls, v):
        if isinstance(v, str):    # 支持 "a,b,c" 字符串输入
            return [t.strip() for t in v.split(",")]
        return v

    @model_validator(mode="after")
    def check_discount(self):
        if self.discount and self.price < 10:
            raise ValueError("低价商品不支持折扣")
        return self

class ItemOut(BaseModel):
    id: int
    name: str
    final_price: float

    # 响应模型过滤：请求里的敏感字段不会出现在响应中
```

请求/响应分离 + 部分更新：

```python
class ItemUpdate(BaseModel):
    name: str | None = None
    price: float | None = None

@app.patch("/items/{item_id}")
async def patch(item_id: int, patch: ItemUpdate, db: DB):
    item = await db.get(Item, item_id)
    data = patch.model_dump(exclude_unset=True)   # 只取显式传入的字段
    for k, v in data.items():
        setattr(item, k, v)
    await db.commit()
    return item
```

### 常见陷阱

- **陷阱1：`model_dump()` 与 `exclude_unset` 混用错误**。全量更新用普通 dump，PATCH 必须 `exclude_unset=True`，否则 None 默认值覆盖数据库。
- **陷阱2：v1 写法残留**。`@validator` → `@field_validator`，`.dict()` → `.model_dump()`，`class Config` → `model_config = ConfigDict(...)`。
- **陷阱3：validator 中的异常类型**。要抛 `ValueError`/`AssertionError`（会被包装成 422），抛其他异常会变 500。
- **陷阱4：响应模型用了 `orm_mode` 旧写法**，v2 是 `model_config = ConfigDict(from_attributes=True)`。
- **陷阱5：`extra="ignore"`（默认）静默丢弃拼错的字段**——对外 API 建议 `forbid` 及早暴露调用方错误。

### 实用示例：可复用的强类型 ID

```python
from pydantic import BeforeValidator
from typing import Annotated

def coerce_id(v):
    try:
        v = int(v)
    except (TypeError, ValueError):
        raise ValueError("ID 必须是整数")
    if v <= 0:
        raise ValueError("ID 必须为正数")
    return v

PositiveId = Annotated[int, BeforeValidator(coerce_id)]

class OrderQuery(BaseModel):
    user_id: PositiveId
    order_id: PositiveId
```

---

## 8. 性能优化与部署要点

### 核心概念

- **服务器栈**：`Gunicorn`（进程管理）+ `Uvicorn worker`（ASGI），或直接 `uvicorn --workers N`
- worker 数量经验值：`(2 × CPU 核数) + 1`，I/O 密集可适当调高
- **响应模型裁剪** + `response_model_exclude_unset` 减少序列化开销
- 缓存：Redis（响应缓存 / 会话）、HTTP 缓存头（ETag、Cache-Control）
- 压缩：`GZipMiddleware`（>1KB 响应开启）
- 观测：结构化日志、Prometheus 指标（`prometheus-fastapi-instrumentator`）、OpenTelemetry 链路追踪
- 容器化：多阶段构建、非 root 运行、健康检查端点

### 关键代码

```bash
# 生产启动（Linux）
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --access-logfile -

# 单机简易方案
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

```python
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    docs_url=None, redoc_url=None,      # 生产环境关闭文档（或加鉴权）
    openapi_url=None,
)

# 注意添加顺序：最后添加的最先执行
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # 不要用 ["*"] + credentials
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=86400,
)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

Dockerfile 示例：

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN useradd -r appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
USER appuser
EXPOSE 8000
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### 常见陷阱

- **陷阱1：`--reload` 带到生产**——热重载会 fork 进程并大幅降低性能，仅限开发。
- **陷阱2：单 worker 跑 CPU 密集 + 异步混合应用**——事件循环被独占，所有请求排队。
- **陷阱3：CORS 配置 `allow_origins=["*"]` 且 `allow_credentials=True`**——浏览器会拒绝且语义危险，必须显式列域名。
- **陷阱4：Docker 里 listen 127.0.0.1**——容器外无法访问，必须 `0.0.0.0`。
- **陷阱5：没有优雅停机**。`--graceful-timeout` 保证滚动发布时正在处理的请求能完成。
- **陷阱6：日志用 print**。用 `logging` + 结构化输出（如 `structlog` JSON），并在中间件里注入 request_id 串联日志。

### 实用示例：Redis 响应缓存装饰器

```python
import json, functools
import redis.asyncio as redis

cache = redis.Redis(host="localhost", decode_responses=True)

def cached(ttl: int = 60, prefix: str = "api"):
    def deco(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{prefix}:{func.__name__}:{hash(json.dumps(kwargs, sort_keys=True, default=str))}"
            if (hit := await cache.get(key)) is not None:
                return json.loads(hit)
            result = await func(*args, **kwargs)
            await cache.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return deco

@app.get("/stats")
@cached(ttl=30)
async def stats(category: str = "all"):
    await asyncio.sleep(1)  # 模拟昂贵计算
    return {"category": category, "value": 42}
```

---

## 9. 附录：进阶陷阱速查表

| 主题 | 陷阱 | 一句话对策 |
|---|---|---|
| 依赖注入 | yield 后抛异常无法改变响应 | 校验放 yield 之前 |
| 依赖注入 | 以为每次 Depends 都是新对象 | 默认每请求缓存，需要时用 `use_cache=False` |
| 中间件 | 中间件内异常不走 handler | 中间件内部自行 try/except |
| 中间件 | body 只读一次 | 读后缓存或重建 receive |
| 异步 | async 路由里调同步阻塞库 | 换异步库或 `to_thread.run_sync` |
| 异步 | BackgroundTasks 当消息队列用 | 关键任务用 Celery/ARQ |
| 数据库 | async ORM 懒加载报 MissingGreenlet | `selectinload` 预加载 |
| 数据库 | Session 当全局单例 | 每请求一个，yield 依赖管理 |
| WebSocket | 广播到死连接 | try/except + 剔除 |
| WebSocket | 多 worker 内存广播失效 | Redis Pub/Sub 总线 |
| 安全 | JWT 未指定 algorithms | `decode(..., algorithms=[...])` 显式指定 |
| 安全 | 密码明文/弱哈希 | argon2/bcrypt + 登录限流 |
| Pydantic | PATCH 全量 dump 覆盖数据 | `exclude_unset=True` |
| Pydantic | validator 抛普通异常变 500 | 只抛 `ValueError` |
| 部署 | `--reload` 上生产 | 仅开发使用 |
| 部署 | 容器内 listen 127.0.0.1 | 绑定 `0.0.0.0` |
| 部署 | 无优雅停机 | `--graceful-timeout` + health check |

---

> **复习建议**：每个主题先遮住代码复述思路，再动手默写最小示例；速查表适合面试前 10 分钟快速过一遍。
