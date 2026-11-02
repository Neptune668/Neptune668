# Java 开发工程师面试题集（归纳整合版）

> 整合初级 / 中级 / 高级三份面试题笔记，按知识模块去重合并。
> **难度标签**：【初】0~2 年必备 ｜【中】2~5 年核心 ｜【高】5 年+ / 架构方向
> 每题给出精炼答题要点，覆盖"概念 → 底层原理 → 应用/踩坑"，供面试前快速过一遍。

---

## 一、Java 基础

### 1.【初】`==` 与 `equals()` 的区别？`hashCode()` 与 `equals()` 的关系？
- `==`：比较基本类型的值，或比较引用类型的地址。
- `equals()`：Object 默认比较地址，String、Integer 等重写后比较内容。
- 重写 equals 必须重写 hashCode，否则放入 HashMap/HashSet 时行为异常；equals 相等的对象 hashCode 必须相等。

### 2.【初】String、StringBuilder、StringBuffer 的区别？String 为什么不可变？
- String 不可变（final 修饰 + 内部 final 字节数组），每次拼接生成新对象。
- StringBuilder 可变、线程不安全、效率高；StringBuffer 可变、线程安全（方法加 synchronized）、效率低。
- 不可变好处：线程安全、可作 HashMap key、字符串常量池复用、防止篡改。

### 3.【初】面向对象三大特性？重载（Overload）与重写（Override）的区别？
- 封装（隐藏内部细节、对外提供接口）、继承（复用父类、扩展功能）、多态（同一方法多种实现，编译看左、运行看右）。
- 重载：同类中方法名相同、参数列表不同，编译期多态。
- 重写：子类重写父类方法，方法名/参数/返回类型一致，访问权限不能更小，运行期多态。

### 4.【初】final、finally、finalize 的区别？
- final：修饰类不可继承、方法不可重写、变量不可修改（引用不可变，内容可改）。
- finally：异常处理中必执行（`System.exit()` 除外），用于释放资源。
- finalize：Object 的方法，对象回收前调用，已废弃（Java 9 起不推荐使用）。

### 5.【初】8 种基本数据类型？装箱与拆箱？Integer 缓存机制？
- byte、short、int、long、float、double、char、boolean。
- 装箱：基本类型 → 包装类（`valueOf`）；拆箱：包装类 → 基本类型（`xxxValue`）。
- Integer 缓存 -128~127，`valueOf` 命中缓存返回同一对象，故 `Integer a=100` 时 `==` 为 true，超范围则为 false。

### 6.【初/中】接口与抽象类的区别？Java 8 接口的 default 方法？
- 抽象类：单继承，可有构造器、成员变量、普通方法，用于代码复用（is-a）。
- 接口：多实现，Java 8 后可有 default（带默认实现）和 static 方法，用于定义行为契约/能力（has-a）。
- default 方法：给接口新增方法而不破坏已有实现，避免实现类强制重写。
- 设计取舍：接口定义行为规范，抽象类提取公共实现。

### 7.【初】访问权限修饰符有哪些？
- public（所有类可访问）、protected（同包 + 子类）、default（同包）、private（本类）。

### 8.【中】深拷贝与浅拷贝的区别？如何实现深拷贝？
- 浅拷贝：只复制对象本身与基本类型字段值，引用类型字段仍指向同一对象（如 `Object.clone()` 默认、`Arrays.copyOf`）。
- 深拷贝：引用类型字段也复制出新对象，形成完全独立的对象图。
- 实现：重写 `clone()` 递归拷贝；序列化（`ObjectOutputStream` 写出再读入）；JSON 序列化（Jackson/Gson）。
- 注意：`clone()` 必须实现 `Cloneable` 接口，否则抛 `CloneNotSupportedException`；`BeanUtils.copyProperties` 是浅拷贝。

### 9.【中】Java 异常体系？受检异常与非受检异常？try-with-resources 原理？
- 体系：`Throwable` → `Error`（不可恢复：OOM、StackOverflow）+ `Exception` → `RuntimeException`（非受检）+ 其他（受检）。
- 受检异常编译期强制处理（IOException、SQLException）；非受检异常运行期抛出（NPE、ClassCastException）。
- try-with-resources：资源实现 `AutoCloseable`，编译后自动生成 `finally` 调用 `close()`，关闭顺序与声明相反，并保留异常抑制信息。

### 10.【中】反射原理与应用场景？JDK 动态代理与 CGLIB 区别？
- 反射：运行时获取 `Class` 对象，动态访问构造器/字段/方法，底层依赖 JVM 元数据（方法区/元空间）。
- 应用：Spring 依赖注入、MyBatis 结果映射、动态代理、注解处理。
- JDK 动态代理：基于接口，`Proxy` + `InvocationHandler`，只能代理实现了接口的类。
- CGLIB：基于继承生成子类，ASM 字节码，不能代理 `final` 类/方法；Spring Boot 2.x 后默认 CGLIB。

### 11.【中】泛型类型擦除？`? extends` 与 `? super`？
- 类型擦除：泛型仅编译期有效，编译后类型参数被擦除（有界→上界，无界→Object），运行时无泛型信息。
- 影响：不能 `new T()`、不能用泛型做 `instanceof`、泛型数组受限；编译器通过桥方法保证多态。
- `? extends T` 上界通配符：只能读不能写（Producer）；`? super T` 下界通配符：只能写不能读（Consumer），即 PECS 原则。

