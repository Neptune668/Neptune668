# FastAPI 面试题整理（AI 应用开发岗位）

> 面向「AI 应用开发」岗位，覆盖：框架认知、核心特性、AI 应用特有考点（SSE 流式 / 异步调用 LLM / 长任务）、性能与并发、部署工程、实操场景，以及进阶补充（路由组织 / 参数校验 / 响应模型 / 限流 / 幂等 / 超时取消 / GIL / ORM 集成）。
> 每题给出【应答思路】和【推荐话术要点】，★ 表示高频追问。技术栈以你 RAG 项目（FastAPI + LangGraph + Milvus + MinIO + MongoDB）为背景举例。

---

## 一、框架认知与基础

### 1. FastAPI 是什么？为什么性能这么高？★
**应答思路**：一句话定位 → 三个层次拆「快」的原因。
**话术**：FastAPI 是现代 Python Web 框架，基于 Starlette（Web/ASGI 层）和 Pydantic（数据校验层）。快在三个层次：① 底层 ASGI 异步非阻塞 I/O，配合 Uvicorn 跑事件循环；② 数据校验用 Pydantic（核心是 Rust 编译的），比纯 Python 快一个量级；③ 类型提示在编译期就确定了字段类型，省去运行时反射开销。性能对标 Node.js / Go 这一档，远快于同步的 Flask/Django。

### 2. 什么是 ASGI？和 WSGI 有什么区别？★
**应答思路**：WSGI 同步、一个请求一个线程；ASGI 异步、支持长连接。
**话术**：WSGI 是同步协议，一个请求占一个线程，并发靠线程数堆，适合短连接；ASGI 是异步协议，事件循环驱动，单线程就能扛大量并发 I/O，而且原生支持 WebSocket、SSE、HTTP/2 这些长连接和流式场景。FastAPI 是 ASGI 框架，用 Uvicorn 跑。

### 3. 为什么 AI 应用开发选 FastAPI？和 Flask/Django 比？★
**应答思路**：AI 应用的特点是「IO 密集 + 长连接 + 流式」，正好命中 FastAPI 优势。
**话术**：AI 应用有几个特点——大量调用 LLM/向量库/外部 MCP，都是网络 IO，不是 CPU 计算；要流式输出；要和前端保持长连接。FastAPI 异步 IO 密集场景吞吐高，`StreamingResponse` 天然支持 SSE 流式，自动生成 OpenAPI 文档方便前端联调，依赖注入方便组织「鉴权 / DB 会话 / 模型客户端」这些复用逻辑。Flask 同步为主、流式和并发弱；Django 重、全家桶对纯 API 服务是负担。所以做 AI 后端我默认选 FastAPI。

---

## 二、核心特性

### 4. 依赖注入（Dependency Injection）是什么？在 AI 应用里怎么用？★
**应答思路**：`Depends()` 复用逻辑 → 结合 AI 应用举三个例子。
**话术**：依赖注入就是用 `Depends()` 把可复用逻辑抽成函数或类，由框架自动注入。AI 应用里我用在三个地方：① 鉴权守卫（从 token 解析用户，失败直接 401）；② 数据库会话（`yield` 形式，请求结束自动关连接）；③ LLM/向量库客户端（模型 client、Milvus 连接复用，避免每次请求重建）。还支持嵌套依赖和缓存，登录用户信息在请求内只解析一次。

### 5. Pydantic 在 FastAPI 里起什么作用？★
**应答思路**：校验 + 序列化 + 自动文档，三个作用。
**话术**：三层作用：① 请求体验证——不符合 `BaseModel` 定义的字段直接 422，还带结构化错误信息；② 响应序列化——`response_model` 自动过滤多余字段、保证输出结构稳定；③ 自动生成 JSON Schema——接口文档和前端类型都能从模型推导。约束用 `Field`，比如 `min_length`、`ge`、`pattern`，配合 `Optional`/默认值。

