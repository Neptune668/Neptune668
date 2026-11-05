# Java 中级开发工程师面试题集（含答题要点）

> **面向岗位**：中级 Java 后端开发（2~5 年经验）
> **标签说明**：【基础巩固】初级必会、中级需秒答 ｜【重点】中级核心高频 ｜【拔高】接近高级、属加分项
> 每题给出精炼答题要点，覆盖"关键结论 + 底层原理"，供面试前快速过一遍。

---

## 一、Java 基础

### 1.【重点】深拷贝与浅拷贝的区别？如何实现深拷贝？
- 浅拷贝：只复制对象本身与基本类型字段值，引用类型字段仍指向同一对象（如 `Object.clone()` 默认、`Arrays.copyOf`）。
- 深拷贝：引用类型字段也复制出新对象，形成完全独立的对象图。
- 实现：重写 `clone()` 递归拷贝；序列化（`ObjectOutputStream` 写出再读入）；JSON 序列化（Jackson/Gson）。
- 注意：`clone()` 必须实现 `Cloneable` 接口，否则抛 `CloneNotSupportedException`；`BeanUtils.copyProperties` 是浅拷贝。

### 2.【重点】Java 异常体系？受检异常与非受检异常？try-with-resources 原理？
- 体系：`Throwable` → `Error`（不可恢复：OOM、StackOverflow）+ `Exception` → `RuntimeException`（非受检）+ 其他（受检）。
- 受检异常编译期强制处理（IOException、SQLException）；非受检异常运行期抛出（NPE、ClassCastException）。
- try-with-resources：资源实现 `AutoCloseable`，编译后自动生成 `finally` 调用 `close()`，关闭顺序与声明相反，并保留异常抑制信息。

### 3.【重点】反射原理与应用场景？JDK 动态代理与 CGLIB 区别？
- 反射：运行时获取 `Class` 对象，动态访问构造器/字段/方法，底层依赖 JVM 元数据（方法区/元空间）。
- 应用：Spring 依赖注入、MyBatis 结果映射、动态代理、注解处理。
- JDK 动态代理：基于接口，`Proxy` + `InvocationHandler`，只能代理实现了接口的类。
- CGLIB：基于继承生成子类，ASM 字节码，不能代理 `final` 类/方法；Spring Boot 2.x 后默认 CGLIB。

### 4.【重点】泛型类型擦除？`? extends` 与 `? super`？
- 类型擦除：泛型仅编译期有效，编译后类型参数被擦除（有界→上界，无界→Object），运行时无泛型信息。
- 影响：不能 `new T()`、不能用泛型做 `instanceof`、泛型数组受限；编译器通过桥方法保证多态。
- `? extends T` 上界通配符：只能读不能写（Producer）；`? super T` 下界通配符：只能写不能读（Consumer），即 PECS 原则。

### 5.【重点】Lambda 与 Stream 原理？Optional 用法？
- Lambda 是函数式接口的实例，编译期用 `invokedynamic` 生成，非匿名内部类（无 this 捕获问题）。
- Stream 惰性求值：中间操作（filter/map/sorted）惰性，终端操作（collect/reduce/forEach）触发；并行流底层 ForkJoinPool。
- Optional 防 NPE：`ofNullable`、`orElse`（立即求值）、`orElseGet`（惰性求值）、`map`、`flatMap`。

### 6.【基础巩固】接口与抽象类的区别？
- 抽象类：单继承，可有构造器/成员变量/普通方法，用于代码复用（is-a）。
- 接口：多实现，Java 8 后可有 default/static 方法，用于定义契约/能力（has-a）。
- 设计取舍：接口定义行为规范，抽象类提取公共实现。

---

## 二、集合与并发

### 1.【重点】HashMap 1.7 多线程死循环？ConcurrentHashMap 1.7 与 1.8 区别？
- 1.7 HashMap 扩容用头插法，并发 resize 可能形成环形链表导致 get 死循环；1.8 改尾插法解决。
- ConcurrentHashMap 1.7：`Segment` 分段锁（继承 ReentrantLock），默认 16 段，锁粒度粗。
- 1.8：CAS + synchronized 锁单个桶（链表头/红黑树根），粒度更细、并发更高，并引入红黑树（链表超 8 转树）。