### 12.【中】Lambda 与 Stream 原理？Optional 用法？
- Lambda 是函数式接口的实例，编译期用 `invokedynamic` 生成，非匿名内部类（无 this 捕获问题）。
- Stream 惰性求值：中间操作（filter/map/sorted）惰性，终端操作（collect/reduce/forEach）触发；并行流底层 ForkJoinPool。
- Optional 防 NPE：`ofNullable`、`orElse`（立即求值）、`orElseGet`（惰性求值）、`map`、`flatMap`。

### 13.【高】Java 只有值传递，如何辨析"传引用"的误区？
- Java 方法参数传递永远是值传递：基本类型传"值的副本"，引用类型传"引用地址的副本"。
- 传入对象时，方法内修改对象属性会影响原对象（副本与原引用指向同一对象）；但重新赋值/`new` 只改副本，不影响原引用。
- 结论：Java 是 pass-by-value，不存在真正意义的引用传递（pass-by-reference）。

---

## 二、集合与并发

### 1.【初】ArrayList 与 LinkedList 的区别？ArrayList 扩容机制？
- ArrayList 底层是数组，查询快 O(1)、增删慢（需移动元素）；LinkedList 底层是双向链表，增删快、查询慢 O(n)。
- ArrayList 默认容量 10，满时扩容 1.5 倍，通过 `Arrays.copyOf` 复制到新数组。

### 2.【初】HashMap 底层原理？put/get 流程？为什么用红黑树？
- 结构：数组 + 链表 + 红黑树；put 先对 key 哈希定位桶，冲突用链表，链表超 8 转红黑树、小于 6 退回链表。
- 默认容量 16、负载因子 0.75，元素超阈值扩容 2 倍。
- 红黑树解决链表过长导致查询从 O(1) 退化为 O(n) 的问题。

### 3.【初】HashMap、Hashtable、ConcurrentHashMap 的区别？
- HashMap 线程不安全、key/value 允许 null。
- Hashtable 全表 synchronized、线程安全但性能差、不允许 null。
- ConcurrentHashMap 线程安全且高效（CAS + 单桶 synchronized 锁），并发场景推荐。

### 4.【初】List、Set、Map 的区别？
- List 有序可重复（ArrayList、LinkedList）；Set 无序不可重复（HashSet、TreeSet）；Map 键值对（HashMap、TreeMap）。

### 5.【中】HashMap 1.7 多线程死循环？ConcurrentHashMap 1.7 与 1.8 区别？
- 1.7 HashMap 扩容用头插法，并发 resize 可能形成环形链表导致 get 死循环；1.8 改尾插法解决。
- ConcurrentHashMap 1.7：`Segment` 分段锁（继承 ReentrantLock），默认 16 段，锁粒度粗。
- 1.8：CAS + synchronized 锁单个桶（链表头/红黑树根），粒度更细、并发更高，并引入红黑树（链表超 8 转树）。

### 6.【中】synchronized 原理？锁升级过程？
- 基于 Monitor，对象头 Mark Word 记录锁状态，方法/代码块编译为 `monitorenter/monitorexit`。
- 升级：无锁 → 偏向锁（同线程多次获取）→ 轻量级锁（CAS 自旋）→ 重量级锁（OS 互斥量，阻塞）。
- 竞争加剧逐级升级且不可降级；1.6 后经大量优化，性能已接近 Lock。

### 7.【中】volatile 原理？与 synchronized 区别？
- 保证可见性（写刷主存、读从主存，靠内存屏障 + MESI 缓存一致性）与有序性（禁止重排序），**不保证原子性**。
- synchronized 保证原子性 + 可见性 + 有序性，但阻塞、重量级。
- 经典应用：单例双重检查锁中 volatile 防止指令重排序返回半初始化对象。

### 8.【中】CAS 原理？ABA 问题？
- CAS（Compare And Swap）：比较内存值 V 与预期值 A，相等则更新为 B，否则自旋；底层 CPU 原子指令（cmpxchg）+ `Unsafe`。
- ABA：值 A→B→A，CAS 误判未变化；解决：加版本号（`AtomicStampedReference`）。
- 缺点：高竞争自旋开销大、只能保证单变量原子性。

### 9.【中】AQS 原理？ReentrantLock 与 synchronized 区别？
- AQS：FIFO 双向队列 + `volatile int state` + CAS 的同步框架；ReentrantLock、CountDownLatch、Semaphore 均基于它。
- ReentrantLock 优势：可中断、可超时、公平/非公平锁、多 Condition、可重入。
- synchronized 优势：JVM 优化后性能接近、自动释放、语义简单；两者均可重入。

### 10.【中】线程池核心参数？执行流程？拒绝策略？线程数如何设置？
- 7 参数：corePoolSize、maximumPoolSize、keepAliveTime、unit、workQueue、threadFactory、handler。
- 流程：先建核心线程 → 队列满则建到最大线程 → 全满走拒绝策略。
- 4 拒绝策略：AbortPolicy（抛异常，默认）、CallerRunsPolicy（调用者执行）、DiscardPolicy（丢弃）、DiscardOldestPolicy（丢最旧）。
- 线程数：CPU 密集型 = N+1；IO 密集型 = 2N 或 N×(1+等待/计算时间比)。

