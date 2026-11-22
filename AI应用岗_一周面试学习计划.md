# AI 应用岗 · 一周面试学习计划

> 目标：用一周时间吃透 `note/` 下《电商运营助手》笔记 1–14，能够脱稿应对 AI 应用岗面试。
> 策略：**倒着学**——先用第 15、16 章建立"考官会问什么"的考题地图，再回 1–14 补细节、对代码、做默写。
> 岗位定位：AI 应用岗，重心在 **LangGraph 编排 + 多 Agent 设计 + LLM 工程化 + Harness 方法论**，分布式可靠性（Outbox/租约/幂等）讲到"思路"即可，不钻数据库锁细节。

---

## 一、"吃透"的 5 条判据（达不到就不算吃透）

1. 不看笔记能 **2 分钟讲完项目**（STAR 结构，见 `15` 章 11.1）；
2. 能**口头画出完整时序**：`同事务写 Outbox → Beat 抢占派发 → Worker 认领租约 → LangGraph 执行 → interrupt 暂停 → 人工恢复 → 幂等落库`；
3. 能讲清 **Harness 四维度**（可控/可恢复/可验证/可观测），每个维度能说一个对应实现；
4. 能**默写关键代码**（见第六节）：StrictModel、LangGraph 条件分支、规则兜底、幂等落库、条件续租 UPDATE；
5. 第 16 章 68 题里，AI 应用岗的 ★★★ 必背题能答出"考察点 + 要点"。

---

## 二、知识分层与面试权重（AI 应用岗定制）

| 分层 | 笔记章节 | 对应面试题（第 16 章） | 精力 |
|---|---|---|---|
| **A 核心（约 55%）** | 10 / 11 / 13 / 07 / 06 | Q12–Q22、Q33–Q44、Q56–Q58 | ★★★ 精读 + 读代码 + 默写 |
| **B 重点（约 30%）** | 12 / 14 / 01 / 02 + 评测 | Q1–Q11、Q23–Q32（讲思路）、Q45–Q48 | ★★ 理解 + 能讲 |
| **C 补充（约 15%）** | 09 / 04 / 05 / 08 / 03 | Q32、Q52–Q55 | ★ 浏览 + 记关键点 |

> 核心判断：**13、10、07、11 是"拉开差距"的部分**；01/02 是"破冰必问"；03 环境搭建、08 图片生成基本只在被问到时一句话带过。

---

## 三、一周逐日任务卡

> 每天按 **三遍法**：① 读笔记抓"为什么 + 结论" → ② 打开源码验证 → ③ 合上笔记口述。

### Day 0（约 1.5h）建立考题地图
- [ ] 通读 `15_面试知识点整理.md` 一遍
- [ ] 通读 `16_面试题集.md` 一遍
- [ ] 用笔圈出所有"答不上来"的题，形成你自己的**必背清单**
- [ ] 把第六节"默写材料"的 5 段代码抄一遍（先建立印象）

### Day 1（2–3h）精读笔记 10：Harness 与多 Agent 设计
- [ ] 精读 `10_Harness工程+多Agent设计.md`
- [ ] 对照 `15` 章 第三节（多 Agent 设计）+ 第四节（Harness 方法论）
- [ ] 必看源码：`api/app/agents/registry.py`、`api/app/agents/policy.py`
- [ ] 做 16 章题：**Q12、Q13、Q14、Q18、Q19**
- [ ] 口述验收：Harness 四维度 + 每个维度对应实现 + "三个分离" + 为什么两个 Agent 零工具

### Day 2（2–3h）精读笔记 11 + 06：数据合同、工具边界、模型接入
- [ ] 精读 `11_Agent数据合同与工具边界.md`、`06_模型配置与调用.md`
- [ ] 对照 `15` 章 6.4（数据合同）+ 6.5（规则兜底）
- [ ] 必看源码：`agents/contracts.py`、`agents/policy.py`、`core/config.py`、`services/llm.py`
- [ ] 做 16 章题：**Q14、Q15、Q40、Q41、Q49、Q50**
- [ ] 口述验收：`extra="forbid"` 为什么重要、OpenAI 兼容协议、密钥只写不读、R0–R3 分级

### Day 3（3h，全计划最重）精读笔记 13：图编排、工具网关、人工审批
- [ ] 精读 `13_图编排、工具网关与人工审批.md`
- [ ] 对照 `15` 章 第六节（商品诊断工作流逐节点）+ 6.3（interrupt 易错点）+ 第七节（两套图）
- [ ] 必看源码：`agents/graph.py`、`agents/tool_gateway.py`、`agents/specialists.py`、`agents/persistence.py`
- [ ] 做 16 章题：**Q33、Q34、Q35、Q36、Q37、Q38、Q39、Q51、Q62**
- [ ] 默写：商品诊断 7 节点图（含返修回路）+ interrupt 两个易错点 + 规则兜底代码