### 6. 路径参数、查询参数、请求体怎么区分？
**话术**：路径参数写在 URL 路径里，`@app.get("/items/{item_id}")`；查询参数是函数签名里除 Pydantic 模型外的普通参数，出现在 `?key=value`；请求体是签名里的 Pydantic 模型参数，走 POST/PUT 的 body。FastAPI 按「类型 + 是否模型」自动判断来源。

### 7. 中间件和异常处理器分别怎么用？★
**话术**：中间件用 `@app.middleware("http")`，在请求进入和响应返回时各执行一段，适合做日志、请求计时、统一加响应头、CORS；异常处理器用 `@app.exception_handler`，捕获特定异常返回统一错误结构，AI 应用里我会把「模型调用超时、向量库连接失败、外部 MCP 报错」转成统一 JSON 错误码，不让裸异常抛给前端。

### 8. 后台任务（BackgroundTasks）是什么？有什么局限？
**话术**：`BackgroundTasks` 在响应返回**之后**执行附加逻辑，适合发通知、写日志这类「不阻塞主响应」的轻量操作。局限是它跑在同一进程的线程池里，不是真正的消息队列——进程重启任务就丢，也不适合重活。AI 应用里真正耗时的导入、批量向量化我会用独立任务队列，不会用 `BackgroundTasks` 硬扛。

### 9. 生命周期事件（Lifespan）怎么用？
**话术**：用 `lifespan` 上下文管理器处理启动/关闭逻辑——启动时初始化模型 client、Milvus 连接池、加载配置；关闭时释放连接。新版推荐 `lifespan` 取代旧的 `@app.on_event("startup"/"shutdown")`，因为它是单入口、更清晰，也方便测试。

---

## 三、AI 应用特有考点（重点）

### 10. SSE 流式输出怎么实现？为什么用 SSE 不用 WebSocket？★
**应答思路**：结合 RAG 项目实际链路讲，再对比 WebSocket。
**话术**：RAG 项目里我是「task_id + 队列」模式——前端先 POST 建任务拿到 task_id，后端用 LangGraph 后台跑查询图，LLM stream 每吐一段就往队列塞一个 delta 事件，前端通过 `/stream/{task_id}` 的 `StreamingResponse`（`media_type="text/event-stream"`）持续接收，结束推 final 事件。选 SSE 不选 WebSocket 的原因：问答是单向流，SSE 基于 HTTP、实现简单、天然支持自动重连，和 FastAPI 的 `StreamingResponse` 契合；WebSocket 是双向长连接，这里用不上还更复杂。文件导入这种「提交后轮询」的场景用 `/status/{task_id}` 轮询即可。

### 11. 异步接口里能不能直接调同步的 LLM/DB 库？会怎样？★
**应答思路**：核心考点——阻塞事件循环，回答要给出三种解法。
**话术**：不能直接调。事件循环是单线程的，一旦在 async 函数里执行同步阻塞操作（比如用 `requests` 调 LLM、用同步数据库驱动），会卡住整个事件循环，所有并发请求一起被堵死。三种解法：① 换成异步驱动（`httpx.AsyncClient` 调 LLM、`asyncpg` 连库）；② 用 `run_in_threadpool` 把同步函数丢线程池跑，不占事件循环；③ 把整个接口函数写成同步 `def`，FastAPI 会自动把它丢进线程池执行。

### 12. `async def` 和同步 `def` 接口，FastAPI 内部怎么调度？★
**话术**：`async def` 的接口在事件循环里跑，适合 IO 密集、逻辑本身是异步的；同步 `def` 的接口会被 FastAPI 丢进线程池（`anyio` 的线程池）执行，适合 CPU 密集或有同步依赖的场景。误区是「一律 async 就快」——如果 async 函数内部是纯 CPU 计算或调了同步库，反而阻塞事件循环、更慢。原则：异步函数里必须全程非阻塞。

