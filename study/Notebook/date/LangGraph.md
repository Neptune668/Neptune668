# 第 1 章 LangGraph概述

## 1. 核心定位

- **本质**：低级编排框架 + 运行时环境，用于构建、管理和部署**长期运行的有状态智能体**。
- **核心理念**：将智能体工作流建模为**图**。

## 2. 三大核心构件

- **节点**：计算单元（如 LLM 调用、工具执行、自定义逻辑）。
- **边**：定义节点间的转换逻辑，控制执行流向。
- **状态**：图执行过程中共享和传递的数据。

```mermaid
flowchart LR
    classDef terminal fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef agent fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef tool fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef router fill:#ffebee,stroke:#b71c1c,stroke-width:2px;

    Start([开始]) --> Agent[🤖 LLM 代理节点<br>接收状态 & 推理]
    Agent --> Router{🔀 条件边<br>判断是否有工具调用?}
    Router -->|是 / 有 tool_calls| ToolNode[🛠️ 工具执行节点<br>调用外部 API / 函数]
    Router -->|否 / 生成回复| End([结束])

    ToolNode -->|返回结果并更新状态| Agent

    class Start,End terminal;
    class Agent agent;
    class ToolNode tool;
    class Router router;
```

## 3. 关键能力

- **持久化执行**：支持故障恢复与长时运行。
- **人机协作**：可随时检查和修改智能体状态。
- **记忆管理**：兼顾短期工作记忆与跨会话长期记忆。
- **流式处理**：原生适配流式工作流。
- **生产级部署**：为有状态、长时工作流提供可扩展基础设施。

## 4. 与 LangChain 的区别

- **一句话概括**：需要 **有状态、可循环、可分支的多步骤控制流**时，LangChain 难以胜任，必须用 LangGraph。

| 特性     | LangGraph           | LangChain      |
| :------- | :------------------ | :------------- |
| 抽象级别 | 低级，细粒度控制    | 高级，开箱即用 |
| 状态管理 | 内置状态机 + 检查点 | 需自行管理     |
| 执行模型 | 基于图的并行执行    | 线性链式执行   |
| 持久化   | 原生支持            | 需额外实现     |
| 适用场景 | 复杂、有状态智能体  | 简单链式调用   |

#### 5. 适用场景

- 复杂多智能体系统
- 需长期记忆的应用
- 含人工审核的工作流
- 后台处理与实时交互
- 需精细控制的定制化智能体编排

#### 6. 资源链接

- **GitHub**：https://github.com/langchain-ai/langgraph
- **官方文档**：https://docs.langchain.com/oss/python/langgraph/overview

> 后续将通过快速入门示例，具体演示如何用 LangGraph 构建应用

-------

```mermaid
flowchart LR
    classDef terminal fill:#fce4ec,stroke:#e53935,stroke-width:2px,color:#b71c1c;
    classDef node fill:#e3f2fd,stroke:#1e88e5,stroke-width:2px,color:#0d47a1;
    classDef router fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#e65100;
    classDef state fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,stroke-dasharray:5 5,color:#4a148c;

    Entry_Point([入口点 Entry Point]):::terminal 
    Agent_Node[节点 Node: Agent 代理逻辑]:::node
    Router_Cond{条件边 Conditional Edge <br> 判断是否调用工具}:::router
    Tool_Node[节点 Node: Tools 工具执行]:::node
    Finish_Point([终点 Finish / END]):::terminal

    State_Center[(状态 State <br> 消息 / 上下文数据)]:::state

    Entry_Point --> Agent_Node
    Agent_Node --> Router_Cond
    Router_Cond -->|是（需要工具）| Tool_Node
    Router_Cond -->|否（生成回复）| Finish_Point
    Tool_Node --> Agent_Node

    State_Center -.-> Agent_Node
    State_Center -.-> Router_Cond
    State_Center -.-> Tool_Node
```

```python
获取Mermaid代码app = build.compile()  ---得到的对象
mermaid_code = app.get_graph().draw_mermaid()
print(mermaid_code)
```

它是 Mermaid 语法中用于定义**流程图（Flowchart）**的**开头声明**：

- **`graph`**：表示接下来要绘制的是一个**流程图**（Graph/Flowchart）。
- **`TD`** 是 **Top-Down**（自上而下）的缩写，表示图表的布局方向是从上到下排列。
  （同理，还有 `LR` 表示从左到右，`RL` 表示从右到左等）

# 第2章.快速入门

> 使用LangGraph构建一个应用，可以分为如下步骤(图示)：

```mermaid
flowchart LR
    A[1. 定义状态] --> B[2. 定义节点函数] --> C[3. 创建Builder并添加节点、边] --> D[4. 编译得到Graph对象] --> E[5. 调用Graph执行]
```

```python
# 此脚本用来演示LangGraph的基本搭建流程
# 模拟搭建一个搜索系统
from typing import TypedDict

from langgraph.constants import START, END
from langgraph.graph import StateGraph

# 1.定义状态
class MyState(TypedDict):
    query:str
    rag_result:str
    web_result:str
    final_answer:str

# 2.定义节点
def rag_search_node(state:MyState):
    # 从状态中获取查询内容
    query = state['query']
    # 模拟构建一个rag搜索结果
    rag_result = f'这是基于{query}的RAG搜索结果OvO'
    # 将处理后的值返回到相应的状态的值里面
    return {"rag_result":rag_result}

def web_search_node(state:MyState):
    # 从状态中获取数据
    query = state['query']
    # 模拟构建一个web搜索结果（函数中的具体业务逻辑）
    web_result = f'这是基于{query}的web搜索结果TAT'
    # 将处理后的结果返回到状态中
    return {'web_result':web_result}

def final_answer_node(state:MyState):
    # 从状态中获取数据
    query = state['query']
    rag_result = state['rag_result']
    web_result = state['web_result']
    # 模拟结果的构建
    final_answer = f'基于{query}，RAG检索到了：{rag_result}，网络搜索到了：{web_result}'
    # 将处理后的结果返回到状态中
    return {'final_answer':final_answer}

# 创建一个构造器对象，开始构造图结构
# 在创建的时候，首先传入状态的定义
builder = StateGraph(state_schema=MyState)
# 将构造好的节点放入构造器里面
builder.add_node("rag_search_node",rag_search_node)
builder.add_node(web_search_node)
builder.add_node(final_answer_node)
# 将注册进的节点通过边实现连接
builder.add_edge(START,"rag_search_node")
builder.add_edge("rag_search_node","web_search_node")
builder.add_edge("web_search_node","final_answer_node")
builder.add_edge("final_answer_node",END)
# 将构造器对象进行编译，得到一个可运行的图对象
graph = builder.compile()
# 调用图对象，通过invoke的方式传入一个初始的状态值
result = graph.invoke({'query':"哈哈，这是一个测试"})
print(result)

graph_structure = graph.get_graph()
res = graph_structure.draw_ascii()
print(res)
```

# 第3章.状态

## 1.状态隔离

### 1.1 作用

- 状态（State）是构建 LangGraph 应用的第一步，代表整个图的**结果目标**，也是节点需要**修改的数据目标**。
- 状态定义了图的内部数据结构和流转方式。

------

### 1. 2定义状态类（State Schema）

有三种主流定义方式，**推荐使用 `TypedDict`**。

#### 2.1 使用 `TypedDict`（推荐）

>Python提供的类型提示工具，用于为字典（Dict）的键和值指定精确的类型信息。状态类继承TypedDict，定义键的类型和reducer函数

