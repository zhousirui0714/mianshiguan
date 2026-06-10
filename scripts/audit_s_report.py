# -*- coding: utf-8 -*-
"""生成 S 级题目审计 Markdown 报告"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")
db = DatabaseManager(DB_PATH)

all_qs = db.get_questions(scenario_id="job_interview")
s_qs = [q for q in all_qs if (q.get("question_level") or "C").strip().upper() == "S"]

def count_tech_keywords(text: str) -> int:
    """统计 HIGH_SPEC_KEYWORDS 匹配数"""
    keywords = [
        "LeetCode", "时间复杂度", "空间复杂度",
        "O(n)", "O(log", "O(1)", "O(n²)",
        "二叉树", "红黑树", "B+树", "B树", "AVL",
        "链表", "数组", "堆", "栈", "队列", "哈希",
        "快排", "归并排序", "冒泡排序", "插入排序", "选择排序",
        "动态规划", "DFS", "BFS", "递归", "迭代",
        "滑动窗口", "双指针", "贪婪", "贪心", "二分查找", "二分法",
        "拓扑排序", "最短路径", "最小生成树", "并查集",
        "设计模式", "单例", "工厂", "观察者",
        "JVM", "GC", "垃圾回收", "内存模型", "类加载",
        "多线程", "线程池", "synchronized", "volatile",
        "CAS", "AQS", "ReentrantLock", "ConcurrentHashMap",
        "Spring", "Spring Boot", "Spring Cloud", "MyBatis",
        "Tomcat", "Netty", "Dubbo",
        "MySQL", "Redis", "MongoDB", "Elasticsearch",
        "索引", "事务", "锁", "MVCC", "分库分表",
        "主从", "读写分离", "慢查询", "explain",
        "缓存穿透", "缓存击穿", "缓存雪崩",
        "架构", "微服务", "分布式", "高可用", "高并发",
        "一致性", "负载均衡", "CAP", "BASE",
        "RPC", "消息队列", "Kafka", "RabbitMQ", "RocketMQ",
        "Docker", "Kubernetes", "K8s", "容器化",
        "TCP", "UDP", "HTTP", "HTTPS", "DNS", "CDN",
        "WebSocket", "QUIC", "SSL", "TLS",
        "拥塞控制", "流量控制", "三次握手", "四次挥手",
        "进程", "线程", "协程", "内存管理", "虚拟内存",
        "页面置换", "文件系统", "inode", "IO多路复用",
        "epoll", "select", "poll", "零拷贝",
        "React", "Vue", "Vuex", "Redux", "TypeScript",
        "JavaScript", "CSS", "DOM", "浏览器渲染",
        "Django", "Flask", "Go", "golang", "Python",
        "DDD", "CQRS", "事件驱动", "领域驱动",
        "原理", "实现", "优化", "设计", "架构",
    ]
    count = 0
    for kw in keywords:
        if kw in text:
            count += 1
    return count

def classify_manually(q: dict) -> str:
    """人工判断应属等级"""
    text = q.get("question_text", "")
    company = q.get("company", "").strip()
    kw_count = count_tech_keywords(text)

    reasons = []

    # 真正 S 的标准：大厂 + 具体技术深度
    big_tech_companies = ["字节跳动", "字节", "抖音", "火山引擎",
                          "腾讯", "微信", "阿里巴巴", "阿里", "蚂蚁",
                          "美团", "京东", "百度", "拼多多", "快手",
                          "网易", "小红书", "滴滴", "华为", "小米",
                          "B站", "哔哩哔哩"]
    is_big_tech = any(c in company for c in big_tech_companies)

    # S 级硬标准：来源 real_interview + 高特异性关键词 >= 2
    # 而且题目本身应该是"大厂高频真题"级别
    is_deep_tech = kw_count >= 2

    # 检查是否泛泛的"请谈谈""简单介绍"类型
    template_indicators = ["请谈谈", "简单介绍", "你怎么", "说说你", "介绍一下"]
    is_template = any(t in text for t in template_indicators)

    # 检查是否基础概念题（只问概念不问原理/实现/优化）
    basic_concepts = [
        ("进程", "线程"),  # 只问区别
    ]
    is_basic = False
    if "进程" in text and "线程" in text and "区别" in text and "原理" not in text and "实现" not in text:
        is_basic = True

    if is_template:
        return "B", "模板/泛泛问题，即使来自 real_interview 也最多 B 级"
    if is_basic and not is_deep_tech:
        return "B", f"基础概念题，仅 {kw_count} 个技术关键词，不够 S 级深度"

    if is_big_tech and is_deep_tech:
        return "S", f"大厂({company}) + 技术深度({kw_count}个关键词)，符合 S 级标准"
    if is_deep_tech:
        # 有深度但无大厂名
        return "A", f"有技术深度({kw_count}个关键词)但无大厂标记(company={company})，建议降 A"
    if is_big_tech:
        # 有大厂名但无技术深度
        return "A", f"来自大厂({company})但技术特异性不足({kw_count}个关键词)，建议降 A"

    # 默认：来自 real_interview 但条件不够 S
    return "A", f"real_interview 但无法确认大厂+深度(kw={kw_count}, company={company})，建议降 A"


rows = []
for q in s_qs:
    text = q.get("question_text", "").strip()
    company = q.get("company", "").strip() or "(空)"
    position = q.get("position", "").strip() or "(空)"
    source_type = q.get("source_type", "").strip()
    kw_count = count_tech_keywords(text)
    verdict, reason = classify_manually(q)
    rows.append((verdict, text, company, kw_count, reason))

# 排序：真正S -> 应降A -> 应降B
def sort_key(r):
    order = {"S": 0, "A": 1, "B": 2}
    return (order.get(r[0], 9), r[1])

rows.sort(key=sort_key)

# 生成 Markdown
md = """# S 级题目审计报告