### 13. 长任务（文档导入、批量向量化）怎么处理？
**应答思路**：同步请求会超时，必须异步化，给「提交 + 轮询/回调」方案。
**话术**：导入、批量 embedding 这种动辄几十秒的任务，不能在 HTTP 请求里同步做完。方案是「异步任务 + 状态查询」：POST 提交立即返回 task_id，后台 worker 跑任务，用 MongoDB/Redis 记录状态（pending/running/success/failed），前端轮询 `/status/{task_id}` 拿进度。任务多了上消息队列（Celery/自研 MQ）削峰，`BackgroundTasks` 只适合秒级的轻任务。

### 14. WebSocket 在 AI 应用里什么时候用？
**话术**：需要服务端主动推送、双向通信时用，比如实时对话机器人、进度条实时刷新、多端协同。`@app.websocket` 是 ASGI 原生支持的。但如果只是「服务端把 LLM 结果一段段吐给前端」这种单向流，SSE 就够了，别为用而用。

### 15. FastAPI 怎么和 LangChain / LangGraph 集成？
**应答思路**：FastAPI 当「接入层」，编排交给 LangGraph，接口只做协议转换。
**话术**：分工是 FastAPI 负责 HTTP 接入、鉴权、参数校验、SSE 推送，LangGraph 负责业务编排（图节点、状态机、多 Agent）。接口函数里拿到参数后，用 `graph.astream()` 异步跑图，把每一步的 state 变化转成 SSE 事件推给前端。注意 LangGraph 的 `astream` 是异步生成器，正好配 FastAPI 的 `StreamingResponse`，不要用同步 `invoke` 阻塞接口。

---

## 四、性能与并发

### 16. AI 应用的性能瓶颈一般在哪？怎么优化？
**应答思路**：瓶颈几乎都在 LLM/IO，不是 FastAPI 本身，按链路讲。
**话术**：AI 应用的瓶颈九成不在 Web 框架，而在 LLM 调用和下游 IO。优化按链路来：① LLM 调用——缓存 + FAQ 命中直接返回，减调用次数；小模型路由，简单问题走小模型；② 并发——用 `httpx.AsyncClient` 保持连接复用，多路召回并行发；③ 流式——首字延迟（TTFT）比总时长更影响体验，用 SSE 边生成边推；④ 连接池——向量库、数据库、模型 client 都要池化，别每次请求新建连接。

### 17. 连接池怎么管理？为什么重要？
**话术**：LLM client、Milvus、MongoDB 这些连接建一次很贵（TCP 握手、鉴权），如果每次请求都重建，高并发下会耗尽连接、打满时延。做法是全局单例 + 连接池，FastAPI 里在 lifespan 启动时初始化好，通过依赖注入复用。`httpx.AsyncClient` 用 `AsyncClient` 实例复用（别用 `async with` 每次建）。

### 18. 压测关注哪些指标？★
**应答思路**：AI 应用重点不是纯 QPS，而是 TTFT/TPOT 等流式指标。
**话术**：除了常规 QPS、P99 时延，AI 流式应用重点看三个：TTFT（首字延迟，影响「快不快」的体感）、TPOT（每 token 生成间隔，影响「卡不卡」）、以及 GPU/模型服务的利用率。我项目里压过 16/32/64 并发，QPS 从 14.8 到 38.9，TTFT P50 在 300-700ms，瓶颈会随并发升高从 CPU 转到 GPU。

---

## 五、部署与工程

### 19. 生产环境怎么部署 FastAPI？★
**应答思路**：Uvicorn 跑单实例 + 多 worker/多进程，前面 Nginx 反向代理。
**话术**：单机用 Uvicorn（`uvicorn main:app --workers N` 多进程）或 Gunicorn + Uvicorn worker 管理多进程，前面挂 Nginx 做反向代理、负载均衡、静态资源和 TLS。我的 RAG 项目是 CPU 应用机（Docker Compose 跑 FastAPI）和 GPU 推理机（vLLM 跑 Embedding/Reranker）拆分部署，API 编排和模型推理互不抢资源。要不要上 K8s 看流量，早期 Compose 更易交付排查。