### 2.【重点】synchronized 原理？锁升级过程？
- 基于 Monitor，对象头 Mark Word 记录锁状态，方法/代码块编译为 `monitorenter/monitorexit`。
- 升级：无锁 → 偏向锁（同线程多次获取）→ 轻量级锁（CAS 自旋）→ 重量级锁（OS 互斥量，阻塞）。
- 竞争加剧逐级升级且不可降级；1.6 后经大量优化，性能已接近 Lock。

### 3.【重点】volatile 原理？与 synchronized 区别？
- 保证可见性（写刷主存、读从主存，靠内存屏障 + MESI 缓存一致性）与有序性（禁止重排序），**不保证原子性**。
- synchronized 保证原子性 + 可见性 + 有序性，但阻塞、重量级。
- 经典应用：单例双重检查锁中 volatile 防止指令重排序返回半初始化对象。

### 4.【重点】CAS 原理？ABA 问题？
- CAS（Compare And Swap）：比较内存值 V 与预期值 A，相等则更新为 B，否则自旋；底层 CPU 原子指令（cmpxchg）+ `Unsafe`。
- ABA：值 A→B→A，CAS 误判未变化；解决：加版本号（`AtomicStampedReference`）。
- 缺点：高竞争自旋开销大、只能保证单变量原子性。

### 5.【重点】AQS 原理？ReentrantLock 与 synchronized 区别？
- AQS：FIFO 双向队列 + `volatile int state` + CAS 的同步框架；ReentrantLock、CountDownLatch、Semaphore 均基于它。
- ReentrantLock 优势：可中断、可超时、公平/非公平锁、多 Condition、可重入。
- synchronized 优势：JVM 优化后性能接近、自动释放、语义简单；两者均可重入。

### 6.【重点】线程池核心参数？执行流程？拒绝策略？线程数如何设置？
- 7 参数：corePoolSize、maximumPoolSize、keepAliveTime、unit、workQueue、threadFactory、handler。
- 流程：先建核心线程 → 队列满则建到最大线程 → 全满走拒绝策略。
- 4 拒绝策略：AbortPolicy（抛异常，默认）、CallerRunsPolicy（调用者执行）、DiscardPolicy（丢弃）、DiscardOldestPolicy（丢最旧）。
- 线程数：CPU 密集型 = N+1；IO 密集型 = 2N 或 N×(1+等待/计算时间比)。

### 7.【重点】ThreadLocal 原理？内存泄漏原因与预防？
- 每个 Thread 持有 ThreadLocalMap，key 是 ThreadLocal 弱引用，value 强引用。
- 泄漏：ThreadLocal 被 GC 后 key 变 null，但 value 仍被 Entry 强引用，线程池中线程不销毁则无法回收。
- 解决：用完调 `remove()`；ThreadLocalMap 在 get/set 时会惰性清理部分 null key。

---

## 三、JVM

### 1.【重点】如何判断对象死亡？GC Roots 有哪些？
- 引用计数法无法解决循环引用（Java 不用）；Java 用可达性分析。
- GC Roots：虚拟机栈本地变量表引用、方法区静态属性引用、常量池引用、JNI 引用、synchronized 持有的对象、JVM 内部引用（类加载器、Class 对象等）。

### 2.【重点】垃圾回收算法？
- 标记-清除：有内存碎片。
- 复制：无碎片但浪费一半空间（新生代 Eden:Survivor=8:1:1，用复制思想）。
- 标记-整理：无碎片但移动开销大（老年代）。
- 分代：新生代（朝生夕死→复制）、老年代（存活率高→标记-整理/清除）。

