# 一、项目概述与整体架构

## 第1章 项目概述 

### 1.1 为什么要做这套系统

电商客服每天都在处理大量重复又零散的对话：

- "帮我查下订单状态" "我那个快递到哪了"
- "这件衣服什么材质" "支持退货吗"
- "你好" "我要退款" "算了不退了"

如果靠人工坐席，要养一个大团队；如果用传统关键词机器人，遇到稍微复杂的问法就答非所问。

在大模型逐渐成熟之后，"用 LLM 理解用户意图 + 用代码执行具体动作" 成为了一种新的工程范式。本课程要做的就是这样一套系统：

> **如何用工程化的方式驯服 LLM 的不确定性，保证业务结果稳定可控？**

### 1.2 功能概览

这是一套面向电商场景的智能客服系统，主要支持三大类能力：

| 能力类型 | 说明                   | 典型场景                                 |
| -------- | ---------------------- | ---------------------------------------- |
| 任务流程 | 处理步骤明确的业务任务 | 订单状态查询、物流查询、申请退款         |
| 信息检索 | 处理查询型问题         | 询问退款政策、询问退货政策、商品信息查询 |
| 闲聊     | 处理轻量自然对话       | 打招呼、简单寒暄、模糊输入兜底           |

#### 1.2.1 固定任务流程（Task）

##### 固定任务流程介绍

固定任务流程，指的是那些步骤比较稳定、处理顺序比较明确、适合按步骤推进的客服任务。这类任务通常不是用户一句话就能直接完成，而是需要系统逐步收集信息、执行动作，并返回处理结果。

在当前项目中，比较典型的固定任务流程包括：

| 流程名称     | 触发场景           | 大致步骤                             |
| ------------ | ------------------ | ------------------------------------ |
| 订单状态查询 | "帮我查下订单状态" | 收集订单号 → 调用订单接口 → 回复结果 |
| 物流查询     | "我的快递到哪了"   | 收集订单号 → 调用物流接口 → 回复结果 |
| 退款申请     | "我要退款"         | 收集订单号 → 收集退款原因 → 提交申请 |

下面以“退款申请”流程为例进行说明：

##### 退款申请交互示例

```text
用户：我要申请退款
客服：请告诉我你的订单号。
用户：A20240315001
客服：请简单说一下退款原因。
用户：尺码不合适
客服：好的，订单 A20240315001 的退款申请已提交，原因是：尺码不合适。
```

##### 退款申请流程图

```mermaid
flowchart TD
    A(["start<br/>开始退款流程"]) --> B["collect: order_number<br/>请告诉我你的订单号"]
    B --> C["collect: refund_reason<br/>请简单说一下退款原因"]
    C --> D["action: action_response<br/>生成退款申请确认回复"]
    D --> E(["end<br/>流程结束"])
```

##### YAML流程描述

本项目支持通过 YAML 文件自定义业务流程，下面是退款申请的流程定义：

```yaml
refund_request:
  name: 退款申请
  description: 帮用户提交简单的退款申请，收集订单号和退款原因。
  steps:
    - id: start
      type: start
      next: ask_order_number

    - id: ask_order_number
      type: collect
      slot_name: order_number
      response:
        text: "请告诉我你的订单号。"
      next: ask_refund_reason

    - id: ask_refund_reason
      type: collect
      slot_name: refund_reason
      response:
        text: "请简单说一下退款原因。"
      next: refund_submitted

    - id: refund_submitted
      type: action
      action: action_response
      args:
        text: "好的，订单{{ slots.order_number }}的退款申请已提交，原因是：{{ slots.refund_reason }}。后续会尽快为你处理。"
      next: end

    - id: end
      type: end
      next: []
```

- 从这个配置可以看出，一个业务流程是由多个步骤组成的。在当前示例中，主要涉及以下几种步骤类型：

  - `start`：流程起点
  - `collect`：收集某个槽位信息，例如订单号、退款原因
  - `action`：执行动作并生成回复
  - `end`：流程结束

**这种写法的关键在于**：业务的步骤、提示语都不写在代码里，而是写在 YAML 里。增加一个新流程不需要改代码，只需要加一份 YAML。

#### 1.2.2 信息检索（Knowledge）

##### 信息检索介绍

除了固定任务流程之外，电商客服中还有大量问题并不要求系统“执行一个流程”，而是希望系统先查到相关信息，再用自然语言组织成回答返回给用户。这类问题就属于信息检索场景。

在当前项目中，信息检索相关的问题主要涵盖以下几个方面：

| 知识意图     | 示例问题                   |
| ------------ | -------------------------- |
| 商品信息咨询 | “这件商品是什么材质？”     |
| 订单信息咨询 | “这个订单现在是什么情况？” |
| 退款政策咨询 | “退款政策是怎样的？”       |
| 退货政策咨询 | “支持退货吗？”             |
| 配送政策咨询 | “多久发货？包邮吗？”       |
| 平台规则咨询 | “平台有哪些限制规则？”     |
| 通用电商问题 | “优惠券怎么用？”           |

不同类型的问题，其检索方式并不完全相同。

- 商品信息、订单信息这类问题，通常需要调用业务 API 获取实时数据
- 退款政策、退货政策、配送政策这类问题，更适合通过 FAQ（Frequently Asked Questions，常见问题）进行回答
- 平台规则、通用电商问题这类内容，更适合通过知识库进行回答（RAG）

也就是说，信息检索链路的核心思路不是“直接让模型自由回答”，而是先找到可信的信息来源，再让模型基于这些信息生成更自然的回复。

##### 信息检索交互示例

```text
用户：这件商品大概是什么情况？
客服：这件商品的名称是“轻薄连帽防晒衣”，当前价格为 129 元，库存状态为有货。
      如果你想进一步了解规格参数或售后信息，也可以继续问我。

用户：适合什么季节穿？
客服：从商品名称和描述来看，这是一件偏轻薄款的防晒衣，更适合春夏季节或日常通勤、户外防晒场景使用。

用户：那现在有货吗？
客服：当前库存状态为有货。如果你需要，我也可以继续帮你看看这件商品的更多信息。
```

#### 1.2.3 闲聊（Chitchat）

##### 闲聊介绍

当用户输入的内容不属于明确任务，也不适合走知识检索时，系统会进入闲聊轨道。

闲聊能力的作用主要是：

- 让系统对话体验更自然
- 在轻量输入场景下给出合理回应
- 在系统暂时无法进入明确业务流程时提供兜底体验

##### 闲聊交互示例

```text
用户：你好
客服：你好，这里是 Atguigu 电商助手。我可以帮你查订单状态、查物流、了解商品信息，或者提交退款申请。

用户：你还挺聪明
客服：谢谢夸奖。如果你有订单、物流或者商品相关的问题，我都可以继续帮你看一下。
```

### 1.3 三条轨道的关系

三条轨道是互斥的，判断走哪一条的工作交给 LLM。

```mermaid
flowchart LR
    A["用户输入"] --> B["LLM 推断意图"]
    B --> C{"哪条轨道?"}
    
    C --明确任务--> D["Task 轨道<br/>按 YAML 流程推进"]
    C --信息咨询--> E["Knowledge 轨道<br/>检索 + LLM 整理"]
    C --其他--> F["Chitchat 轨道<br/>LLM 自由回复"]

    %% 配色匹配原图风格
    classDef userBox fill:#e6f0ff,stroke:#4080ff,stroke-width:2px
    classDef llmBox fill:#f0eaff,stroke:#8060ff,stroke-width:2px
    classDef judgeDia fill:#ffffff,stroke:#333,stroke-width:2px
    classDef taskBox fill:#e6f2ff,stroke:#1677ff,stroke-width:2px
    classDef knowBox fill:#e6fff9,stroke:#00b894,stroke-width:2px
    classDef chatBox fill:#f9eaff,stroke:#9254de,stroke-width:2px

    class A userBox
    class B llmBox
    class C judgeDia
    class D taskBox
    class E knowBox
    class F chatBox
```



## 第2章 项目开发环境

### 2.1 整体环境说明

项目所需环境如下：

- `customer-service-backend`：AI 客服后端服务，承担所有对话与 LLM 调用（课程核心，需要我们开发）
- `customer-service-frontend`：客服前端页面
- `ecommerce-service-backend`：电商业务后端，提供订单、物流、商品的查询接口(业务中台)
- `mysql`：数据库容器、脚本

### 2.2 环境启动说明

建议按下面顺序启动环境：

#### 第一步：数据库

##### windows mysql

直接还原如下数据库脚本即可

```
001_init_customer_service.sql
002_init_commerce.sql
```

#### 第二步：启动模拟电商后端

修改配置文件：

复制 `ecommerce-service-backend`目录下的`.env.example` 到 `.env`，并按实际情况修改数据库配置

启动服务：

```bash
cd ecommerce-service-backend
uv sync
uv run python main.py
```

#### 第三步：启动前端

安装Node.js：node-v24.15.0-x64.msi

官方下载：https://nodejs.org/en/download

配置镜像源

```bash
# ✅ 推荐国内：npmmirror（新淘宝镜像）
npm config set registry https://registry.npmmirror.com
```

安装依赖并运行项目

```bash
cd customer-service-frontend
npm install
npm run dev
```

启动后访问 [http://127.0.0.1:5173](http://127.0.0.1:5173) 即可看到页面。

### 2.3 客服后端 customer-service-backend

这是本项目的核心，也是后续重点学习的部分。

它主要负责：

- 接收用户消息
- 读取和保存对话状态
- 判断当前应进入任务流、知识检索还是闲聊
- 调用大模型完成规划和回复生成
- 调用电商服务获取业务数据
- 生成自然语言回复

主要技术栈：

- FastAPI：提供 HTTP 接口
- LangChain：封装模型调用
- SQLAlchemy：进行数据库访问
- Pydantic：配置和数据结构定义
- Jinja2：Prompt 模板渲染
- PyYAML：流程配置文件加载

### 2.4 客服前端 customer-service-frontend

前端页面是一个教学用的可视化控制台，目的是让你更方便地观察客服系统的行为。

当前页面主要包括两个区域：

- 左侧聊天区：发送文本消息、查看回复、查看历史记录
- 右侧对象区：显示当前用户的订单和商品，并支持发送对象消息

### 2.5 模拟电商后端 ecommerce-service-backend

模拟电商后端的作用，为客服系统提供可查询的业务数据，扮演真实企业里"被 AI 系统消费的业务中台"。

它当前提供的典型接口包括：

| 接口                                          | 作用                   |
| --------------------------------------------- | ---------------------- |
| `GET /users/{user_id}/orders`                 | 获取某用户最近订单列表 |
| `GET /users/{user_id}/products`               | 获取某用户最近商品列表 |
| `GET /orders/{order_id}`                      | 获取订单详情           |
| `GET /orders/{order_id}/status`               | 获取订单状态           |
| `GET /orders/{order_id}/logistics`            | 获取物流信息           |
| `GET /products/{product_id}`                  | 获取商品详情           |
| `POST /orders/{order_id}/shipping-reminders`  | 创建催发货提醒         |
| `POST /orders/{order_id}/refund-applications` | 创建退款申请           |

### 2.6 各组件关系图

下面这张图展示了各组件之间的协作关系：

```mermaid
flowchart TD
    FE["customer-service-frontend<br/>客服前端页面"]
    CS["customer-service-backend<br/>客服后端"]
    EC["ecommerce-service-backend<br/>模拟电商后端"]
    DB["MySQL<br/>数据库"]
    LLM["LLM API<br/>大语言模型接口"]

    FE -->|"聊天请求 / 历史消息"| CS
    CS -->|"订单 / 物流 / 商品查询"| EC
    FE -->|"订单列表 / 商品列表"| EC
    CS -->|"对话状态读写"| DB
    EC -->|"业务数据读写"| DB
    CS -->|"模型调用"| LLM
```

## 第3章 项目架构

### 3.1 总体设计思路

核心设计思路如下图所示：

```mermaid
flowchart TD
    API["API 层<br/>接收消息 / 返回结果"]
    SERVICE["Service 层<br/>组织一次完整处理"]
    ENGINE["Engine 层<br/>DialogueEngine 核心调度"]
    PLAN["Planning 层<br/>本轮规划与校验"]
    ROUTE{"进入哪条轨道?"}
    TASK["Task 轨道<br/>固定任务流"]
    KNOW["Knowledge 轨道<br/>信息检索"]
    CHAT["Chitchat 轨道<br/>闲聊兜底"]
    REPO["Repository 层<br/>状态读取与保存"]
    INFRA["基础设施<br/>LLM / DB / 电商 API"]

    API --> SERVICE
    SERVICE --> ENGINE
    SERVICE --> REPO
    ENGINE --> PLAN
    PLAN --> ROUTE
    ROUTE --> TASK
    ROUTE --> KNOW
    ROUTE --> CHAT
    TASK --> INFRA
    KNOW --> INFRA
    CHAT --> INFRA
    REPO --> INFRA
```

### 3.2 一条消息的完整处理流程

下面这张图展示了一条用户消息从进入系统到生成回复的大致流程：

```mermaid
flowchart TD
    U(["用户发送消息"]) --> API["API 路由层"]
    API --> SVC["DialogueService<br/>加载DialogueState -> 调用引擎"]
    SVC --> PREP["准备会话与当前 turn"]
    PREP --> TYPE{"消息类型?"}

    TYPE -->|TEXT| PLAN["TurnPlanner 进行本轮规划"]
    PLAN --> CONFIRM{"确认吗?"}
    CONFIRM --> |是| ROUTE{"进入哪条轨道?"}
    CONFIRM --> |否| CLARIFY["反问澄清"]
    CLARIFY --> COMMIT
    
    ROUTE -->|knowledge| KNOW["KnowledgeHandler"]
    ROUTE -->|chitchat| CHAT["ChitchatHandler"]
    ROUTE -->|task| TASK["TaskHandler"]
    
    TYPE -->|OBJECT| OBJ["解析对象上下文"]
    OBJ --> SLOT["触发澄清并尝试补槽"]
    SLOT --> TASK

    KNOW --> COMMIT
    CHAT --> COMMIT
    TASK --> COMMIT["提交 turn"]

    COMMIT --> SAVE["保存 DialogueState"]
    SAVE --> R(["返回回复"])
    
  
```

### 3.3 系统分层结构

客服后端的代码组织遵循一个清晰的分层：

| 层                | 主要职责                                 |
| ----------------- | ---------------------------------------- |
| API 层            | 接收 HTTP 请求，组织请求与响应           |
| Service 层        | 把一次对话处理串起来                     |
| Engine 层         | 顶层调度，决定走哪条处理轨道             |
| Planning 层       | 负责做本轮规划、意图判断、校验、澄清兜底 |
| Task 层           | 负责推进固定任务流                       |
| Knowledge 层      | 负责检索信息并生成回复                   |
| Chitchat 层       | 负责闲聊与兜底回复                       |
| Domain 层         | 消息、上下文、对话状态等领域模型         |
| Repository 层     | 把 DialogueState 持久化到数据库          |
| Infrastructure 层 | LLM客户端、HTTP 客户端、数据库客户端     |
| Config层          | 读取环境变量                             |

## 第4章 创建客服后端

### 4.1 创建项目

项目名称：`customer-service-backend`

解释器类型：`uv`

python版本：`3.12`

### 4.2 创建目录结构

从`资料`中找到如下文件

创建并复制`flow_config` 和其中的 `yml`

复制`.env.example`到 `.env`

复制 `pyproject.toml`

安装依赖：

```bash
uv sync
```

### 4.3 pydantic-settings

参考文档：
设置和环境变量：https://fastapi.tiangolo.com/zh/advanced/settings/

参考代码：

```python
# atguigu/conf/config.py
# uv add pydantic-settings

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Path(__file__) — 当前文件的绝对路径（atguigu/conf/config.py）
# .parents[2] — 向上两级目录，到达项目根目录（cusomer_service_demo/）
# 最终指向 项目根目录下的 .env 文件
ENV_FILE = Path(__file__).parents[2] / ".env"


class Settings(BaseSettings):
    # LLM
    llm_model: str
    llm_base_url: str
    llm_api_key: str

    # 商城 API
    commerce_api_base_url: str

    # 数据库
    database_url: str
    database_url_sync: str

    # 服务器
    app_host: str
    app_port: int

    # 从.env文件中读取配置信息
    # 如果读取真实环境变量，则不写这句话
    # extra="ignore" 表示忽略.env中有，这里没有的配置项，不会报错
    # env_file_encoding：如果遇到乱码问题则添加这个属性解决
    # 注意这里对象名必须叫model_config ，而且必须定义，否则配置会被回收
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", env_file_encoding="utf-8")


@lru_cache
def get_settings():
    print("get_settings")
    return Settings()


# @lru_cache 会修改它所装饰的函数，
# 使其返回第一次返回的相同值，而不是每次都重新计算并执行函数代码。
settings = get_settings()

if __name__ == '__main__':
    # 第一次访问
    print(settings.llm_base_url)
    # 再次访问
    print(settings.llm_base_url)

```

### 4.4 基础设施

#### LLM

```python
# atguigu/infrastructure/llm.py
# uv add langchain
# uv add langchain-openai

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from atguigu.conf.config import settings

"""
如果没有 BaseChatModel，你可能需要：
为每个 AI 厂商写不同的代码（OpenAI 一套、百度一套、阿里一套...）
处理各种复杂的 API 调用细节
有了它之后：
统一标准：不管换哪个 AI 模型，代码写法都一样
简化操作：只需要关心"问什么"，不用关心"怎么问"
"""
llm: BaseChatModel = init_chat_model(
    model=settings.llm_model,
    model_provider="openai",
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    temperature=0
)

if __name__ == '__main__':
    print(llm.invoke("你好").content)
```

#### HTTPX

发送异步http请求

快速入门：https://www.python-httpx.org/quickstart/

```python
# atguigu/infrastructure/http_client.py
# uv add httpx

import httpx

# 同步方式
r = httpx.get('http://localhost:18081/users/u1001/orders')
print(r.json())
```

异步调用支持：https://www.python-httpx.org/async/

```python
# atguigu/infrastructure/http_client.py
# uv add httpx

import asyncio
import httpx

# 异步方式
async def main():
    async with httpx.AsyncClient() as client:
        response = await client.get('http://localhost:18081/users/u1001/orders')
        print(response.json())

asyncio.run(main())
```

优化：

```python
# atguigu/infrastructure/http_client.py
# uv add httpx

import asyncio
import httpx

# 全局变量
http_client: httpx.AsyncClient | None = None

# 初始化http客户端
def init_http_client():
    global http_client
    http_client = httpx.AsyncClient(timeout=10.0)

# 关闭资源
async def close_http_client():
    if http_client is not None:
        await http_client.aclose()


if __name__ == '__main__':
    async def test():
        init_http_client()
        result = await http_client.get('http://localhost:18081/users/u1001/orders')
        print(result.json())

        await close_http_client()


    asyncio.run(test())
```

#### Database

参考文档：https://docs.sqlalchemy.org/en/20/intro.html#installation

##### 异步使用

搜索`async`

https://docs.sqlalchemy.org/en/20/dialects/mysql.html#module-sqlalchemy.dialects.mysql.asyncmy

```bash
uv add SQLAlchemy

# 安装mysql的异步驱动
# aiomysql
# mysql+aiomysql://root:123456@127.0.0.1:3306/customer_service?charset=utf8mb4
uv add aiomysql

# asyncmy
# mysql+asyncmy://root:123456@127.0.0.1:3306/customer_service?charset=utf8mb4
uv add asyncmy
```

##### 定义工具

https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.async_sessionmaker

```python
# atguigu/infrastructure/database.py

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine

from atguigu.conf.config import settings

# 声明全局变量
# engine            ：异步数据库引擎，负责管理连接池和与数据库的通信
# session_factory   ：异步会话工厂，用于创建数据库会话（事务单元）
engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None

# 初始化
def init_db_engine() -> None:
    global engine, async_session

    # 1. 创建异步引擎
    # echo=False            ：SQL 语句日志输出，开发环境可设为True，生产环境设置为False
    # pool_pre_ping=True    ：每次从连接池取出连接前发送心跳查询（SELECT 1）检测连接是否存活，
    #                         若连接已断开则自动丢弃并创建新连接，避免"连接已失效"错误
    engine = create_async_engine(settings.database_url, echo=True, pool_pre_ping=True)

    # 2. 创建异步session工厂
    async_session = async_sessionmaker(engine, expire_on_commit=False)

# 关闭资源
async def close_db_engine():
    if engine is not None:
        await engine.dispose()


if __name__ == '__main__':

    async def test():

        # 初始化引擎
        init_db_engine()

        # 创建session
        async with async_session() as session:

            # text()：把 Python字符串 转换成 可执行SQL对象。
            result = await session.execute(text("SELECT 1"))

            # data = result.fetchall()
            data = result.fetchone()
            print(data)
            print(type(data))
            await session.commit()  # 显式提交，就不会再自动 ROLLBACK 了

        # 关闭引擎
        await close_db_engine()


    asyncio.run(test())
```

###### expire_on_commit参数的作用

https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.sessionmaker

![image-20260610051451924](C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/01-expire_on_commit参数.png)

![image-20260610051641579](C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/01-expire_on_commit参数2.png)

翻译过来就是：

当 `expire_on_commit=True`的时候，只要事务提交，内存中的实体对象会被清除，后面再访问`实体属性`的时候会隐式触发sql查询，从数据库中重新查询最新的数据。但是这个功能在异步情况下无法使用，必须设置为`False`。

如果异步的情况下想要获取数据库中的最新数据，则可以通过写一个SQL的方式获取。

###### 为什么会回滚？

SQLAlchemy 的 session 有一个机制：一旦你开始用它，它就会自动开启一个数据库事务。退出 async with 代码块时，如果你没有显式调用 `session.commit()`，它就会自动执行 ROLLBACK 来结束这个事务。
对于 SELECT 这种只读查询，ROLLBACK 和 COMMIT 效果完全一样——都不会改变数据库里的任何数据。只是 ROLLBACK 更"诚实"地告诉数据库：刚才没改任何东西。
如果不想看到这条日志，可以在 with 块结束前加一行 `await session.commit()`



##### 扩展

比较expire_on_commit在异步连接和同步连接下的区别

###### SQL

```sql
CREATE TABLE user_account (
    id INTEGER NOT NULL AUTO_INCREMENT,
    NAME VARCHAR(30) NOT NULL,
    fullname VARCHAR(30),
    PRIMARY KEY (id)
)
```

###### 同步

```python
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from atguigu.conf.config import settings


# 声明ORM模型的基类，所有数据表实体类继承此类
class Base(DeclarativeBase):
    pass

# 用户实体模型，映射数据库user_account表
class User(Base):
    # 指定映射的数据表名称
    __tablename__ = "user_account"
    # 主键id
    id: Mapped[int] = mapped_column(primary_key=True)
    # 用户昵称，最长30字符，非空
    name: Mapped[str] = mapped_column(String(30))
    # 用户全名，可选字段，允许为空
    fullname: Mapped[Optional[str]]

# 创建同步数据库引擎，加载配置中的数据库连接地址，echo=True打印原生SQL日志
engine = create_engine(settings.database_url_sync, echo=True)
# 构建会话工厂，提交后内存对象不过期 False； 过期 True
session_factory = sessionmaker(engine, expire_on_commit=False)

# 创建数据库会话，with 自动关闭会话资源
with session_factory() as session:
    # 实例化User对象，构造一条用户数据
    sandy = User(
        name="sandy",
        fullname="Sandy Cheeks"
    )
    # 将对象加入会话，标记待新增
    session.add(sandy)
    # 提交事务，执行insert写入数据库
    session.commit()

    # 打印新增数据的name字段
    print(sandy.name)
```

###### 异步

```python
import asyncio
from typing import Optional
from sqlalchemy import String
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from atguigu.conf.config import settings

# 声明ORM模型的基类，所有数据表实体类继承此类
class Base(DeclarativeBase):
    pass

# 用户实体模型，映射数据库user_account表
class User(Base):
    # 指定映射的数据表名称
    __tablename__ = "user_account"
    # 主键id
    id: Mapped[int] = mapped_column(primary_key=True)
    # 用户昵称，最长30字符，非空
    name: Mapped[str] = mapped_column(String(30))
    # 用户全名，可选字段，允许为空
    fullname: Mapped[Optional[str]]

# 创建异步数据库引擎，加载配置内异步连接地址，echo开启SQL日志输出
engine = create_async_engine(settings.database_url, echo=True)
# 创建异步会话工厂，提交后内存对象不过期 False；（设置为True会报错）
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def test():
    # 创建数据库异步会话，with 自动释放连接资源
    async with async_session_factory() as session:
        # 实例化User对象，构造一条用户数据
        sandy = User(
            name="sandy",
            fullname="Sandy Cheeks"
        )

        # 将对象加入会话，标记待新增
        session.add(sandy)

        # 异步提交事务，执行INSERT写入数据库
        await session.commit()

        # 打印新增数据的name字段
        print(sandy.name)

# 启动异步事件循环，执行异步函数
asyncio.run(test())
```



# 二、领域模型domain

## 第1章 消息模型 messages

### 1.1 为什么需要“消息”这个概念

在对话系统中，所有的交互本质上都是**一来一回的消息传递**。

- **用户发消息**：表达需求（文字）或指向某个具体商品/订单（对象）。
- **机器人回消息**：给出回答（文字）或指向某个具体商品/订单（对象）。

创建`atguigu/domain/messages.py` 用来定义这些“消息”。

### 1.2 FocusedObject：聚焦对象

当用户在聊天时点击了一个订单卡片或商品卡片，相当于告知系统"接下来的操作都与这个东西相关"。这个消息里就包含了一个“聚焦对象”。它告诉系统：**“我们现在正在讨论这个东西。”**

在`messages.py`中添加如下定义：

```python
class FocusedObject(BaseModel):
    """
    聚焦对象
    """
    id: str  # 对象的唯一标识（如order_id、product_id）
    type: str  # 对象类型（如 "order", "product"）
    title: str  # 对象的标题（如 “纯棉T恤”）
    attributes: dict = {} # 其他额外信息
```

`attributes` 字段的内容举例：

```json
{
    "status":"待发货",
    "amount":"8999.00",
    "created_at":"2026-04-10T10:00:00",
    "cover_url":"https://placehold.co/400x400/0052cc/ffffff?text=iPhone+15+Pro"
}
```

### 1.3 MessageType：消息枚举

这个枚举用来明确标记当前消息的“形态”，方便程序后续的逻辑判断。

在`messages.py`中添加如下定义：

```python
class MessageType(Enum):
    """
    消息类型
    """
    TEXT = "text"  # 文本类型
    OBJECT = "object"  # 对象类型
```

### 1.4 UserMessage：用户消息

在`messages.py`中添加如下定义：

```python
class UserMessage(BaseModel):
    sender_id: str  # 用户ID(必填字段)
    message_id: str  # 消息ID(必填字段)
    type: MessageType  # 消息类型（text 或 object）必填字段
    text: str | None = None  # 文本消息(用户说的话)
    object: FocusedObject | None = None  # 对象类型的消息(用户点击的对象)
```

两种典型场景：

1.  **纯文本**：用户说“我要退款”。此时 `type=TEXT`，`object=None`。
2.  **对象交互**：用户在订单卡片上点了“发送订单”。此时 `type=OBJECT`，`object` 字段会填入那个订单的 `FocusedObject`。

---

### 1.5 BotMessage：机器人消息

在`messages.py`中添加如下定义：

```python
class BotMessage(BaseModel):
    text: str | None = None # 机器人回复的话
    object: FocusedObject | None = None # 机器人返回的对象
```

机器人消息的结构更简单，只关注**回复内容**。

### 1.6 序列化

为了方便后续的操作，可以使用 `pydantic` 的 `obj.model_dump(mode='json')` 和 `cls.model_validate(data)` 做数据类型转换：

| 方法                          | 作用                     | 形象比喻                             |
| ----------------------------- | ------------------------ | ------------------------------------ |
| `obj.model_dump(mode='json')` | 把 Python 对象变成字典   | **打包**：把行李装进箱子，准备入库   |
| `cls.model_validate(data)`    | 把字典还原成 Python 对象 | **拆包**：从箱子里取出行李，恢复原样 |

**示例：**在`messages.py`中添加单元测试

```python
if __name__ == '__main__':
    fo = FocusedObject(id="1", type="2")

    # 把 Python 对象变成字典
    data = fo.model_dump(mode='json')
    # 把字典还原成 Python 对象
    obj = FocusedObject.model_validate(data)

    print(type(fo)) #FocusedObject对象
    print(type(data)) #dict字典
    print(type(obj)) #FocusedObject对象
```

### 1.7 小结

#### 1.7.1 模块

| 模块            | 核心职责                                    |
| --------------- | ------------------------------------------- |
| `FocusedObject` | 描述对话中正在讨论的具体“东西”（订单/商品） |
| `UserMessage`   | 记录用户的输入，支持文字和对象点击          |
| `BotMessage`    | 记录机器人的输出，支持文字和对象            |
| `MessageType`   | 区分消息是“文本”还是“对象”                  |

#### 1.7.2 UML类图

```mermaid
classDiagram
    class BaseModel
    class Enum

	class MessageType {
        <<enumeration>>
        +TEXT = "text"
        +OBJECT = "object"
    }
    class FocusedObject {
        +str id
        +str type
        +str | None title
        +dict attributes
    }
    class UserMessage {
        +str sender_id
        +str message_id
        +MessageType type
        +str | None text
        +FocusedObject | None object
    }
    class BotMessage {
        +str | None text
        +FocusedObject | None object
    }
    
    UserMessage --> MessageType : 持有
    Enum <|-- MessageType
    
    BaseModel  <|--  UserMessage
    BaseModel  <|--  BotMessage
    BaseModel <|--  FocusedObject
    UserMessage --> FocusedObject : 持有
    BotMessage --> FocusedObject : 持有
```

UML：统一建模语言

典型的UML：类图、时序图、用例图、状态机图

#### 1.7.3 完整的代码

```python
# atguigu/domain/messages.py

"""
消息类型：两种
UserMessage(用户)
BotMessage(机器人)
"""
from enum import Enum
from pydantic import BaseModel

class FocusedObject(BaseModel):
    """
    聚焦对象
    """
    id: str  # 对象的唯一标识（如order_id、product_id）
    type: str  # 对象类型（如 "order", "product"）
    title: str | None = None  # 对象的标题（如 “纯棉T恤”）
    attributes: dict = {} # 其他额外信息

class MessageType(Enum):
    TEXT = "text"  # 文本类型
    OBJECT = "object"  # 对象类型

class UserMessage(BaseModel):
    sender_id: str  # 用户ID(必填字段)
    message_id: str  # 消息ID(必填字段)
    type: MessageType  # 消息类型（text or object）必填字段
    text: str | None = None  # 文本消息
    object: FocusedObject | None = None  # 对象类型的消息

class BotMessage(BaseModel):
    text: str | None = None
    object: FocusedObject | None = None

if __name__ == '__main__':
    fo = FocusedObject(id="1", type="2")

    # 把 Python 对象变成字典
    data = fo.model_dump(mode='json')
    # 把字典还原成 Python 对象
    obj = FocusedObject.model_validate(data)

    print(type(fo)) #FocusedObject对象
    print(type(data)) #dict字典
    print(type(obj)) #FocusedObject对象

```

## 第2章 对话上下文模型 contexts

### 2.1 为什么需要"上下文"这个概念

#### 2.1.1 例1 单任务正常完成

在前一节项目概述中，我们已经知道客服系统有三类能力：任务流程、信息检索、闲聊。其中任务流程是最复杂的一类，因为它要分步骤推进，而且经常会被打断。

举几个真实的例子：

```text
例 1：单任务正常完成
用户：我要退款
客服：请告诉我你的订单号。
用户：A20240315001
客服：请简单说一下退款原因。
用户：尺码不合适
客服：好的，订单 A20240315001 的退款申请已提交……
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-单任务正常完成.png" style="zoom: 33%;" />

#### 2.1.2 例2 任务被另一个任务打断

```text
例 2：任务被另一个任务打断
用户：我要退款
客服：请告诉我你的订单号。
用户：先帮我查一下物流
客服：好的，我们先处理物流查询。请告诉我你的订单号。
用户：A20240315001
客服：订单 A20240315001 当前状态是运输中……
用户：继续刚才的退款
客服：好的，我们继续刚才的退款申请。请告诉我你的订单号。
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-任务被另一个任务打断.png" style="zoom: 33%;" />

从例 2 可以看到两件事： 

- 同一时刻可能存在**多个未完成的任务**，需要区分谁是当前活跃的、谁是被搁置的
- 系统在切换任务时会插播一些"过场白"，例如"好的，我们先处理物流查询"

这两件事就分别对应了两类对象：

| 概念            | 作用                                     |
| --------------- | ---------------------------------------- |
| `TaskContext`   | **业务任务**的执行快照（用户想做的事）   |
| `SystemContext` | **系统流程**的执行快照（系统插播的过场） |

只有把"用户的任务"和"系统的过场"分开建模，多任务切换、打断恢复这些行为才说得清楚。下面我们逐一分析。

创建`atguigu/domain/contexts.py` 用来定义这些“上下文”。

### 2.2 TaskContext：业务任务的快照

#### 2.2.1 什么是“业务任务”

```python
active_task: TaskContext | None
paused_tasks: List[TaskContext]
```

用户可以在对话中同时涉及多个业务任务，例如正在办理退款时临时插问一句物流状态。系统的处理方式是：同一时刻只有一个**活跃任务**（`active_task`），被中断的任务压入**挂起列表**（`paused_tasks`），新任务处理完毕后可恢复。`paused_tasks` 是一个有序列表，按挂起的先后顺序排列。每个任务的执行进度封装在 `TaskContext` 中。

#### 2.2.2 定义TaskContext

在`contexts.py`中添加如下定义：

```python
class TaskContext(BaseModel):
    """
    业务任务上下文
    """
    flow_id: str  # 业务任务的流程ID
    step_id: str | None = None  # 业务任务下的步骤ID
    slots: dict = {}  # 业务任务执行过程中收集到的槽位数据
```

字段说明：

| 字段      | 含义                                                         |
| --------- | ------------------------------------------------------------ |
| `flow_id` | 当前业务任务对应的流程 ID，例如 `refund_request`、`order_status_query` |
| `step_id` | 当前业务任务执行到了流程中的哪一步，例如 `ask_order_number`、`ask_refund_reason` |
| `slots`   | 业务任务执行过程中收集到的数据，例如 `{"order_number": "A001", "refund_reason": "尺码不合适"}` |

可以把 `TaskContext` 类比成一份正在填的表单：

- `flow_id` 表示这是哪一种表单（退款单 / 物流单）
- `step_id` 表示当前填到了哪一格
- `slots` 表示已经填写好的内容

#### 2.2.3 场景模拟

以退款申请流程为例：

##### 第一轮

```text
用户：我要退款
客服：请告诉我你的订单号。
```

这一轮结束后，`TaskContext` 的状态是：

`flow_id` 对应配置文件中的流程名称 `refund_request`，`step_id` 对应流程内某个步骤的 `id`，`slots` 中的键来自该流程涉及的槽位定义：

```python
TaskContext(
    flow_id="refund_request",
    step_id="ask_order_number",
    slots={}
)
```

##### 第二轮

```text
用户：A20240315001
客服：请简单说一下退款原因。
```

这一轮结束后变成：

```python
TaskContext(
    flow_id="refund_request",
    step_id="ask_refund_reason",
    slots={"order_number": "A20240315001"}
)
```

##### 第三轮

```
用户：尺码不合适
客服：好的，订单A20240315001的退款申请已提交，原因是：尺码不合适。后续会尽快为你处理。
```

这一轮结束后变成：

```python
TaskContext(
    flow_id="refund_request",
    step_id="refund_submitted",
    slots={"order_number": "A20240315001", "refund_reason": "尺码不合适"}
)
```

可以看到 `step_id` 在流程中不断推进，`slots` 在不断累积。`flow_id` 只在任务开始时确定，之后整个生命周期都不变。

### 2.3 SystemContext：系统流程的快照

#### 2.3.1 什么是"系统流程"

```python
active_system_flow: SystemContext | None
```

系统流程是由系统主动发起的一类特殊交互，用于向用户传递系统级通知，例如询问缺失参数、告知任务启动或完成、说明任务被打断等。

业务任务由用户发起（例如"我要退款"），系统流程则由**系统自己发起**，用来插播一些过场话。

举几个常见的例子：

| 场景             | 系统说的话                             |
| ---------------- | -------------------------------------- |
| 任务刚开始       | "好的，我们先处理退款申请。"           |
| 任务被新任务打断 | "好的，我们先把退款放一放，先看物流。" |
| 任务被用户取消   | "好的，退款已为你取消。"               |
| 之前的任务恢复   | "好的，我们继续刚才的退款。"           |
| 需要补一个槽位   | "请告诉我你的订单号。"                 |

这些话不属于任何一个具体业务流程，它们是系统在"协调"业务流程时说的。所以我们专门为这类交互建一个上下文模型——`SystemContext`。

#### 2.3.2 定义基类SystemContext

`SystemContext` 的基础结构与 `TaskContext` 相同，同样记录流程标识和当前步骤。

在`contexts.py`中添加如下定义：

```python
class SystemContext(BaseModel):
    """
    系统流程上下文
    定义具体流程的通用属性
    """
    flow_id: str  # 系统流程的流程ID
    step_id: str | None = None  # 系统流程当前执行的步骤ID
```

字段说明：

| 字段      | 含义                                                         |
| --------- | ------------------------------------------------------------ |
| `flow_id` | 系统流程的流程ID，例如 `system_task_started`、`system_collect_information` |
| `step_id` | 系统流程当前执行的步骤ID，例如 `start`、`ask`                |

#### 2.3.3 五个子类

| 子类                       | 触发时机                                    | 系统会说的话（举例）                         |
| -------------------------- | ------------------------------------------- | -------------------------------------------- |
| `StartedSystemContext`     | 用户刚发起一个新任务                        | "好的，我们先处理退款申请。"                 |
| `InterruptedSystemContext` | 用户在 A 任务过程中切到 B 任务              | "好的，我们先把退款放一放，先处理物流查询。" |
| `CanceledSystemContext`    | 用户主动取消当前任务                        | "好的，退款申请已为你取消。"                 |
| `ResumedSystemContext`     | 用户要求恢复之前挂起的任务                  | "好的，我们继续刚才的退款申请。"             |
| `CollectSystemContext`     | 业务流程跑到 `collect` 步骤，需要用户补数据 | "请告诉我你的订单号。"                       |

### 2.4 五个 SystemContext 子类

下面逐一定义每个子类，每个子类都搭配一段交互示例，看看它出现在对话的哪个位置。

#### 2.4.1 StartedSystemContext：任务刚开始

##### 类定义

在`contexts.py`中添加如下定义：

```python
class StartedSystemContext(SystemContext):
    """
    流程开始
    """
    started_flow_id: str = ""  #新开始的业务任务ID
    started_flow_name: str = ""  #新开始的业务任务名字
```

##### 场景模拟

```text
用户：我要退款                        ← 触发"业务任务"开始
客服：好的，我们先处理退款申请。       ← 这是 "系统流程" StartedSystemContext(system_task_started) 起作用
客服：请告诉我你的订单号。             ← 这里已经进入了 "业务任务"
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-StartedSystemContext场景模拟.png" style="zoom: 33%;" />

**注意**：

- 第一条机器人回复是"系统流程"产生的过场，第二条才是"业务任务"本身。
- 业务任务和系统流程**同时**存在。这一轮里"系统流程"先说话，说完就退出，然后"业务任务"继续推进。

##### 状态快照

```python
active_task = TaskContext(flow_id="refund_request", step_id="ask_order_number", slots={})
active_system_task = StartedSystemContext(
    flow_id="system_task_started",
    step_id="acknowledge",
    started_flow_id="refund_request",
    started_flow_name="退款申请",
)
```

#### 2.4.2 InterruptedSystemContext：任务被打断

##### 类定义

在`contexts.py`中添加如下定义：

```python
class InterruptedSystemContext(SystemContext):
    """
    流程中断
    """
    interrupted_flow_id: str = ""  # 被中断的旧业务任务ID
    interrupted_flow_name: str = ""  # 被中断的旧业务任务名字
    started_flow_id: str = ""  # 新开始的业务任务ID
    started_flow_name: str = ""  # 新开始的业务任务名字
```

为什么一个上下文里要装"老任务 + 新任务"两份信息？因为系统说话时要把两个名字都念出来。

任务被中断 有两种典型场景。

##### 场景模拟1

###### 场景:打断一个任务(基础)

```text
用户：我要退款
客服：好的，我们先处理退款申请。 
客服：请告诉我你的订单号。
用户：先帮我查一下物流                ← 用户中途切到另一个任务
客服：好的，我们先把退款申请放一放，先处理物流查询。   ← Interrupted
客服：请告诉我你的订单号。
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-InterruptedSystemContext场景模拟.png" style="zoom: 33%;" />

###### 状态快照

- 老的退款任务先放着（用 `interrupted_flow_name`）
- 现在开始处理新的物流查询任务（用 `started_flow_name`）

```python
paused_tasks = [TaskContext(flow_id="refund_request", ...)]   ← 退款被挂起
active_task = TaskContext(flow_id="logistics_tracking", ...)   ← 物流变成活跃
active_system_task = InterruptedSystemContext(
    flow_id="system_task_interrupted",
    step_id="acknowledge",
    interrupted_flow_id="refund_request",
    interrupted_flow_name="退款申请",
    started_flow_id="logistics_tracking",
    started_flow_name="物流查询",
)
```

##### 场景模拟2

###### 场景:打断两个任务(连环打断)

```text
用户:帮我查一下订单状态
客服:好的,我们先处理订单状态查询。      
客服:请告诉我你的订单号。
用户:先帮我查一下物流                  ← 第一次中途切换
客服:好的,我们先把订单状态查询放一放,先处理物流查询。   ← 第一次 Interrupted
客服:请告诉我你的订单号。
用户:我想申请退款                       ← 第二次中途切换
客服:好的,我们先把物流查询放一放,先处理退款申请。      ← 第二次 Interrupted
客服:请告诉我你的订单号。
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-InterruptedSystemContext 打断两个任务(连环打断).png" style="zoom: 33%;" />

###### 状态快照

- `paused_tasks` 不是单个字段,而是一个**列表/栈**。它的本质就是要承接"连环打断"这种场景
- `InterruptedSystemContext` 里的 `interrupted_*` 字段只记录**最近这一次**被打断的任务,而不是全部历史。系统说话只关心"刚刚被你放下的那件事",不需要把所有挂起的任务都念一遍
- 订单状态查询的信息**完整保留**在 `paused_tasks[0]` 里——`step_id`、`slots` 都在。后续如果用户说"继续刚才的订单状态查询",系统能精准恢复到 `ask_order_number` 那一步

```python
# ─── 起点:用户进入对话 ─────────────────────────────────
active_task   = None
paused_tasks  = []

# ─── 第 1 轮:"帮我查一下订单状态" ─────────────────────
active_task   = TaskContext(
    flow_id="order_status_query",
    step_id="ask_order_number",
    slots={},
)
paused_tasks  = []
active_system_task = StartedSystemContext(
    started_flow_id="order_status_query",
    started_flow_name="订单状态查询",
)

# ─── 第 2 轮:"先帮我查一下物流"(第一次打断)──────────
active_task = TaskContext(
    flow_id="logistics_tracking",
    step_id="ask_order_number",
    slots={},
)
paused_tasks  = [
    TaskContext(flow_id="order_status_query", step_id="ask_order_number", slots={}),
]
active_system_task = InterruptedSystemContext(
    interrupted_flow_id="order_status_query",
    interrupted_flow_name="订单状态查询",
    started_flow_id="logistics_tracking",
    started_flow_name="物流查询",
)

# ─── 第 3 轮:"我想申请退款"(第二次打断)────────────
active_task = TaskContext(
    flow_id="refund_request",
    step_id="ask_order_number",
    slots={},
)
paused_tasks  = [
    TaskContext(flow_id="order_status_query", step_id="ask_order_number", slots={}),
    TaskContext(flow_id="logistics_tracking", step_id="ask_order_number", slots={}),
]
active_system_task = InterruptedSystemContext(
    interrupted_flow_id="logistics_tracking",
    interrupted_flow_name="物流查询",
    started_flow_id="refund_request",
    started_flow_name="退款申请",
    flow_id= "system_task_interrupted",
    step_id = "acknowledge"
)
```

#### 2.4.3 CanceledSystemContext：任务被取消

##### 类定义

在`contexts.py`中添加如下定义：

```python
class CanceledSystemContext(SystemContext):
    """
    流程取消
    """
    canceled_flow_id: str = "" # 被取消的业务任务ID
    canceled_flow_name: str = "" # 被取消的业务任务名字
```

##### 场景模拟1

任务取消有两种典型场景，对应用户两种不同的说法

###### 场景:取消当前活跃任务

```text
用户:我要退款
客服:好的,我们先处理退款申请。      
客服:请告诉我你的订单号。
用户:算了不退了                      ← 取消正在做的任务
客服:好的,退款申请先帮你取消。
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-CanceledSystemContext场景模拟.png" style="zoom: 33%;" />

###### 状态快照

此时 `active_task` 被清空,不存在新任务。

注意:被取消的退款**不会**进入 `paused_tasks`,而是直接丢弃。这是和"打断"最根本的区别。

```python
# ─── 起点:用户进入退款流程 ─────────────────────────
active_task   = TaskContext(
    flow_id="refund_request",
    step_id="ask_order_number",
    slots={},
)
paused_tasks  = []
active_system_task = StartedSystemContext(
    flow_id="system_task_started",
    step_id="acknowledge",
    started_flow_id="refund_request",
    started_flow_name="退款申请",
)

# ─── "算了不退了" → 取消活跃任务 ──────────────────
active_task   = None                                ← 被丢弃,不进 paused_tasks
paused_tasks  = []
active_system_task = CanceledSystemContext(
    flow_id="system_task_canceled",
    step_id="acknowledge",
    canceled_flow_id="refund_request",
    canceled_flow_name="退款申请",
)
```

##### 场景模拟2

###### 场景:取消挂起的任务

```text
用户:我要退款
客服:请告诉我你的订单号。
用户:先帮我查一下物流                ← 退款被打断,进入 paused_tasks
客服:好的,我们先把退款放一放,先处理物流查询。
客服:请告诉我你的订单号。
用户:A20240315001
客服:订单当前状态是运输中……
用户:刚才那个退款不退了              ← 在物流任务中,取消挂起栈里的退款
客服:好的,退款申请已为你取消。
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-CanceledSystemContext 取消挂起的任务场景模拟.png" style="zoom: 33%;" />

###### 状态快照

此时 `active_task` 还是物流查询(不动),被丢弃的是 `paused_tasks` 里的退款。物流流程继续往下走。

```python
# ─── 起点:退款被打断,物流查询正在跑 ───────────────
active_task = TaskContext(
    flow_id="logistics_tracking",
    step_id="show_logistics",
    slots={"order_number": "A20240315001", ...},
)
paused_tasks  = [
    TaskContext(flow_id="refund_request", step_id="ask_order_number", slots={}),
]
active_system_task = None                            ← 物流流程的过场已经结束

# ─── "刚才那个退款不退了" → 取消挂起栈里的退款 ────
active_task   = None
paused_tasks  = []                                   ← 退款从栈中被清掉
active_system_task = CanceledSystemContext(
    flow_id = "system_task_canceled"
    step_id = "acknowledge"
    canceled_flow_id="refund_request",
    canceled_flow_name="退款申请",
)
```

##### 取消 vs 打断的区别

|                  | 打断(Interrupted)                          | 取消(Canceled)                          |
| ---------------- | ------------------------------------------ | --------------------------------------- |
| 被处理的任务去向 | 进入 `paused_tasks`,后续可恢复             | 直接丢弃,不保留                         |
| 被处理的是谁     | 一定是**当前活跃任务**(因为有新任务要切入) | 可以是**活跃任务**,也可以是**挂起任务** |
| 是否伴随新任务   | 必然有(没有新任务就不会发生打断)           | 可有可无                                |
| 系统说的话       | "先把 A 放一放,处理 B"                     | "已为你取消 A"                          |

#### 2.4.4 ResumedSystemContext：任务被恢复

##### 类定义

在`contexts.py`中添加如下定义：

```python
class ResumedSystemContext(SystemContext):
    """
    流程恢复
    """
    resumed_flow_id: str = ""  # 被恢复的业务任务ID
    resumed_flow_name: str = ""  # 被恢复的业务任务名字
```

##### 场景模拟1

恢复任务有两种典型场景,对应用户两种不同的说法

接着 2.4.2 的连环打断场景往下:

###### 场景：默认恢复(用户没指明恢复哪个)

```text
(此时栈里有两个挂起任务:订单状态查询、物流查询;
 active_task 是退款申请,正在收集退款原因)

客服:请简单说一下退款原因。
用户:尺码不合适
客服:好的,订单 A20240315001 的退款申请已提交,原因是:尺码不合适。后续会尽快为你处理。
                                       ← 退款流程结束,active_task 清空
用户:继续刚才的                          ← 用户没指明,默认恢复最近挂起的
客服:好的,我们继续刚才的物流查询。       ← Resumed(恢复栈顶)
客服:请告诉我你的订单号。                ← 从物流流程之前停下的位置继续
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-ResumedSystemContext LIFO 默认恢复(用户没指明恢复哪个).png" style="zoom: 33%;" />

###### 状态快照

注意 `paused_tasks` 从栈顶弹出了物流查询，订单状态查询还留在栈里。这就是 LIFO 语义——**后进先出**。

```python
# ─── 退款结束后 ───────────────────────────────────
active_task   = None
paused_tasks  = [
    TaskContext(flow_id="order_status_query", step_id="ask_order_number", slots={}),
    TaskContext(flow_id="logistics_tracking", step_id="ask_order_number", slots={}),
]

# ─── "继续刚才的" → 恢复栈顶(物流查询)────────────
active_task   = TaskContext(
    flow_id="logistics_tracking",
    step_id="ask_order_number",
    slots={},
)
paused_tasks  = [
    TaskContext(flow_id="order_status_query", step_id="ask_order_number", slots={}),
]
active_system_task = ResumedSystemContext(
    flow_id="system_task_resumed",
    step_id="acknowledge",
    resumed_flow_id="logistics_tracking",
    resumed_flow_name="物流查询",
)
```

##### 场景模拟2

###### 场景:精确恢复(用户明确指明)

同样从连环打断的状态出发:

```text
(此时栈里有两个挂起任务:订单状态查询、物流查询;
 active_task 是退款申请)

客服:请简单说一下退款原因。
用户:尺码不合适
客服:好的,订单 A20240315001 的退款申请已提交,原因是:尺码不合适。后续会尽快为你处理。
用户:继续刚才的订单状态查询              ← 用户明确指名,跳过栈顶
客服:好的,我们继续刚才的订单状态查询。   ← Resumed(精确匹配)
客服:请告诉我你的订单号。
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-ResumedSystemContext 精确恢复 (用户明确指明).png" style="zoom: 33%;" />

###### 状态快照

注意这次被恢复的是**栈中间(底部)**的订单状态查询,物流查询还留在栈里没动。这种"跨过栈顶恢复"是 LIFO 默认行为做不到的,必须靠用户明确指明才能触发。

```python
# ─── 退款结束后 ───────────────────────────────────
active_task   = None
paused_tasks  = [
    TaskContext(flow_id="order_status_query", step_id="ask_order_number", slots={}),
    TaskContext(flow_id="logistics_tracking", step_id="ask_order_number", slots={}),
]

# ─── "继续刚才的订单状态查询" → 精确匹配 ─────────
active_task   = TaskContext(
    flow_id="order_status_query",
    step_id="ask_order_number",
    slots={},
)
paused_tasks  = [
    TaskContext(flow_id="logistics_tracking", step_id="ask_order_number", slots={}),
]
active_system_task = ResumedSystemContext(
    flow_id="system_task_resumed",
    step_id="acknowledge",
    resumed_flow_id="order_status_query",
    resumed_flow_name="订单状态查询",
)
```

#### 2.4.5 CollectSystemContext：收集槽位

##### 类定义

在`contexts.py`中添加如下定义：

```python
class CollectedSystemContext(SystemContext):
    """
    系统流程收集槽位信息
    """
    slot_name: str = ""  # 收集的槽位名
    response: dict = {}  # 例如：{"text":"请告诉我你的订单号"}
```

##### 场景模拟

它出现在业务流程跑到 `collect` 步骤、但用户还没提供该信息时：

```text
客服：请告诉我你的订单号。   ← CollectSystemContext 在驱动这条消息
用户：A20240315001
客服：（订单号收集到之后，返回业务任务的流程，继续下一步）
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-CollectSystemContext：收集槽位场景模拟.png" style="zoom: 33%;" />

##### 它和前面四个的不同

|          | 前四个                                    | CollectSystemContext             |
| -------- | ----------------------------------------- | -------------------------------- |
| 触发原因 | 任务的生命周期事件（开始/打断/取消/恢复） | 业务任务主动声明"我需要这个槽位" |
| 出现频率 | 任务切换时可能会出现                      | 每次需要补槽都会出现             |
| 携带数据 | 业务流程名字                              | 槽位名 + 提示文案                |

可以这么理解：前四个是"任务级别"的过场，CollectSystemContext 是"步骤级别"的代理人——它帮业务流程把"我需要这个数据"这句话说出来，然后等用户回答。

##### 状态快照

```python
active_task = TaskContext(
    flow_id="refund_request",
    step_id="ask_order_number",      ← 业务任务流程停在 collect 步骤
    slots={}
)
active_system_task = CollectSystemContext(
    flow_id="system_collect_information",
    step_id="ask",
    slot_name="order_number",
    response={"text": "请告诉我你的订单号。"},
)
```

### 2.5 SystemContext 序列化

#### 2.5.1 问题背景

SystemContext 有多个子类，需要根据 flow_id 动态识别并实例化对应的子类对象。

在`contexts.py`中进行测试如下：

```python
if __name__ == '__main__':

    # 定义StartedSystemContext的字典数据
    data = {
        "flow_id": "system_task_started",
        "step_id": "start",
        "started_flow_id": "order_status_query",
        "started_flow_name": "订单状态查询"
    }

    # 用父类的返序列化方法没办法将子类的字段返序列化出来
    obj1 = SystemContext.model_validate(data)
    print(type(obj1))
    print(obj1)

    # 用子类的返序列化方法每次要区分到底是哪个子类对象
    obj2 = StartedSystemContext.model_validate(data)
    print(type(obj2))
    print(obj2)

```

#### 2.5.2 解决方案

使用 Pydantic Discriminated Union（区分/鉴别联合类型）

###### 步骤1：在每个子类中添加 Literal 类型的 flow_id 字段

   - 作用：作为"身份标签"，唯一标识每个子类

   - 原理：Pydantic 通过读取这个字段的值来判断应该创建哪个子类的实例

在`contexts.py`中的`SystemContext` 的所有子类中添加`flow_id`：

```python
class StartedSystemContext(SystemContext):
    ...
    # 使用 Literal 类型固定 flow_id 值，作为 Discriminated Union 的区分字段
    flow_id: Literal["system_task_started"] = "system_task_started"

class InterruptedSystemContext(SystemContext):
    ...
    flow_id: Literal["system_task_interrupted"] = "system_task_interrupted"

class CanceledSystemContext(SystemContext):
    ...
    flow_id: Literal["system_task_canceled"] = "system_task_canceled"

class ResumedSystemContext(SystemContext):
    ...
    flow_id: Literal["system_task_resumed"] = "system_task_resumed"

class CollectedSystemContext(SystemContext):
    ...
    flow_id: Literal["system_collect_information"] = "system_collect_information"
```

###### 步骤2：定义联合类型 SystemContextUnion

   - 使用 Annotated 将所有子类组合成一个联合类型
   - 通过 `Field(discriminator="flow_id")` 指定 flow_id 为区分字段
   - Pydantic 会根据 flow_id 的值自动选择正确的子类进行反序列化

在`contexts.py`中添加如下定义：

```python
# 定义系统流程的联合类型
SystemContextUnion = Annotated[
    StartedSystemContext |
    InterruptedSystemContext |
    CanceledSystemContext |
    ResumedSystemContext |
    CollectedSystemContext,
    Field(discriminator="flow_id")
]
```

###### 步骤3：创建 TypeAdapter 适配器实例

   - TypeAdapter 是 Pydantic V2 提供的工具，用于处理非 BaseModel 类型
   - 提供 validate_python() 方法替代 model_validate()

在`contexts.py`中添加如下定义：

```python
# 创建适配器实例
system_context_adapter = TypeAdapter(SystemContextUnion)
```

###### 步骤4：使用适配器进行类型转换

   - 反序列化：system_context_adapter.validate_python(data)
   - 优势：无需手动维护映射字典，代码更简洁、类型更安全

测试序列化，在`contexts.py`中添加如下测试代码：

```python
# 使用适配器的 validate_python()：替代 model_validate()
obj = system_context_adapter.validate_python(data)

print(type(obj))
print(obj)
```

### 2.6 TaskContext 与 SystemContext 的协作

最后用一张图把两类上下文的协作关系串起来。

```mermaid
flowchart TD
    A(["用户消息"]) --> B{"判断意图"}
    B -->|新任务| C["创建 TaskContext"]
    C --> D["激活 StartedSystemContext<br/>过场白"]
    D --> E["业务流程开始推进"]

    E --> F{"是否需要槽位?"}
    F -->|需要| G["激活 CollectSystemContext<br/>提示用户输入"]
    G --> H["用户输入数据 → 写入 slots"]
    H --> E
    F -->|不需要| I{"流程是否结束?"}

    I -->|未结束| E
    I -->|结束| J["TaskContext 置空"]
```

再加一条任务切换的支路：

```mermaid
flowchart TD
    K["用户在任务 A 中途<br/>切换到任务 B"]
    K --> L["A 进入 paused_tasks"]
    L --> M["创建任务 B 的 TaskContext"]
    M --> N["激活 InterruptedSystemContext<br/>说: 先把 A 放放,处理 B"]
    N --> O["B 正常推进"]
    O --> P{"B 结束后?"}
    P -->|用户继续 A| Q["从 paused_tasks 取出 A<br/>激活 ResumedSystemContext"]
    P -->|新对话| R["保持现状"]
```

整个 `contexts.py` 的本质，就是用两类对象、五个子类，把"用户的事"和"系统的事"分开，再用 `flow_id` 标识每一种系统流程。

### 2.7 小结

#### 2.7.1 模块

| 模块                       | 核心职责                                 |
| -------------------------- | ---------------------------------------- |
| `TaskContext`              | 用户想做什么、做到哪一步、收集了哪些数据 |
| `SystemContext` 基类       | 系统插播的过场，统一序列化入口           |
| `StartedSystemContext`     | 任务开始的过场                           |
| `InterruptedSystemContext` | 任务被新任务打断的过场                   |
| `CanceledSystemContext`    | 任务被取消的过场                         |
| `ResumedSystemContext`     | 任务被恢复的过场                         |
| `CollectSystemContext`     | 收集槽位时的过场                         |
| `SystemContextUnion`       | 联合类型                                 |
| `system_context_adapter`   | 联合类型适配器实例                       |

#### 2.7.2 类图

`context`整体由两类对象、五个具体的系统流程子类组成

```mermaid
classDiagram
    %% 独立类
    class TaskContext {
        +str flow_id
        +str step_id
        +dict slots
    }

    %% 父基类
    class SystemContext {
        +str flow_id
        +str step_id
    }

    %% 五个子类，全部继承 SystemContext
    class StartedSystemContext {
        +str started_flow_id
        +str started_flow_name
    }
    SystemContext <|-- StartedSystemContext 

    class InterruptedSystemContext {
        +str interrupted_flow_id
        +str interrupted_flow_name
        +str started_flow_id
        +str started_flow_name
    }
    SystemContext <|-- InterruptedSystemContext

    class CanceledSystemContext {
        +str canceled_flow_id
        +str canceled_flow_name
    }
    SystemContext <|-- CanceledSystemContext

    class ResumedSystemContext {
        +str resumed_flow_id
        +str resumed_flow_name
    }
    SystemContext <|-- ResumedSystemContext

    class CollectSystemContext {
        +str slot_name
        +str response
    }
    SystemContext <|-- CollectSystemContext
```

#### 2.7.3 完整的代码

```python
# atguigu/domain/contexts.py
from typing import Literal, Annotated

from pydantic import BaseModel, Field, TypeAdapter


class TaskContext(BaseModel):
    """
    业务任务上下文
    """
    flow_id: str  # 业务任务的流程ID
    step_id: str | None = None  # 业务任务下的步骤ID
    slots: dict = {}  # 业务任务执行过程中收集到的槽位数据


class SystemContext(BaseModel):
    """
    系统流程上下文
    定义具体流程的通用属性
    """
    flow_id: str  # 系统流程的流程ID
    step_id: str | None = None  # 系统流程当前执行的步骤ID

class StartedSystemContext(SystemContext):
    """
    流程开始
    """
    started_flow_id: str = ""  # 新开始的业务任务ID
    started_flow_name: str = ""  # 新开始的业务任务名字

    # 使用 Literal 类型固定 flow_id 值，作为 Discriminated Union 的区分字段
    flow_id: Literal["system_task_started"] = "system_task_started"

class InterruptedSystemContext(SystemContext):
    """
    流程中断
    """
    interrupted_flow_id: str = ""  # 被中断的旧业务任务ID
    interrupted_flow_name: str = ""  # 被中断的旧业务任务名字
    started_flow_id: str = ""  # 新开始的业务任务ID
    started_flow_name: str = ""  # 新开始的业务任务名字
    flow_id: Literal["system_task_interrupted"] = "system_task_interrupted"

class CanceledSystemContext(SystemContext):
    """
    流程取消
    """
    canceled_flow_id: str = "" # 被取消的业务任务ID
    canceled_flow_name: str = "" # 被取消的业务任务名字
    flow_id: Literal["system_task_canceled"] = "system_task_canceled"

class ResumedSystemContext(SystemContext):
    """
    流程恢复
    """
    resumed_flow_id: str = ""  # 被恢复的业务任务ID
    resumed_flow_name: str = ""  # 被恢复的业务任务名字
    flow_id: Literal["system_task_resumed"] = "system_task_resumed"

class CollectedSystemContext(SystemContext):
    """
    系统流程收集槽位信息
    """
    slot_name: str = ""  # 收集的槽位名
    response: dict = {}  # {"text":"请告诉我你的订单号"}
    flow_id: Literal["system_collect_information"] = "system_collect_information"

# 定义系统流程的联合类型
SystemContextUnion = Annotated[
    StartedSystemContext |
    InterruptedSystemContext |
    CanceledSystemContext |
    ResumedSystemContext |
    CollectedSystemContext,
    Field(discriminator="flow_id")
]
# 创建联合类型适配器实例
system_context_adapter = TypeAdapter(SystemContextUnion)

if __name__ == '__main__':

    # 定义StartedSystemContext的字典数据
    data = {
        "flow_id": "system_task_started",
        "step_id": "start",
        "started_flow_id": "order_status_query",
        "started_flow_name": "订单状态查询"
    }

    # 用父类的序列化方法没办法将子类的字段序列化出来
    obj1 = SystemContext.model_validate(data)
    print(type(obj1))
    print(obj1)

    # 用子类的序列化方法每次要区分到底是哪个子类对象
    obj2 = StartedSystemContext.model_validate(data)
    print(type(obj2))
    print(obj2)

    # 使用适配器的 validate_python()：替代 model_validate()
    obj = system_context_adapter.validate_python(data)

    print(type(obj))
    print(obj)
```

## 第3章 对话状态模型 state 

### 3.1 为什么需要 DialogueState

在上一节我们用 `contexts.py` 解决了两件事：

- 用 `TaskContext` 记录"用户当前在做的业务任务"
- 用 `SystemContext` 记录"系统插播的过场"

但是只有这两个对象还不够。一次真实的对话，需要记的东西要多得多：

- 这个用户**正在做**哪个任务？
- 这个用户**搁置**了哪些任务？
- 当前是不是有**系统过场**在进行？
- 用户当前**聚焦**在哪个订单或者商品上？
- 这个用户**历史**上聊过哪些话？

更进一步，一次"我要退款"的处理通常会产生**多条回复**：系统先说"好的，我们先处理退款申请"，再说"请告诉我你的订单号"。如果中途报错了，我们希望整轮回滚，而不是只留半截对话记录在历史里。**所以还需要一个"暂存格子"，专门放正在处理中的那一轮**对话。

这里系统专门定义了一个聚合对象——`DialogueState`，作为整个对话状态的"中央仓库"。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-DialogueState聚合根.png" style="zoom: 33%;" />

创建`atguigu/domain/state.py`，定义`DialogueState`。

### 3.2 Turn：一次对话轮次

#### 3.2.1 概念

一个 `Turn` 表示一次**完整的问答交互**：用户说一句话，机器人给出回复（可能多条消息）。

```text
用户：我要退款           ← user_message
客服：好的，我们先处理退款申请。
客服：请告诉我你的订单号。  ← bot_messages（2 条）
```

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-一次对话轮次.png" style="zoom: 33%;" />

上面这一整段就是一个 Turn。

#### 3.2.2 类定义

在`state.py`中添加如下定义：

```python
class Turn(BaseModel):
    """
    本轮对话的对象
    """
    turn_id: str	# 轮次唯一标识，使用 UUID
    user_message: UserMessage 	# 这一轮用户说的那一句话
    bot_messages: list[BotMessage]	# 这一轮系统给出的所有回复
```

为什么 `bot_messages` 是列表？因为系统在一轮内经常会发多条消息：先说一句过场（"好的，我们先处理退款申请。"），再说一句业务问题（"请告诉我你的订单号。"）。

### 3.3 Session：一段会话

#### 3.3.1 概念

如果 Turn 是"一问一答"，那 Session 就是"一整段聊天"。

举例：用户上午跟客服聊了一阵，又下午回来聊。这两段聊天我们就会划成两个 Session。怎么判断要不要切到新 Session？我们后面会看到一个简单的规则：超过 60 分钟没有活动，就关闭旧 Session。

#### 3.3.2 类定义

在`state.py`中添加如下定义：

```python
class Session(BaseModel):
    """
    会话信息
    """
    session_id: str  # 会话唯一标识，使用 UUID
    started_at: float  # 会话开始的时间戳
    last_activity_at: float  # 最后一次活动的时间戳，用来判断超时
    closed_at: float | None = None  # 会话关闭时间，未关闭时为 `None`
    turns: list[Turn] = []  # 这个会话里的所有轮次
```

#### 3.3.3 一个用户的会话历史举例

```python
state.sessions = [
    Session(
        session_id="abc-123",
        started_at=1700000000.0,
        last_activity_at=1700001800.0,
        closed_at=1700005400.0,         # 已关闭
        turns=[Turn(...), Turn(...), Turn(...)],
    ),
    Session(
        session_id="def-456",
        started_at=1700090000.0,
        last_activity_at=1700090600.0,
        closed_at=None,                  # 当前活跃
        turns=[Turn(...)],
    ),
]
```

### 3.4 DialogueState：对话状态聚合根

到这里，所有零件都准备好了，可以拼起 `DialogueState` 这个聚合根。

在`state.py`中添加如下定义：

```python
class DialogueState(BaseModel):
    sender_id: str  # 用户唯一标识
    active_task: TaskContext | None = None  # 当前活跃的业务任务
    paused_tasks: list[TaskContext] = []  # 被挂起的任务列表
    active_system_task: SystemContext | None = None  # 当前执行的系统流程
    focused_object: FocusedObject | None = None # 用户当前聚焦的订单 / 商品
    sessions: list[Session] = []  # 历史会话列表
    current_session_id: str | None = None  # 当前活跃会话的ID
    pending_turn: Turn | None = None  # 正在处理中的轮次
```

下面我们为 `DialogueState` 定义方法。

### 3.5 任务相关

#### 3.5.1 涉及字段

- `active_task`
- `paused_tasks`
- `active_system_task`

回顾上一节学过的关系：

| 字段                 | 关注                 |
| -------------------- | -------------------- |
| `active_task`        | "用户当前在做什么"   |
| `paused_tasks`       | "用户挂起了哪些事"   |
| `active_system_task` | "系统现在在插播什么" |

#### 3.5.2 方法清单

在`state.py`的类 `DialogueState` 中添加如下方法：

```python
# --------------任务相关--------------------------
def start_active_task(self, active_task: TaskContext):
    """
    把传进来的 TaskContext 设为活跃任务。
    调用时机：当 TurnPlanner 判断用户发起了一个新业务任务时。
    :param active_task:
    :return:
    """
    self.active_task = active_task

def end_active_task(self):
    """
    结束业务任务
    调用时机：当业务任务流程跑到 end 步骤时。
    :return:
    """
    self.active_task = None

def cancel_active_task(self):
    """
    取消业务任务
    把活跃任务和当前系统过场都清空
    调用时机：用户主动说"算了不退了"这类取消意图时。
    :return:
    """
    self.active_task = None
    self.active_system_task = None

def interrupted_active_task(self):
    """
    中断活跃任务
    把当前活跃任务 移到挂起列表，再清空活跃任务。
    调用时机：用户在任务 A 中途切到任务 B 时。
    :return:
    """
    self.paused_tasks.append(self.active_task)
    self.active_task = None

def resumed_active_task(self, flow_id: str | None = None) -> bool:
    """
    恢复业务任务:流程ID

    如果用户没有明确指定需要恢复的具体任务，那么 flow_id = None，恢复最近的任务
    如果用户明确指定需要恢复的具体任务：
      则按 flow_id 在挂起列表里找到这个任务，恢复为活跃任务，并从挂起列表里移除。

    调用时机：用户说"继续刚才的退款"这类意图时。

    注意：任务被恢复时，step_id 和 slots 都还在，所以可以从挂起前的位置接着跑，不用从头来。

    :return: 恢复成功或失败
    """

    # 1. 判断栈中是否存在中断的业务任务
    if not self.paused_tasks:
        return False

    # 2. 如果业务流程ID不存在
    if flow_id is None:
        self.active_task = self.paused_tasks.pop()
        return True

    # 2. 如果业务流程ID存在
    for i, paused_task in enumerate(self.paused_tasks):
        if paused_task.flow_id == flow_id:
            # 激活
            self.active_task = paused_task
            # 删除
            del self.paused_tasks[i]
            return True

    return False

def start_active_system_task(self, active_system_task: SystemContext):
    """
    开启系统流程
    调用时机：每当系统要插播过场白（任务开始、打断、取消、恢复、收集槽位）时。
    :param active_system_task:
    :return:
    """
    self.active_system_task = active_system_task

def end_active_system_task(self):
    """
    结束系统流程
    :return:
    """
    self.active_system_task = None
    
def current_active_task(self):
    """
    返回当前正在执行的任务（系统流程、业务任务）
    先获取系统流程 如果获取不到 获取业务任务
    - 如果有系统流程，先返回系统流程
    - 否则返回业务任务

    为什么系统流程优先？
    因为系统流程往往是要插播一句过场白，必须先说完，然后才能让位给业务任务继续。
    :return:
    """
    return self.active_system_task or self.active_task
```

### 3.6 槽位相关

在`state.py`的类 `DialogueState` 中添加如下方法：

```python
# --------------槽位相关--------------------------
def set_slots(self, slots: dict[str, Any]):
    """
    设置槽位
    把传进来的 dict 合并到当前活跃任务的 slots 里。
    :param slots:
    :return:
    """
    self.active_task.slots.update(slots)

def remove_slot(self, slot_name: str):
    """
    移除槽位
    从当前活跃任务的 `slots` 里删一个键。比如用户输入有误，重新收集时会先清掉旧的。
    :param slot_name: 移除的槽位名
    :return:
    """
    self.active_task.slots.pop(slot_name)
```

### 3.7 会话与轮次相关

#### 3.7.1 涉及字段

- `sessions`
- `current_session_id`
- `pending_turn`

涉及方法（4 个会话方法 + 2 个轮次方法）。

#### 3.7.2 会话方法

在`state.py`的类 `DialogueState` 中添加如下方法：

```python
# -------------- session相关 --------------------------
def current_session(self) -> Session | None:
    """
    获取当前会话对象
    根据 current_session_id 在 sessions 里找出当前会话。
    :return:
    """
    for session in self.sessions:
        if session.session_id == self.current_session_id:
            return session

    return None

def start_session(self):
    """
    开启新会话
    创建一个新的 Session，加进 sessions 列表，并把它设为当前会话。
    :return:
    """
    if self.current_session() is None:
        now = time.time()
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            started_at=now,
            last_activity_at=now
        )
        self.sessions.append(session)
        self.current_session_id = session_id

def close_current_session(self):
    """
    关闭当前会话
    给当前会话打上关闭时间戳，再把 current_session_id 置空。
    :return:
    """
    if self.current_session() is not None:
        # 1. 修改session的时间closed_at
        self.current_session().closed_at = time.time()
        # 2. 清空当前的session_id
        self.current_session_id = None

def reset_runtime_state_for_new_session(self):
    """
    重置会话状态
    session会话超时新会话开始前的"清理工作"。
    注意：
    - 它只清运行时字段：当前任务、挂起任务、系统过场、聚焦对象
    - 它不清 sessions：历史会话需要保留
    :return:
    """
    self.active_task = None
    self.active_system_task = None
    self.paused_tasks = []
    self.focused_object = None
    self.pending_turn = None
    self.current_session_id = None
```

#### 3.7.3 会话方法的协作

实际使用时，会话方法经常按下面这个顺序连起来用：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-三个会话方法的协作.png" style="zoom: 33%;" />

这段逻辑会在后面 `DialogueEngine` 的 `_prepare_session` 方法里看到。这一节我们只要理解他们各自负责什么就够了。

#### 3.7.4 轮次方法

在`state.py`的类 `DialogueState` 中添加如下方法：

```python
# --------------turn相关--------------------------
def begin_turn(self, message: UserMessage):
    """
    开始一个turn
    收到用户消息后，把它装进一个新的 turn 对象
    先放到 pending_turn，而不是直接进 session。
    :param message:
    :return:
    """
    if self.current_session():
        self.pending_turn = Turn(
            turn_id=str(uuid.uuid4()),
            user_message=message,
            bot_messages=[]
        )

def commit_pending_turn(self):
    """
    提交一个turn
    本轮处理完成（机器人回复也填好了）后
    把 pending_turn 追加到当前会话的 turns 里，再把 pending_turn 清空。
    :return:
    """
    if self.current_session():
        self.current_session().turns.append(self.pending_turn)
        self.pending_turn = None
```

#### 3.7.5 为什么要有pending_turn 

为什么要有 **pending_turn** 这个中间字段，这是这一节最值得停下来想一想的地方。如果我们没有 `pending_turn`，处理一轮消息看起来好像也能做：

```text
× 假设没有 pending_turn 的写法
1. 创建一个 turn对象，直接放到 current_session.turns 里
2. user_message 和 bot_message 放在这个 turn对象中
4. 处理完返回
```

这种写法在两个场景下会出问题：

**场景一：处理过程中出错**

如果引擎处理到一半异常退出，`turns` 里就留下了一个"半成品" Turn——有用户消息但回复不完整。下次再读这份历史就乱了。

**场景二：处理结果未必要落盘**

有些请求可能在中途被判定为"非法消息"、"重复消息"，直接丢弃就好。如果已经塞进 `turns`，再删就麻烦了。

所以系统采用"**两步提交**"：

```text
✓ 用 pending_turn 的写法
1. begin_turn → pending_turn = Turn(user_message, [])     ← 暂存区
2. 引擎处理，往 pending_turn.bot_messages 里 append   ← 填补回复
3. commit_pending_turn → 追加到 session.turns         ← 最终落盘
```

这样：

- 处理失败时只要丢掉 `pending_turn` 即可，`turns` 始终干净，
- 决定不入库时也只要不调用 `commit_pending_turn`，`pending_turn` 不参与持久化，它是纯粹的请求内瞬态。
- `turns` 里的每一条 Turn 都是"完整的"

完整流程图：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/02-pending_turn完整流程图.png" style="zoom: 33%;" />

### 3.8 聚焦对象相关

在`state.py`的类 `DialogueState` 中添加如下方法：

```python
# --------------FocusedObject相关--------------------------
def set_focused_object(self, focused_object: FocusedObject):
    """
    设置聚焦对象
    调用时机：
    用户发的不是文本而是一条对象消息时,例如前端点了订单卡片
    需要把这个对象设为当前关注的对象。
    :param focused_object:
    """
    self.focused_object = focused_object
```

### 3.9 持久化

整个 `DialogueState` 不会拆成多张表，而是序列化为一个 JSON 字符串，存到 `dialogue_states` 表的 `state_json` 字段里：

| 字段         | 类型                | 说明                                   |
| ------------ | ------------------- | -------------------------------------- |
| `sender_id`  | `VARCHAR(255)` 主键 | 用户唯一标识                           |
| `state_json` | `TEXT`              | `DialogueState` 序列化后的 JSON 字符串 |

读取时反过来：从数据库读出 `state_json` → `json.loads` → `DialogueState.from_dict()`。

这种"整份 JSON"的设计在生产环境不一定最优，但在学习阶段能让你直接打开一行数据库记录就看到对话的所有状态，调试起来非常直观。

### 3.10 小结

#### 3.10.1 类图

`DialogueState` 是对话系统的核心数据结构，记录了与某位用户的完整对话上下文，它把任务、流程、会话、轮次、聚焦对象统一管起来。它以 `sender_id` 为键进行持久化存储，每次消息处理前从数据库加载，处理完毕后存回。整个处理过程中，所有对话逻辑的读写都发生在同一个 `DialogueState` 实例上。

`DialogueState` 的属性分为四组：**用户任务上下文**、**系统任务上下文**、**聚焦对象**和**会话历史**。

```mermaid
classDiagram
    class DialogueState {
        +str sender_id
        +TaskContext active_task = None
        +List~TaskContext~ paused_tasks
        +SystemContext active_system_flow = None
        +FocusedObject focused_object = None
        +List~Session~ sessions
        +str current_session_id = None
        +Turn pending_turn = None
    }
    class TaskContext {
        +str flow_id
        +str step_id = None
        +dict slots
    }
    class SystemContext {
        +str flow_id
        +str step_id = None
    }
    class FocusedObject {
        +str type
        +str id
        +str title = ""
        +dict attributes
    }
    class Session {
        +str session_id
        +float started_at
        +float last_activity_at
        +float closed_at = None
        +List~Turn~ turns
    }
    class Turn {
        +str turn_id
        +UserMessage user_message
        +List~BotMessage~ bot_messages
    }

    DialogueState --> TaskContext : active_task / paused_tasks
    DialogueState --> SystemContext : active_system_flow
    DialogueState --> FocusedObject : focused_object
    DialogueState --> Session : sessions
    DialogueState --> Turn : pending_turn
    Session --> Turn : turns
```

#### 3.10.2 完整的代码

```python
# atguigu/domain/state.py

import time
import uuid
from typing import Dict, Any

from pydantic import BaseModel

from atguigu.domain.contexts import TaskContext, SystemContext
from atguigu.domain.messages import FocusedObject, UserMessage, BotMessage

class Turn(BaseModel):
    """
    本轮对话的对象
    """
    turn_id: str    # 轮次唯一标识，使用 UUID
    user_message: UserMessage   # 这一轮用户说的那一句话
    bot_messages: list[BotMessage]  # 这一轮系统给出的所有回复

class Session(BaseModel):
    """
    会话信息
    """
    session_id: str  # 会话唯一标识，使用 UUID
    started_at: float  # 会话开始的时间戳
    last_activity_at: float  # 最后一次活动的时间戳，用来判断超时
    closed_at: float | None = None  # 会话关闭时间，未关闭时为 `None`
    turns: list[Turn] = []  # 这个会话里的所有轮次

class DialogueState(BaseModel):
    sender_id: str  # 用户id
    active_task: TaskContext | None = None  # 当前执行的业务任务
    paused_tasks: list[TaskContext] = []  # 当期暂停的业务任务（多个）
    active_system_task: SystemContext | None = None  # 当前执行的系统流程
    focused_object: FocusedObject | None = None
    sessions: list[Session] = [] # 当前用户的所有都存储起来
    current_session_id: str | None = None  # 当前用户的session的sessionID
    pending_turn: Turn | None = None  # turn会话的暂存区（变量：内存中缓冲区）

    # --------------任务相关--------------------------
    def start_active_task(self, active_task: TaskContext):
        """
        把传进来的 TaskContext 设为活跃任务。
        调用时机：当 TurnPlanner 判断用户发起了一个新业务任务时。
        :param active_task:
        :return:
        """
        self.active_task = active_task

    def end_active_task(self):
        """
        结束业务任务
        调用时机：当业务任务流程跑到 end 步骤时。
        :return:
        """
        self.active_task = None

    def cancel_active_task(self):
        """
        取消业务任务
        把活跃任务和当前系统过场都清空
        调用时机：用户主动说"算了不退了"这类取消意图时。
        :return:
        """
        self.active_task = None
        self.active_system_task = None

    def interrupted_active_task(self):
        """
        中断活跃任务
        把当前活跃任务 移到挂起列表，再清空活跃任务。
        调用时机：用户在任务 A 中途切到任务 B 时。
        :return:
        """
        self.paused_tasks.append(self.active_task)
        self.active_task = None

    def resumed_active_task(self, flow_id: str | None):
        """
        恢复业务任务:流程ID
        按 flow_id 在挂起列表里找一个任务，恢复为活跃任务，并从挂起列表里移除。
        调用时机：用户说"继续刚才的退款"这类意图时。

        注意：任务被恢复时，step_id 和 slots 都还在，所以可以从挂起前的位置接着跑，不用从头来。
        :return:
        """
        # 1. 恢复最近的任务
        if not flow_id:
            task = self.paused_tasks.pop()
            self.active_task = task
            return

        # 2. 精确恢复某一暂停的业务任务
        for task in self.paused_tasks:
            if task.flow_id == flow_id:
                self.active_task = task
                self.paused_tasks.remove(task)
                return

        # 3. 兜底
        task = self.paused_tasks.pop()
        self.active_task = task

    def start_active_system_task(self, active_system_task: SystemContext):
        """
        开启系统流程
        调用时机：每当系统要插播过场白（任务开始、打断、取消、恢复、收集槽位）时。
        :param active_system_task:
        :return:
        """
        self.active_system_task = active_system_task

    def end_active_system_task(self):
        """
        结束系统流程
        :return:
        """
        self.active_system_task = None

    def current_active_task(self):
        """
        返回当前正在执行的任务（系统流程、业务任务）
        先获取系统流程 如果获取不到 获取业务任务
        - 如果有系统流程，先返回系统流程
        - 否则返回业务任务

        为什么系统流程优先？
        因为系统流程往往是要插播一句过场白，必须先说完，然后才能让位给业务任务继续。
        :return:
        """
        return self.active_system_task or self.active_task

    # --------------槽位相关--------------------------
    def set_slots(self, slots: Dict[str, Any]):
        """
        设置槽位
        :param slots:
        :return:
        """
        self.active_task.slots.update(slots)

    def remove_slot(self, slot_name: str):
        """
        移除槽位
        :param slot_name: 移除的槽位名
        :return:
        """
        self.active_task.slots.pop(slot_name)

    # -------------- session相关 --------------------------
    def current_session(self) -> Session | None:
        """
        获取当前会话对象
        根据 current_session_id 在 sessions 里找出当前会话。
        :return:
        """
        for session in self.sessions:
            if session.session_id == self.current_session_id:
                return session

        return None

    def start_session(self):
        """
        开启新会话
        创建一个新的 Session，加进 sessions 列表，并把它设为当前会话。
        :return:
        """
        if self.current_session() is None:
            now = time.time()
            session_id = str(uuid.uuid4())
            session = Session(
                session_id=session_id,
                started_at=now,
                last_activity_at=now
            )
            self.sessions.append(session)
            self.current_session_id = session_id

    def close_current_session(self):
        """
        关闭当前会话
        给当前会话打上关闭时间戳，再把 current_session_id 置空。
        :return:
        """
        if self.current_session() is not None:
            # 1. 修改session的时间closed_at
            self.current_session().closed_at = time.time()
            # 2. 清空当前的session_id
            self.current_session_id = None

    def reset_runtime_state_for_new_session(self):
        """
        重置会话状态
        session会话超时新会话开始前的"清理工作"。
        注意：
        - 它只清运行时字段：当前任务、挂起任务、系统过场、聚焦对象
        - 它不清 sessions：历史会话需要保留
        :return:
        """
        self.active_task = None
        self.active_system_task = None
        self.paused_tasks = []
        self.focused_object = None
        self.pending_turn = None
        self.current_session_id = None

    # --------------turn相关--------------------------
    def begin_turn(self, message: UserMessage):
        """
        开始一个turn
        收到用户消息后，把它装进一个新的 turn 对象
        先放到 pending_turn，而不是直接进 session。
        :param message:
        :return:
        """
        if self.current_session():
            self.pending_turn = Turn(
                turn_id=str(uuid.uuid4()),
                user_message=message,
                bot_messages=[]
            )

    def commit_turn(self):
        """
        提交一个turn
        本轮处理完成（机器人回复也填好了）后
        把 pending_turn 追加到当前会话的 turns 里，再把 pending_turn 清空。
        :return:
        """
        if self.current_session():
            self.current_session().turns.append(self.pending_turn)
            self.pending_turn = None

    # --------------FocusedObject相关--------------------------
    def set_focused_object(self, focused_object: FocusedObject):
        """
        设置聚焦对象
        调用时机：
        用户发的不是文本而是一条对象消息时,例如前端点了订单卡片
        需要把这个对象设为当前关注的对象。
        :param focused_object:
        """
        self.focused_object = focused_object
```



# 三、流程数据模型与加载

## 第1章  本章目标

到前面为止，我们已经把"运行时状态"这条线建好了：`TaskContext` / `SystemContext` / `DialogueState`。它们记录的是"对话进行到哪了"。

今天解决另一个问题：**业务流程到底长什么样？谁来定义它？**

以**退款流程**为例：

```yaml
  refund_request:
    name: 退款申请
    description: 帮用户提交简单的退款申请，收集订单号和退款原因。
    steps:
      - id: start
        type: start
        next: ask_order_number

      - id: ask_order_number
        type: collect
        slot_name: order_number
        response:
          text: "请告诉我你的订单号。"
        next: ask_refund_reason

      - id: ask_refund_reason
        type: collect
        slot_name: refund_reason
        response:
          text: "请简单说一下退款原因。"
        next: refund_submitted

      - id: refund_submitted
        type: action
        action: action_response
        args:
          text: "好的，订单{{ slots.order_number }}的退款申请已提交，原因是：{{ slots.refund_reason }}。后续会尽快为你处理。"
        next: end


      - id: end
        type: end
        next: [ ]
```

这份 YAML 现在还只是一个文本文件。要让代码能"读懂"它，并按照定义一步步推进，必须先把它**加载成内存里的 Python 对象**：

- 定义描述流程的所有数据模型（步骤、连接、流程、槽位）
- 写一个加载器，把两个 YAML 文件读进来变成对象

## 第2章 YAML 快速入门

### 2.1 YAML 是什么

YAML 是专门用来写**配置文件**的格式，**大小写敏感、靠缩进表示层级**。

和它对标的是 XML 和 JSON ，但 YAML 去掉了大括号、引号、尖括号这些"噪音"。

同一份数据，三种格式对比：

XML:

```xml
<root>
  <!-- 这是name节点 -->
  <name id="001">退款申请</name>
  <steps>
    <step sort="1">start</step>
    <step sort="2">end</step>
  </steps>
</root>
```

JSON：

不能写注释

```json
{
	"name": {
     	"id": "001",
     	"text": "退款申请"
  	},
  	"steps": [{
        "sort": 1, 
        "text": "start"
    }, {
        "sort": 2, 
        "text": "end"
    }]
}
```

YAML：

```yaml
name: 
  id: 001 #这是唯一标识
  text: 退款申请
steps:
  - sort: 1
    text: start
  - sort: 2
    text: end
```

可以看到 YAML 更清爽。这也是为什么大量工具（Docker Compos、Kubernetes）都用它写配置文件。

### 2.2 核心规则

1. 缩进用空格，不能用 Tab

   通常缩进 2 个空格，不能乱改。

2. 大小写敏感

   `name` 和 `Name` 是两个不同的键。

3. \# 表示注释

   从 `#` 开始到行尾都是注释。

4. 冒号后面必须加一个空格，这是最容易错的地方！

   ```yaml
   key: value
   ```


5. `-` 后要有空格

   ```yaml
   - id: refund_submitted
   ```

### 2.3 基本数据类型

#### 2.3.1 字符串

```yaml
# 直接写
name: 张三

# 带空格/特殊字符，建议加引号
msg: "hello world"
info: '这是一段说明'
```

#### 2.3.2 数字（整数 / 浮点数）

```yaml
age: 20
score: 95.5
```

#### 2.3.3 布尔值

```yaml
isStudent: true
isOpen: false
```

#### 2.3.4 空值

```yaml
data: null
flag:
```

### 2.4 三种基本结构

#### 2.4.1 键值对

```yaml
person:
  name: 李四
  age: 25
```

#### 2.4.2 列表

用 `-` 加空格表示列表的每一项：

```yaml
hobbies:
  - 游泳
  - 跑步
  - 编程
```

#### 2.4.3 嵌套

##### 数组里套对象

```yaml
users:
  - name: 小明
    age: 18
  - name: 小红
    age: 19
    score: 100
```

##### 对象里嵌套对象

```
person:
  name: 李四
  age: 25
  address:
    city: 北京
    street: 中关村
```

### 2.5 两个进阶写法

#### 2.5.1 多行文本

如果一个值很长（比如给 LLM 的提示词），可以用 `|` 写多行，保留换行：

```yaml
prompt: |
  你是一个中文电商客服助手，语气自然、友好。
  请基于建议回复，生成一句更自然的回复。
  改写后的回复：
```

`|` 表示"下面这几行原样保留，包括换行"。我们的 `system_flows.yml` 里 `rephrase` 模式的提示词就是这么写的。

#### 2.5.2 空列表

```yaml
next: []
```

`[]` 表示一个空列表。流程的 `end` 步骤就用它表示"后面没有下一步了"。

### 2.6 Python 怎么读 YAML

安装 `PyYAML` ：

```bash
uv add pyyaml
```

在 `atguigu/test/yaml/` 目录中创建 `test.yml` 文件

```yaml
flows:
  refund_request:
    name: 退款申请
    steps:
      - id: start
        type: start
```

`yaml.safe_load` 会把 YAML 文本**变成 Python 的字典和列表**。映射变成 `dict`，列表变成 `list`，值自动变成对应的 `str` / `int` / `bool`。

```python
# atguigu/test/yaml/load_yml.py

import yaml

with open("test.yml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

print(data)
```

> 为什么用 `safe_load` 而不是 `load`？`safe_load` 只解析纯数据，不会执行 YAML 里可能藏着的任意 Python 代码，更安全。读外部文件一律用 `safe_load`。

```yaml
# 表面上是个配置文件，暗地里却在执行系统命令
bad_actor: !!python/object/apply:os.system
  args: ['rm -rf /']  # 删除一切或者窃取环境变量

# !! 告诉 PyYAML 解析器：“后面我要调用你针对 Python 环境特有的、预先定义好的高级解析类型）
# python/object：告诉解析器，接下来要构建一个 Python 的对象
# /apply：告诉解析器，“立刻调用这个对象，并把下面提供的数据作为参数传给它”。
# :os.system：指定具体的执行目标。冒号后面跟的是 Python 的模块名和函数名——这里指向了 os 模块下的 system 函数（用于执行系统 Shell 命令）。把 args 里的参数传进去，并立刻执行！
```

## 第3章 Flow配置语法

有了 YAML 语法基础，现在来看我们项目实际的 `flow_config\user_flows.yml`和`flow_config\system_flows.yml`。

本系统将 flow 设计成可配置形式，使用 YAML 文件描述业务流程。这样新增或调整业务流程时，可以优先修改配置，而不是直接改代码。

整个 `user_flows.yml` 文件分两大块：`slots` 和 `flows`。

### 3.1 slots：声明所有槽位

`slots` 是一个"全局槽位字典"。它先把各个业务流程里**所有**会用到的槽位集中声明一遍，每个槽位有名字、类型、标签、描述。流程里要用某个槽位时，按名字引用即可。

```yaml
slots:
  order_number:
    type: text
    label: 订单号
    description: 用户的订单号

  order_status:
    type: text
    label: 订单状态
    description: 订单当前状态

  #...
```

### 3.2 flows：声明所有流程

在电商客服系统中，很多业务任务都不是一轮对话就能完成的。

例如用户说“我要退单”，系统可能需要继续追问订单号、退款原因，然后再给出处理结果。这类任务天然是一个多步骤过程。本系统把类似的多步骤任务定义成 `flow`。



`flows` 是一个"流程字典"，键是流程 id（`refund_request`），值是流程定义。每个流程有名字、描述，和一串 `steps`。

```yaml
flows:
  onboarding:
    name: 欢迎引导
    description: 在聊天窗口初次打开时欢迎用户，并介绍助手可处理的电商服务。这个 flow 通常由系统主动触发。
    steps:
      - id: start
        type: start
        next: respond
  #...
```

### 3.3 steps：流程的核心

一个 `flow` 由一系列 `steps` 组成。

每个 `step` 表示流程中的一个节点，每个 step 通过 `next` 指向下一个 step。

具体如下：

```yaml
flows:
  flow_id:
    name: 流程名称
    description: 流程说明
    steps:
      - id: start
        type: start
        next: do_something

      - id: do_something
        type: action
        action: action_response
        args:
          text: "这里是一句回复"
        next: end

      - id: end
        type: end
        next: []
```

顶层字段说明：

| 字段          | 说明                                     |
| ------------- | ---------------------------------------- |
| `flows`       | 所有 flow 的根节点。                     |
| `flow_id`     | flow 的唯一标识，例如 `refund_request`。 |
| `name`        | flow 的可读名称。                        |
| `description` | flow 的能力说明。                        |
| `steps`       | flow 包含的步骤列表。                    |

### 3.4 step: 步骤信息

一个 step 的基础结构如下：

```yaml
- id: step_id
  type: step_type
  next: next_step_id
```

基础字段说明：

| 字段   | 是否必填 | 说明                              |
| ------ | -------- | --------------------------------- |
| `id`   | 是       | step 在当前 flow 内的唯一标识。   |
| `type` | 是       | step 类型。                       |
| `next` | 通常必填 | 当前 step 执行完后进入哪个 step。 |

不同类型的 step 会有不同的额外字段。

### 3.5 type: 流程类型

基础 step type 有四种：

| type      | 作用           |
| --------- | -------------- |
| `start`   | flow 的起点。  |
| `end`     | flow 的终点。  |
| `collect` | 收集一个槽位。 |
| `action`  | 执行一个动作。 |

#### 3.5.1 start

`start` 表示 flow 的入口。

语法：

```yaml
- id: start
  type: start
  next: next_step_id
```

字段说明：

| 字段   | 说明                            |
| ------ | ------------------------------- |
| `id`   | 通常写成 `start`。              |
| `type` | 固定写 `start`。                |
| `next` | 指向第一个真正处理业务的 step。 |

示例：

```yaml
- id: start
  type: start
  next: ask_order_number
```

#### 3.5.2 end

`end` 表示 flow 的结束。

语法：

```yaml
- id: end
  type: end
  next: []
```

字段说明：

| 字段   | 说明                           |
| ------ | ------------------------------ |
| `id`   | 通常写成 `end`。               |
| `type` | 固定写 `end`。                 |
| `next` | 结束节点没有下一步，写空列表。 |

示例：

```yaml
- id: end
  type: end
  next: []
```

#### 3.5.3 action

`action` 表示执行一个动作。action 可以分为内置 action 和自定义 action，其中内置 action 有 `action_response` 和 `action_listen`。

| action            | 作用                               |
| ----------------- | ---------------------------------- |
| `action_response` | 回复用户，支持变量引用。           |
| `action_listen`   | 控制信号，表示等待用户下一轮输入。 |
| 自定义 action     | 执行业务逻辑。                     |

##### action_response

`action_response` 用来向用户回复消息。

语法：

```yaml
- id: respond
  type: action
  action: action_response
  args:
    text: "回复内容"
  next: next_step_id
```

常用args参数：

| 参数     | 说明                                                        |
| -------- | ----------------------------------------------------------- |
| `mode`   | 回复模式，可选值为 `static`、`rephrase`，默认是 `static`。  |
| `text`   | 回复给用户的文本。在 `static` 和 `rephrase` 模式下使用。    |
| `prompt` | 需要大模型改写或生成回复时使用。在 `rephrase`  模式下使用。 |

`mode` 决定 `action_response` 如何生成回复：

| mode       | 作用                                                     | 常用字段         |
| ---------- | -------------------------------------------------------- | ---------------- |
| `static`   | 直接把 `text` 渲染后回复给用户。                         | `text`           |
| `rephrase` | 先渲染 `text` 作为建议回复，再用 `prompt` 让大模型改写。 | `text`、`prompt` |

普通回复示例：

```yaml
- id: ask_order_number
  type: action
  action: action_response
  args:
    text: "请告诉我你的订单号。"
  next: listen_order_number
```

上面没有显式写 `mode`，等价于使用默认的 `static` 模式。

显式声明 `static` 的示例：

```yaml
- id: ask_order_number
  type: action
  action: action_response
  args:
    mode: static
    text: "请告诉我你的订单号。"
  next: listen_order_number
```

`rephrase` 模式示例：

```yaml
- id: not_supported
  type: action
  action: action_response
  args:
    mode: rephrase
    text: "我理解你的意思，不过这个能力目前还没有接入。"
    prompt: |
      你是一个中文电商客服助手，语气自然、友好、简洁。
      请基于下面的建议回复，生成一句更自然的中文回复，保持原意，不要扩写。
      对话上下文：
      {{ history }}
      用户最后一句：
      用户：{{ user_message }}
      建议回复：{{ current_response }}
      改写后的回复：
  next: end
```

`action_response` 支持变量引用。

常见变量有两类：

| 变量      | 说明                                   |
| --------- | -------------------------------------- |
| `slots`   | 当前业务 flow 中已经收集或写入的信息。 |
| `context` | 当前系统 flow 的上下文信息。           |

引用 slots 的示例：

```yaml
- id: refund_submitted
  type: action
  action: action_response
  args:
    text: "好的，订单{{ slots.order_number }}的退款申请已提交，原因是：{{ slots.refund_reason }}。"
  next: end
```

这里：

| 写法                        | 含义                     |
| --------------------------- | ------------------------ |
| `{{ slots.order_number }}`  | 当前 flow 中的订单号。   |
| `{{ slots.refund_reason }}` | 当前 flow 中的退款原因。 |

引用 context 的示例：

```yaml
- id: acknowledge
  type: action
  action: action_response
  args:
    text: "好的，我们先处理{{ context.started_flow_name }}。"
  next: end
```

这里的 `{{ context.started_flow_name }}` 表示当前系统上下文中的任务名称。

##### action_listen

`action_listen` 表示等待用户下一轮输入。

语法：

```yaml
- id: listen
  type: action
  action: action_listen
  next: next_step_id
```

字段说明：

| 字段     | 说明                            |
| -------- | ------------------------------- |
| `action` | 固定写 `action_listen`。        |
| `next`   | 用户补充信息后继续进入的 step。 |

示例：

```yaml
- id: listen_order_number
  type: action
  action: action_listen
  next: ask_refund_reason
```

##### 自定义 action

自定义 action 用来处理项目自己的业务逻辑。

语法：

```yaml
- id: custom_step_id
  type: action
  action: custom_action_name
  args:
    key: value
  next: next_step_id
```

当前项目中已有的自定义 action：

| action                              | 说明           |
| ----------------------------------- | -------------- |
| `action_lookup_order_status`        | 查询订单状态。 |
| `action_lookup_logistics`           | 查询物流信息。 |
| `action_recommend_similar_products` | 推荐相似商品。 |

示例：

```yaml
- id: lookup_order_status
  type: action
  action: action_lookup_order_status
  next: show_order_status
```

自定义 action 通常负责查询或处理业务数据，后续再用 `action_response` 把结果回复给用户。

#### 3.5.4 collect step 的引入

##### 3.5.4.1 使用基础语法写退单流程

先只使用前面讲过的基础语法，实现一个退单流程。

```yaml
flows:
  refund_request:
    name: 退款申请
    description: 帮用户提交退款申请，收集订单号和退款原因。
    steps:
      - id: start
        type: start
        next: ask_order_number

      - id: ask_order_number
        type: action
        action: action_response
        args:
          text: "请告诉我你的订单号。"
        next: listen_order_number

      - id: listen_order_number
        type: action
        action: action_listen
        next: ask_refund_reason

      - id: ask_refund_reason
        type: action
        action: action_response
        args:
          text: "请简单说一下退款原因。"
        next: listen_refund_reason

      - id: listen_refund_reason
        type: action
        action: action_listen
        next: refund_submitted

      - id: refund_submitted
        type: action
        action: action_response
        args:
          text: "好的，订单{{ slots.order_number }}的退款申请已提交，原因是：{{ slots.refund_reason }}。后续会尽快为你处理。"
        next: end

      - id: end
        type: end
        next: []
```

这个 flow 的步骤如下：

| step                   | 说明                   |
| ---------------------- | ---------------------- |
| `ask_order_number`     | 询问订单号。           |
| `listen_order_number`  | 等待用户输入订单号。   |
| `ask_refund_reason`    | 询问退款原因。         |
| `listen_refund_reason` | 等待用户输入退款原因。 |
| `refund_submitted`     | 回复退单申请已提交。   |

##### 3.5.4.2 暴露重复问题

上面的配置可以表达退单流程，但收集 slot 的步骤写得很重复。

收集订单号时，需要：

1. `action_response` 问用户订单号。
2. `action_listen` 等用户回答。

收集退款原因时，也需要：

1. `action_response` 问用户退款原因。
2. `action_listen` 等用户回答。

也就是说，每收集一个 slot，都要重复写一组“问 + 等”的结构。

如果一个业务要收集 5 个字段，就要重复写 5 组类似配置。flow 会变得又长又啰嗦。

真正的业务意图其实是：

| 想表达的业务含义   | 不想重复写的细节 |
| ------------------ | ---------------- |
| 我要收集订单号。   | 怎么问、怎么等。 |
| 我要收集退款原因。 | 怎么问、怎么等。 |

因此，需要引入一个新的 step type：`collect = 问 + 等`。

##### 3.5.4.3 引入 collect step

`collect` step 用来表达“当前流程需要某个 slot”。

语法：

```yaml
- id: step_id
  type: collect
  slot_name: 具体的slot_name
  response:
    text: "询问用户的话"
  next: next_step_id
```

字段说明：

| 字段        | 说明                            |
| ----------- | ------------------------------- |
| `id`        | step 唯一标识。                 |
| `type`      | 固定写 `collect`。              |
| `slot_name` | 要收集的 slot 名称。            |
| `response`  | slot 缺失时，用什么话询问用户。 |
| `next`      | slot 已具备后，进入哪个 step。  |

示例：

```yaml
- id: ask_order_number
  type: collect
  slot_name: order_number
  response:
    text: "请告诉我你的订单号。"
  next: ask_refund_reason
```

含义：

| 情况                    | 行为                             |
| ----------------------- | -------------------------------- |
| `order_number` 已经有值 | 直接进入 `ask_refund_reason`。   |
| `order_number` 没有值   | 询问用户订单号，并等待用户输入。 |

##### 3.5.4.4 CollectSystemFlow 定义

`collect` 之所以能省掉“问 + 等”的重复配置，是因为系统定义了一个专门的 `CollectSystemFlow`。

它的 flow ID 是 `system_collect_information`。

真实配置如下：

```yaml
flows:
  system_collect_information:
    description: Flow for asking the user for a slot value during a collect step
    name: collect information
    steps:
      - id: start
        type: start
        next: ask

      - id: ask
        type: action
        action: action_response
        args: context.response
        next: listen

      - id: listen
        type: action
        action: action_listen
        next: end

      - id: end
        type: end
        next: []
```

这里最关键的是：

```yaml
args: context.response
```

它表示：`action_response` 的参数整体来自 `context.response`。

例如业务 flow 中有这样一个完整的 `collect` step：

```yaml
- id: ask_order_number
  type: collect
  slot_name: order_number
  response:
    text: "请告诉我你的订单号。"
  next: ask_refund_reason
```

其中的 `response` 部分会被放入系统上下文。进入 `system_collect_information` 时，`context.response` 就相当于：

```yaml
text: "请告诉我你的订单号。"
```

所以：

```yaml
args: context.response
```

等价于把这个 collect step 中的 `response` 整体替换成 `action_response` 的 `args`。

这样，`system_collect_information` 就可以复用同一套“回复 + 等待”逻辑，而具体问什么由业务 flow 的 collect step 决定。

##### 3.5.4.5 引入 collect 后的退单流程示例

有了 `collect` 后，退单 flow 可以写成：

```yaml
flows:
  refund_request:
    name: 退款申请
    description: 帮用户提交简单的退款申请，收集订单号和退款原因。
    steps:
      - id: start
        type: start
        next: ask_order_number

      - id: ask_order_number
        type: collect
        slot_name: order_number
        response:
          text: "请告诉我你的订单号。"
        next: ask_refund_reason

      - id: ask_refund_reason
        type: collect
        slot_name: refund_reason
        response:
          text: "请简单说一下退款原因。"
        next: refund_submitted

      - id: refund_submitted
        type: action
        action: action_response
        args:
          text: "好的，订单{{ slots.order_number }}的退款申请已提交，原因是：{{ slots.refund_reason }}。后续会尽快为你处理。"
        next: end

      - id: end
        type: end
        next: []
```

对比基础版本：

| 基础版本                             | collect 版本                                       |
| ------------------------------------ | -------------------------------------------------- |
| 每个 slot 都要写 `action_response`。 | 每个 slot 只写一个 `collect`。                     |
| 每个 slot 都要写 `action_listen`。   | 等待逻辑由 `system_collect_information` 统一处理。 |
| 配置更关注交互细节。                 | 配置更关注业务需要什么信息。                       |

### 3.6 next：步骤之间怎么连

`next` 用来声明当前 step 执行完成后进入哪个 step。

#### 3.6.1 静态跳转

最简单的写法是直接指定下一个 step：

```yaml
next: next_step_id
```

示例：

```yaml
- id: start
  type: start
  next: ask_order_number
```

#### 3.6.2 条件跳转

如果下一步要根据条件决定，可以使用条件分支。

语法：

```yaml
next:
  - if: "条件表达式1"
    then: step_a
  - if: "条件表达式2"
    then: step_b
  - else: step_c
```

字段说明：

| 字段   | 说明                            |
| ------ | ------------------------------- |
| `if`   | 条件表达式。                    |
| `then` | 条件成立时进入的 step。         |
| `else` | 前面条件都不成立时进入的 step。 |

示例：

```yaml
- id: start
  type: start
  next:
    - if: "slots.get('product_id')"
      then: respond
    - else: missing_product_context
```

这个配置表示：

| 条件                      | 下一步                           |
| ------------------------- | -------------------------------- |
| `slots` 中有 `product_id` | 进入 `respond`。                 |
| 否则                      | 进入 `missing_product_context`。 |

条件表达式可以读取：

| 名称      | 说明             |
| --------- | ---------------- |
| `slots`   | 当前业务字段。   |
| `context` | 当前系统上下文。 |
| `flow_id` | 当前 flow ID。   |
| `step_id` | 当前 step ID。   |

多个条件会按顺序判断，命中第一个成立的分支。

### 3.7 其余 SystemFlow

SystemFlow 用来描述系统级交互。

除了前面讲过的 `system_collect_information`，项目中还有以下 SystemFlow。

#### 3.7.1 system_task_started

作用：新任务开始时，告诉用户当前先处理哪个任务。

```yaml
system_task_started:
  description: Flow for acknowledging that a new task has started
  name: task started acknowledgement
  steps:
    - id: start
      type: start
      next: acknowledge

    - id: acknowledge
      type: action
      action: action_response
      args:
        mode: static
        text: "好的，我们先处理{{ context.started_flow_name }}。"
      next: end

    - id: end
      type: end
      next: []
```

#### 3.7.2 system_task_resumed

作用：恢复暂停任务时，告诉用户继续处理刚才的任务。

```yaml
system_task_resumed:
  description: Flow for acknowledging that a paused task has been resumed
  name: task resumed acknowledgement
  steps:
    - id: start
      type: start
      next: acknowledge

    - id: acknowledge
      type: action
      action: action_response
      args:
        mode: static
        text: "好的，我们继续刚才的{{ context.resumed_flow_name }}。"
      next: end

    - id: end
      type: end
      next: []
```

#### 3.7.3 system_task_interrupted

作用：当前任务被打断时，告诉用户先把旧任务放一放。

这个 flow 用到了`context.interrupted_flow_name`：回复被打断的任务名称。

```yaml
system_task_interrupted:
  description: Flow for acknowledging that the current task has been interrupted
  name: task interrupted acknowledgement
  steps:
    - id: start
      type: start
      next: acknowledge

    - id: acknowledge
      type: action
      action: action_response
      args:
        mode: static
        text: "好的，我们先把{{ context.interrupted_flow_name }}放一放，先处理{{ context.started_flow_name }}。"
      next: end

    - id: end
      type: end
      next: []
```

#### 3.7.4 system_task_canceled

作用：当前任务被取消时，告诉用户已取消。

```yaml
system_task_canceled:
  description: Flow for acknowledging that the current task was canceled
  name: task canceled acknowledgement
  steps:
    - id: start
      type: start
      next: acknowledge


    - id: acknowledge
      type: action
      action: action_response
      args:
        mode: static
        text: "好的，{{ context.canceled_flow_name }}先帮你取消。"
      next: end

    - id: end
      type: end
      next: []
```

#### 3.7.5 system_cannot_handle

作用：系统无法处理当前请求时，给出兜底回复。

这个 flow 会根据 `context.reason` 选择不同回复。

分支含义：

| reason                   | 进入 step                | 说明                         |
| ------------------------ | ------------------------ | ---------------------------- |
| `clarification_rejected` | `clarification_rejected` | 澄清失败，引导用户重新说明。 |
| `not_supported`          | `not_supported`          | 当前能力未接入。             |
| `no_relevant_answer`     | `no_relevant_answer`     | 没有找到合适答案。           |
| 其他情况                 | `ask_rephrase`           | 请用户换个说法。             |

```yaml
system_cannot_handle:
  description: Flow for handling requests the assistant cannot support
  name: cannot handle request
  steps:
    - id: start
      type: start
      next:
        - if: "context.get('reason') == 'clarification_rejected'"
          then: clarification_rejected
        - if: "context.get('reason') == 'not_supported'"
          then: not_supported
        - if: "context.get('reason') == 'no_relevant_answer'"
          then: no_relevant_answer
        - else: ask_rephrase
    - id: clarification_rejected
      type: action
      action: action_response
      args:
        mode: rephrase
        text: "看来我刚才理解偏了。你可以重新说一下你想查订单、查物流，还是申请退款吗？"
        prompt: |
          你是一个中文电商客服助手，语气自然、友好、简洁。
          请基于下面的建议回复，生成一句更自然的中文回复，保持原意，不要扩写。
          对话上下文：
          {history}
          用户最后一句：
          用户：{user_message}
          建议回复：{current_response}
          改写后的回复：
      next: end

    - id: not_supported
      type: action
      action: action_response
      args:
        mode: rephrase
        text: "我理解你的意思，不过这个能力目前还没有接入。"
        prompt: |
          你是一个中文电商客服助手，语气自然、友好、简洁。
          请基于下面的建议回复，生成一句更自然的中文回复，保持原意，不要扩写。
          对话上下文：
          {history}
          用户最后一句：
          用户：{user_message}
          建议回复：{current_response}
          改写后的回复：
      next: end

    - id: no_relevant_answer
      type: action
      action: action_response
      args:
        mode: rephrase
        text: "我暂时没有查到合适的信息。你可以换个说法，或者告诉我更具体一点的商品或订单信息。"
        prompt: |
          你是一个中文电商客服助手，语气自然、友好、简洁。
          请基于下面的建议回复，生成一句更自然的中文回复，保持原意，不要扩写。
          对话上下文：
          {history}
          用户最后一句：
          用户：{user_message}
          建议回复：{current_response}
          改写后的回复：
      next: end

    - id: ask_rephrase
      type: action
      action: action_response
      args:
        mode: rephrase
        text: "抱歉，我这边没有完全听明白。你可以再具体说一下你想处理什么电商问题吗？"
        prompt: |
          你是一个中文电商客服助手，语气自然、友好、简洁。
          请基于下面的建议回复，生成一句更自然的中文回复，保持原意，不要扩写。
          对话上下文：
          {history}
          用户最后一句：
          用户：{user_message}
          建议回复：{current_response}
          改写后的回复：
      next: end

    - id: end
      type: end
      next: []
```

### 3.8 Flow 语法总结

#### 3.8.1 flow 顶层语法

```yaml
flows:
  flow_id:
    name: 流程名称
    description: 流程说明
    steps: []
```

#### 3.8.2 step 通用语法

```yaml
- id: step_id
  type: step_type
  next: next_step_id
```

#### 3.8.3 step type 汇总

| type      | 作用      | 常见字段                                      |
| --------- | --------- | --------------------------------------------- |
| `start`   | flow 起点 | `id`、`type`、`next`                          |
| `end`     | flow 终点 | `id`、`type`、`next`                          |
| `action`  | 执行动作  | `id`、`type`、`action`、`args`、`next`        |
| `collect` | 收集 slot | `id`、`type`、`slot_name`、`response`、`next` |

#### 3.8.4 action 汇总

| action            | 作用                               |
| ----------------- | ---------------------------------- |
| `action_response` | 回复用户，支持变量引用。           |
| `action_listen`   | 控制信号，表示等待用户下一轮输入。 |
| 自定义 action     | 执行业务逻辑。                     |

#### 3.8.5 next 汇总

静态跳转：

```yaml
next: step_id
```

条件跳转：

```yaml
next:
  - if: "条件表达式"
    then: step_a
  - else: step_b
```

#### 3.8.6 变量引用汇总

| 写法                | 说明             |
| ------------------- | ---------------- |
| `{{ slots.xxx }}`   | 引用业务 slot。  |
| `{{ context.xxx }}` | 引用系统上下文。 |

#### 3.8.7 SystemFlow 汇总

| SystemFlow                       | 作用                             |
| -------------------------------- | -------------------------------- |
| `system_collect_information`     | 收集 slot 时追问用户并等待输入。 |
| `system_task_started`            | 新任务开始提示。                 |
| `system_task_resumed`            | 任务恢复提示。                   |
| `system_task_interrupted`        | 任务被打断提示。                 |
| `system_task_canceled`           | 任务取消提示。                   |
| `system_cannot_handle`(优化掉了) | 无法处理请求时的兜底回复。       |

### 3.9 YAML 的嵌套层次

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/03-YAML的嵌套层次.png" style="zoom: 50%;" />

理解了 YAML 的层次，我们就能"照葫芦画瓢"地定义对象——YAML 有几层，对象就有几层。

## 第4章 数据模型的定义

### 4.1 数据模型总览

```
atguigu/task/flow/
├── links.py      ← 连接(边):StaticLink / ConditionalLink / FallbackLink
├── steps.py      ← 步骤(节点):StartFlowStep / CollectSlotStep / ...
└── flows.py     ← 流程容器:Flow / FlowsList / FlowSlot
```

它们的关系可以用一张类图概括：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/03-边、节点、容器之间关系.png" alt="03-边、节点、容器之间关系" style="zoom: 33%;" />

把流程看成一张**有向图**：

- **节点 = FlowStep**（步骤，"做什么"）
- **边 = FlowStepLink**（连接，"接下来去哪"）

我们从最小的零件开始，由内向外定义：先 links（边），再 steps（节点），再 models（容器），最后 loader（加载器）。

### 4.2 links.py：步骤之间的连接

步骤之间的连接是流程图里的"边"。

#### 4.2.1 类图

连接是流程图里的"边"，描述从一个步骤怎么走到下一个。

```mermaid
classDiagram
    class FlowStepLink {
        +str target
    }
    
    class FlowStepStaticLink {
    }
    
    class FlowStepConditionalLink {
        +str condition
    }
    
    class FlowStepFallbackLink {
    }
    
    FlowStepLink <|-- FlowStepStaticLink
    FlowStepLink <|-- FlowStepConditionalLink
    FlowStepLink <|-- FlowStepFallbackLink

```

#### 4.2.2 模型定义

创建文件 `atguigu/task/flow/links.py`

```python
# atguigu/task/flow/links.py

from pydantic import BaseModel


class FlowStepLink(BaseModel):
    """
    模版边（基类）
    """
    target: str  # 下一步的stepID


class StaticLink(FlowStepLink):
    """
    静态边
    对应 next 的值是字符串
    """
    pass


class ConditionalLink(FlowStepLink):
    """
    对应的是 next:[{if:"xxxxxx",then:step_id}]
    """
    condition: str  # 接收if 中的 xxxxx


class FallbackLink(FlowStepLink):
    """"
      对应的是 next:[{else:step_id}]
    """
    pass

```

#### 4.2.3 字段说明

| 类                | 字段        | 含义                                             |
| ----------------- | ----------- | ------------------------------------------------ |
| `FlowStepLink`    | `target`    | 目标步骤的 id                                    |
| `ConditionalLink` | `condition` | 条件表达式字符串，如 `"slots.get('product_id')"` |

`StaticLink` 和 `FallbackLink` 没有额外字段，只继承一个 `target`。

它们的区别纯粹是**语义**上的：`StaticLink` 表示"必走"，`FallbackLink` 表示"前面条件都不满足必走"。

### 4.3 steps.py：流程的步骤

步骤是流程图里的"节点"。这是本节最核心的文件。

创建文件：`atguigu/task/flow/steps.py`

#### 4.3.1 响应模型

在`steps.py`中添加如下定义：

```python
class ResponseDefinition(BaseModel):
    """
    响应的模式:静态模式(static) 改写模式(rephrase)
    """
    model: str = "static"  # 响应模式
    text: str  # 必填字段
    prompt: str | None = None
```

`ResponseDefinition` 描述"一句回复怎么生成"：

| 字段     | 含义                                                       |
| -------- | ---------------------------------------------------------- |
| `mode`   | 回复模式，`static`（原样输出）或 `rephrase`（让 LLM 改写） |
| `text`   | 回复文本                                                   |
| `prompt` | 当 `mode=rephrase` 时，给 LLM 的改写提示                   |

#### 4.3.2 步骤类型枚举

在`steps.py`中添加如下定义：

```python
class FlowStepType(Enum):
    """
    流程的步骤类型
    """
    START = "start"
    END = "end"
    ACTION = "action"
    COLLECT = "collect"
```

#### 4.3.3 FlowStep 基类

在`steps.py`中添加如下定义：

```python
class FlowStep(BaseModel):
    """
    流程的步骤 模版
    """
    id: str  # 步骤ID
    type: FlowStepType  # 步骤类型
    next: List[FlowStepLink] = []  # 下一步
    description: str = ""  # 步骤描述
```

| 字段          | 含义                                    |
| ------------- | --------------------------------------- |
| `id`          | 步骤唯一标识，如 `ask_order_number`     |
| `type`        | 步骤类型（枚举）                        |
| `next`        | 出边列表，元素是上一节的 `FlowStepLink` |
| `description` | 步骤描述（可选）                        |

#### 4.3.4 FlowStep 子类

在`steps.py`中添加如下定义：

```python
class StartFlowStep(FlowStep):
    """
    流程步骤：开始
    """
    type: FlowStepType = FlowStepType.START
    pass

class EndFlowStep(FlowStep):
    """
    流程步骤：结束
    """
    type: FlowStepType = FlowStepType.END
    pass

class ActionFlowStep(FlowStep):
    """
    流程步骤：执行某一个动作
    """
    type: FlowStepType = FlowStepType.ACTION
    action: str  # 行动的名字（action_listen:哨兵-等你/action_response:告诉你/action_xxxx:找东西 ）
    args: dict | str = {}  # 动作参数，选填

class CollectFlowStep(FlowStep):
    """
    流程步骤：收集某个槽位信息
    """
    type: FlowStepType = FlowStepType.COLLECT
    slot_name: str  # 必填字段
    response: ResponseDefinition  # 必填字段（填写的槽位）
```

#### 4.3.5 YAML字典转成对象

##### 类型注册表

用"字符串 → 类"的映射表实现多态分发。

在`steps.py`中添加如下定义：

```python
# 多态分发
STEP_TYPE_TO_CLASS = {
    "start": StartFlowStep,
    "action": ActionFlowStep,
    "collect": CollectFlowStep,
    "end": EndFlowStep
}
```

##### from_dict：按 type 分发

在`steps.py`的`FlowStep`类中添加如下方法定义：

```python
@classmethod
def from_dict(cls, step_data: dict[str, Any]) -> "FlowStep":
    step_type = step_data['type']
    clz = STEP_TYPE_TO_CLASS[step_type]
    return clz.from_dict(step_data)
```

它读出 `type` 字段，在 `STEP_TYPE_TO_CLASS` 中找到对应的子类，再交给子类自己的 `from_dict` 。这是一个典型的**多态分发**。

##### base_fields：抽取公共字段

在`steps.py`的`FlowStep`类中添加如下方法定义：

```python
@staticmethod
def base_fields(base_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    加载各个步骤的基础字段
    :param base_data: 各个步骤的字典数据
    :return:
    """
    return {
        "id": base_data['id'],
        "type": FlowStepType(base_data['type']),
        "description": base_data.get('description', ''),
        "next": FlowStep.build_links(base_data['next'])
    }
```

所有子类都有 `id` / `type` / `description` / `next` 这四个公共字段。把它们的抽取逻辑集中在这里。

##### build_links：把 next 翻译成连接列表

在`steps.py`的`FlowStep`类中添加如下方法定义：

```python
@staticmethod
def build_links(link_data: str | list[Dict[str, Any]]) -> List[FlowStepLink]:
    # 1. next是字符串
    if isinstance(link_data, str):
        return [StaticLink(target=link_data)]

    # 2. next是列表
    else:
        links = []
        for link_dict in link_data:
            if "if" in link_dict:
                links.append(ConditionalLink(condition=link_dict['if'], target=link_dict['then']))
            else:
                links.append(FallbackLink(target=link_dict['else']))
        return links
```

这就是`next` 写法的翻译规则：

| YAML 的 next              | 翻译结果                                     |
| ------------------------- | -------------------------------------------- |
| 字符串 `ask_order_number` | `[StaticLink(target="ask_order_number")]`    |
| 列表里带 `if` / `then`    | `ConditionalLink(target=then, condition=if)` |
| 列表里带 `else`           | `FallbackLink(target=else)`                  |

#### 4.3.6 完善四个子类

在`steps.py`中完善如下类的定义：

##### StartFlowStep

```python
class StartFlowStep(FlowStep):
    """
    流程步骤：开始
    """
    type: FlowStepType = FlowStepType.START

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "StartFlowStep":
        return cls(**FlowStep.base_fields(step_data))
```

起点步骤没有任何额外字段，直接用公共字段构造。

##### EndFlowStep

```python
class EndFlowStep(FlowStep):
    """
    流程步骤：结束
    """
    type: FlowStepType = FlowStepType.END

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "EndFlowStep":
        return cls(**FlowStep.base_fields(step_data))
```

起点步骤没有任何额外字段，直接用公共字段构造。

##### ActionFlowStep

```python
class ActionFlowStep(FlowStep):
    """
    流程步骤：执行某一个动作
    """
    type: FlowStepType = FlowStepType.ACTION
    
    action: str = "" # 行动的名字（action_listen:哨兵-等你/action_response:告诉你/action_xxxx:找东西 ）
    args: dict | str = {}  # 动作参数，选填

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "ActionFlowStep":
        return cls(**FlowStep.base_fields(step_data),
                   action=step_data['action'],
                   args=step_data.get('args', {}))
```

| 字段     | 含义                                 |
| -------- | ------------------------------------ |
| `action` | 要执行的动作名，如 `action_response` |
| `args`   | 传给动作的参数                       |

##### CollectSlotStep

```python
class CollectFlowStep(FlowStep):
    """
    流程步骤：收集某个槽位信息
    """
    type: FlowStepType = FlowStepType.COLLECT
    
    slot_name: str  # 必填字段
    response: ResponseDefinition  # 必填字段（填写的槽位）

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "CollectFlowStep":
        return cls(
            **FlowStep.base_fields(step_data),
            slot_name=step_data['slot_name'],
            response=ResponseDefinition(**step_data['response'])
        )
```

| 字段        | 含义                                        |
| ----------- | ------------------------------------------- |
| `slot_name` | 要收集的槽位名，对应 `slots` 块里的某个 key |
| `response`  | 收集时，向用户发的提示                      |

#### 4.3.7 小结

##### 模块

这个文件包含的模块总结如下：

| 模块名称               | 类型         | 说明                      | 关键字段/方法                                                |
| ---------------------- | ------------ | ------------------------- | ------------------------------------------------------------ |
| **ResponseDefinition** | Pydantic模型 | 响应定义（静态/改写模式） | `model`, `text`, `prompt`                                    |
| **FlowStepType**       | 枚举类       | 流程步骤类型枚举          | `START`, `END`, `ACTION`, `COLLECT`                          |
| **FlowStep**           | 基类模型     | 流程步骤基础模板          | `id`, `type`, `next`, `description`<br>`from_dict()`, `base_fields()`, `build_links()` |
| **StartFlowStep**      | 子类模型     | 开始步骤                  | 继承基类，实现`from_dict()`                                  |
| **EndFlowStep**        | 子类模型     | 结束步骤                  | 继承基类，实现`from_dict()`                                  |
| **ActionFlowStep**     | 子类模型     | 行动步骤                  | `action`, `args`<br>实现`from_dict()`                        |
| **CollectFlowStep**    | 子类模型     | 收集槽位步骤              | `slot_name`, `response`<br>实现`from_dict()`                 |
| **STEP_TYPE_TO_CLASS** | 字典映射     | 步骤类型到类的映射表      | `"start"` → `StartFlowStep`<br>`"action"` → `ActionFlowStep`<br>`"collect"` → `CollectFlowStep`<br>`"end"` → `EndFlowStep` |

**核心功能说明：**

1. **工厂模式**：通过 `FlowStep.from_dict()` 和 `STEP_TYPE_TO_CLASS` 实现根据类型字符串自动创建对应的步骤对象

2. **链接构建**：`build_links()` 方法支持两种格式：
   - 字符串格式 → 转换为 `StaticLink`
   - 列表格式 → 根据条件转换为 `ConditionalLink` 或 `FallbackLink`

3. **继承体系**：所有具体步骤类都继承自 `FlowStep`，共享基础字段和逻辑

##### 类图

```mermaid
classDiagram
    class ResponseDefinition {
        +str model = "static"
        +str text
        +str|None prompt = None
    }

    class FlowStepType {
        <<enumeration>>
        +START = "start"
        +END = "end"
        +ACTION = "action"
        +COLLECT = "collect"
    }

    class FlowStep {
        +str id
        +FlowStepType type
        +List[FlowStepLink] next = []
        +str description = ""
        +from_dict(dict[str, Any]) FlowStep$
        +base_fields(Dict[str, Any]) Dict[str, Any]$
        +build_links(str|list[Dict[str, Any]]) List[FlowStepLink]$
    }

    class StartFlowStep {
        +from_dict(dict[str, Any]) StartFlowStep$
    }

    class EndFlowStep {
        +from_dict(dict[str, Any]) EndFlowStep$
    }

    class ActionFlowStep {
        +str action = ""
        +dict args
        +from_dict(dict[str, Any]) ActionFlowStep$
    }

    class CollectFlowStep {
        +str slot_name
        +ResponseDefinition response
        +from_dict(dict[str, Any]) CollectFlowStep$
    }

    %% 继承关系
    FlowStep <|-- StartFlowStep : 继承
    FlowStep <|-- EndFlowStep : 继承
    FlowStep <|-- ActionFlowStep : 继承
    FlowStep <|-- CollectFlowStep  : 继承

    %% 组合关联
    CollectFlowStep --> ResponseDefinition : resposne
    FlowStep o-- FlowStepLink : next

    %% 枚举关联
    FlowStep --> FlowStepType : type

    %% 说明：FlowStepLink及其子类(StaticLink/ConditionalLink/FallbackLink)来自外部links模块，此处只做引用
```

##### 完整的代码

```python
# atguigu/task/flow/steps.py

"""
步骤（节点）设计
"""
from enum import Enum
from typing import List, Dict, Any, Literal, Annotated
from pydantic import BaseModel, Field, TypeAdapter, field_validator
from atguigu.task.flow.links import FlowStepLink, StaticLink, ConditionalLink, FallbackLink


class ResponseDefinition(BaseModel):
    """
    响应的模式:静态模式(static) 改写模式(rephrase)
    """
    model: str = "static"  # 响应模式
    text: str  # 必填字段
    prompt: str | None = None

class FlowStepType(Enum):
    """
    流程的步骤类型
    """
    START = "start"
    END = "end"
    ACTION = "action"
    COLLECT = "collect"

class FlowStep(BaseModel):
    """
    流程模版
    """
    id: str  # 步骤ID
    type: FlowStepType  # 步骤类型
    next: List[FlowStepLink] = []  # 下一步
    description: str = ""  # 步骤描述

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "FlowStep":
        step_type = step_data['type']
        clz = STEP_TYPE_TO_CLASS[step_type]
        return clz.from_dict(step_data)


    @staticmethod
    def base_fields(base_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        加载各个步骤的基础字段
        :param base_data: 各个步骤的字典数据
        :return:
        """
        return {
            "id": base_data['id'],
            "type": FlowStepType(base_data['type']),
            "description": base_data.get('description', ''),
            "next": FlowStep.build_links(base_data['next'])
        }

    @staticmethod
    def build_links(link_data: str | list[Dict[str, Any]]) -> List[FlowStepLink]:
        # 1. next是字符串
        if isinstance(link_data, str):
            return [StaticLink(target=link_data)]

        # 2. next是列表
        else:
            links = []
            for link_dict in link_data:
                if "if" in link_dict:
                    links.append(ConditionalLink(condition=link_dict['if'], target=link_dict['then']))
                else:
                    links.append(FallbackLink(target=link_dict['else']))
            return links


class StartFlowStep(FlowStep):
	"""
    流程步骤：开始
    """
    type: FlowStepType = FlowStepType.START
    
    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "StartFlowStep":
        return cls(**FlowStep.base_fields(step_data))

class EndFlowStep(FlowStep):
    """
    流程步骤：结束
    """
    type: FlowStepType = FlowStepType.END

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "EndFlowStep":
        return cls(**FlowStep.base_fields(step_data))

class ActionFlowStep(FlowStep):
    """
    流程步骤：执行某一个动作
    """
    type: FlowStepType = FlowStepType.ACTION
    
    action: str = "" # 行动的名字（action_listen:哨兵-等你/action_response:告诉你/action_xxxx:找东西 ）
    args: dict | str = {}  # 动作参数，选填

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "ActionFlowStep":
        return cls(**FlowStep.base_fields(step_data),
                   action=step_data['action'],
                   args=step_data.get('args', {}))


class CollectFlowStep(FlowStep):
    """
    流程步骤：收集某个槽位信息
    """
    type: FlowStepType = FlowStepType.COLLECT
    
    slot_name: str  # 必填字段
    response: ResponseDefinition  # 必填字段（填写的槽位）

    @classmethod
    def from_dict(cls, step_data: dict[str, Any]) -> "CollectFlowStep":
        return cls(
            **FlowStep.base_fields(step_data),
            slot_name=step_data['slot_name'],
            response=ResponseDefinition(**step_data['response'])
        )

STEP_TYPE_TO_CLASS = {
    "start": StartFlowStep,
    "action": ActionFlowStep,
    "collect": CollectFlowStep,
    "end": EndFlowStep
}
```

### 4.4 flows.py：流程容器

步骤和连接都有了，接下来定义把它们装起来的容器。

#### 4.4.1 类图

```mermaid
classDiagram
    class FlowSlot {
        +str name
        +str type = "any"
        +str label = ""
        +str description = ""
    }

    class Flow {
        +str id
        +str description = ""
        +List[FlowStep] steps = []
        +List[FlowSlot] slots = []
        +str|None name = None
        +start_step() StartFlowStep|None
        +get_step_by_id(str) FlowStep|None
    }

    class FlowsList {
        +List[Flow] flows = []
        +Dict[str, FlowSlot] slots
        +get_flow_by_id(str) Flow|None
    }

    %% 外部依赖类引用（来自steps模块）
    class FlowStep
    class StartFlowStep
    FlowStep <|-- StartFlowStep

    %% 聚合关系：Flow包含步骤与槽位
    Flow *-- FlowStep : steps
    Flow o-- FlowSlot : slots

    %% FlowsList聚合流程、全局槽位
    FlowsList o-- Flow : flows
    FlowsList o-- FlowSlot : slots

    %% 方法返回依赖
    Flow --> StartFlowStep : start_step返回
    Flow --> FlowStep : get_step_by_id返回
```



#### 4.4.2 模型定义

创建文件 `atguigu/task/flow/flows.py`

```python
# atguigu/task/flow/flows.py

from typing import List, Dict
from pydantic import BaseModel
from atguigu.task.flow.steps import FlowStep, StartFlowStep

class FlowSlot(BaseModel):
    """
    槽位
    """
    name: str  # 槽位的名字
    type: str = "any"  # 槽位的类型
    label: str = ""  # 槽位的标签
    description: str = ""  # 槽位的描述


class Flow(BaseModel):
    """
    流程
    """
    id: str  # 流程的ID
    description: str = ""
    steps: List[FlowStep] = []  # 步骤
    slots: List[FlowSlot] = []  # 槽位
    name: str | None = None  # 流程名字

    def start_step(self) -> StartFlowStep | None:
        """
        返回流程的开始步骤
        :return:
        """
        for step in self.steps:
            if isinstance(step, StartFlowStep):
                return step
        return None

    def get_step_by_id(self, step_id: str) -> FlowStep | None:
        """
        根据步骤ID获取步骤
        :param step_id:
        :return:
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        return None


class FlowsList(BaseModel):
    """
    流程列表
    """
    flows: List[Flow] = []
    slots: Dict[str, FlowSlot] = {}

    def get_flow_by_id(self, flow_id: str) -> Flow | None:
        """
        根据流程ID获取流程
        :param flow_id:
        :return:
        """
        for flow in self.flows:
            if flow.id == flow_id:
                return flow
        return None

```

## 第5章 数据模型加载

创建`atguigu/task/flow/loader.py`，把 YAML 读取到内存中并加载成对象

### 5.1 完整的代码

```python
# atguigu/task/flow/loader.py

from pathlib import Path
from typing import List, Dict, Any

import yaml

from atguigu.task.flow.flows import FlowsList, Flow, FlowSlot
from atguigu.task.flow.steps import FlowStep, CollectFlowStep

"""
yaml --->dict---->数据模型
"""


class FlowLoader:
    """
    流程加载器（加载两个yaml文件）
    """
    def load_many(self, paths: List[Path]) -> FlowsList:
        flows: List[Flow] = []
        slots: Dict[str, FlowSlot] = {}
        for path in paths:
            # 1. 加载单个yaml文件的flow_list
            single_flows_list = self.load(path)
            # 2. 获取单个yaml的flows
            flows.extend(single_flows_list.flows)
            # 3. 检测重复槽位
            duplicate_slot_name = set(slots).intersection(single_flows_list.slots)
            if duplicate_slot_name:  # 去重可选(建议做去重)
                duplicates = ", ".join(sorted(duplicate_slot_name))
                raise ValueError(
                    f"flow定义中存在重复的槽位名称: {duplicates}."
                )
            # 4. 更新
            slots.update(single_flows_list.slots)
        return FlowsList(flows=flows, slots=slots)

    def load(self, path: Path) -> FlowsList:
        """
        加载单个yaml文件
        :param path:
        :return:
        """
        # 1. 读 YAML → dict
        with  open(path, 'r', encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f)

        # 2. 加载slots部分
        slots: Dict[str, FlowSlot] = self._load_slots(data.get('slots', {}))

        # 3. 加载flows部分
        flows = self._load_flows(data.get('flows', {}), slots)

        return FlowsList(slots=slots, flows=flows)

    def _load_slots(self, yaml_slots_data: Dict[str, Any]) -> Dict[str, FlowSlot]:
        """
        加载槽位
        :param yaml_slots_data:
        :return:
        """
        slots = {}
        for slot_name, slot_dict in yaml_slots_data.items():
            slots[slot_name] = FlowSlot(
                name=slot_name,
                **slot_dict
            )

        return slots

    def _load_flows(self, yaml_flows_data: Dict[str, Any], slots_definition: Dict[str, FlowSlot]) -> List[Flow]:
        """
        加载流程
        :param yaml_flows_data:
        :param slots_definition:
        :return:
        """
        flows: List[Flow] = []
        for flow_id, flow_dict in yaml_flows_data.items():
            steps = [FlowStep.from_dict(step) for step in flow_dict.get('steps', [])]
            flows.append(
                Flow(
                    id=flow_id,
                    description=flow_dict.get('description', ''),
                    name=flow_dict.get('name'),
                    steps=steps,
                    slots=self._collect_flow_slots(slots_definition, steps)
                )
            )

        return flows

    def _collect_flow_slots(self, slots_definition: Dict[str, FlowSlot],
                            steps: List[FlowStep]) -> List[FlowSlot]:
        """
        收集流程中的槽位
        :param slots_definition:  业务的所有流程用到的所有槽位定义
        :param steps: 当前流程的所有步骤
        :return: 当前流程要用到的槽位定义
        """
        seen = set()
        flow_slots = []
        for step in steps:

            # 只看收集步骤
            if not isinstance(step, CollectFlowStep):
                continue

            # 去重
            # 流程中可能会在不同的step中有重复的槽位名字
            # (LLM看流程使用的槽位：在同一个流程下 没有必要给LLM两份一样的槽位名字)
            step_slot_name = step.slot_name
            if step_slot_name in seen:
                # 流程中有重复的槽位名字不添加
                continue
            seen.add(step_slot_name)

            # 用 get,查不到不报错
            slot_definition = slots_definition.get(step_slot_name)
            if slot_definition is not None:  # 流程中有的槽位名字对应的槽位定义有
                flow_slots.append(slot_definition)

        return flow_slots


if __name__ == '__main__':
    base_path = Path(__file__).parents[3]
    user_flow_path = base_path / 'flow_config' / 'user_flows.yml'
    system_flow_path = base_path / 'flow_config' / 'system_flows.yml'
    loader = FlowLoader()
    flows_list = loader.load_many([user_flow_path, system_flow_path])
    print(flows_list)

```

### 5.2 load_many：合并多文件

逐个文件调用 `load`，把结果累加。并且**跨文件重复槽位检测**：

`set(slots).intersection(loaded.slots)` 求"已加载的槽位名"和"当前文件的槽位名"的交集。如果交集非空，说明两个文件声明了同名槽位，这通常是人为失误（比如 `user_flows.yml` 和 `system_flows.yml` 都定义了 `order_number`），直接抛 `ValueError` 让问题在**加载期**就暴露，而不是等到运行时槽位被悄悄覆盖、行为诡异才发现。

```python
class FlowLoader:
    """
    流程加载器（加载两个yaml文件）
    """
    def load_many(self, paths: List[Path]) -> FlowsList:
        flows: List[Flow] = []
        slots: Dict[str, FlowSlot] = {}  # set()集合找重复的 set1("order_name","11111")  set2("order_name"，“2222”)----找交集
        for path in paths:
            # 1. 加载单个yaml文件的flow_list
            single_flows_list = self.load(path)
            # 2. 获取单个yaml的flows
            flows.extend(single_flows_list.flows)
            # 3. 检测重复槽位
            duplicate_slot_name = set(slots).intersection(single_flows_list.slots)
            if duplicate_slot_name:  # 去重
                duplicates = ", ".join(sorted(duplicate_slot_name))
                raise ValueError(
                    f"flow定义中存在重复的槽位名称: {duplicates}."
                )
            # 4. 更新
            slots.update(single_flows_list.slots)
        return FlowsList(flows=flows, slots=slots)
```

> **让错误尽早失败**（fail fast）。配置冲突在启动时报错，远好过在用户对话到一半时才出问题。

### 5.3 load：单文件加载三步走

1. `yaml.safe_load` 把文件读成嵌套的 Python 字典
2. 先解析 `slots` 块，得到全局槽位字典
3. 再解析 `flows` 块——注意它要用到第 2 步的 slots（流程要从全局槽位里挑出自己用的）

```python
    def load(self, path: Path) -> FlowsList:
        """
        加载单个yaml文件
        :param path:
        :return:
        """
        # 1. 读 YAML → dict
        with  open(path, 'r', encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f)

        # 2. 加载slots部分
        slots: Dict[str, FlowSlot] = self._load_slots(data.get('slots', {}))

        # 3. 加载flows部分
        flows = self._load_flows(data.get('flows', {}), slots)

        return FlowsList(slots=slots, flows=flows)
```

### 5.4 _load_slots：解析槽位

遍历 YAML 的 `slots` 块，每一项构造一个 `FlowSlot`。注意 `name=slot_name` 是单独传的，因为 YAML 里槽位名是字典的 key，不在值里面。

```python
def _load_slots(self, yaml_slots_data: Dict[str, Any]) -> Dict[str, FlowSlot]:
    """
    加载槽位
    :param yaml_slots_data:
    :return:
    """
    slots = {}
    for slot_name, slot_dict in yaml_slots_data.items():
        slots[slot_name] = FlowSlot(
            name=slot_name,
            **slot_dict
        )

    return slots
```

### 5.5 _load_flows：解析流程

对每个流程做两件事：

1. **构造 steps**：把 `flow_data['steps']` 里每个字典丢给 `FlowStep.from_dict`，通过多态分发，使每个 step 字典变成正确的子类对象
2. **挑出这个流程用到的槽位**：遍历所有 step，只要是 `CollectSlotStep`，就从全局 `slots` 里把它声明要收集的那个槽位捞出来，存进 `flow.slots`

收集到的 `flow.slots`，流程对象里直接带着"我会用到哪些槽位"的清单，后面做意图判断、给 LLM 喂上下文时很方便，不用再查找 step。

```yaml
def _load_flows(self, yaml_flows_data: Dict[str, Any], slots_definition: Dict[str, FlowSlot]) -> List[Flow]:
    """
    加载流程
    :param yaml_flows_data:
    :param slots_definition:
    :return:
    """
    flows: List[Flow] = []
    for flow_id, flow_dict in yaml_flows_data.items():
        steps = [FlowStep.from_dict(step) for step in flow_dict.get('steps', [])]
        flows.append(
            Flow(
                id=flow_id,
                description=flow_dict.get('description', ''),
                name=flow_dict.get('name'),
                steps=steps,
                slots=self._collect_flow_slots(slots_definition, steps)
            )
        )

    return flows
```

### 5.6 _collect_flow_slots：挑出流程用到的槽位

这个方法做的事遍历所有 step，把 `CollectSlotStep` 声明要收集的槽位，从全局槽位字典里捞出来。

**去重（`slot_names` 集合）**：如果一个流程里有多个步骤收集同一个槽位（比如校验失败后重新收集），这里用 `slot_names` 保证每个槽位只进一次。

```python
    def _collect_flow_slots(self, slots_definition: Dict[str, FlowSlot], steps: List[FlowStep]) -> List[FlowSlot]:
        """
        从所有已定义的槽位列表中获取当前流程的所有步骤需要的槽位
        :param slots_definition:
        :param steps:
        :return:
        """
        slot_names = {step.slot_name for step in steps if isinstance(step, CollectFlowStep)}
        return [slots_definition[name] for name in slot_names if name in slots_definition]
```

### 5.7 测试

```python
if __name__ == '__main__':
    base_path = Path(__file__).parents[3]
    user_flow_path = base_path / 'flow_config' / 'user_flows.yml'
    system_flow_path = base_path / 'flow_config' / 'system_flows.yml'
    loader = FlowLoader()
    flows_list = loader.load_many([user_flow_path, system_flow_path])
    print(flows_list)
```

> `Path(__file__).parents[3]` 是从 `loader.py` 往上跳 3 层，定位到项目根目录，再进 `flow_config`。这样不管在哪个目录运行都能找到 yml。

### 5.8 加载流程

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/03-加载流程全景.png" style="zoom:50%;" />



# 四、三层架构

## 第1章 任务目标

我们已经把两类"静态资料"准备好了：

- **领域模型**：`UserMessage` / `BotMessage` / `DialogueState` / `TaskContext` …
- **流程定义**：`FlowsList`

但这些目前都只是"躺在内存里的对象"，没有一个**入口**让外界把消息送进来、把回复拿回去，也没有一个地方把对话状态**存下来、读出来**。这一节就来搭这条主链路。

### 1.1 搭建三层架构

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/04-搭建三层.png" style="zoom: 67%;" />

三层各管一件事：

| 层         | 职责                                                         | 本节实现                         |
| ---------- | ------------------------------------------------------------ | -------------------------------- |
| Web（API） | 收 HTTP 请求、校验参数、转成领域对象、`调用Service`、把结果转回 JSON | ✅ 完整实现                       |
| Service    | 编排一次完整的处理：`调用Repository`加载状态 → `调引擎` → `调用Repository`保存状态 | ✅ 完整实现                       |
| Repository | 把 `DialogueState` 存进数据库、把 `DialogueState` 从数据库读出来 | ✅ 完整实现                       |
| Engine     | 真正的对话逻辑（路由、推流程、调 LLM）                       | ⛔ 本节用**占位实现**，下一节再做 |

### 1.2 为什么 Engine 先放占位

引擎本身很复杂（要做 LLM 路由、流程推进、知识检索），如果等它全部写完再来搭 web，周期太长，也不利于先把"骨架"跑通。

所以这一节我们给引擎写一个**最小占位实现**——它不做任何智能处理，只回复一句固定的话。这样做的好处是：

- 整条链路（HTTP → Service → Repository → DB → 然后原路返回）可以**当场跑通、当场验证**
- 等下一节真正实现引擎时，只要把占位换成真货，上下游一行都不用改

这是一种很常见的开发节奏：**先用假实现打通骨架，再逐个替换成真实现**。

## 第2章 数据模型的两套体系

在写代码之前，必须先想清楚一件事：**这条链路上其实有"两套"数据模型**，它们长得像，但职责完全不同。

### 2.1 两套模型

|      | 领域模型（domain - 对内）                      | 接口模型（schema - 对外）        |
| ---- | ---------------------------------------------- | -------------------------------- |
| 在哪 | `atguigu/domain/messages.py`                   | `atguigu/api/schemas.py`         |
| 基类 | `pydantic.BaseModel`或`@dataclass`             | `pydantic.BaseModel`             |
| 代表 | `UserMessage` / `BotMessage` / `ProcessResult` | `ChatRequest` / `ChatResponse` … |
| 用途 | 系统内部流转                                   | 和外部（HTTP）打交道             |

### 2.2 领域模型补全

`UserMessage` / `BotMessage` 已经有了。这一节补上引擎的**返回值类型** `ProcessResult`，放在 `atguigu/domain/messages.py`中。

```python
# atguigu/domain/messages.py

class ProcessResult(BaseModel):
    sender_id: str  # 用户ID
    message_id: str  # 消息ID(内部生成)
    messages: list[BotMessage]  # 回复消息（机器人回复的所有消息都给前端）
```

| 字段         | 含义                                   |
| ------------ | -------------------------------------- |
| `sender_id`  | 这次回复给哪个用户                     |
| `message_id` | 本轮消息的 id（和请求里的对应）        |
| `messages`   | 机器人本轮要回复的消息列表（可能多条） |

### 2.3 接口模型

在 `atguigu/api/schemas.py`中定义接口模型：

```python
# atguigu/api/schemas.py

from pydantic import BaseModel


class ChatObject(BaseModel):
    """
    聚焦对象：
    对应前端点击订单/商品卡片时带的数据
    """
    type: str # 聚焦对象的类型 order、product
    id: str # 对象 id
    title: str | None = None # 对象标题
    attributes: dict = {} # 扩展属性，默认空字典


class ChatRequest(BaseModel):
    """
    请求对象（用户问题）
    `POST /api/chat` 的请求体
    注意：
    text 和 object 都是可选的，但实际使用中至少要传一个
    文本消息传 text，对象消息传 object
    """
    sender_id: str # 用户唯一标识
    message_id: str | None = None # 客户端消息 id，不传则服务端生成
    text: str | None = None # 文本消息内容
    object: ChatObject | None = None # 对象消息内容


class ChatBotMessage(BaseModel):
    """
    机器人消息
    """
    text: str | None = None
    object: ChatObject | None = None


class ChatResponse(BaseModel):
    """
    响应对象（机器人回复）
    """
    sender_id: str
    message_id: str
    messages: list[ChatBotMessage]


class HistoryMessage(BaseModel):
    """
    历史消息
    """
    role: str  # user or bot
    text: str | None = None
    object: ChatObject | None = None

class HistoryResponse(BaseModel):
    """
    历史消息列表
    `GET /api/chat/history` 的返回体。
    """
    sender_id: str
    messages: list[HistoryMessage]
```

### 2.4 为什么要分两套

直接拿领域模型当接口模型不行吗？分开有几个实在的好处：

1. 职责清晰：接口模型是给前端看的"契约"，领域模型是给业务用的。
2. 内外解耦：两者分开，将来内部重构不会破坏对外契约，反之亦然。

所以 Web 层有一个核心动作就是**翻译**：把进来的 `ChatRequest`（schema）翻成 `UserMessage`（domain），把出去的 `ProcessResult`（domain）翻成 `ChatResponse`（schema）。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/04-核心交互转换.png" style="zoom: 67%;" />

## 第3章 数据库映射：ORM 模型

`DialogueState` 要存进数据库，需要一张表来承载。这一节用 SQLAlchemy 的 ORM 把表映射成 Python 类。

### 3.1 Base 基类

所有 ORM 模型的共同父类，放在 `atguigu/models/base.py`中：

```python
# atguigu/models/base.py

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

`DeclarativeBase` 是 SQLAlchemy 2.x 推荐的声明式基类。所有表模型都继承它，SQLAlchemy 才能统一管理它们的元数据。

### 3.2 DialogueStateRecord

创建 `atguigu/models/dialogue_state.py`：

```python
# atguigu/models/dialogue_state.py

from atguigu.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TEXT


class DialogueStateRecord(Base):
    __tablename__ = "dialogue_states"
    sender_id: Mapped[str] = mapped_column(primary_key=True)
    state_json: Mapped[str] = mapped_column(TEXT, nullable=False, default={})  # 数据库长文本类型
```

| 字段         | 类型                 | 含义                                        |
| ------------ | -------------------- | ------------------------------------------- |
| `sender_id`  | `VARCHAR(255)`，主键 | 用户唯一标识，一个用户一行                  |
| `state_json` | `TEXT`               | 整份 `DialogueState` 序列化后的 JSON 字符串 |

### 3.3 存 整份JSON原因

这是一个值得停下来想的设计取舍。

一份 `DialogueState` 里有活跃任务、暂停任务栈、聚焦对象、会话历史（里面又嵌套了一堆 Turn、消息）……如果按传统关系建模，要拆成好多张表，外键关联一大堆。

而这里只用了**一张表、两列**：用户 id 当主键，剩下整份状态压成一个 JSON 字符串塞进 `state_json`。

|            | 拆多张表                 | 整存 JSON                    |
| ---------- | ------------------------ | ---------------------------- |
| 写入       | 多表事务，复杂           | 一次 upsert                  |
| 读取       | 多表 join                | 一次主键查询                 |
| 单字段查询 | 方便（SQL where）        | 不方便（要解析 JSON）        |
| 适合场景   | 需要按状态字段检索、统计 | 整份读写、不需要按内部字段查 |

我们的场景是"每次处理对话，整份读出来、整份写回去"，从不需要"查所有 active_task 是退款的用户"这种内部字段检索。所以整存 JSON 简单又够用，特别适合学习阶段理解多轮对话。

> 这种"一个聚合整存一份"的思路，和 DDD 里"聚合根作为持久化单元"是一致的。生产环境如果有复杂检索需求，再考虑拆表或上文档数据库。

DDD = 领域驱动设计，核心思想是：

- 🎯 业务优先：先理解业务，再设计代码
- 📦 聚合根作为整体：加载 → 修改 → 保存，保证一致性
- 💾 持久化是细节：先保证业务正确，再优化存储

当前的 DialogueState 设计符合 DDD 理念：

- ✅ 以 sender_id 为聚合根
- ✅ 整个状态整存整取
- ✅ 如果未来有复杂查询需求，再考虑拆表或用 MongoDB

这种做法在对话系统、游戏存档、用户配置等场景非常常见。

### 3.4 基础设施：数据库引擎

ORM 模型有了，还需要一个**异步数据库引擎**和**会话工厂**来真正连数据库。放在 `atguigu/infrastructure/database.py`。（已经实现）

几个要点：

- `engine` 和 `session_factory` 是**模块级全局变量**，整个应用共享一个引擎（引擎内部维护连接池，不能每次请求都新建）
- `init_db_engine()` 在应用启动时调用一次，创建引擎和会话工厂
- `close_db_engine()` 在应用关闭时调用，释放连接池
- `create_async_engine` 用的是**异步**引擎——因为客服后端整体是 async 的，数据库访问也必须异步，否则会阻塞事件循环
- `expire_on_commit=False`：commit 之后对象字段仍可访问，不会被标记过期（异步场景下常用这个设置避免意外的额外查询）

> `settings.database_url` 来自配置（`.env` 里的 `DATABASE_URL`），形如 `mysql+asyncmy://user:pwd@host:3306/db`

## 第4章 Repository 层

**状态的存与取**。Repository 负责把 `DialogueState` 在"内存对象"和"数据库 JSON"之间来回转换。

创建 `atguigu/repository/dialogue_state_repository.py`。

### 4.1 类结构

`DialogueStateRepository` 持有一个 `AsyncSession`（数据库会话）。会话从哪来？由依赖注入传进来（后面讲），Repository 自己不创建会话——它只管用。

```python
# atguigu/repository/dialogue_state_repository.py

import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from atguigu.domain.state import DialogueState
from atguigu.models.dialogue_state import DialogueStateRecord


class DialogueStateRepository:

    def __init__(self, session: AsyncSession):
        self.session = session
```

### 4.2 load_state：读取状态

在 `DialogueStateRepository` 中定义方法

```python
   async def load_state(self, sender_id: str) -> DialogueState:
        """
        读操作
        :return:
        """

        # 1. 定义sql
        sql = select(DialogueStateRecord).where(DialogueStateRecord.sender_id == sender_id)

        # 2. 执行sql
        result = await self.session.execute(sql)

        # 3. 获取结果
        sate = result.scalar_one_or_none()

        if sate:
            # 将 state.state_json 反序列化成一个 DialogueState 对象
            state_dict = json.loads(sate.state_json)
            return DialogueState.model_validate(state_dict)

        return DialogueState(sender_id=sender_id)
```

业务逻辑：

1. 构造一条按 `sender_id` 查询的 SQL
2. `execute` 执行SQL，`scalar_one_or_none()` 取唯一一行
3. **查到了**：`json.loads` 把 JSON 字符串变回字典，再 `DialogueState.model_validate` 还原成对象
4. **没查到**（新用户第一次来）：直接 创建一个空的 `DialogueState` 返回

第 4 步很关键：**新用户没有历史状态，则返回一个全新的空状态**。这样上层逻辑不用区分"老用户/新用户"，拿到的永远是一个可用的 `DialogueState`。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/04-读取状态.png" style="zoom: 67%;" />

### 4.3 save_state：保存状态

```python
async def save_state(self, dialogue_state: DialogueState):
    """
    写操作(插入、修改)
    传统：插入之前先查询该条件（sender_id）对应的记录是否存在，如果不存在 则插入，反之修改
    进阶：负责将插入sql直接升级为修改sql(主键重复机制判断)
    :return:
    """

    # 1. 得到DialogueState的json字符串
    state_json: str = json.dumps(dialogue_state.model_dump(mode="json"))

    # 2. 定义插入的sql语句
    # 注意这里的依赖是：sqlalchemy.dialects.mysql.insert  而不是  sqlalchemy.insert
    insert_stmt = insert(DialogueStateRecord).values(
        sender_id=dialogue_state.sender_id, state_json=state_json
    )

    # 3. 升级update语句的sql
    update_stmt = insert_stmt.on_duplicate_key_update(
        state_json=insert_stmt.inserted.state_json
    )

    # 4. 执行sql
    await  self.session.execute(update_stmt)

    # 5. 提交
    await self.session.commit()
```

业务逻辑：

1. `dialogue_state.model_dump()` 把整份状态变成字典，`json.dumps` 再变成 JSON 字符串
2. 构造一条 `INSERT` 语句
3. `on_duplicate_key_update` 把它变成 **upsert**：如果这个 `sender_id` 已存在，就改成 `UPDATE state_json`
4. 执行 + 提交

### 4.4 为什么用 upsert

`save_state` 会在两种情况下被调用：

- **新用户**：表里还没有这一行 → 应该 `INSERT`
- **老用户**：表里已有这一行 → 应该 `UPDATE`

如果分别判断"先查、再决定 insert 还是 update"，要两次数据库往返，还可能有并发问题。`on_duplicate_key_update` 是 MySQL 的原生能力——**主键冲突时自动转为更新**，一条语句搞定，既简洁又避免竞态。

> 这里用的是 MySQL 方言的 insert  `from sqlalchemy.dialects.mysql import insert` ，
>
> 才有 `on_duplicate_key_update` 方法。标准的 `sqlalchemy.insert` 没有这个方法。

### 4.5 Repository 的本质

Repository 把"业务对象"和"存储格式"之间的转换完全封装起来。上层（Service）只调 `load_state` / `save_state`，完全不知道底层是 MySQL 还是 JSON 还是别的——这就是 Repository 模式的价值：**隔离持久化细节**。

## 第5章 占位 Engine

让链路先跑起来，Service 要调引擎，但引擎这一节暂时不实现。我们写一个**最小占位实现**，只回一句固定的话，让链路能通。

创建 `atguigu/engine/dialogue_engine.py`：

```python
# atguigu/engine/dialogue_engine.py

from atguigu.domain.state import DialogueState
from atguigu.domain.messages import UserMessage, ProcessResult, BotMessage


class DialogueEngine:

    async def process_message(self, dialogue_state: DialogueState,
                            user_message: UserMessage) -> ProcessResult:


        # TODO (用户的消息---->LLM路由(三条轨道的某一条) 执行某一条)

        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=[
                BotMessage(text="我是智能小客服"),
                BotMessage(text="欢迎你来到这里...")
            ]

        )

```

注意它的方法签名和真实引擎**完全一致**：`process_message(self, state, user_message) -> ProcessResult`。这样下一节实现真引擎时，Service 调用它的那行代码一个字都不用改。

> 这就是"面向接口编程"的好处——只要签名（契约）不变，实现可以随时替换。占位实现也是合法实现，它满足了同样的契约。

## 第6章 Service 层

Service 把 Repository 和 Engine 串起来，完成一次对话处理的完整编排。

创建 `atguigu/service/dialogue_service.py`。

### 6.1 完整代码

```python
# atguigu/service/dialogue_service.py

from atguigu.domain.messages import UserMessage, ProcessResult
from atguigu.domain.state import DialogueState
from atguigu.repository.dialogue_state_repository import DialogueStateRepository
from atguigu.engine.dialogue_engine import DialogueEngine


class DialogueService:
    """
    处理对话的业务类
    """

    def __init__(self, dialogue_state_repository: DialogueStateRepository,
                 dialogue_engine: DialogueEngine):
        self.dialogue_state_repository = dialogue_state_repository
        self.dialogue_engine = dialogue_engine

    async def process_message(self, user_message: UserMessage) -> ProcessResult:
        """
        核心处理逻辑(IO：很慢/计算:调用LLM以及执行引擎、比较慢)
        :param user_message:
        :return:
        """
        # 1. 通过 repository 根据 sender_id 加载对话状态(O 阶段)
        dialogue_state: DialogueState = await self.dialogue_state_repository.load_state(user_message.sender_id)
        # 2. 使用 engine 根据对话状态处理最新消息
        process_result: ProcessResult = await self.dialogue_engine.process_message(dialogue_state, user_message)
        # 3. 通过 repository 保存最新的对话状态(I 阶段)
        await self.dialogue_state_repository.save_state(dialogue_state)
        # 4. 返回本轮处理结果
        return process_result

```

### 6.2 三步编排

`process_message` 的逻辑非常清晰，就是三步：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/04-三步编排.png" style="zoom: 67%;" />

| 步骤   | 做什么                                                       |
| ------ | ------------------------------------------------------------ |
| ① 加载 | 按 `sender_id` 从数据库读出这个用户的 `DialogueState`        |
| ② 处理 | 把状态和新消息交给引擎，引擎**就地修改** `state`，返回回复信息 |
| ③ 保存 | 把被引擎改过的 `state` 写回数据库                            |

### 6.3 一个关键设计：I/O 在两端，计算在中间

注意这个编排的形状：

- **①加载** 和 **③保存** 是仅有的两次数据库 I/O，都在 Service 这一层
- 中间的 **②引擎处理** 完全不碰数据库——它只在内存里读改 `state` 对象

这种"**I/O 集中在两端、计算集中在中间**"的设计有两个好处：

1. **引擎是纯计算、无副作用的**——给它一个 state 和 message，它就改 state、返回结果，不依赖数据库。
2. **事务边界清晰**——什么时候读、什么时候写，一目了然，都在 Service 里

> 即便这一节引擎是占位实现，这个结构也已经立住了。下一节换上真引擎，编排逻辑完全不变。

**注意：引擎是"就地修改"state**

第 ② 步有个容易忽略的点：`engine.process_message(dialogue_state, user_message)` 会**直接修改传进去的 `state` 对象**（比如往里面追加 Turn、更新 active_task）。所以第 ③ 步保存的，正是被引擎改过的同一个 `state`。

引擎**不需要**把 state 当返回值传回来——因为 Python 对象是引用传递，Service 手里的 `state` 和引擎改的是同一个对象。引擎的返回值 `ProcessResult` 只装"这一轮要回复什么"，不装状态。

## 第7章 Web 层

### 7.1 依赖注入

创建 `atguigu/api/routers/dependencies.py`。

```yaml
# atguigu/api/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from atguigu.service.dialogue_service import DialogueService
from atguigu.repository.dialogue_state_repository import DialogueStateRepository
from atguigu.engine.dialogue_engine import DialogueEngine

# 注意：必须通过这种方式引入database，需要的时候再获取： database.async_session()
from atguigu.infrastructure import database

# 不要通过这种方式引入async_session，会是一个NoneType
# from atguigu.infrastructure.database import async_session

async def get_session():
    """
    实际流程：
        进入 async with → 打开 session
        yield session → 把 session 交给repository函数使用
        路由函数执行完毕 → 回到 yield 之后
        退出 async with → 自动关闭 session ✅
    :return:
    """
    async with database.async_session() as session:  # 异步方式获取session  获取session要网络传输（耗时的）
        yield session


async def get_dialogue_state_repository(session: AsyncSession = Depends(get_session)):
    """
    创建 DialogueStateRepository 实例

    依赖链执行顺序：
       1. get_session() 打开 session 并 yield
       2. 这里拿到 session，创建 Repository
       3. Repository 被Service使用，Service被路由函数使用
       4. 路由函数返回后，get_session() 继续执行，自动关闭 session
    :param session:
    :return:
    """
    return DialogueStateRepository(session=session)
    # 3. 函数返回后，FastAPI 继续执行 get_session() y


async def get_engine():
    return DialogueEngine()

async def get_dialogue_service(
        dialogue_state_repository: DialogueStateRepository = Depends(get_dialogue_state_repository),
        dialogue_engine: DialogueEngine = Depends(get_engine)
) -> DialogueService:
    return DialogueService(dialogue_state_repository=dialogue_state_repository, dialogue_engine=dialogue_engine)

```

### 7.2 chat 接口

最外层的 Web 层 负责收 HTTP、做模型翻译、调 Service、返回 JSON。

创建 `atguigu/api/routers/chat_router.py`。

```python
import uuid
from fastapi import APIRouter, Depends

from atguigu.api.dependencies import get_dialogue_service
from atguigu.api.schemas import ChatRequest, ChatResponse, ChatBotMessage, ChatObject
from atguigu.domain.messages import ProcessResult, UserMessage, MessageType, FocusedObject
from atguigu.service.dialogue_service import DialogueService

router = APIRouter()


# 定义路由接口

@router.post("/api/chat")
async def chat_endpoint(
        chat_request: ChatRequest,
        dialogue_service: DialogueService = Depends(get_dialogue_service)
) -> ChatResponse:
    # 1. 处理输入接口模型
    user_message = _build_user_message(chat_request)
    # 2. 业务处理
    process_result: ProcessResult = await dialogue_service.process_message(user_message)
    # 3. 处理输出接口模型
    return _build_chat_response(process_result)
```

接口函数本身只有两行：

1. 把请求翻译成 `UserMessage`，交给 service 处理
2. 把 service 返回的 `ProcessResult` 翻译成 `ChatResponse` 返回

`dialogue_service` 从哪来？通过 `Depends(get_dialogue_service)` 注入——这是 FastAPI 的依赖注入，细节留到讲依赖注入那一节，这里先理解为"框架帮我把 service 准备好传进来了"。

### 7.3 请求翻译

**schema → domain**

```python
def _build_user_message(chat_request: ChatRequest) -> UserMessage:
    """
    将请求数据模型转换为领域数据模型 供业务使用
    :param chat_request:
    :return:
    """
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id=chat_request.message_id if chat_request.message_id else str(uuid.uuid4()),
        type=MessageType.TEXT if chat_request.text else MessageType.OBJECT,
        text=chat_request.text,
        object=FocusedObject(
            id=chat_request.object.id,
            type=chat_request.object.type,
            title=chat_request.object.title,
            attributes=chat_request.object.attributes,
        ) if chat_request.object else None
    )
```

几个细节：

- `message_id`：请求没传就用 `uuid4()` 生成一个，保证每条消息都有 id
- `type`：有 `text` 就是 `TEXT` 类型，否则当 `OBJECT` 类型
- `object`：请求带了对象就翻译成 `FocusedObject`，否则为 `None`

### 7.4 响应翻译

**domain → schema**

```python
def _build_chat_response(process_result: ProcessResult) -> ChatResponse:
    return ChatResponse(
        sender_id=process_result.sender_id,
        message_id=process_result.message_id,
        messages=[
            ChatBotMessage(
                text=bot_msg.text,
                object=ChatObject(
                    type=bot_msg.object.type,
                    id=bot_msg.object.id,
                    title=bot_msg.object.title,
                    attributes=bot_msg.object.attributes
                ) if bot_msg.object else None
            )
            for bot_msg in process_result.messages
        ]
    )
```

把 `ProcessResult` 里的每条 `BotMessage`（domain）翻译成 `ChatBotMessage`（schema），组装成 `ChatResponse`。

### 7.5 history 接口（先返回假数据）

```python
@router.get('/api/chat/history')
async def history(sender_id: str) -> HistoryResponse:
    return HistoryResponse(
        sender_id=sender_id,
        messages=[
            HistoryMessage(role='user', text='你好'),
            HistoryMessage(role='bot', text='我不好'),
        ],
    )
```

历史接口这一节先用**写死的假数据**占位。真正的实现要从 `DialogueState.sessions` 里把历史 Turn 取出来翻译成 `HistoryMessage`，这部分逻辑等讲完会话历史的取用方式后再补。先留一个能返回正确结构的桩，前端联调时不至于报错。

### 7.6 应用生命周期管理

#### 7.6.1 代码实现

创建 `atguigu/api/app.py`

```python
# atguigu/api/app.py

"""
定义fastapi实例

"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from atguigu.api.routers.chat_router import router
from atguigu.infrastructure.database import init_db_engine, close_db_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理：
        - 启动时：执行 yield 前的代码（初始化数据库引擎）
        - 运行中：yield 让出控制权，FastAPI 处理请求
        - 关闭时：执行 yield 后的代码（关闭数据库引擎）

    注意：
        - app 参数必须指定，类型为 FastAPI
        - 可通过 app.state 存储全局共享资源（当前未使用）
    """
    # 1. 应用启动
    print("启动服务器...")
    app.state.abc = "abc" # 测试通过 app.state 存储全局共享资源
    
    init_db_engine()  # ← 执行这里，创建数据库连接池

    # 2. 进入 yield
    yield  # ← FastAPI 开始接收请求
    #    用户访问 API...
    #    用户访问 API...

    # 3. 应用关闭（Ctrl+C 或部署平台停止）
    await close_db_engine()  # ← 执行这里，关闭连接池
    print("服务器已关闭")


app = FastAPI(description="电商小二智能客服应用", lifespan=lifespan)

app.include_router(router)
```

生命周期示意图

```
uvicorn启动
    ↓
lifespan() 开始执行
    ↓
初始化资源（init_db_engine）
    ↓
yield →【暂停】======> FastAPI对外提供服务（处理无数请求）
                        ↓
收到停止信号
    ↓
从yield位置继续执行
    ↓
释放资源（close_db_engine）
    ↓
lifespan函数结束
    ↓
服务彻底退出
```

#### 7.6.2 async_session的加载时机

在`dependencies.py`中导入`async_session`必须注意以下事项

```python
# 必须通过这种方式引入database，需要的时候再获取： database.async_session()
from atguigu.infrastructure import database

# 不要通过这种方式引入async_session，会是一个NoneType
# from atguigu.infrastructure.database import async_session
```

因为：`dependencies.py` 的加载（模块导入阶段）远早于 `lifespan` 中 `init_db_engine()` 的执行（服务启动阶段）。下面详细拆解。

```
阶段一：模块导入（uvicorn 启动的那一瞬间）
│
├─ 导入 app.py
│   └─ from ...chat_router import router  → 导入 chat_router
│       └─ 导入 dependencies.py
│           └─ from atguigu.infrastructure.database import async_session
│               └─ 此时 database.py 刚被加载：
│                  async_session = None   ← 模块加载时的初始值！
│               └─ dependencies.py 里的 async_session 这个名字 = None（快照）
│
阶段二：服务运行（lifespan 开始执行）
│
├─ app.py：init_db_engine()
│   └─ database.py：async_session = async_sessionmaker(...)  ← 此时才有真值
│       └─ 但 dependencies.py 里的 async_session 还是 None，不会跟着变

```

#### 7.6.3 扩展：利用app.state挂载对象

扩展：利用 `app.state` 在生命周期挂载全局对象：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):

    print("服务启动....")
    app.state.abc = "abc"
```

在router中访问全局对象：

```python
from fastapi import Request
@router.get("/api/chat/history")
async def get_history(sender_id: str, request: Request) -> HistoryResponse:
    print(request.app.state.abc)
    return Xxx
```

### 7.7 启动程序

创建 `atguigu/main.py`

```python
# atguigu/main.py

"""
启动uvicorn
"""
import uvicorn

from atguigu.conf.config import settings

if __name__ == '__main__':
    uvicorn.run(
        app="api.app:app",
        host=settings.app_host,
        port=settings.app_port
    )
```

### 7.8 Web 层的本质

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/04-Web 层的本质.png" style="zoom: 67%;" />

Web 层做的事可以概括成一句话：**两次自动转换（FastAPI 负责 JSON ↔ schema），两次手动翻译（我们负责 schema ↔ domain），中间夹一次 Service 调用**。

## 第8章 小结

### 8.1 把整条链路串起来

到这里三层都实现了（引擎是占位）。完整看一条 `POST /api/chat` 请求的旅程：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/04-整条链路.png" style="zoom: 67%;" />

这条链路现在是**完全可运行**的：

- 发一条 `{"sender_id": "u1", "text": "你好"}`
- 会真的去数据库 load → 占位引擎处理 → 真的 save → 返回 `（占位回复）我已经收到你的消息了。`
- 再发一条，能在数据库 `dialogue_states` 表里看到 `u1` 这一行的 `state_json`

虽然引擎还没智能，但**整个骨架已经通了、状态持久化已经work了**。下一节把占位引擎换成真引擎，立刻就有真正的对话能力。

### 8.2 这一节实现了什么

| 文件                                          | 内容                                                         |
| --------------------------------------------- | ------------------------------------------------------------ |
| `domain/messages.py`                          | 补上 `ProcessResult`                                         |
| `api/schemas.py`                              | 接口模型 `ChatRequest` / `ChatResponse` / `HistoryResponse` 等 |
| `models/base.py` / `models/dialogue_state.py` | ORM 基类 + `DialogueStateRecord` 表映射                      |
| `repository/dialogue_state_repository.py`     | `load_state` / `save_state`                                  |
| `engine/dialogue_engine.py`                   | **占位**引擎（下节替换）                                     |
| `service/dialogue_service.py`                 | 三步编排：加载 → 处理 → 保存                                 |
| `api/routers/dependencies.py`                 | 依赖注入                                                     |
| `api/routers/chat_router.py`                  | `chat` / `history` 路由 + 模型翻译                           |
| `main.py`、`api/app.py`                       | 启动程序，加载FastAPI、创建数据库连接池                      |

### 8.3 几个好的设计

1. **两套模型分工**：schema（对外）vs domain（对内），Web 层负责在两者间翻译。
2. **Repository 隔离持久化**：上层只调 `load_state` / `save_state`，不关心底层是 MySQL 还是 JSON。新用户自动给空状态，保存用 upsert。
3. **I/O 在两端、计算在中间**：Service 管加载/保存，引擎是纯计算，便于测试、事务边界清晰。
4. **先占位、再替换**：用最小占位引擎打通骨架，契约（方法签名）不变，下一节无缝换真引擎。





# 五、DialogueEngine 与 TurnPlanner的LLM调用

## 第1章 任务目标 

上一节我们把三层架构搭建好了，会话引擎使用了一个**占位实现**。这一节就来把这个占位换成真正的引擎实现，并完成其中最核心的一段：**用 LLM 判断用户意图、为"办业务"这条轨道生成结构化指令**。

### 1.1 引擎要做的三件事

`DialogueEngine.process_message` 是整个对话系统的"大脑入口"。它要做三件事：

1. **理解**：用户这句话到底想干嘛？办业务（查订单、退款）、咨询信息（问政策、问商品），还是闲聊？（调用LLM）
2. **决策**：根据理解的结果，决定走哪条处理轨道，并生成对应的"行动指令"（定义行动指令）
3. **执行**：把指令交给对应的处理器去执行，拿到回复

这一节聚焦前两件事里和**「办业务」轨道**相关的部分。

### 1.2 对话处理流程

`DialogueEngine` 是一轮消息处理的调度中心。

它接收用户消息和 `DialogueState`，判断本轮走哪条处理路径，并返回机器人回复。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/05-对话处理流程.png" style="zoom: 67%;" />

涉及组件如下：

| 组件                | 简要作用                             |
| ------------------- | ------------------------------------ |
| `DialogueState`     | 保存会话、任务、聚焦对象和历史记录。 |
| `Turn`              | 保存本轮用户输入和机器人输出。       |
| `TurnPlanner`       | 根据文本消息和状态生成本轮计划。     |
| `TurnPlanValidator` | 检查本轮计划是否可靠、是否可执行。   |
| `ClarifyResponder`  | 在计划不清晰时生成追问。             |
| `TaskHandler`       | 处理业务任务。                       |
| `KnowledgeHandler`  | 处理知识问答。                       |
| `ChitchatHandler`   | 处理闲聊。                           |

### 1.3 本节内容

这一节是引擎的"全局框架 + 一条轨道的入口"，**不是引擎的全部**。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/05-流程.png" style="zoom: 67%;" />

| 内容                                                   | 本节               |
| ------------------------------------------------------ | ------------------ |
| `process_message` 整体框架（会话准备、开启turn、收尾） | ✅ 实现             |
| 文本消息 → 调 LLM 生成 `TurnPlan`                      | ✅ 实现             |
| `TurnPlanner` 全局框架 + prompt 构建                   | ✅ 详细实现         |
| `Command` / `TurnPlan` 数据模型设计                    | ✅ 实现             |
| task 轨道：把 LLM 结果交给 `TaskHandler`               | ✅ 实现**调用入口** |
| 对象消息（OBJECT）的处理                               | ⛔ 后面讲           |
| 防幻觉校验（`TurnPlanValidator`）                      | ⛔ 后面讲           |
| knowledge / chitchat 两条轨道                          | ⛔ 后面讲           |
| `TaskHandler` 内部（命令处理 + 流程推进）              | ⛔ 后面讲           |

也就是说：我们这一节让"用户发一句『我要退款』→ LLM 输出 `start_flow` 指令 → 进入 task 轨道入口"这条链路通起来，但 task 轨道**内部**怎么推进流程，留到下一节。

## 第2章 消息处理全局框架

先看引擎的入口方法 `process_message`，建立整体骨架，再逐段深入。

### 2.1 引擎的依赖

```python
class DialogueEngine:

    def __init__(
            self,
            turn_planner: TurnPlanner,
            task_handler: TaskHandler
            # knowledge_handler: KnowledgeHandler,
            # chitchat_handler: ChitchatHandler,
            # clarify_responder: ClarifyResponder,
            # turn_plan_validator: TurnPlanValidator
    ) -> None:
        self.turn_planner = turn_planner
        self.task_handler = task_handler
        # self.knowledge_handler = knowledge_handler
        # self.chitchat_handler = chitchat_handler
        # self.clarify_responder = clarify_responder
        # self.turn_plan_validator = turn_plan_validator
```

引擎自己**不干活**，它持有一堆"专员"，自己只负责调度：

| 依赖                  | 职责                                  | 本节是否展开 |
| --------------------- | ------------------------------------- | ------------ |
| `turn_planner`        | 调 LLM，把用户意图变成 `TurnPlan`     | ✅ 本节重点   |
| `task_handler`        | 执行 task 轨道（命令处理 + 流程推进） | 仅调用入口   |
| `knowledge_handler`   | 执行 knowledge 轨道                   | ⛔            |
| `chitchat_handler`    | 执行 chitchat 轨道                    | ⛔            |
| `clarify_responder`   | 校验失败时生成澄清回复                | ⛔            |
| `turn_plan_validator` | 防幻觉校验                            | ⛔            |

### 2.2  消息处理主流程

整个方法分成五个步骤：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/05-消息处理五步.png" style="zoom: 67%;" />

代码实现：修改`atguigu/engine/dialogue_engine.py`的`process_message`方法

```python
async def process_message(self, dialogue_state: DialogueState,
                          user_message: UserMessage) -> ProcessResult:

    # 1. 准备会话
    self._prepare_session(dialogue_state)

    # 2. 开启本轮turn
    self._begin_turn(dialogue_state, user_message)

    # 3. 按消息类型分流
    if user_message.type is MessageType.TEXT:
        messages = await self._handle_text_message(dialogue_state)
    else:
        # 对象消息(本节不实现,后面讲)
        # TODO
        pass

    # 4. 把本轮回复写入turn
    dialogue_state.pending_turn.bot_messages.extend(messages)
    # 提交:turn 进入 session 历史
    dialogue_state.commit_pending_turn()

    # 5. 组装返回结果
    return ProcessResult(
        sender_id=user_message.sender_id,
        message_id=user_message.message_id,
        messages=messages,
    )
```

### 2.3 第一步 准备会话

在`atguigu/engine/dialogue_engine.py`中添加方法：

```python
def _prepare_session(self, dialogue_state: DialogueState) -> None:
    """
    准备会话
    :param dialogue_state:
    :return:
    """

    # 1. 获取当前会话
    session = dialogue_state.current_session()

    # 2. 如果当前会话不存在，则创建一个会话
    if session is None:
        dialogue_state.start_session()
        return

    # 3. 判断会话是否超时
    now = time.time()
    if now - session.last_activity_at > 60 * 60: # 1小时
        # 关闭会话
        dialogue_state.close_current_session()
        # 重置运行时状态
        dialogue_state.reset_runtime_state_for_new_session()
        # 创建会话
        dialogue_state.start_session()
    else:
        # 更新会话（会话续期）
        session.last_activity_at = now
```

这一步决定"这条消息属于哪一段会话"，三种情况：

| 情况                             | 处理                                 |
| -------------------------------- | ------------------------------------ |
| 当前没有会话（新用户/首次对话）  | 直接开一个新会话                     |
| 有会话，但距上次活动超过 60 分钟 | 关掉旧会话，重置运行时状态，开新会话 |
| 有会话，且没超时                 | 复用，更新最后活动时间               |

第二种情况的"重置运行时状态"很关键：超过一小时没说话，再回来时不该还停在一小时前的半截业务任务的流程里，所以把 active_task、paused_tasks、focused_object 都清掉，相当于"重新开始"。（这套方法在 state 那一节都讲过，这里是它们的使用现场。）

### 2.4 第二步：开启本轮对话

在`atguigu/engine/dialogue_engine.py`中添加方法：

```python
def _begin_turn(self, dialogue_state: DialogueState, user_message: UserMessage) -> None:
    """
    开始一个turn
    :param dialogue_state:
    :param user_message:
    :return:
    """
    dialogue_state.begin_turn(user_message)
```

调 `state.begin_turn`，把用户消息装进一个新的 `pending_turn`。回顾 state 那一节讲的"两步提交"：现在先 `begin`，等本轮处理完、回复也填好了，再 `commit`。中途出错就丢掉 pending_turn，不污染历史。

### 2.5 第三步分流：消息类别分流

本节只实现 if 分支

```python
# 3. 按消息类型分流
if user_message.type is MessageType.TEXT:
    messages = await self._handle_text_message(dialogue_state)
else:
    # 对象消息(本节不实现,后面讲)
    # TODO
    pass
```

#### 2.5.1 文本消息的处理

在`atguigu/engine/dialogue_engine.py`中添加方法：

```python
async def _handle_text_message(self, dialogue_state: DialogueState) -> list[BotMessage]:

    # 1. 调 LLM 生成本轮计划（确定任务轨道）
    turn_plan = await self.turn_planner.predict(dialogue_state, self.task_handler.flows)

    # 2. 防幻觉校验(本节不实现,后面讲)
    # TODO

    # 3. 按轨道分发
    if turn_plan.task is not None:
        return await self.task_handler.handle(
            commands=turn_plan.task.commands,
            state=dialogue_state,
        )
    elif turn_plan.knowledge is not None:
        # TODO(本节不实现,后面讲)
        return None
    else:
        # TODO(本节不实现,后面讲)
        return None
```

创建文件 `atguigu/task/handler.py`

```python
# atguigu/task/handler.py

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.command.models import Command
from atguigu.task.flow.flows import FlowsList


class TaskHandler:

    def __init__(self, flows:FlowsList):
        self.flows = flows

    async def handle(self, commands: list[Command], state: DialogueState) -> list[BotMessage]:
        return [BotMessage(text="任务已经处理")]
```

这是引擎的"决策中枢"，三步：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/05-决策中枢.png" style="zoom: 67%;" />

本节我们把注意力放在**第 1 步（怎么调 LLM 生成 TurnPlan）**和**第 3 步的 task 分支（怎么把结果交给 TaskHandler）**。第 2 步校验、knowledge/chitchat 分支，暂不展开。

#### 2.5.2 "伪装校验已通过"

你可能会问：校验都没实现，第 3 步直接用 `turn_plan.task` 安全吗？

短期是安全的——只要 LLM 表现正常、输出合法的 task 计划，第 3 步就能正常走。校验（`TurnPlanValidator`）解决的是 LLM **出幻觉**时的兜底（比如编了一个不存在的 flow）。我们这一节先让"正常路径"通起来，把"异常路径"的防护留到讲校验那一节补。这也符合一贯的开发节奏：**先打通主干，再加固边界**。

### 2.6 第四五两步：收尾

```python
# 4. 把本轮回复写入turn
dialogue_state.pending_turn.bot_messages.extend(messages)
# 提交:turn 进入 session 历史
dialogue_state.commit_pending_turn()

# 5. 组装返回结果
return ProcessResult(
    sender_id=user_message.sender_id,
    message_id=user_message.message_id,
    messages=messages,
)
```

不管走的是文本还是对象、task 还是其它轨道，最后都汇到这里：把生成的回复填进 pending_turn，commit 落到会话历史，再包装成 `ProcessResult` 返回给 Service。

### 2.7 依赖注入

修改 `atguigu/api/routers/dependencies.py` 文件的 `get_engine()` 方法

```python
async def get_engine():
    base_path = Path(__file__).parents[3]
    user_flow_path = base_path / "flow_config" / "user_flows.yml"
    system_flow_path = base_path / "flow_config" / "system_flows.yml"

    loader = FlowLoader()
    flow_list = loader.load_many([user_flow_path, system_flow_path])

    return DialogueEngine(turn_planner = TurnPlanner(), task_handler = TaskHandler(flows=flow_list))
```

## 第3章 Command  和 TurnPlan

### 3.1 概念

`TurnPlanner` 负责根据用户当前输入和对话状态，生成本轮对话计划 `TurnPlan`。

在看 `TurnPlanner` 怎么调 LLM 之前，必须先搞清楚它的**产出物**长什么样——也就是 `TurnPlan` 和 `Command` 这两组数据模型。LLM 的输出会被解析成它们。

### 3.2 JSON

LLM 输出的 `TurnPlan` 可以是一个 JSON 对象，顶层固定包含三个字段：

```json
{
  "task": null,
  "knowledge": null,
  "chitchat": null
}
```

如果用户是在办理业务，填写 `task`：

```json
{
  "task": {
    "commands": [{"command": "start_flow", "flow": "refund_request"}]
  },
  "knowledge": null,
  "chitchat": null
}
```

如果用户是在咨询知识，填写 `knowledge`：

```json
{
  "task": null,
  "knowledge": {
    "intents": ["refund_policy"]
  },
  "chitchat": null
}
```

如果用户是在闲聊，填写 `chitchat`：

```json
{
  "task": null,
  "knowledge": null,
  "chitchat": {}
}
```

如果用户一句话同时表达多个意图，LLM 也可以同时填写多个轨道：

```json
{
  "task": {
    "commands": [
      {"command": "start_flow", "flow": "refund_request"}
    ]
  },
  "knowledge": {
    "intents": ["refund_policy"]
  },
  "chitchat": null
}
```

> 注意：当然多意图 `TurnPlan` 最后会被 `TurnPlanValidator` 认定为当前引擎不能直接执行，然后引导**用户澄清**先处理哪一个。

### 3.3 Command

`task` 轨道的核心是 `commands`。它是 LLM 对"用户想办的业务任务"的**结构化**表达。

先想一个问题:**用户在办业务的过程中,到底会做哪些动作?**

把前面几节出现过的对话场景回顾一遍,会发现用户的动作其实就那么几类:

```
用户:我要退款                    ← 动作:开启一个新业务
用户:订单号是 A001               ← 动作:为当前业务提供一项信息
用户:算了不退了                  ← 动作:放弃当前业务
用户:继续刚才的物流查询          ← 动作:重新拾起之前搁置的业务
```

这四类动作,恰好覆盖了一个任务从"开始"到"结束"会经历的所有用户操作:发起、补充信息、中途放弃、回头继续。我们要做的,就是把用户这些**自然语言动作**,翻译成系统能执行的**结构化指令**——这就是 `Command`。

可以这样理解 `Command`:它是办理业务的"原子指令",一句用户的话,会被 LLM 拆解成一条或多条这样的指令。比如"我要退款,订单号 A001"这一句,就可能被拆成两条：开启退款流程 + 填写订单号。

#### 3.3.1 四种 Command

启动任务：

```json
{"command": "start_flow", "flow": "refund_request"}
```

填写信息(写入槽位)：

```json
{"command": "set_slots", "slots": {"order_number": "10001"}}
```

取消任务：

```json
{"command": "cancel_flow"}
```

恢复任务：

```json
{"command": "resume_flow", "flow": "refund_request"}
```

#### 3.3.2 Command 模型

创建文件 `atguigu/task/command/models.py`:

实现方案：多态分发

```python
# atguigu/task/command/models.py

from typing import Any

from pydantic import BaseModel


class Command(BaseModel):
    command: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Command":
        clz = COMMAND_NAME_TO_CLASS[data["command"]]
        return clz(**data)

class StartFlowCommand(Command):
    flow: str

class SetSlotsCommand(Command):
    slots: dict[str, Any]

class CancelFlowCommand(Command):
    pass


class ResumeFlowCommand(Command):
    flow: str | None = None


COMMAND_NAME_TO_CLASS = {
    "start_flow": StartFlowCommand,
    "set_slots": SetSlotsCommand,
    "cancel_flow": CancelFlowCommand,
    "resume_flow": ResumeFlowCommand,
}


if __name__ == '__main__':
    command = {"command": "set_slots", "slots": {"order_number": "10001"}}
    print(Command.from_dict(command))
```

四种命令,正好对应刚才分析的四类用户动作:

| 命令                | 含义               | 用户说法举例     |
| ------------------- | ------------------ | ---------------- |
| `StartFlowCommand`  | 开启一个新流程     | "我要退款"       |
| `SetSlotsCommand`   | 填写一个或多个槽位 | "订单号是 A001"  |
| `CancelFlowCommand` | 取消当前流程       | "算了不退了"     |
| `ResumeFlowCommand` | 恢复之前挂起的流程 | "继续刚才的退款" |

注意每个子类**携带的参数**也对应着动作的需要:

- 开流程要说清"开哪个",所以 `StartFlowCommand` 带 `flow`
- 填槽位要说清"填什么",所以 `SetSlotsCommand` 带 `slots`
- 取消就是取消当前的,不需要额外信息,所以 `CancelFlowCommand` 是空的
- 恢复要说清"恢复哪个挂起的",所以 `ResumeFlowCommand` 带 `flow`

### 3.4 TurnPlan

#### 3.4.1 三个轨道的 TurnPlan

`task` / `knowledge` / `chitchat` 三个字段告诉我们**走哪条轨道**

```json
"task":      { "commands": [...] }    // 办业务:要执行一串命令
"knowledge": { "intents": [...] }     // 咨询:要命中一个或多个知识意图
"chitchat":  {}                       // 闲聊:什么参数都不需要
```

- 办业务最复杂——用户可能"开流程"、可能"填槽位"、可能"取消",所以要装一串 `commands`
- 咨询次之——只需要知道用户问的是哪类信息,装一个 `intents` 列表
- 闲聊最简单——不需要任何参数,空对象即可

所以这三个字段不能用同一种类型,得各自定义一个数据模型来承载各自的信息。

创建文件 `atguigu/plan/models.py`:

```python
# atguigu/plan/models.py
from atguigu.task.command.models import Command
from pydantic import BaseModel


class TaskTurnPlan(BaseModel):
    commands: list[Command] = [] # 命令

    @classmethod
    def from_dict(cls, data: dict) -> "TaskTurnPlan":
        return cls(commands=[Command.from_dict(command) for command in data["commands"]])

class KnowledgeTurnPlan(BaseModel):
    intents: list[str] = [] # 意图

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeTurnPlan":
        return cls(intents=data["intents"])

class ChitchatTurnPlan(BaseModel):
    pass
```

| 轨道模型            | 装什么                          | 对应 JSON             |
| ------------------- | ------------------------------- | --------------------- |
| `TaskTurnPlan`      | 一个 `Command` 列表（本节重点） | `{"commands": [...]}` |
| `KnowledgeTurnPlan` | 一个意图字符串列表              | `{"intents": [...]}`  |
| `ChitchatTurnPlan`  | 空（闲聊不需要参数）            | `{}`                  |

#### 3.4.2 TurnPlan 模型

`TurnPlan` 就是 LLM 这一轮的"决策结果"，三个字段对应三条轨道，**每个要么是对应的计划对象、要么是 `None`**：

在文件 `atguigu/plan/models.py` 中添加：

```python
# atguigu/plan/models.py

class TurnPlan(BaseModel):
    """
    本轮对话的规划结果
    """
    task: TaskTurnPlan | None = None # 业务任务的轨道
    knowledge: KnowledgeTurnPlan | None = None  # 信息咨询业务轨道
    chitchat: ChitchatTurnPlan | None = None  # 闲聊业务轨道

    @classmethod
    def from_dict(cls, data: dict) -> "TurnPlan":
        return cls(
            task=TaskTurnPlan.from_dict(data["task"]) if data.get("task") is not None else None,
            knowledge=KnowledgeTurnPlan.from_dict(data["knowledge"]) if data.get("knowledge") is not None else None,
            
            # 注意此处直接创建ChitchatTurnPlan对象即可，不需要做反序列化
            chitchat=ChitchatTurnPlan() if data.get("chitchat") is not None else None,
        )
```

| 字段        | 非空表示                            |
| ----------- | ----------------------------------- |
| `task`      | 用户在办业务，里面装一串 `commands` |
| `knowledge` | 用户在咨询信息，里面装 `intents`    |
| `chitchat`  | 用户在闲聊                          |

正常情况下只有一个字段非空。如果 LLM 觉得用户同时表达了多个意图，可能填多个——那就是校验那一节要处理的"多轨道"情况。

### 3.5 从 LLM 输出到对象

假设用户说"我要退款"，LLM 应该输出：

```json
{
  "task": {
    "commands": [
      {"command": "start_flow", "flow": "refund_request"}
    ]
  },
  "knowledge": null,
  "chitchat": null
}
```

经过 `TurnPlan.from_dict`，变成：

```python
TurnPlan(
    task=TaskTurnPlan(commands=[
        StartFlowCommand(command="start_flow", flow="refund_request")
    ]),
    knowledge=None,
    chitchat=None,
)
```

引擎拿到这个 `TurnPlan`，看到 `task` 非空，就把 `commands` 交给 `TaskHandler`。

再看一个用户在流程中途提供信息的例子。用户说"订单号是 A001"：

```json
{
  "task": {
    "commands": [
      {"command": "set_slots", "slots": {"order_number": "A001"}}
    ]
  },
  "knowledge": null,
  "chitchat": null
}
```

经过 `TurnPlan.from_dict`，变成：

```python
TurnPlan(
    task=TaskTurnPlan(commands=[
        SetSlotsCommand(command="set_slots", slots={"order_number": "A001"})
    ]),
    knowledge=None,
    chitchat=None,
)
```

对应以上示例的测试用例，在文件 `atguigu/plan/models.py` 中添加：

```python
# atguigu/plan/models.py

if __name__ == '__main__':


    json_str1 = """
    {
      "task": {
        "commands": [
          {"command": "start_flow", "flow": "refund_request"}
        ]
      },
      "knowledge": null,
      "chitchat": null
    }
    """

    # 转成dict
    turn_plan1 = TurnPlan.from_dict(json.loads(json_str1))
    print(turn_plan1)

    json_str2 = """
    {
      "task": {
        "commands": [
          {"command": "set_slots", "slots": {"order_number": "A001"}}
        ]
      },
      "knowledge": null,
      "chitchat": null
    }
    """
    # 转成dict
    turn_plan2 = TurnPlan.from_dict(json.loads(json_str2))
    print(turn_plan2)
```

## 第4章 提示词

### 4.1 Jinja2 模板引擎介绍

#### 4.1.1 定义

**Jinja2 是 Python 生态最主流、高性能的模板引擎**，用来把「静态模板文件 + Python 数据」拼接生成动态文本（HTML、配置文件、JSON、脚本等）。

由 Flask 框架配套开发。

#### 4.1.2 核心作用：分离数据与页面

后端 Python 只负责查数据、处理逻辑；

模板只写页面结构、展示内容；

Jinja2 自动把数据填充进模板占位符，输出完整文本。

#### 4.1.3 三大基础语法

##### {{变量}}

 输出数据

```jinja
# 这是注释吗？不是
你好，{{ username }}
数字：{{ age }}
转大写：{{ name|upper }}  {# | 过滤器，加工变量 #}
```

##### {% 逻辑代码 %} 

循环、判断、继承（块语句）

```jinja
{% if age >= 18 %}
    成年人
{% else %}
    未成年
{% endif %}

{% for item in list %}
    <li>{{ item }}</li>
{% endfor %}
```

##### {# 注释 #}

模板内注释，渲染后不会输出

#### 4.1.4 核心优势

1. **安全防 XSS**：默认自动转义 HTML 特殊字符，避免注入攻击
2. **高性能**：模板首次编译为 Python 字节码并缓存，重复渲染极快
3. 复用能力强
   - 模板继承 `{% block %}`：统一网页头部底部，不用重复写
   - 宏 `macro`：模板内封装可复用片段，类似函数
   - `include`：引入公共片段（导航、页脚）
4. **高度扩展**：自定义过滤器、全局函数、沙箱隔离（安全渲染第三方模板）
5. **不限文件格式**：不只做网页，还能生成 yaml、shell、sql、Dockerfile 配置

#### 4.1.5 常见使用场景

1. **Web 开发**：Flask 内置模板引擎；FastAPI、Sanic 常用配套
2. **自动化运维**：Ansible 配置模板、K8s yaml 动态渲染
3. **AI / 工具脚本**：动态生成提示词 Prompt、报表文本、邮件内容
4. **代码生成器**：批量生成 CRUD 页面、接口代码

#### 4.1.6 使用示例

##### 安装

```bash
uv add jinja2
```

##### 案例1 读取并渲染内存模板

创建文件 `atguigu/test/jinja2/simple_template.py`：

```python
# atguigu/test/jinjia2/simple_template.py

from jinja2 import Template

# 模板文本
tpl = Template("用户：{{ name }}，积分：{{ score }}")
# 传入数据渲染
result = tpl.render(name="小明", score=99)
print(result)
# 输出：用户：小明，积分：99
```

##### 案例2 读取并渲染文件模板

创建模板文件 `atguigu/test/jinjia2/template.jinja2`：

```jinjia
{# atguigu/test/jinjia2/template.jinjia2 #}
{# 系统角色 #}
你是一名专业AI助手，基于提供的参考资料回答用户问题，禁止编造内容。

{% if docs %}
### 参考资料
{% for item in docs %}
{{ loop.index }}. {{ item.content | trim | truncate(800) }}
{% endfor %}
{% endif %}

{% if history %}
### 历史对话
{% for msg in history %}
{% if msg.role == "user" %}用户：{{ msg.content }}
{% else %}助手：{{ msg.content }}
{% endif %}
{% endfor %}
{% endif %}

用户现在的问题：{{ question }}
输出要求：以简洁markdown格式回答
```

创建python解析文件 `atguigu/test/jinjia2/load_template_file.py`：

```python
# atguigu/test/jinjia2/load_template_file.py

from jinja2 import Environment, FileSystemLoader
import os

# 1. 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 创建 Jinja2 环境，设置模板搜索路径为当前目录
env = Environment(loader=FileSystemLoader(current_dir))

# 3. 加载模板文件
tpl = env.get_template('template.jinjia2')
print(type(tpl))

# 4. 准备渲染数据
data = {
    "question": "Jinja2和f-string有什么区别？",
    "docs": [
        {"content": "Jinja2是专业第三方模板引擎，支持循环、判断、外部文件"},
        {"content": "f-string是Python原生字符串格式化，仅适合简单文本"}
    ],
    "history": [
        {"role": "user", "content": "什么是Prompt模板？"},
        {"role": "assistant", "content": "用来动态生成发给大模型指令的文本工具"}
    ]
}

# 5. 渲染完整prompt字符串
full_prompt = tpl.render(**data)

# 打印最终生成的提示词
print(full_prompt)

```

##### 案例3 读取当前项目的提示词模板

创建文件 `atguigu/prompts/loader.py`

```python
# atguigu/prompts/loader.py

"""
jinja2:模版引擎（计算逻辑和表现分开）
"""

from pathlib import Path


def load_prompt(prompt_file_name: str) -> str:
    """
    根据任务类型的提示词文件名字 读取对应文件的内容
    :param prompt_file_name:
    :return:
    """
    prompt_file_path = Path(__file__).resolve().parents[0] / "jinja2" / f"{prompt_file_name}.jinja2"

    return prompt_file_path.read_text(encoding="utf-8")

if __name__ == '__main__':
    print(load_prompt("turn_plan"))
```

### 4.2 HistoryBuilder

`HistoryBuilder`的作用：把消息对象渲染成文本

渲染规则也很直观：

- 文本消息：直接取 `text`，比如 `"我要退款"`
- 对象消息：渲染成一段描述，比如 `[订单对象 id=A20240315001, title=小米手机]`——因为 LLM 看不懂 Python 对象，必须把对象的关键信息摊成它能读的文字

创建文件：`atguigu/prompts/history_builder.py`:

```python
# atguigu/prompts/history_builder.py

from typing import List, Dict, Any
from atguigu.domain.state import Turn
from atguigu.domain.messages import UserMessage, BotMessage, FocusedObject, MessageType


class HistoryBuilder:
    """

    1. 将用户消息的UserMessage对象序列化为字符串---->"USER: 我准备查询订单信息"
    2. 将历史对话的Q(UserMessage)A(BotMessage)对象序列化为字符串："USER: 我想查询物流信息\n BOT: 好的，先提供订单编号"

    """

    @staticmethod
    def build(turns: List[Turn]) -> str:
        """
        构建历史对话
        :param turns:
        :return:
        """

        msgs: List[str] = []
        for turn in turns:
            # 1. 用户消息
            user_message = turn.user_message
            user_message_str = HistoryBuilder._render_user_message(user_message)
            msgs.append(f"USER: {user_message_str}")
            # 2. 机器人回复消息
            for bot_msg in turn.bot_messages:
                bot_msg_str = HistoryBuilder._render_bot_message(bot_msg)
                msgs.append(f"BOT: {bot_msg_str}")
        return "\n".join(msgs)

    @staticmethod
    def _render_user_message(user_message: UserMessage) -> str:
        """
        渲染用户消息
        :param user_message:
        :return:
        """
        if user_message.type is MessageType.TEXT:
            return HistoryBuilder._render_text_msg(user_message.text)
        else:
            return HistoryBuilder._render_obj_msg(user_message.object)

    @staticmethod
    def _render_bot_message(bot_msg: BotMessage) -> str:
        if bot_msg.text:
            return HistoryBuilder._render_text_msg(bot_msg.text)
        else:
            return HistoryBuilder._render_obj_msg(bot_msg.object)  # 基本走不到


    @staticmethod
    def _render_text_msg(text: str) -> str:
        return text.strip()

    @staticmethod
    def _render_obj_msg(object_msg: FocusedObject) -> str:
        """
        id
        type
        title
        attributes
        :param object_msg:
        :return:
        "[id="对应的编号", type="订单对象 or 商品对象", title="对应的描述",attributes=price=1000 url="www.pic.com" ]"
        """
        label = "订单对象" if object_msg.type == "order" else "商品对象"
        id = object_msg.id
        title = object_msg.title
        attributes: Dict[str, Any] = object_msg.attributes
        attributes_str = " ".join([f"{key}={value}" for key, value in attributes.items()])

        return f"[label={label}, id={id}, title={title}, attributes={attributes_str}]"


if __name__ == '__main__':

    """
    测试 HistoryBuilder 的 build 方法
    """
    from atguigu.prompts.history_builder import HistoryBuilder
    from atguigu.domain.state import Turn
    from atguigu.domain.messages import UserMessage, BotMessage, FocusedObject, MessageType

    def test_build_single_text_turn():
        """测试单轮纯文本对话"""
        # 创建用户消息
        user_msg = UserMessage(
            sender_id="user_001",
            message_id="msg_001",
            type=MessageType.TEXT,
            text="我想查询订单信息"
        )

        # 创建机器人回复
        bot_msg1 = BotMessage(text="你好")
        bot_msg2 = BotMessage(text="请提供订单编号")

        # 创建轮次
        turn = Turn(
            turn_id="turn_001",
            user_message=user_msg,
            bot_messages=[bot_msg1, bot_msg2]
        )

        # 构建历史对话
        result = HistoryBuilder.build([turn])
        print(f"结果:\n{result}")


    def test_build_with_object_message():
        """测试包含对象类型的消息"""
        # 用户点击了一个订单对象
        focused_obj = FocusedObject(
            id="order_12345",
            type="order",
            title="iPhone 15 Pro Max",
            attributes={"price": "9999", "status": "已发货"}
        )

        user_msg = UserMessage(
            sender_id="user_001",
            message_id="msg_001",
            type=MessageType.OBJECT,
            object=focused_obj
        )

        bot_msg = BotMessage(text="我看到您点击了这个订单，请问需要什么帮助？")

        turn = Turn(
            turn_id="turn_001",
            user_message=user_msg,
            bot_messages=[bot_msg]
        )

        result = HistoryBuilder.build([turn])
        print(f"结果:\n{result}")

    # 运行所有测试
    test_build_single_text_turn()
    test_build_with_object_message()
```

### 4.3 提示词分析

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/05-七个字段总览.png" style="zoom: 67%;" />

| 字段                   | 类别     | 不传的后果                                 |
| ---------------------- | -------- | ------------------------------------------ |
| `user_message`         | 判断输入 | 无从判断                                   |
| `current_conversation` | 判断输入 | 看不懂依赖上下文的短句（"算了"、报个号码） |
| `active_task`          | 当前状态 | 分不清"回答当前流程"还是"开新业务"         |
| `interrupted_tasks`    | 当前状态 | 没法正确生成 `resume_flow`                 |
| `focused_object`       | 当前状态 | 理解不了"这个""它"等指代                   |
| `available_flows`      | 可选范围 | 瞎编 flow id                               |
| `knowledge_intents`    | 可选范围 | 瞎编 intent id                             |

一句话总结：**前两个让 LLM "看懂用户说什么"，中间三个让 LLM "知道现在是什么处境"，后两个给 LLM "划定能选什么"**。三组信息凑齐，LLM 才能做出又准又合法的判断。

## 第5章 TurnPlanner 

`TurnPlanner` 的职责：把当前对话状态喂给 LLM，让 LLM 输出一个 `TurnPlan`。

### 5.1 入口 

创建文件 `atguigu/plan/turn_planner.py`

```python
# atguigu/plan/turn_planner.py

class TurnPlanner:
    """
    意图分析器
    作用：根据自然语言 调用LLM 分析轨道类型
    """

    async def predict(self, state: DialogueState, flows: FlowsList) -> TurnPlan:
        """

        :param state:
        :return: 返回值是什么?(分析:定义数据模型)
        """

        # 1. 构建提示词
        inputs_prompt = self._build_prompt_inputs(state, flows)

        # 2. 调用LLM模型
        turn_plan = await  self._predict_from_prompt_inputs(inputs_prompt)

        return turn_plan
```

`predict` 接收两样东西：

| 入参    | 是什么                                        |
| ------- | --------------------------------------------- |
| `state` | 当前对话状态（含历史、活跃任务、聚焦对象等）  |
| `flows` | 系统支持的所有流程（告诉 LLM 有哪些业务可办） |

它只做两件事：

1. `_build_prompt_inputs`：把这三样东西**整理成给 LLM 的提示词变量**
2. `_predict_from_prompt_inputs`：拿提示词变量**调 用LLM**，把输出解析成 `TurnPlan`

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/05-predict.png" style="zoom:50%;" />

### 5.2 提示词的实现

`_build_prompt_inputs` 把信息从 `state` / `flows`里取出来，序列化成提示词变量：

```python
    def _build_prompt_inputs(self, state: DialogueState, flows_list: FlowsList) -> Dict[str, Any]:
        """
        构建提示词输入参数
        :param state:
        :param flows_list:
        :return:
        """
        # 1. 用户消息
        user_msg = HistoryBuilder._render_user_message(state.pending_turn.user_message)

        # 2. 历史对话(当前session的turns:后10轮：最近的10轮) 。历史对话取多少 取哪些：动态策略
        current_conversation = HistoryBuilder.build(state.current_session().turns[-10:])

        # 3. 当前激活任务(业务任务)
        active_task_json = json.dumps(
            state.active_task.model_dump(mode="json"),ensure_ascii=False
        ) if state.active_task is not None else None

        # 4. 中断任务
        interrupted_tasks_json = json.dumps(
            [paused_task.model_dump(mode="json") for paused_task in state.paused_tasks],
            ensure_ascii=False
        )

        # 5. 页面点击卡片获取的信息
        focused_object_json = json.dumps(state.focused_object.model_dump(mode="json")) if state.focused_object is not None else None

        # 6. 流程清单
        # available_flows_json=[{} for flow in flows_list.flows]

        available_flows_json = json.dumps(
            {
                "flows": [{k: v for k, v in flow.model_dump(mode="json").items() if k != "steps"} for flow in flows_list.flows]
            },
            ensure_ascii=False)

        return {
            "user_message": user_msg,
            "current_conversation": current_conversation,
            "active_task_json": active_task_json,
            "interrupted_tasks_json": interrupted_tasks_json,
            "focused_object_json": focused_object_json,
            "available_flows_json": available_flows_json,
            "knowledge_intents_json": ""
        }
```

它返回一个字典，一共 **7 个字段**，每个都会被填进 prompt 模板的某个 `{{ }}` 占位符。

这些字段返回后，会交给  `_predict_from_prompt_inputs`：填进 jinja2 模板、调 LLM、解析成 `TurnPlan`。

### 5.3 调用 LLM

```python
async def _predict_from_prompt_inputs(self, inputs_prompt: Dict[str, Any]) -> TurnPlan:
        """
        1. 加载提示词模板
        2. 格式化模版
        3. 调用模型
        :param inputs_prompt:
        :return:
        """

        prompt_template_text = load_prompt("turn_plan")

        prompt_template = PromptTemplate.from_template(template=prompt_template_text, template_format="jinja2")

        # LangChain 的链式写法
        chain = prompt_template | llm | JsonOutputParser()

        llm_response_dict: Dict[str, Any] = await chain.ainvoke(inputs_prompt)

        return TurnPlan.from_dict(llm_response_dict)

```

这里用了 LangChain 的链式写法，三个环节串成一条流水线：

```text
prompt(模板) | llm(大模型) | JsonOutputParser(解析成字典)
```

| 环节               | 做什么                                                       |
| ------------------ | ------------------------------------------------------------ |
| `prompt`           | 把 `prompt_inputs` 里的变量填进 jinja2 模板，渲染成最终提示词 |
| `llm`              | 把渲染好的提示词发给大模型，拿到文本回复                     |
| `JsonOutputParser` | 把模型返回的 JSON 文本解析成 Python 字典                     |

最后 `TurnPlan.from_dict(llm_output)` 把字典变成 `TurnPlan` 对象。

- `load_prompt("turn_plan")`：从 prompt 目录读取 `turn_plan.jinja2` 模板文本
- `template_format="jinja2"`：告诉 LangChain 用 jinja2 语法渲染（模板里用 `{{ }}` 取变量）
- `await chain.ainvoke(...)`：异步调用，因为 LLM 请求是高延迟 I/O，必须 async

## 第6章 小结

### 6.1 把整条链路串起来

完整走一遍"用户说『我要退款』"的链路（文本 + task 轨道）：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/05-把这一节串起来.png" style="zoom: 67%;" />

这条链路现在打通了从"用户文本"到"task 轨道入口"的全过程：

- 用户说"我要退款"
- 引擎准备会话、开 turn
- TurnPlanner 把 7个字段组装成 prompt，调 LLM
- LLM 返回 `{"task": {"commands": [{"command": "start_flow", "flow": "refund_request"}]}}`
- 解析成 `TurnPlan`，看到 task 非空
- 把 commands 交给 `TaskHandler.handle`（内部留到下一节）

### 6.2 这一节实现了什么

| 文件                              | 内容                                                         |
| --------------------------------- | ------------------------------------------------------------ |
| `engine/dialogue_engine.py`       | `process_message` 框架 + `_prepare_session` / `_begin_turn` / `_handle_text_message`（task 分支） |
| `plan/models.py`                  | `TurnPlan` / `TaskTurnPlan` / `KnowledgeTurnPlan` / `ChitchatTurnPlan` |
| `task/command/models.py`          | `Command` 四子类 + `COMMAND_NAME_TO_CLASS`                   |
| `plan/turn_planner.py`            | `TurnPlanner.predict` / `_build_prompt_inputs` / `_predict_from_prompt_inputs` |
| `prompts/jinja2/turn_plan.jinja2` | 提示词模板                                                   |

### 6.3 几个好的设计

1. **引擎只调度、不干活**：引擎持有一堆"专员"，自己只决定走哪条轨道、把活派给谁。
2. **多态反序列化的老套路**：`Command.from_dict` 用 `COMMAND_NAME_TO_CLASS` 映射表分发。
3. **给 LLM 的 7个字段各有所司**：判断输入（user_message / history）+ 当前状态（active_task / interrupted_tasks / focused_object）+ 可选范围（available_flows / knowledge_intents）。给 LLM 看什么，直接决定它判断得准不准、合不合法。
4. **available_flows 去掉 steps**：LLM 只需"业务说明书"，不需要流程内部步骤，省 token 又防干扰。
5. **先打通主干，再加固边界**：本节先让正常路径跑通，校验（防幻觉）和对象消息留到后面。



# 六、防幻觉校验与对象消息处理

## 第1章 任务目标 

上一节我们让"文本消息 → LLM 生成 TurnPlan → 进入 task 轨道"这条主干跑通了，但刻意跳过了两块"防护"和"另一类输入"：

- **防幻觉校验**：LLM 是概率模型，它可能编出一个根本不存在的 flow、给出自相矛盾的指令。直接拿它的输出去执行是危险的。这一节实现 `TurnPlanValidator`。
- **对象消息**：用户不只会打字，还会**点卡片**——点一个订单、点一个商品。这类"对象消息"怎么处理，这一节实现 `_handle_object_message`。

### 1.1 本节范围

| 内容                                                 | 本节                     |
| ---------------------------------------------------- | ------------------------ |
| `TurnPlanValidator` 防幻觉校验（9 种 ClarifyReason） | ✅ 详细实现               |
| 对象消息处理 `_handle_object_message`                | ✅ 详细实现               |
| `_resolve_object_commands`（对象转命令）             | ✅ 重点                   |
| `_flow_has_unfilled_collect_slot`（能否填槽判断）    | ✅ 重点                   |
| 点击卡片的各种时机场景                               | ✅ 详细展示               |
| `TaskHandler` 内部（命令执行、流程推进）             | ⛔ 仍不实现，调用入口为止 |
| knowledge / chitchat 处理器内部                      | ⛔ 不展开                 |

### 1.2 校验以及对象消息流程

**引擎的"安全网"和"另一只手"**

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-校验以及对象消息流程.png" style="zoom:67%;" />

---

## 第2章 防幻觉校验

### 2.1 为什么需要防幻觉校验

#### LLM 的输出不能直接信

回顾上一节，`TurnPlanner` 调 LLM 后，把返回的 JSON 解析成 `TurnPlan`。但 LLM 是概率生成模型，它的输出**不保证合法**。几种典型的"翻车"情况：

| LLM 可能的翻车                               | 后果（如果不校验）                       |
| -------------------------------------------- | ---------------------------------------- |
| 三个轨道全填 `null`（没判断出意图）          | 引擎不知道走哪条轨道                     |
| 同时填了 task 和 knowledge                   | 引擎一次只能处理一条轨道，不知道先走哪个 |
| task 轨道但 commands 是空的                  | 知道要办业务，却没有任何指令可执行       |
| 编了一个不存在的 flow，比如 `"tuikuan_flow"` | 下游查流程表 → 找不到 → 崩溃             |
| 一次塞了两个 `start_flow`                    | 同时开两个流程，状态混乱                 |

这些就是所谓的"幻觉"——LLM 一本正经地输出了**结构对、但内容不合法**的东西。

### 2.2 校验的职责

`TurnPlanValidator` 的职责很纯粹：**检查 `TurnPlan` 能不能执行，不能执行就给出一个"原因码"**。它本身不生成任何回复话术——那是 `ClarifyResponder` 的事。一句话校验器**只判断，不回复**

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-校验的职责.png" style="zoom:67%;" />

这种"校验只判断、回复另交他人"的分工，让校验逻辑保持干净——它只关心"对不对"，不关心"怎么跟用户说"。

---

### 2.3 校验结果数据模型

在 `atguigu/plan/models.py` 追加模型的定义

```python
# atguigu/plan/models.py

class ClarifyReason(str, Enum):
    MISSING_TRACK = "missing_track"
    MULTIPLE_TRACKS = "multiple_tracks"
    MISSING_TASK_COMMANDS = "missing_task_commands"
    MISSING_KNOWLEDGE_INTENT = "missing_knowledge_intent"
    MISSING_FOCUSED_OBJECT = "missing_focused_object"
    OBJECT_REQUIRES_INTENT = "object_requires_intent"
    INVALID_TASK_COMMANDS = "invalid_task_commands"
    MULTIPLE_TASK_FLOWS = "multiple_task_flows"
    UNKNOWN_TASK_FLOW = "unknown_task_flow"

class TurnPlanValidationResult(BaseModel):
    valid: bool # 是否有效
    reason: ClarifyReason | None = None #无效时的原因
```

- `valid`：这个 `TurnPlan` 能不能直接执行
- `reason`：不能执行时，是什么原因（一个固定枚举值）
- 继承 str, Enum ：表示既可以将变量作为字符串比较，也可以将变量作为枚举比较

### 2.4 九种原因码

`ClarifyReason` 一共 9 种，按"在校验的哪个环节触发"可以分成三组：

**第一组：轨道层面（在所有校验最前面）**

| 原因码            | 触发条件                                                    |
| ----------------- | ----------------------------------------------------------- |
| `MISSING_TRACK`   | task / knowledge / chitchat 三个都为 null，没判断出任何方向 |
| `MULTIPLE_TRACKS` | 同时命中多个轨道，但引擎一次只能执行一个                    |

**第二组：task 轨道内部（命中 task 后细查）**

| 原因码                  | 触发条件                                            |
| ----------------------- | --------------------------------------------------- |
| `MISSING_TASK_COMMANDS` | task 轨道，但 commands 为空                         |
| `INVALID_TASK_COMMANDS` | commands 里有不认识的命令类型                       |
| `MULTIPLE_TASK_FLOWS`   | 一次出现多个 `start_flow`，同时想开好几个流程       |
| `UNKNOWN_TASK_FLOW`     | `start_flow` 指定的 flow 在系统里不存在（典型幻觉） |

**第三组：knowledge / 对象相关**

| 原因码                     | 触发条件                                           |
| -------------------------- | -------------------------------------------------- |
| `MISSING_KNOWLEDGE_INTENT` | knowledge 轨道，但 intents 为空                    |
| `MISSING_FOCUSED_OBJECT`   | 知识意图需要聚焦对象，但当前没有                   |
| `OBJECT_REQUIRES_INTENT`   | 用户只发了对象，没说要干嘛（对象消息处理时会用到） |

> 注意 `OBJECT_REQUIRES_INTENT` 不是 validator 产生的，而是对象消息处理时直接用的——放在同一个枚举里统一管理。

---

### 2.5 校验主流程

#### 2.5.1 validate 入口

校验是一个"层层收窄"的过程：先看轨道数量，再钻进具体轨道细查。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-validate 入口.png" style="zoom: 67%;" />

创建文件 `atguigu/plan/turn_validator.py`：

```python
# atguigu/plan/turn_validator.py

from typing import Dict

from atguigu.domain.state import DialogueState
from atguigu.knowledge.intents import KnowledgeIntent
from atguigu.plan.models import TurnPlan, TurnPlanValidationResult, ClarifyReason
from atguigu.task.command.models import SetSlotsCommand, StartFlowCommand, ResumeFlowCommand, CancelFlowCommand
from atguigu.task.flow.flows import FlowsList


class TurnPlanValidator:

    def validate(
            self,
            state: DialogueState,
            turn_plan: TurnPlan,
            flow_list: FlowsList,
            intents: Dict[str, KnowledgeIntent]
    ) -> TurnPlanValidationResult:
        """
        校验 turn_plan
        :param turn_plan:
        :return:
        """

        active_tracks = self._active_tracks(turn_plan)

        # 1. 是否没有命中轨道
        if not active_tracks:
            return self._reject(ClarifyReason.MISSING_TRACK)

        # 2. 是否命中多条轨道
        if len(active_tracks) > 1:
            return self._reject(ClarifyReason.MULTIPLE_TRACKS)

        # 3. 获取唯一的轨道
        active_track = active_tracks[0]

        # 4. 判断轨道到底是哪一个
        if active_track == "task":
            # 4.1 业务任务轨道
            return self._validate_task(turn_plan, flow_list)

        if active_track == "knowledge":
            # 4.2 信息咨询任务轨道（后面2.7.2小节实现）
            return self._validate_knowledge(state, turn_plan, intents)
		
        # True：校验通过
        return TurnPlanValidationResult(valid=True)
```

注意 chitchat 不需要任何校验，命中即合法。

#### 2.5.2 _active_tracks

**计算命中了几个轨道**

在 `atguigu/plan/turn_validator.py`中添加如下代码：

```python
@staticmethod
def _active_tracks(turn_plan: TurnPlan) -> list[str]:
    active_tracks: list[str] = []
    if turn_plan.task is not None:
        active_tracks.append("task")  # 轨道的名字

    if turn_plan.knowledge is not None:
        active_tracks.append("knowledge")  # 轨道的名字

    if turn_plan.chitchat is not None:
        active_tracks.append("chitchat")  # 轨道的名字

    return active_tracks
```

把三个字段里非 null 的轨道名收集成列表。这个列表的长度决定了前两道关卡：

- 长度 0 → `MISSING_TRACK`
- 长度 > 1 → `MULTIPLE_TRACKS`
- 长度 1 → 进入对应轨道细查

> 这条规则体现了系统的一个核心约束：**TurnPlanner 允许识别出多个意图，但 DialogueEngine 一次只执行一个轨道**。多意图时触发澄清，让用户确定先办哪个。

#### 2.5.3  _reject

返回校验失败结果，封装一个 `valid=False` 和原因码。不生成话术，把"怎么跟用户说"留给 `ClarifyResponder`

在 `atguigu/plan/turn_validator.py`中添加如下代码：

```python
def _reject(self, reason: ClarifyReason) -> TurnPlanValidationResult:
    return TurnPlanValidationResult(
        valid=False,
        reason=reason
    )
```

### 2.6 task 轨道的四重校验

`_validate_task` 是防幻觉的核心，它对 task 轨道做了**四重检查**，任何一重不过就拒绝。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-task 轨道的四重校验.png" style="zoom: 67%;" />

完整的校验代码：在 `atguigu/plan/turn_validator.py`中添加如下代码

```python
    def    (
            self,
            turn_plan: TurnPlan,
            flows: FlowsList,
    ) -> TurnPlanValidationResult:

        task_plan = turn_plan.task

        # 第一重:commands 不能为空
        if task_plan is None or not task_plan.commands:
            return self._reject(ClarifyReason.MISSING_TASK_COMMANDS)

        # 第二重:每个 command 都得是认识的类型
        allowed = (StartFlowCommand, ResumeFlowCommand, CancelFlowCommand, SetSlotsCommand)
        if not all(isinstance(cmd, allowed) for cmd in task_plan.commands):
            return self._reject(ClarifyReason.INVALID_TASK_COMMANDS)

        # 第三重:不能一次开多个流程
        start_commands = [cmd for cmd in task_plan.commands if isinstance(cmd, StartFlowCommand)]
        if len(start_commands) > 1:
            return self._reject(ClarifyReason.MULTIPLE_TASK_FLOWS)

        # 第四重:要开的流程必须真实存在
        if start_commands:
            flow = flows.get_flow_by_id(start_commands[0].flow)
            if flow is None:
                return self._reject(ClarifyReason.UNKNOWN_TASK_FLOW)

        # 校验成功
        return TurnPlanValidationResult(valid=True)
```

#### 2.6.1 第一重：commands 非空

```python
if task_plan is None or not task_plan.commands:
    return self._reject(ClarifyReason.MISSING_TASK_COMMANDS)
```

LLM 说"用户在办业务"（命中了 task 轨道），却没给出任何 command。这等于"我知道他要办事，但不知道办什么"——无法执行，拒绝。

#### 2.6.2 第二重：命令类型合法

```python
allowed = (StartFlowCommand, ResumeFlowCommand, CancelFlowCommand, SetSlotsCommand)
if not all(isinstance(cmd, allowed) for cmd in task_plan.commands):
    return self._reject(ClarifyReason.INVALID_TASK_COMMANDS)
```

正常情况下 `Command.from_dict` 解析时遇到不认识的 command 名会直接报错，但这里再加一道防线，确保每条命令都是这四种已知类型之一。**这是典型的"防御性编程"——即不假设上游一定干净**。

#### 2.6.3 第三重：不能一次开多个流程

```python
start_commands = [cmd for cmd in task_plan.commands if isinstance(cmd, StartFlowCommand)]
if len(start_commands) > 1:
    return self._reject(ClarifyReason.MULTIPLE_TASK_FLOWS)
```

一条用户消息里出现两个 `start_flow`，意味着 LLM 想同时开两个流程。比如同时开"退款"和"查物流"。系统一次只能有一个活跃任务，所以拒绝，让用户先明确处理哪个。

#### 2.6.4 第四重：流程必须真实存在

```python
if start_commands:
    flow = flows.get_flow_by_id(start_commands[0].flow)
    if flow is None:
        return self._reject(ClarifyReason.UNKNOWN_TASK_FLOW)
```

这是**最典型的防幻觉检查**。LLM 可能编出一个 YAML 里根本没定义的 flow id。比如把 `refund_request` 写成 `refund` 或 `tuikuan`。

这里用 `flows.get_flow_by_id` 去**真实的流程列表**里查证。查不到，说明是幻觉，拒绝。

### 2.7 Knowledge校验

#### 2.7.1 KnowledgeIntent：信息检索意图注册表

在看 knowledge 校验之前，要先补一个一直在用、却没正式讲过的数据模型——`KnowledgeIntent`。前面 TurnPlanner 的 prompt 字段 `knowledge_intents_json`、这里的 `_validate_knowledge`，都依赖它。

先说清楚一件事：**什么是"知识意图"？** 所谓知识意图，就是**用户咨询类问题的一个分类**。用户问的问题五花八门——"这件衣服什么材质""退款多久到账""支持七天无理由吗"——但归一归类，无非就那么几种。每一类，就是一个 `KnowledgeIntent`。

下面这张表，把用户的原话映射到对应的意图，先建立直观印象：

| 用户可能这么问                     | 归类到哪个意图（id）              |
| ---------------------------------- | --------------------------------- |
| "这件衣服什么材质？""这个多少钱？" | `product_info`（商品信息咨询）    |
| "我那个订单啥状态了？"             | `order_info`（订单信息咨询）      |
| "退款多久到账？"                   | `refund_policy`（退款政策咨询）   |
| "支持七天无理由吗？"               | `return_policy`（退货政策咨询）   |
| "你们多久发货？"                   | `shipping_policy`（配送政策咨询） |

`KnowledgeIntent` 就是用来描述"这样一类问题"的数据模型，它定义在 `atguigu/knowledge/intents.py`：

```python
# atguigu/knowledge/intents.py

from pydantic import BaseModel

class KnowledgeIntent(BaseModel):
    id: str
    description: str
    provider_ids: list[str] = []
    requires_object: str | None = None
```

| 字段              | 含义                                                         |
| ----------------- | ------------------------------------------------------------ |
| `id`              | 意图唯一标识，如 `product_info`                              |
| `description`     | 意图的中文说明，喂给 LLM 帮它分类                            |
| `provider_ids`    | 这个意图要查哪些知识源（FAQ、RAG、订单 API 等）              |
| `requires_object` | 这个意图是否必须依附一个聚焦对象，值是对象类型（`product` / `order`），不需要则为 `None` |

系统支持的所有知识意图，集中注册在一张 `dict` 里（key 是意图 id），在 `atguigu/knowledge/intents.py`中添加如下定义：

```python
# atguigu/knowledge/intents.py

KNOWLEDGE_INTENTS: dict[str, KnowledgeIntent] = {
    "product_info": KnowledgeIntent(
        id="product_info",
        description="商品信息咨询",
        provider_ids=["api.product"],
        requires_object="product",
    ),
    "order_info": KnowledgeIntent(
        id="order_info",
        description="订单信息咨询",
        provider_ids=["api.order"],
        requires_object="order",
    ),
    "refund_policy": KnowledgeIntent(
        id="refund_policy",
        description="退款政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "return_policy": KnowledgeIntent(
        id="return_policy",
        description="退货政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "shipping_policy": KnowledgeIntent(
        id="shipping_policy",
        description="配送政策咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
    "platform_rule": KnowledgeIntent(
        id="platform_rule",
        description="平台规则咨询",
        provider_ids=["rag.default"],
    ),
    "general_ecommerce_info": KnowledgeIntent(
        id="general_ecommerce_info",
        description="电商通用信息咨询",
        provider_ids=["faq.default", "rag.default"],
    ),
}
```

这张注册表在系统里同时扮演**三个角色**，值得记住：

| 角色             | 怎么用                                                       | 在哪用                                       |
| ---------------- | ------------------------------------------------------------ | -------------------------------------------- |
| LLM 的"分类词表" | 把 `id` + `description` 喂给 LLM，约束它只能从这几类里选，防止瞎编意图 | TurnPlanner 的 `knowledge_intents_json` 字段 |
| 校验白名单       | LLM 返回的意图 id 必须能在这张表里查到                       | 本章 `_validate_knowledge`                   |
| 路由元数据       | 命中意图后，按 `provider_ids` 决定查哪些知识源、按 `requires_object` 决定要不要先有聚焦对象 | KnowledgeHandler（后面讲解）                 |

 `requires_object` ：这个字段是下面 knowledge 校验的依据：

- `product_info`（问商品信息）`requires_object="product"`：必须先有一个聚焦的商品
- `order_info`（问订单信息）`requires_object="order"`：必须先有一个聚焦的订单
- `refund_policy` / `shipping_policy` 这类**政策咨询**不需要有 `requires_object`，不需要指定具体订单或商品

> 这一节只需理解 `KnowledgeIntent` 这个数据模型，以及它的 `requires_object` 字段。完整的知识检索流程——`provider_ids` 怎么映射到具体的 FAQ/RAG/API、怎么检索拼接知识、怎么生成回答——是 `KnowledgeHandler` 的内容，留到后面讲解。

#### 2.7.2 knowledge 轨道校验

在 `atguigu/plan/turn_validator.py`中添加如下代码：

```python
def _validate_knowledge(
        self,
        state: DialogueState,
        turn_plan: TurnPlan,
        intents: Dict[str, KnowledgeIntent]
) -> TurnPlanValidationResult:

    knowledge_plan = turn_plan.knowledge
    if knowledge_plan is None or not knowledge_plan.intents:
        return self._reject(ClarifyReason.MISSING_KNOWLEDGE_INTENT)

    focused_object = state.focused_object
    for intent in knowledge_plan.intents:
        intent_meta = intents[intent]
        required_object = intent_meta.requires_object
        if required_object is not None:
            if focused_object is None or focused_object.type != required_object:
                return self._reject(ClarifyReason.MISSING_FOCUSED_OBJECT)

    return TurnPlanValidationResult(valid=True)
```

两道检查：intents 不能为空；如果某个意图（比如"问商品价格"）**必须依附一个对象**，那当前就得有对应类型的 focused_object，否则没法回答"它多少钱"，因为"它"是谁都不知道。

### 2.8 整合幻觉校验

#### 2.8.1 添加KnowLedgeHandler

创建文件： `atguigu/knowledge/handler.py`

```python
# atguigu/knowledge/handler.py

from typing import Dict
from atguigu.knowledge.intents import KnowledgeIntent
from atguigu.domain.messages import BotMessage

class KnowLedgeHandler:

    def __init__(self, knowledge_intents: Dict[str, KnowledgeIntent]):
        self.knowledge_intents = knowledge_intents

    def handle(self) -> list[BotMessage]:
        return [BotMessage(text="我暂不知道任何信息")]
```

#### 2.8.2 初始化

初始化 `KnowLedgeHandler` 和 `TurnPlanValidator`

`atguigu/engine/dialogue_engine.py`文件 的 `__init__` 方法中添加 `KnowLedgeHandler` 和 `TurnPlanValidator`

```python
class DialogueEngine:
    """
    对话引擎
    """

    def __init__(
            self,
            turn_planner: TurnPlanner,
            task_handler: TaskHandler,
            knowledge_handler: KnowLedgeHandler,
            # chitchat_handler: ChitchatHandler,
            # clarify_responder: ClarifyResponder,
            turn_plan_validator: TurnPlanValidator
    ) -> None:
        self.turn_planner = turn_planner
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        # self.chitchat_handler = chitchat_handler
        # self.clarify_responder = clarify_responder
        self.turn_plan_validator = turn_plan_validator
```

#### 2.8.3 依赖注入

`atguigu/api/routers/dependencies.py` 文件 `get_dialogue_engine`方法中修改  `return DialogueEngine`

```python
async def get_dialogue_engine():
    ...其他代码
    return DialogueEngine(
        turn_planner = TurnPlanner(),
        task_handler = TaskHandler(flows=flow_list),
        knowledge_handler = KnowLedgeHandler(knowledge_intents=KNOWLEDGE_INTENTS),
        turn_plan_validator = TurnPlanValidator())
```

#### 2.8.4 引擎中添加幻觉校验 

`atguigu/engine/dialogue_engine.py` 文件 `_handle_text_message` 方法中添加如下代码：

```python
# 2. 防幻觉校验
validated = self.turn_plan_validator.validate(dialogue_state, turn_plan, self.task_handler.flows, self.knowledge_handler.knowledge_intents)

# 2.1 校验不通过则澄清意图
# TODO 
```

### 2.9 渲染信息检索意图提示词模板

#### 2.9.1 引擎中传递intents参数

`atguigu/engine/dialogue_engine.py` 文件的 `_handle_text_message`  方法中调用 `predict` 方法的位置传递参数： `self.knowledge_handler.knowledge_intents`

```python
# 1. 调 LLM 生成本轮计划（确定任务轨道）
turn_plan = await self.turn_planner.predict(dialogue_state, self.task_handler.flows, self.knowledge_handler.knowledge_intents)
```

#### 2.9.2 意图分析器中生成知识意图清单

`atguigu/plan/turn_planner.py` 文件的`predict`方法和 `_build_prompt_inputs` 方法中：**传递 `intents` 参数**

然后创建知识意图清单并返回

```python
class TurnPlanner:
    """
    意图分析器
    作用：根据任务自然语言 调用LLM 分析轨道类型
    """

    async def predict(self, state: DialogueState, flows_list: FlowsList, intents: Dict[str, KnowledgeIntent]) -> TurnPlan:

        # 1. 构建提示词
        inputs_prompt = self._build_prompt_inputs(state, flows_list, intents)
	   
        ....其他代码
        

    def _build_prompt_inputs(self, state: DialogueState, flows_list: FlowsList, intents: Dict[str, KnowledgeIntent]) -> dict:
        
        ....其他代码
        
        # 7. 知识意图清单
        knowledge_intents_json = json.dumps(
            [{"id": intent.id, "description": intent.description} for intent in intents.values()], ensure_ascii=False)

        return {
            ....其他代码
            "knowledge_intents_json": knowledge_intents_json
        }
        
....其他代码
```

## 第3章 对象消息处理

讲完校验（文本轨道的安全网），现在转向**另一类输入**：对象消息。

### 3.1 什么是对象消息

用户和客服交互，除了打字，还能**点击卡片**。前端会把订单列表、商品列表展示成卡片，用户点一下，前端就发来一条"对象消息"——类型是 `OBJECT`，带着这个订单/商品的 id。

```json
{
  "type": "order",
  "id": "O1001",
  "title": "订单 O1001"
}
```

对象消息和文本消息最大的区别：**它不经过 LLM**。点击一个订单的语义很明确（用户关注这个订单），不需要 LLM 去"理解"。

### 3.2 对象消息的入口

完善 `atguigu/engine/dialogue_engine.py` 文件的 `process_message` 方法的消息分流：

```python
# 3. 按消息类型分流
if user_message.type is MessageType.TEXT:
    # 3.1 文本消息
    messages = await self._handle_text_message(dialogue_state)
else:
    # 3.2 对象消息
    dialogue_state.set_focused_object(user_message.object)
    messages = await self._handle_object_message(user_message, dialogue_state)
```

对象消息分支做两件事：

1. **先把对象记成 `focused_object`**——不管接下来怎么处理，"用户现在关注这个订单"这个事实先记下来
2. 再进入 `_handle_object_message` 决定怎么回应

### 3.3 点击卡片的几种时机场景

这是理解对象消息处理的关键。同样是"点一个订单卡片"，**在对话的不同时机，含义完全不同**。把所有场景列出来：

**场景 A：流程正等着要订单号时，点了订单**

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-场景 A.png" style="zoom: 67%;" />

这是最理想的情况——点击的对象**正好是当前流程缺的那个槽位**。系统应该把它当成"填槽位"，直接推进流程。

**场景 B：没有任何流程时，点了订单**

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-场景B.png" style="zoom: 67%;" />

用户只是点了个订单，没表达意图。系统知道"他关注 O1001"，但不知道"他想干嘛"——查状态？查物流？退款？只能追问。这就是 `OBJECT_REQUIRES_INTENT` 澄清。

**场景 C：流程进行中、但当前不缺这个对象时，点了订单**

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-场景C.png" style="zoom: 67%;" />

流程正在收集 `refund_reason`，这时点订单卡片，对象对当前槽位**没用**。但用户毕竟在一个流程里，不该粗暴打断，于是"不填槽、也不澄清，让流程继续等它要的东西"。

**三种场景的处理对照**：

| 场景 | 当前状态                 | 对象能否填当前槽 | 处理                           |
| ---- | ------------------------ | ---------------- | ------------------------------ |
| A    | 流程正收集 order_number  | 能               | 转成 SetSlotsCommand，推进流程 |
| B    | 没有 active_task         | 不能（没流程）   | OBJECT_REQUIRES_INTENT 澄清    |
| C    | 流程在收集 refund_reason | 不能（槽不匹配） | 不打断，让流程继续             |

### 3.4 _handle_object_message：三分支

上面三种场景，正好对应 `_handle_object_message` 的三条分支：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-三分支.png" style="zoom: 67%;" />

关键就看 `_resolve_object_commands` 能不能把对象转成命令——能转（场景 A），就推进；不能转，再看在不在流程里（场景 C vs 场景 B）:

```python
async def _handle_object_message(
        self,
        message: UserMessage,
        state: DialogueState,
) -> list[BotMessage]:
    """
    处理对象消息
    :param message:
    :param state:
    :return:
    """

    # 1. 将对象解析成command(SetSlotsCommand)
    commands = self._resolve_object_commands(
        message=message,
        state=state,
        flows=self.task_handler.flows,
    )

    # 2. 判断command是否已经存在(流程的步骤刚好需要你点击的卡片)
    if commands:
        # 场景 A:对象能填当前槽 → 转成命令,推进流程
        return await self.task_handler.handle(commands=commands, state=state)

    # 有流程，没有匹配到 slot
    # 如果用户正在一个流程中,不打断,让流程继续。
    if state.active_task is not None:
        # 场景 C:在流程里但槽不匹配 → 不打断,空命令让流程继续
        return await self.task_handler.handle(commands=[], state=state)

    # 没有流程：
    # 场景 B:没有流程 → 澄清
    return await self.clarify_responder.respond(
        state=state,
        reason=ClarifyReason.OBJECT_REQUIRES_INTENT,
    )
```

### 3.5 _resolve_object_commands：对象转命令

这是对象消息处理的核心。它判断：**当前点击的这个对象，能不能填进当前流程正缺的槽位？** 能就生成一个 `SetSlotsCommand`，不能就返回空列表。

```python
def _resolve_object_commands(
        self, 
        message: UserMessage,
        state: DialogueState,
        flows: FlowsList
) -> list[Command]:
    """
    将对象消息转换成command
    :param message:
    :param state:
    :param flows:
    :return:
    """

    # 1. 获取聚焦对象
    focused_object = message.object
    if focused_object is None:
        return []

    # 2. 获取聚焦对象的类型
    object_type = focused_object.type

    # 3.1. 判读对象的类型 order
    if object_type == "order":
        if self._flow_has_unfilled_collect_slot(state, flows, "order_number"):
            return [SetSlotsCommand(command="set_slots", slots={"order_number": focused_object.id})]

        return []

    # 3.2. 判读对象的类型 product
    if object_type == "product":
        if self._flow_has_unfilled_collect_slot(state, flows, "product_id"):
            return [SetSlotsCommand(command="set_slots", slots={"product_id": focused_object.id})]

        return []

    return []
```

逻辑很清楚，按对象类型分两路：

- **订单对象**（`order`）：当前流程如果正缺 `order_number`，就把订单 id 填进去
- **商品对象**（`product`）：当前流程如果正缺 `product_id`，就把商品 id 填进去
- 其它类型、或者当前不缺对应槽位：返回空列表（交回 3.4 去判断场景 B / C）

> 注意"当前流程缺不缺"这个判断，全交给了 `_flow_has_unfilled_collect_slot`。

### 3.6 _flow_has_unfilled_collect_slot：能否填槽的判断

这个方法回答一个精确的问题：**当前流程，是不是定义了某个收集槽（如 order_number），而且这个槽还没填？**

```python
def _flow_has_unfilled_collect_slot(
        self,
        state: DialogueState,
        flows: FlowsList,
        slot_name: str
) -> bool:
    """
    判断流程中是否有未填的收集槽位
    :param state:
    :param flows:
    :param slot_name:
    :return:
    """

    # 1. 获取活跃任务
    active_task = state.active_task

    # 2. 是否存在活跃任务
    if active_task is None:
        # 不存在
        return False

    # 3. 根据活跃任务的id获取流程
    flow_id = active_task.flow_id
    flow = flows.get_flow_by_id(flow_id)
    if flow is None:
        # 不存在
        return False

    # 4. 判断该流程中的当前槽位是否已经填过
    if active_task.slots.get(slot_name):
        return False

    # 5. 遍历流程的步骤,查找是否存在收集这个槽位的步骤
    for step in flow.steps:
        if isinstance(step, CollectFlowStep) and step.slot_name == slot_name:
            return True

    return False
```

四步判断，任何一步不满足就返回 `False`（不能填）：

| 步骤 | 判断                         | False 表示                       |
| ---- | ---------------------------- | -------------------------------- |
| ①    | 有没有 active_task           | 没流程，谈不上填槽（→ 场景 B）   |
| ②    | flow_id 能不能查到流程       | 防御性兜底，理论上不该发生       |
| ③    | 这个槽是不是已经填了         | 已填，不用再填                   |
| ④    | 流程里有没有收集这个槽的步骤 | 此时不需要收集这个槽（→ 场景 C） |

全部通过，才返回 `True`——当前流程确实需要这个槽、而且还空着，正好可以用点击的对象来填。

**逐个场景验证这个方法**：

- **场景 A**（退款流程在收集 order_number）：① 有 active_task ✓ ② flow 查得到 ✓ ③ order_number 还没填 ✓ ④ 退款流程有收集 order_number 的步骤 ✓ → 返回 `True`，能填
- **场景 B**（没有流程）：① active_task 是 None → 返回 `False`，不能填
- **场景 C**（流程在收集 refund_reason，用户点订单）：查的是 `order_number` 槽，但 ③ 退款流程其实已经填过 order_number 了（用户之前给过）→ 返回 `False`，不能填

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-能否填槽的判断.png" style="zoom:67%;" />

### 3.7 为什么对象消息也要SetSlotsCommand

你可能注意到一个设计上的巧思：对象消息能填槽时，不是直接改 state，而是**构造一个 `SetSlotsCommand` 再交给 TaskHandler**。

为什么不直接 `state.set_slots(...)`？因为：

- **统一入口**：文本消息填槽走的是"LLM 产出 SetSlotsCommand → TaskHandler"，对象消息也走同一条路，下游 `TaskHandler` / `CommandProcessor` 不需要区分"这个槽是打字填的还是点卡片填的"
- **复用流程推进逻辑**：填完一个槽位后,流程不会自己停下——它还要接着判断下一步、生成下一句回复(继续问下一个槽,或执行 action)。这套"填槽后怎么往下走"的逻辑,已经在 `TaskHandler` 里为文本消息实现好了。对象消息只要也转成 `SetSlotsCommand` 交给同一个 `TaskHandler`,就能直接复用这套逻辑,而不必在对象处理这条路里把它重写一遍。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-SetSlotsCommand统一入口.png" style="zoom: 67%;" />

**两条输入殊途同归**——这是一个很优雅的设计，把"对象消息"归一化成了"和文本一样的命令"。

## 第4章 ClarifyResponder：生成澄清回复

不管是文本校验失败，还是对象消息要澄清，最终都汇到 `ClarifyResponder`。它的职责是：把一个冷冰冰的**原因码**，变成一句**自然的、说给用户听的追问**。

### 4.1 ClarifyResponder

#### 4.1.1 完整代码

创建文件 `atguigu/clarify/responder.py`

```python
# atguigu/clarify/responder.py

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure.llm import llm
from atguigu.plan.models import ClarifyReason
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt


class ClarifyResponder:

    async def respond(self, state: DialogueState, reason: ClarifyReason) -> list[BotMessage]:

        clarify_message = self.build_clarify_message(reason=reason, state=state)
        user_message = state.pending_turn.user_message
        user_message_str = HistoryBuilder._render_user_message(user_message)
        history_str = HistoryBuilder.build(state.current_session().turns[-10:])
        focused_object_str = state.focused_object.model_dump_json() if state.focused_object is not None else None

        prompt_text = load_prompt("clarify_respond")
        prompt_template = PromptTemplate.from_template(template=prompt_text, template_format="jinja2")
        chain = prompt_template | llm | StrOutputParser()
        rewritten = await  chain.ainvoke({
            "user_message": user_message_str,
            "history": history_str,
            "focused_object": focused_object_str,
            "clarify_message": clarify_message,
            "reason": reason.value
        })
        return [BotMessage(text=rewritten)]


    def build_clarify_message(
            self,
            reason: ClarifyReason,
            state: DialogueState,
    ) -> str:
        if reason is ClarifyReason.MULTIPLE_TRACKS:
            return "你这次同时提到了多个方向。我们先处理一个，你想先办业务还是先咨询信息呢？"

        if reason is ClarifyReason.MISSING_FOCUSED_OBJECT:
            return "请先发送你想咨询的对象，我再继续帮你看。"

        if reason is ClarifyReason.MISSING_KNOWLEDGE_INTENT:
            return "你是想了解商品信息、订单信息，还是售后配送规则呢？"

        if reason is ClarifyReason.MISSING_TRACK:
            return "你是想先处理业务问题，还是先咨询信息呢？"

        if reason is ClarifyReason.MISSING_TASK_COMMANDS:
            return "你这次是想办理什么业务呢？比如查订单、查物流，或者申请退款。"

        if reason is ClarifyReason.OBJECT_REQUIRES_INTENT:
            focused_object = state.focused_object
            if focused_object is not None and focused_object.type == "order":
                return "我已经收到这个订单了。你想查订单状态、查物流，还是申请退款呢？"
            if focused_object is not None and focused_object.type == "product":
                return "我已经收到这个商品了。你想了解它的商品信息、发货情况，还是售后相关问题呢？"

        return "我还需要再确认一下你的意思，你可以换个更具体的说法告诉我。"

```

#### 4.1.2 初始化

`atguigu/engine/dialogue_engine.py`文件 的 `__init__` 方法中添加 `ClarifyResponder` 

```python
class DialogueEngine:
    """
    对话引擎
    """

    def __init__(
            self,
            turn_planner: TurnPlanner,
            task_handler: TaskHandler,
            knowledge_handler: KnowLedgeHandler,
            # chitchat_handler: ChitchatHandler,
            clarify_responder: ClarifyResponder,
            turn_plan_validator: TurnPlanValidator
    ) -> None:
        self.turn_planner = turn_planner
        self.task_handler = task_handler
        self.knowledge_handler = knowledge_handler
        # self.chitchat_handler = chitchat_handler
        self.clarify_responder = clarify_responder
        self.turn_plan_validator = turn_plan_validator
```

#### 4.1.3 依赖注入

`atguigu/api/routers/dependencies.py` 文件 `get_dialogue_engine`方法中修改  `return DialogueEngine`

```python
async def get_dialogue_engine():
    
    ...其他代码

    return DialogueEngine(
        turn_planner = TurnPlanner(),
        task_handler = TaskHandler(flows=flow_list),
        knowledge_handler = KnowLedgeHandler(knowledge_intents=KNOWLEDGE_INTENTS),
        clarify_responder = ClarifyResponder(),
        turn_plan_validator = TurnPlanValidator())
```

### 4.2 引擎怎么调用它

#### 4.2.1 防幻觉校验

```python
# atguigu/engine/dialogue_engine.py
# 2.1 校验不通过则澄清意图
if not validated.valid:
    return await self.clarify_responder.respond(dialogue_state, validated.reason)
```

#### 4.2.2 对象消息

完善 `atguigu/engine/dialogue_engine.py` 文件中 `_handle_object_message` 方法的返回值

```python
# 场景 B:没有流程 → 澄清
return await self.clarify_responder.respond(
    state=state,
    reason=ClarifyReason.OBJECT_REQUIRES_INTENT,
)
```

引擎只传两样东西：当前 `state` 和一个 `reason`（原因码）。剩下的全交给 `ClarifyResponder`。

### 4.3 两段式设计

**先模板话术，再 LLM 润色**

`ClarifyResponder` 生成回复分两步：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-生成回复.png" style="zoom: 67%;" />

| 步骤       | 做什么                                    | 为什么                                          |
| ---------- | ----------------------------------------- | ----------------------------------------------- |
| ① 基础话术 | 按 `reason` 用 if-else 写死一句兜底话术   | 保证**永远有一句能用的话**，不依赖 LLM 一定成功 |
| ② LLM 润色 | 把基础话术 + 上下文喂给 LLM，改写得更自然 | 让追问贴合当前对话，不生硬                      |

这种"**规则保底 + LLM 润色**"的组合很值得学：基础话术保证下限（哪怕 LLM 调用失败也有话说），LLM 润色提升体验（结合上下文说得更自然）。

#### 4.3.1 build_clarify_message 生成基础话术

`build_clarify_message`方法是一张"原因码 → 话术"的对照表，用 if-else 实现。几个要点：

- **每个 reason 一句专属话术**：追问要贴着原因来。缺意图就引导"你想办什么"，多意图就引导"先处理哪个"。
- **`OBJECT_REQUIRES_INTENT` 还会看对象类型**：点的是订单，就提示"查状态/查物流/退款"；点的是商品，就提示"商品信息/发货/售后"。引导的选项要对得上用户手里的东西。
- **最后有一句兜底**：所有 reason 都没匹配上时（比如 task 的几个细化原因 `INVALID_TASK_COMMANDS` 等），返回一句通用的"换个说法"。

> 注意 task 的四种原因里，只有 `MISSING_TASK_COMMANDS` 有专属话术，`INVALID_TASK_COMMANDS` / `MULTIPLE_TASK_FLOWS` / `UNKNOWN_TASK_FLOW` 走最后的兜底——因为对用户来说，这几种本质都是"我没搞懂你要办什么业务"，用一句通用引导就够了，不必为内部细分各写一句。

#### 4.3.2 respond 调 LLM 润色

`respond` 方法的执行流程：

1. 先调 `build_clarify_message` 拿到基础话术（第一步的产物）
2. 准备润色需要的上下文：用户这句话、对话历史、聚焦对象
3. 用 `clarify_respond` 提示词，把"基础话术 + 上下文"喂给 LLM
4. LLM 输出润色后的自然回复，包成 `BotMessage`

注意它用的是 `StrOutputParser()`——和 TurnPlanner 用 `JsonOutputParser` 不同。因为澄清回复就是**一句给用户看的自然语言**，不需要解析成结构化对象，直接拿文本即可。

#### 4.3.3 润色用的提示词

`clarify_respond.jinja2` 模板：

```jinja2
你是一个中文电商客服助手，语气自然、友好、简洁。
你的任务是把一条系统澄清提示改写成更自然的一句话，不要扩写，不要新增信息，不要改变澄清意图。

澄清原因：{{ reason }}
建议回复：{{ clarify_message }}
{% if focused_object %}
当前聚焦对象：{{ focused_object }}
{% endif %}
{% if history %}
对话历史：
{{ history }}
{% endif %}
用户最后一句：{{ user_message }}

改写后的回复：
```

这个提示词的设计很克制，几个关键约束：

- **"不要扩写，不要新增信息，不要改变澄清意图"**——LLM 只能润色措辞，不能改变追问的核心内容。这防止 LLM 自由发挥跑偏，把"问订单号"改成别的。
- **基础话术作为 `建议回复` 传入**——LLM 是在一个已经正确的话术上润色，而不是从零生成。下限被基础话术兜住了。
- **带上 history 和 focused_object**——让润色后的描述贴合上下文。比如用户刚刚说过什么？聚焦的是哪个订单？LLM 可以自然地呼应。

各变量：

| 变量              | 含义                                    |
| ----------------- | --------------------------------------- |
| `reason`          | 原因码的字符串值，帮 LLM 理解在澄清什么 |
| `clarify_message` | 第一步生成的基础话术（润色的底稿）      |
| `focused_object`  | 当前聚焦对象描述，没有则模板里不出现    |
| `history`         | 当前会话历史                            |
| `user_message`    | 用户本轮这句话                          |

#### 4.3.4 一个完整例子

用户在没有任何流程时，点了一个订单卡片（场景 B，触发 `OBJECT_REQUIRES_INTENT`）：

**第一步**，`build_clarify_message` 看到 reason 是 `OBJECT_REQUIRES_INTENT`、对象类型是 order，返回基础话术：

```text
我已经收到这个订单了。你想查订单状态、查物流，还是申请退款呢？
```

**第二步**，把这句话连同上下文喂给 LLM 润色。LLM 可能输出：

```text
好的，我看到你选的订单 O1001 了～ 你是想查这个订单的状态、看看物流到哪了，还是要申请退款呢？
```

可以看到：核心追问没变（还是引导查状态/查物流/退款），但语气更自然、还自然带上了订单号。这就是两段式的价值——**规则保证说对，LLM 保证说得好听**。

### 4.4 ClarifyResponder 全貌

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-ClarifyResponder 全貌.png" style="zoom: 67%;" />

> 至此，澄清这条线完整了：`TurnPlanValidator` 判断失败给出 `reason` → `ClarifyResponder` 按 reason 生成基础话术 → LLM 润色 → 回复用户。validator 管"对不对"，responder 管"怎么说"，分工清晰。

## 第5章 小结

### 5.1 把整条链路串起来

完整的 `_handle_text_message`（含校验）和对象消息处理，合起来看引擎现在的全貌：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/06-完整流程.png" style="zoom: 67%;" />

至此，引擎的"理解 + 决策"层基本完整：

- 文本消息有了 LLM 理解 + 防幻觉校验的安全网
- 对象消息有了三场景的精细处理
- 所有"看不懂、不合法、缺信息"的情况，统一收口到 ClarifyResponder

剩下没做的，主要是各个 Handler 的内部实现（TaskHandler 怎么推流程、KnowledgeHandler 怎么检索、ChitchatHandler 怎么闲聊）

### 5.2 这一节实现了什么

| 文件                           | 内容                                                         |
| ------------------------------ | ------------------------------------------------------------ |
| `plan/models.py`               | `ClarifyReason`（9 种）、`TurnPlanValidationResult`          |
| `plan/turn_validator.py`       | `TurnPlanValidator`：轨道层校验 + task 四重校验 + knowledge 校验 |
| `atguigu/knowledge/intents.py` | `KnowledgeIntent`/`KNOWLEDGE_INTENTS`： 信息检索意图注册表   |
| `atguigu/knowledge/handler.py` | `KnowLedgeHandler`：信息检索处理器的创建、初始化（`DialogueEngine.__init__`）、依赖注入(`dependencies.py`) |
| `engine/dialogue_engine.py`    | `_handle_object_message` / `_resolve_object_commands` / `_flow_has_unfilled_collect_slot` |
| `atguigu/clarify/responder.py` | `ClarifyResponder`：澄清回复的创建、初始化（`DialogueEngine.__init__`）、依赖注入(`dependencies.py`) |

### 5.3 几个值得记住的设计

1. **LLM 输出必须校验**：概率模型会产出结构对、内容错的"幻觉"。task 四重校验里，"flow 必须真实存在"是最关键的一道防线。
2. **校验只判断、不回复**：validator 只给原因码，话术交给 ClarifyResponder，职责单一。
3. **多意图不强选**：识别出多个轨道时触发 MULTIPLE_TRACKS 澄清，让用户决定，而不是替用户猜。
4. **对象消息三场景**：能填槽（推进）/ 无流程（澄清）/ 在流程但槽不匹配（不打断）。核心判断在 `_flow_has_unfilled_collect_slot`。
5. **对象归一化为命令**：点卡片填槽和打字填槽，都绕回 `SetSlotsCommand` 走同一条 TaskHandler 链路，复用流程推进逻辑。



# 	七、TaskHandler 与 CommandProcessor

## 第1章 任务目标 

前面几节我们已经让引擎能：把用户的话交给 LLM 理解、产出一串 `Command`、校验合法、再把这串 `Command` 交给 `TaskHandler`。但 `TaskHandler` 内部一直是个黑盒。

这一节就打开这个黑盒的**前半部分**：`CommandProcessor`。它负责把一条条 `Command` **真正应用到 `DialogueState`** 上，也就是让对话状态按用户的意图发生变化。

### 1.1 TaskHandler 的两个阶段

`TaskHandler` 处理一轮 task 分两步：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/07-TaskHandler 的两个阶段.png" style="zoom: 67%;" />

| 阶段               | 职责                                            | 本节       |
| ------------------ | ----------------------------------------------- | ---------- |
| ① CommandProcessor | 改状态：建任务、填槽、取消、恢复、挂起          | ✅ 详细实现 |
| ② FlowExecutor     | 读状态、按 YAML 推进流程、执行 action、生成回复 | ⛔ 下一节   |

这一节专注阶段 ①。**理解 CommandProcessor 的关键，是理解每种命令在不同的对话处境下，会让 `DialogueState` 发生什么变化**——尤其是任务的"开始、打断、恢复、取消"这套生命周期。

### 1.2 反复用到的 YAML 流程

这一节所有场景都基于 `user_flows.yml` 里的三个流程，先记住它们：

| flow_id              | name         | 第一步要收集      |
| -------------------- | ------------ | ----------------- |
| `order_status_query` | 订单状态查询 | 订单号            |
| `logistics_tracking` | 物流查询     | 订单号            |
| `refund_request`     | 退款申请     | 订单号 → 退款原因 |

### 1.3 重构恢复任务的逻辑

`atguigu/domain/state.py`

```python
# atguigu/domain/state.py

def resumed_active_task(self, flow_id: str | None = None) -> bool:
    """
    恢复业务任务:流程ID

    如果用户没有明确指定需要恢复的具体任务，那么 flow_id = None，恢复最近的任务
    如果用户明确指定需要恢复的具体任务：
      则按 flow_id 在挂起列表里找到这个任务，恢复为活跃任务，并从挂起列表里移除。

    调用时机：用户说"继续刚才的退款"这类意图时。

    注意：任务被恢复时，step_id 和 slots 都还在，所以可以从挂起前的位置接着跑，不用从头来。

    :return: 恢复成功或失败
    """

    # 1. 判断栈中是否存在中断的业务任务
    if not self.paused_tasks:
        return False

    # 2. 如果业务流程ID不存在
    if flow_id is None:
        self.active_task = self.paused_tasks.pop()
        return True

    # 2. 如果业务流程ID存在
    for i, paused_task in enumerate(self.paused_tasks):
        if paused_task.flow_id == flow_id:
            # 激活
            self.active_task = paused_task
            # 删除
            del self.paused_tasks[i]
            return True

    return False
```

## 第2章 TaskHandler：两阶段的协调者

先看 `TaskHandler` 本身，它很薄，只是把两个阶段串起来。

`atguigu/task/handler.py`

```python
# atguigu/task/handler.py

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.command.models import Command
from atguigu.task.flow.flows import FlowsList


class TaskHandler:

    def __init__(
            self,
            flows: FlowsList,
            command_processor: CommandProcessor
            # flow_executor: FlowExecutor,
            # action_runner: ActionRunner
    ):
        self.command_processor = command_processor
        self.flows = flows
        # self.flow_executor = flow_executor
        # self.action_runner = action_runner

    async def handle(self, commands: list[Command], state: DialogueState) -> list[BotMessage]:
        
        # 阶段1:把命令应用到 state
        self.command_processor.run(commands, state, self.flows)

        # 阶段2:推进流程,生成回复(下一节 TODO)
        # messages: list[BotMessage] = await self.flow_executor.run_task(
        #     state, self.flows, self.action_runner
        # )
        # return messages

        return [BotMessage(text="任务已经处理")]
```

`handle` 就两行：先让 `CommandProcessor` 改状态，再让 `FlowExecutor` 推进流程得到回复。

> 注意 commands 可能是空列表（比如上一节对象消息"在流程中但槽不匹配"的场景 C，传的是 `[]`）。空列表时 CommandProcessor 什么都不做，直接进入阶段2推进流程——这正是"不打断、让流程继续"的实现方式。

## 第3章 CommandProcessor 的骨架

### 3.1 run 与 _apply

创建文件 `atguigu/task/command/processor.py` 命令处理器

```python
# atguigu/task/command/processor.py

from atguigu.domain.state import DialogueState
from atguigu.task.command.models import Command, StartFlowCommand, SetSlotsCommand, CancelFlowCommand, ResumeFlowCommand
from atguigu.task.flow.flows import FlowsList


class CommandProcessor:
    """
    命令处理器
    """
    
    def run(
            self,
            commands: list[Command],
            state: DialogueState,
            flows: FlowsList,
    ) -> None:
        """
        把命令应用到 state
        :param commands:
        :param state:
        :param flows:
        :return:
        """
        for command in commands:
            self._apply(command, state, flows)


    def _apply(
            self,
            command: Command,
            state: DialogueState,
            flows: FlowsList,
    ) -> None:
        """
        处理命令
        :param command:
        :param state:
        :param flows:
        :return:
        """
        if isinstance(command, StartFlowCommand):
            self._handle_start_flow(command, state, flows)
        elif isinstance(command, SetSlotsCommand):
            self._handle_set_slots(command, state)
        elif isinstance(command, CancelFlowCommand):
            self._handle_cancel_flow(state, flows)
        elif isinstance(command, ResumeFlowCommand):
            self._handle_resume_flow(command, state, flows)
```

骨架很简单：`run` 逐条遍历，`_apply` 按命令类型分发到四个 `_handle_*` 方法。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/07-run 与 _apply.png" style="zoom: 67%;" />

### 3.2 为什么是"逐条应用"

一轮里可能有多条命令。最常见的组合：用户说"我要退款，订单号 A001"，LLM 拆成两条：

```python
[
    StartFlowCommand(command="start_flow", flow="refund_request"),
    SetSlotsCommand(command="set_slots", slots={"order_number": "A001"}),
]
```

`run` 会**按顺序**应用：先 `start_flow` 创建退款任务，再 `set_slots` 把订单号填进去。顺序很重要——必须先有活跃任务，`set_slots` 才有地方填。下面四章逐个拆解这四个 `_handle_*`。

### 3.3 依赖注入

`atguigu/api/routers/dependencies.py` 文件 `get_dialogue_engine`方法中修改  `return DialogueEngine`

```python
async def get_dialogue_engine():
    
    ...其他代码
    
    return DialogueEngine(
        turn_planner = TurnPlanner(),
        task_handler = TaskHandler(flows=flow_list, command_processor=CommandProcessor()),
        knowledge_handler = KnowLedgeHandler(knowledge_intents=KNOWLEDGE_INTENTS),
        clarify_responder = ClarifyResponder(),
        turn_plan_validator = TurnPlanValidator())
```

## 第4章 开启流程（最复杂）

这是四个处理方法里**最复杂**的一个，因为"开启一个流程"在不同处境下行为完全不同。

### 4.1 _readable_flow_name：取流程显示名

把 flow_id（如 `refund_request`）转成可读的中文名（如"退款申请"）。系统过场要说"先把**退款申请**放一放"，用的就是这个名字。查不到就退而用 flow_id 本身，保证不崩。

文件 `atguigu/task/command/processor.py`：

```python
@staticmethod
def _readable_flow_name(flow_id: str, flows: FlowsList) -> str:
    flow = flows.get_flow_by_id(flow_id)
    return flow.name if flow else flow_id
```

### 4.2 激活三个系统过场

三个方法长得几乎一样，都是"创建一个 SystemContext"。这些 SystemContext 被激活后，会成为 `active_system_task`。阶段2`FlowExecutor` 会先处理它（让系统先说那句过场白），再继续业务流程。系统过场的文案，就来自 `system_flows.yml` 里对应流程的 action 步骤（带 `{{ context.started_flow_name }}` 这类模板变量）。

文件 `atguigu/task/command/processor.py`：

```python
@staticmethod
def _activate_started_system_flow(state: DialogueState, flows: FlowsList, started_flow_id: str, started_flow_name: str):
    flow = flows.get_flow_by_id("system_task_started")
    state.start_active_system_task(StartedSystemContext(
        #flow_id=flow.id,
        step_id=flow.start_step().id,
        started_flow_id=started_flow_id,
        started_flow_name=started_flow_name,
    ))

@staticmethod
def _activate_interrupted_system_flow(
        state: DialogueState, flows: FlowsList, interrupted_flow_id: str,interrupted_flow_name: str,
        started_flow_id: str,started_flow_name: str):

    flow = flows.get_flow_by_id("system_task_interrupted")
    state.start_active_system_task(InterruptedSystemContext(
        #flow_id=flow.id,
        step_id=flow.start_step().id,
        interrupted_flow_id=interrupted_flow_id,
        interrupted_flow_name=interrupted_flow_name,
        started_flow_id=started_flow_id,
        started_flow_name=started_flow_name
    ))

@staticmethod
def _activate_resumed_system_flow(
        state: DialogueState, flows: FlowsList,
        resumed_flow_id: str, resumed_flow_name: str):

    flow = flows.get_flow_by_id("system_task_resumed")
    state.start_active_system_task(ResumedSystemContext(
        #flow_id=flow.id,
        step_id=flow.start_step().id,
        resumed_flow_id=resumed_flow_id,
        resumed_flow_name=resumed_flow_name
    ))

@staticmethod
def _activate_canceled_system_flow(
        state: DialogueState,
        flows: FlowsList,
        canceled_flow_id: str,
        canceled_flow_name: str
):
    """"
    激活取消流程的过场白
    """
    flow = flows.get_flow_by_id("system_task_canceled")
    state.start_active_system_task(CanceledSystemContext(
        #flow_id=flow.id,
        step_id=flow.start_step().id,
        canceled_flow_id=canceled_flow_id,
        canceled_flow_name=canceled_flow_name
    ))
```

### 4.3 代码

文件 `atguigu/task/command/processor.py`：

只包含基本步骤的最简单版本：

```python
def _handle_start_flow_v1(self, command: StartFlowCommand, state: DialogueState, flows: FlowsList) -> None:
    """
    开启业务任务-基础版
    :param command:
    :param state:
    :param flows:
    :return:
    """

    # 1. 激活业务任务
    target_flow = flows.get_flow_by_id(command.flow)
    start_step = target_flow.start_step()
    state.start_active_task(TaskContext(flow_id=command.flow, step_id=start_step.id))

    # 2. 激活系统流程："开始"过场
    self._activate_started_system_flow(
        state, flows, command.flow, self._readable_flow_name(command.flow, flows),
    )
```

完整版本：

```python
def _handle_start_flow(self, command: StartFlowCommand, state: DialogueState, flows: FlowsList) -> None:
    """
    开启业务任务
    :param command:
    :param state:
    :param flows:
    :return:
    """

    # 清除当前系统流程
    state.end_active_system_task()

    # 防御:不允许直接启动 system_ 开头的内部流程
    if command.flow.startswith("system_"):
        raise ValueError(f"不能直接启动系统流程：'{command.flow}'")

    # 校验:流程必须存在
    target_flow = flows.get_flow_by_id(command.flow)
    if target_flow is None:
        raise ValueError(f"未知流程：'{command.flow}'.")

    # 校验:流程必须有起点
    start_step = target_flow.start_step()
    if start_step is None:
        raise ValueError(f"流程 '{command.flow}' 没有开始步骤")

    active_task = state.active_task

    # ===== 情况一:当前有活跃任务 =====
    if active_task is not None:

        # 同一个流程：不重复启动
        if active_task.flow_id == command.flow:
            return

        # 不是同一个流程：把当前任务放进暂停栈
        state.interrupted_active_task()

        # 试着从暂停栈恢复要开的流程
        resumed = state.resumed_active_task(command.flow)
        if not resumed:
            # 要开的流程不在暂停栈 → 新建
            state.start_active_task(TaskContext(flow_id=command.flow, step_id=start_step.id))

        # 激活"打断"过场
        interrupted_flow_id = active_task.flow_id
        interrupted_flow_name = self._readable_flow_name(active_task.flow_id, flows)
        started_flow_id = command.flow
        started_flow_name = self._readable_flow_name(command.flow, flows)
        self._activate_interrupted_system_flow(
            state, flows, interrupted_flow_id, interrupted_flow_name,
            started_flow_id, started_flow_name)

        return

    # ===== 情况二:当前没有活跃任务 =====
    # 试着恢复同名任务
    resumed = state.resumed_active_task(command.flow)
    if resumed:
        # 要开的流程在暂停栈 → 激活"恢复"过场
        self._activate_resumed_system_flow(
            state, flows, command.flow, self._readable_flow_name(command.flow, flows)
        )
        return

    # 要开的流程从没做过 → 新建
    state.start_active_task(TaskContext(flow_id=command.flow, step_id=start_step.id))
    self._activate_started_system_flow(
        state, flows, command.flow, self._readable_flow_name(command.flow, flows)
    )
```

代码很长，但骨架是清晰的：**先做三道前置检查，再按"有没有活跃任务"分两大情况，每种情况内部再按"要开的流程在不在暂停栈"分支**。下面拆开讲。

### 4.4 开启流程全景

把五个分支汇成一张图：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/07-把五个分支汇成一张图：.png" style="zoom:67%;" />

#### 4.4.1 场景1 当前有活跃任务

用户正在办一件事，又要开另一件。

##### 场景 A

正在查物流，突然要退款（全新的退款），代码走分支 ②

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/07-当前有活跃任务（打断场景）.png" style="zoom:67%;" />

##### 场景 B

A 任务中要切到 B，而 B 之前被挂起过，代码走分支 ③

```
【B任务】
用户：我要退款
AI：请告我你的订单号
用户：DJ001
AI：请告诉我你的退款原因
【切到A任务】              ---> 将 B任务放在paused_tasks 列表中（挂起B任务）
用户：帮我查一下物流
AI：请告我你的订单号
【切回B任务】              ---> 需要还原B任务
用户：我要退款
```

##### 场景 C

重复start 同一个流程，已经在办退款了，直接 return，什么都不做，走分支 ①

```text
用户：我要退款
AI：请告我你的订单号
用户：DJ001
AI：请告诉我你的退款原因
用户：我要退款                --->  正在处理退款，又要求开启退款流程
```

#### 4.4.2 场景2 当前没有活跃任务

没有正在做的事，用户开一个流程，相对简单——只看要开的流程在不在暂停栈。

##### 场景 D

什么都没做，开一个全新流程，代码走分支 ⑤

```text
(active_task = None, paused_tasks = [])
用户:我要退款                  ← start_flow refund_request
客服:好的,我们先处理退款申请。   ← Started 过场
客服:请告诉我你的订单号。
```

##### 场景 E

什么都没做，但要开的流程之前做过一半，走分支 ④

```text
【B任务】
用户：我要退款
AI：请告我你的订单号
用户：DJ001
AI：请告诉我你的退款原因
【切到A任务】              ---> 将 B任务放在paused_tasks 列表中（挂起B任务）
用户：帮我查一下物流
AI：请告我你的订单号
用户：DJ001
AI：你的订单DJ001物流状态是"运输中"    ---> A任务已结束，没有active_task
【切回B任务】              ---> 还原B任务
用户：我要退款
AI：好的,我们继续刚才的退款申请。  ← Resumed 过场(注意是"继续"不是"开始")
AI：请简单说一下退款原因。   ← 接着之前进度
```

## 第5章 填写槽位（最简单）

### 5.1 代码

文件 `atguigu/task/command/processor.py` 中添加如下方法：

```python
def _handle_set_slots(self, command: SetSlotsCommand, state: DialogueState):
    if state.active_task:
        state.set_slots(command.slots)
```

四个处理方法里最简单的一个：**有活跃任务才填，否则什么都不做**。

### 5.2 场景：填订单号

#### 场景 A

流程问订单号，用户回答

```text
用户:我要退款
客服:请告诉我你的订单号。        ← 退款流程停在收集 order_number
用户:A001                       ← set_slots {order_number: A001}
客服:请简单说一下退款原因。       ← 订单号填好,流程推进到下一步
```

#### 场景 B

一次填多个槽：如果用户说"订单 A001，因为尺码不对"，LLM 可能一次给多个槽：

```python
用户:我要退款
客服:请告诉我你的订单号。        ← 退款流程停在收集 order_number
用户:订单 A001，因为尺码不对     ← set_slots {order_number: A001, refund_reason: 尺码不合适}
```

`state.set_slots` 用 `dict.update`，多个键一次合并进去。退款需要的两个槽一次填齐，流程就能直接跑到提交。

#### 场景 C

点击订单卡片填槽：用户点订单卡片、且当前流程正缺 order_number 时，引擎会构造一个 `SetSlotsCommand` 。它最终会调用这个 `_handle_set_slots`。

```python
用户:我要退款
客服:请告诉我你的订单号。        ← 退款流程停在收集 order_number
用户: [点击订单卡片]            ← set_slots {order_number: A001}
客服:请简单说一下退款原因。      ← 订单号填好,流程推进到下一步
```

## 第6章 取消流程

### 6.1 代码

三步：

- 记下当前任务是哪个
- `cancel_active_task()` 清空它
- 激活"取消"过场，让系统说"好的，xx 已为你取消"。

文件 `atguigu/task/command/processor.py`：

```python
def _handle_cancel_flow(self, state: DialogueState, flows: FlowsList):

    # 获取当前流程
    active_task = state.active_task

    # 取消当前流程
    state.cancel_active_task()

    # 激活系统流程：“取消”过场
    canceled_flow_id = active_task.flow_id,
    canceled_flow_name = self._readable_flow_name(canceled_flow_id, flows)
    self._activate_canceled_system_flow(
        state, flows, canceled_flow_id, canceled_flow_name
    )
```

### 6.2 场景：取消退款

办退款途中放弃

```text
用户:我要退款
客服:请告诉我你的订单号。       ← active_task = refund_request
用户:算了不退了                ← cancel_flow
客服:好的,退款申请先帮你取消。   ← Canceled 过场
```

## 第7章 恢复挂起的流程

### 7.1 完整代码

```python
def _handle_resume_flow(self, command: ResumeFlowCommand, state: DialogueState, flows: FlowsList):
    # ===== 第一步:确定要恢复哪个流程 =====
    if command.flow is not None:
        # 指名恢复:用户明确说了恢复哪个
        target_flow = flows.get_flow_by_id(command.flow)
        if target_flow is None:
            raise ValueError(f"未知流程 '{command.flow}'.")
        target_flow_id = target_flow.id
        target_flow_name = target_flow.name
    else:
        # 不指名恢复:用户只说"继续刚才的" → 取暂停栈栈顶(最近挂起的)
        if not state.paused_tasks:
            return
        top_paused = state.paused_tasks[-1]
        target_flow_id = top_paused.flow_id
        target_flow_name = self._readable_flow_name(target_flow_id, flows)

    # ===== 第二步:按"当前有没有活跃任务"恢复 =====
    active_task = state.active_task
    if active_task is not None:
        if active_task.flow_id == target_flow_id:
            return  # 已经在办它,不重复
        interrupted_flow_id = active_task.flow_id
        interrupted_flow_name = self._readable_flow_name(active_task.flow_id, flows)
        state.interrupted_active_task()
        if not state.resumed_active_task(target_flow_id):
            state.resumed_active_task()  # 恢复失败,回退（将state.interrupted_active_task()压入栈顶的任务出栈）
            return
        self._activate_interrupted_system_flow(  # ③打断当前+恢复目标
            state, flows, interrupted_flow_id, interrupted_flow_name,
            target_flow_id, target_flow_name)
    else:
        if not state.resumed_active_task(command.flow):  # ④没任务,直接恢复
            return

        resumed = state.active_task
        self._activate_resumed_system_flow(
            state, flows, resumed.flow_id, self._readable_flow_name(resumed.flow_id, flows))

```

### 7.2 恢复与挂起全景

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/07-恢复与挂起全景.png" style="zoom: 80%;" />

四个分支对应的"用户处境 → 系统反应"：

| 分支 | 用户处境                             | 系统过场                        |
| ---- | ------------------------------------ | ------------------------------- |
| ①    | 要恢复的就是当前正办的               | 无（不重复）                    |
| ②    | 要恢复的不在暂停栈                   | 无（回退，静默）                |
| ③    | 办 A 时要回到挂起的 B                | Interrupted（先放下 A，处理 B） |
| ④    | 没事做，回到挂起的任务（指名或栈顶） | Resumed（继续刚才的 X）         |

#### 7.2.1 场景1：当前有活跃任务

确定了恢复目标后，如果当前正办着别的事，要先打断它，再恢复目标。

**场景 7.3.A：办 A 时，要回去办挂起的 B（指名）**

```text
(paused_tasks = [refund_request], active_task = logistics_tracking)
用户:先不查物流了,继续刚才的退款    ← resume_flow(flow="refund_request")
客服:好的,先把物流查询放一放,先处理退款申请。
客服:请简单说一下退款原因。        ← 退款带着旧进度回来
```

**场景 7.3.B：恢复失败的回退（防御）**

如果要恢复的流程不在暂停栈里（比如 LLM 判断错、或栈里根本没有它）：

```python
state.interrupted_active_task()	 # 已经把当前任务挤进了暂停栈
if not state.resumed_active_task(target_flow_id):	# 但目标不在暂停栈,恢复失败
    state.resumed_active_task()  # 回退:把刚挤进去的任务再恢复回来
    return
```

这里有个精妙的**回退**：前一步已经 `interrupted_active_task()` 把当前任务挤进了暂停栈，如果接着恢复目标失败，不能让当前任务就这么被挂起——所以调用无参的 `state.resumed_active_task()`（恢复最近挂起的，也就是刚被挤进去的那个），把状态还原，当作什么都没发生。

> 这是"操作要么全做、要么回滚"的典型：先动了 state，发现做不下去，就把动过的撤回来。

#### 7.2.2 场景2：当前没有活跃任务

没有正在办的事，直接恢复目标即可，不涉及打断。

**场景 7.4.A：没事做，回到挂起的退款（指名）**

```text
(active_task = None, paused_tasks = [refund_request])
用户:继续刚才的退款            ← resume_flow(flow="refund_request")
客服:好的,我们继续刚才的退款申请。  ← Resumed 过场
客服:请简单说一下退款原因。
```

**场景 7.4.B：没事做，"继续刚才的"（不指名）**

```text
(active_task = None, paused_tasks = [order_status_query, logistics_tracking])
用户:继续刚才的              ← resume_flow(flow=None)
客服:好的,我们继续刚才的物流查询。  ← 恢复栈顶 logistics_tracking
```

## 第8章 串起来：一个完整的多命令例子

把四种命令放到一个连续对话里，看 CommandProcessor 怎么一步步改 state。

```text
[1] 用户:我要查订单状态
[2] 用户:先帮我查物流
[3] 用户:A001
[4] 用户:算了,还是看订单状态吧
```

**[1] "我要查订单状态"** → `start_flow(order_status_query)`

- 无 active_task，暂停栈空 → 新建 + Started 过场

```python
active_task  = order_status_query(step=ask_order_number)
paused_tasks = []
```

**[2] "先帮我查物流"** → `start_flow(logistics_tracking)`

- 有 active_task（订单状态），目标不同，物流不在暂停栈 → 打断+新建 + Interrupted 过场

```python
active_task  = logistics_tracking(step=ask_order_number)
paused_tasks = [order_status_query]
```

**[3] "A001"** → `set_slots({order_number: A001})`

- 有 active_task（物流）→ 填进去

```python
active_task  = logistics_tracking(slots={order_number: A001})
paused_tasks = [order_status_query]
```

**[4] "算了，还是看订单状态吧"** → 这里 LLM 可能产出 `resume_flow(order_status_query)`

- 有 active_task（物流），目标是订单状态（在暂停栈）→ 打断物流+恢复订单状态 + Interrupted 过场

```python
active_task  = order_status_query   ← 从暂停栈恢复
paused_tasks = [logistics_tracking] ← 物流反过来被挂起
```

可以看到，四条命令一路改下来，`active_task` 和 `paused_tasks` 像一个栈一样此起彼伏。这正是这套设计要支撑的"多任务穿插"能力。

## 第9章 小结

### 9.1 这一节实现了什么

| 文件                        | 内容                                                         |
| --------------------------- | ------------------------------------------------------------ |
| `task/handler.py`           | `TaskHandler`：两阶段协调（本节只实现阶段1调用）             |
| `task/command/processor.py` | `CommandProcessor`：四种命令的处理 + 三个激活辅助 + `_readable_flow_name` |

### 9.2 四种命令处理对照

| 命令                  | 核心动作               | 分支数 | 复杂度 |
| --------------------- | ---------------------- | ------ | ------ |
| `_handle_start_flow`  | 建/恢复任务 + 打断     | 5      | 最高   |
| `_handle_resume_flow` | 恢复挂起任务（含回退） | 4      | 高     |
| `_handle_cancel_flow` | 清空当前任务           | 1      | 低     |
| `_handle_set_slots`   | 填槽位                 | 1      | 最低   |

### 9.3 几个值得学习的设计

1. **命令逐条应用**：一轮可能多条命令（如 start+set_slots），按顺序改 state，顺序有意义。
2. **start_flow 的五种处境**：有无活跃任务 × 目标在不在暂停栈，决定新建/恢复/打断/不响应，并激活对应的系统过场。
3. **改状态 + 激活过场成对出现**：每次改任务状态，都顺手激活一个 SystemContext，让系统能说出贴合处境的过场白。
4. **操作可回退**：resume_flow 里"先 interrupt 再尝试 resume，失败就回退"，是"要么全做要么撤销"的典型。
5. **取消 vs 打断**：丢弃 vs 挂起，这是任务生命周期里最需要分清的一对。
6. **resume 支持指名与不指名**：`command.flow` 指名时精确恢复某个流程；为 None（"继续刚才的"）时取暂停栈栈顶（LIFO），贴合"接着最近那件事"的对话直觉。



# 八、Action 实现（所有动作）

---

## 第1章 任务目标

上一节 `CommandProcessor` 把对话状态改好了——任务建好、槽位填好、系统过场激活。但到目前为止，**还没有任何"干实事"的代码**：没有去查订单、没有调物流接口、没有生成回复文本。这些"实事"，就是这一节的主角——**Action**。

### 1.1 Action 在整个系统里的位置

回顾流程编排那一节，YAML 流程里有一种 `action` 步骤：

```yaml
- id: lookup_order_status
  type: action
  action: action_lookup_order_status   # ← 这里引用一个 action 名
  next: show_order_status
```

YAML 只负责"编排"——规定先做什么、后做什么。但"具体怎么查订单""怎么生成回复"这些**真正的业务实现**，YAML 写不了，得交给 Python 代码。这段 Python 代码，就是一个 `Action`。

<img src="C:\Users\YuanYi\Desktop\2.资料\1.笔记\images\08-Action 在整个系统里的位置.png" style="zoom: 80%;" />

### 1.2 本节范围

这一节把**所有 action 以及它们的支撑框架**一次性实现完，但**仍不实现 FlowExecutor**。

| 内容                                                   | 本节     |
| ------------------------------------------------------ | -------- |
| Action 基类、ActionResult                              | ✅        |
| ActionRegistry 注册表、ActionRunner 执行器、ActionCall | ✅        |
| 内置 action：ActionResponse（三模式）、ActionListen    | ✅        |
| 自定义 action：查订单、查物流、推荐商品                | ✅        |
| shared：调用电商接口的工具函数                         | ✅        |
| action 的自动注册（builder）                           | ✅        |
| FlowExecutor（谁来调这些 action）                      | ⛔ 下一节 |

### 1.3 action 全景

这一节要实现的所有 action：

| 类别   | action 名                           | 干什么                     |
| ------ | ----------------------------------- | -------------------------- |
| 内置   | `action_response`                   | 生成一条回复（三种模式）   |
| 内置   | `action_listen`                     | 哨兵：表示"该等用户输入了" |
| 自定义 | `action_lookup_order_status`        | 调订单接口查状态           |
| 自定义 | `action_lookup_logistics`           | 调物流接口查进度           |
| 自定义 | `action_recommend_similar_products` | 推荐相似商品（占位）       |

## 第2章 Action 框架：四个核心概念

在看具体 action 之前，先把支撑它们的四个框架概念理清楚：`Action`（基类）、`ActionResult`（返回值）、`ActionRegistry`（注册表）、`ActionRunner`（执行器）。

### 2.1 Action：所有动作的基类

创建文件：`atguigu/task/action/base.py`

```python
# atguigu/task/action/base.py

from abc import ABC, abstractmethod
from typing import Any
from atguigu.domain.state import DialogueState

  
class Action(ABC):
    name: str #Action的名字

    @abstractmethod
    async def run(
            self,
            state: DialogueState,
            action_kwargs: dict[str, Any],
    ) -> ActionResult:
        pass
```

每个 action 都是 `Action` 的子类，要做两件事：

- 定一个唯一的 `name`（和 YAML 里 `action: xxx` 对上）
- 实现 `run` 方法：拿到当前 `state` 和参数 `action_kwargs`，干活，返回 `ActionResult`

`run` 是 `async` 的——因为很多 action 要调外部接口（查订单/物流），是高延迟 I/O，必须异步。

### 2.2 ActionResult：动作的产物

文件：`atguigu/task/action/base.py`，定义在`class Action(ABC):` 的上方

```python
# atguigu/task/action/base.py

from atguigu.domain.messages import BotMessage
from pydantic import BaseModel

class ActionResult(BaseModel):
    messages: list[BotMessage] = [] # 要发给用户的回复
    slot_updates: dict[str, Any] = {} # 要写回 state 的槽位
```

一个 action 干完活，会产出两类东西之一（或都不产出）：

| 字段           | 含义                | 哪种 action 用                          |
| -------------- | ------------------- | --------------------------------------- |
| `messages`     | 要发给用户的回复    | 生成回复类（action_response、推荐商品） |
| `slot_updates` | 要写回 state 的槽位 | 查询类（查订单、查物流）                |

### 2.3 ActionRegistry：Action注册表

创建文件：`atguigu/task/action/registry.py`

```python
# atguigu/task/action/registry.py

from atguigu.task.action.base import Action


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, Action] = {}

    def register(self, action: Action) -> None:
        self._actions[action.name] = action

    def get(self, name: str) -> Action:
        if name not in self._actions:
            raise KeyError(f"Unknown action '{name}'.")
        return self._actions[name]
```

注册表维护一张 `name -> Action 实例` 的表。它的意义是**解耦**：YAML 里写的是 action 的**名字**（字符串 `action_lookup_order_status`），而真正执行的是 Python **实例**。注册表负责把名字翻译成实例。

<img src="C:\Users\YuanYi\Desktop\2.资料\1.笔记\images\08-动作注册表.png" style="zoom:67%;" />

这又是课程里反复出现的"字符串 → 对象"映射套路，和 `STEP_TYPE_TO_CLASS`、`COMMAND_NAME_TO_CLASS` 同源。

### 2.4 ActionRunner 与 ActionCall：动作执行器

创建文件：`atguigu/task/action/runner.py`

```python
# atguigu/task/action/runner.py

from typing import Any

from pydantic import BaseModel

from atguigu.task.action.registry import ActionRegistry
from atguigu.task.action.base import ActionResult
from atguigu.domain.state import DialogueState


class ActionCall(BaseModel):
    action_name: str
    action_kwargs: dict[str, Any] = {}

# 面向修改关闭，面向扩展开放
class ActionRunner:
    """
    通过给定的action_call，执行action
    """
    def __init__(self, registry: ActionRegistry) -> None:
        self.registry = registry

    async def run(self, action_call: ActionCall, state: DialogueState) -> ActionResult:
        # 1. 获取action的名字
        action_name = action_call.action_name

        # 2. 从Action注册中心获取名字对应的Action的实例对象
        action = self.registry.get(action_name)

        # 3. 调用具体Action的逻辑
        return await action.run(state, action_call.action_kwargs)
```

- `ActionCall`：一次动作调用请求，装着"调哪个 action（`action_name`）+ 传什么参数（`action_kwargs`）"。它由下一节的 `FlowExecutor` 构造。
- `ActionRunner.run`：拿到 `ActionCall`，从注册表查出 action 实例，调它的 `run`，返回结果。
- `ActionRunner` 自己不关心 action 内部干什么，它只做三件事：**查表 → 调用 → 返回**。

### 2.5 四个概念的协作

一句话串起来：FlowExecutor 想执行某个 action，就构造一个 `ActionCall` 交给 `ActionRunner`；`ActionRunner` 拿 name 去 `ActionRegistry` 查出 `Action` 实例，调它的 `run`，把 `ActionResult` 还回去。

<img src="C:\Users\YuanYi\Desktop\2.资料\1.笔记\images\08-四个概念的协作.png" style="zoom: 67%;" />

## 第3章 Action

### 3.1 ActionListen

`ActionListen` 是一个"哨兵"，不干任何活，只起一个**信号标记**作用，表示"流程跑到这里，该停下来等用户输入了"。

创建文件：`atguigu/task/action/builtin/action_listen.py`

```python
# atguigu/task/action/builtin/action_listen.py
import asyncio
from typing import Any

from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class ActionListen(Action):
    """
    什么都不做，返回空的ActionResult
    """
    name = "action_listen"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        print("action_listen")
        return ActionResult()


if __name__ == '__main__':
    action =  ActionListen()
    asyncio.run(action.run(None, None))
```

回顾 `system_collect_information` 流程：

```yaml
- id: ask
  type: action
  action: action_response      # 先问"请告诉我你的订单号。"
  args: context.response
  next: listen
- id: listen
  type: action
  action: action_listen        # 然后停下来,等用户回答
  next: end
```

收集槽位时，系统先用 `action_response` 问一句，再用 `action_listen` 把流程"挂起"，等用户下一句输入。

`action_listen` 的真正作用要在下一节 `FlowExecutor` 里才看得清，下一节 `FlowExecutor` 的外层循环里会有这样一行判断：

```python
if action_call.action_name == "action_listen":
    break
```

也就是说，`action_listen` 是"该等用户输入了"的退出信号。流程跑到这一步，意味着系统已经把该说的都说完了，下面该让用户开口了。

### 3.2 ActionResponse

`action_response` 是最重要、也最复杂的 action，几乎所有"**对用户说话**"都靠它。它支持三种模式。

#### 3.1.1 三种模式总览

ActionResponse支持三种模式

| mode       | 用 LLM 吗 | 适用场景                              |
| ---------- | --------- | ------------------------------------- |
| `static`   | 否        | 文案已写死在 YAML，直接用             |
| `rephrase` | 是        | 有模板底稿，但想说得更自然，让LLM润色 |
| `generate` | 是        | 没有预设文案，直接让LLM从零生成       |

<img src="C:\Users\YuanYi\Desktop\2.资料\1.笔记\images\08-三种模式总览.png" style="zoom:67%;" />



创建文件：`atguigu/task/action/builtin/action_response.py`

```python
# atguigu/task/action/builtin/action_response.py

from typing import Any

from jinja2 import Template
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.infrastructure.llm import llm
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.task.action.base import Action, ActionResult


class ActionResponse(Action):
    name = "action_response"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        """
        响应内容
        :param state:
        :param action_kwargs:
        :return:
        """

        mode = action_kwargs.get("mode", "static")
        if mode == "static":
            text = action_kwargs['text']
            rendered_text = self._render_text(text, state)
            return ActionResult(messages=[BotMessage(text=rendered_text)])

        elif mode == "rephrase":
            text = action_kwargs['text']
            rendered_text = self._render_text(text, state)
            prompt_text = action_kwargs['prompt']
            message = await self._call_llm(prompt_text, state, rendered_text)
            return ActionResult(messages=[BotMessage(text=message)])

        else:  # generate
            prompt_text = action_kwargs['prompt']
            message = await self._call_llm(prompt_text, state)
            return ActionResult(messages=[BotMessage(text=message)])

    def _render_text(self, text: str, state: DialogueState) -> str:
        # 把模板里的 {{  }} 替换成真实值。
        template = Template(text)
        result = template.render(
            slots=state.active_task.slots if state.active_task else {},
            context=state.active_system_task or state.active_task,
        )
        return result

    async def _call_llm(self, prompt_text: str, state: DialogueState, rendered_text: str = "") -> str:
        """
        rephrase 和 generate 都走这个方法，区别在传不传 rendered_text
        :param prompt_text:
        :param state:
        :param rendered_text:
        :return:
        """
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm | StrOutputParser()

        bot_message = await chain.ainvoke({
            "history": HistoryBuilder.build(state.current_session().turns),
            "user_message": HistoryBuilder._render_user_message(state.pending_turn.user_message),
            "current_response": rendered_text,
        })
        return bot_message

if __name__ == '__main__':

    data = "好的，订单{{ order_number }}的退款申请已提交"
    template = Template(data)
    res = template.render(order_number="12345")

    # data = "好的，订单{{ slots.order_number }}的退款申请已提交"
    # template = Template(data)
    # res = template.render(slots={"order_number": "12345"})
    print(res)

```

#### 3.1.2 static 模式

最常用的模式。YAML 里写好文案模板，直接渲染：

```yaml
- id: show_order_status
  type: action
  action: action_response
  args:
    text: "订单{{ slots.order_number }}当前状态是：{{ slots.order_status }}。{{ slots.order_summary }}"
  next: end
```

模板里能访问两个变量：

| 变量      | 是什么                                   | 例子                                     |
| --------- | ---------------------------------------- | ---------------------------------------- |
| `slots`   | 当前任务收集/查到的槽位                  | `slots.order_number` → "A001"            |
| `context` | 当前上下文（系统过场优先，否则业务任务） | `context.started_flow_name` → "退款申请" |

举例：查完订单状态后，`slots` 里已经有了 `order_number="A001"`、`order_status="已发货"`、`order_summary="订单金额 ¥99。"`，渲染上面那个模板得到：

```text
订单A001当前状态是：已发货。订单金额 ¥99。
```

> 注意 `context` 变量：业务流程里它是 active_task，**系统流程**里它是 active_system_task。这就是为什么 `system_flows.yml` 里能写 `{{ context.started_flow_name }}`，因为 context 指向的是 `StartedSystemContext`，带着 `started_flow_name` 字段。

#### 3.1.3 rephrase 模式

有时候 YAML 里写死的文案太生硬，想让它更自然。rephrase 模式：先渲染出底稿，再交给 LLM 润色。

`text` 是底稿（建议回复），`prompt` 是给 LLM 的润色指令。注意 prompt 里的 `{{ current_response }}`就是渲染好的底稿，LLM 在它的基础上改写。

`system_flows.yml` 的 `system_cannot_handle` 流程就用了它：

```yaml
- id: ask_rephrase
  type: action
  action: action_response
  args:
    mode: rephrase
    text: "抱歉，我这边没有完全听明白。你可以再具体说一下你想处理什么电商问题吗？"
    prompt: |
      你是一个中文电商客服助手，语气自然、友好、简洁。
      请基于下面的建议回复，生成一句更自然的中文回复，保持原意，不要扩写。
      对话上下文：
      { history }
      用户最后一句：
      用户：{ user_message }
      建议回复：{ current_response }
      改写后的回复：
```

#### 3.1.4 generate 模式

没有预设文案，完全靠 LLM 按 prompt从零 生成。`run` 里 generate 分支不读 `text`，只用 `prompt`

### 3.3 自定义 action

内置 action 是通用的（发消息、等输入），而**查订单、查物流**这类具体业务，放在 `custom/` 目录下，是自定义 action。它们的共性是：**调电商后端的 HTTP 接口，把结果写回槽位**。

#### 3.3.1 shared.py：调接口的工具函数

自定义 action 都要调电商接口

创建文件：`atguigu/task/action/custom/shared.py`

```python
# atguigu/task/action/custom/shared.py

from urllib.parse import quote
from atguigu.conf.config import settings
from atguigu.infrastructure import http_client


def _base_url() -> str:
    return settings.commerce_api_base_url.rstrip("/")


def _extract_data(result: dict | None) -> dict | None:
    data = result.get("data") if isinstance(result, dict) else None
    return data if isinstance(data, dict) else None


async def fetch_order(order_id: str) -> dict | None:
    try:
        # 注意此处：
        # 文件头部 from atguigu.infrastructure import http_client
        # 此处使用 http_client.http_client.get(url) 调用

        # 不要这样做：
        # 文件头部 from atguigu.infrastructure.http_client import http_client
        # 此处使用 http_client.get(url) 调用
        # 会使拿到的 http_client 是 None
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id)}")
        return _extract_data(r.json())
    except Exception:
        return None


async def fetch_logistics(order_id: str) -> dict | None:
    try:
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id)}/logistics")
        return _extract_data(r.json())
    except Exception:
        return None


async def fetch_product(product_id: str) -> dict | None:
    try:
        r = await http_client.http_client.get(f"{_base_url()}/products/{quote(product_id)}")
        return _extract_data(r.json())
    except Exception:
        return None
```

三个 fetch 函数分别调订单、物流、商品接口。几个共性设计：

| 设计                   | 说明                                                         |
| ---------------------- | ------------------------------------------------------------ |
| 共享 `http_client`     | 模块级单例，复用连接池，不每次新建（高并发友好）             |
| `quote(order_id)`      | URL 编码，防止 id 里有特殊字符破坏 URL                       |
| `try/except` 返回 None | **优雅降级**：接口挂了不抛异常，返回 None，让上层 action 兜底 |
| `_extract_data`        | 电商接口返回 `{"data": {...}}` 包了一层，统一剥出里面的 data |

`_build_order_summary` 是个辅助函数，把订单数据拼成一句摘要：

文件：`atguigu/task/action/custom/shared.py`

```python
# atguigu/task/action/custom/shared.py

def _build_order_summary(payload: dict[str, Any]) -> str:
    parts = []
    if payload.get("amount"):
        parts.append(f"订单金额 ¥{payload['amount']}")
    items = payload.get("items") or []
    if items:
        titles = [str(item.get("title_snapshot") or "").strip()
                  for item in items[:2] if item.get("title_snapshot")]
        if titles:
            parts.append("商品：" + "、".join(titles))
    return "。".join(parts) + "。" if parts else ""
```

#### 3.3.2 查订单状态

创建文件 `atguigu/task/action/custom/lookup_order_status.py`

```python
# atguigu/task/action/custom/lookup_order_status.py

class LookupOrderStatusAction(Action):
    name = "action_lookup_order_status"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        order_number = state.active_task.slots.get("order_number")
        payload = await fetch_order(order_number)

        if payload is None:
            return ActionResult(slot_updates={
                "order_status": "查询失败",
                "order_summary": "暂时无法查到该订单信息，请稍后再试。",
            })

        return ActionResult(slot_updates={
            "order_status": payload.get("status_desc") or payload.get("status") or "未知",
            "order_summary": _build_order_summary(payload),
        })
```

它的逻辑很典型，是所有"查询类 action"的模板：

1. **从槽位读输入**：`state.active_task.slots.get("order_number")`——订单号是之前 collect 步骤收集来的
2. **调接口**：`fetch_order(order_number)`
3. **失败兜底**：接口返回 None，写一组"查询失败"的降级槽位，保证流程能继续（不会因为没数据而崩）
4. **成功写回**：把查到的状态、摘要打包进 `slot_updates` 返回

注意它返回的是 **slot_updates 而不是 messages**——它只负责"查到数据写回槽位"，至于把这些槽位拼成话发给用户，是后面 `action_response` 的事。

回顾 `order_status_query` 流程，正好印证这个分工：

```yaml
- id: lookup_order_status
  type: action
  action: action_lookup_order_status      # ① 查数据,写进 order_status/order_summary 槽
  next: show_order_status
- id: show_order_status
  type: action
  action: action_response                 # ② 把槽位拼成话发给用户
  args:
    text: "订单{{ slots.order_number }}当前状态是：{{ slots.order_status }}。{{ slots.order_summary }}"
  next: end
```

**查（写槽）和说（读槽生成回复）分成两步** ——这是这套设计的一个典型模式。

#### 3.3.3 查物流

创建文件  `atguigu/task/action/custom/lookup_logistics.py`

```python
# atguigu/task/action/custom/lookup_logistics.py

class LookupLogisticsAction(Action):
    name = "action_lookup_logistics"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        order_number = state.active_task.slots.get("order_number")
        payload = await fetch_logistics(order_number)

        if payload is None:
            return ActionResult(slot_updates={
                "tracking_number": "未知",
                "logistics_company": "未知",
                "logistics_status": "暂时无法查到物流信息，请稍后再试。",
            })

        return ActionResult(slot_updates={
            "tracking_number": payload.get("tracking_number") or "未知",
            "logistics_company": payload.get("logistics_company") or "未知",
            "logistics_status": payload.get("status_desc") or payload.get("status") or "未知",
        })
```

和查订单几乎一样的结构，只是查的是物流、写的是物流相关的三个槽位（单号、公司、进度）。同样是"读 order_number → 调接口 → 写槽 / 失败兜底"。

它在 `logistics_tracking` 流程里也是"查 + 说"两步搭配 `action_response`。

#### 3.3.4 推荐相似商品（占位）

创建文件：`atguigu/task/action/custom/recommend_similar_products.py`

```python
# atguigu/task/action/custom/recommend_similar_products.py
class RecommendSimilarProductsAction(Action):
    name = "action_recommend_similar_products"

    async def run(self, state: DialogueState, action_kwargs: dict[str, Any]) -> ActionResult:
        product_id = state.active_task.slots.get("product_id")
        label = product_id or "这件商品"

        payload = await fetch_product(product_id)
        if payload:
            label = str(payload.get("title") or "").strip() or label

        text = (
            f"我已经收到你对\"{label}\"的相似商品推荐需求。"
            "不过当前版本还没有接入正式的推荐系统，稍后可以继续补上这部分能力。"
        )
        return ActionResult(messages=[BotMessage(text=text)])
```

这是一个**占位 action**——推荐功能还没真正实现，先返回一句"已收到需求，但功能待接入"。

注意它和前两个查询 action 的区别：它返回的是 **messages 而不是 slot_updates**——因为它直接生成回复给用户，不需要后面再接 `action_response`。它会查一下商品名（`fetch_product`）让回复更具体，查不到就用"这件商品"兜底。

#### 3.3.5 三个自定义 action 对照

| action                              | 读什么槽     | 调什么接口 | 产出                             | 后面接什么             |
| ----------------------------------- | ------------ | ---------- | -------------------------------- | ---------------------- |
| `action_lookup_order_status`        | order_number | 订单接口   | slot_updates（状态、摘要）       | action_response 说出来 |
| `action_lookup_logistics`           | order_number | 物流接口   | slot_updates（单号、公司、进度） | action_response 说出来 |
| `action_recommend_similar_products` | product_id   | 商品接口   | messages（直接回复）             | 无（自己就是回复）     |

可以看到两种风格：**查询类**（写槽，留给 action_response 说）和**直接回复类**（自己产出 messages）。

### 3.4 action 的注册

action 写好了，得注册进 `ActionRegistry`，然后`ActionRunner` 才能按名字找到它们。

#### 3.4.1 注册

- 内置 action：手动注册
- 自定义 action：自动发现

创建文件：`atguigu/task/action/builder.py`

```python
# atguigu/task/action/builder.py

import importlib
import inspect
import pkgutil
from atguigu.task.action.runner import ActionRunner
from atguigu.task.action.registry import ActionRegistry
from atguigu.task.action.base import Action
from atguigu.task.action.builtin.action_listen import ActionListen
from atguigu.task.action.builtin.action_response import ActionResponse


def register_builtin_actions(action_runner: ActionRunner):
    """
    注册内置的action：手动 register
    :param action_runner:
    :return:
    """
    action_listen = ActionListen()
    action_response = ActionResponse()
    action_runner.registry.register(action_listen)
    action_runner.registry.register(action_response)


def register_custom_actions(action_runner: ActionRunner):
    """
    扫描指定包，完成 Action子类的自动注册
    :param action_runner:
    :return:
    """

    package = importlib.import_module("atguigu.task.action.custom")

    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, prefix=f"{package.__name__}."):

        # 只处理模块文件，不处理子包
        if is_pkg:
            continue
        module = importlib.import_module(module_name)
        for _, obj in inspect.getmembers(module, inspect.isclass):

            # 只要 Action 的子类，排除基类本身
            if not issubclass(obj, Action) or obj is Action:
                continue

            # 只注册"在这个模块里定义的"类，排除 import 进来的
            # 如 LookUpOrderStatusAction 被 lookup_logistics.py import 时不重复注册
            if obj.__module__ != module.__name__:
                continue
            action_runner.registry.register(obj())

def build_action_runner() -> ActionRunner:
    action_runner = ActionRunner(ActionRegistry())
    register_builtin_actions(action_runner)
    register_custom_actions(action_runner)
    return action_runner

if __name__ == '__main__':

     build_action_runner()
```

#### 3.4.2 自动发现的好处

有了自动发现，**新增一个自定义 action 时，完全不用改注册代码**——只要在 `custom/` 下新建一个文件、写个 `Action` 子类，启动时就会被自动扫到注册。这是开闭原则的又一次体现。

> 例如：想新增"查询优惠券"功能？在 `custom/lookup_coupon.py` 写一个 `class LookupCouponAction(Action)`、设 `name = "action_lookup_coupon"`、实现 `run`，然后在 YAML 里配置 `action: action_lookup_coupon` 即可。注册代码一行都不用动。

#### 3.4.3 依赖注入

文件 `atguigu/task/handler.py` 中添加 `ActionRunner` 的配置

```python
# atguigu/task/handler.py

class TaskHandler:

    def __init__(
            self,
            flows: FlowsList,
            command_processor: CommandProcessor,
            action_runner: ActionRunner):
        self.flows = flows
        self.command_processor = command_processor
        self.action_runner = action_runner
```

文件 `atguigu/api/routers/dependencies.py` 中添加 `action_runner=build_action_runner()` 的配置

```python
# atguigu/api/routers/dependencies.py

return DialogueEngine(
    turn_planner = TurnPlanner(),
    task_handler = TaskHandler(flows=flow_list, command_processor=CommandProcessor(), action_runner=build_action_runner()),
    knowledge_handler = KnowledgeHandler(knowledge_intents = KNOWLEDGE_INTENTS),
    clarify_responder = ClarifyResponder(),
    turn_plan_validator = TurnPlanValidator()
)
```

## 第4章 本节流程

虽然 FlowExecutor 还没实现，但我们可以预演一下"查订单状态"这个流程里 action 是怎么协作的（假设 FlowExecutor 已经在按流程推进）：

```text
用户:查订单状态 A001
```

流程 `order_status_query` 推进到 action 步骤时：

<img src="C:\Users\YuanYi\Desktop\2.资料\1.笔记\images\08-本节流程.png" style="zoom:50%;" />

可以看到两类 action 的配合：

1. `action_lookup_order_status` 负责**查**——调接口、把结果写进槽位（slot_updates）
2. `action_response` 负责**说**——读槽位、渲染成回复（messages）

中间"把 slot_updates 写回 state"这一步由 FlowExecutor 做（下一节）。

## 第5章 小结

### 5.1 这一节实现了什么

| 文件                                               | 内容                                                         |
| -------------------------------------------------- | ------------------------------------------------------------ |
| `task/action/base.py`                              | `Action` 基类、`ActionResult`结果类                          |
| `task/action/runner.py`                            | 通过给定的`action_call`，执行`action`                        |
| `task/action/builder.py`                           | 内置手动注册 + 自定义自动发现                                |
| `task/action/registry.py`                          | `ActionRegistry`， Action注册表                              |
| `task/action/builtin/action_response.py`           | `ActionResponse`（static/rephrase/generate 三模式）          |
| `task/action/builtin/action_listen.py`             | `ActionListen`（哨兵）                                       |
| `task/action/custom/shared.py`                     | `fetch_order` / `fetch_logistics` / `fetch_product` / `_build_order_summary` |
| `task/action/custom/lookup_order_status.py`        | `LookupOrderStatusAction`                                    |
| `task/action/custom/lookup_logistics.py`           | `LookupLogisticsAction`                                      |
| `task/action/custom/recommend_similar_products.py` | `RecommendSimilarProductsAction`                             |

### 5.2 几个值得学习的设计

1. **YAML 是骨架，Action 是血肉**：YAML 编排流程，Action 实现"查 API、发消息、等输入"这些实事。
2. **Action 不直接改 state**：只返回 `ActionResult`（messages / slot_updates），由调用方统一写回。副作用集中可控、易测试。
3. **查与说分离**：查询类 action 写槽（slot_updates），回复类 action（action_response）读槽生成回复。两步搭配。
4. **ActionResponse 三模式**：static（模板）/ rephrase（润色）/ generate（生成），按"要不要 LLM、用 LLM 做什么"区分。static 最常用。
5. **优雅降级**：接口调用 try/except 返回 None，action 写降级槽位，保证流程不崩。
6. **自动发现**：custom 目录下的 action 自动扫描注册，新增 action 不用改注册代码。
7. **action_listen 是哨兵**：本身不干活，作为"该等用户输入了"的信号，下一节 FlowExecutor 靠它退出推进循环。



# 九、FlowExecutor 执行器

## 第1章 任务目标

到目前为止，我们已经造好了所有"零件"：

- 流程定义（YAML 加载成 `FlowsList`）
- 对话状态（`DialogueState`、各种 Context）
- 命令处理（`CommandProcessor` 改 state）
- 各种动作（`Action` 及其子类）

但还差最关键的一步：**谁把这些零件串起来跑？** 谁去读 state、按 YAML 一步步推进、在该执行 action 时调 ActionRunner、在该等用户时停下来？

这就是这一节的主角——**`FlowExecutor`**。

了解 FlowExecutor 在整个系统中的位置，有助于理解它的职责边界。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/09-FlowExecutor位置.png" style="zoom: 67%;" />

## 第2章 整合FlowExecutor

### 2.1 创建FlowExecutor

创建文件： `atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py

from atguigu.domain.state import DialogueState
from atguigu.task.flow.flows import FlowsList
from atguigu.task.action.runner import ActionRunner

class FlowExecutor:
    """
    流程执行器：推进yaml中定义的业务任务流程以及系统任务流程
    """

    async def run_task(self,state: DialogueState,flows: FlowsList,action_runner: ActionRunner):

        pass
```

### 2.2 修改TaskHandler

回顾上一节 并完善`TaskHandler` 的两步：`CommandProcessor` 改完状态就退场，`FlowExecutor` 接手，读取改好的 `state`，按 `YAML` 流程一步步推进，每遇到 `action` 步骤就交给 `ActionRunner` 执行。

完善文件`atguigu/task/handler.py`，添加 `flow_executor` 和步骤2

```python
# atguigu/task/handler.py

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.action.runner import ActionRunner
from atguigu.task.command.models import Command
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.flow.flows import FlowsList

class TaskHandler:

    def __init__(
            self,
            flows: FlowsList,
            command_processor: CommandProcessor,
            action_runner: ActionRunner,
            flow_executor: FlowExecutor
    ):
        self.flows = flows
        self.command_processor = command_processor
        self.action_runner = action_runner
        self.flow_executor = flow_executor

    async def handle(self, commands: list[Command], state: DialogueState) -> list[BotMessage]:
        # 阶段1：CommandProcessor 进行状态的修改
        self.command_processor.run(commands, state, self.flows)

        # 阶段2：FlowExecutor 进行任务/流程的推进
        messages = await self.flow_executor.run_task(state, self.flows, self.action_runner)

        # 返回流程执行器得到的消息
        return messages
```

### 2.3 依赖注入

文件 `atguigu/api/routers/dependencies.py` 中完善 `DialogueEngine` 中的 `task_handler` 配置

```python
# atguigu/api/routers/dependencies.py

return DialogueEngine(
    turn_planner = TurnPlanner(),
    task_handler = TaskHandler(
        flows=flow_list,
        command_processor=CommandProcessor(),
        action_runner=build_action_runner(),
        flow_executor=FlowExecutor()
    ),
    knowledge_handler = KnowledgeHandler(knowledge_intents = KNOWLEDGE_INTENTS),
    clarify_responder = ClarifyResponder(),
    turn_plan_validator = TurnPlanValidator()
)
```

## 第3章 run_task：外层循环

### 3.1 代码

文件： `atguigu/task/flow/executor.py` 

```python
# atguigu/task/flow/executor.py

async def run_task(self,state: DialogueState,flows: FlowsList,action_runner: ActionRunner):

    messages: list[BotMessage] = []
    while True:  # 找要执行的流程步骤

        # 1. 推进流程以及内部step，当step的type类型是action是从advance_until_action中退出
        action_call: ActionCall = self.advance_until_action(state, flows)

        # 2. 当action_name是action_listen的时候，结束流程，并返回消息，等待下一轮的用户输入
        if action_call.action_name == "action_listen":
            break
        else:

            # 3. 如果是其他类型的action，则执行action
            action_result: ActionResult = await action_runner.run(action_call, state)
            state.set_slots(action_result.slot_updates)
            messages.extend(action_result.messages)

    # 4. 返回消息，等待下一轮的用户输入
    return messages
```

### 3.2 三件事

外层循环每一轮做三件事：

1. **找下一个要执行的 action**：调 `advance_until_action`，它会沿流程推进，遇到action则返回，最终返回一个 `ActionCall`
2. **判断要不要退场**：如果拿到的是 `action_listen`，说明该等用户的下一轮输入了，break 退出循环
3. **真正干活**：如果不是`action_listen`，则交给 `ActionRunner` 执行；把 action 返回的**槽位更新**写回 state、把消息添加到消息列表

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/09-外层循环.png" style="zoom: 33%;" />

## 第4章 advance_until_action：内层循环

这是 FlowExecutor 的**心脏**。它沿着 YAML 流程图,跳过不需要执行 action 的步骤，遇到要执行 action 的步骤就返回。

### 4.1 代码

文件： `atguigu/task/flow/executor.py` 

```python
# atguigu/task/flow/executor.py
def advance_until_action(self, state: DialogueState, flows: FlowsList) -> ActionCall:

    while True:

        # 1. 获取当前任务上下文对象：系统任务优先
        current_active_task = state.current_active_task()

        # 2. 如果当前没有任务，手动返回action_listen，等待用户输入
        # 两种典型情况：
        # - 业务流程刚跑完 end 步骤，active_task 被清空，又没有系统过场
        # - 用户刚启动会话，根本还没开任何任务
        if current_active_task is None:
            return ActionCall(action_name="action_listen")

        # 3. 获取当前流程对象
        flow = flows.get_flow_by_id(current_active_task.flow_id)

        # 4. 获取当前step
        step = flow.get_step_by_id(current_active_task.step_id)

        # 5. 运行当前step
        action_call = self._run_step(state, step, flows)

        # 6. 如果step的类型是action,退出while true
        if action_call is not None:
            return action_call
```

### 4.2 没有当前任务的情形

`current_active_taskis None` 时直接返回 `action_listen`——没事可做，等用户输入。

两种典型情况：

- 业务流程刚跑完 `end` 步骤，`active_task` 被清空，又没有系统过场
- 用户刚启动会话，根本还没开任何任务

### 4.3 内层循环做什么

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/09-内层循环流程图.png" style="zoom: 67%;" />

### 4.4 _run_step：按 step 类型分发

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _run_step(self, state: DialogueState, step: FlowStep, flows: FlowsList) -> ActionCall | None:

    if isinstance(step, StartFlowStep):
        return self._run_start_step(step, state)
    if isinstance(step, EndFlowStep):
        return self._run_end_step(state)
    if isinstance(step, CollectFlowStep):
        return self._run_collect_step(step, state, flows)
    if isinstance(step, ActionFlowStep):
        return self._run_action_step(step, state)
```

四种 step 各有处理方法和不同的返回值。返回 `None` 表示"这一步不产生 action，请继续推进"，返回 `ActionCall` 表示"该执行这个 action 了"。

四种 step 的处理 vs 返回值：

| step 类型 | 处理                   | 返回 None 还是 ActionCall |
| --------- | ---------------------- | ------------------------- |
| `start`   | 跳到 next step         | None（继续推）            |
| `end`     | 结束当前 flow          | None（继续推）            |
| `collect` | 自动补槽 + 槽位判断    | 视情况                    |
| `action`  | 推进 + 构造 ActionCall | **ActionCall**            |

后面四章逐个拆解这四种 step 的处理。

## 第5章 处理 start step（最复杂）

### 5.1 代码

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _run_start_step(self, step: StartFlowStep, state: DialogueState) -> None:
    # 1. 推进下一步
    self._advance_next_step(state, step)
    # 2. 返回None
    return None
```

`start` 步骤是流程的**入口标记**。处理两件事：把当前任务的 `step_id` 设成 next step，然后返回 None 让内层循环继续推进流程向后执行。

### 5.2 配合 YAML 看

退款流程的开头：

```yaml
- id: start
  type: start
  next: ask_order_number 
```

当前 step 是 `start` 时，`_advance_to_next_step` 会读 `next: ask_order_number`，把 task 的 `step_id` 改成 `ask_order_number`。下一轮内层循环就从 `ask_order_number` 这个步骤开始处理。

### 5.3 推进的本质

`_advance_to_next_step` 是所有 step 推进的公用方法。

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _advance_next_step(self, state, step):
    # 1. 寻找下一个step id
    next_step_id = self._select_next_step(step, state)
    # 2. 更新当前任务上下文的step_id(给当前执行任务流程的上下文用)不做这个动作，出不来
    state.current_active_task().step_id = next_step_id
```

它的本质：**改 `step_id`**。流程"推进"在代码里就是这么简单——把当前任务记的 step_id 改成下一个 step 的 id。

### 5.4 选择下一步

`_select_next_step` 负责从 `next` 链接中挑出目标 step，条件跳转的核心逻辑就在这里。

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _select_next_step(self, step: FlowStep, state: DialogueState) -> str:

    for link in step.next:
        if isinstance(link, StaticLink):
            return link.target  # 下一个步骤的id
        if isinstance(link, ConditionalLink):
            if self._eval_condition(state, link.condition):
                return link.target
        if isinstance(link, FallbackLink):
            return link.target
    return "没有下一步"
```

回顾流程加载那一节：每个 step 的 `next` 在加载时被解析成一个 `FlowStepLink` 列表。这里就是按列表遍历，决定走哪个 target：

| 链接类型                                 | 处理                                          |
| ---------------------------------------- | --------------------------------------------- |
| `StaticLink`（YAML 写 `next: xxx`）      | 直接返回 target                               |
| `ConditionalLink`（YAML 写 `- if: ...`） | 表达式为真就返回 target，否则跳过看下一个分支 |
| `FallbackLink`（YAML 写 `- else: ...`）  | 直接返回 target（之前的条件都没满足时的兜底） |

回顾推荐相似商品流程，正好用到条件跳转：

```yaml
- id: start
  type: start
  next:
    - if: "slots.get('product_id')"        # 有商品就推荐
      then: respond
    - else: missing_product_context        # 没有就提示先选商品
```

`_select_next_step` 跑下来，会让 `start step` 根据 `slots.get('product_id')` 走向不同的下一步。

### 5.5 计算条件表达式

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _eval_condition(self, state: DialogueState, condition: str) -> bool:
    data = {
        "slots": state.active_task.slots,
        # current_active_task：获取当前任务上下文对象：系统任务优先
        # model_dump：对象转字典
        "context": state.current_active_task().model_dump(mode="json")
    }
    return bool(eval(condition, {'__builtins__': None}, data))
```

#### 5.5.1 代码执行 eval

##### 测试evel

`eval` 是 Python 内置函数，能把**字符串当作代码来执行**。

三个参数分别是：

- `condition`：要执行的字符串，比如 `"slots.get('product_id')"` 这种 YAML 里写的条件
- `{}`：全局变量，这里给空字典，意思是"不允许访问任何全局变量"，比较安全
- `data`：局部变量，也就是代码里能"看到"哪些变量, `data` 是一个字典

```python
# atguigu/test/evel/test1.py
condition = "a>b"
data = {"a": 3, "b": 2}
print(eval(condition, data))
```

另一个例子

```python
# atguigu/test/evel/test2.py
condition = "context.get('reason') == 'xyz'"
data = {
    "context": {"reason": "abc"}
}
print(bool(eval(condition,  data)))
```

##### 安全执行

###### 场景一：如果不限制全局变量（危险）

```python
# atguigu/test/evel/test3.py

# 假设全局变量不限制，eval 能访问 Python 的所有内置功能
condition = "__import__('os').system('del important_file.txt')"
data = {"slots": {}}
result = eval(condition, data)  # 这会把你的文件删掉！
```

###### 场景二： 限制全局变量（安全）

为了"安全"，不给它任何全局能力，只让条件字符串能访问我们主动放进 `data` 的变量。

```python
# atguigu/test/evel/test4.py
condition = "__import__('os').system('del important_file.txt')"
data = {"slots": {}}

# 禁止执行内部函数
result = eval(condition, {'__builtins__': None}, data)
# ❌ 报错！
# 因为全局变量字典被禁用，__import__ 这个函数不存在
```

###### 生活化类比

想象你给小孩一个房间让他玩：

| 做法                                            | 类比                                                         |
| ----------------------------------------------- | ------------------------------------------------------------ |
| `eval(condition)` 不限制                        | 小孩能打开房间里任何柜子，包括刀具柜、药品柜，很危险         |
| `eval(condition, {'__builtins__': None}, data)` | 只给他 `data` 这个玩具箱，房间其他柜子全锁死，他只能玩玩具箱里的 `slots` 和 `context` 两个玩具 |

## 第6章 处理 end step（最简单）

### 6.1 代码

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _run_end_step(self, state: DialogueState) -> None:
    if state.active_system_task:
        # 清空state中系统任务流程上下文
        state.end_active_system_task()
    else:
        # 清空state中业务任务流程上下文
        state.end_active_task()
    return None
```

### 6.2 业务结束和系统过场结束

`end` 步骤标志一个 flow 跑完了，按"当前是系统流还是业务流"分别清掉。

因为两种 end 的语义完全不同。系统流（如过场"好的，先处理退款"）是一个**临时叠加层**，它结束时业务任务还在下面等着，所以只清系统任务。

| 当前                               | 处理                                                  |
| ---------------------------------- | ----------------------------------------------------- |
| 系统任务（如"先处理退款"过场跑完） | `end_active_system_task()` 清掉系统过场，业务流接着跑 |
| 业务任务（如退款流程到 end）       | `end_active_task()` 清掉活跃任务                      |

清掉之后返回 None。下一轮内层循环再调 `state.current_active_task()`：

- 业务结束 → 就没事了，返回 `action_listen`
- 系统过场结束 → 业务任务还在，继续推进业务

## 第7章 处理 action step

### 7.1 代码

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _run_action_step(self, step: ActionFlowStep, state: DialogueState) -> ActionCall:
    # 1. 推进下一步
    self._advance_next_step(state, step)
    # 2. 构造 ActionCall
    action_call  = self._build_action_call(state, step) 
    # 3. 退出内层让外层执行
    return action_call 
```

### 7.2 构造 ActionCall

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _build_action_call(self, state, step) -> ActionCall:
    # 1. 获取action_name (action_listen/action_response/action_xxx)
    # 2. 获取action_kwargs (构建参数)
    action_name = step.action
    action_kwargs = step.args
    # action_kwargs有可能有:结构有可能是一个str、dict、或者空字典{}
    # str: "context.response"
    if isinstance(action_kwargs, str):
        action_kwargs = state.active_system_task.model_dump(mode="json")[action_kwargs.split(".")[1]]
    return ActionCall(action_name=action_name, action_kwargs=action_kwargs)
```

正常情况下 `step.args` 是个 dict，直接当 action_kwargs 传。但有一种特殊情况：`args` 写成了字符串 `"context.response"`，需要从当前任务的对应字段里取出来。如下

```yaml
- id: ask
  type: action
  action: action_response
  args: context.response       # ← 字符串引用,不是 dict
```

代码里 `args.split('.')[1]` 取 `"response"`，再 `state.active_system_task.model_dump(mode="json")`

也就是从当前 `CollectedSystemContext` 里取出 `response` 字段（这正是激活系统流时塞进来的那份 response）。

这种"间接引用"解决了一个实际问题：**同一个系统流如何服务不同的业务场景**。`system_collect_information` 只有一个，但几十个业务 collect step 的问句各不相同——"请告诉我你的订单号""请简单说一下退款原因"。如果把问句写死在系统流的 YAML 里，每个 collect step 都需要一个独立的系统流。通过 `context.response` 间接引用，问句变成了激活系统流时传入的参数，一个系统流通用于所有 collect step。

### 7.3 顺序为什么重要

注意代码里的执行顺序：**先 `_advance_to_next_step` 把 step_id 推到下一步，再构造 ActionCall 返回**。

如果不先推进，外层执行完 action 后内层下一轮还是停在同一个 action step 上，会**死循环**反复执行同一个 action。先推进掉，外层执行完回来时，内层从下一个 step 开始。

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/09-顺序为什么重要.png" style="zoom: 33%;" />

## 第8章 处理 collect step

`collect` 是四种 step 里最复杂的一个。因为它要处理"槽位的所有可能状态"：刚来时可能本来就有值、可能从聚焦对象自动补一个、可能有值但没通过校验、可能完全没值。

### 8.1 代码

文件：`atguigu/task/flow/executor.py`

```python
def _run_collect_step(self, step: CollectFlowStep, state: DialogueState, flows: FlowsList):

    # 1. 尝试自动补槽
    self._try_to_fill_collect_slot_focused_object(state, step)

    # 2. 判断槽位是否已经填过
    if state.active_task.slots.get(step.slot_name):

        # 填过则直接执行下一步
        self._advance_next_step(state, step)
        return None
    else:
        # 没填过则启动系统过场：补槽任务
        state.start_active_system_task(CollectedSystemContext(
            # flow_id="system_collect_information",
            step_id=flows.get_flow_by_id('system_collect_information').start_step().id,
            slot_name=step.slot_name,
            response=step.response.model_dump(mode="json")
        ))
        return None
```

### 8.2 尝试自动补槽

文件：`atguigu/task/flow/executor.py`

```python
# atguigu/task/flow/executor.py
def _try_to_fill_collect_slot_focused_object(self, state: DialogueState, step: CollectFlowStep):

    if state.focused_object is None:
        return None

    if step.slot_name == 'order_number' and state.focused_object.type == "order":
        state.set_slots({step.slot_name: state.focused_object.id})

    if step.slot_name == "product_id" and state.focused_object.type == "product":
        state.set_slots({step.slot_name: state.focused_object.id})
```

进入 collect step 第一件事：看看 `focused_object` 能不能直接提供这个槽位的值。

**它要解决什么问题？** 考虑一个真实的交互顺序：用户在首页先点了一张订单卡片，然后说"查物流"。这个交互跨了两个 turn：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/09-尝试自动补槽.png" style="zoom: 67%;" />

如果在 collect step 不做自动补槽，会发生什么？用户**已经点过订单卡片了**，但进流程后系统还要再问一遍"请告诉我你的订单号"。用户会困惑：我刚不是点了吗？

`_try_to_fill_slot_from_focused_object` 就是为这个场景设计的。它利用 `focused_object` **跨 turn 持久化**的特性（只有 session 过期才清），在 collect step 被处理时顺手检查一下——如果用户的聚焦对象恰好匹配这个槽位，直接填入，省掉一次追问。

## 第9章 小结

### 9.1 这一节实现了什么

| 文件                    | 内容                                                         |
| ----------------------- | ------------------------------------------------------------ |
| `task/flow/executor.py` | `FlowExecutor` 全部方法：`run_task` / `advance_until_action` / `_run_step` / 四个 `_run_*_step` / `_select_next_step` / `_eval_condition` / `_advance_to_next_step` / `_build_action_call` / `_try_to_fill_slot_from_focused_object` |

### 9.2 方法的命名

在 Python 里，方法名前面加一个下划线 `_` 是一个**约定俗成的信号**，意思是"这是内部用的，外人别随便调用"（类似把东西放在家里抽屉里，不在客厅摆着）。

来看看这个类的分工：

| 方法                                                    | 有没有下划线 | 角色                                           |
| ------------------------------------------------------- | ------------ | ---------------------------------------------- |
| `run_task`                                              | ❌ 没有       | **大门**——外部调用流程的唯一入口               |
| `advance_until_action`                                  | ❌ 没有       | **客厅**——流程推进的核心逻辑，对外可见         |
| `_run_step`、`_run_start_step`、`_advance_next_step` 等 | ✅ 有         | **抽屉里的工具**——内部实现细节，外部不需要关心 |

**为什么 `advance_until_action` 不给它加下划线？**

因为它是这个流程引擎里**对外暴露的核心能力**。打个比方：

- `run_task` 就像"启动洗衣机"
- `advance_until_action` 就像"让洗衣机一直走到需要你干预的那一步（比如加洗衣液）"

这两个都是"用户"（外部调用方）需要知道的、有意义的概念。外部代码有可能直接调用 `advance_until_action` 来单独推进流程，所以它属于**公共 API**，不加下划线。

而 `_run_step`、`_advance_next_step`、`_eval_condition` 这些，就像是洗衣机内部的齿轮、电路——拆开来每一步对"用户"没意义，只是实现细节，所以加下划线表示"别碰我，内部用的"。

**总结一句话**：`advance_until_action` 不加下划线是因为它被设计为**对外的公共方法**（和 `run_task` 一样），其他方法加下划线是因为它们只是内部辅助工具，不应该被外部直接调用。

### 9.3 几个值得记住的设计

1. **两层循环**：外层管 action 执行，内层管 step 推进。`action_listen` 是唯一的退出信号。这样拆是因为 step 推进和 action 执行是两种不同粒度的操作——把它们混在一起会让每一步都做类型判断。
2. **系统任务优先**：`current_task()` 优先返回系统任务。用一行 `or` 短路求值，让系统过场和 collect 追问能在业务流程之上"覆盖"执行，不需要中断/恢复框架。
3. **action step 先推进再返回**：先改 `step_id` 再构造 `ActionCall`。顺序如果反过来，外层执行完 action 后内层会停在同一个 action step 上，产生死循环。
4. **自动补槽**：进 collect step 第一件事尝试从 `focused_object` 填。解决的是"用户先点卡片、后说意图"的跨 turn 场景——focused_object 跨 turn 持久化，collect step 主动检查它。

### 9.4 至此整个 task 轨道完整了

回看整条链路：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/09-整条链路.png" style="zoom:67%;" />

从用户说"我要退款"到客服回出"请告诉我你的订单号"，所有齿轮都对上了。（整个客服系统的核心逻辑业务任务处理器实现完毕）下一节就可以把KnowledgeHandler、以及ChitChatHandler两个简单的轨道处理器接入进来，形成完整闭环。



# 十、信息检索与闲聊

## 第1章 任务目标

实现 **`ChitchatHandler` 和 `KnowledgeHandler`** 这两条轨道

| 顺序    | handler            | 说明                               |
| ------- | ------------------ | ---------------------------------- |
| 第 2 章 | `ChitchatHandler`  | 闲聊轨道（轻）                     |
| 第 3 章 | `KnowledgeHandler` | 知识轨道（重，涉及 provider 检索） |

## 第2章 ChitchatHandler

闲聊是三条轨道里最轻的一条，没有流程推进、没有知识检索、没有命令处理，就是单纯把用户的话和对话历史交给 LLM，让它自然回一句。

### 2.1 handler 实现

```python
# atguigu/chitchat/handler.py

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.chitchat.responder import ChitChatResponder


class ChitChatHandler:
    def __init__(self, responder: ChitChatResponder):
        self.responder = responder

    async def handle(self, state: DialogueState) -> list[BotMessage]:
        pending_turn = state.pending_turn
        user_message = pending_turn.user_message
        recent_turns = state.current_session().turns

        return await self.responder.respond(
            user_message=user_message,
            recent_turns=recent_turns,
        )
```

handler 自己不干活，它只是把 state 里的两份原料拿出来——**当前用户消息**和**最近对话历史**——交给 `ChitchatResponder` 处理。

### 2.2 responder 实现

真正调 LLM 的是 responder。

```python
# atguigu/chitchat/responder.py

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from atguigu.domain.messages import UserMessage, BotMessage
from atguigu.domain.state import Turn
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt
from atguigu.infrastructure.llm import llm

class ChitChatResponder:

    async def respond(self,
                      user_message: UserMessage,
                      recent_turns: list[Turn]):

        user_message = HistoryBuilder._render_user_message(user_message)
        history = HistoryBuilder.build(recent_turns)

        prompt_text = load_prompt("chitchat_respond")
        prompt = PromptTemplate.from_template(prompt_text, template_format="jinja2")
        chain = prompt | llm | StrOutputParser()
        response = await chain.ainvoke({
            "user_message": user_message,
            "history": history,
        })
        return [BotMessage(text=response)]
```

整个 respond 的逻辑很短：

1. 把用户消息渲染成文本（`_render_user_message` 处理对象消息时也能转成 `[订单对象 ...]` 这种描述）
2. 把会话历史拼成对话记录
3. 加载 `chitchat_respond` 提示词，组成链
4. 调 LLM，输出文本包成 `BotMessage`

### 2.3 整合和依赖注入

在文件 `atguigu/engine/dialogue_engine.py` 中的 `__init__`方法中添加 `ChitChatHandler`

```python
# atguigu/engine/dialogue_engine.py

def __init__(
        self,
        turn_planner: TurnPlanner,
        task_handler: TaskHandler,
        knowledge_handler: KnowledgeHandler,
        chitchat_handler: ChitChatHandler,
        clarify_responder: ClarifyResponder,
        turn_plan_validator: TurnPlanValidator
) -> None:
    self.turn_planner = turn_planner
    self.task_handler = task_handler
    self.knowledge_handler = knowledge_handler
    self.chitchat_handler = chitchat_handler
    self.clarify_responder = clarify_responder
    self.turn_plan_validator = turn_plan_validator
```

在在文件 `atguigu/engine/dialogue_engine.py` 中添加闲聊轨道的调用

```python
else:
    # 3.3 闲聊
    return await self.chitchat_handler.handle(state = dialogue_state)
```

在 `atguigu/api/routers/dependencies.py` 中注入 `chitchat_handler` 对象：

```python
return DialogueEngine(
    turn_planner = TurnPlanner(),
    task_handler = TaskHandler(
        flows=flow_list,
        command_processor=CommandProcessor(),
        action_runner=build_action_runner(),
        flow_executor=FlowExecutor()
    ),
    knowledge_handler = KnowledgeHandler(knowledge_intents = KNOWLEDGE_INTENTS),
    clarify_responder = ClarifyResponder(),
    turn_plan_validator = TurnPlanValidator(),
    chitchat_handler=ChitChatHandler(ChitChatResponder())
)
```

### 2.4 闲聊轨道全貌

合起来看一次闲聊请求的完整链路：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/10-闲聊轨道全貌.png" style="zoom: 80%;" />

## 第3章 KnowledgeHandler

知识问答比闲聊复杂：它要先**根据意图（intents）找到知识来源（registry + providers）**，再**从这些来源检索知识**，最后结合知识生成回复（LLM + responder）**。

### 3.1 模块总览

```
atguigu/knowledge/
├── __init__.py          # 空文件，标记为 Python 包
├── intents.py           # 意图定义 → 映射到 provider
├── providers.py         # 知识提供者（API / FAQ / RAG）
├── registry.py          # provider 注册表
├── responder.py         # 用知识 + LLM 生成回复
└── handler.py           # 对外入口，编排整个 knowledge 流程
```

### 3.2 知识轨道全貌

把整个 knowledge 轨道串成一条链：

<img src="C:/Users/YuanYi/Desktop/2.资料/1.笔记/images/10-全貌.png" style="zoom: 80%;" />

### 3.3 知识提供者

创建文件：`atguigu/knowledge/providers.py`

```python
# atguigu/knowledge/providers.py

import json, asyncio
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel
from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.infrastructure import http_client


class KnowledgeChunk(BaseModel):
    content: str

class KnowledgeProvider(ABC):

    # 知识提者的ID
    provider_id = ""

    @abstractmethod
    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:
        """
        提供检索方法
        :param state:
        :return:
        """
        pass

class ProductAPIProvider(KnowledgeProvider):

    provider_id = 'api.product'

    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:
        product_id = state.focused_object.id
        data: dict[str, Any] = await self._get_product_info_by_id(product_id)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        return [KnowledgeChunk(content=f"商品信息:\n{text}")]

    async def _get_product_info_by_id(self, product_id: str) -> dict[str, Any]:
        url = f"{settings.commerce_api_base_url}/products/{product_id}"
        # 注意此处：
        # 文件头部 from atguigu.infrastructure import http_client
        # 此处使用 http_client.http_client.get(url) 调用

        # 不要这样做：
        # 文件头部 from atguigu.infrastructure.http_client import http_client
        # 此处使用 http_client.get(url) 调用
        # 会使拿到的 http_client 是 None
        response = await http_client.http_client.get(url)
        return response.json()["data"]

class OrderAPIProvider(KnowledgeProvider):

    provider_id = 'api.order'

    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:
        order_number = state.focused_object.id

        order_payload, logistics_payload = await asyncio.gather(
            self._fetch_order(order_number),
            self._fetch_logistics(order_number),
        )

        return [
            KnowledgeChunk(
                content="订单与物流信息：\n"
                        + json.dumps(
                    {
                        "order_number": order_number,
                        "order": order_payload,
                        "logistics": logistics_payload,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        ]

    async def _fetch_order(self, order_number) -> dict[str, Any]:
        url = f"{settings.commerce_api_base_url}/orders/{order_number}"
        response = await http_client.http_client.get(url)
        return response.json()["data"]

    async def _fetch_logistics(self, order_number) -> dict[str, Any]:
        url = f"{settings.commerce_api_base_url}/orders/{order_number}/logistics"
        response = await http_client.http_client.get(url)
        return response.json().get("data", {})

class FAQProvider(KnowledgeProvider):

    provider_id = 'faq.default'

    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:
        # TODO
        return [KnowledgeChunk(content="FAQ：未检索到相关问题")]

class RAGProvider(KnowledgeProvider):

    provider_id = 'rag.default'

    async def retrieve(self, state: DialogueState) -> list[KnowledgeChunk]:
        # TODO
        return [KnowledgeChunk(content="RAG：未检索到相关信息")]

```

四种 provider 按类型分两组：

**API 类 —— 查实时业务数据：**

| Provider             | provider_id   | 数据来源                                          | 特点                                                     |
| -------------------- | ------------- | ------------------------------------------------- | -------------------------------------------------------- |
| `ProductAPIProvider` | `api.product` | `GET /products/{id}`                              | 从 `state.focused_object.id` 取商品 ID                   |
| `OrderAPIProvider`   | `api.order`   | `GET /orders/{id}` + `GET /orders/{id}/logistics` | 用 `asyncio.gather` **并发**查订单和物流，省一半等待时间 |

**FAQ / RAG 类 —— 占位实现，将来接入真实库：**

| Provider      | provider_id   | 当前行为               | 将来替换方向                           |
| ------------- | ------------- | ---------------------- | -------------------------------------- |
| `FAQProvider` | `faq.default` | 返回"未检索到相关问题" | 接入 ElasticSearch  FAQ 库             |
| `RAGProvider` | `rag.default` | 返回"未检索到相关信息" | 接入向量数据库（如 Milvus / Pinecone） |

这里"占位"的意义是——**接口契约先定下来**，将来接 ElasticSearch、向量数据库都只是替换 `retrieve` 的实现，整个 KnowledgeHandler 不需要做出改变。

### 3.4 Provider 注册表

创建文件：`atguigu/knowledge/registry.py`

```python
# atguigu/knowledge/registry.py

from atguigu.knowledge.providers import KnowledgeProvider


class KnowledgeProviderRegistry:
    """
    只是提供者注册表
    """

    def __init__(self, providers: list[KnowledgeProvider]) -> None:

        self._providers_by_id = {p.provider_id: p for p in providers}

    def get(self, provider_id: str) -> KnowledgeProvider:
        return self._providers_by_id[provider_id]
```

注册表就是一个 `{provider_id → provider 实例}` 的字典包装。构造时传入所有 provider 实例，运行时按 ID 快速查找。`get` 找不到时直接抛 `KeyError`——这是设计选择，因为 provider_id 是代码里写死的常量，不应该出现找不到的情况。

### 3.5 提示词模板

**knowledge_respond.jinja2**

```jinja2
你是一个中文电商客服助手，语气自然、友好、简洁。
{% if knowledge_content %}
以下是与用户问题相关的商品或业务信息，请优先基于这些内容作答：
{{ knowledge_content }}
{% endif %}
要求：
- 只根据已知信息作答，不要编造不存在的内容。
- 如果信息不足，坦诚告知并引导用户提供更多细节。
- 语气自然，不要机械复述资料原文。
{% if history %}
对话历史：
{{ history }}
{% endif %}
用户当前问题：{{ user_message }}

助手回复：
```

模板的关键设计：

1. **`{% if knowledge_content %}`**：只有当确实检索到知识内容时才渲染段落。当FAQ/RAG 占位时， knowledge_content 的值是 `"未检索到相关信息"`，提醒 LLM 知道信息不足。
2. **三条约束**："不编造"、"信息不足时坦诚告知"、"语气自然不机械复述"——这三条是知识问答质量的底线。
3. **`{% if history %}`**：只有当有历史对话时才渲染历史段落。

### 3.6 知识回复生成器

创建文件 `atguigu/knowledge/responder.py`

```python
# atguigu/knowledge/responder.py

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from atguigu.infrastructure.llm import llm
from atguigu.domain.messages import UserMessage, BotMessage
from atguigu.domain.state import Turn
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import  load_prompt
from atguigu.knowledge.providers import KnowledgeChunk


class KnowledgeResponder:

    async def respond(
            self, 
            user_message: UserMessage, 
            recent_turns: list[Turn], 
            chunks: list[KnowledgeChunk] 
    ) -> list[BotMessage]:
        
        # 准备提示词上下文
        user_message = HistoryBuilder._render_user_message(user_message)
        history = HistoryBuilder.build(recent_turns)
        knowledge_content = "\n\n".join([chunk.content for chunk in chunks])

        # 构造chain
        prompt_text = load_prompt("knowledge_respond")
        prompt = PromptTemplate.from_template(
            prompt_text,
            template_format="jinja2"
        )
        chain = prompt | llm | StrOutputParser()

        # 运行chain
        response = await chain.ainvoke({
            "user_message": user_message,
            "history": history,
            "knowledge_content": knowledge_content,
        })

        return [BotMessage(text=response)]

```

它和 `ChitchatResponder` 的结构很像，多的就是 **`knowledge_content`** 这一个变量——把所有 chunks 的 content 用空行拼起来，塞进 prompt 给 LLM。

`"\n\n".join([chunk.content for chunk in chunks])` 这一行：当多个 provider 都返回了结果时（比如 FAQ + RAG 双路检索），它们的知识内容会被拼成一段完整的上下文。

### 3.7 知识检索处理器

文件： `atguigu/knowledge/handler.py`

```python
# atguigu/knowledge/handler.py

from atguigu.domain.messages import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.knowledge.intents import KnowledgeIntent
from atguigu.knowledge.providers import KnowledgeChunk
from atguigu.knowledge.registry import KnowledgeProviderRegistry
from atguigu.knowledge.responder import KnowledgeResponder

class KnowledgeHandler:

    def __init__(
            self,
            knowledge_intents: dict[str, KnowledgeIntent],
            provider_registry: KnowledgeProviderRegistry,
            knowledge_responder: KnowledgeResponder):

        self.knowledge_intents = knowledge_intents
        self.provider_registry = provider_registry
        self.knowledge_responder = knowledge_responder

    async def handle(self, intents: list[str], state: DialogueState) -> list[BotMessage]:

        # 1. 根据意图寻找知识来源（知识提供者id列表）
        provider_ids: list[str] = self._get_provider_ids_by_intents(intents)

        # 2. 从每个 provider 检索知识片段
        chunks: list[KnowledgeChunk] = []
        for provider_id in provider_ids:
            provider = self.provider_registry.get(provider_id)
            current_chunks = await provider.retrieve(state)
            chunks.extend(current_chunks)

        # 3. 用知识生成回复
        return await self.knowledge_responder.respond(
            user_message=state.pending_turn.user_message,
            recent_turns=state.current_session().turns,
            chunks=chunks
        )


    def _get_provider_ids_by_intents(self, intents: list[str]) -> list[str]:
        provider_ids: list[str] = []
        for intent in intents:
            provider_ids.extend(self.knowledge_intents[intent].provider_ids)
        return list(set(provider_ids))
```

`handle` 方法三件事，按顺序推进：

| 步骤        | 方法                               | 输入                               | 输出                              |
| ----------- | ---------------------------------- | ---------------------------------- | --------------------------------- |
| ① 意图→来源 | `_get_provider_ids_by_intents`     | `list[str]`（如 `["order_info"]`） | `list[str]`（如 `["api.order"]`） |
| ② 检索知识  | 遍历 `provider.retrieve(state)`    | provider_id 列表                   | `list[KnowledgeChunk]`            |
| ③ 生成回复  | `knowledge_responder.respond(...)` | chunks + 对话上下文                | `list[BotMessage]`                |

`_get_provider_ids_by_intents` 里用 `list(set(...))` 去重——LLM 可能一次给多个 intents（比如同时问"退款政策"和"退货政策"），它们可能指向同一个 provider。

### 3.8 组装

文件： `atguigu/engine/dialogue_engine.py` 中，添加信息检索的轨道调用

```python
# atguigu/engine/dialogue_engine.py
elif turn_plan.knowledge is not None:
    # 3.2 信息检索
    return await self.knowledge_handler.handle(intents=turn_plan.knowledge.intents, state=dialogue_state)
```

文件：修改 `atguigu/api/routers/dependencies.py` 中 `KnowledgeHandler` 的组装

```python
# atguigu/api/routers/dependencies.py
return DialogueEngine(
    turn_planner = TurnPlanner(),
    task_handler = TaskHandler(
        flows=flow_list,
        command_processor=CommandProcessor(),
        action_runner=build_action_runner(),
        flow_executor=FlowExecutor()
    ),
    knowledge_handler = KnowledgeHandler(
        knowledge_intents=KNOWLEDGE_INTENTS,
        knowledge_responder=KnowledgeResponder(),
        provider_registry=KnowledgeProviderRegistry(
            [
                ProductAPIProvider(),
                OrderAPIProvider(),
                FAQProvider(),
                RAGProvider(),
            ]
        ),
    ),
    clarify_responder = ClarifyResponder(),
    turn_plan_validator = TurnPlanValidator(),
    chitchat_handler=ChitChatHandler(ChitChatResponder())
)
```

初始化http_client

文件： `atguigu/api/app.py` 中 添加 `http_client`的初始化和关闭代码

```python
# atguigu/api/app.py 

# 初始化session引擎和session工厂
print("启动服务器")
print("初始化数据库链接资源")
init_db_engine() # 自带连接池
# 初始化http
init_http_client()

yield

await close_db_engine()
print("释放数据库链接资源")
await close_http_client()
print("停止服务器")
```

## 第4章 小结

### 4.1 这一节实现了什么

| 文件                                                         | 内容                                |
| ------------------------------------------------------------ | ----------------------------------- |
| `chitchat/handler.py` + `chitchat/responder.py` + `prompts/jinja2/chitchat_respond.jinja2` | 闲聊轨道完整实现                    |
| `knowledge/handler.py` + `knowledge/responder.py` + `prompts/jinja2/knowledge_respond.jinja2` | 只是检索轨道的实现                  |
| `knowledge/providers.py`                                     | 4 种知识提供者（API×2 + FAQ + RAG） |
| `knowledge/registry.py`                                      | Provider 注册表                     |

### 4.2 几个值得记住的设计

1. **handler 不干活**：两个 handler 都把真正工作交给对应的 responder，自己只负责调度。
2. **provider 抽象**：API / FAQ / RAG 不同知识来源用同一个 `retrieve(state) → chunks` 接口，FAQ / RAG 当前是占位，将来接入真实库不影响上层。
3. **OrderAPIProvider 的并发设计**：用 `asyncio.gather` 同时查订单和物流，减少 latency。



# 历史对话实现

## 第 1 章 任务目标 

前面几节里，我们已经把电商客服的核心对话链路跑通了：用户发消息，后端进入 `DialogueEngine`，再根据 planner 的结果走 task、knowledge、chitchat 等不同轨道，最后把机器人回复返回给前端。

但是，一个真正可用的客服系统不能只处理“当前这一句话”。用户刷新页面、重新进入页面时，也应该看到之前的聊天记录。

这一节要补上的就是**历史对话展示能力**。

目标效果分成两种场景：

1. **用户刚进入页面加载历史**
   - 返回数据库里所有 session 的消息
   - 前端直接展示全部历史
   - 不插入分割线

2. **用户进入页面后发送了新消息**
   - 页面加载时已有的消息算历史
   - 本次页面打开后新产生的消息算当前消息
   - 这时才在两者中间插入分割线

也就是说，分割线不是数据库里天然存在的东西，而是前端根据“页面生命周期”做出来的展示效果。

理解了业务目标后，下面先看整体设计路线。

## 第 2 章 设计路线

历史对话这块最容易混淆的点是：**session 是后端业务概念，分割线是前端展示概念**。

后端知道每条消息属于哪个 session，但后端并不知道用户是不是“刚刚打开页面”。页面打开前后的边界，是浏览器里的状态，不是数据库里的状态。

所以这一节采用的设计是：

| 层   | 职责                                                         |
| ---- | ------------------------------------------------------------ |
| 后端 | 返回所有历史消息，并给每条消息带上 `session_id`              |
| 前端 | 记录页面首次加载时的历史快照，首次发送新消息时插入 分割线`divider` |

这条分工非常重要：

- `session_id` 用来表达“消息属于哪个后端会话”
- `divider` 用来表达“页面打开前”和“页面打开后”的视觉边界

两者不是同一个概念。

那为什么后端还要返回 `session_id` 呢？因为历史消息接口返回的是一组平铺消息，如果不带 `session_id`，前端虽然能展示消息，但已经看不出这些消息原本属于哪个后端 session。

例如后端原始结构是：

```text
session-a
  用户：查订单
  机器人：请提供订单号

session-b
  用户：我要退款
  机器人：请问退款原因
```

如果接口只返回 `role` 和 `text`，这个 session 归属关系就丢了。加上 `session_id` 后，即使消息被平铺返回，也还能保留“每条消息属于哪个业务会话”的信息。

所以可以这样理解：

| 概念         | 作用                                         |
| ------------ | -------------------------------------------- |
| `session_id` | 后端数据归属，表示消息属于哪个业务 session   |
| `divider`    | 前端展示效果，表示页面加载前后消息的视觉分割 |

对当前“首次进入不显示分割线，首次发送才显示分割线”的功能来说，`session_id` 不是必需条件；但对历史接口来说，返回 `session_id` 是合理的，因为它保留了后端会话结构，方便后续做按会话折叠、会话分组展示、等扩展。

有了这个分工，下面先从后端的数据模型开始讲。

## 第 3 章 后端响应模型

已经定义过的模型

```python
# atguigu/api/schemas.py

class HistoryMessage(BaseModel):
    """
    历史消息
    """
    session_id: str
    role: str  # user or bot
    text: str | None = None
    object: ChatObject | None = None

class HistoryResponse(BaseModel):
    """
    历史消息列表
    `GET /api/chat/history` 的返回体。
    """
    sender_id: str
    messages: list[HistoryMessage]
```

## 第 4 章 构建历史消息

项目里原来已经有一个 `HistoryBuilder`，它主要负责把历史对话渲染成 prompt 字符串，供 LLM 理解上下文。

比如：

```python
USER: 我想查订单
BOT: 请提供订单号
```

这次历史接口要做的事情不一样。它不是给 LLM 看，而是给前端页面看，所以我们在 `HistoryBuilder` 里增加两个面向接口响应的方法。

```python
# atguigu/prompts/history_builder.py

@staticmethod
def render_user_message(session_id: str, user_message: UserMessage) -> HistoryMessage:
    user_obj = ChatObject(**user_message.object.model_dump()) if user_message.object else None
    return HistoryMessage(
        session_id=session_id,
        role="user",
        text=user_message.text,
        object=user_obj,
    )

@staticmethod
def render_bot_message(session_id: str, bot_messages: BotMessage) -> HistoryMessage:
    bot_obj = ChatObject(**bot_messages.object.model_dump()) if bot_messages.object else None
    return HistoryMessage(
        session_id=session_id,
        role="bot",
        text=bot_messages.text,
        object=bot_obj,
    )
```

这两个方法做的事情很轻：

| 方法                  | 输入                         | 输出                      |
| --------------------- | ---------------------------- | ------------------------- |
| `render_user_message` | `session_id` + `UserMessage` | role 为 `user` 的历史消息 |
| `render_bot_messages` | `session_id` + `BotMessage`  | role 为 `bot` 的历史消息  |

这里把 `session_id` 作为参数传进去，而不是让 `UserMessage` 或 `BotMessage` 自己保存 session 信息。

原因是：

- `UserMessage` 表示“用户发来的这一条消息”
- `BotMessage` 表示“机器人回复的一条消息”
- 它们本身不负责知道自己属于哪个 session
- session 归属关系存在于外层 `Session.turns` 结构里

所以转换历史消息时，由外层遍历 session 的代码把 `session.session_id` 补进去。

## 第 5 章 加载全部历史

历史加载入口在 `DialogueService.load_chat_history`。

```python
# atguigu/service/dialogue_service.py

async def load_chat_history(self, sender_id: str) -> list[HistoryMessage]:
    
    # 根据 sender_id 从数据库加载完整 DialogueState
    state = await self.dialogue_state_repository.load_state(sender_id)

    # 遍历 state.sessions，把每个 turn 展开成消息列表
    chat_messages: list[HistoryMessage] = []
    for session in state.sessions:
        for turn in session.turns:
            chat_messages.append(HistoryBuilder.render_user_message(session.session_id, turn.user_message))
            chat_messages.extend([
                HistoryBuilder.render_bot_message(session.session_id, b_msg) for b_msg in turn.bot_messages
            ])

    # 返回给 router 组装的结果
    return chat_messages
```

for 循环遍历顺序是：

```text
Session 1
  Turn 1
    user message
    [bot message 1,bot message 2]
  Turn 2
    user message
    [bot message]
Session 2
  Turn 1
    user message
    [bot message]
```

展开后，接口返回的是一个平铺的消息数组。

示例响应大概长这样：

```json
{
  "sender_id": "u1001",
  "messages": [
    {
      "session_id": "session-a",
      "role": "user",
      "text": "我想查订单",
      "object": null
    },
    {
      "session_id": "session-a",
      "role": "bot",
      "text": "请提供订单号。",
      "object": null
    },
    {
      "session_id": "session-b",
      "role": "user",
      "text": "我要退款",
      "object": null
    }
  ]
}
```

历史接口定义在 `chat_router.py`。

```python
# atguigu/api/routers/chat_router.py

@router.get("/api/chat/history")
async def history(sender_id: str, service: DialogueService = Depends(get_dialogue_service)) -> HistoryResponse:
    chat_message_response: list[HistoryMessage] = await service.load_chat_history(sender_id)
    return HistoryResponse(sender_id=sender_id, messages=chat_message_response)
```