### 11.【中】ThreadLocal 原理？内存泄漏原因与预防？
- 每个 Thread 持有 ThreadLocalMap，key 是 ThreadLocal 弱引用，value 强引用。
- 泄漏：ThreadLocal 被 GC 后 key 变 null，但 value 仍被 Entry 强引用，线程池中线程不销毁则无法回收。
- 解决：用完调 `remove()`；ThreadLocalMap 在 get/set 时会惰性清理部分 null key。

### 12.【高】CountDownLatch、CyclicBarrier、Semaphore 的区别？
- CountDownLatch：一次性，一个/多个线程等待计数减到 0（countDown），不可复用。
- CyclicBarrier：可循环复用，一组线程互相等待到齐后一起执行（await）。
- Semaphore：信号量，控制同时访问资源的线程数（acquire/release），用于限流。
- 场景：CountDownLatch 等任务完成再汇总；CyclicBarrier 多线程分阶段协同；Semaphore 连接池/限流。

### 13.【高】阻塞队列原理？ArrayBlockingQueue 与 LinkedBlockingQueue 区别？
- 阻塞队列基于 ReentrantLock + Condition（notFull/notEmpty），满时 put 阻塞、空时 take 阻塞。
- ArrayBlockingQueue：有界数组、单把锁（读写共用）、可配公平锁。
- LinkedBlockingQueue：链表、可无界、两把锁（putLock/takeLock）分离读写、吞吐更高。
- 应用：线程池任务队列、生产者-消费者模型。

---

## 三、JVM

### 1.【初】JVM 内存区域划分？哪些线程私有、哪些共享？
- 线程私有：虚拟机栈（方法调用与局部变量）、本地方法栈、程序计数器。
- 线程共享：堆（存放对象实例）、方法区/元空间（类信息、常量、静态变量）。

### 2.【初】对象的创建过程？对象在内存中的布局？
- 创建：new → 类加载检查 → 分配内存 → 初始化零值 → 设置对象头 → 执行构造器（init）。
- 布局：对象头（Mark Word + 类型指针）、实例数据、对齐填充。

### 3.【中】如何判断对象死亡？GC Roots 有哪些？
- 引用计数法无法解决循环引用（Java 不用）；Java 用可达性分析。
- GC Roots：虚拟机栈本地变量表引用、方法区静态属性引用、常量池引用、JNI 引用、synchronized 持有的对象、JVM 内部引用（类加载器、Class 对象等）。

### 4.【中】垃圾回收算法？
- 标记-清除：有内存碎片。
- 复制：无碎片但浪费一半空间（新生代 Eden:Survivor=8:1:1，用复制思想）。
- 标记-整理：无碎片但移动开销大（老年代）。
- 分代：新生代（朝生夕死→复制）、老年代（存活率高→标记-整理/清除）。

### 5.【中】常见垃圾收集器？
- 新生代：Serial（单线程）、ParNew（多线程 Serial）、Parallel Scavenge（吞吐量优先）。
- 老年代：Serial Old、Parallel Old、CMS、G1。
- CMS（并发标记清除、低停顿）：初始标记→并发标记→重新标记→并发清除；缺点：碎片、浮动垃圾、对 CPU 敏感。
- G1：Region 分区 + 可回收性排序，可预测停顿；ZGC：着色指针 + 读屏障，亚毫秒停顿、可上 TB 堆。

### 6.【中】类加载过程？双亲委派模型？
- 过程：加载 → 验证 → 准备（静态变量赋默认值）→ 解析（符号引用→直接引用）→ 初始化（执行 clinit）。
- 双亲委派：请求先给父加载器，父无法加载才自己加载，保证核心类安全与唯一性。
- 打破场景：SPI（JDBC 线程上下文类加载器）、Tomcat 类加载隔离、热部署。

### 7.【中/高】线上 OOM / CPU 飙高如何排查？
- OOM：区分堆溢出（Java heap space）、栈溢出（StackOverflowError）、元空间溢出、直接内存溢出；加 `-XX:+HeapDumpOnOutOfMemoryError` 抓 dump → MAT/JProfiler 分析 Dominator Tree、GC Roots、大对象引用链。
- CPU 飙高：`top` 找进程 → `top -Hp <pid>` 找高 CPU 线程 → `printf '%x'` 转十六进制 → `jstack <pid> | grep -A 20 <nid>` 定位代码。
- 常见原因：死循环、频繁 GC、正则回溯、大量计算、锁竞争。

### 8.【高】G1 收集器原理？
- Region 分区（默认 2048 个，1~32M），逻辑分代、物理不分，可预测停顿模型。
- Young GC + Mixed GC；通过 RSet（Remembered Set）避免全堆扫描、SATB 快照保证并发标记正确性。
- 适合大堆、要求可预测停顿的场景；相比 CMS 无碎片。

### 9.【高】内存泄漏如何排查？常见场景？
- 多次 `jmap` 快照或 dump 对比，观察对象数量持续增长；`jstat` 观察 GC 后老年代仍高。
- 常见场景：静态集合持有对象、ThreadLocal 未 remove、连接/流未关闭、监听器未注销、内部类持有外部类。

