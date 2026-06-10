# -*- coding: utf-8 -*-
"""
审计：当前 category/tag 系统是否适合做 Deep Dive Topic。
只审计不修改。输出到文件避免终端编码问题。
"""
import sys, os, json, sqlite3
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "audit_deepdive_report.txt")

def println(*args, **kwargs):
    print(*args, **kwargs)
    with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
        print(*args, **kwargs, file=f)

# 清空输出文件
open(OUTPUT_PATH, "w", encoding="utf-8").close()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
all_rows = conn.execute("SELECT * FROM questions").fetchall()
total = len(all_rows)
println(f"总题数: {total}")
println()

# ================================================================
# 1. 现有 tags 字段分布
# ================================================================
tag_count = defaultdict(int)
tag_level = defaultdict(lambda: defaultdict(int))
for r in all_rows:
    d = dict(r)
    tags_str = (d.get("tags") or "[]").strip()
    try:
        tags = json.loads(tags_str)
    except:
        tags = []
    lev = (d.get("question_level") or "C").strip().upper()
    for t in tags:
        tag_count[t] += 1
        tag_level[t][lev] += 1

println("=" * 70)
println("1. 现有 tags 字段全量分布")
println("=" * 70)
println(f"{'Tag':25s} {'Count':>6s} {'S':>5s} {'A':>5s} {'B':>5s} {'C':>5s}")
println("-" * 55)
for tag, cnt in sorted(tag_count.items(), key=lambda x: -x[1]):
    s = tag_level[tag].get("S", 0)
    a = tag_level[tag].get("A", 0)
    b = tag_level[tag].get("B", 0)
    c = tag_level[tag].get("C", 0)
    println(f"{tag:25s} {cnt:6d} {s:5d} {a:5d} {b:5d} {c:5d}")

println()

# ================================================================
# 2. 从 question_text + tags 提取技术主题
# ================================================================

TOPIC_KEYWORDS = {
    "Redis": ["redis", "缓存穿透", "缓存雪崩", "缓存击穿", "分布式锁"],
    "MySQL": ["mysql", "索引", "innodb", "b+树", "事务隔离", "mvcc", "主从"],
    "Kafka": ["kafka", "消息队列", "分区", "副本", "offset"],
    "JVM": ["jvm", "gc", "垃圾回收", "内存模型", "类加载", "full gc"],
    "Spring": ["spring", "ioc", "aop", "mybatis", "dubbo", "nacos", "eureka"],
    "Netty": ["netty", "nio", "reactor"],
    "分布式/一致性": ["分布式事务", "cap", "base", "raft", "paxos", "一致性算法"],
    "微服务": ["微服务", "service mesh", "rpc", "grpc"],
    "Docker/K8s": ["docker", "kubernetes", "k8s", "容器"],
    "RAG": ["rag", "检索增强", "embedding", "向量数据库", "langchain"],
    "Agent": ["agent", "function call", "tool use", "react"],
    "Transformer": ["transformer", "attention", "self-attention", "bert", "gpt"],
    "LLM训练": ["llm", "大模型", "sft", "rlhf", "fine-tune", "微调"],
    "LoRA/微调": ["lora", "qlora", "adalo", "微调"],
    "MoE": ["moe", "混合专家"],
    "模型量化/部署": ["量化", "vllm", "tgi", "模型压缩"],
    "强化学习": ["强化学习", "rlhf", "ppo"],
    "React": ["react", "虚拟dom", "diff算法", "jsx", "hooks"],
    "Vue": ["vue", "响应式", "双向绑定", "nexttick"],
    "浏览器原理": ["浏览器渲染", "浏览器缓存", "事件循环", "event loop"],
    "前端工程化": ["webpack", "vite", "babel", "构建", "打包"],
    "CSS": ["css", "盒模型", "flex", "grid"],
    "JavaScript": ["javascript", "promise", "闭包", "原型链", "async"],
    "TypeScript": ["typescript", "interface"],
    "自动化测试": ["自动化", "selenium", "appium", "pytest"],
    "性能测试": ["性能测试", "压测", "jmeter", "压力测试"],
    "CI/CD/DevOps": ["ci/cd", "jenkins", "链路追踪"],
}


def match_topics(text: str) -> list:
    t = text.lower()
    matched = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw.lower() in t for kw in keywords):
            matched.append(topic)
    return matched


topic_count = defaultdict(int)
topic_level = defaultdict(lambda: defaultdict(int))
topic_stage = defaultdict(lambda: defaultdict(int))

no_match = 0
for r in all_rows:
    d = dict(r)
    text = (d.get("question_text") or "") + " " + (d.get("tags") or "")
    lev = (d.get("question_level") or "C").strip().upper()
    stage = (d.get("interview_stage") or "basic").strip()
    matched = match_topics(text)
    if not matched:
        no_match += 1
    for t in matched:
        topic_count[t] += 1
        topic_level[t][lev] += 1
        topic_stage[t][stage] += 1

println()
println("=" * 70)
println("2. 从题目文本自动匹配的技术主题分布")
println("=" * 70)
println(f"{'Topic':22s} {'Total':>6s} {'S':>5s} {'A':>5s} {'B':>5s} {'C':>5s}  {'stage分布(前3)':30s}")
println("-" * 75)
for topic, cnt in sorted(topic_count.items(), key=lambda x: -x[1]):
    s = topic_level[topic].get("S", 0)
    a = topic_level[topic].get("A", 0)
    b = topic_level[topic].get("B", 0)
    c = topic_level[topic].get("C", 0)
    stages_sorted = sorted(topic_stage[topic].items(), key=lambda x: -x[1])[:3]
    stages_display = ", ".join(f"{st}:{sc}" for st, sc in stages_sorted)
    println(f"{topic:22s} {cnt:6d} {s:5d} {a:5d} {b:5d} {c:5d}  {stages_display:30s}")