### 3.【重点】常见垃圾收集器？
- 新生代：Serial（单线程）、ParNew（多线程 Serial）、Parallel Scavenge（吞吐量优先）。
- 老年代：Serial Old、Parallel Old、CMS、G1。
- CMS（并发标记清除、低停顿）：初始标记→并发标记→重新标记→并发清除；缺点：碎片、浮动垃圾、对 CPU 敏感。
- G1：Region 分区 + 可回收性排序，可预测停顿；ZGC：着色指针 + 读屏障，亚毫秒停顿、可上 TB 堆。

### 4.【重点】类加载过程？双亲委派模型？
- 过程：加载 → 验证 → 准备（静态变量赋默认值）→ 解析（符号引用→直接引用）→ 初始化（执行 clinit）。
- 双亲委派：请求先给父加载器，父无法加载才自己加载，保证核心类安全与唯一性。
- 打破场景：SPI（JDBC 线程上下文类加载器）、Tomcat 类加载隔离、热部署。

### 5.【拔高】线上 OOM / CPU 飙高如何排查？
- OOM：加 `-XX:+HeapDumpOnOutOfMemoryError` 抓 dump → MAT/JProfiler 分析大对象与引用链；区分堆溢出 vs 元空间溢出。
- CPU 飙高：`top` 找进程 → `top -Hp` 找线程 → 转十六进制 → `jstack` 定位线程栈与代码位置。

---

## 四、数据库与事务

### 1.【重点】事务隔离级别？脏读/不可重复读/幻读？
- 读未提交（脏读）、读已提交（不可重复读）、可重复读（幻读，MySQL 默认）、串行化。
- 脏读：读到未提交数据；不可重复读：两次读结果不同（update）；幻读：两次查询行数不同（insert/delete）。
- InnoDB 在可重复读下通过 MVCC + 间隙锁基本解决幻读。

### 2.【重点】MVCC 原理？
- 通过 undo log + ReadView 实现多版本，读写不阻塞。
- 每行隐藏列：DB_TRX_ID（最后修改事务）、DB_ROLL_PTR（undo log 回滚指针）。
- 可重复读在事务第一次读时创建 ReadView，读已提交每次读都新建；快照读走 MVCC，当前读（FOR UPDATE）走锁。

### 3.【重点】InnoDB 锁机制？间隙锁、临键锁？
- 行锁（锁索引记录）、间隙锁（锁记录间空隙，防插入）、临键锁（= 行锁 + 间隙锁，左开右闭，默认）。
- 可重复读下靠间隙锁 + 临键锁解决幻读；加锁针对索引，未命中索引退化为表锁。

### 4.【重点】最左前缀原则？索引失效场景？
- 联合索引按最左匹配：查询从最左列开始且不跳过中间列才走索引（a,b,c → where a / a,b / a,b,c）。
- 失效：对索引列做函数/计算、隐式类型转换、`like '%xx'`、or 含非索引列、`!=`/`not in`、跳过联合索引最左列。

### 5.【重点】Explain 各字段含义？
- type（访问类型，优→劣：const > eq_ref > ref > range > index > all，目标到 ref/range）。
- key（实际用到的索引）、rows（预估扫描行数）。
- Extra：Using index（覆盖索引）、Using filesort（需优化排序）、Using temporary（临时表）、Using where。

### 6.【重点】索引为什么用 B+ 树？
- 比 B 树：非叶子不存数据，单页存更多键，树更矮（IO 次数少）；叶子双向链表支持范围查询。
- 比红黑树：二叉、树高、IO 多；比 Hash：支持范围查询与排序。

### 7.【重点】聚簇/非聚簇索引？回表？覆盖索引？
- 聚簇索引叶子存整行数据（主键即聚簇索引，一表一个）；二级索引叶子存主键值。
- 回表：二级索引查到主键后回聚簇索引查整行，多一次 IO。
- 覆盖索引：查询列都在二级索引中无需回表（Extra=Using index）；索引下推（ICP）减少回表次数。

---

## 五、Spring 框架

