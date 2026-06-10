# -*- coding: utf-8 -*-
"""
Topic Classification Script

为全部题目打 topic 标签（基于关键词规则）。
Topic Taxonomy v1 — 22 个二级主题，分属 12 个一级分类。
"""
import sys, os, json, sqlite3, random
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")


# ================================================================
# Topic Taxonomy v1 — 关键词规则
# ================================================================
# 每条规则使用 AND/OR 逻辑：
#   同一个 list 内的关键词是 OR 关系（任一匹配即命中）
#   匹配范围：question_text + tags + category

TOPIC_RULES = {
    # ============ 计算机基础 ============
    "操作系统": [
        "操作系统", "进程", "线程", "内存管理", "虚拟内存",
        "文件系统", "调度算法", "死锁", "页面置换",
        "epoll", "select", "零拷贝", "io多路复用",
        "用户态", "内核态", "中断", "dma",
    ],
    "网络": [
        "tcp", "udp", "http", "https",
        "三次握手", "四次挥手", "拥塞控制", "滑动窗口",
        "dns", "cdn", "负载均衡", "反向代理",
        "ip地址", "子网掩码", "arp",
        "websocket", "quic", "http2", "http3",
    ],

    # ============ Java ============
    "JVM": [
        "jvm", "虚拟机", "垃圾回收", "gc",
        "内存模型", "堆", "栈", "方法区",
        "类加载", "双亲委派", "字节码",
        "young gc", "full gc", "cms", "g1",
    ],
    "并发编程": [
        "synchronized", "volatile", "cas", "aqs",
        "reentrantlock", "threadlocal",
        "threadpoolexecutor", "线程池",
        "concurrenthashmap", "copyonwrite",
        "锁升级", "偏向锁", "轻量级锁", "重量级锁",
        "countdownlatch", "cyclicbarrier", "semaphore",
        "java线程", "多线程", "并发",
    ],
    "Spring框架": [
        "spring", "mybatis", "dubbo", "nacos",
        "ioc", "aop", "依赖注入", "控制反转",
        "bean", "servlet", "tomcat",
        "feign", "gateway", "sentinel",
    ],

    # ============ 数据库 ============
    "MySQL": [
        "mysql", "索引", "innodb",
        "事务隔离", "mvcc", "间隙锁",
        "b+树", "聚簇索引", "回表",
        "主从", "binlog", "redolog", "undolog",
        "explain", "慢查询", "sql优化",
        "分库分表", "读写分离",
    ],
    "Redis": [
        "redis", "缓存穿透", "缓存雪崩", "缓存击穿",
        "分布式锁", "redlock",
        "redis数据结构", "跳表", "skiplist",
        "rdb", "aof", "哨兵", "redis集群",
        "缓存淘汰", "lru",
    ],

    # ============ 中间件 ============
    "消息队列": [
        "kafka", "rocketmq", "rabbitmq",
        "消息队列", "消息丢失", "消息重复",
        "分区", "副本", "offset",
        "producer", "consumer", "broker",
        "推模式", "拉模式",
    ],

    # ============ 分布式/架构 ============
    "系统设计": [
        "系统设计", "架构设计", "设计一个",
        "秒杀", "短链接", "红包",
        "高并发", "高可用", "高扩展",
        "分布式", "cap", "base",
        "raft", "paxos", "一致性算法",
        "分布式事务", "seata",
        "配置中心", "注册中心",
        "灰度发布", "全链路",
    ],
    "微服务/容器化": [
        "微服务", "service mesh",
        "docker", "kubernetes", "k8s",
        "容器", "pod",
        "rpc", "grpc", "protobuf",
    ],

    # ============ 前端 ============
    "前端框架": [
        "react", "vue",
        "虚拟dom", "diff算法",
        "响应式", "双向绑定", "nexttick",
        "hooks", "jsx", "组件通信",
        "angular",
    ],
    "浏览器/JS": [
        "浏览器渲染", "浏览器缓存", "浏览器安全",
        "事件循环", "event loop",
        "javascript", "dom", "bom",
        "promise", "async", "await",
        "闭包", "原型链", "作用域",
        "css", "盒模型", "flex", "grid",
        "html", "语义化",
        "跨域", "csrf", "xss",
    ],
    "前端工程化": [
        "webpack", "vite", "babel",
        "构建", "打包", "模块化",
        "微前端", "spa", "ssr",
        "npm", "yarn", "pnpm",
    ],

    # ============ AI ============
    "LLM/大模型": [
        "llm", "大模型", "大语言模型",
        "transformer", "attention", "self-attention",
        "bert", "gpt", "glm", "llama", "qwen",
        "位置编码", "rope", "embedding",
    ],
    "Agent": [
        "agent", "function call", "tool使用", "tool use",
        "react模式", "react 循环", "plan-execute",
        "multi-agent", "多agent", "多智能体",
        "工具调用",
    ],
    "RAG": [
        "rag", "检索增强", "检索增强生成",
        "向量数据库", "向量检索",
        "embedding", "langchain",
        "chunk", "文档问答",
    ],
    "模型训练/对齐": [
        "sft", "rlhf", "dpo", "ppo",
        "微调", "fine-tune", "lora", "qlora",
        "moe", "混合专家",
        "模型量化", "量化", "vllm", "tgi",
        "强化学习", "灾难性遗忘",
        "预训练", "pretrain", "continue pretrain",
    ],

    # ============ 算法 ============
    "数据结构与算法": [
        "leetcode", "算法", "数据结构",
        "动态规划", "dfs", "bfs",
        "双指针", "滑动窗口", "贪心",
        "二分查找", "二分法",
        "反转链表", "lru", "接雨水",
        "排序", "哈希", "栈", "队列", "堆",
        "二叉树", "红黑树", "trie", "并查集",
        "字符串匹配", "kmp",
        "时间复杂度", "空间复杂度",
        "top k", "第k个",
    ],

    # ============ 测试/质量 ============
    "测试开发": [
        "测试用例", "自动化测试", "测试框架",
        "selenium", "appium", "pytest", "junit",
        "接口测试", "性能测试", "压力测试",
        "jmeter", "压测",
        "ci/cd", "jenkins", "pipeline",
        "白盒测试", "黑盒测试", "单元测试",
        "质量保障", "qa", "bug",
        "流量回放", "diffy",
        "全链路压测",
    ],

    # ============ 软技能 ============
    "项目经验": [
        "项目经验", "项目经历", "项目中",
        "你做过", "你实现", "你参与", "你负责",
        "你在项目中", "描述一个", "分享一个",
        "star法则", "stsr法则",
        "技术选型", "架构选型",
        "难点", "挑战", "最有成就感",
    ],
    "行为面试": [
        "自我介绍", "介绍自己", "介绍一下你",
        "你的优点", "你的缺点", "你的优势", "你的不足",
        "职业规划", "五年规划", "三年规划",
        "为什么选择", "你如何看待", "你觉得你",
        "还有什么问题", "你对加班", "你对薪资",
        "你的离职", "核心竞争力",
    ],

    # ============ 产品/业务 ============
    "产品经理": [
        "产品需求", "prd", "原型图",
        "用户调研", "用户需求", "用户体验",
        "axure", "figma",
        "埋点", "转化率", "留存", "dau", "mau",
        "竞品分析", "商业模式",
        "增长", "运营", "项目管理",
    ],

    # ============ 非技术面试 ============
    "公务员面试": [
        "公务员", "省考", "国考", "公考",
        "结构化面试", "综合分析",
        "应急处理", "组织协调",
        "自我认知", "岗位认知",
    ],
    "教资面试": [
        "教资", "教师资格", "教师面试",
        "班级管理", "教学设计", "教育理念",
        "课堂管理", "学生心理", "家校沟通",
        "教育法规", "教育技术",
    ],
    "考研复试": [
        "考研", "复试", "研究生",
        "科研能力", "学术面试", "专业基础",
        "学习动机", "综合素质",
    ],
    "MBA面试": [
        "mba", "商学院", "经管",
        "商业洞察", "领导力", "团队管理",
        "决策分析", "管理经验",
    ],
    "雅思口语": [
        "雅思", "ielts", "口语",
        "part 1", "part 2", "part 3",
        "描述一个", "观点表达",
    ],
}


