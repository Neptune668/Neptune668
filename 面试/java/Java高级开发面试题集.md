# Java 高级开发工程师面试题集（含答题要点）

> **面向岗位**：高级 Java 后端开发（5 年+ / 架构方向）
> **标签说明**：【高频】高级面试常见、必须掌握 ｜【深入】拉开差距的深度/加分题
> 高级岗位重点考察：底层原理深度、架构设计能力、线上故障排查经验，以及系统设计题。

---

## 一、Java 基础

### 1.【高频】Java 只有值传递，如何辨析"传引用"的误区？
- Java 方法参数传递永远是值传递：基本类型传"值的副本"，引用类型传"引用地址的副本"。
- 传入对象时，方法内修改对象属性会影响原对象（副本与原引用指向同一对象）；但重新赋值/`new` 只改副本，不影响原引用。
- 结论：Java 是 pass-by-value，不存在真正意义的引用传递（pass-by-reference）。

---

## 二、集合与并发

### 1.【高频】CountDownLatch、CyclicBarrier、Semaphore 的区别？
- CountDownLatch：一次性，一个/多个线程等待计数减到 0（countDown），不可复用。
- CyclicBarrier：可循环复用，一组线程互相等待到齐后一起执行（await）。
- Semaphore：信号量，控制同时访问资源的线程数（acquire/release），用于限流。
- 场景：CountDownLatch 等任务完成再汇总；CyclicBarrier 多线程分阶段协同；Semaphore 连接池/限流。

### 2.【高频】阻塞队列原理？ArrayBlockingQueue 与 LinkedBlockingQueue 区别？
- 阻塞队列基于 ReentrantLock + Condition（notFull/notEmpty），满时 put 阻塞、空时 take 阻塞。
- ArrayBlockingQueue：有界数组、单把锁（读写共用）、可配公平锁。
- LinkedBlockingQueue：链表、可无界、两把锁（putLock/takeLock）分离读写、吞吐更高。
- 应用：线程池任务队列、生产者-消费者模型。

---

## 三、JVM

### 1.【高频】线上 OOM 如何排查？
- 区分类型：堆溢出（OutOfMemoryError: Java heap space）、栈溢出（StackOverflowError）、元空间溢出、直接内存溢出。
- 抓堆：`-XX:+HeapDumpOnOutOfMemoryError` 生成 dump → MAT/JProfiler 分析 Dominator Tree、GC Roots、大对象引用链。

### 2.【高频】CPU 使用率飙高如何定位？
- `top` 找进程 → `top -Hp <pid>` 找高 CPU 线程 → `printf '%x'` 转十六进制 → `jstack <pid> | grep -A 20 <nid>` 定位代码。
- 常见原因：死循环、频繁 GC、正则回溯、大量计算、锁竞争。

### 3.【高频】G1 收集器原理？
- Region 分区（默认 2048 个，1~32M），逻辑分代、物理不分，可预测停顿模型。
- Young GC + Mixed GC；通过 RSet（Remembered Set）避免全堆扫描、SATB 快照保证并发标记正确性。
- 适合大堆、要求可预测停顿的场景；相比 CMS 无碎片。

### 4.【深入】内存泄漏如何排查？常见场景？
- 多次 `jmap` 快照或 dump 对比，观察对象数量持续增长；`jstat` 观察 GC 后老年代仍高。
- 常见场景：静态集合持有对象、ThreadLocal 未 remove、连接/流未关闭、监听器未注销、内部类持有外部类。

---

## 四、数据库与事务

### 1.【高频】分库分表如何设计？
- 垂直拆分（按业务/字段拆库表）解决单库压力与耦合；水平拆分（按分片键路由）解决单表数据量。
- 关键：分片键选择、路由算法（哈希/范围）、全局唯一 ID、跨库 join 与分布式事务、数据迁移与平滑扩容（一致性哈希/双倍扩容）。

### 2.【高频】主从复制原理？读写分离如何保证一致性？
- 主库写 binlog，从库 IO 线程拉取写 relay log，SQL 线程重放；异步/半同步复制。
- 读写分离提升读吞吐但存在延迟；一致性方案：敏感操作强制走主库、半同步复制、并行复制、GTID。

### 3.【高频】大表如何优化？慢查询如何治理？
- 慢查询定位：slow_query_log + mysqldumpslow + Explain。
- 优化：加/调索引、避免 select *、深分页优化（延迟关联/游标）、归档冷数据、分库分表。

