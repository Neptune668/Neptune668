# AI 应用开发岗位 · 面试题库与参考答案

> 基于本工程（电商运营助手后端）真实实现整理，面向「AI 应用开发」岗位。所有模型名、配置键、枚举、文件路径均与代码一致，面试时可直接引用。
>
> 与《电商运营助手》项目面试串讲.md 的区别：本文件按「AI 应用开发」的考察维度重新组织，重点放在 LLM 接入、结构化输出、Agent 编排、受控工具、可靠投递、记忆/RAG、评测与多模态，答案以「要点」形式给出，便于背诵。

---

## 一、大模型接入与结构化输出

### Q1. 大模型是怎么接入的？为什么用 `response_format=json_object`？
**参考答案要点**
- 走 OpenAI 兼容的 `/chat/completions`（`api/app/services/llm.py` 里 `_chat_completion_url` 会自动补 `/chat/completions`）。
- 所有业务都用 `create_json_chat_completion`，强制 `response_format={"type": "json_object"}` + 提示词里反复要求「只输出合法 JSON、不输出 Markdown」，从两个层面把输出约束成 JSON。
- 拿到 content 后 `json.loads` 解析，再交给 Pydantic 模型校验（如 `ProductDiagnosisOutput`），解析失败抛 `LLMResponseError` 由上层兜底。
- 补充：为什么不用 `temperature=0` 追求完全确定？——诊断/创意需要一定发散，所以温度设 0.25/0.35；确定性的诉求交给「结构化校验 + 规则质检」而非压温度。

### Q2. 怎么保证大模型输出的结构可靠？模型「乱说」怎么办？
**参考答案要点**
- 四道防线：① JSON mode 约束；② Pydantic `StrictModel`/`Field(min_length=...)` 校验，字段对不上直接抛 `ValidationError`；③ 每个 Agent 的 try/except 捕获 `LLMNotConfiguredError / LLMResponseError / ValidationError`，回退到 `_rule_based_*` 规则版（`specialists.py`、`diagnosis.py` 都有规则兜底）；④ 质量合规 Agent 做规则质检，不达标进返修/人审。
- 强调「LLM 失败不阻断业务」：模型没配/挂了，规则版仍能产出可继续的草稿（`source` 标记为 `rules`），整条运营链路不中断。

### Q3. 为什么要做规则兜底，而不是失败就报错？
**参考答案要点**
- 诊断是素材、投放建议的上游（`diagnosis.py` 注释明确写了「模型不可用时用规则版保持单品运营链路可继续」）。
- 兜底保证可用性（availability），但代价是质量下降，所以 `provenance` 里记录 `fallback_reason`，并在复盘规则版里追加「本次使用规则版兜底，原因：xxx」，让下游能感知「这次是降级结果」。
- 这是 AI 应用很关键的一个点：区分「模型不可用的降级」和「模型输出不合规的返修」，二者处理策略不同。

### Q4. DeepSeek 的 `thinking` 为什么要显式禁用？
**参考答案要点**
- `llm.py` 里对 `deepseek` 前缀的模型加了 `payload["thinking"] = {"type": "disabled"}`。
- 原因：本项目要的是「稳定、低延迟的结构化输出」，推理链（thinking）会多消耗 token、增加首字延迟，且思考内容可能干扰 JSON 解析。
- 面试加分点：这体现「按场景选择模型行为」——做代码/复杂推理才开 thinking，做结构化抽取/生成就关掉。

---

## 二、多 Agent 与 LangGraph 编排

### Q5. 为什么选 LangGraph？它的 StateGraph、节点、条件边、`interrupt` 分别怎么用？
**参考答案要点**
- `StateGraph(AgentWorkflowState)` 构建图：`add_node` 注册节点，`add_edge` 连固定顺序，`add_conditional_edges` 做条件路由（如 `_quality_route` 根据质检结果走 `revise`/`review`）。
- 状态用 `TypedDict`（`AgentWorkflowState`）做「所有节点读写的中枢」，节点只返回自己负责的增量字段，避免节点间直接传参。
- `interrupt(...)` 是人工审批的暂停点：把草稿 + 质检报告塞进返回值并持久化到 checkpoint，之后 `Command(resume=resume_payload)` 从断点继续，前面跑完的 Agent 不重跑。
- 选 LangGraph 的核心理由：内置**检查点持久化**（checkpointer）+ **中断/恢复**（interrupt/resume），正好匹配「长流程 + 人审 + 崩溃恢复」的需求，不用自己造状态机。