---

## 四、数据库与事务

### 1.【初】MySQL 存储引擎？InnoDB 与 MyISAM 的区别？
- InnoDB：支持事务、行级锁、聚簇索引、外键，MySQL 5.5 后默认引擎。
- MyISAM：不支持事务、表级锁、查询快，现在已较少使用。

### 2.【初】索引有哪些类型？B+ 树索引原理？
- 主键、唯一、普通、联合、全文索引。
- B+ 树：非叶子节点只存键、叶子节点存数据且用链表有序连接，树矮、IO 少、支持范围查询。

### 3.【初】事务四大特性（ACID）？
- 原子性（要么全成功要么全失败）、一致性（数据始终满足约束）、隔离性（事务间互不干扰）、持久性（提交后永久保存）。

### 4.【初】内连接与外连接的区别？group by 与 having？
- 内连接只返回匹配行；左连接返回左表全部 + 右表匹配；右连接反之。
- group by 分组，having 对分组后结果过滤（where 在分组前）。

### 5.【中】事务隔离级别？脏读/不可重复读/幻读？
- 读未提交（脏读）、读已提交（不可重复读）、可重复读（幻读，MySQL 默认）、串行化。
- 脏读：读到未提交数据；不可重复读：两次读结果不同（update）；幻读：两次查询行数不同（insert/delete）。
- InnoDB 在可重复读下通过 MVCC + 间隙锁基本解决幻读。

### 6.【中】MVCC 原理？
- 通过 undo log + ReadView 实现多版本，读写不阻塞。
- 每行隐藏列：DB_TRX_ID（最后修改事务）、DB_ROLL_PTR（undo log 回滚指针）。
- 可重复读在事务第一次读时创建 ReadView，读已提交每次读都新建；快照读走 MVCC，当前读（FOR UPDATE）走锁。

### 7.【中】InnoDB 锁机制？间隙锁、临键锁？
- 行锁（锁索引记录）、间隙锁（锁记录间空隙，防插入）、临键锁（= 行锁 + 间隙锁，左开右闭，默认）。
- 可重复读下靠间隙锁 + 临键锁解决幻读；加锁针对索引，未命中索引退化为表锁。

### 8.【中】最左前缀原则？索引失效场景？
- 联合索引按最左匹配：查询从最左列开始且不跳过中间列才走索引（a,b,c → where a / a,b / a,b,c）。
- 失效：对索引列做函数/计算、隐式类型转换、`like '%xx'`、or 含非索引列、`!=`/`not in`、跳过联合索引最左列。

### 9.【中】Explain 各字段含义？
- type（访问类型，优→劣：const > eq_ref > ref > range > index > all，目标到 ref/range）。
- key（实际用到的索引）、rows（预估扫描行数）。
- Extra：Using index（覆盖索引）、Using filesort（需优化排序）、Using temporary（临时表）、Using where。

### 10.【中】索引为什么用 B+ 树？
- 比 B 树：非叶子不存数据，单页存更多键，树更矮（IO 次数少）；叶子双向链表支持范围查询。
- 比红黑树：二叉、树高、IO 多；比 Hash：支持范围查询与排序。

### 11.【中】聚簇/非聚簇索引？回表？覆盖索引？
- 聚簇索引叶子存整行数据（主键即聚簇索引，一表一个）；二级索引叶子存主键值。
- 回表：二级索引查到主键后回聚簇索引查整行，多一次 IO。
- 覆盖索引：查询列都在二级索引中无需回表（Extra=Using index）；索引下推（ICP）减少回表次数。

### 12.【高】分库分表如何设计？
- 垂直拆分（按业务/字段拆库表）解决单库压力与耦合；水平拆分（按分片键路由）解决单表数据量。
- 关键：分片键选择、路由算法（哈希/范围）、全局唯一 ID、跨库 join 与分布式事务、数据迁移与平滑扩容（一致性哈希/双倍扩容）。

### 13.【高】主从复制原理？读写分离如何保证一致性？
- 主库写 binlog，从库 IO 线程拉取写 relay log，SQL 线程重放；异步/半同步复制。
- 读写分离提升读吞吐但存在延迟；一致性方案：敏感操作强制走主库、半同步复制、并行复制、GTID。

### 14.【高】大表如何优化？慢查询如何治理？
- 慢查询定位：slow_query_log + mysqldumpslow + Explain。
- 优化：加/调索引、避免 select *、深分页优化（延迟关联/游标）、归档冷数据、分库分表。

### 15.【高】数据库死锁如何排查与避免？
- 死锁典型：两事务交叉加锁；用 `SHOW ENGINE INNODB STATUS` 查看 LATEST DETECTED DEADLOCK。
- 避免：固定加锁顺序、事务尽量短、降低隔离级别、加索引缩小锁范围。

---

## 五、Spring 框架

### 1.【初】Spring 是什么？对 IoC 与 AOP 的理解？
- IoC（控制反转）：对象创建与依赖注入交给容器（DI），降低耦合。
- AOP（面向切面）：横向抽取公共逻辑（日志、事务、权限）织入业务，减少重复代码。