### 4.【深入】数据库死锁如何排查与避免？
- 死锁典型：两事务交叉加锁；用 `SHOW ENGINE INNODB STATUS` 查看 LATEST DETECTED DEADLOCK。
- 避免：固定加锁顺序、事务尽量短、降低隔离级别、加索引缩小锁范围。

---

## 五、Spring 框架

### 1.【高频】Spring 事务失效场景汇总？
- 方法非 public、自调用（this 不经过代理）、异常被 catch 吞掉、rollbackFor 不匹配、类未被 Spring 管理、数据库引擎不支持事务、多线程调用（不同线程不同连接）、传播类型 NOT_SUPPORTED。

### 2.【高频】Spring 框架用到了哪些设计模式？
- 工厂（BeanFactory）、单例（Bean 默认）、代理（AOP）、模板方法（JdbcTemplate/RestTemplate）、观察者（事件机制）、适配器（HandlerAdapter）、策略（Resource 加载）、装饰器（BeanWrapper）。

### 3.【深入】Spring Boot 启动流程？
- new SpringApplication → 推断应用类型 → 加载 ApplicationContextInitializer/Listener → refresh()（IoC 初始化）→ 加载自动配置 → 启动 Web 服务器 → 发布 started/ready 事件。

---

## 六、Redis 缓存

### 1.【高频】Redis Cluster 原理？
- 16384 槽位分片，key 通过 CRC16%16384 定位槽；每个节点负责部分槽，master 带副本。
- 故障检测（Gossip 协议）、故障转移（选举新 master）；客户端 MOVED/ASK 重定向。
- 限制：不支持跨槽事务；批量操作需同槽（hash tag）。

### 2.【高频】大 Key、热 Key 问题如何发现与处理？
- 大 Key：单个 key 过大导致阻塞与带宽问题；用 `redis-cli --bigkeys`、`MEMORY USAGE` 排查；拆分/压缩。
- 热 Key：热点集中单节点；多级缓存、本地缓存、读写分离、key 拆分（复制多份分散压力）。

### 3.【深入】Redis 6.0 引入多线程的动机？
- 6.0 引入 IO 多线程（默认关闭），只负责网络读写与解析，命令执行仍单线程。
- 动机：网络 IO 成为瓶颈，多线程提升读写吞吐；命令单线程保证原子性。

### 4.【高频】Redis 与 Memcached 的区别？
- Redis：数据类型丰富、支持持久化、集群、发布订阅、事务/Lua 脚本。
- Memcached：只支持字符串、纯内存不持久化、多线程；简单缓存高性能场景可用。

---

## 七、消息队列

### 1.【高频】Kafka 架构原理？
- 分区（Partition）、副本（Replica）、ISR、Leader/Follower、Controller、高水位（HW/LEO）。
- 顺序写 + 页缓存 + 零拷贝实现高吞吐；消费组 + offset 管理。

### 2.【高频】RocketMQ 架构？事务消息、延迟消息原理？
- NameServer（路由）、Broker（存储）、Producer/Consumer；CommitLog + ConsumeQueue 存储结构。
- 事务消息：半消息（half message）→ 本地事务 → commit/rollback + 定时回查。
- 延迟消息：先投递到延迟队列，定时调度到期后投递真实队列。

### 3.【深入】如何设计一个消息队列？
- 存储（顺序写、分段文件）、通信（Netty）、高可用（副本同步）、消费（offset/ack）、路由（topic/分区）、可靠性（刷盘/复制）。

---

## 八、微服务与分布式

### 1.【高频】服务拆分的原则与边界？
- 单一职责、高内聚低耦合、按业务域（DDD 限界上下文）、数据自治（避免跨库 join）、考虑团队边界。
- 避免过度拆分（分布式事务、链路复杂、运维成本）。

### 2.【高频】Raft 与 Paxos 的核心思想？
- Paxos：基于多数派的一致性算法，难理解难实现。
- Raft：更易理解，领导者选举 + 日志复制 + 安全性；Leader 接收写请求复制到多数派后提交；Term 任期 + 心跳机制。

### 3.【高频】网关原理？限流算法？
- 网关：统一入口，负责路由、鉴权、限流、熔断、日志；Spring Cloud Gateway（WebFlux 非阻塞）。
- 限流算法：固定窗口（临界问题）、滑动窗口（精确但存储开销）、漏桶（匀速）、令牌桶（允许突发）。