### 20. 多 worker 部署有什么要注意的？
**应答思路**：多进程下内存状态不共享，全局变量会不一致。
**话术**：多 worker 是多进程，进程间内存不共享——所以不能在内存里存「全局计数器、会话状态、简单缓存」，否则每个进程一份、数据不一致。要共享就用 Redis/DB 这类外部存储。我项目里 task 状态就存 MongoDB 而不是内存字典，正是为了多副本都能读到。另外 SSE 长连接 + 多 worker 时要注意 Nginx 的超时和 buffer 配置。

### 21. CORS 怎么配？
**话术**：加 `CORSMiddleware`，配 `allow_origins`（跨域域名白名单）、`allow_methods`、`allow_headers`。前后端分离、前端不同域名时必配，否则浏览器直接拦截。

### 22. 安全和认证怎么做？
**应答思路**：AI 应用常见三层，按需选。
**话术**：AI 应用常见三种：① API Key——对内服务/工具调用，`Header` 里带 key 校验，最简单；② JWT——对外用户系统，OAuth2 密码流发 token，`HTTPBearer` + 依赖注入做鉴权守卫；③ 外部 OAuth2（微信/企业微信登录）。FastAPI 自带 `OAuth2PasswordBearer`，JWT 用 `python-jose` 或 `PyJWT`。关键是把鉴权做成依赖注入，每个受保护接口 `Depends(get_current_user)` 即可。

### 23. 可观测性怎么做？
**话术**：三层——日志（结构化日志，带 request_id 串联一次请求）、指标（QPS、P99、错误率，接 Prometheus/Grafana）、链路追踪（AI 应用用 LangSmith/Langfuse 或自研 trace，记录 Query、召回 chunk、rerank 分、prompt、输出、各节点耗时）。我项目里每个 RAG 节点都有耗时日志，响应变慢能直接定位到是 LLM 节点还是 MCP 网络检索节点。

---

## 六、实操场景题

### 24. 给你设计一个「RAG 问答 + 文档管理」的后端接口，怎么设计？
**应答思路**：按「导入 / 查询 / 状态」三类接口讲，突出 task_id 异步化。
**话术**：分三组：① 导入——`POST /import`（上传文件，返回 task_id）→ `GET /import/{task_id}/status`（轮询状态）；② 查询——`POST /query`（建会话返回 task_id + session_id）→ `GET /stream/{task_id}`（SSE 流式返回答案，含引用的图片/chunk）；③ 文档管理——`GET /docs`、`DELETE /docs/{id}`。设计原则：耗时操作一律异步化返回 task_id，查询走 SSE 而不是一次性 JSON，状态用 session 持久化支持多轮。

### 25. 接口怎么测试？
**应答思路**：TestClient + pytest，关键业务逻辑 mock 掉 LLM。
**话术**：用 FastAPI 自带的 `TestClient`（基于 httpx）+ pytest 写测试。测三层：① 参数校验——错误类型/字段是否返回 422；② 依赖注入——鉴权失败返回 401；③ 业务逻辑——重点把 LLM 调用 mock 掉，用固定返回值测编排逻辑，避免测试依赖真实模型（慢且不稳定）。异步接口用 `pytest-asyncio` 或 `httpx.AsyncClient` 测。

---

## 七、进阶补充考点

### 26. APIRouter 是什么？项目怎么按模块拆分路由？★
**应答思路**：工程化必问——单文件会失控，用 Router 模块化。
**话术**：`APIRouter` 把路由按业务模块拆分，每个模块一个 `router`，最后在主应用里 `app.include_router()` 挂载，还能统一加前缀和 tags。我的 RAG 项目就拆成 `import_router`（文档导入）、`query_router`（问答查询）、`docs_router`（文档管理），各自独立、互不影响。拆分的好处是职责清晰、多人协作不冲突、依赖注入和中间件可以按模块局部生效。