### Day 4（2–3h）精读笔记 07 + 评测：LLM 工程化
- [ ] 精读 `07_文本模型服务.md`
- [ ] 评测部分看 `15` 章 九（可观测性）+ `16` 章 十一（评估与测试 Q56–Q58）
- [ ] 必看源码：`services/llm.py`、`agents/specialists.py`、`agents/evaluation.py`、`api/evals/product_operation_cases.json`
- [ ] 做 16 章题：**Q42、Q43、Q44、Q56、Q57、Q58**
- [ ] 口述验收：结构化输出怎么保证、LLM 失败/幻觉怎么兜底、fake_model 怎么评测

### Day 5（2–3h）精读笔记 12 + 14：可靠投递与可靠恢复（讲思路）
- [ ] 精读 `12_Agent任务记录与可靠投递.md`、`14_运行维护、租约与可靠恢复.md`
- [ ] 对照 `15` 章 第五节（可靠投递链路）+ 第八节（Task vs Run）
- [ ] 必看源码：`services/agent_tasks.py`、`services/outbox.py`、`services/agent_leases.py`、`services/agent_maintenance.py`、`worker/celery_app.py`
- [ ] 做 16 章题：**Q23、Q24、Q25、Q26、Q27、Q28、Q29、Q45、Q46**
- [ ] 默写：完整时序图 + 幂等落库伪代码 + 条件续租 UPDATE

### Day 6（2–3h）略读 01/02/04/09 + 背 STAR
- [ ] 略读 `01_项目介绍.md`、`02_技术架构.md`、`04_数据模型设计.md`、`09_Celery后台生成任务.md`
- [ ] 对照 `15` 章 第一、二、八节 + 十一（STAR 话术）
- [ ] 做 16 章题：**Q1–Q11、Q47、Q48、Q10、Q11**
- [ ] 背诵并脱稿：STAR 项目介绍（2 分钟版）+ 三库职责 + `task_acks_late` 一句话

### Day 7（3h）全量自测
- [ ] 16 章 68 题全部口述一遍，重点 ★★★ 必背题
- [ ] 默写 5 段代码（见第六节）
- [ ] 默画可靠投递完整时序图
- [ ] 开放题 Q59–Q63 各说 3 点（尤其 Q60 模型质量下降、Q62 两套图为什么）
- [ ] 用第七节"验收清单"逐项勾选，卡壳处回查笔记

---

## 四、必背源码速查表

| 章节 | 必看源码（`api/app/`） | 必须能口述的点 |
|---|---|---|
| 10 | `agents/registry.py`、`agents/policy.py` | Harness 四维度、三个分离、两个零工具 Agent |
| 11 | `agents/contracts.py`、`agents/policy.py` | `extra="forbid"` 拒多余字段、工具白名单、R0–R3 |
| 13 | `agents/graph.py`、`agents/tool_gateway.py`、`agents/specialists.py` | 7 节点图、条件边返回节点名、interrupt 两易错点、`source="rules"` 兜底 |
| 07 | `services/llm.py`、各文本 service | `response_format=json_object` + Pydantic 强校验、`provenance` 可追溯 |
| 06 | `core/config.py`、`.env` | OpenAI Chat Completions 兼容、模型四要素、api_key 只写不读 |
| 12 | `agents/registry.py`、`services/agent_tasks.py` | 三大注册表版本化、Task vs Run、Outbox 同事务 |
| 14 | `services/agent_leases.py`、`services/outbox.py`、`services/agent_maintenance.py` | 心跳续租带条件 UPDATE、fencing token、巡检恢复 |
| 评测 | `agents/evaluation.py`、`evals/product_operation_cases.json` | fake_model 三种行为、断言最终状态、六类边界 |

---

## 五、AI 应用岗面试题优先级清单（第 16 章题号）

### ★★★ 必背（拉开差距）
- **Q18** Harness 四维度
- **Q13** 为什么协调/质量 Agent 零工具
- **Q33 / Q34 / Q36 / Q37 / Q38 / Q39** LangGraph：State/Node/Edge、interrupt、thread_id、副作用、条件边、返修
- **Q41 / Q42** 结构化输出 + LLM 兜底
- **Q56 / Q57 / Q58** Agent 评测
- **Q15 / Q19** 越权防护 / 可控

### ★★ 高频
- **Q23 / Q24** Outbox（讲思路）
- **Q25 / Q26** 租约 + fencing（讲思路）
- **Q35** checkpoint 为什么用 PostgreSQL
- **Q43 / Q44** temperature / token 预算
- **Q7** 三库职责、**Q10** acks_late、**Q62** 两套图、**Q60** 模型质量下降

### ★ 基础（破冰必问）
- **Q1–Q6** 项目介绍/架构、**Q12** 9 Agent 分工、**Q40** LLM 接入、**Q45** Task vs Run