### 2.【初】Spring 常用注解？@Autowired 与 @Resource 的区别？
- @Component/@Service/@Controller/@Repository、@Autowired、@Value、@Configuration、@Bean 等。
- @Autowired 按类型注入（Spring）；@Resource 先按名称再按类型（JSR-250）。

### 3.【初】Spring Bean 的作用域？
- singleton（默认，单例）、prototype（多例）、request（一次请求）、session（一个会话）、application。

### 4.【初】@RestController 与 @Controller 的区别？
- @Controller 返回视图名（配合视图解析器）；@RestController = @Controller + @ResponseBody，直接返回 JSON 数据。

### 5.【中】Spring Bean 生命周期？
- 实例化（构造器）→ 属性填充（依赖注入）→ Aware 回调 → BeanPostProcessor 前置 → 初始化（afterPropertiesSet/@PostConstruct）→ BeanPostProcessor 后置（AOP 代理生成）→ 使用 → 销毁（destroy/@PreDestroy）。

### 6.【中】循环依赖如何解决？三级缓存？
- 三级缓存：singletonObjects（成品）、earlySingletonObjects（早期引用）、singletonFactories（ObjectFactory 可生成代理）。
- 流程：A 创建→存工厂到三级→依赖 B→B 依赖 A→从三级拿 A 提前暴露→B 完成→A 完成。
- 为什么三级：AOP 下提前暴露的可能是代理，第三级工厂保证拿到最终代理；二级缓存保证单例唯一。
- 仅能解决单例 setter/字段注入；构造器注入循环依赖无法解决（可用 @Lazy）。

### 7.【中】AOP 原理？JDK 与 CGLIB 区别？
- 基于动态代理：切面、切点、通知（前置/后置/环绕/异常/返回）。
- JDK：实现接口，Proxy + InvocationHandler；CGLIB：继承子类，ASM 字节码。
- Spring Boot 2.x 默认 CGLIB；final 类/方法无法被 CGLIB 代理。

### 8.【中/高】事务传播机制？失效场景？
- 7 种传播：REQUIRED（默认）、REQUIRES_NEW、SUPPORTS、NOT_SUPPORTED、MANDATORY、NEVER、NESTED。
- 失效：方法非 public、自调用（this 不经过代理）、异常被 catch 吞掉、rollbackFor 不匹配（默认只回滚 RuntimeException）、类未被 Spring 管理、数据库引擎不支持事务、多线程调用（不同线程不同连接）、传播类型 NOT_SUPPORTED。

### 9.【中】Spring MVC 执行流程？
- DispatcherServlet → HandlerMapping 找 Handler → HandlerAdapter 调用 Controller → 返回 ModelAndView → ViewResolver 解析视图 → 渲染返回。
- 扩展：HandlerInterceptor 拦截器、@RestControllerAdvice 全局异常处理。

### 10.【中】Spring Boot 自动配置原理？
- @SpringBootApplication = @SpringBootConfiguration + @EnableAutoConfiguration + @ComponentScan。
- @EnableAutoConfiguration 通过 @Import(AutoConfigurationImportSelector) 读取 spring.factories（3.x 为 AutoConfiguration.imports）加载配置类。
- @ConditionalOnClass/@ConditionalOnMissingBean 决定是否生效；自定义 starter 用 @Configuration + 配置类 + spring.factories。

### 11.【高】Spring 框架用到了哪些设计模式？
- 工厂（BeanFactory）、单例（Bean 默认）、代理（AOP）、模板方法（JdbcTemplate/RestTemplate）、观察者（事件机制）、适配器（HandlerAdapter）、策略（Resource 加载）、装饰器（BeanWrapper）。

### 12.【高】Spring Boot 启动流程？
- new SpringApplication → 推断应用类型 → 加载 ApplicationContextInitializer/Listener → refresh()（IoC 初始化）→ 加载自动配置 → 启动 Web 服务器 → 发布 started/ready 事件。

---

## 六、Redis 缓存

### 1.【初】Redis 常见数据类型及应用场景？
- String（缓存、计数器）、Hash（对象存储）、List（消息队列）、Set（去重、共同好友）、ZSet（排行榜）。

### 2.【初】Redis 为什么快？
- 基于内存、单线程模型避免锁竞争与上下文切换、IO 多路复用、高效的数据结构。

### 3.【中】持久化 RDB 与 AOF 区别？
- RDB：快照，fork 子进程生成 dump.rdb，恢复快、文件小，但两次快照间数据可能丢失。
- AOF：追加写命令日志，appendfsync（always/everysec/no），更完整（everysec 最多丢 1 秒），但文件大、恢复慢。
- 生产常用 RDB + AOF 混合（4.0 混合持久化）+ AOF 重写压缩。

### 4.【中】过期删除策略？内存淘汰策略？
- 过期删除：惰性删除（访问时检查）+ 定期删除（定期随机抽样）。
- 淘汰（内存满）：noeviction（默认报错）、allkeys-lru、volatile-lru、allkeys-random、volatile-random、volatile-ttl、allkeys-lfu、volatile-lfu。
- LRU 是近似 LRU（随机采样）；LFU 按访问频率。