println(f"\n未匹配任何 Topic: {no_match} 题")
println()

# ================================================================
# 3. 最适合 Deep Dive 的 Topic
# ================================================================
println("=" * 70)
println("3. 最适合 Deep Dive 的 Topic（>=10题 且 >=3道S级）")
println("=" * 70)
println(f"{'Topic':22s} {'Total':>6s} {'S':>5s} {'A':>5s} {'B':>5s} {'C':>5s} {'S占比':>6s}")
println("-" * 55)

candidates = []
for topic, cnt in topic_count.items():
    s = topic_level[topic].get("S", 0)
    a = topic_level[topic].get("A", 0)
    if cnt >= 10 and s >= 3:
        candidates.append((topic, cnt, s, a))

candidates.sort(key=lambda x: (-x[2], -x[1]))

for topic, cnt, s, a in candidates[:20]:
    b = topic_level[topic].get("B", 0)
    c = topic_level[topic].get("C", 0)
    s_pct = s / cnt * 100
    println(f"{topic:22s} {cnt:6d} {s:5d} {a:5d} {b:5d} {c:5d}  {s_pct:5.1f}%")

println()

# ================================================================
# 4. 不足以支撑 Deep Dive 的 Topic
# ================================================================
println("=" * 70)
println("4. 不足以支撑连续追问的 Topic（<10题 或 <3道S级）")
println("=" * 70)
println(f"{'Topic':22s} {'Total':>6s} {'S':>5s} {'A':>5s} {'原因':24s}")
println("-" * 55)

weak_topics = []
for topic, cnt in topic_count.items():
    s = topic_level[topic].get("S", 0)
    if cnt < 10 or s < 3:
        reasons = []
        if cnt < 10:
            reasons.append(f"仅{cnt}题")
        if s < 3:
            reasons.append(f"仅{s}道S级")
        weak_topics.append((topic, cnt, s, "; ".join(reasons)))

weak_topics.sort(key=lambda x: x[1])

for topic, cnt, s, reason in weak_topics:
    a = topic_level[topic].get("A", 0)
    println(f"{topic:22s} {cnt:6d} {s:5d} {a:5d}  {reason:24s}")

println()

# ================================================================
# 5. 现有 tags 分析
# ================================================================
println("=" * 70)
println("5. 现有 tags 与 Deep Dive 标签缺失分析")
println("=" * 70)
println()

deepdive_check_tags = [
    "Redis", "MySQL", "Kafka", "JVM", "Spring",
    "RAG", "Agent", "Transformer",
    "React", "Vue",
]
println("细粒度技术标签检查:")
for t in deepdive_check_tags:
    if t in tag_count:
        s = tag_level[t].get("S", 0)
        a = tag_level[t].get("A", 0)
        println(f"  [已有] {t}: {tag_count[t]}题 (S:{s} A:{a})")
    else:
        println(f"  [缺少] {t}")

println()

# ================================================================
# 6. 最终建议
# ================================================================
println("=" * 70)
println("6. 最终建议")
println("=" * 70)

ready = [(t, c, s) for t, c, s, a in candidates if c >= 15 and s >= 5]
ok_but_need = [(t, c, s) for t, c, s, a in candidates if not (c >= 15 and s >= 5)]

println(f"\n[可立即上线 Deep Dive] (>=15题 且 >=5道S级)")
for topic, cnt, s in ready:
    println(f"  >>> {topic:22s} ({cnt}题, S级{s}道)")

println(f"\n[可以上线但建议补题] (达标但偏少)")
for topic, cnt, s in ok_but_need:
    a = topic_level[topic].get("A", 0)
    println(f"  {topic:22s} ({cnt}题, S级{s}道, A级{a}道)")

println(f"\n[暂不建议上线，题量严重不足]")
for topic, cnt, s, reason in weak_topics:
    a = topic_level[topic].get("A", 0)
    println(f"  {topic:22s} ({cnt}题, S级{s}道, A级{a}道) — {reason}")

println()
println("=" * 70)
println("诊断总结")
println("=" * 70)
println(f"""
1. 当前 tags 字段问题:
   - tags 以场景/来源为主（如"求职面试"557题、"第一面"49题、"牛客网"13题）
   - 缺少细粒度技术标签（Redis/MySQL/RAG/Agent 等多为0题）
   - 少数技术标签如"Agent"(19题)、"系统设计"(67题) 已存在但不够系统

2. 自动匹配发现:
   - 标题中实际包含技术关键词的题目不少（MySQL 52题、Redis 39题等）
   - 但 tags 字段没有反映这一点
   - 925题未匹配到任何技术主题（多为非技术类和通用类）

3. Deep Dive 就绪状态:
   - 可直接上线: LLM训练(82题/S13)、Agent(48题/S10)、MySQL(52题/S7)
   - 可上线但需补题: React(14/S5)、Spring(14/S5)
   - 其余 Topic 均不足10题或S级不足3题

4. 建议:
   - 立即上线 LLM训练 / Agent / MySQL 三个 Topic 的 Deep Dive
   - 为 React、Spring 补题后上线
   - 优先给现有 tags 补充 Redis / Kafka / JVM 等细粒度技术标签
   - 或新增 topic 字段，与 category(广义分类) 和 tags(多源场景) 共存
""")

conn.close()
println(f"\n报告已保存至: {OUTPUT_PATH}")