```python
from typing import TypedDict

class MyStateFull(TypedDict):
    rag_result: str
    web_search_result: str
    final_answer: str
    query: str
    a_new_key: str
```

#### 2.2 使用 Pydantic `BaseModel`

>Pydantic BaseModel：Pydantic 提供运行时数据校验，并支持静态类型检查工具进行类型推导。状态类通过继承Pydantic的BaseModel，定义键的类型和reducer函数；

```python
from pydantic import BaseModel

class MyStateFull(BaseModel):
    rag_result: str
    web_search_result: str
    final_answer: str
    query: str
    a_new_key: str
```

#### 2.3 使用 `dataclass`

>Dataclass: dataclass是Python标准库中的一个装饰器，用于自动生成常见特殊方法（如__init__、__repr__、__eq__等），从而简化主要用作数据容器的类的定义。状态类通过dataclass装饰器装饰后，定义键的类型和reducer函数即可

```python
from dataclasses import dataclass

@dataclass
class MyStateFullTwo():
    rag_result: str
    web_search_result: str
    final_answer: str
    query: str
    a_new_key: str   # 注意：原代码缩进有误，实际应放在类内
```

> **说明**：三种方式均需定义键的类型，并可配合 reducer 函数（后续章节介绍）处理状态合并逻辑。

------

### 3. 输入/输出数据隔离

通过 `StateGraph` 构造参数精细控制图接收的输入和返回的输出：

| 参数            | 作用                                           | 是否必填 | 默认值              |
| :-------------- | :--------------------------------------------- | :------- | :------------------ |
| `state_schema`  | 图的完整内部状态，所有节点可读写               | **必填** | 无                  |
| `input_schema`  | 限制外部传入的字段，须为 `state_schema` 的子集 | 可选     | 等于 `state_schema` |
| `output_schema` | 限制图输出的字段，须为 `state_schema` 的子集   | 可选     | 等于 `state_schema` |

```python
# 此脚本用于演示状态的输入输出隔离
# 目的是规范什么状态可以作为输出，什么状态可以作为输出
from typing import TypedDict

from langgraph.constants import START
from langgraph.graph import StateGraph


# 1.定义出主状态
class MyState(TypedDict):
    query:str
    rag_result:str
    web_result:str
    final_answer:str
    extra_input:str
# 定义输入状态类
class InputSchema(TypedDict):
    query:str
# 定义输出状态类
class OutputSchema(TypedDict):
    final_answer:str
    extra_input: str
# 2.构建节点函数
def rag_search_node(state:MyState):
    query = state['query']
    rag_result = f"这是基于{query}构造的RAG模拟结果......QAQ"
    return {'rag_result':rag_result}

def web_search_node(state:MyState):
    query = state['query']
    web_result = f'这是基于{query}构造的web模拟结果......^_^'
    return {'web_result':web_result}

def final_answer_node(state:MyState):
    query = state['query']
    rag_result = state['rag_result']
    web_result = state['web_result']
    final_answer = f'基于{query}，RAG检索到了：{rag_result}，网络搜索到了：{web_result}'
    return {'final_answer':final_answer}

# 3.创建一个图的构造器对象
builder = StateGraph(state_schema = MyState,
                     input_schema = InputSchema,
                     output_schema = OutputSchema)
builder.add_node(rag_search_node)
builder.add_node(web_search_node)
builder.add_node(final_answer_node)

builder.add_edge(START,"rag_search_node")
builder.add_edge("rag_search_node","web_search_node")
builder.add_edge("web_search_node","final_answer_node")
# 最终到END的可写可不写
graph = builder.compile()
result = graph.invoke({"query":"atguigu","extra_input":"这是额外输入"})
print(result)
```

>输入和输出不写，默认MyState

------

### 4. 节点间数据隔离（私有状态）

- 可以为特定节点指定**非全局的私有状态**，用于内部数据传递，**不参与初始输入和最终输出**。
- 方法：在节点函数参数中，使用不同于主状态的 `TypedDict` 类型注解。

```python
# 此脚本用于展示私有状态的设置，私有状态只是用于内部信息的传递，不参与初始的输入和最终的输出
from typing import TypedDict

from langgraph.constants import START, END
from langgraph.graph import StateGraph


# 主状态
class MyState(TypedDict):
    query:str
    final_answer:str

# 扩展部分，综合了一下输入输出隔离
class InputSchema(TypedDict):
    query:str
class OutputSchema(TypedDict):
    final_answer:str

# 私有状态,用于中间过程的数据传递，不参与最终的输出和初始的输入
class PrivateState(TypedDict):
    rag_result:str
    web_result:str

def rag_search_node(state:MyState):
    query = state['query']
    rag_result = f'这是基于{query}构造的RAG模拟结果......QAQ'
    return {'rag_result':rag_result}

def web_search_node(state:MyState):
    query = state['query']
    web_result = f'这是基于{query}构造的web模拟结果......^_^'
    return {'web_result':web_result}

# 这个最终汇总节点需要接收rag_result,一个web_result
def final_answer_node(state:PrivateState):
    rag_result = state['rag_result']
    web_result = state['web_result']
    final_answer = f'RAG检索到了：{rag_result}，网络搜索到了：{web_result}'
    return {"final_answer":final_answer}

# 创建构造器
builder = StateGraph(state_schema = MyState,
                     input_schema = InputSchema,
                     output_schema = OutputSchema)
builder.add_node(rag_search_node)
builder.add_node(web_search_node)
builder.add_node(final_answer_node)

builder.add_edge(START,'rag_search_node')
builder.add_edge('rag_search_node','web_search_node')
builder.add_edge('web_search_node','final_answer_node')
builder.add_edge('final_answer_node',END)

# 编译
graph = builder.compile()
result = graph.invoke({"query":"Atguigu123"})
print(result)
```

> START,END映射字符串
>
> 上述代码有扩展在StateGrapth中加OutputSchema,输出数据隔离

## 2. Reducer 函数

Reducer用于进行`当前增量状态（节点输出的状态）和全局状态的合并`

- 每个键可以指定独立的 reducer 函数
- 节点返回值中的每个 key 会与全局 `state_schema` 中对应的 key 进行合并
- 合并逻辑由每个 key 指定的 reducer 函数决定

------

### 2.1 默认行为：覆盖更新

如果未指定 reducer，默认采用 **直接覆盖**。

```python
class MyState(TypedDict):
    data: str          # 无 reducer，覆盖更新
```

------

### 2.2 常用内置 Reducer

通过 `Annotated[类型, reducer函数]` 来为键指定 reducer：

```python
from typing import Annotated, List
import operator

class MyState(TypedDict):
    str_data: Annotated[str, operator.add]           # 字符串拼接
    list_data: Annotated[List[str], operator.add]    # 列表追加（合并）
    int_data: Annotated[int, operator.add]           # 数值累加
```

>没开启reducer的初始情况：{}  ，开启reducer的初始情况{data:[]} ?

**运行效果**：

- 第一次返回 `"A"`，第二次返回 `"B"` → 最终 `"AB"`
- 第一次返回 `[1]`，第二次返回 `[2]` → 最终 `[1, 2]`
- 数值同理累加

> ⚠️ **注意**：`operator.mul` 在初始值为 0 的情况下，后续所有值都会乘以 0，结果为 0，不适合作为数值累计 reducer。没有值默认有[],""

------