### 5.【中】缓存穿透、击穿、雪崩？
- 穿透（查不存在的数据）：布隆过滤器、缓存空值。
- 击穿（热点 key 过期瞬间高并发）：互斥锁/逻辑过期、热点 key 不设过期。
- 雪崩（大量 key 同时过期/宕机）：过期时间加随机、多级缓存、集群高可用、限流降级。

### 6.【中】Redis 分布式锁如何实现？
- `SET key value NX PX 毫秒`（原子）+ value 唯一标识（UUID）。
- 解锁用 Lua 脚本保证"判断 value + 删除"原子性，防误删。
- 续期用看门狗（Redisson 自动续期）；可重入用计数器/Redisson；主从切换丢锁可用 RedLock。

### 7.【中/高】主从、哨兵、集群（Cluster）区别？Cluster 原理？
- 主从：一主多从，读写分离，异步复制可能不一致。
- 哨兵：监控 + 自动故障转移 + 通知，解决高可用（仍单主写）。
- Cluster：16384 槽位分片，key 通过 CRC16%16384 定位槽；每个节点负责部分槽，master 带副本，多主多从横向扩展。
- 故障检测（Gossip 协议）、故障转移（选举新 master）；客户端 MOVED/ASK 重定向；不支持跨槽事务，批量操作需同槽（hash tag）。

### 8.【中】缓存与数据库一致性？
- 旁路缓存（Cache Aside）：先更库再删缓存（或延迟双删），读未命中回填。
- 先更库再删缓存减少不一致窗口；最终一致用 binlog + 消息队列（Canal）异步同步。

### 9.【高】大 Key、热 Key 问题如何发现与处理？
- 大 Key：单个 key 过大导致阻塞与带宽问题；用 `redis-cli --bigkeys`、`MEMORY USAGE` 排查；拆分/压缩。
- 热 Key：热点集中单节点；多级缓存、本地缓存、读写分离、key 拆分（复制多份分散压力）。

### 10.【高】Redis 6.0 引入多线程的动机？
- 6.0 引入 IO 多线程（默认关闭），只负责网络读写与解析，命令执行仍单线程。
- 动机：网络 IO 成为瓶颈，多线程提升读写吞吐；命令单线程保证原子性。

### 11.【高】Redis 与 Memcached 的区别？
- Redis：数据类型丰富、支持持久化、集群、发布订阅、事务/Lua 脚本。
- Memcached：只支持字符串、纯内存不持久化、多线程；简单缓存高性能场景可用。

---

## 七、消息队列

### 1.【初】为什么使用消息队列？三大应用场景？
- 异步（提升响应速度）、解耦（系统间不直接依赖）、削峰（缓冲流量高峰、保护下游）。

### 2.【中】消息队列选型？
- RabbitMQ：功能全、低延迟、复杂路由，Erlang，吞吐量中等。
- RocketMQ：事务/延迟/顺序消息支持好，Java，吞吐量高。
- Kafka：超高通量、持久化强、分区有序，适合日志/流处理，延迟略高、无消息重试。

### 3.【中】如何保证消息不丢失？
- 生产者：同步确认（ack）+ 重试；Broker：持久化刷盘 + 主从复制；消费者：手动 ack、处理完再提交 offset。
- 关键：不要自动 ack，先处理业务再提交。

### 4.【中】如何保证消息不重复消费（幂等）？
- 至少一次投递必然可能重复，需消费端幂等：唯一业务 id 去重表、数据库唯一约束、Redis setnx、状态机。

### 5.【中】如何保证消息顺序性？
- 局部有序：同一业务 key（订单 id）hash 到同一分区，单分区内有序，单消费者顺序消费。
- 全局有序：单分区单消费者（牺牲吞吐）。

### 6.【中】消息堆积如何处理？
- 扩容消费者、提升消费速度（批量、异步）、临时多线程消费、降级丢弃/转存；定位慢消费（下游瓶颈、慢 SQL）。

### 7.【高】Kafka 架构原理？
- 分区（Partition）、副本（Replica）、ISR、Leader/Follower、Controller、高水位（HW/LEO）。
- 顺序写 + 页缓存 + 零拷贝实现高吞吐；消费组 + offset 管理。

### 8.【高】RocketMQ 架构？事务消息、延迟消息原理？
- NameServer（路由）、Broker（存储）、Producer/Consumer；CommitLog + ConsumeQueue 存储结构。
- 事务消息：半消息（half message）→ 本地事务 → commit/rollback + 定时回查。
- 延迟消息：先投递到延迟队列，定时调度到期后投递真实队列。

### 9.【高】如何设计一个消息队列？
- 存储（顺序写、分段文件）、通信（Netty）、高可用（副本同步）、消费（offset/ack）、路由（topic/分区）、可靠性（刷盘/复制）。

---

## 八、微服务与分布式

### 1.【初】什么是微服务？优缺点？
- 按业务将单体拆分为多个独立小服务，独立开发、部署、扩展。
- 优点：独立扩展、技术栈灵活、故障隔离；缺点：系统复杂、分布式事务与一致性难、运维成本高。

### 2.【中】CAP 与 BASE 理论？
- CAP：一致性（C）、可用性（A）、分区容错性（P）；分布式下 P 必选，CP 或 AP 二选一。
- BASE：基本可用 + 软状态 + 最终一致，是 AP 的实践。
- 举例：Zookeeper 偏 CP、Eureka 偏 AP、Nacos 可 AP/CP 切换。