### 1.【重点】Spring Bean 生命周期？
- 实例化（构造器）→ 属性填充（依赖注入）→ Aware 回调 → BeanPostProcessor 前置 → 初始化（afterPropertiesSet/@PostConstruct）→ BeanPostProcessor 后置（AOP 代理生成）→ 使用 → 销毁（destroy/@PreDestroy）。

### 2.【重点】循环依赖如何解决？三级缓存？
- 三级缓存：singletonObjects（成品）、earlySingletonObjects（早期引用）、singletonFactories（ObjectFactory 可生成代理）。
- 流程：A 创建→存工厂到三级→依赖 B→B 依赖 A→从三级拿 A 提前暴露→B 完成→A 完成。
- 为什么三级：AOP 下提前暴露的可能是代理，第三级工厂保证拿到最终代理；二级缓存保证单例唯一。
- 仅能解决单例 setter/字段注入；构造器注入循环依赖无法解决（可用 @Lazy）。

### 3.【重点】AOP 原理？JDK 与 CGLIB 区别？
- 基于动态代理：切面、切点、通知（前置/后置/环绕/异常/返回）。
- JDK：实现接口，Proxy + InvocationHandler；CGLIB：继承子类，ASM 字节码。
- Spring Boot 2.x 默认 CGLIB；final 类/方法无法被 CGLIB 代理。

### 4.【重点】事务传播机制？失效场景？
- 7 种：REQUIRED（默认）、REQUIRES_NEW、SUPPORTS、NOT_SUPPORTED、MANDATORY、NEVER、NESTED。
- 失效：方法非 public、自调用（this 不经过代理）、异常被 catch、rollbackFor 不匹配（默认只回滚 RuntimeException）、类未被 Spring 管理、引擎不支持事务。

### 5.【重点】Spring MVC 执行流程？
- DispatcherServlet → HandlerMapping 找 Handler → HandlerAdapter 调用 Controller → 返回 ModelAndView → ViewResolver 解析视图 → 渲染返回。
- 扩展：HandlerInterceptor 拦截器、@RestControllerAdvice 全局异常处理。

### 6.【重点】Spring Boot 自动配置原理？
- @SpringBootApplication = @SpringBootConfiguration + @EnableAutoConfiguration + @ComponentScan。
- @EnableAutoConfiguration 通过 @Import(AutoConfigurationImportSelector) 读取 spring.factories（3.x 为 AutoConfiguration.imports）加载配置类。
- @ConditionalOnClass/@ConditionalOnMissingBean 决定是否生效；自定义 starter 用 @Configuration + 配置类 + spring.factories。

---

## 六、Redis 缓存

### 1.【重点】持久化 RDB 与 AOF 区别？
- RDB：快照，fork 子进程生成 dump.rdb，恢复快、文件小，但两次快照间数据可能丢失。
- AOF：追加写命令日志，appendfsync（always/everysec/no），更完整（everysec 最多丢 1 秒），但文件大、恢复慢。
- 生产常用 RDB + AOF 混合（4.0 混合持久化）+ AOF 重写压缩。

### 2.【重点】过期删除策略？内存淘汰策略？
- 过期删除：惰性删除（访问时检查）+ 定期删除（定期随机抽样）。
- 淘汰（内存满）：noeviction（默认报错）、allkeys-lru、volatile-lru、allkeys-random、volatile-random、volatile-ttl、allkeys-lfu、volatile-lfu。
- LRU 是近似 LRU（随机采样）；LFU 按访问频率。

### 3.【重点】缓存穿透、击穿、雪崩？
- 穿透（查不存在的数据）：布隆过滤器、缓存空值。
- 击穿（热点 key 过期瞬间高并发）：互斥锁/逻辑过期、热点 key 不设过期。
- 雪崩（大量 key 同时过期/宕机）：过期时间加随机、多级缓存、集群高可用、限流降级。

### 4.【重点】Redis 分布式锁如何实现？
- `SET key value NX PX 毫秒`（原子）+ value 唯一标识（UUID）。
- 解锁用 Lua 脚本保证"判断 value + 删除"原子性，防误删。
- 续期用看门狗（Redisson 自动续期）；可重入用计数器/Redisson；主从切换丢锁可用 RedLock。