```python
# 完整版
# 此脚本用于展示LangGraph中状态的更新方式设置
import operator
from typing import TypedDict, Annotated, List

from langgraph.constants import START, END
from langgraph.graph import StateGraph


class MyState(TypedDict):
    # str_data:str
    # int_data:int
    # list_data:list[str]
    str_data :Annotated[str,operator.add]
    int_data:Annotated[int,operator.add]
    list_data:Annotated[List[str],operator.add]
    # test_data:Annotated[int,operator.mul]

# 定义一个更新节点，目的是将值返回到状态中
def update_node_1(state:MyState):
    print(f"节点1当前的状态为：{state}")
    return {
        "str_data":"这是node_1返回的结果",
        "int_data":1,
        "list_data":["这是node_1返回的结果"]
    }

def update_node_2(state:MyState):
    print(f"节点2当前的状态为：{state}")
    return {
        "str_data":"这是node_2返回的结果",
        "int_data":2,
        "list_data":["这是node_2返回的结果"]
    }

builder = StateGraph(state_schema = MyState)
builder.add_node(update_node_1)
builder.add_node(update_node_2)
builder.add_edge(START,"update_node_1")
builder.add_edge("update_node_1","update_node_2")
builder.add_edge("update_node_2",END)

graph = builder.compile()
result = graph.invoke({})
print(result)
```

### 2.3 自定义 Reducer

自定义 reducer 函数接收两个参数：**当前全局值** 和 **节点返回的新值**，返回合并后的结果。

```python
# 此脚本用于展示LangGraph中的自定义reducer函数
import operator
from typing import TypedDict, Annotated, List

from langgraph.constants import START, END
from langgraph.graph import StateGraph

# 其中会传入两个参数，第一个参数作为当前的状态值，第二个参数作为新接收的值
def custom_reducer(origin_value:int,new_value:int):
    return origin_value*3 + new_value*2

class MyState(TypedDict):
    # str_data:str
    # int_data:int
    # list_data:list[str]
    str_data :Annotated[str,operator.add]
    int_data:Annotated[int,custom_reducer]
    list_data:Annotated[List[str],operator.add]
    # test_data:Annotated[int,operator.mul]

# 定义一个更新节点，目的是将值返回到状态中
def update_node_1(state:MyState):
    print(f"节点1当前的状态为：{state}")
    return {
        "str_data":"这是node_1返回的结果",
        "int_data":1,
        "list_data":["这是node_1返回的结果"]
    }

def update_node_2(state:MyState):
    print(f"节点2当前的状态为：{state}")
    return {
        "str_data":"这是node_2返回的结果",
        "int_data":2,
        "list_data":["这是node_2返回的结果"]
    }

builder = StateGraph(state_schema = MyState)
builder.add_node(update_node_1)
builder.add_node(update_node_2)
builder.add_edge(START,"update_node_1")
builder.add_edge("update_node_1","update_node_2")
builder.add_edge("update_node_2",END)

graph = builder.compile()
result = graph.invoke({})
print(result)
```

**示例完整流程**：

>该脚本演示自定义 reducer：int_data 按 旧值×3 + 新值×2 更新。节点1返回1（0→2），节点2返回2（2→10）。字符串和列表用 operator.add 拼接合并。最终状态即为累加后的结果。

------

### 2.4自定义 Reducer 用于消息列表

在实际 Agent 开发中，常用来**累积对话消息历史**：

```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from typing import Annotated, List, TypedDict

def add_message(left: list, right: list) -> list:
    print("合并消息...")
    return left + right

class MyAgent(TypedDict):
    messages: Annotated[List[BaseMessage], add_message]
```

这样每次节点返回新消息时，都会**追加**到历史消息列表中，而不是覆盖。

------

## 3.状态的存储（Checkpointer）

### 3.2.1 为什么需要状态存储

| 场景                | 问题                                     |
| :------------------ | :--------------------------------------- |
| 多次调用保持上下文  | 每次 invoke 都初始化空状态，丢失历史消息 |
| 断点续传 / 故障恢复 | 节点执行中途报错，已执行节点的状态丢失   |

### 3.2.2 解决方案：Checkpointer + thread_id

**三步实现状态持久化**：

1. **创建 Checkpointer**（内存 / 数据库）
2. **编译图时传入** `checkpointer`
3. **调用时传入** `thread_id`（会话隔离标识）

```python
# 此案例用于演示agent中的检查点机制，体现LangGraph中状态持久化的意义
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

# from langchain_community.chat_models import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(model = "qwen3.7-plus")


@tool
def weather_tool(city: str, date: str) -> str:
    """查天气的工具"""
    return f'{city}在{date}的天气是雷鸣电闪，还刮大风'
#创建检查点保存器（Checkpointer）
checkpointer = InMemorySaver()

agent = create_agent(
    model=llm,
    tools=[weather_tool],
    checkpointer=checkpointer
)

config = {
    "configurable":{
        "thread_id":"atguigu"
    }
}
response_1 = agent.invoke(
    {"messages":"深圳在2026年7月3日的天气怎么样？"},
    config =config
)
print('第一次调用',response_1['messages'][-1],end="\n\n==============\n\n")

response_2 = agent.invoke(
    {"messages":"这个天气适合出门野餐吗"},
    config = config
)
print('第二次调用',response_2['messages'][-1],end="\n\n==============\n\n")
```

- `InMemorySaver` 是 LangGraph 提供的一种**内存型检查点存储**，用于在程序运行期间保存 Agent 的每一步状态（消息列表、工具调用结果、当前节点等）。
- 这种方式适合演示和单次运行，生产环境可替换为 `SqliteSaver` 或 `RedisSaver` 等持久化存储

> **关键点**：
>
> - 相同 `thread_id` = 同一个会话，状态可累积
> - 不同 `thread_id` = 新会话，状态隔离

------

下面文字是上面代码的详细解析