### Q6. 为什么拆成 9 个专用 Agent，而不是一个大 Agent 挂一堆工具？
**参考答案要点**
- 单 Agent + 工具：工具一多系统提示词膨胀，模型易混淆职责、乱调无关工具。
- 拆开的好处：① 职责收敛，降低幻觉和误调用；② 权限粒度更细（库存 Agent 能看到 `inventory.adjust`，创意 Agent 完全看不到）；③ 可观测（日志/事件能定位到具体角色）；④ 编排灵活（工作流决定角色顺序）。
- 代价：要维护注册表和多套提示词。
- 关键澄清（面试常被追问）：**不是多个 Agent 互相聊天**，而是上层工作流驱动顺序执行，Agent 之间只通过共享 State 传递结构化数据。

### Q7. 基础图（`graph.py`）和平台图（`platform_graph.py`）是什么关系？
**参考答案要点**
- 基础图 `build_product_operation_graph`：把「商品诊断与优化」这条业务线讲透，节点硬编码（上下文→诊断→创意→质检→返修/人审→落库），是「特例实现」。
- 平台图 `build_platform_workflow_graph`：由 `WORKFLOW_REGISTRY` 驱动，用同一套编排代码装配全部 7 条工作流，是「通用实现」。
- 二者通过 `WORKFLOW_ALIASES` 打通：`product_operation` → `product_diagnosis_optimization`；命中诊断优化时平台图转调基础图（`agent_workflows.py` 里 `run_registered_agent_workflow` 判断后调 `run_agent_workflow`）。
- 体现的工程思想：先做单条可验证的样板，再抽象成注册表驱动的框架，两条链路共享同一套「租约 + Outbox + Checkpoint」可靠性骨架。

### Q8. Checkpoint 持久化解决什么问题？项目怎么用？
**参考答案要点**
- Checkpoint 是 LangGraph 的状态持久化，保存图每一步的 State。项目用 PostgreSQL（`langgraph-checkpoint-postgres` 的 `PostgresSaver`），和业务 MySQL 分开。
- 作用：① 执行到 `interrupt` 人审时，完整 State 落库、Worker 释放租约退出；② 审批后按 `thread_id` 读回状态、从中断节点往后跑，已完成的 Agent 不重跑；③ Worker 崩溃可恢复，不丢中间上下文。
- 一个细节：`persistence.py` 用 contextmanager 让「每个 Celery 任务独立持有连接」，避免 worker fork 后复用父进程数据库连接。

---

## 三、Agent 安全与受控工具调用

### Q9. 为什么不让大模型自由 Function Calling，而要做「受控工具调用」？
**参考答案要点**
- 自由调用意味着可能随意改库存、删数据、产生越权副作用。
- 项目不是让模型自己选工具，而是：工作流预定义每个 Agent 要调的工具，`ToolGateway` 统一拦截、逐层校验后由**确定性代码**执行（`_execute_tool` 里 handler 映射到已有 service），模型只负责「生成内容」，不负责「决定能不能改数据」。
- 一句话：把「要不要执行、能不能执行」从模型手里收回到策略层，模型只做生成。

### Q10. R0–R3 风险分级和完整授权链路是什么？
**参考答案要点**
- 分级（`registry.py` 的 `TOOL_REGISTRY`）：R0 只读（`product.read` 等）、R1 生成草稿（`diagnosis.draft`、`creative.plan.draft` 等）、R2 需人工审批（`ad.experiment.create`、`artifact.persist`）、R3 仅 Owner（`inventory.adjust`，`owner_only=True`）。
- 授权链路（`tool_gateway.py` + `policy.py`）层层防御：① 先校验 run 归属 workspace + 有效租约（`require_active_lease` 带行锁）；② `authorize_tool` 校验 Agent 白名单是否含该工具；③ VIEWER 只能 R0；④ owner_only 工具仅 OWNER；⑤ R2/R3 标记需审批 → 抛 `ToolApprovalRequired` 中断工作流写 `AgentApproval`。
- 关键点：即使注册了工具、也在白名单里，只要 handler 没实现，`ToolGateway` 会直接拒绝（`Tool has no executable adapter`）——「注册」≠「可执行」，元数据与实现解耦。

### Q11. 工具调用的幂等性是怎么保证的？
**参考答案要点**
- `AgentRunOperation` 表 + `operation_key`（如 `tool:{agent_key}:{tool_key}`、`finalize-v1`）。
- 执行前先查：同 run 同 key 且 status=`completed` 则直接返回上次结果；否则新建 `running` 记录，成功后置 `completed`。
- 配合 Celery 的 `task_acks_late` + `task_reject_on_worker_lost`（消息可能重复投递），以及租约 fencing（`lease_owner` 不匹配直接拒绝写入），共同吸收「消息重复消费」产生的脏数据。

---

## 四、可靠投递与故障恢复（后台任务）