def classify_topics(text: str, tags_str: str, category: str) -> list:
    """根据文本、tags、category 匹配 topic"""
    t = (text + " " + tags_str + " " + category).lower()
    matched = []
    for topic, keywords in TOPIC_RULES.items():
        if any(kw.lower() in t for kw in keywords):
            matched.append(topic)
    if not matched:
        matched.append("通用")
    return matched


# ================================================================
# Main
# ================================================================

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# 确保列存在
try:
    conn.execute("ALTER TABLE questions ADD COLUMN topics TEXT DEFAULT '[]'")
    conn.commit()
    print("[migrate] 新增 topics 列")
except sqlite3.OperationalError:
    pass

all_rows = conn.execute("SELECT * FROM questions").fetchall()
print(f"总题数: {len(all_rows)}")
print()

# ================================================================
# 1. 执行分类
# ================================================================
topic_stats = defaultdict(lambda: {"count": 0, "S": 0, "A": 0, "B": 0, "C": 0})
topic_questions = defaultdict(list)  # topic -> [(qid, text, level)]

updated = 0
for row in all_rows:
    d = dict(row)
    text = (d.get("question_text") or "") or ""
    tags_str = (d.get("tags") or "") or ""
    category = (d.get("category") or "") or ""
    qid = d["id"]
    lev = (d.get("question_level") or "C").strip().upper()

    topics = classify_topics(text, tags_str, category)
    topics_json = json.dumps(topics, ensure_ascii=False)

    conn.execute(
        "UPDATE questions SET topics = ? WHERE id = ?",
        (topics_json, qid)
    )
    updated += 1

    for t in topics:
        topic_stats[t]["count"] += 1
        topic_stats[t][lev] += 1
        topic_questions[t].append((qid, text, lev))