```python

1. 环境与模型初始化
python
load_dotenv()
llm = ChatOpenAI(model = "qwen3.7-plus")
加载 .env 文件中的环境变量（如 API Key）。

使用 ChatOpenAI 创建一个 LLM 实例，这里指定了模型名 qwen3.7-plus（阿里通义千问），实际可通过 OpenAI 兼容接口调用。

2. 定义工具（Tool）
python
@tool
def weather_tool(city: str, date: str) -> str:
    """查天气的工具"""
    return f'{city}在{date}的天气是雷鸣电闪，还刮大风'
使用 @tool 装饰器将一个普通函数声明为 LangChain 工具。

该工具接收城市和日期，返回一个固定的天气字符串（模拟数据，并非真实API）。

3. 创建检查点保存器（Checkpointer）
python
checkpointer = InMemorySaver()
InMemorySaver 是 LangGraph 提供的一种内存型检查点存储，用于在程序运行期间保存 Agent 的每一步状态（消息列表、工具调用结果、当前节点等）。

这种方式适合演示和单次运行，生产环境可替换为 SqliteSaver 或 RedisSaver 等持久化存储。

4. 构建 Agent
python
agent = create_agent(
    model=llm,
    tools=[weather_tool],
    checkpointer=checkpointer
)
使用 create_agent（来自 langchain.agents）创建一个可执行 Agent。

将 LLM、工具列表和检查点保存器传入。Agent 内部是一个 LangGraph 状态图，每次调用都会自动将当前状态保存到检查点中。

5. 配置线程 ID
python
config = {
    "configurable": {
        "thread_id": "atguigu"
    }
}
通过 config 配置一个 thread_id，用于标识一个独立的对话线程（会话）。

不同的 thread_id 对应不同的状态存储空间，从而实现多会话隔离。

6. 第一次调用
python
response_1 = agent.invoke(
    {"messages": "深圳在2026年7月3日的天气怎么样？"},
    config=config
)
print('第一次调用', response_1['messages'][-1], end="\n\n==============\n\n")
向 Agent 发送第一条用户消息。

Agent 识别到需要查天气，自动调用 weather_tool，将工具返回的结果（雷鸣电闪、大风）添加到消息历史中。

最终输出的是 Agent 的最终回复（response_1['messages'][-1]），其中包含了天气信息。

在调用结束后，整个状态（包括用户问题、工具调用、工具响应、最终回复）都会被 保存到检查点，并与 thread_id 绑定。

7. 第二次调用（上下文依赖）
python
response_2 = agent.invoke(
    {"messages": "这个天气适合出门野餐吗"},
    config=config
)
print('第二次调用', response_2['messages'][-1], end="\n\n==============\n\n")
这次用户只说了“这个天气适合出门野餐吗”，没有明确提及城市和日期。

由于我们在 config 中使用了相同的 thread_id，Agent 会自动从检查点中恢复之前的所有状态，包括第一次对话中的天气信息。

因此 Agent 理解“这个天气”指的是第一次查询到的“深圳 2026-07-03 的天气（雷鸣电闪、大风）”，并据此给出建议（例如“不适合，雷电天气有危险”）。

第二次调用不再需要重复调用天气工具，因为所需信息已存在于历史状态中。

8. 检查点机制的意义
状态持久化：Agent 的整个状态图（消息、工具调用中间结果、当前执行节点等）被保存下来，确保跨轮次对话的连贯性。

高效性：避免重复调用相同的工具或重新计算中间结果，节省时间和资源。

可恢复性：若程序意外中断，可以从最近的检查点恢复，继续执行（需要持久化存储支持）。

多会话管理：通过 thread_id 区分不同的用户或会话，互不干扰。

输出预期（简略）
第一次调用会输出类似：

text
第一次调用 深圳在2026年7月3日的天气是雷鸣电闪，还刮大风
==============
第二次调用会输出：

text
第二次调用 不建议出门野餐，因为雷雨大风天气存在安全隐患。
==============
（具体文案由 LLM 生成，但一定会参考历史天气信息）

注意事项
代码中的 create_agent 实际可能来自 langgraph.prebuilt 或 langchain.agents（不同版本位置不同），但核心逻辑一致。

本示例使用内存检查点，程序结束则状态丢失；若需长期保存，可替换为 SqliteSaver 并配置持久化路径。

通过这个简单的例子，你可以直观地理解 LangGraph 检查点如何实现 Agent 的“记忆”能力，这是构建复杂多轮对话应用的基础。
```



### 3.2.3 从故障中恢复执行（断点续传）

**使用内存存储的问题**：进程退出后状态丢失，无法恢复。

**生产方案**：使用数据库持久化（如 SQLite、PostgreSQL）。

#### 使用 SQLite 持久化

```python
# 此脚本展示如何在LangGraph中上次运行断掉的地方恢复运行
import sqlite3
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.constants import START
from langgraph.graph import StateGraph

# 创建sqlite的检查点 -> 不是放在内存中，而是放在了数据库中
conn = sqlite3.connect(
    database="./sqlite_data/langgraph_sqlite",
    check_same_thread=False
)
memory = SqliteSaver(conn=conn)


class MyState(TypedDict):
    key_1:str
    key_2:str
    key_3:str

def node_1(state:MyState):
    print(f"node_1的初始状态是：{state}")
    return {"key_1":"value_1"}

def node_2(state:MyState):
    print(f"node_2的初始状态是：{state}")
    raise Exception("节点2报错啦！！！！！")
    return {"key_2":"value_2"}

def node_3(state:MyState):
    print(f"node_3的初始状态是：{state}")
    return {"key_3":"value_3"}

builder = StateGraph(MyState)
builder.add_node(node_1)
builder.add_node(node_2)
builder.add_node(node_3)
builder.add_edge(START,"node_1")
builder.add_edge("node_1","node_2")
builder.add_edge("node_1","node_3")

graph = builder.compile(checkpointer=memory)
config = {
    "configurable":{
        'thread_id':"upguigu"
    }
}
result = graph.invoke({},config=config)
```

#### 故障恢复步骤

假设 `node_2` 执行报错，修复后继续执行：

```python
# 此脚本展示如何在LangGraph中上次运行断掉的地方恢复运行
import sqlite3
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.constants import START
from langgraph.graph import StateGraph

# 创建sqlite的检查点 -> 不是放在内存中，而是放在了数据库中
conn = sqlite3.connect(
    database="./sqlite_data/langgraph_sqlite",
    check_same_thread=False
)
memory = SqliteSaver(conn=conn)


class MyState(TypedDict):
    key_1:str
    key_2:str
    key_3:str

def node_1(state:MyState):
    print(f"node_1的初始状态是：{state}")
    return {"key_1":"value_1"}

def node_2(state:MyState):
    print(f"node_2的初始状态是：{state}")
    # raise Exception("节点2报错啦！！！！！")
    return {"key_2":"value_2"}

def node_3(state:MyState):
    print(f"node_3的初始状态是：{state}")
    return {"key_3":"value_3"}

builder = StateGraph(MyState)
builder.add_node(node_1)
builder.add_node(node_2)
builder.add_node(node_3)
builder.add_edge(START,"node_1")
builder.add_edge("node_1","node_2")
builder.add_edge("node_1","node_3")

graph = builder.compile(checkpointer=memory)
config = {
    "configurable":{
        'thread_id':"upguigu"
    }
}
result = graph.invoke(None,config=config)
```

> **恢复条件**：
>
> 1. `invoke` 传入 `None`（非初始状态）
> 2. 传入**相同的 `thread_id`**

------

## 4 获取历史状态

#### 3.3.1 LangGraph 底层：Pregel 算法

> LangGraph 的运行时由 **Pregel** 类控制，其核心采用**超步（SuperStep）**机制迭代执行，而非传统 DAG 的拓扑排序。

**两大核心组件**

- **Actors（节点/PregelNode）**：实现 Runnable 接口，订阅并读写 Channels 进行数据交互。
- **Channels（通道）**：负责 Actors 间的通信，包含值类型、更新类型及合并更新的函数

#### 3.3.2 超步（SuperStep）执行流程

LangGraph 的执行由多个 **超步** 组成，每个超步分三阶段：

| 阶段                | 动作                                                      |
| :------------------ | :-------------------------------------------------------- |
| **Plan（计划）**    | 确定本轮要执行哪些节点（订阅了已更新通道的节点）          |
| **Execute（执行）** | 并行执行所有选中的节点,直至全部完成、出现失败或达到超时。 |
| **Update（更新）**  | 将节点输出写入通道，更新全局状态                          |

- 超步**循环执行**，直到没有节点可执行或达到最大步数
- **不是传统 DAG**：执行顺序不只看边连接，更依赖于通道订阅关系

------

##### 核心总结