### Q12. Outbox 发件箱模式解决什么问题？原理？
**参考答案要点**
- 解决「数据库写入成功、但发消息失败导致任务丢失」：创建任务要写 Task/Run 记录 + 发 Celery 消息，若消息投递时网络异常，会出现「有记录但永远不执行」。
- 做法：同一事务里写业务记录 + `OutboxEvent`（`pending`），成功一起提交、失败一起回滚；独立的 `maintenance.dispatch_outbox`（beat 每 5s）扫描 pending 事件投递到 `agent.workflow` 队列，失败退避重试、超 10 次置 `failed`，保证最终一致性。
- 注意 `idempotency_key` 和 `with_for_update(skip_locked=True)`：多个调度实例并发扫表也不会重复投递。

### Q13. Worker 任务卡死/崩溃怎么识别和回收？
**参考答案要点**
- 租约 + 心跳：认领时写 `lease_owner` + `lease_expires_at`（5 分钟），后台心跳线程每 60s 续租；`maintenance.agent_runtime`（beat 每 30s）扫描 `RUNNING` 且租约过期的 Run，重置为 `QUEUED`、`attempt+1`、重新生成 Outbox 事件入队。
- fencing：`require_active_lease` 每次写前校验 `lease_owner` 一致，旧的崩溃 worker「复活」后也无法覆盖新 worker 的进度。
- 分三层各管一段：**Outbox** 管消息不丢、**租约** 管宕机识别与回收、**Checkpoint** 管恢复不重跑。

### Q14. 同一商品/同一工作区并发发起多个 Agent 任务怎么保护？
**参考答案要点**
- 两个粒度：① 行级——认领/查询用 `with_for_update` 行锁，避免多 worker 同时认领同一行；② 租户级——`_enforce_workspace_concurrency` 锁 Workspace 行后计数，单工作区最多 10 个活跃 Run，超出直接拒绝，防止一个租户占满资源。
- 补充：同一商品维度还有「已有非终态 Run 则拒绝新任务」（`create_agent_run_record` 里 `active_run` 检查），避免对同一商品重复跑。

---

## 五、记忆 / 上下文工程（RAG 视角）

### Q15. 项目里的「记忆」是怎么实现的？和 RAG 是什么关系？
**参考答案要点**
- 只有**长期记忆**、没有短期记忆/对话历史：用户在 Agent 中心手动保存一个结构化值（`AgentMemory`），带 `scope_type`（workspace/user/product/store）、`memory_key`、`effective_at/expires_at`、`status`。
- 任务启动时 `_memory_context` 按 scope 过滤加载有效记录（`status=ACTIVE` 且时间窗内），`limit 50` 注入上下文。
- 和 RAG 的关系：本质是「结构化、作用域过滤的上下文注入」，**没有**向量检索、没有 embedding、没有摘要压缩。`memory_key` 非唯一索引，同 key 多条并存、无冲突仲裁——这是当前局限，面试可主动点出并给改进方向（向量化 + 语义检索 + 摘要压缩 + 冲突仲裁）。

### Q16. 上下文是怎么裁剪/控成本的？
**参考答案要点**
- token 预算：全局 `AGENT_MAX_TOTAL_TOKENS=12000`，每次调模型前 `remaining_model_tokens` 计算剩余额度，耗尽抛 `AgentBudgetExceededError` 熔断本次运行。
- 记忆只加载有效记录 + `limit 50`；经营复盘只取最近周期 + 近几期做上下文，避免把历史样本混成实时结论。
- 非推理环节走规则不走模型（质检、价格带判断、指标补算等），省 token 又确定。

---

## 六、评测与可观测性

### Q17. Agent 是怎么测评的？关注哪些指标？
**参考答案要点**
- 两层：研发阶段离线评测（固定用例集、假模型档位隔离随机性、对结构化字段断言）；运行阶段看任务完成率、质检通过率/返修率、人审通过率与采纳率（编辑后通过占比最能反映质量）、广告实验的 CTR/CVR/ROI AB 对比。
- 现有测试 `test_agent_foundation.py` 覆盖了策略层：工具白名单允许/拒绝、未知 Agent 拒绝、快照脱敏。
- 诚实说明短板：客户满意度无埋点，最接近的信号是人审反馈。

### Q18. 可观测性怎么做的？敏感信息怎么处理？
**参考答案要点**
- 每个节点用 `_run_observed` 包装：OpenTelemetry 建 span（trace_id/span_id）+ 记录 `agent_step_started/completed/failed` 事件到 `AgentRunEvent`，带 latency、脱敏后的输入输出快照。
- `redact_snapshot`（`harness.py`）做安全快照：命中 `api_key/password/token/secret` 等字段替换为 `[redacted]`；超长字符串截 2000 字符；嵌套深度上限 8、条目上限 200，防止递归爆炸和自引用。
- 这解决「可回放但密钥不泄漏、体积有硬上界」。

---

## 七、多模态生成（图片/视频）

