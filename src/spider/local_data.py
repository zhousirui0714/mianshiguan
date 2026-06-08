"""
本地题库数据 — 来自已知开源仓库的预整理面试题

数据来源：
- Snailclimb/JavaGuide (14w+ Star) — Java 面试指南
- CyC2018/CS-Notes (18w+ Star) — 计算机基础
- youngyangyang04/leetcode-master — 代码随想录算法题

结构: [{repo, default_cat, content: markdown}, ...]
"""

SOURCES_LOCAL = [
    # ============ JavaGuide — Java 基础 ============
    {
        "repo": "Snailclimb/JavaGuide",
        "file_path": "docs/java/basis/Java基础知识.md",
        "default_cat": "Java",
        "content": r"""
## Q: 什么是 Java 虚拟机？为什么 Java 被称作"平台无关的编程语言"？
Java 虚拟机（JVM）是运行 Java 字节码的虚拟机。Java 源码被编译成字节码，JVM 将字节码解释/编译为机器码。
"一次编写，到处运行"的核心就是 JVM。不同平台有不同 JVM 实现，但字节码是统一的。

## Q: JDK 和 JRE 的区别是什么？
JDK（Java Development Kit）是功能齐全的 Java SDK，包含 JRE 和开发工具（javac、jdb 等）。
JRE（Java Runtime Environment）是 Java 运行时环境，包含 JVM 和核心类库。
如果只是运行 Java 程序，只需要 JRE；如果要开发 Java 程序，需要 JDK。

## Q: Java 有哪些基本数据类型？
byte（1字节）、short（2字节）、int（4字节）、long（8字节）、float（4字节）、double（8字节）、boolean（未明确大小）、char（2字节）。

## Q: 访问修饰符 public、private、protected 以及默认的区别？
public：任何地方可见。protected：同一包内 + 子类可见。default：同一包内可见。private：仅同一类可见。

## Q: 重载和重写的区别？
重载（Overload）：同一类中方法名相同、参数列表不同，编译时多态。
重写（Override）：子类重写父类方法，运行时多态。方法签名必须相同，访问权限不能更低，返回值类型可以是协变的。

## Q: 抽象类和接口的区别？
JDK8 之前：接口只能有抽象方法，抽象类可以有抽象方法和具体方法。
JDK8+：接口可以有 default 和 static 方法。
JDK9+：接口可以有 private 方法。
核心区别：抽象类表示 is-a 关系，接口表示 has-a / can-do 能力。一个类只能继承一个抽象类但可以实现多个接口。

## Q: String、StringBuffer、StringBuilder 的区别？
String 不可变（final），每次修改创建新对象。StringBuffer 可变、线程安全（synchronized）。StringBuilder 可变、线程不安全但性能最好。单线程用 StringBuilder，多线程用 StringBuffer。

## Q: == 和 equals() 的区别？
== 比较基本类型时比值，比较引用类型时比内存地址。
equals() 是 Object 类的方法，默认也是比地址，但 String、Integer 等类重写了它来比较内容。

## Q: final 关键字的作用？
final 修饰类：不能被继承。修饰方法：不能被重写。修饰变量：变为常量（基本类型值不变，引用类型引用不变）。

## Q: 异常处理机制？checked 和 unchecked 异常的区别？
Throwable 下分 Error（不可恢复，如 OutOfMemoryError）和 Exception（可恢复）。
Exception 分 Checked Exception（必须 catch 或 throws，如 IOException）和 Unchecked Exception/RuntimeException（可选处理，如 NullPointerException）。

## Q: 什么是泛型？类型擦除是什么？
泛型提供编译时类型安全检查。类型擦除（Type Erasure）：编译时移除泛型信息，运行时 List<Integer> 和 List<String> 都是 List。
桥接方法用于保持多态。可以通过反射在运行时获取类型参数（通过 super type token 模式）。

## Q: 反射的原理和用途？
反射允许程序在运行时检查/修改类和对象的状态和行为。核心类：Class、Method、Field、Constructor。
用途：框架（Spring IOC 依赖注入）、ORM（MyBatis 映射）、动态代理。性能较直接调用慢（有缓存可缓解）。

## Q: 什么是序列化？什么是 transient？
序列化：将对象转成字节流以便存储或传输。Java 通过实现 Serializable 接口（标记接口）来实现。
transient：修饰的字段不参与序列化。常用于密码、敏感信息、或可推导的缓存字段。
serialVersionUID：用于版本控制，反序列化时校验一致性。

## Q: 深拷贝和浅拷贝的区别？
浅拷贝：复制基本类型字段和引用地址（新旧对象共享引用对象）。Object.clone() 默认浅拷贝。
深拷贝：完全复制所有字段和引用对象。方式：重写 clone() + 手动复制引用对象、序列化反序列化、构造器复制。

## Q: Java 中的代理模式？静态代理和动态代理的区别？
静态代理：手动编写代理类，编译时确定。动态代理：运行时生成代理类。
JDK 动态代理：基于接口，Proxy + InvocationHandler。CGLIB 动态代理：基于继承（ASM 字节码生成），可代理没有接口的类。
Spring AOP 默认：单例用 CGLIB，有接口用 JDK 动态代理。
""",
        "scenario": "job_interview",
    },
    {
        "repo": "Snailclimb/JavaGuide",
        "file_path": "docs/java/concurrent/Java并发编程.md",
        "default_cat": "Java",
        "content": r"""
## Q: 线程的创建方式有哪些？
1. 继承 Thread 类 2. 实现 Runnable 接口 3. 实现 Callable 接口（有返回值） 4. 线程池（ExecutorService）。
推荐方式：Runnable/Callable（避免单继承限制）+ 线程池（减少创建开销）。

## Q: 线程有哪些状态？状态转换是怎样的？
NEW（新建）→ RUNNABLE（可运行）→ BLOCKED（阻塞）/ WAITING（等待）/ TIMED_WAITING（超时等待）→ TERMINATED（终止）。
Thread.sleep() 进入 TIMED_WAITING；Object.wait() 进入 WAITING；synchronized 获取锁失败进入 BLOCKED。

## Q: synchronized 关键字的底层实现原理？
synchronized 基于 Monitor 对象。Java6 后引入锁升级：偏向锁（一个线程）→ 轻量级锁（CAS 自旋）→ 重量级锁（OS 互斥量）。
偏向锁在 JDK15 默认关闭。锁只能升级不能降级。

## Q: volatile 关键字的作用？
1. 保证可见性：写 volatile 变量立即同步到主存，读从主存取。2. 禁止指令重排序（内存屏障）。
不能保证原子性（i++ 不是原子操作）。

## Q: ThreadLocal 的原理？内存泄漏原因？
每个线程有 ThreadLocalMap（Entry<ThreadLocal, value>）。ThreadLocal key 是弱引用。
内存泄漏：key 被 GC 回收后 value 仍有强引用。解决：用完调用 remove()。

## Q: 线程池的核心参数有哪些？
corePoolSize（核心线程数）→ maxPoolSize（最大线程数）→ keepAliveTime（空闲存活时间）→ workQueue（任务队列）→ threadFactory（线程工厂）→ handler（拒绝策略）。

## Q: 线程池的任务提交和执行流程？
1. 线程数 < corePoolSize → 创建新线程执行。2. 线程数 ≥ corePoolSize → 入队列。3. 队列满且线程数 < maxPoolSize → 创建新线程。4. 队列满且达 maxPoolSize → 执行拒绝策略。

## Q: AQS（AbstractQueuedSynchronizer）原理？
AQS 是 JUC 锁和同步器的基石。核心：volatile int state + CLH 变体等待队列。
ReentrantLock、Semaphore、CountDownLatch 等都基于 AQS。独占/共享两种模式。

## Q: ReentrantLock 和 synchronized 的区别？
ReentrantLock：可中断、可超时、可尝试获取（tryLock）、公平/非公平、支持多个 Condition。
synchronized：自动释放、Java 内置、jstack 可看到锁信息。
性能差距已不大（synchronized 已优化）。

## Q: ConcurrentHashMap 的实现原理？
JDK7：Segment（ReentrantLock 分段锁）。JDK8：CAS + synchronized（锁链表头节点）。
JDK8 优势：锁粒度更细、并发度更高。扩容采用多线程协助迁移。

## Q: CountDownLatch 和 CyclicBarrier 的区别？
CountDownLatch：一个线程等 N 个线程完成，不可重用。CyclicBarrier：N 个线程互相等待到齐，可重用（reset()）。

## Q: 什么是 CAS？ABA 问题如何解决？
CAS（Compare And Swap）：硬件原子指令，比较并交换。ABA 问题：A→B→A，CAS 误判。解决：AtomicStampedReference（版本号）。
""",
        "scenario": "job_interview",
    },
    {
        "repo": "Snailclimb/JavaGuide",
        "file_path": "docs/database/MySQL.md",
        "default_cat": "数据库",
        "content": r"""
## Q: MySQL 的索引类型有哪些？
B+ 树索引（最常用）、哈希索引（Memory 引擎）、全文索引（MyISAM/InnoDB 支持）、空间索引（GIS）。
InnoDB 索引分类：聚簇索引（主键索引，叶子节点存整行数据）、二级索引（非主键索引，叶子节点存主键值，需回表）。

## Q: 为什么 InnoDB 用 B+ 树而不是 B 树？
B+ 树非叶子节点不存数据（只存索引），同大小节点能存更多索引→树更矮→IO 更少。
叶子节点用链表连接→支持范围查询和排序。B 树每层都可能包含数据，范围查询需要中序遍历。

## Q: 覆盖索引是什么？
查询所需字段全部在一个索引中，无需回表。
Extra 列显示 Using index 即表示使用了覆盖索引。常见优化：创建联合索引满足查询字段。

## Q: 最左前缀原则？
联合索引 (a,b,c)，查询条件必须从最左列开始匹配。WHERE a=1 AND b=2 走索引；WHERE b=2 不走索引。MySQL 8.0 引入了索引跳跃扫描（Index Skip Scan）可部分优化。

## Q: 事务的四大特性（ACID）？
原子性（Atomicity）：全部成功或全部回滚。一致性（Consistency）：事务前后数据完整。隔离性（Isolation）：并发事务互不干扰。持久性（Durability）：提交后数据永久保存。

## Q: 事务隔离级别有哪些？
READ UNCOMMITTED（读未提交，脏读）→ READ COMMITTED（读已提交，不可重复读）→ REPEATABLE READ（可重复读，幻读）→ SERIALIZABLE（串行化）。MySQL InnoDB 默认 RR，通过 MVCC + Next-Key Lock 解决幻读。

## Q: MVCC 实现原理？
隐藏列：DB_TRX_ID（最后修改事务ID）、DB_ROLL_PTR（回滚指针）。Read View（活跃事务列表）。快照读：SELECT（不加锁）。当前读：UPDATE/DELETE/SELECT...FOR UPDATE（加锁）。
RR 下 Read View 事务开始时创建，整个事务复用一个快照。

## Q: 间隙锁（Gap Lock）是什么？
锁定索引记录之间的间隙，防止其他事务插入数据。与行锁组成 Next-Key Lock。在 RR 隔离级别生效。
防止幻读：A 事务 SELECT * FROM t WHERE id>10 FOR UPDATE，B 无法插入 id=11 的记录。

## Q: MySQL 主从复制原理？
binlog（二进制日志）→ 主库提交事务前写入 binlog → 从库 IO 线程拉取 binlog 写入 relay log → 从库 SQL 线程回放 relay log。
同步方式：异步复制、半同步复制（至少一个从库确认）、组复制（Paxos 协议）。

## Q: 慢 SQL 如何优化？
1. EXPLAIN 分析执行计划（type、key、rows、Extra）。2. 加合适索引。3. 改写 SQL（避免 SELECT *、避免函数操作索引列）。4. 大分页优化（游标分页）。5. 读写分离。6. 必要时上缓存（Redis）。
""",
        "scenario": "job_interview",
    },
    # ============ CS-Notes — 算法 ============
    {
        "repo": "CyC2018/CS-Notes",
        "file_path": "notes/算法-面试题.md",
        "default_cat": "算法",
        "content": r"""
## Q: 反转单链表
迭代：三个指针 prev/curr/next 原地反转。递归：递推到最后一个节点，归回来反转指针。
时间复杂度 O(n)，空间复杂度 O(1)（迭代）。

## Q: 两个链表的第一个公共节点
双指针：pA 走完 A 走 B，pB 走完 B 走 A，相遇点即为公共节点。时间复杂度 O(m+n)。

## Q: 合并两个有序链表
迭代：哨兵节点 + 比较两链表当前节点。递归：l1.val < l2.val ? 递归合并剩余部分。O(n)。

## Q: 二叉树的层序遍历
BFS：队列。每轮处理完当前队列中的所有节点（记录大小），得到一层所有节点。

## Q: 二叉树的前序/中序/后序遍历
递归：三行代码。迭代：前序用栈，中序用栈+左链，后序用两个栈或反转。

## Q: 岛屿数量（LeetCode 200）
DFS/BFS/Union-Find。遍历矩阵，遇到 '1' 计数并 DFS 淹没整个岛屿（置 '0'）。
""",
        "scenario": "job_interview",
    },
    {
        "repo": "CyC2018/CS-Notes",
        "file_path": "notes/计算机网络.md",
        "default_cat": "网络",
        "content": r"""
## Q: OSI 七层模型和 TCP/IP 四层模型？
OSI：应用层→表示层→会话层→传输层→网络层→数据链路层→物理层。
TCP/IP：应用层→传输层（TCP/UDP）→网络层（IP）→网络接口层。

## Q: TCP 三次握手的过程？
1. 客户端发 SYN（seq=x）。2. 服务端发 SYN+ACK（seq=y, ack=x+1）。3. 客户端发 ACK（seq=x+1, ack=y+1）。
为什么不是两次：防止旧的连接请求到达服务器造成错误连接。

## Q: TCP 四次挥手的过程？
1. 主动方发 FIN。2. 被动方回 ACK。3. 被动方发 FIN。4. 主动方回 ACK。
TIME_WAIT：主动方在最后等待 2MSL。原因：确保被动方收到最后的 ACK；让旧连接报文消失在网络中。

## Q: TCP 如何保证可靠传输？
校验和、序列号 + 确认应答（ACK）、超时重传、流量控制（滑动窗口）、拥塞控制（慢启动/拥塞避免/快重传/快恢复）。

## Q: HTTP 和 HTTPS 的区别？
HTTPS = HTTP + SSL/TLS。默认端口 443 vs 80。HTTPS 需要 CA 证书。TLS 握手：非对称加密交换密钥 + 对称加密传输数据。

## Q: HTTP 1.0、1.1、2.0 的区别？
1.0：短连接。1.1：长连接（keep-alive）、管道化（有队头阻塞问题）。2.0：二进制分帧、多路复用（解决队头阻塞）、HPACK 头部压缩、服务端推送。

## Q: GET 和 POST 的区别？
GET：幂等、数据在 URL（长度限制）、可缓存、只读语义。POST：非幂等、数据在 body、不缓存、修改语义。
实际浏览器差异已不大，但 RESTful API 推荐按语义使用。

## Q: Cookie 和 Session 的区别？
Cookie 在客户端，Session 在服务端。Session 通过 Cookie（JSESSIONID）或 URL 重写关联用户。
Cookie 有大小限制（4KB）和数量限制（20个/域）。
""",
        "scenario": "job_interview",
    },
    # ============ 操作系统 ============
    {
        "repo": "CyC2018/CS-Notes",
        "file_path": "notes/操作系统.md",
        "default_cat": "操作系统",
        "content": r"""
## Q: 进程和线程的区别？
进程：资源分配的最小单位，独立地址空间，切换开销大。
线程：CPU 调度的最小单位，共享进程地址空间，切换开销小。同一进程的线程共享堆和方法区，各自有程序计数器和栈。

## Q: 进程调度算法？
FCFS（先来先服务）、SJF（短作业优先，有饥饿问题）、优先级调度、RR（时间片轮转）、多级反馈队列（Linux 使用）。

## Q: 死锁的四个必要条件？
互斥、请求保持、不可剥夺、循环等待。预防：破坏任一条件。银行家算法用于避免死锁。

## Q: 虚拟内存的作用？
将虚拟地址映射到物理地址，使进程以为拥有连续完整的地址空间。缺页中断：访问的页面不在内存中时触发，从磁盘加载。
页面置换算法：FIFO、LRU（最久未使用）、LFU（最不常用）、Clock 算法。

## Q: Linux 中进程间通信（IPC）方式？
管道（pipe/FIFO）、信号（signal）、共享内存（最快）、消息队列、信号量（同步）、套接字（跨网络通信）。

## Q: select、poll、epoll 的区别？
select：fd 有限（1024）、O(n) 遍历。poll：链表无上限、O(n) 遍历。epoll：事件驱动、回调机制、O(1)。
epoll 使用红黑树 + 就绪链表，只返回就绪的 fd，避免了无差别遍历。
""",
        "scenario": "job_interview",
    },
    # ============ 系统设计 ============
    {
        "repo": "Snailclimb/JavaGuide",
        "file_path": "docs/system-design/分布式基础.md",
        "default_cat": "系统设计",
        "content": r"""
## Q: 什么是 CAP 定理？
一致性（Consistency）：所有节点同时看到相同数据。可用性（Availability）：每个请求都能收到响应。分区容错性（Partition Tolerance）：系统仍能运行。分布式系统只能满足其中两个。

## Q: 什么是 BASE 理论？
Basically Available（基本可用）、Soft State（软状态）、Eventually Consistent（最终一致性）。
BASE 是 AP 思路的体现，牺牲强一致性换取可用性。

## Q: 什么是分布式事务？实现方案有哪些？
2PC（两阶段提交：准备+提交，同步阻塞，协调者单点问题）。
TCC（Try-Confirm-Cancel，业务补偿，无锁，侵入性强）。
Seata AT（自动反向 SQL，适合需要自动回滚的场景）。
Saga（拆分成多个子事务 + 补偿操作，适合长事务）。

## Q: 什么是分布式 Session？实现方式？
Session 复制（Tomcat 自带，性能差）、客户端存储（不安全+大小限制）、粘性 Session（负载均衡 hash，有单点风险）、集中式 Session（Redis，最常用）。

## Q: 负载均衡算法有哪些？
轮询、加权轮询、最少连接、IP Hash、一致性 Hash。应用层：Nginx。传输层：LVS（F5）。
""",
        "scenario": "job_interview",
    },
    # ============ JavaGuide — Redis ============
    {
        "repo": "Snailclimb/JavaGuide",
        "file_path": "docs/database/Redis.md",
        "default_cat": "数据库",
        "content": r"""
## Q: Redis 的数据类型有哪些？
String（字符串）、Hash（哈希）、List（列表）、Set（集合）、ZSet（有序集合）。
额外：Bitmap、HyperLogLog、Geo、Stream。底层数据结构：SDS、ziplist/listpack、skiplist、dict、intset。

## Q: Redis 为什么快？
纯内存操作、单线程（避免锁竞争，6.0+ 多线程处理网络 IO）、IO 多路复用（epoll）、高效的数据结构。

## Q: Redis 的持久化方式？
RDB（快照）：全量数据二进制 dump，适合备份，可能丢数据。
AOF（追加文件）：记录每一条写命令，可配置 everysec/always/no，文件大。
Redis 4.0+ 混合持久化：RDB + AOF（增量）。推荐开启 AOF + 定时 RDB。

## Q: 缓存穿透、缓存击穿、缓存雪崩？
穿透：查询不存在的数据。解决：布隆过滤器 + 缓存 null 值。
击穿：热点 key 过期。解决：互斥锁 + 逻辑过期时间。
雪崩：大量 key 同时过期。解决：过期时间加随机值 + 多级缓存 + 限流。

## Q: Redis 分布式锁的实现？
SET key value NX EX 30（原子加锁+过期）。解锁：Lua 脚本（GET + DEL 原子操作）。
Redisson 看门狗：定时续期（默认每 10 秒续 30 秒）。

## Q: Redis 过期策略？
定期删除（随机抽查过期 key）+ 惰性删除（访问时检查是否过期）。
内存淘汰策略：LRU、LFU、TTL、随机、不淘汰。
""",
        "scenario": "job_interview",
    },
]