| 概念             | 关键点                                                       |
| :--------------- | :----------------------------------------------------------- |
| **Reducer**      | 指定每个状态键的合并逻辑（默认覆盖；支持 `operator.add` 和自定义函数） |
| **Checkpointer** | 状态持久化工具，支持内存 / SQLite / PostgreSQL 等            |
| **thread_id**    | 会话隔离标识，复用即共享上下文，新 ID 即新会话               |
| **断点续传**     | 使用数据库 + 传入 `None` + 相同 `thread_id` 从故障点恢复     |
| **Pregel 模型**  | 基于超步（Plan→Execute→Update）循环执行，非传统 DAG          |
| **消息累积**     | 使用自定义 reducer 拼接消息列表，实现 Agent 短期记忆         |

> 💡 **实践建议**：
>
> - 开发测试用 `InMemorySaver`
> - 生产环境使用 `SqliteSaver` 或 `PostgresSaver`
> - 为每个用户/会话分配唯一的 `thread_id`
> - 消息列表建议使用 `add_messages`（LangGraph 内置）或自定义 `add_message` 避免覆盖历史

```python
# 此脚本通过构建一个较为复杂的例子，展示LangGraph底层运行的原理
import operator
from typing import TypedDict, Annotated, List

from langgraph.constants import START
from langgraph.graph import StateGraph


class MyState(TypedDict):
    data_list:Annotated[List[str],operator.add]

def a(state:MyState):
    return {"data_list":["a"]}
def b_1(state:MyState):
    return {"data_list":["b_1"]}
def b_2(state:MyState):
    return {"data_list":["b_2"]}
def c(state:MyState):
    return {"data_list":["c"]}
def d(state:MyState):
    return {"data_list":["d"]}

builder = StateGraph(MyState)
builder.add_node(a)
builder.add_node(b_1)
builder.add_node(b_2)
builder.add_node(c)
builder.add_node(d)

builder.add_edge(START,"a")
builder.add_edge("a","b_1")
builder.add_edge("b_1","b_2")
builder.add_edge("a","c")
builder.add_edge("c","d")
builder.add_edge("b_2","d")

graph = builder.compile()
result = graph.invoke({})
print(result)

# A :[a,b_1,b_2,c,d]
# B :[a,c,b_1,b_2,d]
# C :[a,b_1,c,b_2,d]
# D :我觉得都不对，我的答案是：[]
```

#### 3.3.3获取历史状态的方法(扩展)

构建好的 `graph` 实例提供两个方法：

| 方法                        | 说明                                                         |
| :-------------------------- | :----------------------------------------------------------- |
| `get_state(config)`         | 获取**最近一个时间步**（最后一个超步）的状态快照。           |
| `get_state_history(config)` | 获取**所有历史时间步**的状态快照，返回一个**迭代器**，按时间**倒序**排列（最新的在前）。 |

**入参**：均需传入包含 `thread_id` 的配置字典，用于标识执行线程。

```python
# 最近状态
last_state = graph.get_state(config={'configurable': {'thread_id': '1'}})

# 全部历史状态（迭代器，倒序）
all_states = graph.get_state_history(config={'configurable': {'thread_id': '1'}})
```



------

##### 3. 状态快照（StateSnapshot）的结构

每个历史状态以 `StateSnapshot` 实例表示，包含以下关键字段：

| 字段            | 类型                    | 描述                                                         |
| :-------------- | :---------------------- | :----------------------------------------------------------- |
| `values`        | `dict[str, Any]`        | 当前超步结束时的状态数据（即节点返回值聚合后的结果）。       |
| `next`          | `tuple[str, ...]`       | **下一个超步中待执行的节点名称列表**（用于故障恢复时确定恢复起点）。 |
| `config`        | `RunnableConfig`        | 获取该快照时使用的配置。                                     |
| `metadata`      | `CheckpointMetadata`    | 关联的元数据（如时间戳、步骤号等）。                         |
| `parent_config` | `RunnableConfig`        | 父快照的配置（若存在），用于追溯前一个状态。                 |
| `interrupts`    | `tuple[Interrupt, ...]` | 当前超步中发生且尚未解决的中断信息（用于人机交互场景）。     |

**重点关注**：`values` 存储当前聚合状态；`next` 指明后续执行路径，是实现断点续传的关键依据。

------

##### 4. 示例代码解析

##### 4.1 环境准备

python

```python
import operator
from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

connection = sqlite3.connect('checkpointer.db', check_same_thread=False)
checkpointer = SqliteSaver(connection)
```

- 使用 SQLite 作为检查点存储，用于持久化每个超步的状态。

##### 4.2 定义状态与节点

python

```python
class State(TypedDict):
    aggregate: Annotated[list, operator.add]   # 列表聚合（追加）

def a(state: State, config):
    print(f'Adding "A" to {state["aggregate"]}')
    return {"aggregate": ["A"]}

def b(state: State, config):
    print(f'Adding "B" to {state["aggregate"]}')
    return {"aggregate": ["B"]}

# ... 类似定义 b_2, c, d
```



- 每个节点返回一个字典，键为 `"aggregate"`，值为包含单个字母的列表。
- 因为使用 `operator.add` 作为 reducer，状态中的 `aggregate` 会不断追加新列表元素。

##### 4.3 构建图

```python
builder = StateGraph(State)
builder.add_node("a", a)
builder.add_node("b", b)
builder.add_node("b_2", b_2)
builder.add_node("c", c)
builder.add_node("d", d)

builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("a", "c")
builder.add_edge("b", "b_2")
builder.add_edge("b_2", "d")
builder.add_edge("c", "d")
builder.add_edge("d", END)

graph = builder.compile(checkpointer=checkpointer)
```



- 图结构：`START → a → (b → b_2 → d) 和 (c → d)` 并行分支，最终汇聚到 `d`。

##### 4.4 执行并获取状态

python

```python
res = graph.invoke({}, config={'configurable': {'thread_id': '1'}})
print(res)  # 最终聚合结果，应为 ['A','B','B_2','D'] 或 ['A','C','D']？实际取决于调度顺序，但因为是并行边，a 后 b 和 c 并行，顺序不确定，但聚合是追加。

# 获取全部历史
all_states = graph.get_state_history(config={'configurable': {'thread_id': '1'}})
for state in all_states:
    print(state)   # 打印每个 StateSnapshot 对象
```



##### 4.5 输出解读（预期）

- **最终状态**：`{'aggregate': ['A','B','B_2','D']}`（假设 b 分支先完成）或 `['A','C','D']`（取决于执行顺序，但 b 和 c 并行，最终 d 会等待两者都完成？注意图中 `b_2→d` 和 `c→d`，d 需要两个前驱都完成才会执行，所以实际上 aggregate 会包含 `A`、`B`、`B_2`、`C`、`D`？）
  需要重新分析图：

  - a 执行，返回 ["A"]
  - a 后同时触发 b 和 c（并行）
  - b 返回 ["B"]，b 后触发 b_2，b_2 返回 ["B_2"]
  - c 返回 ["C"]
  - d 等待 b_2 和 c 都完成才执行，d 返回 ["D"]
    因此最终 aggregate 为 `['A','B','B_2','C','D']`（顺序由执行和聚合决定，但 aggregate 是列表追加，最终包含所有这些元素）。

- ###### **历史快照**：每个超步结束都会保存一个快照，例如：

  - 超步1：a 执行后，values = {"aggregate": ["A"]}, next = ("b","c")
  - 超步2：b 和 c 并行执行后，values = {"aggregate": ["A","B","C"]}, next = ("b_2",)（因为 c 已完成，但 b 的后续 b_2 待执行；实际上 b 和 c 在同一超步完成，b_2 需要等待 b 完成，所以下一超步执行 b_2）
  - 超步3：b_2 执行后，values = {"aggregate": ["A","B","C","B_2"]}, next = ("d",)
  - 超步4：d 执行后，values = {"aggregate": ["A","B","C","B_2","D"]}, next = ()

