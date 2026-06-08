"""
题库扩充 — 数据源配置

"主数据源：raw.githubusercontent.com 可直接访问的仓库
"本地回退：预整理的面试题数据（来自知名开源题库）

=  GitHub 直连源（已验证可下载） =
=  1. DolbyUUU/Awesome-LLM-Interview-Questions-and-Answers
=  2. azl397985856/fe-interview
=  3. datawhalechina/hello-agents
=
=  本地回退源（打包在项目中）=
=  4. Snailclimb/JavaGuide
=  5. CyC2018/CS-Notes
=  6. youngyangyang04/leetcode-master
"""

SKIP_FILE_KEYWORDS = [
    "readme", "index", "summary", "changelog", "contributing",
    "license", "_sidebar", "_navbar", "toc", "pull_request",
    "issue_template", "code_of_conduct",
]

REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

CATEGORY_KEYWORDS = {
    "算法": [
        "排序", "链表", "二叉树", "动态规划", "回溯", "双指针",
        "滑动窗口", "递归", "栈", "队列", "哈希", "DFS", "BFS",
        "LeetCode", "算法", "时间复杂度", "空间复杂度",
    ],
    "Java": [
        "JVM", "Java", "Spring", "MyBatis", "线程池", "HashMap",
        "ConcurrentHashMap", "synchronized", "volatile", "ThreadLocal",
        "类加载", "反射", "代理", "AOP", "IOC", "Spring Boot",
    ],
    "数据库": [
        "MySQL", "索引", "事务", "SQL", "分库分表", "B+树",
        "数据库", "Redis", "Kafka", "消息队列", "缓存", "主从",
        "NoSQL", "MongoDB", "读写分离", "慢查询",
    ],
    "网络": [
        "TCP", "HTTP", "HTTPS", "DNS", "三次握手", "四次挥手",
        "网络", "IP", "Socket", "WebSocket", "CDN", "TLS",
    ],
    "操作系统": [
        "进程", "线程", "内存", "文件系统", "调度", "锁",
        "操作系统", "Linux", "内核", "IO", "epoll", "select",
    ],
    "系统设计": [
        "设计", "高并发", "分布式", "微服务", "架构", "限流",
        "熔断", "降级", "秒杀", "短链接", "RPC", "网关",
        "一致性", "CAP", "BASE", "分布式事务",
    ],
    "前端": [
        "React", "Vue", "JavaScript", "TypeScript", "CSS", "DOM",
        "浏览器", "事件循环", "闭包", "原型链", "异步", "Promise",
        "前端", "组件", "虚拟DOM", "Fiber",
    ],
    "AI/大模型": [
        "Transformer", "大模型", "LLM", "GPT", "BERT", "Attention",
        "深度学习", "机器学习", "神经网络", "RLHF", "RAG",
        "Agent", "Prompt", "向量数据库", "Embedding",
    ],
    "项目深挖/行为面试": [
        "项目", "STAR", "职业规划", "团队", "沟通", "领导力",
        "为什么", "经历", "成就", "失败",
    ],
}

DEFAULT_CATEGORY = "计算机基础"