### 4.【高频】如何设计接口幂等性？
- 幂等：多次请求结果一致；方案：唯一请求 id（去重表）、数据库唯一约束、乐观锁（版本号）、状态机、token 机制。

---

## 九、设计模式

### 1.【高频】手写单例？如何防止反射、序列化破坏？
- 双重检查锁 + volatile；静态内部类（延迟 + 线程安全）。
- 反射可破坏（setAccessible 调私有构造）；序列化反序列化会生成新实例；枚举单例天然防反射/序列化破坏。

### 2.【高频】观察者模式与发布-订阅模式的区别？
- 观察者：观察者直接注册到主题，主题直接通知，耦合较紧。
- 发布-订阅：中间增加事件总线/Broker，发布者与订阅者完全解耦。

### 3.【深入】责任链模式在框架中的应用？
- Servlet Filter 链、Spring Interceptor、网关过滤器、审批流。
- 好处：解耦、动态组合、灵活增删处理节点。

---

## 十、网络与操作系统

### 1.【高频】TCP 为什么三次握手、四次挥手？TIME_WAIT 作用？
- 三次握手：同步初始序列号、避免历史连接、双方确认收发能力；两次不安全、四次冗余。
- 四次挥手：TCP 全双工，两端独立关闭；TIME_WAIT 主动关闭方等待 2MSL，确保最后 ACK 到达、让旧连接报文消散。
- 大量 TIME_WAIT 优化：内核参数复用、减少短连接。

### 2.【高频】select、poll、epoll 的区别？
- select：fd 数组，O(n) 遍历，fd 上限 1024，每次拷贝到内核。
- poll：链表无上限，仍 O(n) 遍历。
- epoll：事件驱动，红黑树 + 就绪链表，O(1) 获取就绪事件，无 fd 上限，LT/ET 模式；ET 需非阻塞 + 一次性读完。

### 3.【高频】零拷贝原理？
- 传统 4 次拷贝（用户态/内核态来回）+ 多次上下文切换；mmap + sendfile 减少拷贝；sendfile + DMA 实现 2 次拷贝（内核态直接到网卡）。
- 应用：Kafka、文件传输、静态资源服务。

### 4.【高频】浏览器输入 URL 到页面展示的完整过程？
- DNS 解析 → TCP 三次握手 → 发送 HTTP 请求 → 服务器处理返回 → 浏览器解析渲染（DOM/CSSOM → 渲染树 → 布局 → 绘制）→ 四次挥手。
- 涉及：DNS 缓存、CDN、缓存策略、HTTPS 握手。

---

## 附：高频系统设计题（答题思路）

1. **设计一个秒杀系统**
   - 热点库存预热、前端限流 + 后端限流（令牌桶）、Redis 预扣减 + Lua 原子操作、异步下单（MQ）、防超卖、接口防刷、熔断降级。

2. **设计一个短链接系统**
   - 发号器（雪花/自增）→ Base62 编码 → 存储（MySQL + Redis 缓存）→ 302 跳转；处理 hash 冲突。

3. **设计一个分布式 ID 生成器**
   - 雪花算法 + 时钟回拨处理；美团 Leaf（号段模式 + 双 buffer）。

4. **设计一个限流器**
   - 令牌桶/漏桶/滑动窗口；Redis + Lua 或本地限流（Guava RateLimiter）。

5. **设计一个高并发缓存架构**
   - 多级缓存（本地 + Redis）、缓存一致性（Cache Aside + 延迟双删）、热点 key 治理、大 key 拆分、集群容灾。

---

## 附：高级岗位备考建议

1. **深度优先**：JVM、并发、分布式一致性、分库分表、Kafka/RocketMQ 架构是高级面试的分水岭，要能讲到底层实现。
2. **结合踩坑经验**：准备 2~3 个真实的生产故障案例（OOM、CPU 飙高、死锁、消息堆积、缓存雪崩），讲清"现象 → 定位 → 方案 → 复盘"。
3. **准备系统设计题**：秒杀、短链接、限流、ID 生成是高频设计题，要能画出架构图并说明取舍。
4. **表达架构思维**：回答时从"可用性、性能、一致性、扩展性"多维度权衡，体现全局视角。