### 5.【重点】主从、哨兵、集群区别？
- 主从：一主多从，读写分离，异步复制可能不一致。
- 哨兵：监控 + 自动故障转移 + 通知，解决高可用（仍单主写）。
- Cluster：16384 槽位分片，多主多从横向扩展；key 用 CRC16%16384 定位槽；不支持跨槽事务。

### 6.【重点】缓存与数据库一致性？
- 旁路缓存（Cache Aside）：先更库再删缓存（或延迟双删），读未命中回填。
- 先更库再删缓存减少不一致窗口；最终一致用 binlog + 消息队列（Canal）异步同步。

---

## 七、消息队列

### 1.【重点】消息队列选型？
- RabbitMQ：功能全、低延迟、复杂路由，Erlang，吞吐量中等。
- RocketMQ：事务/延迟/顺序消息支持好，Java，吞吐量高。
- Kafka：超高通量、持久化强、分区有序，适合日志/流处理，延迟略高、无消息重试。

### 2.【重点】如何保证消息不丢失？
- 生产者：同步确认（ack）+ 重试；Broker：持久化刷盘 + 主从复制；消费者：手动 ack、处理完再提交 offset。
- 关键：不要自动 ack，先处理业务再提交。

### 3.【重点】如何保证消息不重复消费（幂等）？
- 至少一次投递必然可能重复，需消费端幂等：唯一业务 id 去重表、数据库唯一约束、Redis setnx、状态机。

### 4.【重点】如何保证消息顺序性？
- 局部有序：同一业务 key（订单 id）hash 到同一分区，单分区内有序，单消费者顺序消费。
- 全局有序：单分区单消费者（牺牲吞吐）。

### 5.【重点】消息堆积如何处理？
- 扩容消费者、提升消费速度（批量、异步）、临时多线程消费、降级丢弃/转存；定位慢消费（下游瓶颈、慢 SQL）。

---

## 八、微服务与分布式

### 1.【重点】CAP 与 BASE 理论？
- CAP：一致性（C）、可用性（A）、分区容错性（P）；分布式下 P 必选，CP 或 AP 二选一。
- BASE：基本可用 + 软状态 + 最终一致，是 AP 的实践。
- 举例：Zookeeper 偏 CP、Eureka 偏 AP、Nacos 可 AP/CP 切换。

### 2.【重点】服务注册与发现原理？注册中心对比？
- 服务启动注册到注册中心，消费者拉取/订阅服务列表，心跳续约，下线剔除。
- Eureka（AP、自我保护）、Zookeeper（CP、强一致）、Nacos（AP/CP 切换 + 配置中心）。

### 3.【重点】负载均衡算法？
- 轮询、加权轮询、随机、最少连接、一致性哈希（缓存/节点扩缩容稳定）、源地址哈希（会话保持）。

### 4.【重点】熔断、降级、限流？
- 熔断：失败率超阈值打开熔断器快速失败，一段时间后半开试探。
- 降级：非核心功能降级（返回兜底），保证核心链路。
- 限流：令牌桶（允许突发）、漏桶（匀速）、滑动窗口；工具 Sentinel/Hystrix。

### 5.【重点】分布式事务方案？
- 2PC（强一致、同步阻塞、单点）、3PC（引入超时）、TCC（Try-Confirm-Cancel，业务侵入）、SAGA（长事务补偿）、本地消息表 + 可靠消息最终一致（RocketMQ 事务消息）。
- 优先合理拆分服务避免分布式事务，最终一致优先。

### 6.【重点】分布式锁？Redis 与 Zookeeper 对比？
- Redis：setnx + Lua + 看门狗（Redisson），性能高但主从切换可能丢锁。
- Zookeeper：临时顺序节点 + watch，天然公平可重入、强一致，但性能较低。

### 7.【重点】分布式 ID 生成方案？
- UUID（无规律、索引差）、数据库自增（瓶颈）、号段模式（Leaf）、雪花算法（时间戳+机器 id+序列号，趋势递增，注意时钟回拨）、美团 Leaf/百度 UidGenerator。