conn.commit()

# ================================================================
# 2. 输出统计
# ================================================================
print(f"已更新: {updated}")
print()
print("=" * 70)
print("Topic 分布统计")
print("=" * 70)
print(f"{'Topic':25s} {'Count':>6s} {'S':>5s} {'A':>5s} {'B':>5s} {'C':>5s} {'DeepDive就绪':>12s}")
print("-" * 65)

ready_count = 0
for topic, st in sorted(topic_stats.items(), key=lambda x: -x[1]["count"]):
    cnt = st["count"]
    s = st["S"]
    a = st["A"]
    b = st["B"]
    c = st["C"]
    # Deep Dive 条件：>= 10题 且 >= 3道S级
    ready = "可上线" if (cnt >= 10 and s >= 3) else ("需补题" if cnt >= 5 else "不足")
    if ready == "可上线":
        ready_count += 1
    print(f"{topic:25s} {cnt:6d} {s:5d} {a:5d} {b:5d} {c:5d}  {ready:>12s}")

print(f"\n可进行 Deep Dive 的 Topic: {ready_count}")
print()

# ================================================================
# 3. 抽样验证：Redis / MySQL / Agent / 项目经验
# ================================================================
SAMPLE_TOPICS = ["Redis", "MySQL", "Agent", "项目经验"]
random.seed(42)

print("=" * 70)
print("抽样验证 — 随机20题检查标签准确性")
print("=" * 70)

for topic in SAMPLE_TOPICS:
    qs = topic_questions.get(topic, [])
    sample = random.sample(qs, min(20, len(qs)))
    print(f"\n>>> {topic} ({len(qs)}题总, 抽查{len(sample)}题)")
    print("-" * 60)
    for i, (qid, text, lev) in enumerate(sample, 1):
        # 截断显示
        text_short = text[:80] + "..." if len(text) > 80 else text
        print(f"  {i:2d}. [{lev}] {text_short}")

conn.close()
print(f"\n{'=' * 70}")
print("完成。请人工复核以上抽样结果，确认标签准确率。")
