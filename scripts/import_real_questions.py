"""
导入 100 道大厂真实面试真题

数据来源：100道大厂真实面试真题.md
适用场景：job_interview（求职面试）

用法：python scripts/import_real_questions.py
"""

import sys
import os

# 将项目根目录加入 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.database import DatabaseManager

# ================================================================
# 数据映射
# ================================================================

POSITION_MAP = {
    "后端": "后端开发",
    "前端": "前端开发",
    "AI/算法": "AI/算法工程师",
    "大模型算法": "大模型算法工程师",
    "产品": "产品经理",
    "测试": "测试开发",
    "通用": "通用",
}

DIFFICULTY_MAP = {
    "一面": 3,
    "二面": 4,
    "三面": 5,
}

QUESTIONS = [
    # ============================================================
    # 一、字节跳动（20题）
    # ============================================================
    ("字节跳动", "后端", "一面", 1, "手写 LRU Cache，要求 O(1) get/put，HashMap + 双向链表",
     "核心：HashMap 存 key→Node，双向链表维护访问顺序。get 时将节点移到头部；put 时若已存在则更新并移到头部，否则创建新节点加入头部，超出容量则删除尾部节点。",
     "算法手撕"),
    ("字节跳动", "后端", "一面", 2, "接雨水（LeetCode 42），先给暴力解，优化到双指针 O(n)",
     "暴力：每个位置找左右最大高度，O(n²)。优化：左右双指针，维护 left_max 和 right_max，哪边小移动哪边，累加 min(left_max,right_max)-height[i]。",
     "算法手撕"),
    ("字节跳动", "后端", "一面", 3, "最长无重复字符子串（滑动窗口 + HashMap）",
     "滑动窗口 + HashMap 存字符→最近下标。右指针移动，若遇到重复字符则左指针跳到重复字符下标+1。更新最大窗口长度。O(n)。",
     "算法手撕"),
    ("字节跳动", "后端", "一面", 4, "数组第 K 大的数，快排 partition 思路 vs 小顶堆思路",
     "快排 partition：每次确定一个元素位置，若 pivot 正好是第 K 大则返回，否则递归一侧。时间复杂度 O(n) 期望。小顶堆：维护大小为 K 的小顶堆，遍历数组，大于堆顶则入堆淘汰堆顶。O(n log K)。",
     "算法手撕"),
    ("字节跳动", "后端", "一面", 5, "HashMap 1.7 vs 1.8 底层实现差异？为什么线程不安全？",
     "1.7：数组+链表，头插法，rehash 时可能死循环。1.8：数组+链表/红黑树，尾插法。线程不安全原因：同时 put 导致数据覆盖；扩容时多个线程同时 rehash 形成环。",
     "Java/Go 八股"),
    ("字节跳动", "后端", "一面", 6, "ConcurrentHashMap 如何保证并发安全？1.7 分段锁 vs 1.8 CAS+Synchronized",
     "1.7：Segment 继承 ReentrantLock，每段独立加锁，锁粒度粗。1.8：CAS 插入链表头 + Synchronized 锁链表头节点，锁粒度更细，并发度更高。",
     "Java/Go 八股"),
    ("字节跳动", "后端", "一面", 7, "volatile 的作用？能否保证原子性？内存语义是什么？",
     "作用：保证可见性（写立即同步到主存，读从主存取）和禁止指令重排序。不能保证原子性（如 i++ 是读-改-写三步）。内存语义：写 volatile 变量相当于 MonitorExit，读相当于 MonitorEnter。",
     "Java/Go 八股"),
    ("字节跳动", "后端", "一面", 8, "TCP 三次握手四次挥手，TIME_WAIT 发生在哪一方？为什么需要？",
     "三次握手：SYN → SYN+ACK → ACK。四次挥手：FIN → ACK → FIN → ACK。TIME_WAIT 发生在主动关闭连接的一方（先发 FIN 的一方）。原因：1. 确保被动方收到最后的 ACK；2. 让旧连接的所有报文在网络中消失。2MSL 时长。",
     "网络/OS/JVM"),
    ("字节跳动", "后端", "二面", 9, "联合索引 (a,b,c)，a 全是一个值，WHERE b=1 AND c=1 能走索引吗？",
     "能。联合索引最左匹配原则，但 a 全为一个值相当于过滤掉了 a 的区分度，b 和 c 可以继续走索引。本质上这是 前缀1 确定后的索引下推场景。",
     "MySQL/Redis/Kafka"),
    ("字节跳动", "后端", "二面", 10, "LIMIT 100000,10 深分页如何优化？",
     "1. 子查询 + 覆盖索引：先查 id 再 JOIN。2. 记录上一页最后一条的 id，WHERE id > last_id LIMIT 10（游标分页）。3. 延迟关联：先查索引列再关联回表。",
     "MySQL/Redis/Kafka"),
    ("字节跳动", "后端", "二面", 11, "Redis 缓存穿透、击穿、雪崩分别怎么解决？",
     "穿透：查询不存在的数据。解决：布隆过滤器 + 缓存空值。击穿：热点 key 过期瞬间高并发打到 DB。解决：互斥锁 + 逻辑过期。雪崩：大量 key 同时过期。解决：过期时间加随机值 + 多级缓存 + 限流降级。",
     "MySQL/Redis/Kafka"),
    ("字节跳动", "后端", "二面", 12, "链表重排：1→n→2→n-1→3→n-2...，要求 O(1) 额外空间",
     "三步走：1. 快慢指针找中点。2. 反转后半段链表。3. 交替合并前后两段。O(n) 时间，O(1) 空间。",
     "算法手撕"),
    ("字节跳动", "后端", "二面", 13, "Kafka 为什么高吞吐？怎样保证不重复消费？",
     "高吞吐原因：1. 顺序写磁盘。2. 零拷贝（sendfile）。3. 批量压缩发送。4. 分区并行。不重复消费：消费者手动提交 offset + 业务幂等（唯一ID去重）。Kafka 0.11+ 支持幂等生产者 exactly-once。",
     "MySQL/Redis/Kafka"),
    ("字节跳动", "后端", "三面", 14, "设计一个短链接系统（Short URL），QPS 10 万+",
     "1. 短码生成：发号器（雪花算法）→ Base62 编码 / 预生成+取号。2. 存储：Redis 缓存热点 + MySQL 持久化。3. 分库分表：按短码 hash。4. 重定向：301 永久（浏览器缓存）vs 302 临时（便于统计）。",
     "系统设计/场景题"),
    ("字节跳动", "后端", "三面", 15, "设计高并发秒杀系统，从网关到数据库全链路梳理",
     "1. 网关层：限流（令牌桶）+ 防刷（用户维度）。2. 应用层：Redis 预扣库存 + Lua 原子操作。3. 队列层：MQ 异步下单 + 削峰。4. 数据库层：乐观锁扣减 + 事务补偿。5. 兜底：库存回滚 + 对账。",
     "系统设计/场景题"),
    ("字节跳动", "后端", "三面", 16, "线上 CPU 100% 怎么排查？",
     "1. top -H 找到高 CPU 线程。2. printf '%x\\n' 转十六进制。3. jstack dump 线程栈，找到对应线程 ID。4. 分析线程状态：RUNNABLE（业务逻辑死循环）/ BLOCKED（锁竞争）。5. 如果是 Full GC 频繁则 dump 堆分析。",
     "网络/OS/JVM"),
    ("字节跳动", "前端", "一面", 17, "手写带并发限制的 Promise 调度器",
     "维护一个队列和当前并发数。每次从队列取出任务执行，完成时递归取下一个。通过 Promise.resolve() 控制队列顺序。关键：在任务开始前判断并发数是否已满。",
     "前端"),
    ("字节跳动", "前端", "一面", 18, "React Fiber 架构解决了什么问题？",
     "Stack Reconciler 递归不可中断，长时间占用主线程导致掉帧。Fiber 引入可中断的异步渲染：1. 每个组件对应 Fiber 节点。2. 双缓冲树（current/workInProgress）。3. 优先级调度（Lane）。4. 时间分片（5ms 检查一次）。",
     "前端"),
    ("字节跳动", "前端", "二面", 19, "大文件断点续传 + 秒传如何实现？",
     "1. 秒传：文件内容 hash（spark-md5）→ 服务端检查是否已存在。2. 切片：File.slice() 按固定大小切割。3. 并发上传：限制并发数，每个切片独立上传。4. 断点续传：上传前查询已上传切片列表。5. 合并：所有切片上传完成后通知服务端合并。",
     "前端"),
    ("字节跳动", "AI/算法", "一面", 20, "Transformer 自注意力机制公式和计算流程？Q、K、V 分别是什么？",
     "公式：Attention(Q,K,V) = softmax(QK^T/√d_k)V。Q=Query 查询向量，K=Key 键向量，V=Value 值向量。计算流程：1. 输入 Embedding 通过三个线性层得到 Q/K/V。2. Q×K^T 计算注意力分数。3. 除以 √d_k 缩放。4. Softmax 归一化。5. 与 V 加权求和。",
     "AI/大模型/Agent"),

    # ============================================================
    # 二、腾讯（20题）
    # ============================================================
    ("腾讯", "后端", "一面", 21, "只有 0、1、2 的数组按顺序摆放，要求 O(n) 时间、不使用排序函数",
     "三指针（荷兰国旗问题）：left=0, right=n-1, i=0 遍历。nums[i]==0 则 swap(nums[i], nums[left])，left++，i++；nums[i]==2 则 swap(nums[i], nums[right])，right--；nums[i]==1 则 i++。",
     "算法手撕"),
    ("腾讯", "后端", "一面", 22, "数组中重复的数（LeetCode 442），要求 O(1) 额外空间、O(n) 时间",
     "利用数组值范围在 [1,n] 的特点。遍历数组，将 nums[abs(nums[i])-1] 取负数。如果某位置已经是负数，说明该下标+1 重复出现。返回结果。",
     "算法手撕"),
    ("腾讯", "后端", "一面", 23, "进程和线程的根本区别？协程又是什么？",
     "进程：OS 资源分配的最小单位，独立地址空间，切换开销大。线程：CPU 调度的最小单位，共享进程地址空间，切换开销中等。协程：用户态轻量级线程，由程序自身调度，切换开销极小（微秒级），一个线程可承载上万个协程。Go goroutine 是典型实现。",
     "网络/OS/JVM"),
    ("腾讯", "后端", "一面", 24, "HTTP 与 HTTPS 区别？SSL/TLS 握手过程？",
     "区别：HTTPS = HTTP + SSL/TLS，默认端口 443 vs 80。TLS 握手：1. ClientHello（支持的加密套件）。2. ServerHello（选加密套件 + 证书）。3. 客户端验证证书。4. 客户端生成 pre-master secret 用公钥加密发送。5. 双方计算会话密钥。6. 后续对称加密通信。",
     "网络/OS/JVM"),
    ("腾讯", "后端", "一面", 25, "MySQL InnoDB 为什么用 B+ 树而不是 B 树或哈希表？",
     "B+ 树 vs B 树：B+ 树非叶子节点只存索引不存数据，叶子节点存数据并用链表连接。优点：1. 非叶子节点可存更多索引，树更矮（减少 IO）。2. 叶子节点链表支持范围查询和排序。哈希表：只支持等值查询，不支持范围查询和排序。",
     "MySQL/Redis/Kafka"),
    ("腾讯", "后端", "一面", 26, "Go GMP 调度模型详解，Work Stealing 机制是什么？",
     "G（Goroutine）- M（Machine/线程）- P（Processor/逻辑处理器）。M 必须绑定 P 才能执行 G。调度：1. 全局队列+每个 P 本地队列。2. 发生阻塞时 M 和 P 解绑，P 找新 M 或创建 M。Work Stealing：P 本地队列为空时，从其他 P 偷一半 G 过来执行。",
     "Java/Go 八股"),
    ("腾讯", "后端", "二面", 27, "三种括号 {[()]} 判断合法性，但有优先级 {} > [] > ()",
     "用两个栈：一个存左括号，一个存优先级。遍历字符串，遇到左括号入栈并记录优先级；遇到右括号时检查是否与栈顶括号匹配，且当前右括号优先级 ≥ 栈顶左括号入栈时的优先级（即栈内优先级必须 ≥ 外部优先级）。",
     "算法手撕"),
    ("腾讯", "后端", "二面", 28, "TCP 长连接如何排查？Keepalive 机制原理？",
     "排查：netstat -anp 查看连接状态（ESTABLISHED/TIME_WAIT/CLOSE_WAIT），ss -t 看 socket 统计。Keepalive：TCP 层保活机制。空闲 2h 后发探测报文，若连续多次无响应则关闭连接。HTTP Keep-Alive 是应用层概念，复用 TCP 连接避免重复握手。",
     "网络/OS/JVM"),
    ("腾讯", "后端", "二面", 29, "MySQL Gap Lock 是什么？在什么隔离级别下生效？",
     "Gap Lock（间隙锁）：锁定索引记录之间的间隙，防止其他事务插入数据。在 RR（可重复读）隔离级别下生效。与行锁组合成 Next-Key Lock。幻读：同一事务两次查询结果集不同。Gap Lock 防止新的符合条件的数据被插入。",
     "MySQL/Redis/Kafka"),
    ("腾讯", "后端", "二面", 30, "MVCC 原理？Read View 如何判断可见性？",
     "MVCC 通过隐藏列（DB_TRX_ID 事务ID、DB_ROLL_PTR 回滚指针）实现。Read View 包含：m_low_limit_id（当前已分配最大事务ID）、m_up_limit_id（活跃事务最小ID）、m_ids（活跃事务列表）。判断：trx_id < up_limit_id 可见；trx_id > low_limit_id 不可见；在 m_ids 中不可见。RR 下 Read View 只在事务开始时创建，RC 下每条语句创建。",
     "MySQL/Redis/Kafka"),
    ("腾讯", "后端", "二面", 31, "Go Context 的使用场景？被调用方如何感知超时？",
     "Context 用于传递请求范围的值、取消信号、超时/截止时间。使用场景：1. 请求链路超时控制。2. 并发操作取消。3. 传递 trace ID 等元数据。被调用方通过 ctx.Done() channel 感知取消，通常结合 select 使用：有数据则处理，ctx.Done() 则返回超时错误。",
     "Java/Go 八股"),
    ("腾讯", "后端", "三面", 32, "大 V 发微博的设计题——推拉结合模式",
     "普通用户：推模式（发微博→写入粉丝收件箱）。大 V：拉模式（粉丝读取时拉取大 V 微博）。结合：大 V 发微博写入自身时间线，粉丝读取时先拉取热榜/大 V 微博，再合并普通用户推送消息。优化：冷热数据分离、缓存粉丝关系、异步 fanout。",
     "系统设计/场景题"),
    ("腾讯", "后端", "三面", 33, "零拷贝 sendfile / mmap 原理？为什么 Kafka 要用零拷贝？",
     "传统 IO：磁盘→内核缓冲区→用户缓冲区→Socket 缓冲区→网卡，4 次上下文切换 + 数据拷贝。sendfile：磁盘→内核缓冲区→Socket 缓冲区→网卡，2 次上下文切换。mmap：用户态直接映射内核空间。Kafka 用 sendfile 将数据从文件直接发送到网卡，避免用户态拷贝，提升吞吐。",
     "网络/OS/JVM"),
    ("腾讯", "后端", "三面", 34, "一致性 Hash 原理？普通 Hash 有什么问题？",
     "普通 Hash（hash(key) % N）：节点增减导致大量 key 重新映射，缓存雪崩。一致性 Hash：将 Hash 值空间组织成环，节点和 key 都落在环上，key 顺时针找最近节点。增减节点只影响相邻节点。虚拟节点解决数据倾斜问题。",
     "系统设计/场景题"),
    ("腾讯", "前端", "一面", 35, "Event Loop 浏览器和 Node.js 的差异？",
     "浏览器：宏任务（script/setTimeout/UI事件）→ 微任务（Promise/MutationObserver）→ 渲染。Node.js：timers → pending callbacks → idle/prepare → poll → check → close。Node 11+ 后每个宏任务后清空微任务，与浏览器行为一致。process.nextTick 优先级最高。",
     "前端"),
    ("腾讯", "前端", "一面", 36, "跨端通信 JSBridge 原理？",
     "WebView → Native：1. 拦截 URL Scheme（iframe.src = 'jsbridge://method?params'）。2. Native 拦截请求并解析。Native → WebView：evaluateJavascript 注入回调。更现代的方式：addJavascriptInterface（Android）/ WKScriptMessageHandler（iOS）。",
     "前端"),
    ("腾讯", "前端", "二面", 37, "XSS / CSRF 攻击原理和防护方案？",
     "XSS：注入恶意脚本。防护：输入过滤 + 输出转义 + CSP HTTP 头 + HttpOnly Cookie。CSRF：跨站请求伪造。防护：SameSite Cookie + Token 验证 + Referer 检查 + 验证码（关键操作）。Cookie SameSite=Strict/Lax 可阻止第三方网站携带 cookie。",
     "前端"),
    ("腾讯", "产品", "一面", 38, "假设 GMV 下降 20%，你会如何诊断并提出方案？",
     "诊断框架：1. 拆 GMV = 流量 × 转化率 × 客单价 × 复购率。2. 定位下降环节：新用户 vs 老用户、各渠道、各品类。3. 外部因素：竞品动作、季节性、政策变化。方案：A/B 测试验证假设，快速迭代。",
     "项目深挖/行为面试"),
    ("腾讯", "产品", "二面", 39, "描述一次你从 0 到 1 做产品的经历",
     "STAR-R 法则：Situation（背景/痛点）→ Task（目标/指标）→ Action（行动/方案）→ Result（量化结果）→ Reflection（复盘/反思）。重点展示：用户调研方法、决策依据、数据驱动、协同推动。",
     "项目深挖/行为面试"),
    ("腾讯", "测试", "一面", 40, "抖音视频上传功能，你如何设计测试方案？",
     "功能：选择文件、进度条、暂停/续传、取消、格式校验、大小限制。性能：不同网络（4G/WiFi/弱网）、大文件、并发上传。兼容性：不同机型/系统/分辨率。异常：断网恢复、存储空间不足、后台切换、文件损坏。安全：注入攻击、文件类型欺骗。",
     "系统设计/场景题"),

    # ============================================================
    # 三、阿里巴巴（20题）
    # ============================================================
    ("阿里巴巴", "后端", "一面", 41, "HashMap 底层结构？1.7 头插法 → 1.8 尾插法，链表转红黑树的阈值是多少？",
     "底层结构：数组+链表/红黑树。1.7 头插法：rehash 时逆序，多线程可能死循环。1.8 尾插法：保持原有顺序。链表转红黑树阈值：≥8 且数组长度 ≥64。红黑树转链表阈值：≤6。阈值8 是泊松分布的结果，概率极低。",
     "Java/Go 八股"),
    ("阿里巴巴", "后端", "一面", 42, "hashCode 与 equals 的关系？",
     "约定：1. 两个对象 equals 返回 true，hashCode 必须相等。2. 反之 hashCode 相等，equals 不要求 true（哈希碰撞）。只重写 hashCode 不重写 equals：HashMap 中可能找到正确桶但 equals 返回 false，无法正确获取 value。",
     "Java/Go 八股"),
    ("阿里巴巴", "后端", "一面", 43, "synchronized 锁升级过程？",
     "无锁 → 偏向锁（单线程竞争，Mark Word 存线程 ID）→ 轻量级锁（CAS 自旋，Mark Word 存栈帧锁记录）→ 重量级锁（OS 互斥量，阻塞等待）。锁只能升级不能降级。偏向锁在 JDK 15 默认关闭。",
     "Java/Go 八股"),
    ("阿里巴巴", "后端", "一面", 44, "ThreadLocal 底层实现原理？为什么会有内存泄漏？",
     "每个线程有 ThreadLocalMap（Entry<ThreadLocal, value>）。ThreadLocal 的 key 是弱引用（WeakReference）。内存泄漏原因：ThreadLocal 被 GC 回收后 key 为 null，但 value 仍有强引用可达（线程存活期间无法回收）。解决：用完调用 remove()。",
     "Java/Go 八股"),
    ("阿里巴巴", "后端", "一面", 45, "线程池核心参数是什么？",
     "corePoolSize（核心线程数）→ maxPoolSize（最大线程数）→ keepAliveTime（空闲线程存活时间）→ workQueue（任务队列，如 ArrayBlockingQueue）→ threadFactory（线程工厂）→ handler（拒绝策略：AbortPolicy/CallerRunsPolicy/DiscardOldestPolicy/DiscardPolicy）。",
     "Java/Go 八股"),
    ("阿里巴巴", "后端", "一面", 46, "线程池提交任务后的执行流程？",
     "1. 线程数 < corePoolSize：创建新线程执行。2. ≥ corePoolSize：任务入 workQueue。3. 队列满且线程数 < maxPoolSize：创建新线程执行。4. 队列满且已达 maxPoolSize：执行拒绝策略。",
     "Java/Go 八股"),
    ("阿里巴巴", "后端", "一面", 47, "CAS 实现原理？ABA 问题是什么？如何解决？",
     "CAS（Compare And Swap）：硬件原子指令，三个操作数（内存地址 V、预期值 A、新值 B）。若 V==A 则写入 B，否则重试/失败。ABA 问题：A→B→A，CAS 误认为没被修改过。解决：AtomicStampedReference 加版本号/时间戳。",
     "Java/Go 八股"),
    ("阿里巴巴", "后端", "二面", 48, "JVM 内存结构各区域详细说明",
     "1. 堆（Heap）：对象实例，GC 主要区域，分新生代和老年代。2. 方法区（元空间）：类信息、常量、静态变量。3. 虚拟机栈：栈帧（局部变量表/操作数栈/动态链接/出口）。4. 程序计数器：当前线程执行字节码行号。5. 本地方法栈：native 方法。",
     "网络/OS/JVM"),
    ("阿里巴巴", "后端", "二面", 49, "CMS 和 G1 垃圾收集器的详细对比？",
     "CMS（Concurrent Mark Sweep）：标记-清除，关注最短停顿时间。步骤：初始标记→并发标记→重新标记→并发清除。缺点：内存碎片、浮动垃圾。G1（Garbage First）：分 Region、维持暂停时间预测（-XX:MaxGCPauseMillis）。步骤：初始标记→并发标记→最终标记→筛选回收。G1 可指定停顿时间目标，更适合大堆。",
     "网络/OS/JVM"),
    ("阿里巴巴", "后端", "二面", 50, "Minor GC / Major GC / Full GC 触发条件区别？",
     "Minor GC（Young GC）：Eden 区满时触发。Major GC：老年代空间不足。Full GC：1. 老年代空间不足。2. 方法区空间不足。3. System.gc() 调用。4. CMS 并发模式失败（Concurrent Mode Failure）。5. 晋升担保失败。",
     "网络/OS/JVM"),
    ("阿里巴巴", "后端", "二面", 51, "OOM 如何排查？jmap dump + MAT 分析的具体步骤？",
     "1. 启动参数加 -XX:+HeapDumpOnOutOfMemoryError。2. jmap -dump:format=b,file=heap.hprof <pid>。3. MAT 打开 dump 文件。4. Leak Suspect Report 看嫌疑对象。5. Dominator Tree 找大对象。6. GC Root 路径分析确认引用链。",
     "网络/OS/JVM"),
    ("阿里巴巴", "后端", "二面", 52, "Redis 分布式锁如何实现？Redisson 看门狗机制？",
     "SET key value NX EX 30：原子加锁+过期。解锁用 Lua 脚本（GET + DEL）保证原子性。Redisson 看门狗：加锁后启动定时任务，每隔 1/3 锁过期时间（默认 10s）自动续期。解决了业务执行时间超过锁过期时间的问题。",
     "MySQL/Redis/Kafka"),
    ("阿里巴巴", "后端", "二面", 53, "数据库和缓存（Redis）如何保证数据一致性？",
     "推荐策略：先更新数据库 → 再删除缓存（Cache-Aside Pattern）。为什么不先删缓存：删缓存后 DB 更新前其他线程读 DB 写旧缓存。延迟双删：先删缓存 → 更新 DB → sleep 毫秒级 → 再删缓存。最终一致性方案：监听 Binlog（Canal）异步同步。",
     "MySQL/Redis/Kafka"),
    ("阿里巴巴", "后端", "二面", 54, "MySQL 慢 SQL 排查全流程：EXPLAIN 各字段含义",
     "EXPLAIN 关键字段：type（ALL/index/range/ref/eq_ref/const 性能由差到好）、key（实际使用索引）、rows（扫描行数估计值）、Extra（Using filesort 需优化、Using temporary 临时表、Using index 覆盖索引）。优化：加索引、改写 SQL、分页优化、读写分离。",
     "MySQL/Redis/Kafka"),
    ("阿里巴巴", "后端", "二面", 55, "分布式事务有哪些实现方案？",
     "2PC（两阶段提交）：Prepare+Commit，同步阻塞，协调者单点。TCC（Try-Confirm-Cancel）：业务补偿，无锁，适合短事务。Seata AT：自动代理 SQL，回滚生成逆 SQL。Saga：长事务拆分，每个子事务有补偿操作，适合异步流程。根据一致性要求选择。",
     "系统设计/场景题"),
    ("阿里巴巴", "后端", "二面", 56, "RocketMQ 事务消息原理？与 Kafka 的事务有什么区别？",
     "RocketMQ 事务消息：1. 发送半消息（prepare）。2. 执行本地事务。3. 提交/回滚。4. 回查（broker 定期询问事务状态）。Kafka 事务：基于幂等和原子写入，跨分区事务需要 Transaction Coordinator 协调。本质差异：RocketMQ 先发消息后执行本地事务，Kafka 先执行后发消息。",
     "MySQL/Redis/Kafka"),
    ("阿里巴巴", "后端", "二面", 57, "分库分表如何设计？跨分片查询怎么处理？",
     "分片键选择：高频查询字段。取模/范围/一致性 Hash。跨分片查询：1. 聚合查询（汇总各分片结果再合并）。2. 基因法（sharding key 冗余到非分片字段）。3. ES 全局索引。4. 尽量避免跨分片 JOIN。ShardingSphere/MyCat 可屏蔽分片复杂度。",
     "系统设计/场景题"),
    ("阿里巴巴", "后端", "二面", 58, "项目中被否决的方案是什么？为什么被否决？",
     "考察技术决策能力和复盘意识。结构：背景→你提出的方案→否决原因（如成本/性能/可维护性/团队能力不匹配）→当时的反应→事后反思→学到了什么。重点是展示对技术选型限制因素的理解。",
     "项目深挖/行为面试"),
    ("阿里巴巴", "AI/算法", "一面", 59, "Transformer 为什么用 Decoder-Only 架构？和 Encoder-Decoder 的区别？",
     "Decoder-Only（GPT 系列）：自回归生成，每个 token 只能看前面的 token（causal attention）。Encoder-Decoder（T5/BART）：Encoder 双向上下文，Decoder 单向生成。Decoder-Only 优势：1. 统一 pre-train 和 fine-tune 范式。2. 更简单的训练和扩展（scaling law）。3. In-context learning 能力更强。",
     "AI/大模型/Agent"),
    ("阿里巴巴", "AI/算法", "二面", 60, "DeepSpeed ZeRO Stage 1/2/3 的区别？FSDP 对比？",
     "ZeRO-1：优化器状态分片。ZeRO-2：优化器+梯度分片。ZeRO-3：优化器+梯度+模型参数全分片，通信量最大但显存最省。FSDP（PyTorch）：类似 ZeRO-3，在 forward/backward 时 all-gather 参数，计算完即释放。大模型 OOM 处理：梯度累积、混合精度、activation checkpointing、CPU offload。",
     "AI/大模型/Agent"),

    # ============================================================
    # 四、美团（10题）
    # ============================================================
    ("美团", "后端", "一面", 61, "删除链表倒数第 k 个节点（LeetCode 19）",
     "快慢指针：快指针先走 k 步，然后快慢指针同时走。快指针到末尾时慢指针指向倒数第 k 个节点的前驱。注意删除头节点的边界情况。O(n)。",
     "算法手撕"),
    ("美团", "后端", "一面", 62, "Redis ZSet 底层实现（listpack + skiplist），为什么跳表而不用平衡树？",
     "ZSet 在元素较少时用 ziplist（7.0+ 改为 listpack），超过阈值用 skiplist + dict。跳表优势：1. 实现简单，调整平衡代价低。2. 范围查询效率高（ZRANGEBYSCORE）。3. 内存更紧凑。平衡树：调整复杂，需要旋转维持平衡。",
     "MySQL/Redis/Kafka"),
    ("美团", "后端", "一面", 63, "MySQL 默认隔离级别 RR，MVCC + Read View 如何实现？能解决幻读吗？",
     "RR 下 Read View 在事务开始时创建，整个事务复用。MVCC 通过 undo log 快照读实现非锁定读。能解决快照读的幻读（同一事务多次快照读结果一致），但不能解决当前读的幻读（SELECT ... FOR UPDATE 需要 Gap Lock 防止）。",
     "MySQL/Redis/Kafka"),
    ("美团", "后端", "一面", 64, "Kafka 消息可靠性如何保证？",
     "生产者：acks=all（等待所有副本确认）→ 重试 + 幂等。Broker：min.insync.replicas ≥ 2 → unclean.leader.election=false。消费者：enable.auto.commit=false 手动提交 → 处理完再提交 offset。幂等消费（业务唯一 ID 去重）。",
     "MySQL/Redis/Kafka"),
    ("美团", "后端", "二面", 65, "JVM 新生代和老年代为什么要分开？",
     "分代收集理论：大部分对象朝生夕死。新生代：频繁 Minor GC，复制算法效率高。老年代：存活久的对象，Mark-Sweep/Mark-Compact 算法。分开的好处：1. 针对不同存活率用不同算法，提高效率。2. 减少 Full GC 频率。3. 对象晋升条件可作为 GC 调优依据。",
     "网络/OS/JVM"),
    ("美团", "后端", "二面", 66, "项目中有哪些技术难点？如何用方法论解决？",
     "方法论：最小可复现（缩小问题范围）→ 量化观测（埋点/监控/指标）→ 回归验证（改前改后对比）。示例：线上接口慢→看 trace 定位到某 SQL→EXPLAIN 分析→加索引→压测验证→灰度上线。",
     "项目深挖/行为面试"),
    ("美团", "后端", "二面", 67, "系统设计：千万级用户社区内容推荐系统",
     "核心链路：用户画像 → 内容召回（协同过滤/向量相似度/热榜）→ 粗排（LR/GBDT）→ 精排（DeepFM/DIN）→ 重排（打散/多样性/去重）。技术栈：Redis 缓存特征、ES 召回、Faiss 向量检索。离线训练+在线 serving 分层。AB 平台。",
     "系统设计/场景题"),
    ("美团", "前端", "一面", 68, "数组转树形结构，输入 [{id, pid}]，输出嵌套树",
     "O(n) 解法：用 HashMap 存 id→node 映射，遍历把每个节点挂到父节点的 children 上。根节点 pid===null。注意不能嵌套循环。处理乱序：先全部放入 map，再遍历一次关联父节点。",
     "前端"),
    ("美团", "前端", "二面", 69, "虚拟列表如何实现？",
     "只渲染可视区域 + 缓冲区 DOM。核心：1. 计算可视区可容纳行数。2. 监听滚动计算 startIndex 和 endIndex。3. 绝对定位 + transform translateY 保持滚动条正确高度。4. DOM 回收：超出缓冲区的节点复用或移除。ResizeObserver 监听元素尺寸变化。",
     "前端"),
    ("美团", "产品", "一面", 70, "共享单车如何设计盈利模式？3C 框架分析",
     "3C 框架：Customer（用户：通勤/短途、价格敏感、便捷需求）、Cost（成本：车辆制造成本、运维调度、损毁折旧、电费）、Competition（竞品：滴滴青桔/哈啰/美团单车的价格战、市政单车免费）。盈利方向：骑行收入+广告+数据服务+异业合作。核心：提高周转率和降低运维成本。",
     "项目深挖/行为面试"),

    # ============================================================
    # 五、快手（8题）
    # ============================================================
    ("快手", "后端", "一面", 71, "字符串相加（LeetCode 415），手写大数加法",
     "双指针从尾部遍历，逐位相加+进位。结果用数组倒序存放。注意处理不同长度和最后进位。",
     "算法手撕"),
    ("快手", "后端", "一面", 72, "乐观锁解决超卖问题？Redis + Lua 脚本 vs 数据库乐观锁",
     "数据库乐观锁：UPDATE SET stock=stock-1 WHERE id=? AND stock>0，利用行锁保证原子。Redis+Lua：在 Redis 中用 Lua 脚本原子执行 DECR 和检查，性能更高。各自优缺点：DB 锁简单可靠但吞吐受限；Redis+Lua 高吞吐但可能丢数据（需要持久化+主从同步）。",
     "MySQL/Redis/Kafka"),
    ("快手", "后端", "一面", 73, "Redis 客户端对比：Jedis vs Lettuce vs Redisson",
     "Jedis：直连，线程不安全（需要连接池），轻量，适合简单场景。Lettuce：基于 Netty，线程安全（可多线程共享连接），支持异步/Reactive，Spring Boot 2.x 默认。Redisson：封装了分布式对象/锁/集合/队列，功能丰富，学习成本高。",
     "MySQL/Redis/Kafka"),
    ("快手", "后端", "二面", 74, "70 万 QPS 下三级存储 + 两级缓存架构设计",
     "三级存储：Redis（热数据）→ 本地内存（超高频率）→ MySQL（持久化）。两级缓存：本地缓存（Caffeine/Guava）+ 分布式缓存（Redis）。数据一致性：本地缓存短 TTL + 订阅变更消息 + 主动失效。对账方案：离线定时扫描 DB vs Redis 差异并修复。",
     "系统设计/场景题"),
    ("快手", "后端", "二面", 75, "Spring Boot 自动配置原理？@SpringBootApplication 背后做了什么？",
     "@SpringBootApplication = @Configuration + @EnableAutoConfiguration + @ComponentScan。自动配置核心：spring.factories 中配置的 AutoConfiguration 类，通过 @Conditional 条件判断是否生效。ConditionalOnClass/ConditionalOnMissingBean/ConditionalOnProperty。",
     "Java/Go 八股"),
    ("快手", "后端", "三面", 76, "手写判断有效括号（LeetCode 20），扩展支持多种括号嵌套",
     "栈。遇到左括号入栈，遇到右括号检查栈顶是否匹配。遍历完栈为空则有效。扩展题：支持带优先级的括号（类似腾讯 27 题），需要用两个栈或记录优先级信息。",
     "算法手撕"),
    ("快手", "后端", "三面", 77, "限流算法：令牌桶 vs 漏桶区别？应对突发流量选哪个？",
     "令牌桶：以固定速率生成令牌放入桶中，请求消耗令牌。可应对突发流量（桶内积累的令牌可一次性消耗）。漏桶：固定速率出水（处理请求），超出则丢弃。令牌桶更适合突发流量场景。实际生产常用令牌桶 + 预热（Guava RateLimiter）。",
     "系统设计/场景题"),
    ("快手", "AI/算法", "一面", 78, "大模型 RLHF 中 PPO vs DPO vs GRPO 的区别？",
     "PPO：策略梯度方法，需要参考模型(reference policy)和奖励模型(reward model)。DPO：直接偏好优化，不需要奖励模型，直接从偏好数据学习。GRPO（DeepSeek R1）：分组相对策略优化，对同一 prompt 生成多个 response 计算相对优势，避免奖励模型和参考模型的内存开销。GRPO 核心创新：group-based advantage 计算。",
     "AI/大模型/Agent"),

    # ============================================================
    # 六、小红书（8题）
    # ============================================================
    ("小红书", "后端", "一面", 79, "Goroutine 栈内存扩展机制？GODEBUG 怎么用来调试调度器？",
     "Go goroutine 初始栈 2KB（1.19+），动态扩展。触发栈复制：当栈空间不足时，Go runtime 分配更大的栈（2x），复制原栈内容并调整指针。GODEBUG=schedtrace=1000 每 1s 打印调度信息；scheddetail=1 打印详细 goroutine 状态。",
     "Java/Go 八股"),
    ("小红书", "后端", "一面", 80, "Go Map 底层实现？为什么线程不安全？渐进式扩容如何工作？",
     "底层：hash 表 + 桶（bucket），每个桶存 8 个 key-value。渐进式扩容：当负载因子 > 6.5 时触发，将旧 buckets 迁移到新 buckets，每次写操作顺便迁移一个 bucket，避免一次性迁移。线程不安全：并发读写导致 data race（map flag 检查），需要加 sync.RWMutex 或使用 sync.Map。",
     "Java/Go 八股"),
    ("小红书", "后端", "一面", 81, "数据统计页面加载速度优化",
     "1. 前端：骨架屏、按需加载、大组件懒加载、缓存（SWR）。2. 接口：按需查询（只查可见范围数据）、预聚合（物化视图/ES 聚合）、异步计算。3. 后端：结果缓存 Redis、异步队列生成报表、增量更新。4. 数据量特别大时用 ClickHouse/TiDB。",
     "系统设计/场景题"),
    ("小红书", "后端", "二面", 82, "秒杀系统异步下单：Disruptor + 幂等补偿 + 对账兜底",
     "Disruptor：无锁环形队列，避免锁竞争和 GC 压力。幂等补偿：每个操作有唯一 requestId，下游去重执行。兜底对账：离线扫描订单状态 + 支付状态差异，自动补偿。全链路：网关限流→库存预扣→Disruptor 异步下单→幂等写入→对账修复。",
     "系统设计/场景题"),
    ("小红书", "后端", "二面", 83, "全链路限流设计",
     "四层限流：1. 前端置灰（防重复提交）。2. 网关令牌桶（全局流量整形）。3. 商品维度漏桶（每个商品的请求速率）。4. 用户滑动窗口（单个用户访问频率）。分层协同：上层拦截无效流量，下层保核心逻辑。",
     "系统设计/场景题"),
    ("小红书", "后端", "二面", 84, "全链路故障优化，RT 从 200ms 降到 30ms",
     "具体措施：1. 缓存热点数据（Redis + 本地缓存）。2. 慢 SQL 优化（加索引/改 SQL/读写分离）。3. 串行改并行（CompletableFuture allOf）。4. 连接池优化。5. 非核心逻辑异步化（MQ）。6. 压缩数据（ProtoBuf/JSON 精简）。量化：每个措施前后的耗时对比。",
     "系统设计/场景题"),
    ("小红书", "后端", "二面", 85, "Golang 错误处理：显式错误处理 vs try-catch？",
     "Go 用显式 if err != nil 而非 try-catch。优点：1. 错误处理可见，不容易被忽略。2. 控制流清晰。自定义错误类型：实现 error 接口（Error() string）+ 包装。标准库 errors.Is/As 支持 unwrap 和类型断言。panic 仅用于不可恢复错误。",
     "Java/Go 八股"),
    ("小红书", "测试", "二面", 86, "秒杀系统测试方案设计",
     "1. 压力测试：逐渐增大并发，观察 QPS/SLA/错误率，找到系统瓶颈。2. 数据一致性验证：下单数 vs 库存扣减数对账、重复支付检测、超卖检查。3. 异常容错：Redis 宕机、DB 主从切换、MQ 积压、网络分区。每个场景下系统行为是否符合预期。",
     "系统设计/场景题"),

    # ============================================================
    # 七、AI / 算法 / 大模型（10题）
    # ============================================================
    ("通用", "大模型算法", "一面", 87, "RAG 整体流程？混合检索怎么设计？",
     "RAG 流程：Query → Embedding → 向量检索 → 混合检索 → Rerank → LLM 生成。混合检索：Dense（向量语义）+ Sparse（关键词精确匹配）+ BM25（词频统计）。融合策略：加权求和（Reciprocal Rank Fusion）或学习排序。",
     "AI/大模型/Agent"),
    ("通用", "大模型算法", "一面", 88, "Rerank 在 RAG 中的作用？Cross-Encoder vs Bi-Encoder？",
     "Rerank 对检索结果精排，提高 Top-K 准确率。Cross-Encoder：Query+Doc 拼接过 Transformer，计算交互注意力，精度高但速度慢（不能预计算向量）。Bi-Encoder：Query 和 Doc 独立编码，余弦相似度匹配，速度快可预计算。RAG 典型流程：Bi-Encoder 粗排（召回 Top-100）→ Cross-Encoder 精排（Rerank Top-5）。",
     "AI/大模型/Agent"),
    ("通用", "大模型算法", "一面", 89, "Agent 核心组件？ReAct 框架详解",
     "Agent 核心组件：LLM（大脑）+ Tools（手脚）+ Memory（记忆）+ Planning（规划）。ReAct 框架：推理（Reasoning）→ 行动（Acting）→ 观察（Observation）循环。每步 LLM 思考→选择工具→执行观察→继续推理。关键：CoT（思维链）+ Tool Use + Self-Correction。",
     "AI/大模型/Agent"),
    ("通用", "大模型算法", "一面", 90, "Function Calling 实现原理？Tool Calling 与 MCP 协议？",
     "Function Calling：LLM 返回结构化参数而非自然语言。原理：在 system prompt 中注入 function schema（JSON Schema 格式），模型学会输出符合格式的 function call。Tool Calling 是 Function Calling 的扩展，支持任意工具。MCP（Model Context Protocol）：标准化 Tool Calling 协议，统一工具注册/发现/调用。",
     "AI/大模型/Agent"),
    ("通用", "大模型算法", "一面", 91, "LLM Agent 的记忆设计：分层架构",
     "三层记忆：1. 工作记忆（Working Memory）：当前对话上下文，短窗口。2. 会话记忆（Episodic Memory）：本次会话历史，通过 summarizing/compression 管理。3. 长期记忆（Long-term Memory）：跨会话知识，存入向量数据库 + 检索增强。分层实现减少 token 消耗和 attention 稀释。",
     "AI/大模型/Agent"),
    ("通用", "大模型算法", "二面", 92, "多 Agent 协同如何提高推理正确率？",
     "调度策略：1. 轮询（Round Robin）：顺序问每个 Agent，简单但无选择。2. 投票（Majority Vote）：多个 Agent 独立回答，取多数结果。3. 仲裁（Debate/Referee）：Agent 间辩论，裁判选择最优答案。4. 分层（Hierarchical）：主 Agent 分配任务，子 Agent 执行。多样性能提高推理准确率（类似于 ensemble）。",
     "AI/大模型/Agent"),
    ("通用", "大模型算法", "二面", 93, "SFT 冷启动数据集如何构造？",
     "流程：1. 数据收集：公开数据集、蒸馏（stronger model 生成）、真实场景日志。2. 数据清洗：去重（MinHash/Embedding 去重）、质量过滤（规则+模型打分）。3. 均衡采样：各领域/难度均衡。4. 质量评估：人工标注 + 模型评估 + 上线 A/B 测试。核心：少量高质量 >> 大量低质量。",
     "AI/大模型/Agent"),
    ("通用", "AI/算法", "一面", 94, "CLIP 原理？图文预训练中的对比学习 Loss 如何计算？",
     "CLIP：双塔结构，Image Encoder（ViT/ResNet）+ Text Encoder（Transformer）。训练：batch 内 N 个图文对，计算 N×N 的相似度矩阵（image 输出 ⊗ text 输出），对角线为正例，其他为负例。Loss=交叉熵（InfoNCE），label 为对角线的 one-hot 索引。",
     "AI/大模型/Agent"),
    ("通用", "AI/算法", "二面", 95, "手写位置编码（RoPE）和多头注意力机制",
     "RoPE（旋转位置编码）：在 Q 和 K 的向量空间做旋转变换，点积结果天然包含相对位置信息。公式：f(q,m)=q·e^(imθ)，将位置信息编码到旋转矩阵中。Multi-Head Attention：将 Q/K/V 拆分成 h 个头，每个头独立计算注意力，再拼接线性投影。不同头关注不同的语义子空间。",
     "AI/大模型/Agent"),
    ("通用", "AI/算法", "一面", 96, "Prompt 优化效果的评估指标？",
     "自动化评估：ROUGE/BLEU/BERTScore、LLM-as-Judge（GPT-4 打分）、对比测试（A/B）。人工评估：质量打分（1-5）、偏好对比（win/tie/loss）。上线评估：用户满意度、任务完成率、留存率。自动化+人工+上线三阶段结合。",
     "AI/大模型/Agent"),

    # ============================================================
    # 八、通用场景设计 / 项目深挖（4题）
    # ============================================================
    ("通用", "后端", "通用", 97, "系统 QPS 从 1k 涨到 10k，需要做哪些架构优化？",
     "逐层展开：1. 缓存层：本地缓存→Redis 多级缓存。2. 数据库层：索引优化→读写分离→分库分表。3. 中间件：MQ 削峰、异步解耦。4. 限流降级：令牌桶/漏桶、熔断器（Sentinel/Hystrix）。5. 静态资源：CDN。6. 微服务拆分：按业务垂直拆分。7. 容器化+弹性伸缩。",
     "系统设计/场景题"),
    ("通用", "后端", "通用", 98, "介绍一下你最有成就感的项目（STAR 法则）",
     "Situation（背景/痛点）→ Task（目标/量化指标）→ Action（技术方案/设计决策/分工协作）→ Result（量化成果：XX% 提升/XX ms 降低）→ 踩坑（什么坑？怎么发现的？如何修复？）→ 复盘（如果再重来会怎么做？学到什么？）。",
     "项目深挖/行为面试"),
    ("通用", "后端", "通用", 99, "系统接口响应时间从 50ms 涨到 2s，如何定位？",
     "链路排查：1. 网络层：ping/traceroute、是否跨机房、DNS 解析。2. 网关层：是否有限流/熔断。3. 应用层：CPU/内存/GC 情况、慢 SQL、Redis 耗时、外部 RPC 调用。4. 数据库层：锁等待、慢查询、连接池耗尽。5. APM 工具（SkyWalking/Arthas）定位瓶颈节点。",
     "系统设计/场景题"),
    ("通用", "通用", "通用", 100, "你对自己 3-5 年的职业规划是什么？为什么想来我们公司？",
     "职业规划：1. 短期（1年）：深入业务+夯实技术基础→成为某领域的可靠执行者。2. 中期（2-3年）：独立负责核心模块→带项目/带新人→技术深度+业务理解并重。3. 长期（3-5年）：技术专家 or 技术leader→能影响团队技术方向。对公司：体现对业务的认同 + 对技术栈的兴趣 + 与自己规划的匹配度。",
     "项目深挖/行为面试"),
]