------

##### 5. 关键应用场景

- **故障恢复**：通过 `state.next` 可获知中断位置，从该节点恢复执行。
- **调试与审计**：查看每一步的中间状态，便于追踪数据流向和逻辑错误。
- **人机交互**：`interrupts` 字段可用于处理需要人工输入的中断点。

------

##### 6. 注意事项

- `get_state_history()` 返回迭代器，按**倒序**（最新→最旧）排列，遍历时注意顺序。
- 检查点（Checkpoint）需在编译图时传入 `checkpointer` 对象，否则状态不会被持久化。
- 状态快照中包含 `config` 和 `parent_config`，可用于重建上下文或回溯父状态。

# 第4章

## 1.1 节点的输入输出

### 1.1.1 节点输入

在LangGraph中，一般来讲，节点都是Python函数（可以是同步的，也可以是异步的），它们接受以下参数:

state：图的状态，代表了具体的业务数据；

config：一个RunnableConfig对象，包含诸如thread_id之类的配置信息，在调用图时，也可以传递用户定义的其他配置；

runtime：一个Runtime对象，包含运行时context（可自定context，在调用图时传入即可）以及其他信息，如store和stream_writer等；2

>config和runtime的实际用途

以上参数，会在运行过程中，自动被LangGraph运行时注入。

节点定义config和runtime入参如下所示，在运行时，这两个参数LangGraph名称会通过关键字传参方式进行传参，因此两个参数位置可以调换。

```python
# 此案例目的是展示如何在节点的参数里进行多种数据的注入
# 比如说：状态，配置参数，类对象
from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.constants import START,END
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from config import config	#congfig创建的配置文件
from runtime import Atguigu	#Atguigu创建的类

class MyState(TypedDict):
    query:str
    response:str

def node_1(state:MyState,config:RunnableConfig):
    configurable = config.get("configurable",{})
    user_id = configurable.get("user_id","downguigu")
    print(user_id)

def node_2(state:MyState,runtime:Runtime):
    atguigu = runtime.context['sgg']
    atguigu.show()

builder = StateGraph(state_schema=MyState)
builder.add_node(node_1)
builder.add_node(node_2)
builder.add_edge(START,"node_1")
builder.add_edge("node_1","node_2")
builder.add_edge("node_2",END)

graph = builder.compile()
my_atguigu = Atguigu()
context = {
    "sgg":my_atguigu
}

result = graph.invoke({"query":"哈喽"},config = config,context =context)
```

```python
#创建两个包
config = {
    "configurable":{
        "user_id":"atguigu"
    }
}
class Atguigu:
    def show(self):
        print("正在运行这个类中的show方法")
```

### 1.1.2 节点输出

节点的输出为当前节点对状态的增量更新，而不能将接收到的整个状态实例返回出去。

LangGraph底层会将所有节点输出的状态，都作为增量状态，并尝试和当前的全局状态做一次合并操作。如果将整个状态都输出，对于没有配置任何reducer的状态键，langgraph底层无法完成合并，会抛出异常；对于配置了reducer的状态键，如果节点输出了不属于该节点更新的状态，也会导致数据产生问题。

以下演示错误返回了整个状态的问题：

```python
# 此脚本展示错误的返回模式：直接返回一个state的后果
import operator
from typing import Annotated, List, TypedDict

from langgraph.constants import START
from langgraph.graph import StateGraph


class MyState(TypedDict):
    str_data:str
    add_list_data:Annotated[List[str],operator.add]
    add_str_data:Annotated[str,operator.add]

def node_1(state:MyState):
    print(state)
    str_data = state['str_data']
    state['str_data'] = "node_1"
    state['add_list_data'] = ["1"]
    # state['add_str_data'] = "1"
    return state

def node_2(state:MyState):
    print(state)
    str_data = state['str_data']
    state['str_data'] = "node_2"
    # state['add_list_data'] = ["2"]
    return state

def node_3(state:MyState):
    print(state)
    str_data = state['str_data']
    state['str_data'] = "node_3"
    # state['add_list_data'] = ["3"]
    return state

builder = StateGraph(MyState)
builder.add_node(node_1)
builder.add_node(node_2)
builder.add_node(node_3)
builder.add_edge(START,"node_1")
builder.add_edge("node_1","node_2")
builder.add_edge("node_2","node_3")

graph = builder.compile()
result = graph.invoke({"str_data":"你好","add_list_data":["0"],"add_str_data":"1"})
print( result)
```

>node_2没有返回list_data,出现了自动追加前面所有值的情况

## 2. 特殊节点

START和END节点都是LangGraph当中的特殊节点。START它代表着将用户输入发送到图中的节点。引用此节点的主要目的是确定应首先调用哪些节点。END节点是一个特殊节点，代表终止节点。当想表示哪些边在完成后没有动作时，会引用这个节点。

START和END节点本质上是一个字符串，如下所示：

```python
END = sys.intern("__end__")
"""The last (maybe virtual) node in graph-style Pregel."""
START = sys.intern("__start__")
"""The first (maybe virtual) node in graph-style Pregel."""
```

START作为一个特殊节点，在图执行完START节点之后，也会创建一个checkpoint

## 3. 节点缓存

LangGraph支持基于节点输入对节点进行缓存。对于配置了缓存的节点，且缓存结果没有过期，以相同的输入再次调用节点时，可直接从缓存当中读取结果，不需要再进行节点计算。

使用缓存的方法如下：

（1）编译图时指定缓存存储后端：langgraph.cache包当中提供了内存级别的缓存后端，Redis缓存后端，和Sqlite缓存后端的具体实现，需要构造相关实例，并在图编译时传入。

（2）为节点指定缓存策略。每个缓存策略需配置：

key_func：用于根据节点的输入生成缓存键，默认情况下是使用pickle对输入进行hash运算的结果。

ttl：缓存的生存时间（以秒为单位）。如果未指定，缓存将永不过期

```python
# 此脚本展示了LangGraph中节点如何开启缓存策略，以及缓存策略的效果
import time
from typing import TypedDict
from langgraph.cache.memory import InMemoryCache
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import CachePolicy

class MyState(TypedDict):
    x:int
    result:int

# 进入此节点之前，状态为{"x":1}
# 如何击中缓存：
# 1.图结构和映射名全都不变；
# 2.运行到该开启缓存的节点时，状态和之前创建缓存时一致
def node_1(state:MyState):
    print(f"初始时的状态为：{state}")
    print("进入计算节点......")
    time.sleep(3)
    print("计算完成！！！！！")
    x = state['x']
    return {"result": x*2}

def node_2(state:MyState):
    time.sleep(3)

builder = StateGraph(MyState)
builder.add_node(node_1,cache_policy = CachePolicy(ttl=1))#保存上一个节点10s
builder.add_node(node_2)
builder.add_edge(START,"node_1")
builder.add_edge("node_1","node_2")


cache = InMemoryCache()#创建一个内存缓存实例。
checkpointer = InMemorySaver()#创建一个内存检查点保存器实例。
graph = builder.compile(cache = cache,checkpointer = checkpointer)
#调用编译方法，将之前定义好的图（builder 通常是一个 StateGraph 或 MessageGraph 的构建器）编译成可执行的运行时图。
config_1 = {"configurable":{"thread_id":"id_1"}}
config_2 = {"configurable":{"thread_id":"id_2"}}

result_1 = graph.invoke({"x":1},config=config_1)
print(result_1)
result_2 = graph.invoke({"x":1},config=config_2)
print(result_2)
```