### 3.【中】服务注册与发现原理？注册中心对比？
- 服务启动注册到注册中心，消费者拉取/订阅服务列表，心跳续约，下线剔除。
- Eureka（AP、自我保护）、Zookeeper（CP、强一致）、Nacos（AP/CP 切换 + 配置中心）。

### 4.【中】负载均衡算法？
- 轮询、加权轮询、随机、最少连接、一致性哈希（缓存/节点扩缩容稳定）、源地址哈希（会话保持）。

### 5.【中】熔断、降级、限流？
- 熔断：失败率超阈值打开熔断器快速失败，一段时间后半开试探。
- 降级：非核心功能降级（返回兜底），保证核心链路。
- 限流：令牌桶（允许突发）、漏桶（匀速）、滑动窗口；工具 Sentinel/Hystrix。

### 6.【中】分布式事务方案？
- 2PC（强一致、同步阻塞、单点）、3PC（引入超时）、TCC（Try-Confirm-Cancel，业务侵入）、SAGA（长事务补偿）、本地消息表 + 可靠消息最终一致（RocketMQ 事务消息）。
- 优先合理拆分服务避免分布式事务，最终一致优先。

### 7.【中】分布式锁？Redis 与 Zookeeper 对比？
- Redis：setnx + Lua + 看门狗（Redisson），性能高但主从切换可能丢锁。
- Zookeeper：临时顺序节点 + watch，天然公平可重入、强一致，但性能较低。

### 8.【中】分布式 ID 生成方案？
- UUID（无规律、索引差）、数据库自增（瓶颈）、号段模式（Leaf）、雪花算法（时间戳+机器 id+序列号，趋势递增，注意时钟回拨）、美团 Leaf/百度 UidGenerator。

### 9.【高】服务拆分的原则与边界？
- 单一职责、高内聚低耦合、按业务域（DDD 限界上下文）、数据自治（避免跨库 join）、考虑团队边界。
- 避免过度拆分（分布式事务、链路复杂、运维成本）。

### 10.【高】Raft 与 Paxos 的核心思想？
- Paxos：基于多数派的一致性算法，难理解难实现。
- Raft：更易理解，领导者选举 + 日志复制 + 安全性；Leader 接收写请求复制到多数派后提交；Term 任期 + 心跳机制。

### 11.【高】网关原理？限流算法？
- 网关：统一入口，负责路由、鉴权、限流、熔断、日志；Spring Cloud Gateway（WebFlux 非阻塞）。
- 限流算法：固定窗口（临界问题）、滑动窗口（精确但存储开销）、漏桶（匀速）、令牌桶（允许突发）。

### 12.【高】如何设计接口幂等性？
- 幂等：多次请求结果一致；方案：唯一请求 id（去重表）、数据库唯一约束、乐观锁（版本号）、状态机、token 机制。

---

## 九、设计模式

### 1.【初/中】设计模式六大原则？
- 单一职责、开闭（对扩展开放、对修改关闭）、里氏替换（子类可替换父类）、依赖倒置（依赖抽象不依赖具体）、接口隔离、迪米特（最少知道）。

### 2.【初/中/高】单例模式几种实现方式？如何防反射、序列化破坏？
- 饿汉（类加载即创建，简单线程安全）、懒汉（延迟，需双重检查锁 + volatile）、静态内部类（延迟 + 线程安全，推荐）、枚举（防反射/序列化破坏，最安全）。
- 反射可破坏（setAccessible 调私有构造）；序列化反序列化会生成新实例；枚举单例天然防反射/序列化破坏。

### 3.【中】工厂模式？
- 简单工厂（一个工厂按参数创建产品）、工厂方法（每个产品一个工厂，符合开闭）、抽象工厂（产品族）。

### 4.【中】代理模式？
- 静态代理（手动实现同接口）、动态代理（运行时生成，JDK/CGLIB）。
- 场景：日志、事务、权限、AOP、RPC。

### 5.【中】策略、模板方法、观察者模式？
- 策略：算法可替换（支付方式），消除 if-else。
- 模板方法：父类定义骨架，子类实现步骤（JdbcTemplate）。
- 观察者：一对多依赖，状态变化通知（事件监听）。

### 6.【中】装饰器模式与代理模式区别？
- 装饰器：增强功能（对客户端透明、可动态叠加职责），如 IO 流 BufferedInputStream。
- 代理：控制访问（非透明、通常不叠加），如 AOP。

### 7.【高】观察者模式与发布-订阅模式的区别？
- 观察者：观察者直接注册到主题，主题直接通知，耦合较紧。
- 发布-订阅：中间增加事件总线/Broker，发布者与订阅者完全解耦。

### 8.【高】责任链模式在框架中的应用？
- Servlet Filter 链、Spring Interceptor、网关过滤器、审批流。
- 好处：解耦、动态组合、灵活增删处理节点。

---

## 十、网络与操作系统

### 1.【初】OSI 七层模型与 TCP/IP 四层模型？
- OSI：物理、数据链路、网络、传输、会话、表示、应用。
- TCP/IP：网络接口、网络（IP）、传输（TCP/UDP）、应用（HTTP/DNS/FTP）。

