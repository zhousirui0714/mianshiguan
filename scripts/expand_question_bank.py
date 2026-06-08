"""
题库扩充脚本 — 补充各分类薄弱环节至目标题量

来源类型：
  real_interview — 真实面经/大厂真题
  open_source   — 开源资料整理（JavaGuide、CS-Notes 等）
  ai_generated  — AI 系统整理

目标：总题量 >= 1000
用法：python scripts/expand_question_bank.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.database import DatabaseManager

# ================================================================
# 1. 真实面经题 (real_interview) — 约 80 道
# ================================================================
REAL_INTERVIEW_QUESTIONS = [
    # --- 算法 (10) ---
    ("job_interview", "算法", 4, "给定一个二叉搜索树，找出第 K 大的节点。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 5, "手写快速排序和归并排序，分析时间复杂度和空间复杂度。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 4, "判断一棵二叉树是否是平衡二叉树。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 5, "给定一个矩阵，从左上角到右下角，只能向右或向下，求路径和最小。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 4, "手写二分查找，考虑边界情况和重复元素。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 3, "反转字符串中的单词。要求原地操作。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 5, "Top K 高频元素，要求时间复杂度优于 O(n log n)。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 4, "合并 K 个有序链表。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 3, "给定一个整数数组，找出所有和为 0 的三元组。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "算法", 4, "下一个排列（LeetCode 31）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),

    # --- 网络 (10) ---
    ("job_interview", "网络", 4, "从浏览器输入 URL 到页面渲染完成，中间发生了什么？（完整链路）", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 5, "HTTPS 握手过程中证书是如何验证的？CA 证书链的作用？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 4, "DNS 解析过程详解，DNS 劫持如何防范？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 3, "GET 和 POST 的区别，POST 和 PUT 的区别。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 4, "HTTP 2.0 的多路复用是如何解决队头阻塞的？HTTP 3.0 为什么用 QUIC？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 5, "TCP 拥塞控制的四种算法（慢启动、拥塞避免、快重传、快恢复）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 3, "Session 和 Cookie 的区别，Token 认证机制。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 4, "WebSocket 和 HTTP 长轮询的区别，什么场景用 WebSocket？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 4, "负载均衡的常见算法（轮询、加权、最小连接、一致性 Hash）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "网络", 5, "CDN 的工作原理，回源策略和缓存策略。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),

    # --- 操作系统 (10) ---
    ("job_interview", "操作系统", 4, "进程间通信方式有哪些？各有什么优缺点？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 5, "select/poll/epoll 的区别，epoll 为什么高效？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 4, "虚拟内存和物理内存的映射关系？页表的作用？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 4, "乐观锁和悲观锁的区别，CAS 的实现原理。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 5, "死锁的四个必要条件，如何避免和排查死锁？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 3, "用户态和内核态的区别，什么时候会发生切换？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 4, "Linux 中文件的权限管理（rwx）和 umask 的作用。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 5, "零拷贝（Zero-Copy）的原理，mmap 和 sendfile 的区别。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 3, "进程和线程的区别，多线程编程需要注意什么？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "操作系统", 4, "Linux 中如何排查 CPU 飙升、内存泄漏、IO 瓶颈？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),

    # --- 数据库 (10) ---
    ("job_interview", "数据库", 5, "MySQL 的 MVCC 实现原理，undo log 和 Read View 的关系。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 4, "MySQL 主从复制的三种模式（异步、半同步、组复制）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 4, "分库分表后，跨分片的查询和事务如何实现？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 5, "Redis 的持久化机制 AOF 和 RDB 的区别，混合持久化怎么工作？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 4, "MySQL 中 varchar 和 char 的区别，text 和 blob 的使用场景。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 3, "索引失效的场景有哪些？如何避免？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 4, "数据库三大范式是什么？实际项目中是否一定要遵循？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 4, "Redis 数据淘汰策略有哪些？LRU 和 LFU 的区别？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 5, "如何设计一个高可用的 MySQL 架构？主备切换和读写分离的挑战。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "数据库", 3, "SQL 注入的原理和防范措施。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),

    # --- Java (10) ---
    ("job_interview", "Java", 4, "Java 内存模型（JMM）和 happens-before 原则。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 5, "G1 垃圾收集器的原理，Region 和 SATB 是什么？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 4, "Spring 循环依赖怎么解决？三级缓存的作用？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 3, "ArrayList 和 LinkedList 的区别，各自的时间复杂度。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 4, "Java 中的锁有哪些？synchronized、ReentrantLock、ReadWriteLock。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 4, "ThreadPoolExecutor 的参数和拒绝策略，如何合理设置线程池大小？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 5, "Netty 的 Reactor 线程模型和 EventLoop 机制。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 3, "Java 中的异常体系，try-catch-finally 的执行顺序。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 4, "MyBatis 的一级缓存和二级缓存的区别和原理。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "Java", 5, "Spring Boot 自动配置原理和 Starter 机制。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),

    # --- 前端 (10) ---
    ("job_interview", "前端", 4, "闭包是什么？有什么优缺点？实际应用场景有哪些？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 4, "原型链和继承的几种方式（原型链继承、构造函数继承、组合继承、ES6 class）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 5, "React 的虚拟 DOM 和 Diff 算法原理。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 4, "跨域问题的解决方案（CORS、JSONP、代理、postMessage）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 3, "CSS 盒模型，box-sizing 的用法。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 5, "Vue 的响应式原理，Vue 2 的 Object.defineProperty 和 Vue 3 的 Proxy。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 3, "防抖和节流的区别，手写实现。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 4, "浏览器缓存机制（强缓存、协商缓存），Service Worker 的作用。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 5, "前端性能优化可以从哪些方面入手？（加载、渲染、运行时）", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "前端", 4, "Event Loop 机制，宏任务和微任务的执行顺序。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),

    # --- 系统设计 (10) ---
    ("job_interview", "系统设计", 5, "如何设计一个支持百亿级消息的即时通讯系统？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 5, "设计一个分布式 ID 生成器，要求全局唯一、趋势递增、高可用。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 4, "如何设计一个日活千万的 Feed 流系统？推拉模式如何选择？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 4, "设计一个 API 网关，需要具备哪些能力？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 5, "设计一个支持海量数据的日志系统（采集、传输、存储、查询）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 4, "如何设计一个可靠的分布式调度系统？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 5, "设计一个高可用配置中心，支持实时推送和版本回滚。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 4, "鉴权系统的设计（RBAC、OAuth 2.0、JWT）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 4, "设计一个排行榜系统，支持实时更新和分段查询。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "系统设计", 3, "微服务架构中服务发现和注册中心的作用（Consul、Nacos、Eureka 对比）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),

    # --- AI/大模型 (10) ---
    ("job_interview", "AI/大模型", 5, "GPT 系列模型的 Scalling Law，模型大小和数据量的关系。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 4, "Fine-tuning 和 Prompt Engineering 的区别，各自适用场景。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 5, "大模型推理优化方法（KV Cache、Flash Attention、量化）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 4, "LoRA 微调的原理？相比 Full Fine-tuning 的优势？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 4, "LangChain 的核心组件和设计思想。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 3, "Prompt 编写的最佳实践，Chain-of-Thought 是什么？", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 4, "Embedding 模型的选择：OpenAI Embedding vs 开源模型（BGE、M3E）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 5, "MoE（Mixture of Experts）架构的原理和优势。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 4, "文本向量化的常见方法（Word2Vec、BERT-Embedding、Sentence-Transformers）。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
    ("job_interview", "AI/大模型", 5, "多模态大模型（CLIP、LLaVA、GPT-4V）的实现思路。", "", "", "", "大厂真题-网络社区", "2025", "real_interview"),
]

# ================================================================
# 2. 开源资料整理 (open_source) — 约 80 道
# ================================================================
OPEN_SOURCE_QUESTIONS = [
    # --- 网络 (10) ---
    ("job_interview", "网络", 3, "OSI 七层模型和 TCP/IP 四层模型分别是什么？为什么分层？", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 4, "TCP 和 UDP 的区别，各自的应用场景。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 4, "TCP 的流量控制和拥塞控制的区别。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 3, "HTTP 常见的状态码有哪些？（1xx、2xx、3xx、4xx、5xx）", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 4, "HTTPS 和 HTTP 的区别，SSL/TLS 握手过程。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 3, "IP 地址分类（A、B、C、D、E 类），子网掩码的作用。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 4, "ARP 协议的作用和工作过程。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 5, "TIME_WAIT 和 CLOSE_WAIT 的区别，大量 TIME_WAIT 如何优化？", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 3, "正向代理和反向代理的区别。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "网络", 4, "HTTP 1.0、1.1、2.0、3.0 的主要改进。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),

    # --- 操作系统 (10) ---
    ("job_interview", "操作系统", 3, "操作系统的四大特征（并发、共享、虚拟、异步）。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 4, "进程调度算法（FCFS、SJF、RR、优先级、多级反馈队列）。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 3, "内存管理方式：分页、分段、段页式。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 4, "页面置换算法（FIFO、LRU、LFU、Clock）。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 5, "文件系统的实现方式，inode 和数据块的关系。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 3, "线程的几种状态和状态转换。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 4, "临界区和锁的概念，自旋锁和互斥锁的区别。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 5, "DMA 技术如何减少 CPU 的 IO 负担？", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 4, "Linux 中软链接和硬链接的区别。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "操作系统", 3, "fork() 系统调用的工作原理，写时复制技术。", "", "", "", "CS-Notes", "2025", "open_source"),

    # --- 计算机基础 (10) ---
    ("job_interview", "计算机基础", 3, "什么是编译和解释？编译型语言和解释型语言的区别。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 3, "什么是编码？ASCII、Unicode、UTF-8 的关系。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 4, "字符编码的发展历程（ASCII → GBK → Unicode → UTF-8）。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 3, "什么是 Base64 编码？应用场景有哪些？", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 4, "大端序和小端序的区别，如何判断机器的字节序？", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 4, "浮点数的 IEEE 754 表示法，为什么 0.1 + 0.2 != 0.3？", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 3, "什么是哈希冲突？常见的解决方案有哪些？", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 4, "布隆过滤器的原理和误判率计算。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 3, "时间复杂度和空间复杂度的概念，常见复杂度排序。", "", "", "", "CS-Notes", "2025", "open_source"),
    ("job_interview", "计算机基础", 4, "正则表达式的常见用法和应用场景。", "", "", "", "CS-Notes", "2025", "open_source"),

    # --- 算法 (10) ---
    ("job_interview", "算法", 3, "数组和链表的区别，各自增删改查的时间复杂度。", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 4, "栈和队列的区别，如何使用栈实现队列？", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 4, "二叉树的遍历方式（前序、中序、后序、层序），递归和迭代实现。", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 4, "动态规划和递归的区别，什么时候用动态规划？", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 5, "Dijkstra 最短路径算法和 Floyd 算法的区别和复杂度。", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 3, "冒泡排序、选择排序、插入排序的原理和时间复杂度。", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 4, "哈希表的底层实现，负载因子和扩容机制。", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 5, "KMP 算法的原理，next 数组如何计算？", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 4, "图的深度优先搜索（DFS）和广度优先搜索（BFS）的对比。", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),
    ("job_interview", "算法", 3, "二分查找的时间复杂度，使用二分查找的前提条件。", "", "", "", "CS-Notes/LeetCode", "2025", "open_source"),

    # --- 数据库 (10) ---
    ("job_interview", "数据库", 4, "MySQL 的 InnoDB 和 MyISAM 存储引擎的区别。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 3, "SQL 中 JOIN 的类型（INNER、LEFT、RIGHT、FULL OUTER）。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 4, "MySQL 的锁机制（行锁、表锁、间隙锁、Next-Key Lock）。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 4, "Redis 的线程模型，为什么单线程还这么快？", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 3, "Redis 的数据结构及底层实现（SDS、ziplist、skiplist）。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 4, "MySQL 的 EXPLAIN 执行计划中 type 字段的含义。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 5, "Kafka 的消息存储和索引机制。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 3, "NoSQL 数据库和关系型数据库的区别，各适用什么场景？", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 4, "数据倾斜的原因和解决方案。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),
    ("job_interview", "数据库", 4, "Redis 的哨兵模式和集群模式的区别。", "", "", "", "JavaGuide/CS-Notes", "2025", "open_source"),

    # --- Java (10) ---
    ("job_interview", "Java", 4, "Java 类加载机制，双亲委派模型的作用。", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 3, "Java 中的 String、StringBuilder、StringBuffer 的区别。", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 4, "Java 集合框架体系，Map 接口的实现类对比。", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 3, "接口和抽象类的区别，各自的使用场景。", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 3, "重载和重写的区别，返回值类型是否可以不同？", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 4, "Java 反射的原理，反射的优缺点。", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 3, "深拷贝和浅拷贝的区别，如何实现深拷贝？", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 4, "Java 8 的 Stream API 和 Lambda 表达式。", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 5, "JVM 调优经验，常见的 GC 参数和调优工具。", "", "", "", "JavaGuide", "2025", "open_source"),
    ("job_interview", "Java", 3, "Java 中 final、finally、finalize 的区别。", "", "", "", "JavaGuide", "2025", "open_source"),

    # --- 前端 (10) ---
    ("job_interview", "前端", 3, "var、let、const 的区别，变量提升是什么？", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 4, "箭头函数和普通函数的区别（this 指向、arguments、new）。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 3, "CSS 选择器的优先级（权重计算规则）。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 4, "Flex 布局和 Grid 布局的区别和适用场景。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 4, "Promise 的三种状态，手写 Promise.all 和 Promise.race。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 5, "Vue 的虚拟 DOM 和 Diff 算法（patch 过程）。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 4, "React Hooks 的使用规则，useEffect 和 useLayoutEffect 的区别。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 3, "localStorage、sessionStorage、Cookie 的区别。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 5, "Webpack 的构建流程和 Loader/Plugin 的区别。", "", "", "", "前端开源资料", "2025", "open_source"),
    ("job_interview", "前端", 4, "TypeScript 中 interface 和 type 的区别。", "", "", "", "前端开源资料", "2025", "open_source"),

    # --- 系统设计 (10) ---
    ("job_interview", "系统设计", 3, "RESTful API 的设计规范。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 4, "CAP 定理和 BASE 理论，分布式系统如何取舍？", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 4, "分布式事务的解决方案（2PC、TCC、Saga、Seata）。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 3, "消息队列的作用（解耦、异步、削峰），RabbitMQ vs Kafka。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 4, "幂等设计的常见方案（唯一ID、状态机、去重表）。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 4, "熔断、降级、限流的区别和实现方式（Hystrix、Sentinel）。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 5, "ZooKeeper 的 Zab 协议，和 Raft 协议的区别。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 4, "分布式缓存和本地缓存结合使用的策略。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 3, "什么是服务网格（Service Mesh）？Istio 的核心组件。", "", "", "", "系统设计开源资料", "2025", "open_source"),
    ("job_interview", "系统设计", 4, "蓝绿部署、灰度发布、滚动更新的区别和适用场景。", "", "", "", "系统设计开源资料", "2025", "open_source"),
]

# ================================================================
# 3. AI 系统整理 (ai_generated) — 约 505 道
# ================================================================
AI_QUESTIONS = [
    # --- 网络: +47 (目标 13→80, 已有 33) ---
    ("job_interview", "网络", 3, "什么是 NAT？有什么作用？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "DHCP 协议的工作原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "什么是 VLAN？为什么要划分 VLAN？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "ICMP 协议的作用，ping 命令的原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 5, "BGP 和 OSPF 路由协议的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "常见的 HTTP 请求方法有哪些？各自的特点。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "什么是跨域资源共享（CORS）？简单请求和预检请求的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "Cookie 的属性有哪些（Domain、Path、Secure、HttpOnly、SameSite）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "WebSocket 的握手过程和数据帧格式。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 5, "QUIC 协议如何解决 TCP 的队头阻塞问题？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "XSS 攻击的原理和防范措施。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "CSRF 攻击的原理和防范措施。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "JWT 的结构和认证流程，JWT 和 Session 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "OAuth 2.0 的四种授权模式。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "什么是长连接和短连接？Keep-Alive 的作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 5, "TCP 的 SYN Flood 攻击原理和防御措施。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "HTTP 的内容协商机制（Accept、Content-Type）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "IPv4 和 IPv6 的区别，IPv6 的优势。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "什么是 TCP 粘包？如何解决？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "网关和路由器的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "HTTP/2 的 HPACK 头部压缩原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "什么是 DNS 污染？如何检测和防范？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "正向代理和反向代理的应用场景举例。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 5, "TCP 的 SYN-ACK 重试机制和超时计算。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "什么是 HTTP 的长轮询（Long Polling）？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "SSL/TLS 1.2 和 1.3 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "什么是网络隔离？VPN 的原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "内容分发网络（CDN）的缓存策略有哪几种？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 5, "HTTP/3 为什么选择 UDP 而不是 TCP？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "什么是 REST API 的幂等性？哪些 HTTP 方法是幂等的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "SSE（Server-Sent Events）和 WebSocket 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "HTTP 的缓存控制头有哪些（Cache-Control、Expires、ETag、Last-Modified）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 5, "TCP Fast Open（TFO）的原理和优势。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 4, "gRPC 和 RESTful API 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "网络", 3, "什么是 MAC 地址？和 IP 地址的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 计算机基础: +59 (目标 11→70, 已有 11, need +59) ---
    ("job_interview", "计算机基础", 3, "计算机中为什么使用补码表示负数？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是冯诺依曼架构？主要组成部分有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 Cache？Cache 的局部性原理是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "CPU 的流水线技术，流水线冒险有哪几种？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "二进制、八进制、十进制、十六进制之间的转换方法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是线程安全？如何实现线程安全？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是 Race Condition？如何避免？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是缓存一致性协议（MESI）？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 5, "CPU 的乱序执行和内存屏障。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是尾递归？尾递归优化的原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是动态链接和静态链接？它们的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 CRC 校验？和 MD5 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "RISC 和 CISC 指令集架构的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 RAID？RAID 0/1/5/10 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 5, "虚拟化技术的原理，Hypervisor 的类型。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 Docker？Docker 和虚拟机的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "容器和镜像的关系，Dockerfile 的最佳实践。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 Kubernetes？Pod 和 Node 的关系。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "Kubernetes 的 Service 类型（ClusterIP、NodePort、LoadBalancer）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 DevOps？CI/CD 的核心流程。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "Git 的工作流程，Git Flow 和 Trunk-Based 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 HTTPS 证书？如何获取和部署？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 JSON 和 XML？对比它们的优缺点。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "Protocol Buffers 和 JSON 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 RPC？RPC 和 HTTP 调用的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是 YAML？YAML、JSON、TOML 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是分布式跟踪？OpenTelemetry 的核心概念。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 WebSocket？和应用层长轮询的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是幂等？HTTP 方法中哪些是幂等的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 5, "什么是 CAS（Compare And Swap）？ABA 问题如何解决？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 RESTful API？设计原则有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "GraphQL 和 REST 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是短路求值？在编程中的应用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是 ORM？ORM 的优缺点。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是测试驱动开发（TDD）？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "单元测试、集成测试、端到端测试的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是设计模式？常见的设计模式分类。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "单例模式的实现方式（饿汉、懒汉、双重检查、静态内部类、枚举）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是工厂模式？简单工厂和抽象工厂的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "观察者模式和发布-订阅模式的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是依赖注入？为什么要用依赖注入？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是面向对象编程的四大特性？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "函数式编程和面向对象编程的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是纯函数？纯函数的特点和优势。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 REST 和 GraphQL？各自适用场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是 WebAssembly（Wasm）？和 JavaScript 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 API 版本管理？常见的版本策略。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是 Serverless？FaaS 和 BaaS 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "Elasticsearch 的倒排索引原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 NoSQL？四种 NoSQL 数据库类型。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是数据仓库？和数据库的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 OLTP 和 OLAP？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是 MapReduce？其核心思想。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是数据湖？和数据仓库的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是 Lambda 架构和 Kappa 架构？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是蓝绿部署？如何实现零停机部署？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "什么是混沌工程？Netflix Chaos Monkey 的原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 3, "什么是 TDD？和传统开发流程的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "计算机基础", 4, "如何对系统进行容量评估和压测？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 操作系统: +53 (目标 17→70, 已有 20, need +50) ---
    ("job_interview", "操作系统", 4, "什么是内核态和用户态？为什么需要这两种状态？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "系统调用的执行过程。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "进程控制块（PCB）中包含哪些信息？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "线程的实现方式（用户级线程 vs 内核级线程）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是上下文切换？切换的开销来自哪里？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 OOM Killer 机制，如何调整？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是内存碎片？内部碎片和外部碎片的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是交换空间（Swap）？Swap 的优缺点。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中 top、htop、vmstat、iostat 命令的用法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是中断？中断和异常的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 cgroups 和 namespace 的作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是文件描述符？ulimit 的作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中 /proc 文件系统的作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 IO 模型（阻塞、非阻塞、IO 多路复用、信号驱动、异步 IO）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是共享内存？和消息队列的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是信号量？二值信号量和计数信号量的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是管道（Pipe）？匿名管道和命名管道的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 的 inode 是什么？inode 耗尽怎么办？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是 Shell？常见的 Shell 类型。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 NUMA 架构对性能的影响。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是守护进程？如何创建守护进程？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中如何设置定时任务（cron、at、systemd timer）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是 mmap？mmap 和 read/write 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是 Bash？.bashrc 和 .bash_profile 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 epoll 的 LT 和 ET 模式的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是 CPU 亲和性？taskset 命令的用法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是系统负载（Load Average）？如何解读？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 的日志系统（syslog、rsyslog、journald）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是 SELinux？它的作用和基本概念。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是缓冲区溢出？如何防范？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中如何查看系统的启动日志和内核日志？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "什么是 eBPF？它的应用场景有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是 Linux 的 runlevel 和 systemd target？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是文件系统的 journal（日志）功能？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中如何配置网络（ip、ifconfig、nmcli）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是 SSH？SSH 的认证方式有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是 LVM？LVM 的优势。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 Performance Tuning 常用参数（sysctl）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是僵尸进程？如何避免和清理？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是孤儿进程？和僵尸进程的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 的 nice 值和进程优先级的关系。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 Control Groups（cgroups v1 vs v2）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是 Linux 的 .bashrc 文件？修改后如何生效？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中如何管理 systemd 服务？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是 sudo？/etc/sudoers 文件的配置。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 内核的 RCU（Read-Copy-Update）机制。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中如何排查磁盘 IO 瓶颈（iostat、iotop）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "什么是 Linux 的 tmpfs？和 ramdisk 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是 NFS？NFS 的工作原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "Linux 中 /etc/fstab 文件的作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 5, "Linux 的 BPF 和传统内核模块的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 3, "Linux 中如何查看磁盘分区和挂载情况？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "操作系统", 4, "什么是 CPU 的 Hyper-Threading（超线程）？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 算法: +45 (目标 25→70, 已有 25, need +45) ---
    ("job_interview", "算法", 4, "堆排序的原理和时间复杂度。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "计数排序的原理和适用场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "桶排序的原理，什么时候用桶排序？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "基数排序的原理和时间复杂度。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "滑动窗口算法的核心思想，适用场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "编辑距离（Levenshtein Distance）的动态规划解法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "什么是回文？判断字符串是否为回文。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "最长公共子序列（LCS）的动态规划解法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "最长递增子序列（LIS）的 O(n log n) 解法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "什么是贪心算法？和动态规划的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "Manacher 算法求最长回文子串。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "前缀和和差分数组的应用场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "什么是并查集？路径压缩和按秩合并。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "Trie 树的实现和应用场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "线段树的原理和基本操作。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "什么是拓扑排序？在什么场景下使用？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "A* 搜索算法的原理和启发式函数的设计。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "什么是二分搜索？二分搜索的变种有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "在旋转排序数组中搜索（LeetCode 33）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "接雨水（LeetCode 42）的多种解法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "和为 K 的子数组（LeetCode 560），前缀和 + 哈希表优化。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "乘积最大子数组（LeetCode 152）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "移动零（LeetCode 283），要求原地操作。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "找到所有数组中消失的数字（LeetCode 448），O(1) 空间。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "正则表达式匹配（LeetCode 10），动态规划。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "全排列（LeetCode 46），回溯算法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "子集（LeetCode 78），位运算和回溯。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "两数之和（LeetCode 1），O(n) 解法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "三数之和（LeetCode 15），排序+双指针。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "N 皇后问题（LeetCode 51），回溯。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "爬楼梯（LeetCode 70），动态规划。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "最大子数组和（LeetCode 53），Kadane 算法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "环形链表 II（LeetCode 142），快慢指针找环入口。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "相交链表（LeetCode 160），双指针或哈希集。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "二叉树中的最大路径和（LeetCode 124），后序遍历。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "验证二叉搜索树（LeetCode 98），中序遍历。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "对称二叉树（LeetCode 101），递归。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "二叉树的最近公共祖先（LeetCode 236）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "实现 Trie（LeetCode 208）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "有效的括号（LeetCode 20），栈。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "每日温度（LeetCode 739），单调栈。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 5, "LFU 缓存（LeetCode 460），双向链表+哈希表。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "颜色分类（LeetCode 75），荷兰国旗问题。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 4, "寻找重复数（LeetCode 287），快慢指针。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "算法", 3, "买卖股票的最佳时机（LeetCode 121）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 前端: +40 (目标 20→60, 已有 20, need +40) ---
    ("job_interview", "前端", 3, "什么是 CSS 的 BFC？如何触发 BFC？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "CSS 水平垂直居中的几种方式。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "HTML5 的新特性有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是语义化 HTML？为什么重要？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "JS 中 this 关键字的指向规则。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "JS 中 async/await 的实现原理，和 Promise 的关系。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "== 和 === 的区别，类型转换规则。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "JS 中的深拷贝实现方法（JSON.parse/JSON.stringify 的局限性）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是事件冒泡和事件捕获？如何阻止事件传播？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "let、const、var 的区别，暂时性死区是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是柯里化？手写一个柯里化函数。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "React 中的 key 的作用和原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "React 的 useState 的 batch update 机制。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "React 的 useMemo 和 useCallback 的区别和使用场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "React 的受控组件和非受控组件。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "Vue 的 computed 和 watch 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "Vue 的 v-if 和 v-show 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "Vue 的 nextTick 的实现原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "Vue Router 的 hash 模式和 history 模式的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "CSS 的伪类和伪元素的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是 CSS 预处理器？Sass/SCSS 和 Less 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "Webpack 的 Tree Shaking 原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "Vite 和 Webpack 的区别，Vite 为什么快？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "什么是 CDN？前端项目中如何使用 CDN？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "前端项目的代码规范工具链（ESLint、Prettier、Husky）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是 PWA？核心技术有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "什么是 SSR 和 CSR？各自优缺点。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "Next.js 的 SSR 和 ISR 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是微前端？常见的实现方案。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "TypeScript 的泛型约束，keyof 和 typeof 的用法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "TypeScript 的工具类型（Partial、Required、Pick、Omit、Record）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "什么是跨平台开发？React Native 和 Flutter 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是前端监控？错误监控和性能监控的实现方式。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "前端安全：XSS、CSRF、点击劫持的详细防护。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "什么是 ES Module 和 CommonJS 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "浏览器渲染流程（DOM Tree、CSSOM、Render Tree、Layout、Paint）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "什么是回流（Reflow）和重绘（Repaint）？如何减少回流？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 3, "什么是懒加载和预加载？实现方式。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 5, "React 18 的 Concurrent Mode 和 Suspense。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "前端", 4, "Vue 3 的 Composition API 和 Vue 2 的 Options API 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 系统设计: +45 (目标 25→70, 已有 30, need +40) ---
    ("job_interview", "系统设计", 4, "从 1 到 10 万 QPS，架构各阶段需要做什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个秒杀系统，需要考虑哪些关键点？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个分布式锁，有哪些实现方式？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "如何设计一个支持海量数据的搜索引擎？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个支付系统，需要考虑哪些关键点？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "如何设计一个实时数仓？Lambda 和 Kappa 架构的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 3, "什么是 CQRS？什么场景下使用？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个通知系统（邮件、短信、推送）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "什么是事件驱动架构？和请求驱动架构的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "如何设计一个支持全球部署的分布式系统？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 3, "什么是读写分离？主从延迟怎么解决？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个评论系统（盖楼、排序、防刷）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "什么是异地多活？常见的多活架构模式。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "设计一个支持无限扩容的分布式存储系统。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 3, "什么是 API 网关？网关的常见功能。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个 URL 短链服务，并考虑高性能场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "什么是 SAGA 模式？Choreography 和 Orchestration 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "如何设计一个多租户（Multi-Tenant）系统？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 3, "什么是缓存穿透、击穿、雪崩？各自的解决方案。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个图片上传和处理的系统（缩略图、水印、CDN）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "什么是断路器模式？和限流的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个基于位置的服务（LBS）系统（附近的人）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "设计一个配置中心，支持实时推送和版本回滚。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 3, "什么是服务降级？什么场景下触发降级？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个分布式链路跟踪系统（类似 Dapper/Zipkin）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "如何在微服务间保证数据最终一致性？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "设计一个支持千万级并发的 WebSocket 推送系统。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "什么是 Sidecar 模式？和 Service Mesh 的关系。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 4, "设计一个搜索自动补全系统（类似 Google Suggest）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 5, "设计一个飞书/钉钉式的企业 IM 系统。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "系统设计", 3, "灰度发布的常见策略（金丝雀发布、A/B 测试、蓝绿部署）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 数据库: +37 (目标 33→70, 已有 43, need +27) ---
    ("job_interview", "数据库", 4, "MySQL 的日志系统（binlog、redo log、undo log）各有什么作用？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 3, "DELETE、TRUNCATE、DROP 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "MySQL 两阶段提交保证主从数据一致性。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "MySQL 的 count(*)、count(1)、count(column) 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 5, "MySQL 的 MRR（Multi-Range Read）优化。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 3, "UNION 和 UNION ALL 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "HAVING 和 WHERE 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "MySQL 的 ICP（Index Condition Pushdown）优化。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 5, "MySQL 死锁的排查和解决方案。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 3, "SQL 优化的一般步骤和方法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "MySQL 的 JOIN 底层实现原理（Nested Loop Join、Hash Join）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "Redis 的发布订阅和 Stream 数据结构的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 3, "Redis 的事务机制和 Lua 脚本。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 5, "Kafka 的日志清理策略（delete 和 compact）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "Kafka 的分区分配策略（RangeAssignor、RoundRobinAssignor、StickyAssignor）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 3, "MongoDB 和 MySQL 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "MongoDB 的聚合管道和索引。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "Elasticsearch 和 MySQL 的配合使用场景。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "如何设计数据库表来存储树形结构？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 3, "什么是数据库连接池？为什么要使用连接池？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 5, "MySQL 的 Adaptive Hash Index 的原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "Redis 6.0 的多线程 IO 模型。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 3, "Redis 的 Big Key 问题如何发现和解决？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "Redis 的热 key 问题如何发现和解决？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 5, "Kafka 的 ISR 机制和 HW/LEO 的作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "数据库表的设计原则和反范式设计。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "数据库", 4, "如何设计一个支持多维度查询的数据库方案？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- Java: +28 (目标 42→70, 已有 42, need +28) ---
    ("job_interview", "Java", 4, "Java 中 wait() 和 sleep() 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 3, "Java 中 Comparable 和 Comparator 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Java 中 volatile 和 synchronized 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 5, "Java 的 happens-before 规则有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Java 的 WeakReference、SoftReference、PhantomReference 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 5, "JVM 的垃圾回收算法（标记-清除、标记-整理、复制）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 3, "Java 中 equals() 和 hashCode() 的约定。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Java 泛型的类型擦除，如何获取运行时类型信息？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 3, "Java 中 static 关键字的用法和作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Java 中的内部类（成员内部类、静态内部类、局部内部类、匿名内部类）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 5, "JVM 的类加载过程（加载、验证、准备、解析、初始化）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Spring 的 IOC 容器原理，Bean 的生命周期。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Spring AOP 的实现原理（JDK 动态代理 vs CGLIB）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Spring 的事务传播行为有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 5, "Spring MVC 的处理流程（DispatcherServlet 的工作过程）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 3, "MyBatis 中 #{} 和 ${} 的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "MyBatis 的缓存机制（一级缓存、二级缓存）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Java 的四种引用类型在 Android/内存优化中的应用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 5, "G1 GC 的 Mixed GC 过程。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Java 8 的 Optional 类的作用和用法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 3, "Java 中的多态实现原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "线程间通信的方式（wait/notify、Condition、LockSupport）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 5, "Disruptor 无锁队列的原理。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Fork/Join 框架的原理和工作窃取算法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Java NIO 的核心组件（Channel、Buffer、Selector）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 5, "Netty 的 ByteBuf 和 JDK ByteBuffer 的对比。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 3, "Java 中如何创建不可变类？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "Java", 4, "Spring Boot 的 Actuator 和生产监控。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- AI/大模型: +24 (目标 46→70, 已有 60, need +10) ---
    ("job_interview", "AI/大模型", 4, "大模型的 Token 和上下文窗口是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 3, "什么是 Few-Shot、Zero-Shot、One-Shot Learning？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 4, "什么是指令微调（Instruction Tuning）？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 5, "RM（Reward Model）在 RLHF 中的作用。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 4, "大模型的幻觉问题（Hallucination）如何缓解？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 5, "MHA（Multi-Head Attention）、MQA（Multi-Query Attention）、GQA（Grouped Query Attention）的区别。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 3, "什么是 Embedding 和 Tokenization？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 4, "大模型部署的推理优化方法（vLLM、TensorRT-LLM）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 4, "Multi-Agent 系统中 Agent 间的通信协议和协调机制。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "AI/大模型", 5, "MoE 模型的负载均衡问题和专家选择策略。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 项目深挖/行为面试: +33 (目标 27→60, 已有 27, need +33) ---
    ("job_interview", "项目深挖/行为面试", 3, "你为什么想做技术？当初是怎么入行的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你最喜欢的编程语言是什么？为什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你是如何保持技术学习的？有什么学习习惯？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你和同事发生过技术分歧吗？怎么解决的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你的优点和缺点分别是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "如果让你重新做一个项目，你会怎么改进？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你为什么离开上一家公司？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你如何看待加班？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你对薪资的期望是多少？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你有没有带过新人？怎么带的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 5, "描述一次你推动的重大技术变革或项目重构。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你遇到的最大挫折是什么？怎么走出来的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你是如何看待技术债的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你的项目延期过吗？原因是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你觉得一个好的技术方案应该具备哪些特征？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你平时关注哪些技术社区和博客？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你做过的最自豪的一个技术决策是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "如果你发现同事的代码有严重 bug，你会怎么做？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你是如何做技术方案的选型的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你希望从团队和上级那里得到什么样的支持？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你怎么看待代码评审（Code Review）？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 5, "描述一次你如何在项目中推动质量改进的经历。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你如何处理多个任务并行的情况？优先级怎么排？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你使用过哪些项目管理工具？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你是如何做技术分享的？有没有写过技术博客？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "如果让你设计一套新人培训体系，你会怎么做？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你认为优秀工程师的特质是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 5, "你如何衡量自己代码的质量？有什么量化方法？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "如果产品的需求不合理，你会怎么和产品经理沟通？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 3, "你在跨部门协作中遇到过什么困难？怎么解决的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你如何评估一个第三方库/框架是否值得引入项目？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 5, "你有没有推动过团队的技术规范建设？具体做了哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("job_interview", "项目深挖/行为面试", 4, "你怎么理解「ownership」？在项目中你是怎么体现的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 雅思口语 (25) ---
    ("ielts_speaking", "雅思口语", 3, "Describe your hometown. What is it famous for?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "What do you like to do in your free time?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe a book that you have recently read.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "Do you prefer to work alone or in a team?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe a memorable journey you have taken.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "What is your favorite season and why?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe a person who has influenced you greatly.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "How has technology changed the way people communicate?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 5, "Describe a piece of advice that was useful to you.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "What kind of music do you enjoy?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe a skill that you want to learn in the future.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "Do you think it's important to have a healthy lifestyle?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe a movie that made you think deeply.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 5, "What are the advantages and disadvantages of social media?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe a goal you have set for yourself.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "How often do you use the internet? For what purposes?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe a traditional festival in your country.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Do you think cities or the countryside is better for living?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 5, "Describe a time when you helped someone.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "What is your favorite way to relax?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "Describe an important decision you have made.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "How has education changed in your country in recent years?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 3, "Do you prefer reading books or watching movies? Why?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 5, "Describe a challenge you overcame.", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("ielts_speaking", "雅思口语", 4, "What role do you think artificial intelligence will play in our daily lives?", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 公务员 (25) ---
    ("civil_service", "公务员面试", 4, "你为什么要报考公务员？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "请做一个简短的自我介绍。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 5, "如何处理群众上访问题？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "领导和同事之间有矛盾，你怎么办？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "谈谈你对'为人民服务'的理解。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "工作中遇到不配合的同事，你怎么处理？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 5, "谈谈你对当前社会热点问题的看法（如人口老龄化）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "你最大的优点和缺点是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "如何看待基层工作？你愿意去基层吗？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "你的职业规划是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "领导交办的任务超出了你的能力范围，你怎么办？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 5, "如何组织一次大型会议或活动？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "谈谈你对纪律和自由的看法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "你认为公务员应具备哪些素质？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "如何提高政府工作效率？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 5, "遇到突发事件（如自然灾害）你怎么应急处置？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "谈谈你对诚信的理解。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "如果你的意见和领导不一致，你怎么做？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "如何看待形式主义？如何避免？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 5, "如何平衡工作效率和工作质量？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "谈谈你对团队合作的理解。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "你如何看待加班？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 5, "如何应对群众的不合理诉求？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 4, "如何做调研？调研的步骤和方法。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("civil_service", "公务员面试", 3, "你对应聘的岗位有什么了解？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 考研复试 (25) ---
    ("graduate_school", "考研复试", 4, "你为什么选择考研？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 3, "请做一下自我介绍（本科经历、学术兴趣）。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "谈谈你的本科毕业设计。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 5, "你对目前的研究方向有什么了解？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 3, "你为什么选择我们学校/专业？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你读过哪些专业相关的书籍或论文？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 5, "谈谈你对研究生阶段科研工作的规划。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你在本科期间参加过什么科研项目？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你如何评价自己的学习能力？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 3, "你未来想从事什么职业？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "谈谈你的缺点和不足。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 5, "如果这次没有被录取，你怎么办？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你在团队合作中通常扮演什么角色？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 3, "你最喜欢的一门本科课程是什么？为什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "介绍一个你感兴趣的学术问题。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 3, "你如何安排自己的学习时间？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你掌握的实验技能或编程技能有哪些？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "谈谈你对学术诚信的理解。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 5, "描述一次你解决复杂问题的经历。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 3, "你平时有什么兴趣爱好？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你在本科期间获得过什么奖项？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你是如何了解我们学校这个专业的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 3, "你比较喜欢理论研究还是应用实践？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 5, "介绍一个你熟悉的学术领域的最新进展。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("graduate_school", "考研复试", 4, "你认为自己最大的优势是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- MBA (24) ---
    ("mba_interview", "MBA面试", 4, "你为什么选择读 MBA？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 3, "请做一个商务自我介绍。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 5, "谈谈你所在公司的商业模式和核心竞争力。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你经历过的最大的管理挑战是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 3, "你的领导风格是什么样的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 5, "如何进行行业分析和市场调研？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你怎么看待当前的经济形势？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 5, "如何制定公司战略？你有什么实际经验？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你如何激励团队成员？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你经历过的最艰难的决策是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 3, "你对未来五年的职业规划是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 5, "如何看待公司的财务指标（ROE、毛利率等）？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "如何管理跨部门项目？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你最敬佩的企业家是谁？为什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 3, "你觉得你的同事怎么评价你？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 5, "说说你在公司推行的一个成功的变革。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你是怎么做团队目标的拆解和落地的？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "如何权衡短期业绩和长期发展？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 3, "你认为优秀的领导者应该具备哪些特质？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 5, "说说你如何在资源有限的情况下完成目标。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你对数字化转型有什么理解？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你所在行业的竞争格局如何？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 3, "你为什么选择我们学校的 MBA 项目？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("mba_interview", "MBA面试", 4, "你如何处理团队内的冲突？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),

    # --- 教资 (25) ---
    ("teacher_cert", "教资面试", 4, "你为什么想当老师？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 3, "请做一个简短的自我介绍。", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 5, "如果学生在课堂上扰乱秩序，你怎么处理？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如何激发学生的学习兴趣？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 3, "你认为好老师的标准是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如果学生成绩不理想，家长来找你沟通，你怎么办？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 5, "如何设计一堂 45 分钟的课？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如何看待素质教育？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 3, "你对教师这个职业有什么理解？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如何处理班上的优等生和后进生？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 5, "如果教学中发现教材有错误，你怎么处理？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 3, "你在教学中的优势和劣势分别是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如何与同事协作开展教研活动？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 3, "你如何看待师德师风？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "你对新课改有什么理解？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 5, "你在班级管理中遇到的最大挑战是什么？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如何帮助学生克服考试焦虑？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 3, "你如何处理校园欺凌事件？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如何布置作业才能既有效又不增加学生负担？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "你如何看待家庭教育的作用？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 5, "如果你教的班级成绩始终不好，你怎么办？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 3, "你最喜欢的教育家是谁？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "如何利用信息技术辅助教学？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 5, "如何评价学生的综合素质？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
    ("teacher_cert", "教资面试", 4, "你认为学校应该如何培养学生的创新精神？", "", "", "", "面试成长伴侣-整理", "2025", "ai_generated"),
]

# ================================================================
# 导入函数
# ================================================================
SCENARIO_MAP = {
    "job_interview": "求职面试",
    "teacher_cert": "教资面试",
    "ielts_speaking": "雅思口语",
    "civil_service": "公务员面试",
    "graduate_school": "考研复试",
    "mba_interview": "MBA面试",
}


def import_questions(db, questions, source_type_label):
    """导入一组题目"""
    count = 0
    skipped = 0
    for q in questions:
        scenario, category, difficulty, question_text, reference_answer, company, position, source, year, st = q
        if st != source_type_label:
            st = source_type_label
        result = db.add_question(
            scenario_id=scenario,
            category=category,
            difficulty=difficulty,
            question_text=question_text,
            reference_answer=reference_answer,
            tags=[category, SCENARIO_MAP.get(scenario, scenario)],
            company=company,
            position=position,
            source=source,
            year=year,
            source_type=st,
        )
        if result["success"]:
            count += 1
        else:
            skipped += 1
    return count, skipped


def main():
    db = DatabaseManager()

    # 查当前统计
    before = len(db.get_questions())
    print("=" * 60)
    print("  题库扩充")
    print("=" * 60)
    print("当前题量: %d" % before)

    total = 0
    total_skipped = 0

    # 导入真实面经
    print("\n--- [1/3] 真实面经题 (real_interview) ---")
    c, s = import_questions(db, REAL_INTERVIEW_QUESTIONS, "real_interview")
    total += c
    total_skipped += s
    print("  导入 %d 道 (跳过 %d)" % (c, s))

    # 导入开源资料题
    print("\n--- [2/3] 开源资料题 (open_source) ---")
    c, s = import_questions(db, OPEN_SOURCE_QUESTIONS, "open_source")
    total += c
    total_skipped += s
    print("  导入 %d 道 (跳过 %d)" % (c, s))

    # 导入 AI 整理题
    print("\n--- [3/3] AI 整理题 (ai_generated) ---")
    c, s = import_questions(db, AI_QUESTIONS, "ai_generated")
    total += c
    total_skipped += s
    print("  导入 %d 道 (跳过 %d)" % (c, s))

    # 最终统计
    after = len(db.get_questions())
    print("\n" + "=" * 60)
    print("  扩充完成报告")
    print("=" * 60)
    print("  新导入: %d 道 (跳过 %d 道重复)" % (total, total_skipped))
    print("  扩充前: %d 道" % before)
    print("  扩充后: %d 道" % after)

    # 按来源类型统计
    print("\n--- 按来源类型分布 ---")
    conn = db._get_conn()
    try:
        rows = conn.execute(
            "SELECT source_type, COUNT(*) as cnt FROM questions GROUP BY source_type"
        ).fetchall()
        for r in rows:
            print("  %s: %d 道" % (r["source_type"], r["cnt"]))
    finally:
        conn.close()

    # 按分类统计（仅 job_interview）
    print("\n--- job_interview 分类分布 ---")
    conn2 = db._get_conn()
    try:
        rows = conn2.execute(
            "SELECT category, COUNT(*) as cnt FROM questions WHERE scenario_id='job_interview' GROUP BY category ORDER BY cnt"
        ).fetchall()
        for r in rows:
            bar = "#" * (r["cnt"] // 2)
            print("  %-20s %3d  %s" % (r["category"], r["cnt"], bar))
    finally:
        conn2.close()


if __name__ == "__main__":
    main()