## 4. 节点重试

很多使用场景中，有些节点由于客观原因限制，导致其执行过程是不稳定的。因此，我们可能希望节点拥有自定义的重试策略，例如在调用API、查询数据库或调用大语言模型（LLM）等情况下。

为节点添加重试策略，需要在add_node中设置retry_policy参数。retry_policy参数接受一个RetryPolicy命名元组对象。RetryPolicy对象有两个属性：max_attempts和retry_on参数，前者定义了总共重试次数，后者定义了对于哪些异常类型进行重试。	示例代码如下：

```python
# 这个脚本用于展示节点的重试策略，在一些可以通过重试解决的问题时，开启此功能可以实现解决
from typing import TypedDict

from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.types import RetryPolicy
from sqlalchemy.orm.base import state_str

class MyState(TypedDict):
    result:str

attempt_count = 0

def unstable_api_call(state:MyState):
    global attempt_count
    attempt_count += 1
    print(f"运行第{attempt_count}次")
    if attempt_count < 3:
        raise Exception(f"运行失败，这是第{attempt_count}次调用")
        # raise ValueError(f"运行失败，这是第{attempt_count}次调用")

    else:
        return{"result":"运行成功！！"}

builder = StateGraph(MyState)
builder.add_node(unstable_api_call,
                 retry_policy = RetryPolicy(max_attempts = 5))#尝试次数
builder.add_edge(START,"unstable_api_call")
graph = builder.compile()
result = graph.invoke({})
print(result)
print("1. 使用默认重试策略:")
print("   默认策略会对除特定异常外的所有异常进行重试")
print("   不会重试的异常包括: ValueError, TypeError, ArithmeticError, ImportError,")
print("                     LookupError, NameError, SyntaxError, RuntimeError,")
print("                     ReferenceError, StopIteration, StopAsyncIteration, OSError\n")
```

## 5. 图内外数据传递（重要）

默认情况下，通过graph.invoke调用图时，仅在整个图的执行过程都结束之后，我们才能够拿到最终的状态，那么如果想要在图的执行过程当中，想要获取到图内部所产生的数据，应该如何实现？

考虑Agent的一个场景：首先，我们希望在LLM输出时，就能够拿到LLM所产生的token，在前端进行展示；其次，如果Agent的流程较长，我们希望能够拿到，当前正在执行的节点或者流程是什么。

由于LangGraph实现了langchain_core当中的Runnable接口，其为我们提供了stream和astream方法，也即流式输出方法，通过流式输出，就能解决前面所说到的问题。

Stream方法提供了多种不同的模式，如下表所示：

| **模式**      | **描述**                                                     |
| ------------- | ------------------------------------------------------------ |
| **values**    | 每一个执行后，流式输出完整的状态                             |
| **updates**   | 图执行过程中，每一步执行后流式输出增量更新。如果在同一个步当中产生了多个增量更新，这些增量更新会分别流式输出。 |
| `custom`      | 流式输出节点内部的自定义数据。                               |
| **messages ** | 在任何调用了LLM的节点当中，流式输出两元组数据：（LLM Token，metadata） |
| **debug**     | 流式输出所有能输出的信息                                     |
| **混合模式**  | 流模式传入列表，在列表当中添加多种不同的模式，可以得到多种流式输出  stream_mode=["update","custom"] |

具体代码如下所示：05代码	`流式输出`

```python
# 这个脚本用于展示LangGraph中的流式输出，在每个节点运行完之后，输出该节点返回的状态信息等
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.constants import START
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

load_dotenv()
llm = ChatOpenAI(model="qwen3.7-plus")

class MyState(TypedDict):
    value_1:str
    value_2:str
    value_3:str


def node_1(state:MyState,runtime:Runtime):
    writer = runtime.stream_writer
    writer({
        "node_name":"node_1",
        "status":"succeed",
        "description":"节点一运行成功"
    })
    llm.invoke("你觉得先有鸡还是先有蛋")
    return {"value_1":"111"}
def node_2(state:MyState,runtime:Runtime):
    writer = runtime.stream_writer
    writer({
        "node_name":"node_2",
        "status":"succeed",
        "description":"节点二运行成功"
    })
    return {"value_2":"222"}
def node_3(state:MyState,runtime:Runtime):
    writer = runtime.stream_writer
    writer({
        "node_name":"node_3",
        "status":"succeed",
        "description":"节点三运行成功"
    })
    return {"value_3":"333"}

builder = StateGraph(MyState)
builder.add_node(node_1)
builder.add_node(node_2)
builder.add_node(node_3)
builder.add_edge(START,"node_1")
builder.add_edge("node_1","node_2")
builder.add_edge("node_2","node_3")
graph = builder.compile()

# for event in graph.stream({},stream_mode = "values"):
#     print(event)
# for event in graph.stream({},stream_mode = "updates"):
#     print(event)
# for event in graph.stream({},stream_mode = "debug"):
#     print(event)
# for event in graph.stream({},stream_mode = "custom"):
#     print(event)
# for event in graph.stream({},stream_mode =["updates","custom","debug"]):
#     print(event)
for event in graph.stream({},stream_mode ="messages"):
    print(event)
```

05_2

```python
import time
from typing import TypedDict, Annotated, List
import operator

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import StreamWriter
from langgraph.runtime import Runtime
load_dotenv()
llm = ChatOpenAI(model="qwen3.7-plus")


# --- 1. 定义状态 ---
class State(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_step: str


# --- 2. 定义节点 ---

def node_input(state: State):
    """模拟接收用户输入"""
    return {
        "messages": [HumanMessage(content="请帮我写一段Python代码")],
        "current_step": "input_received"
    }


def node_processing(state: State, runtime: Runtime):
    """
    模拟中间处理过程，并使用 writer 输出自定义流式数据
    这对应 stream_mode="custom"
    """
    steps = ["正在分析意图...", "正在检索知识库...", "正在构建Prompt..."]
    writer = runtime.stream_writer
    for i, step in enumerate(steps):
        time.sleep(0.5)  # 模拟耗时操作

        # 使用 writer 发送自定义数据 (不影响图的状态)
        # 这些数据只能通过 stream_mode="custom" 接收到
        writer({
            "step_index": i + 1,
            "description": step,
            "timestamp": time.time()
        })

    return {"current_step": "processing_complete"}


def node_generation(state: State):
    """
    模拟 LLM 生成过程
    LangGraph 的 stream_mode="messages" 会自动捕获 LLM 的流式输出
    """

    # 调用 LLM
    response = llm.invoke(state["messages"])

    return {
        "messages": [response],
        "current_step": "generation_complete"
    }


# --- 3. 构建图 ---
builder = StateGraph(State)
builder.add_node("input", node_input)
builder.add_node("process", node_processing)
builder.add_node("generate", node_generation)

builder.add_edge(START, "input")
builder.add_edge("input", "process")
builder.add_edge("process", "generate")
builder.add_edge("generate", END)

graph = builder.compile()


# --- 4. 演示不同的流式输出模式 ---
def run_demo():
    initial_state = {"messages": [], "current_step": "start"}

    print(f"\n{'=' * 20} 4. Mode: messages (输出 LLM Token) {'=' * 20}")
    print("描述: 输出 LLM 生成的消息片段 (Token)")
    # 注意：FakeListChatModel 默认是一次性返回，但在 messages 模式下会被包装成 chunk
    for chunk, metadata in graph.stream(initial_state, stream_mode="messages"):
        # chunk 是 BaseMessageChunk 对象
        # metadata 包含 node 信息
        node_name = metadata.get('langgraph_node', 'unknown')
        print(f"[{node_name}] Token: {chunk.content!r}")
        # print(chunk.content,end="")
        time.sleep(0.2)


if __name__ == "__main__":
    run_demo()

```

