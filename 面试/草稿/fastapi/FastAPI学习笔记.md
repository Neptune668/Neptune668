# FastAPI 系统化学习笔记

> 本笔记按由浅入深的顺序组织，从「快速上手」到「高级特性」，覆盖 FastAPI 核心开发流程。
> 每个主题包含：**概念说明** → **代码示例** → **注意事项** → **最佳实践**。
>
> 环境建议：Python 3.9+，`pip install "fastapi[standard]"`（含 uvicorn、pydantic v2）。

---

## 目录

1. [快速上手：最小应用](#1-快速上手最小应用)
2. [路由定义与请求处理（GET/POST/PUT/DELETE）](#2-路由定义与请求处理)
3. [路径参数与查询参数](#3-路径参数与查询参数)
4. [请求体模型与 Pydantic 数据验证](#4-请求体模型与-pydantic-数据验证)
5. [依赖注入机制](#5-依赖注入机制)
6. [中间件与异常处理](#6-中间件与异常处理)
7. [异步支持与后台任务](#7-异步支持与后台任务)
8. [自动文档生成（Swagger UI 与 ReDoc）](#8-自动文档生成)
9. [附录：常见陷阱速查](#9-附录常见陷阱速查)

---

## 1. 快速上手：最小应用

### 概念说明

FastAPI 是基于 Python 类型注解（type hints）构建的现代 Web 框架，底层由 Starlette（负责 Web 部分）和 Pydantic（负责数据校验）驱动。核心思路是：**用类型注解声明参数，框架自动完成校验、序列化与文档生成**。

### 代码示例

```python
from fastapi import FastAPI

app = FastAPI()  # 创建应用实例，是所有路由的挂载点


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}
```

启动命令：

```bash
uvicorn main:app --reload
# main = 文件名，app = 应用实例，--reload = 开发热重载
```

访问 `http://127.0.0.1:8000/` 即可看到 JSON 返回。

### 注意事项

- `uvicorn main:app` 中的 `app` 必须是**模块级变量**，不能被 `if __name__ == "__main__"` 包裹，否则无法被导入。
- 默认监听 `8000` 端口，若冲突用 `--port 8080` 指定。
- 生产环境**不要**用 `--reload`，应使用多进程（如 `gunicorn -k uvicorn.workers.UvicornWorker`）。

### 最佳实践

- 项目规模变大后，用 APIRouter 拆分路由，而不是把所有接口堆在 `main.py`。
- 保持 `app = FastAPI()` 的创建逻辑简单，复杂配置（文档标题、中间件）集中在 `create_app` 工厂函数中。

---

## 2. 路由定义与请求处理

### 概念说明

路由（Route）把「HTTP 方法 + 路径」映射到具体处理函数。FastAPI 用装饰器声明：`@app.get`、`@app.post`、`@app.put`、`@app.delete` 分别对应四种最常用的请求方法。装饰器内第一个参数是路径，函数返回值会被自动序列化为 JSON 响应。

### 代码示例

```python
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/items")
def list_items():
    return [{"id": 1, "name": "键盘"}]


@app.post("/items", status_code=status.HTTP_201_CREATED)  # 指定状态码
def create_item(item: dict):
    # 创建成功后返回 201，而非默认的 200
    return {"id": 2, **item}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: dict):
    return {"id": item_id, **item}


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    # 204 表示成功但无返回体
    return None


# 一个函数同时处理多个方法
@app.api_route("/ping", methods=["GET", "HEAD"])
def ping():
    return {"status": "ok"}
```

### 注意事项

- `PUT` 语义是**整体替换**，`PATCH` 才是部分更新；但 FastAPI 中两者实现方式相同，区分的是业务语义。
- `status.HTTP_201_CREATED` 优于魔法数字 `201`，可读性更好，也避免写错。
- 返回 `None` 时如果声明了 `204`，FastAPI 会正常返回空体；若未声明则可能报错，注意配套使用。

### 最佳实践

- 按资源组织路由：`/items`、`/items/{item_id}`、`/items/{item_id}/comments`。
- 一个 REST 资源的一组接口用 APIRouter 聚拢，并在主应用中 `include_router`。
- 状态码语义化：创建→201、删除→204、未授权→401、禁止→403、未找到→404。

---

## 3. 路径参数与查询参数

### 概念说明

- **路径参数（Path Parameter）**：写在 URL 路径中的变量，如 `/items/{item_id}`，通常用于定位具体资源，是 URL 的一部分，**必填**。
- **查询参数（Query Parameter）**：写在 `?` 之后的键值对，如 `/items?skip=0&limit=10`，通常用于过滤、排序、分页，可设默认值变为可选。
- 两者都通过**函数参数的类型注解**声明，FastAPI 自动做类型转换与校验。

### 代码示例

```python
from fastapi import FastAPI, Path, Query
from typing import Annotated  # Python 3.9+

app = FastAPI()


# 路径参数：自动转 int，非数字会返回 422
@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}


# 查询参数：有默认值 → 可选；无默认值 → 必填
@app.get("/search")
def search(
    q: str,                    # 必填查询参数
    page: int = 1,             # 可选，默认 1
    limit: int = 10,
):
    return {"q": q, "page": page, "limit": limit}


# 用 Annotated + Path/Query 添加校验与元数据
@app.get("/items/")
def list_items(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return {"skip": skip, "limit": limit}


@app.get("/users/{user_id}")
def get_user(
    user_id: Annotated[int, Path(gt=0, description="用户 ID")],
    verbose: Annotated[bool, Query()] = False,
):
    return {"user_id": user_id, "verbose": verbose}
```

调用示例：

```
GET /items/42            → item_id=42
GET /search?q=hello&page=2
GET /items/?skip=20&limit=50
GET /users/5?verbose=true
```

### 注意事项

- **路由声明顺序很重要**：`/items/{item_id}` 会捕获 `/items/anything`，因此静态路径（如 `/items/me`）必须声明在动态路径**之前**，否则会被动态路径吞掉。
- 路径参数与查询参数可以同名吗？**不能**——如果函数里同时有 `item_id` 且它既是路径参数又是查询参数会冲突，需刻意区分命名。
- 布尔查询参数：`?verbose=true` 中 `true/false/1/0` 会被自动解析为 `bool`。
- 同一个路径参数若在多个函数中重复，类型注解要保持一致。

### 最佳实践

- 分页、过滤、排序一律用查询参数，并给默认值 + 范围校验（`ge/le`）。
- 用 `Annotated[..., Query(...)]` 而不是把默认值直接写进 `Query()`，代码更清晰，也便于复用类型。
- 路径参数永远用于**资源定位**，不要用来传复杂对象。

---

## 4. 请求体模型与 Pydantic 数据验证

### 概念说明

请求体（Request Body）是 POST/PUT/PATCH 中随请求发送的 JSON 数据。FastAPI 用 **Pydantic 模型**声明请求体结构：定义一个继承 `BaseModel` 的类，把它的类型作为函数参数注解，框架就会自动完成「JSON → Python 对象 → 校验 → 失败返回 422」的完整链路。

### 代码示例

```python
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field, field_validator, EmailStr
from fastapi import FastAPI, Query

app = FastAPI()


# 基础模型
class Item(BaseModel):
    name: str
    price: float = Field(gt=0, description="价格，必须大于 0")
    is_offer: bool = False          # 带默认值 → 可选字段
    tags: List[str] = []
    description: Optional[str] = None


# 嵌套模型
class User(BaseModel):
    username: str
    email: EmailStr                # 自动校验邮箱格式（需安装 email-validator）
    full_name: Optional[str] = None


class Order(BaseModel):
    item: Item
    user: User
    quantity: int = Field(default=1, ge=1)


# 自定义校验器
class Signup(BaseModel):
    username: str
    password: str = Field(min_length=8)
    password2: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()

    @field_validator("password2")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次密码不一致")
        return v


@app.post("/items/")
def create_item(item: Item):
    # 校验通过后，item 已是类型安全的 Item 对象
    return {"name": item.name, "price": item.price}


@app.post("/orders/")
def create_order(order: Order):
    return {"user": order.user.username, "item": order.item.name}


@app.post("/signup")
def signup(data: Signup):
    return {"username": data.username}
```

### 注意事项

- Pydantic v2 中校验器写法为 `@field_validator`，旧版 `@validator` 已废弃，注意版本差异。
- `Optional[str]` / `str | None` 表示「可为 None」，与「有默认值」是两回事；没有默认值且非 Optional 的字段**必填**。
- 校验失败时 FastAPI 自动返回 **422 Unprocessable Entity**，并在响应体里给出详细错误明细。
- `EmailStr` 需要额外安装 `email-validator` 包，否则启动会报错。
- 不要把敏感字段（如密码哈希）直接回显给客户端，应使用 `response_model` 过滤。

### 最佳实践

- 用 `Field()` 集中声明约束（`gt/ge/lt/le/min_length/max_length/pattern`），而不是在业务逻辑里手写判断。
- 校验逻辑复杂时用 `@field_validator` / `@model_validator` 封装，保持模型自洽。
- 请求模型与响应模型分离：请求用 `ItemCreate`，响应用 `ItemOut`（配 `response_model`），避免过度暴露字段。
- 大量可选字段用 `model_config = ConfigDict(extra="forbid")` 拒绝未声明字段，防止脏数据。

---

## 5. 依赖注入机制

### 概念说明

依赖注入（Dependency Injection，DI）是 FastAPI 的核心设计。通过 `Depends()`，FastAPI 会**自动解析函数的依赖参数**，按需调用依赖函数并传入结果。依赖可以：复用公共逻辑（鉴权、DB 会话、分页参数）、层层嵌套（依赖的依赖）、以及在请求后自动清理资源（yield 依赖）。

### 代码示例

```python
from typing import Annotated
from fastapi import FastAPI, Depends, Header, HTTPException

app = FastAPI()


# 1. 函数式依赖：可复用、可嵌套
def common_params(
    q: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    return {"q": q, "skip": skip, "limit": limit}


@app.get("/items/")
def read_items(commons: Annotated[dict, Depends(common_params)]):
    return commons


# 2. 鉴权依赖：从请求头读取 token
def verify_token(authorization: str | None = Header(default=None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    return authorization.removeprefix("Bearer ")


@app.get("/me")
def read_me(token: Annotated[str, Depends(verify_token)]):
    return {"token": token}


# 3. yield 依赖：数据库会话的「获取 → 使用 → 释放」
async def get_db():
    db = "模拟数据库连接"
    try:
        yield db                      # 请求处理期间使用这个值
    finally:
        print("关闭数据库连接")        # 请求结束后自动执行清理


@app.get("/data")
async def read_data(db: Annotated[str, Depends(get_db)]):
    return {"db": db}


# 4. 类式依赖：适合需要状态或较多方法的场景
class Pagination:
    def __init__(self, page: int = 1, size: int = 10):
        self.page = page
        self.size = size

    @property
    def offset(self):
        return (self.page - 1) * self.size


@app.get("/products")
def read_products(pg: Annotated[Pagination, Depends()]):
    # Depends() 不传参数时，自动以「类」作为依赖
    return {"page": pg.page, "offset": pg.offset}
```

### 注意事项

- `Depends()` 里的函数与路径操作函数**共享同一套参数解析规则**（路径参数、查询参数、Header 都能作为依赖的参数）。
- yield 依赖必须用 `async def` + `await` 或 `def` 中的 `finally` 保证清理逻辑执行；若依赖中有 `try/finally`，`finally` 在响应发出**之后**才运行。
- **同一个依赖默认只执行一次**：如果多个接口依赖同一个函数，FastAPI 默认缓存一次调用结果（`use_cache=True`）。若需每次独立执行，传 `Depends(fn, use_cache=False)`。
- 依赖可以层层嵌套：依赖 A 依赖 B，B 依赖 C，FastAPI 会自动构建解析链。

### 最佳实践

- 把「鉴权」「当前用户」「数据库会话」「分页」等横切逻辑全部抽成依赖，路由函数只写业务。
- 用 `Annotated[类型, Depends(...)]` 而不是 `Depends()` 作为默认值，方便类型推导与 IDE 提示。
- 数据库连接务必用 **yield 依赖**，让框架管理生命周期，避免手动 try/finally 散落各处。
- 安全相关的依赖（如 OAuth2）组合使用，形成「鉴权 → 取用户 → 取权限」的依赖链。

---

## 6. 中间件与异常处理

### 概念说明

- **中间件（Middleware）**：在请求进入路由处理函数**之前**、响应返回**之后**执行的「夹层」逻辑，可全局记录日志、统计耗时、注入 CORS 头、统一鉴权等。FastAPI 支持 `@app.middleware("http")` 装饰器（基于 Starlette）。
- **异常处理（Exception Handling）**：捕获路由或依赖抛出的异常，返回统一结构的错误响应。内置 `HTTPException` 是业务异常的推荐抛出方式，也可通过 `@app.exception_handler` 注册自定义异常或覆盖内置异常（如校验错误 `RequestValidationError`）。

### 代码示例

```python
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# 1. 自定义中间件：统计每个请求耗时
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)   # 交给后续处理
    process_time = time.perf_counter() - start
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 2. CORS 中间件（跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. 自定义业务异常
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id


@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"code": "ITEM_NOT_FOUND", "message": f"商品 {exc.item_id} 不存在"},
    )


# 4. 覆盖内置校验异常，统一错误格式
@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": "VALIDATION_ERROR", "errors": exc.errors()},
    )


# 5. 业务中抛 HTTPException
@app.get("/items/{item_id}")
def get_item(item_id: int):
    if item_id == 0:
        raise HTTPException(status_code=404, detail="商品不存在")
    if item_id < 0:
        raise ItemNotFoundError(item_id)
    return {"item_id": item_id}
```

### 注意事项

- 中间件的执行顺序：**后注册的先执行**（洋葱模型）。注册顺序会影响日志、鉴权等行为的先后，需要留意。
- `@app.middleware("http")` 是**全局**的，会影响所有请求，不要在中间件里做重量级阻塞操作。
- 自定义异常处理器只捕获**对应异常类型**；`HTTPException` 若想统一格式，需单独注册 `@app.exception_handler(HTTPException)`。
- 用 `JSONResponse` 构造响应时需手动设置状态码与内容，与普通路由自动序列化不同。
- 中间件里的 `call_next` 必须 `await`，且不能漏掉返回。

### 最佳实践

- 错误响应统一结构（如 `{"code", "message", "detail"}`），方便前端统一处理。
- 优先用 `HTTPException` 处理「已知的业务失败」，用自定义异常 + handler 处理「领域特定错误」。
- 耗时统计、请求日志、请求 ID 注入这类横切逻辑放中间件，而非复制到每个路由。
- CORS 配置尽量收紧 `allow_origins`，生产环境不要用 `"*"` 配合携带凭证的请求。

---

## 7. 异步支持与后台任务

### 概念说明

- **异步支持**：FastAPI 同时支持 `def`（同步，跑在线程池）和 `async def`（异步，跑在事件循环）两种路由。对于 I/O 密集型操作（数据库、HTTP 调用），用 `async def` + `await` 能提升并发吞吐。
- **后台任务（BackgroundTasks）**：在响应返回**之后**再执行的轻量任务（如发邮件、写日志），通过把 `BackgroundTasks` 注入到路由并调用 `add_task` 实现。

### 代码示例

```python
import asyncio
import time
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()


# 同步路由：FastAPI 会丢进线程池，不阻塞事件循环
@app.get("/sync")
def sync_endpoint():
    time.sleep(1)      # 模拟阻塞操作
    return {"mode": "sync"}


# 异步路由：真正的协程并发
@app.get("/async")
async def async_endpoint():
    await asyncio.sleep(1)   # 模拟非阻塞等待
    return {"mode": "async"}


# 后台任务：响应先返回，任务后执行
def send_email(email: str, message: str):
    # 这里是同步函数，在响应发出后由线程池执行
    print(f"发送邮件给 {email}: {message}")


@app.post("/register")
async def register(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, email, "欢迎注册")
    return {"message": "注册成功，邮件稍后发送"}


# 后台任务 + 异步任务
async def write_log(message: str):
    await asyncio.sleep(0.1)
    print(f"日志: {message}")


@app.post("/action")
async def action(background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, "用户执行了操作")
    return {"status": "done"}
```

### 注意事项

- **不要在 `async def` 路由里调用阻塞函数**（如同步的 `time.sleep`、阻塞的数据库驱动、`requests`），否则会卡住整个事件循环。阻塞操作要么用 `def` 路由（自动进线程池），要么换成异步库（如 `httpx`、`aiomysql`）。
- 后台任务适合**耗时短、结果无关紧要**的操作；重量级或需要重试/持久化的任务，应改用消息队列（如 Celery、RQ）。
- 后台任务在响应返回后执行，但若服务器进程异常退出，任务可能丢失，不保证可靠性。
- 若想「先执行后台任务再返回响应」，把 `await background_tasks()` 显式调用即可。

### 最佳实践

- I/O 密集 → `async def` + 异步库；CPU 密集 → `def`（线程池）或 `run_in_threadpool`。
- 异步路由里调用第三方 HTTP，统一用 `httpx.AsyncClient`；数据库用 SQLAlchemy async 版或异步 ORM。
- 发邮件、发通知、写审计日志这类「成功但无需立即完成」的事用 BackgroundTasks。
- 重要异步任务（定时、重试、海量）上消息队列，不要依赖后台任务。

---

## 8. 自动文档生成

### 概念说明

FastAPI 基于类型注解与 OpenAPI 规范，**零配置**自动生成交互式 API 文档：

- **Swagger UI**：`/docs`，可交互、可直接在页面上调试接口。
- **ReDoc**：`/redoc`，阅读体验更好，适合对外展示完整 API 说明。

文档内容来自：函数/参数的类型注解、`summary`/`description`、docstring、`tags`、Pydantic 模型的 `Field(description=...)` 等元数据。

### 代码示例

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="商品管理 API",
    description="用于演示 FastAPI 自动文档的示例服务",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI 路径
    redoc_url="/redoc",     # ReDoc 路径
    openapi_url="/openapi.json",  # 原始 OpenAPI schema
)

tags_metadata = [
    {"name": "items", "description": "商品相关接口"},
    {"name": "users", "description": "用户相关接口"},
]


class Item(BaseModel):
    name: str = Field(..., description="商品名称")
    price: float = Field(..., gt=0, description="价格（元）")


@app.get("/items/", tags=["items"], summary="获取商品列表", response_model=list[Item])
def list_items():
    """返回全部商品。

    - 可按分页参数过滤
    - 结果按价格降序排列
    """
    return [{"name": "键盘", "price": 199.0}]


@app.post("/items/", tags=["items"], response_model=Item, status_code=201)
def create_item(item: Item) -> Item:
    """创建新商品。"""
    return item
```

### 注意事项

- 文档的准确性**完全取决于类型注解和 docstring**：注解越精确，文档越可靠。用 `Any` 或 `dict` 会让文档失去意义。
- 生产环境通常要**关闭或隐藏**公开文档（如 `docs_url=None, redoc_url=None`），避免泄露接口结构。
- `response_model` 决定文档中响应结构，同时也会过滤掉响应里多余的字段，是「文档 + 安全」双保险。
- 修改 `docs_url`/`redoc_url`/`openapi_url` 为 `None` 可禁用对应文档。

### 最佳实践

- 每个模型字段都写 `Field(description=...)`，每个接口都写 `summary` + 简短 docstring。
- 用 `tags` 对接口分组，配合 `openapi_tags` 统一声明分组说明。
- 用 `response_model` 显式声明响应结构，而不是直接返回内部 ORM 对象。
- 需要自定义时，通过 `app.openapi()` 钩子或 `OpenAPI` 配置扩展，而不是手写文档。

---

## 9. 附录：常见陷阱速查

| 陷阱 | 原因 | 解决 |
| --- | --- | --- |
| 动态路由吞掉静态路由 | `/items/{item_id}` 会匹配 `/items/me` | 静态路径声明在前 |
| `async def` 里调 `time.sleep` | 阻塞事件循环，拖慢所有请求 | 换 `await asyncio.sleep` 或用 `def` 路由 |
| 布尔查询参数解析错误 | `?flag=False` 中字符串 `"False"` 会解析为 `True` | 传 `false`（小写）或 `0` |
| 依赖每次都想重新执行 | FastAPI 默认缓存依赖结果 | `Depends(fn, use_cache=False)` |
| 返回 Pydantic 模型却没校验响应 | 缺少 `response_model` | 显式声明 `response_model` |
| 用了 `EmailStr` 启动报错 | 未装 `email-validator` | `pip install email-validator` |
| 生产暴露 `/docs` | 泄露接口结构 | `docs_url=None` 或加鉴权 |
| 跨域失败 | 未配置 CORS 中间件 | `add_middleware(CORSMiddleware, ...)` |

---

## 学习路径建议

1. **第 1～3 章**：跑通最小应用，手写 GET/POST，体会类型注解如何「声明即校验」。
2. **第 4 章**：用 Pydantic 模型替换裸 `dict`，掌握校验器与嵌套模型。
3. **第 5～6 章**：把重复逻辑抽成依赖，加中间件记录日志、统一异常结构。
4. **第 7 章**：理解 `def` vs `async def`，用后台任务处理非关键操作。
5. **第 8 章**：补全元数据，让 `/docs` 成为团队可用的「活文档」。

> 练习建议：把上述示例整合成一个「商品 CRUD」小项目，从路由 → 校验 → 依赖 → 中间件 → 文档逐步完善，即可贯通 FastAPI 的核心开发流程。