SOURCE = "牛客网/CSDN/力扣社区/GitHub 开源/B站/小红书"
YEAR = "2025"


def import_questions(db: DatabaseManager) -> None:
    """
    导入 100 道真实面试题。
    """
    count = 0
    skipped = 0

    print(f"[Import] 开始导入 {len(QUESTIONS)} 道面试题...")

    for company, position_short, round_label, q_no, question_text, reference_answer, category in QUESTIONS:
        position = POSITION_MAP.get(position_short, position_short)
        difficulty = DIFFICULTY_MAP.get(round_label, 3)

        result = db.add_question(
            scenario_id="job_interview",
            category=category,
            difficulty=difficulty,
            question_text=question_text,
            reference_answer=reference_answer,
            tags=[category, company, position, f"第{round_label}"],
            company=company,
            position=position,
            source=SOURCE,
            year=YEAR,
        )

        if result["success"]:
            count += 1
            # 进度提示
            if count % 10 == 0:
                print(f"  ... 已导入 {count}/{len(QUESTIONS)}")
        else:
            skipped += 1
            print(f"  [跳过] 第 {q_no} 题（{company}）：{result.get('error', 'unknown')}")

    print(f"\n[Import] 完成！成功导入 {count} 题，跳过 {skipped} 题（重复）")


def main():
    from src.core.database import DatabaseManager
    db = DatabaseManager()
    import_questions(db)


if __name__ == "__main__":
    main()