-----

## 6. 人工审核节点

Agent在完成用户设定的任务时，有时候我们希望用户参与当中部分重要决策过程。LangGraph为此提供了一个非常方便的原语：interrupt。其原理如下图所示：

​                                

可以在节点内部任意位置引入interrupt，当节点执行到interrupt所在位置时，就会停止执行，并可以得到从图内传递出来的，需要用户审核的数据，在用户进行相关审核完成后，又可通过graph.invoke，让图继续往下执行。

具体示例如下：

```python
#06  视频08
import time
from typing import TypedDict, Annotated, List
import operator

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import StreamWriter
from langgraph.runtime import Runtime
load_dotenv()
llm = ChatOpenAI(model="qwen3.7-plus")


# --- 1. 定义状态 ---
class State(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_step: str


# --- 2. 定义节点 ---

def node_input(state: State):
    """模拟接收用户输入"""
    return {
        "messages": [HumanMessage(content="请帮我写一段Python代码")],
        "current_step": "input_received"
    }


def node_processing(state: State, runtime: Runtime):
    """
    模拟中间处理过程，并使用 writer 输出自定义流式数据
    这对应 stream_mode="custom"
    """
    steps = ["正在分析意图...", "正在检索知识库...", "正在构建Prompt..."]
    writer = runtime.stream_writer
    for i, step in enumerate(steps):
        time.sleep(0.5)  # 模拟耗时操作

        # 使用 writer 发送自定义数据 (不影响图的状态)
        # 这些数据只能通过 stream_mode="custom" 接收到
        writer({
            "step_index": i + 1,
            "description": step,
            "timestamp": time.time()
        })

    return {"current_step": "processing_complete"}


def node_generation(state: State):
    """
    模拟 LLM 生成过程
    LangGraph 的 stream_mode="messages" 会自动捕获 LLM 的流式输出
    """

    # 调用 LLM
    response = llm.invoke(state["messages"])

    return {
        "messages": [response],
        "current_step": "generation_complete"
    }


# --- 3. 构建图 ---
builder = StateGraph(State)
builder.add_node("input", node_input)
builder.add_node("process", node_processing)
builder.add_node("generate", node_generation)

builder.add_edge(START, "input")
builder.add_edge("input", "process")
builder.add_edge("process", "generate")
builder.add_edge("generate", END)

graph = builder.compile()


# --- 4. 演示不同的流式输出模式 ---
def run_demo():
    initial_state = {"messages": [], "current_step": "start"}

    print(f"\n{'=' * 20} 4. Mode: messages (输出 LLM Token) {'=' * 20}")
    print("描述: 输出 LLM 生成的消息片段 (Token)")
    # 注意：FakeListChatModel 默认是一次性返回，但在 messages 模式下会被包装成 chunk
    for chunk, metadata in graph.stream(initial_state, stream_mode="messages"):
        # chunk 是 BaseMessageChunk 对象
        # metadata 包含 node 信息
        node_name = metadata.get('langgraph_node', 'unknown')
        print(f"[{node_name}] Token: {chunk.content!r}")
        # print(chunk.content,end="")
        time.sleep(0.2)


if __name__ == "__main__":
    run_demo()
```

**需要注意的是**，使用interrupt时，在第二次调用graph.invoke(command)继续执行时，有interrupt的函数，会从函数起点往下执行，如果在函数当中，有更新数据、调用API接口等相关操作时，会造成多次重复执行的情况。因此，一定要保证这种类型操作的幂等性，或者是将其封装到一个单独的节点当中，避免在恢复时再次执行

# 第5章 边（重点）

## 1.1 边的本质

定义边，本质上是定义了，Pregel当中节点订阅的状态通道和节点执行之后，需要更新的状态通道。

边有几种关键类型：

Normal Edges: 普通边。直接从一个节点连接到下一个节点。

Conditional Edges: 条件边。调用函数以确定接下来要前往哪个（哪些）节点。

## 1.2 条件边

条件边的本质是一个路由函数，其根据当前状态动态决定下一个要执行的节点。

```python
# 此脚本功能是展示条件边如何配置
# 条件边的执行逻辑：通过定义一个函数，从状态中取值，判断
from typing import TypedDict

from langgraph.constants import START
from langgraph.graph import StateGraph


class MyState(TypedDict):
    value:int

def input_node(state:MyState):
    print("开始获取输入数据....")
    return {"value":10086}

def odd_node(state:MyState):
    value = state["value"]
    print(f"{value}是奇数！")

def even_node(state:MyState):
    value = state["value"]
    print(f"{value}是偶数！")

def route_condition(state:MyState):
    value = state["value"]
    if value % 2 == 0:
        return "even"
    else:
        return "odd"

builder = StateGraph(MyState)
builder.add_node(input_node)
builder.add_node(odd_node)
builder.add_node(even_node)
builder.add_edge(START,"input_node")
builder.add_conditional_edges(
    "input_node", # 起始节点的映射名
    route_condition, # 路由函数
    {
        "even":"even_node",
        "odd":"odd_node"
    }
)
graph = builder.compile()
graph.invoke({})
```

## 1.3 可控循环

通过条件边，我们可以构建带有循环结构的图，例如在典型的REACT模式下，工具调用和大模型总结生成结果形成了一个循环，如下图所示：

​                                   

需要注意的是，这种带循环的图结构，有一个隐藏的问题：图执行过程当中，可能因为某些原因，导致一直在循环内循环往复执行，因此LangGraph也提供了一个强制使图的执行终止的递归限制参数。

递归限制设定了图在抛出错误之前允许执行的超级步骤数量，`默认值25`，在graph.invoke的config参数中指定。在经过指定数量的超级步骤后，图还没有自然停止执行时，LangGraph会抛出异常GraphRecursionError。

示例代码如下所示：

```python
# 这个脚本用于展示LangGraph中的循环操作
import operator
from typing import TypedDict, Annotated

from langgraph.constants import START, END
from langgraph.graph import StateGraph


class MyState(TypedDict):
    value:Annotated[int,operator.add]

def node_1(state:MyState):
    value = state["value"]
    print(f"当前值为：{value}")
    return {"value":1}

def node_2(state:MyState):
    value = state["value"]
    print(f"当前值为：{value}")
    return {"value":1}

def route_condition(state:MyState):
    value = state["value"]
    if value < 30:
        return "node_1"
    else:
        return "end"
builder = StateGraph(MyState)
builder.add_node(node_1)
builder.add_node(node_2)
builder.add_edge(START,"node_1")
builder.add_edge("node_1","node_2")
builder.add_conditional_edges(
    "node_2",
    route_condition,
    {
        "node_1":"node_1",
        "end":END
    }
)
graph = builder.compile()
graph.invoke({"value":1},config={
        'recursion_limit': 100  # 设置递归限制
    }
)
```