---

## 九、设计模式

### 1.【基础巩固】设计模式六大原则？
- 单一职责、开闭（对扩展开放对修改关闭）、里氏替换（子类可替换父类）、依赖倒置（依赖抽象不依赖具体）、接口隔离、迪米特（最少知道）。

### 2.【重点】单例模式几种实现？
- 饿汉（类加载即创建，简单线程安全）、懒汉（延迟，需双重检查锁 + volatile）、静态内部类（延迟 + 线程安全，推荐）、枚举（防反射/序列化破坏，最安全）。

### 3.【重点】工厂模式？
- 简单工厂（一个工厂按参数创建产品）、工厂方法（每个产品一个工厂，符合开闭）、抽象工厂（产品族）。

### 4.【重点】代理模式？
- 静态代理（手动实现同接口）、动态代理（运行时生成，JDK/CGLIB）。
- 场景：日志、事务、权限、AOP、RPC。

### 5.【重点】策略、模板方法、观察者模式？
- 策略：算法可替换（支付方式），消除 if-else。
- 模板方法：父类定义骨架，子类实现步骤（JdbcTemplate）。
- 观察者：一对多依赖，状态变化通知（事件监听）。

### 6.【重点】装饰器模式与代理模式区别？
- 装饰器：增强功能（对客户端透明、可动态叠加职责），如 IO 流 BufferedInputStream。
- 代理：控制访问（非透明、通常不叠加），如 AOP。

---

## 十、网络与操作系统

### 1.【重点】HTTP 常见状态码？
- 2xx 成功（200/201/204）、3xx 重定向（301 永久、302 临时、304 缓存）、4xx 客户端错误（400/401 未认证/403 无权限/404）、5xx 服务端错误（500/502 网关/503 不可用/504 超时）。

### 2.【重点】HTTP 1.0 / 1.1 / 2.0 区别？
- 1.0：短连接，每次请求建连。
- 1.1：长连接（keep-alive）、管道化、Host 头、分块传输。
- 2.0：二进制分帧、多路复用（单连接并发）、头部压缩（HPACK）、服务器推送。

### 3.【基础巩固】GET 与 POST 区别？
- GET 幂等、可缓存、参数在 URL（长度受限、明文）；POST 非幂等、参数在 body（可传二进制、不限长）。
- 本质是语义差异；POST 参数不进 URL 日志、相对安全。

### 4.【重点】进程与线程区别？进程间通信方式？
- 进程：资源分配单位，独立地址空间；线程：CPU 调度单位，共享堆/全局变量，独立栈与 PC。
- 进程间通信：管道、消息队列、共享内存（最快）、信号量、信号、Socket。

### 5.【重点】BIO / NIO / AIO？
- BIO：阻塞同步，一连接一线程。
- NIO：非阻塞同步，Selector 多路复用 + Channel + Buffer，单线程管多连接。
- AIO：异步非阻塞，回调/完成通知；Netty 基于 NIO（Reactor 模型）。

### 6.【重点】死锁的四个条件？如何避免？
- 四条件：互斥、持有并等待、不可剥夺、循环等待。
- 预防：破坏任一条件（加锁顺序一致、一次性申请、超时释放）；避免：银行家算法；检测：jstack 查看锁等待。

---

## 附：中级岗位备考建议

1. **优先级**：集合与并发、JVM、数据库事务、Redis、Spring 是中级面试的绝对核心，务必吃透底层原理。
2. **答题套路**：每个知识点按"是什么 → 底层原理 → 为什么这样设计 → 项目中的应用/踩坑"来组织，避免只背结论。
3. **手写要求**：HashMap 扩容、线程池参数、单例模式、手写 SQL 与索引优化，中级面试常要求现场写。
4. **项目深挖**：准备好 1~2 个能讲清楚"遇到的性能/一致性问题 + 定位过程 + 解决方案"的项目案例。