### 编码实战（AI 应用岗尤其要会现场写）
- **Q65** LangGraph 条件分支图、**Q66** Pydantic 数据合同（必会）
- **Q64** Celery 任务、**Q67** 幂等落库、**Q68** 条件续租 UPDATE（会写思路即可）

---

## 六、默写材料（5 段关键代码 + 1 张图）

### 1. Pydantic 数据合同（Q66）
```python
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class DiagnosisDraft(StrictModel):
    source: Literal["llm", "rules"]
    positioning: str = Field(min_length=1)
```

### 2. LangGraph 条件分支图（Q65）
```python
builder = StateGraph(OrderState)
builder.add_node("decide", decide_route)
builder.add_node("manual", manual_review)
builder.add_node("auto", auto_approve)
builder.add_conditional_edges("decide", choose_next, {"manual": "manual", "auto": "auto"})
```

### 3. LLM 规则兜底（`specialists.py`）
```python
try:
    result = self.completion_client(...)
    validated = ProductDiagnosisOutput.model_validate(result.output)
    diagnosis = DiagnosisDraft(source="llm", **validated.model_dump(), provenance={"model": result.model})
    return SpecialistResult(diagnosis.model_dump(), result.usage)
except (LLMNotConfiguredError, LLMResponseError, ValidationError) as exc:
    fallback = _rule_based_diagnosis(context, fallback_reason=str(exc))
    return SpecialistResult(fallback.model_dump(), ModelUsage())
```

### 4. 幂等落库伪代码（Q67）
```python
operation = db.scalar(select(AgentRunOperation).where(run_id=..., operation_key=...))
if operation and operation.status == "completed":
    return operation.result
if operation is None:
    operation = AgentRunOperation(status="running"); db.add(operation); db.flush()
# ... 执行副作用
operation.status = "completed"; operation.result = result; db.commit()
```

### 5. 条件续租 UPDATE（Q68）
```python
result = db.execute(
    update(AgentRun)
    .where(AgentRun.id == run_id,
           AgentRun.status == RUNNING,
           AgentRun.lease_owner == lease_owner,   # fencing token
           AgentRun.cancel_requested_at.is_(None))
    .values(lease_expires_at=now + LEASE_DURATION)
)
if result.rowcount != 1:
    return
```

### 6. 商品诊断 7 节点图（默画）
```
START → product_context → diagnosis → creative_strategy → quality_review
                              ↑（返修回路 prepare_revision，revision_count < max_revisions）
                      通过 → human_review_gate（interrupt 暂停）→ finalize_output → END
```

---

## 七、验收清单（全部勾选即可去面）

- [ ] 2 分钟 STAR 项目介绍能脱稿（含"规则保稳定、模型给建议、人做最终决策"）
- [ ] 一句话讲清 Harness 四维度，每个维度能说一个实现 + 一个"不做会怎样"
- [ ] 默画商品诊断 7 节点图（含返修回路、条件边、interrupt 闸门）
- [ ] 能讲清 interrupt 两个易错点 + `thread_id` 为什么必须相同
- [ ] 能答"如何保证 LLM 结构化输出""LLM 失败/幻觉怎么兜底"（`StrictModel` + `try/except` 降级 + `source="rules"` + `provenance`）
- [ ] 能答"为什么两个 Agent 零工具""三个分离是什么"
- [ ] 能答"如何评测 Agent 效果"（fake model + 固定用例 + 边界覆盖）
- [ ] 能画出可靠投递完整时序，讲清每段防什么
- [ ] 默写 5 段代码通过（见第六节）
- [ ] 开放题 Q59–Q63 各能说 3 点

---

## 八、开放题提示（Q59–Q63，各说 3 点即可）

| 题 | 要点 |
|---|---|
| Q59 并发翻 10 倍 | 水平扩 worker、加只读副本/连接池、热点缓存、查并发上限与 SKIP LOCKED 是否成瓶颈 |
| Q60 模型质量下降 | 看 `source="rules"` 降级比例 + `provenance` 定位、质量 Agent 失败率告警、评测集回归、提示词版本化 |
| Q61 多轮记忆 | 已有 `AgentMemory` 表（结构化事实 + scope + 引用 + 有效期），在 `AgentConversation` 上加记忆检索注入 |
| Q62 两套图为什么 | 商品诊断是重点案例用硬编码细粒度图（有返修回路），其余 6 条走注册表驱动通用图，能力复用 + 配置化编排 |
| Q63 模型调用慢 | 慢任务交 Celery、API 立即返回任务编号、心跳线程独立续租、前端轮询数据库状态 |

---

*本计划配套笔记：`note/15_面试知识点整理.md`、`note/16_面试题集.md`；关键代码已在 `api/` 源码中核对。*
