# -*- coding: utf-8 -*-
"""
Question Quality Classification Script

Assigns question_level (S/A/B/C) to all existing questions in the database.

Usage:
    python scripts/classify_questions.py

Classification Criteria:
    S: real_interview with specific technical depth (大厂高频真题)
    A: real_interview (general) or open_source with technical content (真实面试常见)
    B: open_source (general) or ai_generated with technical keywords (基础知识)
    C: Template questions, gibberish, low-value AI-generated (低价值)
"""
import os
import sys
import sqlite3

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# DB path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")

# ============================================================
# Keyword Sets
# ============================================================

# 大厂名单 — company 字段匹配用
BIG_TECH_COMPANIES = [
    "字节跳动", "字节", "抖音", "火山引擎",
    "腾讯", "微信",
    "阿里巴巴", "阿里", "蚂蚁", "阿里云", "菜鸟",
    "美团", "大众点评",
    "京东",
    "百度",
    "拼多多",
    "快手",
    "网易",
    "小红书",
    "滴滴", "滴滴出行",
    "华为",
    "小米",
    "B站", "哔哩哔哩",
    "360",
    "搜狐",
    "新浪",
]

# 技术高特异性关键词 — S级判定用（具体到算法名、框架名、协议名）
HIGH_SPEC_KEYWORDS = [
    # Algorithms
    "LeetCode", "时间复杂度", "空间复杂度",
    "O(n)", "O(log", "O(1)", "O(n²)",
    "二叉树", "红黑树", "B+树", "B树", "AVL",
    "链表", "数组", "堆", "栈", "队列", "哈希",
    "快排", "归并排序", "冒泡排序", "插入排序", "选择排序",
    "动态规划", "DFS", "BFS", "递归", "迭代",
    "滑动窗口", "双指针", "贪心", "二分查找", "二分法",
    "拓扑排序", "最短路径", "最小生成树", "并查集",
    "设计模式", "单例", "工厂", "观察者",
    # Java / JVM
    "JVM", "GC", "垃圾回收", "内存模型", "类加载",
    "多线程", "线程池", "synchronized", "volatile",
    "CAS", "AQS", "ReentrantLock", "ConcurrentHashMap",
    "Spring", "Spring Boot", "Spring Cloud", "MyBatis",
    "Tomcat", "Netty", "Dubbo",
    # Database
    "MySQL", "Redis", "MongoDB", "Elasticsearch",
    "索引", "事务", "锁", "MVCC", "分库分表",
    "主从", "读写分离", "慢查询", "explain",
    "缓存穿透", "缓存击穿", "缓存雪崩",
    # System Design
    "架构", "微服务", "分布式", "高可用", "高并发",
    "一致性", "负载均衡", "CAP", "BASE",
    "RPC", "消息队列", "Kafka", "RabbitMQ", "RocketMQ",
    "Docker", "Kubernetes", "K8s", "容器化",
    # Network
    "TCP", "UDP", "HTTP", "HTTPS", "DNS", "CDN",
    "WebSocket", "QUIC", "SSL", "TLS",
    "拥塞控制", "流量控制", "三次握手", "四次挥手",
    # OS
    "进程", "线程", "协程", "内存管理", "虚拟内存",
    "页面置换", "文件系统", "inode", "IO多路复用",
    "epoll", "select", "poll", "零拷贝",
    # Frontend
    "React", "Vue", "Vuex", "Redux", "TypeScript",
    "JavaScript", "CSS", "DOM", "浏览器渲染",
    # Specific tech stacks
    "Django", "Flask", "Go", "golang", "Python",
    "DDD", "CQRS", "事件驱动", "领域驱动",
    # General technical depth markers
    "原理", "实现", "优化", "设计", "架构",
]

# 通用技术关键词 — B级判定用（含通用技术术语）
TECH_KEYWORDS = HIGH_SPEC_KEYWORDS + [
    "数据库", "缓存", "并发", "并行", "异步", "同步",
    "接口", "API", "网络", "协议", "安全",
    "性能", "监控", "日志", "配置", "部署",
    "算法", "数据结构", "排序", "搜索",
    "代码", "编程", "开发", "测试",
    "前端", "后端", "全栈", "客户端", "服务端",
    "系统", "框架", "中间件", "容器", "云原生",
    "数据", "存储", "计算", "分析", "挖掘",
]

# 模板关键词 — C级判定用（泛泛而谈的问题）
TEMPLATE_KEYWORDS = [
    # 自我介绍/通用面试题
    "自我介绍", "介绍自己", "简单介绍",
    "最大的优势", "最大的不足", "最大优势", "最大不足",
    "优点", "缺点", "优势", "不足",
    "职业规划", "未来规划", "五年规划",
    "为什么选择", "为什么离开", "为什么跳槽",
    "还有什么想问", "还有什么问题",
    "谈谈你", "你怎么", "介绍你",
    "你的期望薪资", "期望薪资", "薪资要求",
    "你对加班", "你对这个行业",
    "你为什么", "你为什么要",
    "你有什么想问",
    "你如何看待", "你怎么看待",
    "简单聊聊", "随便聊聊",
    "介绍一下你",
    "你的兴趣爱好", "兴趣爱好",
    "你的性格", "性格特点",
    # 泛泛的教资/行为问题（无具体场景）
    "你心目中", "你认为", "你觉得",
    "好老师", "优秀教师",
    "谈谈你的理解", "你怎么理解",
]


def normalize_text(text: str) -> str:
    """Normalize text for keyword matching"""
    if not text:
        return ""
    return text.strip()