### 27. response_model 的作用？和直接返回 dict 有什么区别？
**应答思路**：过滤 + 校验 + 文档，三个价值。
**话术**：`response_model` 让 FastAPI 在返回前把数据**过滤和序列化**成指定结构——多余字段被剔除、类型被强校验、还能隐藏敏感字段（比如不返回用户密码哈希）。不写 `response_model` 直接返回 dict 的话，就是原样透传，结构不受控、也不会出现在文档的响应 schema 里。AI 应用里我要求所有接口都声明 `response_model`，保证前后端契约稳定。

### 28. Query / Path / Header 参数校验怎么做？★
**话术**：路径参数用 `Path(...)`、查询参数用 `Query(...)`、请求头用 `Header(...)`，都能加约束：必填、默认值、`min_length`、`max_length`、`ge/le`、正则 `pattern`、枚举。比如 `@app.get("/search")` 里 `q: str = Query(..., min_length=1, max_length=200)`，`limit: int = Query(10, ge=1, le=100)`。校验失败自动返回 422，比在函数体里手动 `if` 判断干净得多。

### 29. 文件上传和下载怎么处理？
**应答思路**：上传用 `UploadFile`（流式），下载用 `FileResponse`/`StreamingResponse`，注意大文件别读进内存。
**话术**：上传用 `UploadFile` 参数，它是 `SpooledTemporaryFile`，小文件在内存、大文件落盘，配合 `await file.read()` 分块写，适合大文件。下载用 `FileResponse`（本地文件）或 `StreamingResponse`（动态生成/流式）。AI 项目里文档导入接口就是 `UploadFile` 接收文件 → 存本地 + 归档 MinIO → 返回 task_id 异步处理，不会在请求里同步解析大文件。

### 30. LLM 调用超时、请求取消怎么处理？★
**应答思路**：AI 应用关键考点——超时要控制、用户断开要能取消上游，别浪费 token。
**话术**：两层控制：① 超时——用 `httpx.AsyncClient(timeout=...)` 给 LLM 调用设超时（连接超时 + 读取超时分开设），超时走重试或降级小模型；② 取消——SSE 场景用户中途断开，用 `await request.is_disconnected()` 检测，前端断了就主动取消正在跑的 LLM 流，避免白烧 token。这在「流式生成一半用户关页面」的场景特别重要，不做的话每次都会有一堆半截请求浪费算力。

### 31. 接口限流怎么实现？为什么 AI 应用尤其重要？★
**应答思路**：AI 应用限流是「成本 + 稳定性」双需求。
**话术**：AI 应用限流特别重要，因为 LLM 按 token 计费，而且模型服务本身有并发上限，不限流会被少数用户打爆。实现三层：① 用 `slowapi`（基于 `limits` 库）配 `@limiter.limit("5/minute")` 装饰器，最简单的速率限制；② 分布式用 Redis 计数器（固定窗口/滑动窗口/令牌桶）；③ 网关层限流（Nginx/Kong）。我项目里除了接口限流，模型调用侧还单独设了并发和每分钟 token 上限，配合 MQ 排队。

### 32. 数据库 ORM 怎么集成？SQLModel 是什么？
**应答思路**：SQLAlchemy 是主流，SQLModel 是 FastAPI 作者出的融合方案。
**话术**：最主流是 SQLAlchemy，用 `Session`/异步 `AsyncSession` + 依赖注入管理会话生命周期（`yield` 形式，请求结束自动关闭）。SQLModel 是 FastAPI 作者把 Pydantic + SQLAlchemy 合二为一的方案——一个模型类既是数据库表定义又是请求/响应校验模型，少写一套 schema，适合中小项目。我项目里向量库用 Milvus、会话和任务状态存 MongoDB（文档型更适合多变结构），文本类元数据存 MySQL/SQLModel 即可。

### 33. GIL 对 FastAPI 并发有影响吗？★
**应答思路**：区分「IO 密集」和「CPU 密集」，这是高频陷阱题。
**话术**：GIL 让同一进程内多线程不能并行执行 Python 字节码，但对 FastAPI 的影响要看负载类型。AI 应用主要是 IO 密集（调 LLM、向量库、DB），异步时大部分时间在等网络返回，GIL 会释放，影响很小。真正受影响的是 CPU 密集任务——比如纯 Python 的向量计算、数据预处理，这类会卡住事件循环或被 GIL 限制，解法是丢线程池/多进程，或者把重活交给 C 扩展库（Pydantic、numpy）和 GPU（vLLM 部署的模型服务）。