### 2.【初】TCP 与 UDP 的区别？三次握手、四次挥手？
- TCP 面向连接、可靠、有序、字节流；UDP 无连接、不可靠、快、面向报文。
- 三次握手：SYN → SYN+ACK → ACK，确认双方收发能力；四次挥手断开连接。

### 3.【初】HTTP 与 HTTPS 的区别？HTTPS 加密过程？
- HTTP 明文传输；HTTPS = HTTP + SSL/TLS，默认端口 443。
- 加密：非对称加密交换密钥 + 对称加密传输数据 + CA 证书验证身份。

### 4.【中】HTTP 常见状态码？
- 2xx 成功（200/201/204）、3xx 重定向（301 永久、302 临时、304 缓存）、4xx 客户端错误（400/401 未认证/403 无权限/404）、5xx 服务端错误（500/502 网关/503 不可用/504 超时）。

### 5.【中】HTTP 1.0 / 1.1 / 2.0 区别？
- 1.0：短连接，每次请求建连。
- 1.1：长连接（keep-alive）、管道化、Host 头、分块传输。
- 2.0：二进制分帧、多路复用（单连接并发）、头部压缩（HPACK）、服务器推送。

### 6.【中】GET 与 POST 区别？
- GET 幂等、可缓存、参数在 URL（长度受限、明文）；POST 非幂等、参数在 body（可传二进制、不限长）。
- 本质是语义差异；POST 参数不进 URL 日志、相对安全。

### 7.【中】进程与线程区别？进程间通信方式？
- 进程：资源分配单位，独立地址空间；线程：CPU 调度单位，共享堆/全局变量，独立栈与 PC。
- 进程间通信：管道、消息队列、共享内存（最快）、信号量、信号、Socket。

### 8.【中】BIO / NIO / AIO？
- BIO：阻塞同步，一连接一线程。
- NIO：非阻塞同步，Selector 多路复用 + Channel + Buffer，单线程管多连接。
- AIO：异步非阻塞，回调/完成通知；Netty 基于 NIO（Reactor 模型）。

### 9.【中】死锁的四个条件？如何避免？
- 四条件：互斥、持有并等待、不可剥夺、循环等待。
- 预防：破坏任一条件（加锁顺序一致、一次性申请、超时释放）；避免：银行家算法；检测：jstack 查看锁等待。

### 10.【高】TCP 为什么三次握手、四次挥手？TIME_WAIT 作用？
- 三次握手：同步初始序列号、避免历史连接、双方确认收发能力；两次不安全、四次冗余。
- 四次挥手：TCP 全双工，两端独立关闭；TIME_WAIT 主动关闭方等待 2MSL，确保最后 ACK 到达、让旧连接报文消散。
- 大量 TIME_WAIT 优化：内核参数复用、减少短连接。

### 11.【高】select、poll、epoll 的区别？
- select：fd 数组，O(n) 遍历，fd 上限 1024，每次拷贝到内核。
- poll：链表无上限，仍 O(n) 遍历。
- epoll：事件驱动，红黑树 + 就绪链表，O(1) 获取就绪事件，无 fd 上限，LT/ET 模式；ET 需非阻塞 + 一次性读完。

### 12.【高】零拷贝原理？
- 传统 4 次拷贝（用户态/内核态来回）+ 多次上下文切换；mmap + sendfile 减少拷贝；sendfile + DMA 实现 2 次拷贝（内核态直接到网卡）。
- 应用：Kafka、文件传输、静态资源服务。

### 13.【高】浏览器输入 URL 到页面展示的完整过程？
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

## 附：分阶段备考建议

**初级（0~2 年）**
1. 基础为王：Java 基础语法、集合、SQL、HTTP 是绝对核心，务必熟练到秒答。
2. 动手写代码：准备好手写常见算法（排序、字符串处理）、手写单例、手写简单 SQL。
3. 项目讲清楚：能清晰描述 1 个自己参与的项目（技术栈、负责模块、遇到的问题及解决）。
4. 原理点到为止：JVM、并发、分布式原理能讲清基本概念和关键区别即可，答出原理是加分项。

**中级（2~5 年）**
1. 优先级：集合与并发、JVM、数据库事务、Redis、Spring 是绝对核心，务必吃透底层原理。
2. 答题套路：按"是什么 → 底层原理 → 为什么这样设计 → 项目中的应用/踩坑"组织，避免只背结论。
3. 手写要求：HashMap 扩容、线程池参数、单例模式、手写 SQL 与索引优化，常要求现场写。
4. 项目深挖：准备好 1~2 个能讲清楚"性能/一致性问题 + 定位过程 + 解决方案"的项目案例。

**高级（5 年+ / 架构方向）**
1. 深度优先：JVM、并发、分布式一致性、分库分表、Kafka/RocketMQ 架构是分水岭，要能讲到底层实现。
2. 结合踩坑经验：准备 2~3 个真实生产故障案例（OOM、CPU 飙高、死锁、消息堆积、缓存雪崩），讲清"现象 → 定位 → 方案 → 复盘"。
3. 准备系统设计题：秒杀、短链接、限流、ID 生成是高频设计题，要能画出架构图并说明取舍。
4. 表达架构思维：从"可用性、性能、一致性、扩展性"多维度权衡，体现全局视角。