def contains_any(text: str, keywords: list) -> bool:
    """Check if text contains any of the keywords"""
    t = normalize_text(text)
    if not t:
        return False
    for kw in keywords:
        if kw in t:
            return True
    return False


def count_matches(text: str, keywords: list) -> int:
    """Count how many keywords match in the text"""
    t = normalize_text(text)
    if not t:
        return 0
    count = 0
    for kw in keywords:
        if kw in t:
            count += 1
    return count


def classify_question(row: dict) -> str:
    """
    Classify a question into S/A/B/C based on its attributes.

    Priority-based classification (first match wins):
    1. S级 - real_interview with technical depth
    2. A级 - real_interview (all) or quality open_source/ai_generated
    3. B级 - basic knowledge questions
    4. C级 - template/generic
    """
    source_type = (row.get("source_type") or "ai_generated").strip()
    question_text = normalize_text(row.get("question_text") or "")
    company = normalize_text(row.get("company") or "")
    position = normalize_text(row.get("position") or "")
    text_len = len(question_text)

    # ============================================================
    # Rule 1: Trash data → C
    # ============================================================
    if text_len < 5:
        return "C"

    # ============================================================
    # Rule 2: S级 — 大厂高频真题
    # Criteria: real_interview with high-specificity technical keywords
    # ============================================================
    if source_type == "real_interview":
        high_spec_count = count_matches(question_text, HIGH_SPEC_KEYWORDS)
        if high_spec_count >= 2:
            return "S"
        if high_spec_count >= 1:
            return "A"
        # real_interview questions without specific tech keywords are rare
        # If it's real_interview but doesn't match tech keywords, still A
        return "A"

    # ============================================================
    # Rule 3: open_source
    # ============================================================
    if source_type == "open_source":
        if contains_any(question_text, HIGH_SPEC_KEYWORDS):
            return "A"
        if contains_any(question_text, TECH_KEYWORDS):
            return "B"
        return "B"  # open_source is at least B

    # ============================================================
    # Rule 4: ai_generated — check quality signals
    # ============================================================
    # Check if it's a template question (C级)
    if contains_any(question_text, TEMPLATE_KEYWORDS):
        # If it has technical keywords AND template keywords, it might be
        # a specific question that happens to start with "谈谈你"
        # Only classify as C if it has NO technical keywords
        if not contains_any(question_text, TECH_KEYWORDS):
            return "C"
        # Has both template and tech → B (borderline)
        return "B"

    # ai_generated with high specificity → A
    if contains_any(question_text, HIGH_SPEC_KEYWORDS):
        # If from a big-tech company, upgrade to A
        if any(bc.lower() in company.lower() for bc in BIG_TECH_COMPANIES):
            return "A"
        return "B"

    # ai_generated with general tech keywords → B
    if contains_any(question_text, TECH_KEYWORDS):
        return "B"

    # Remaining ai_generated → C
    return "C"


def main():
    """Main entry point"""
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        sys.exit(1)

    print(f"[classify] 连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure column exists
    try:
        conn.execute("ALTER TABLE questions ADD COLUMN question_level TEXT DEFAULT 'C'")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Read all questions
    rows = conn.execute("SELECT * FROM questions").fetchall()
    print(f"[classify] 读取到 {len(rows)} 道题目")

    # Classify each question
    stats = {"S": 0, "A": 0, "B": 0, "C": 0}
    samples = {"S": [], "A": [], "B": [], "C": []}
    MAX_SAMPLES = 5

    for row in rows:
        qid = row["id"]
        level = classify_question(dict(row))
        conn.execute(
            "UPDATE questions SET question_level = ? WHERE id = ?",
            (level, qid)
        )
        stats[level] = stats.get(level, 0) + 1
        if len(samples[level]) < MAX_SAMPLES:
            samples[level].append(row["question_text"][:60])

    conn.commit()

    # ============================================================
    # Report
    # ============================================================
    print()
    print("=" * 60)
    print("  题目质量评级结果")
    print("=" * 60)
    total = len(rows)
    for level in ["S", "A", "B", "C"]:
        count = stats.get(level, 0)
        pct = count / total * 100 if total else 0
        label = {"S": "大厂高频真题", "A": "真实面试常见",
                 "B": "基础知识", "C": "低价值/AI模板"}.get(level, "")
        print(f"\n  [{level}] {label} ({count}/{total} = {pct:.1f}%)")
        for s in samples[level]:
            print(f"    - {s}")

    # Scenario breakdown
    print()
    print("-" * 60)
    print("  按场景分布")
    print("-" * 60)
    cursor = conn.execute("""
        SELECT scenario_id, question_level, COUNT(*) as cnt
        FROM questions
        GROUP BY scenario_id, question_level
        ORDER BY scenario_id, question_level
    """)
    breakdown = {}
    for r in cursor.fetchall():
        sid = r["scenario_id"]
        lev = r["question_level"]
        cnt = r["cnt"]
        if sid not in breakdown:
            breakdown[sid] = {}
        breakdown[sid][lev] = cnt

    for sid in sorted(breakdown.keys()):
        levs = breakdown[sid]
        total_s = sum(levs.values())
        parts = [f"{l}={levs.get(l, 0)}" for l in ["S", "A", "B", "C"]]
        print(f"  {sid:20s}  {' | '.join(parts)}  (总计={total_s})")

    conn.close()
    print()
    print("[classify] 完成")


if __name__ == "__main__":
    main()