### Q19. 即梦文生图/文生视频是怎么接的？异步任务怎么处理？
**参考答案要点**
- 火山引擎 `CVSync2AsyncSubmitTask` 提交 → 拿 task_id → `CVSync2AsyncGetResult` 轮询取 URL → 下载到本地 `uploads`（避免供应商临时链接过期）。
- 签名：`volcengine.py` 手写 HMAC-SHA256 四级派生密钥（日期/区域/服务/request），生成 `Authorization` + `X-Date` + `X-Content-Sha256`。
- 模型硬编码校验：图片必须 `jimeng_t2i_v30`、视频必须 `jimeng_t2v_v30`；视频是纯文生视频，带参考图会显式拒绝。
- 提示词清洗 `_sanitize_*_prompt`：替换特殊货币符号、全角引号、不可见字符，降低接口解析失败概率。

### Q20. 生成的图片/视频怎么质检？能自动返修吗？
**参考答案要点**
- 次序要说对：质检在**调即梦之前**（针对主图方案/视频脚本的文本草稿），是纯规则（诊断建议数量、角度重复、绝对化违禁词、证明点缺失），不是识图。
- 即梦产物**本身不做机器质检**：没有 OCR、没有视觉模型；产物下载入库后状态默认「待评估」，由运营人工改为通过/弃用/复测。
- 返修分两层：文本草稿返修（质检问题转反馈注入提示词重跑，最多 1 次）vs 生成任务技术重试（失败/超时退避重试，最多 3 次）。成品图不能基于质检结果自动返修——这是改进方向（图生图 + 视觉模型做保真比对）。

---

## 八、工程化与生产落地

### Q21. 模型配置为什么能做「数据库覆盖环境变量」？
**参考答案要点**
- `model_settings.py` 的 `get_runtime_settings`：优先读 `ModelProviderSetting` 表（text/image/video 三个 target 分开存），字段为空才回退环境变量。
- 好处：运营后台改模型不用重启、不用改部署；文本/图片/视频供应商解耦，只换图片模型不影响文本链路。
- 密钥处理细节：保存时「空字符串表示不更新密钥」，避免表单回显时把已有 key 清空；读回时只返回 `api_key_masked` 和 `has_api_key`，不泄露明文。

### Q22. 这套多 Agent 平台有哪些局限？上生产会怎么改进？
**参考答案要点**
- 局限：① 意图路由只用关键词规则，复杂自然语言意图识别弱；② Agent 之间靠全局 State 交换，State 会随业务膨胀、无消息隔离；③ 记忆只按 scope 过滤、缺摘要压缩；④ 工具限流/熔断未完整实现，下游抖动会连锁影响任务。
- 改进：意图路由换轻量 LLM 分类；State 设大小上限 + 大上下文摘要压缩；ToolGateway 加限流熔断、LLM 加超时退避；补每个 Agent 的调用次数/token/失败率指标 + 链路追踪；加工具调用审计日志。

### Q23. 自研 Token 鉴权踩过什么坑？生产会怎么做？
**参考答案要点**
- 实现：hmac-sha256 签名，payload 只放 `sub/email/role/exp`，敏感信息不进 Token。
- 踩坑：最初只验签名没回查数据库，导致「账号禁用后旧 Token 仍有效」；后来加了「每次请求解析后回查用户状态」（`ensure_user_can_login`）。
- 生产：会换成成熟 JWT 库，但「签名为先、回查用户状态、权限后端强校验」这些原则不变。

---

## 附：高频速查（背这些足够应付一轮）

| 主题 | 一句话答案 |
| --- | --- |
| 架构分层 | FastAPI + SQLAlchemy(MySQL) + Celery/Redis + LangGraph + PostgreSQL(Checkpoint) |
| Agent 规模 | 9 个角色 / 16 项工具 / 7 条工作流 |
| 风险分级 | R0 只读 · R1 草稿 · R2 人审 · R3 仅 Owner |
| 授权入口 | `ToolGateway` 统一校验身份 / 工作区 / 角色 / 租约 / 幂等 |
| 结构化输出 | JSON mode + Pydantic 校验 + 规则兜底 |
| Token 预算 | 全局 12000，耗尽熔断；返修上限 1 次 |
| 可靠投递 | Outbox（消息不丢）+ 租约（宕机回收）+ Checkpoint（恢复不重跑） |
| 并发保护 | `with_for_update` 行锁 + 单工作区 10 个活跃 Run 上限 |
| 记忆 | 长期记忆、scope 过滤，无向量检索/无短期记忆 |
| 多模态 | 即梦 `jimeng_t2i_v30` / `jimeng_t2v_v30`，异步提交 + 轮询 + 火山签名 |
| 评测 | 离线用例 + 规则质检 + 任务/质量/业务三层指标 |
