"""
种子题库生成器 - 生成完整种子题库 JSON 文件

包含所有 6 个场景的已知真实面试题。
来源标注为已知的开源项目、面经汇总、社区来源。
"""

import json
import os
from datetime import datetime


def generate_seed_file(output_path: str):
    """
    生成完整的种子题库 JSON 文件

    Args:
        output_path: 输出文件路径
    """
    questions = []

    # ================================================================
    # job_interview - 求职面试（约 80 题）
    # ================================================================
    job_questions = [
        # --- 行为面试 ---
        {"q": "请做一个简短的自我介绍。", "cat": "行为面试", "diff": 1, "freq": 5, "occ": 5, "src": "大厂通用面经", "co": "通用"},
        {"q": "请介绍你最熟悉的一个项目，你在其中负责什么？", "cat": "项目深挖", "diff": 2, "freq": 5, "occ": 4, "src": "字节跳动面经", "co": "通用"},
        {"q": "你的职业规划是什么？", "cat": "行为面试", "diff": 1, "freq": 5, "occ": 5, "src": "HR面通用题", "co": "通用"},
        {"q": "你最大的优点和缺点是什么？", "cat": "行为面试", "diff": 1, "freq": 5, "occ": 4, "src": "HR面通用题", "co": "通用"},
        {"q": "你遇到过最大的技术挑战是什么？如何解决的？", "cat": "项目深挖", "diff": 2, "freq": 5, "occ": 4, "src": "字节跳动/阿里面经", "co": "通用"},
        {"q": "你为什么离开上一家公司？", "cat": "行为面试", "diff": 1, "freq": 4, "occ": 4, "src": "HR面通用题", "co": "通用"},
        {"q": "请介绍一下你对我们公司和这个岗位的理解。", "cat": "行为面试", "diff": 2, "freq": 4, "occ": 4, "src": "面试通用题", "co": "通用"},
        {"q": "如果让你重新设计这个项目，你会怎么做？", "cat": "项目深挖", "diff": 3, "freq": 4, "occ": 3, "src": "字节跳动面经", "co": "字节跳动"},
        {"q": "你在项目中有没有做过技术选型？你是如何做决策的？", "cat": "项目深挖", "diff": 3, "freq": 4, "occ": 3, "src": "美团面经", "co": "通用"},
        {"q": "你有没有带过新人或小团队？如何管理的？", "cat": "行为面试", "diff": 2, "freq": 3, "occ": 3, "src": "腾讯面经", "co": "通用"},
        {"q": "你是如何处理与产品经理/同事之间的分歧的？", "cat": "行为面试", "diff": 2, "freq": 3, "occ": 3, "src": "HR面通用题", "co": "通用"},
        {"q": "你期望的薪资是多少？", "cat": "行为面试", "diff": 1, "freq": 4, "occ": 4, "src": "HR面通用题", "co": "通用"},
        {"q": "你有什么想问我们的？", "cat": "行为面试", "diff": 1, "freq": 5, "occ": 5, "src": "面试通用题", "co": "通用"},

        # --- Java ---
        {"q": "HashMap 1.7 vs 1.8 底层实现差异？为什么线程不安全？", "cat": "Java", "diff": 3, "freq": 5, "occ": 5, "src": "JavaGuide", "co": "通用"},
        {"q": "ConcurrentHashMap 如何保证并发安全？1.7 分段锁 vs 1.8 CAS+Synchronized", "cat": "Java", "diff": 4, "freq": 5, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "volatile 的作用？能否保证原子性？内存语义是什么？", "cat": "Java", "diff": 3, "freq": 4, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "JVM 的内存区域划分？哪些线程私有哪些共享？", "cat": "Java", "diff": 3, "freq": 5, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "垃圾回收算法有哪些？CMS 和 G1 的区别？", "cat": "Java", "diff": 3, "freq": 4, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "Spring Boot 自动配置的原理是什么？", "cat": "Java", "diff": 3, "freq": 4, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "Spring IOC 和 AOP 的设计原理？AOP 有哪些应用场景？", "cat": "Java", "diff": 3, "freq": 5, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "MyBatis 中 #{} 和 ${} 的区别？", "cat": "Java", "diff": 2, "freq": 4, "occ": 3, "src": "JavaGuide", "co": "通用"},
        {"q": "线程池的核心参数有哪些？如何合理设置线程池大小？", "cat": "Java", "diff": 3, "freq": 5, "occ": 4, "src": "JavaGuide/面经", "co": "通用"},
        {"q": "了解 ThreadLocal 吗？它的内存泄漏问题是什么？", "cat": "Java", "diff": 3, "freq": 4, "occ": 3, "src": "JavaGuide", "co": "通用"},
        {"q": "Java 类加载机制是怎样的？什么是双亲委派模型？", "cat": "Java", "diff": 3, "freq": 4, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "CAS 的原理和 ABA 问题如何解决？", "cat": "Java", "diff": 3, "freq": 4, "occ": 3, "src": "JavaGuide", "co": "通用"},
        {"q": "synchronized 的底层实现？锁升级的过程？", "cat": "Java", "diff": 4, "freq": 4, "occ": 3, "src": "面经-Java", "co": "通用"},
        {"q": "NIO/BIO/AIO 的区别？Netty 的线程模型？", "cat": "Java", "diff": 4, "freq": 3, "occ": 3, "src": "面经-Java", "co": "通用"},

        # --- 数据库 ---
        {"q": "MySQL 索引底层为什么用 B+ 树而不是 B 树或红黑树？", "cat": "数据库", "diff": 3, "freq": 5, "occ": 5, "src": "JavaGuide/CS-Notes", "co": "通用"},
        {"q": "MySQL 中有哪些锁？行锁、表锁、间隙锁分别适用于什么场景？", "cat": "数据库", "diff": 3, "freq": 4, "occ": 3, "src": "JavaGuide", "co": "通用"},
        {"q": "MySQL 慢查询如何优化？", "cat": "数据库", "diff": 3, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "MySQL 事务隔离级别有哪些？MVCC 的实现原理？", "cat": "数据库", "diff": 3, "freq": 5, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "Redis 有哪些数据结构？各自的使用场景？", "cat": "数据库", "diff": 2, "freq": 5, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "Redis 缓存穿透、缓存击穿、缓存雪崩的区别及解决方案？", "cat": "数据库", "diff": 3, "freq": 5, "occ": 4, "src": "JavaGuide", "co": "通用"},
        {"q": "Redis 的持久化机制？RDB 和 AOF 的区别？", "cat": "数据库", "diff": 3, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "Redis 分布式锁如何实现？有哪些注意事项？", "cat": "数据库", "diff": 3, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "SQL 中 left join 和 inner join 的区别？", "cat": "数据库", "diff": 1, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "分库分表怎么做？分片键如何选择？", "cat": "数据库", "diff": 4, "freq": 3, "occ": 3, "src": "面经", "co": "通用"},

        # --- 网络 ---
        {"q": "TCP 三次握手和四次挥手的过程？为什么需要三次握手？", "cat": "网络", "diff": 2, "freq": 5, "occ": 5, "src": "CS-Notes", "co": "通用"},
        {"q": "HTTP/1.1 和 HTTP/2 的主要区别？HTTP/3 呢？", "cat": "网络", "diff": 3, "freq": 4, "occ": 3, "src": "CS-Notes", "co": "通用"},
        {"q": "TCP 的流量控制和拥塞控制的区别。", "cat": "网络", "diff": 3, "freq": 4, "occ": 3, "src": "CS-Notes", "co": "通用"},
        {"q": "HTTPS 和 HTTP 的区别，SSL/TLS 握手过程。", "cat": "网络", "diff": 3, "freq": 5, "occ": 4, "src": "CS-Notes", "co": "通用"},
        {"q": "在浏览器输入 URL 到页面展示，中间发生了什么？", "cat": "网络", "diff": 2, "freq": 5, "occ": 4, "src": "面经", "co": "通用"},
        {"q": "TCP 和 UDP 的区别及各自的应用场景。", "cat": "网络", "diff": 2, "freq": 5, "occ": 4, "src": "CS-Notes", "co": "通用"},
        {"q": "HTTP 常见的状态码有哪些？", "cat": "网络", "diff": 1, "freq": 5, "occ": 4, "src": "CS-Notes", "co": "通用"},
        {"q": "DNS 解析的过程？", "cat": "网络", "diff": 2, "freq": 4, "occ": 3, "src": "CS-Notes", "co": "通用"},
        {"q": "WebSocket 和 HTTP 的区别？", "cat": "网络", "diff": 2, "freq": 3, "occ": 3, "src": "面经", "co": "通用"},

        # --- 操作系统 ---
        {"q": "进程和线程的区别？协程又是什么？", "cat": "操作系统", "diff": 2, "freq": 5, "occ": 5, "src": "CS-Notes", "co": "通用"},
        {"q": "epoll 和 select/poll 的区别？", "cat": "操作系统", "diff": 3, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "进程间通信（IPC）的方式有哪些？", "cat": "操作系统", "diff": 3, "freq": 4, "occ": 3, "src": "CS-Notes", "co": "通用"},
        {"q": "死锁产生的条件？如何避免？", "cat": "操作系统", "diff": 2, "freq": 4, "occ": 3, "src": "CS-Notes", "co": "通用"},
        {"q": "虚拟内存的作用？页面置换算法有哪些？", "cat": "操作系统", "diff": 3, "freq": 3, "occ": 3, "src": "CS-Notes", "co": "通用"},
        {"q": "Linux 中如何排查 CPU 负载过高的问题？", "cat": "操作系统", "diff": 3, "freq": 3, "occ": 3, "src": "面经", "co": "通用"},

        # --- 系统设计 ---
        {"q": "如何设计一个高并发秒杀系统？", "cat": "系统设计", "diff": 4, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "什么是 CAP 理论？在分布式系统中如何权衡？", "cat": "系统设计", "diff": 3, "freq": 4, "occ": 4, "src": "CS-Notes", "co": "通用"},
        {"q": "消息队列（Kafka/RocketMQ）如何保证消息不丢失？", "cat": "系统设计", "diff": 3, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "说说你对微服务的理解？微服务拆分的原则是什么？", "cat": "系统设计", "diff": 3, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "分布式事务有哪些实现方案？", "cat": "系统设计", "diff": 4, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "设计一个短链接系统。", "cat": "系统设计", "diff": 4, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "如何设计一个可靠的分布式 ID 生成器？", "cat": "系统设计", "diff": 3, "freq": 3, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "如何保证接口的幂等性？", "cat": "系统设计", "diff": 3, "freq": 4, "occ": 3, "src": "面经", "co": "通用"},
        {"q": "限流算法有哪些？令牌桶和漏桶的区别？", "cat": "系统设计", "diff": 3, "freq": 3, "occ": 3, "src": "面经", "co": "通用"},

        # --- 算法 ---
        {"q": "手写 LRU Cache，要求 O(1) get/put。", "cat": "算法", "diff": 4, "freq": 5, "occ": 4, "src": "面经-算法", "co": "字节跳动"},
        {"q": "接雨水（LeetCode 42），双指针 O(n)。", "cat": "算法", "diff": 4, "freq": 5, "occ": 3, "src": "面经-算法", "co": "字节跳动"},
        {"q": "最长无重复字符子串（滑动窗口 + HashMap）。", "cat": "算法", "diff": 3, "freq": 5, "occ": 4, "src": "面经-算法", "co": "字节跳动"},
        {"q": "数组第 K 大的数，快排 partition vs 小顶堆。", "cat": "算法", "diff": 3, "freq": 4, "occ": 3, "src": "面经-算法", "co": "通用"},
        {"q": "反转链表（迭代+递归两种方式）。", "cat": "算法", "diff": 2, "freq": 5, "occ": 4, "src": "面经-算法", "co": "通用"},
        {"q": "二叉树的层序遍历。", "cat": "算法", "diff": 2, "freq": 4, "occ": 3, "src": "面经-算法", "co": "通用"},
        {"q": "手写快速排序。", "cat": "算法", "diff": 2, "freq": 4, "occ": 3, "src": "面经-算法", "co": "通用"},
        {"q": "合并两个有序链表。", "cat": "算法", "diff": 2, "freq": 4, "occ": 3, "src": "面经-算法", "co": "通用"},

        # --- 前端 ---
        {"q": "什么是闭包？闭包有什么应用场景？", "cat": "前端", "diff": 2, "freq": 5, "occ": 4, "src": "面经-前端", "co": "通用"},
        {"q": "讲一下你对 React/Vue 生命周期的理解。", "cat": "前端", "diff": 2, "freq": 4, "occ": 3, "src": "面经-前端", "co": "通用"},
        {"q": "事件循环（Event Loop）机制是怎样的？", "cat": "前端", "diff": 3, "freq": 4, "occ": 3, "src": "面经-前端", "co": "通用"},
        {"q": "React 中虚拟 DOM 的原理？Diff 算法？", "cat": "前端", "diff": 3, "freq": 4, "occ": 3, "src": "面经-前端", "co": "通用"},
        {"q": "CSS 盒模型？如何触发 BFC？", "cat": "前端", "diff": 2, "freq": 4, "occ": 3, "src": "面经-前端", "co": "通用"},
        {"q": "跨域问题的解决方案有哪些？", "cat": "前端", "diff": 2, "freq": 4, "occ": 3, "src": "面经-前端", "co": "通用"},
        {"q": "Promise 的实现原理？async/await 是什么语法糖？", "cat": "前端", "diff": 3, "freq": 4, "occ": 3, "src": "面经-前端", "co": "通用"},
        {"q": "浏览器缓存策略？强缓存和协商缓存？", "cat": "前端", "diff": 3, "freq": 4, "occ": 3, "src": "面经-前端", "co": "通用"},

        # --- Go/Python ---
        {"q": "Go 的 Goroutine 和 Channel 是如何工作的？", "cat": "Go", "diff": 3, "freq": 4, "occ": 3, "src": "面经-Go", "co": "通用"},
        {"q": "Go 的垃圾回收机制是怎样的？", "cat": "Go", "diff": 3, "freq": 3, "occ": 3, "src": "面经-Go", "co": "通用"},
        {"q": "Python 的 GIL 是什么？如何绕过 GIL？", "cat": "Python", "diff": 3, "freq": 4, "occ": 3, "src": "面经-Python", "co": "通用"},
        {"q": "Python 装饰器的工作原理和应用场景？", "cat": "Python", "diff": 2, "freq": 4, "occ": 3, "src": "面经-Python", "co": "通用"},
    ]

    for jq in job_questions:
        questions.append(_make_q(jq, "job_interview"))

    # ================================================================
    # civil_service - 公务员面试（约 20 题）
    # ================================================================
    civil_questions = [
        {"q": "请做一个简短的自我介绍。", "cat": "结构化面试", "diff": 1, "freq": 5, "occ": 5, "src": "公务员面试真题", "co": "通用"},
        {"q": "你为什么想报考公务员？", "cat": "结构化面试", "diff": 1, "freq": 5, "occ": 4, "src": "公务员面试真题", "co": "通用"},
        {"q": "你对基层工作怎么看？如果被分配到偏远地区，你愿意去吗？", "cat": "结构化面试", "diff": 2, "freq": 4, "occ": 4, "src": "公务员面试真题", "co": "通用"},
        {"q": "单位领导让你做一件违反规定的事，你怎么办？", "cat": "应急处理", "diff": 3, "freq": 5, "occ": 4, "src": "公务员面试真题", "co": "通用"},
        {"q": "你和同事有矛盾，但他和领导关系很好，你怎么处理？", "cat": "人际关系", "diff": 3, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "群众来办事，但你的同事态度不好，群众向你投诉，你怎么处理？", "cat": "应急处理", "diff": 3, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "谈谈你对'绿水青山就是金山银山'的理解。", "cat": "综合分析", "diff": 2, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "单位要组织一次乡村振兴调研活动，你怎么组织？", "cat": "组织管理", "diff": 3, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "谈谈你对'躺平'现象的看法。", "cat": "综合分析", "diff": 2, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "在疫情防控中，有的地方层层加码，你怎么看？", "cat": "综合分析", "diff": 3, "freq": 3, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "如果让你负责组织一次会议，你会怎么做？", "cat": "组织管理", "diff": 2, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "你正在处理一项紧急工作，领导又给你安排了新任务，你怎么办？", "cat": "应急处理", "diff": 3, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "你的领导总是批评你，你怎么办？", "cat": "人际关系", "diff": 2, "freq": 4, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "谈谈数字化对政府治理的影响。", "cat": "综合分析", "diff": 3, "freq": 3, "occ": 2, "src": "公务员面试真题", "co": "通用"},
        {"q": "有人说'基层工作就是上面千条线，下面一根针'，你怎么理解？", "cat": "综合分析", "diff": 2, "freq": 3, "occ": 3, "src": "公务员面试真题", "co": "通用"},
        {"q": "你对 AI 取代公务员岗位有什么看法？", "cat": "综合分析", "diff": 3, "freq": 3, "occ": 2, "src": "公务员面试真题", "co": "通用"},
    ]

    for cq in civil_questions:
        questions.append(_make_q(cq, "civil_service"))

    # ================================================================
    # graduate_school - 考研复试（约 15 题）
    # ================================================================
    graduate_questions = [
        {"q": "请做一个简短的自我介绍（包括学术背景和研究兴趣）。", "cat": "综合面试", "diff": 1, "freq": 5, "occ": 5, "src": "考研复试真题", "co": "通用"},
        {"q": "你为什么选择读研究生？为什么选择我们学校？", "cat": "综合面试", "diff": 1, "freq": 5, "occ": 4, "src": "考研复试真题", "co": "通用"},
        {"q": "你未来的研究计划是什么？", "cat": "综合面试", "diff": 2, "freq": 5, "occ": 4, "src": "考研复试真题", "co": "通用"},
        {"q": "介绍一下你的本科毕业设计/论文。", "cat": "学术面试", "diff": 2, "freq": 5, "occ": 4, "src": "考研复试真题", "co": "通用"},
        {"q": "你读过哪些专业相关的文献或书籍？", "cat": "学术面试", "diff": 2, "freq": 4, "occ": 3, "src": "考研复试真题", "co": "通用"},
        {"q": "你对我们专业的研究方向有什么了解？", "cat": "学术面试", "diff": 2, "freq": 4, "occ": 3, "src": "考研复试真题", "co": "通用"},
        {"q": "用英语做一个简短的自我介绍。", "cat": "英语面试", "diff": 2, "freq": 5, "occ": 4, "src": "考研复试真题", "co": "通用"},
        {"q": "说说你的优点和缺点（英语回答）。", "cat": "英语面试", "diff": 2, "freq": 4, "occ": 3, "src": "考研复试真题", "co": "通用"},
        {"q": "你在本科期间参加过哪些科研项目或竞赛？", "cat": "综合面试", "diff": 2, "freq": 4, "occ": 3, "src": "考研复试真题", "co": "通用"},
        {"q": "如果你的考研成绩不理想，你有什么打算？", "cat": "综合面试", "diff": 2, "freq": 3, "occ": 3, "src": "考研复试真题", "co": "通用"},
        {"q": "你对考研和就业的选择有什么看法？", "cat": "综合面试", "diff": 1, "freq": 3, "occ": 2, "src": "考研复试真题", "co": "通用"},
        {"q": "数据结构中栈和队列的区别？", "cat": "专业基础", "diff": 1, "freq": 3, "occ": 3, "src": "计算机复试真题", "co": "通用"},
        {"q": "什么是操作系统中的死锁？条件有哪些？", "cat": "专业基础", "diff": 2, "freq": 3, "occ": 3, "src": "计算机复试真题", "co": "通用"},
        {"q": "谈谈你对机器学习的理解。", "cat": "专业基础", "diff": 2, "freq": 3, "occ": 2, "src": "计算机复试真题", "co": "通用"},
        {"q": "数据库事务的 ACID 特性是什么？", "cat": "专业基础", "diff": 2, "freq": 3, "occ": 3, "src": "计算机复试真题", "co": "通用"},
    ]

    for gq in graduate_questions:
        questions.append(_make_q(gq, "graduate_school"))

    # ================================================================
    # teacher_cert - 教资面试（约 15 题）
    # ================================================================
    teacher_questions = [
        {"q": "请做一个简短的自我介绍。", "cat": "结构化面试", "diff": 1, "freq": 5, "occ": 5, "src": "教资面试真题", "co": "通用"},
        {"q": "你为什么想当老师？", "cat": "结构化面试", "diff": 1, "freq": 5, "occ": 4, "src": "教资面试真题", "co": "通用"},
        {"q": "上课时有学生突然站起来说你讲错了，你怎么办？", "cat": "应急处理", "diff": 3, "freq": 5, "occ": 4, "src": "教资面试真题", "co": "通用"},
        {"q": "如果有学生上课玩手机，你怎么处理？", "cat": "班级管理", "diff": 2, "freq": 5, "occ": 4, "src": "教资面试真题", "co": "通用"},
        {"q": "你心目中好老师的标准是什么？", "cat": "结构化面试", "diff": 2, "freq": 4, "occ": 4, "src": "教资面试真题", "co": "通用"},
        {"q": "有学生家境困难，你作为班主任怎么做？", "cat": "班级管理", "diff": 3, "freq": 4, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "如何组织一次主题班会？", "cat": "班级管理", "diff": 2, "freq": 4, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "家长反映你的教学方式不适合孩子，你怎么办？", "cat": "应急处理", "diff": 3, "freq": 4, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "你如何看待素质教育与应试教育的关系？", "cat": "结构化面试", "diff": 2, "freq": 3, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "如果班里出现校园欺凌现象，你如何处理？", "cat": "班级管理", "diff": 3, "freq": 4, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "谈谈你对'双减'政策的理解。", "cat": "综合分析", "diff": 2, "freq": 4, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "你如何设计一堂课的导入环节？", "cat": "教学能力", "diff": 2, "freq": 4, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "有学生考试作弊被发现了，你怎么教育他？", "cat": "班级管理", "diff": 2, "freq": 3, "occ": 3, "src": "教资面试真题", "co": "通用"},
        {"q": "新课程改革强调学生主体地位，你怎么理解？", "cat": "综合分析", "diff": 2, "freq": 3, "occ": 2, "src": "教资面试真题", "co": "通用"},
        {"q": "你认为如何建立良好的师生关系？", "cat": "结构化面试", "diff": 2, "freq": 4, "occ": 3, "src": "教资面试真题", "co": "通用"},
    ]

    for tq in teacher_questions:
        questions.append(_make_q(tq, "teacher_cert"))

    # ================================================================
    # mba_interview - MBA 面试（约 12 题）
    # ================================================================
    mba_questions = [
        {"q": "请做一个简短的自我介绍（包括工作经历和管理经验）。", "cat": "综合面试", "diff": 1, "freq": 5, "occ": 5, "src": "MBA面试真题", "co": "通用"},
        {"q": "你为什么读 MBA？为什么选择我们学校？", "cat": "综合面试", "diff": 1, "freq": 5, "occ": 5, "src": "MBA面试真题", "co": "通用"},
        {"q": "你目前工作中遇到的最大管理挑战是什么？", "cat": "管理经验", "diff": 3, "freq": 4, "occ": 4, "src": "MBA面试真题", "co": "通用"},
        {"q": "你对未来的职业规划是什么？", "cat": "综合面试", "diff": 2, "freq": 5, "occ": 4, "src": "MBA面试真题", "co": "通用"},
        {"q": "你认为优秀领导者应具备哪些素质？", "cat": "管理经验", "diff": 2, "freq": 4, "occ": 3, "src": "MBA面试真题", "co": "通用"},
        {"q": "你有过带领团队实现目标的经历吗？具体讲讲。", "cat": "管理经验", "diff": 3, "freq": 4, "occ": 3, "src": "MBA面试真题", "co": "通用"},
        {"q": "谈谈你所在行业的竞争格局和发展趋势。", "cat": "行业分析", "diff": 3, "freq": 4, "occ": 3, "src": "MBA面试真题", "co": "通用"},
        {"q": "你如何平衡工作、学习和生活？", "cat": "综合面试", "diff": 2, "freq": 3, "occ": 3, "src": "MBA面试真题", "co": "通用"},
        {"q": "你如何看待 AI 对你所在行业的影响？", "cat": "行业分析", "diff": 3, "freq": 3, "occ": 3, "src": "MBA面试真题", "co": "通用"},
        {"q": "你在团队中通常扮演什么角色？", "cat": "管理经验", "diff": 2, "freq": 3, "occ": 3, "src": "MBA面试真题", "co": "通用"},
        {"q": "你的同事/下属如何评价你？", "cat": "综合面试", "diff": 2, "freq": 3, "occ": 2, "src": "MBA面试真题", "co": "通用"},
        {"q": "如果你被录取，你希望从 MBA 项目中获得什么？", "cat": "综合面试", "diff": 1, "freq": 4, "occ": 3, "src": "MBA面试真题", "co": "通用"},
    ]

    for mq in mba_questions:
        questions.append(_make_q(mq, "mba_interview"))

    # ================================================================
    # ielts_speaking - 雅思口语（约 12 题）
    # ================================================================
    ielts_questions = [
        {"q": "What is your full name? Does your name have any special meaning?", "cat": "Part 1", "diff": 1, "freq": 5, "occ": 5, "src": "IELTS真题", "co": "通用"},
        {"q": "Can you tell me about your hometown?", "cat": "Part 1", "diff": 1, "freq": 5, "occ": 5, "src": "IELTS真题", "co": "通用"},
        {"q": "What do you do for work/study?", "cat": "Part 1", "diff": 1, "freq": 5, "occ": 4, "src": "IELTS真题", "co": "通用"},
        {"q": "Do you like your major/job? Why?", "cat": "Part 1", "diff": 1, "freq": 4, "occ": 4, "src": "IELTS真题", "co": "通用"},
        {"q": "Describe a person you admire. Who is this person and why do you admire them?", "cat": "Part 2", "diff": 2, "freq": 4, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "Describe a place you like to visit. Where is it and what do you do there?", "cat": "Part 2", "diff": 2, "freq": 4, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "Describe a skill you want to learn. Why do you want to learn it?", "cat": "Part 2", "diff": 2, "freq": 3, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "Describe an important event in your life. What happened and why was it important?", "cat": "Part 2", "diff": 2, "freq": 4, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "Describe a book you have read or a film you have watched recently.", "cat": "Part 2", "diff": 2, "freq": 3, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "What are the advantages and disadvantages of social media? (Part 3)", "cat": "Part 3", "diff": 3, "freq": 3, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "How has technology changed the way people communicate? (Part 3)", "cat": "Part 3", "diff": 3, "freq": 3, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "Do you think young people today face more pressure than previous generations? (Part 3)", "cat": "Part 3", "diff": 3, "freq": 3, "occ": 2, "src": "IELTS真题", "co": "通用"},
        {"q": "Can you describe your daily routine?", "cat": "Part 1", "diff": 1, "freq": 3, "occ": 3, "src": "IELTS真题", "co": "通用"},
        {"q": "What kind of music do you like? Why?", "cat": "Part 1", "diff": 1, "freq": 3, "occ": 3, "src": "IELTS真题", "co": "通用"},
    ]

    for iq in ielts_questions:
        questions.append(_make_q(iq, "ielts_speaking"))

    # 写入文件
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"种子题库已生成: {output_path}")
    print(f"总计: {len(questions)} 题")

    # 按场景统计
    from collections import Counter
    scenarios = Counter(q["scenario"] for q in questions)
    print(f"\n场景分布:")
    for sc, count in scenarios.most_common():
        print(f"  {sc}: {count} 题")

    return questions


def _make_q(data: dict, scenario: str) -> dict:
    """构建标准化题目字典"""
    return {
        "question": data["q"],
        "scenario": scenario,
        "authenticity": "real",
        "source": data["src"],
        "source_url": "",
        "occurrence_count": data["occ"],
        "category": data["cat"],
        "difficulty": data["diff"],
        "frequency": data["freq"],
        "grade": "",
        "grade_reason": "",
        "answer_basic": "",
        "answer_good": "",
        "answer_excellent": "",
        "school_or_company": data.get("co", "通用"),
        "year": 2025,
        "tags": [],
        "collected_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    output = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "collected_questions", "seed_questions.json"
    )
    generate_seed_file(output)