### 34. 幂等性怎么设计？★
**应答思路**：AI 应用「创建任务 / 扣费」必须幂等，防重复执行。
**话术**：写操作要幂等，核心是「幂等键」——客户端每次提交带一个唯一 ID（如 `Idempotency-Key` 请求头或业务单号），服务端用 Redis/DB 记录「key → 结果」，重复请求直接返回已有结果，不重复执行。AI 应用典型场景：用户重复点「生成」按钮不能重复创建任务、重复扣 token 费；写操作超时了，先查「到底成没成功」再决定重试，避免重复执行。

### 35. 环境配置与敏感信息怎么管理？
**应答思路**：pydantic-settings 加载，环境变量区分环境，密钥不落代码库。
**话术**：用 `pydantic-settings`（FastAPI 生态标配）定义配置类，从环境变量 / `.env` 文件加载，字段带类型校验。API Key、数据库密码、模型 token 这些敏感信息只走环境变量或密钥管理服务（KMS/Vault），绝不写进代码或提交到 Git。本地 `.env`、测试、生产用不同的配置实例，`BaseSettings` 还支持字段校验，配错启动就报错，避免「配置缺失到运行时才炸」。

### 36. 接口版本控制怎么做？
**话术**：常见三种：① URL 前缀 `/api/v1`、`/api/v2`，最直观，用 APIRouter 加 prefix 轻松实现；② 请求头版本号 `Accept-Version`；③ 查询参数 `?version=1`。推荐 URL 前缀，清晰且利于网关路由和缓存。AI 应用里模型能力会升级、prompt 会变，接口契约最好一开始就定版本，避免前端联调乱套。

### 37. Docker 部署 FastAPI 有哪些要点？
**应答思路**：分层缓存 + 健康检查 + 单进程跑 Uvicorn，别用 `--reload`。
**话术**：几个要点：① Dockerfile 用多阶段构建、先把 `requirements.txt` 单独 COPY 再 `pip install`，充分利用层缓存；② 容器里以单进程跑 Uvicorn（`uvicorn main:app --host 0.0.0.0 --port 8000`），多副本靠编排层扩展，不要 `--reload` 和 `--workers`（那是在容器里再分进程，违反容器单进程约定）；③ 加健康检查端点 `/health`，配合 `docker compose` 的 healthcheck 做自愈；④ 非 root 用户运行、镜像用 `python:3.x-slim` 减小体积。我的项目就是 CPU 应用机（FastAPI 容器）+ GPU 推理机（vLLM 容器）拆开跑，用 Compose 编排。

---

## 附：回答节奏建议
- **框架题**：先一句结论（定位/区别），再展开 2-3 点，主动补一句「代价」或「什么时候不用」，显得有判断力。
- **异步题**：务必点出「阻塞事件循环」这个核心，再给三种解法（异步驱动 / 线程池 / 同步 def），这是 AI 岗最常考的坑。
- **AI 场景题**：往你的 RAG 项目上靠——SSE 流式、task_id 轮询、LangGraph 编排、CPU/GPU 拆分部署，这些是你项目里真实存在的，说出来最有说服力。
- **数字记忆点**（来自你的项目）：QPS 14.8/25.6/38.9（16/32/64 并发）、TTFT P50 310ms、GPU 利用率 61%→91%。
- **遇到不会的**：坦诚 + 给排查思路（先定位节点 → 看指标 → 小步验证），比硬编更得分。
- **进阶题记忆点**：限流「成本 + 稳定性」双需求；幂等靠「幂等键 + 超时先查成没成功」；GIL 只影响 CPU 密集、IO 密集影响小；取消用 `request.is_disconnected()` 别白烧 token；Docker 里单进程跑 Uvicorn、不要 `--reload`/`--workers`。