## 判定标准

| 判定 | 标准 |
|------|------|
| **真正S** | 大厂(字节/腾讯/阿里/美团/京东/百度等) + 技术深度(≥2个高特异性关键词) |
| **应降A** | real_interview 但无明确大厂标记 或 技术特异性不足 |
| **应降B** | 基础概念对比题 / 泛泛问题，即使来自面经也只适合 B 级 |

> 高特异性关键词计数：包含具体算法名、框架名、协议名等（不含通用词如"系统""架构"）

---

## 汇总

"""

summary = {"S": [], "A": [], "B": []}
for r in rows:
    summary[r[0]].append(r)

md += f"| 判定 | 数量 | 占比 |\n|------|------|------|\n"
for verdict, label in [("S", "真正S"), ("A", "应降A"), ("B", "应降B")]:
    cnt = len(summary[verdict])
    md += f"| **{label}** | {cnt} | {cnt/60*100:.1f}% |\n"

md += "\n---\n\n"

# 真正 S
md += "## 一、真正 S（大厂高频真题）\n\n"
md += f"共 {len(summary['S'])} 题\n\n"
md += "| # | 题目 | 公司 | 技术关键词数 | 判定理由 |\n|------|------|------|:------:|------|\n"
for i, (_, text, company, kw_count, reason) in enumerate(summary["S"], 1):
    short_text = text[:60] + ("..." if len(text) > 60 else "")
    md += f"| {i} | {short_text} | {company} | {kw_count} | {reason} |\n"

# 应降 A
md += "\n## 二、应降 A（真实面试常见，非大厂或深度不够）\n\n"
md += f"共 {len(summary['A'])} 题\n\n"
md += "| # | 题目 | 公司 | 技术关键词数 | 判定理由 |\n|------|------|------|:------:|------|\n"
for i, (_, text, company, kw_count, reason) in enumerate(summary["A"], 1):
    short_text = text[:60] + ("..." if len(text) > 60 else "")
    md += f"| {i} | {short_text} | {company} | {kw_count} | {reason} |\n"

# 应降 B
md += "\n## 三、应降 B（基础知识/模板问题）\n\n"
md += f"共 {len(summary['B'])} 题\n\n"
md += "| # | 题目 | 公司 | 技术关键词数 | 判定理由 |\n|------|------|------|:------:|------|\n"
for i, (_, text, company, kw_count, reason) in enumerate(summary["B"], 1):
    short_text = text[:80] + ("..." if len(text) > 80 else "")
    md += f"| {i} | {short_text} | {company} | {kw_count} | {reason} |\n"

# 写入文件
outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "docs", "S级题目审计报告.md")
os.makedirs(os.path.dirname(outpath), exist_ok=True)
with open(outpath, "w", encoding="utf-8") as f:
    f.write(md)

print(f"报告已生成: {outpath}")
print(f"    真正S: {len(summary['S'])}")
print(f"    应降A: {len(summary['A'])}")
print(f"    应降B: {len(summary['B'])}")
