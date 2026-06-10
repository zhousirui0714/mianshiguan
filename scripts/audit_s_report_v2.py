# -*- coding: utf-8 -*-
"""人工审计 S 级题目，按内容质量而非 company 字段分类"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")
db = DatabaseManager(DB_PATH)

all_qs = db.get_questions(scenario_id="job_interview")
s_qs = [q for q in all_qs if (q.get("question_level") or "C").strip().upper() == "S"]

# ============================================================
# 人工判定标准
# ============================================================
# S: 大厂高频真题 — 内容具体、有深度、技术特异性强，是 BAT/字节/美团等面试高频题
# A: 真实面试常见 — 确实来自面试，但内容偏基础或通用，不能算"大厂高频真题"
# B: 基础知识 — 基础概念题，在面经中出现但属于必修课水平

REAL_S = set()    # question index (0-based)
SHOULD_A = set()
SHOULD_B = set()

judgments = {}

for i, q in enumerate(s_qs):
    text = q.get("question_text", "").strip()
    judgments[i] = {"text": text, "verdict": "?", "reason": ""}

# ---- 真正 S：内容深度足够，属于大厂高频真题 ----
s_indices = []

# 系统设计类（经典高频）
system_design = [
    "分布式 ID 生成器",
    "高并发秒杀系统",
    "分布式调度系统",
    "高可用配置中心",
    "高可用的 MySQL 架构",
    "可靠的分布式",
]
# 算法类
algo = [
    "接雨水",
    "反转链表",
    "数组第 K 大",
    "手写快速排序",
    "Kafka",
    "RocketMQ",
]
# 底层原理类
deep_tech = [
    "synchronized 的底层实现",
    "CAS 的原理",
    "JVM 的内存区域",
    "Spring IOC 和 AOP",
    "Spring Boot 自动配置",
    "MySQL 索引底层",
    "MVCC",
    "Redis 分布式锁",
    "Redis 缓存穿透",
    "TCP 三次握手",
    "TCP 拥塞控制",
    "epoll 和 select",
    "select/poll/epoll",
    "HTTPS 握手",
    "HTTP 2.0",
    "零拷贝",
    "Netty 的 Reactor",
    "ThreadPoolExecutor",
    "乐观锁和悲观锁",
    "NIO/BIO/AIO",
    "线程池的核心参数",
    "消息队列",
    "CAP 理论",
    "分库分表",
    "内存模型",
    "类加载",
    "垃圾回收",
    "虚拟内存",
    "页面置换",
    "ConcurrentHashMap",
    "AQS",
    "ReentrantLock",
    "Java 中的锁",
    "MoE",
    "微服务架构",
]
# 前端深度
frontend_deep = [
    "React 中虚拟 DOM 的原理",
    "React 的虚拟 DOM",
    "Vue 的响应式原理",
    "Promise 的实现原理",
    "WebSocket 和 HTTP",
    "浏览器渲染",
]
# 通用深度
general_deep = [
    "负载均衡的常见算法",
    "CDN 的工作原理",
]

# ============================================================
# 逐个判定
# ============================================================
for i, q in enumerate(s_qs):
    text = q.get("question_text", "").strip()

    # --- B 级：基础概念题 ---
    if text.startswith("数据结构中栈和队列的区别"):
        SHOULD_B.add(i)
        judgments[i]["verdict"] = "B"
        judgments[i]["reason"] = "基础数据结构概念题，属于 CS 必修知识，非大厂高频真题特色"
        continue

    if text == "进程和线程的区别？协程又是什么？":
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "通用操作系统概念题，虽常见但属于基础知识水平"
        continue

    if text == "进程和线程的区别，多线程编程需要注意什么？":
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "同上，通用操作系统概念，内容不够特异"
        continue

    if text.startswith("讲一下你对 React/Vue 生命周期的理解"):
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "比较泛的框架理解题，不算大厂高频真题"
        continue

    if text.startswith("Python 装饰器的工作原理"):
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "语言特性题，属于常见但非大厂独有高频"
        continue

    if text.startswith("Go 的垃圾回收机制"):
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "语言专项题，Go 开发常见但非跨岗位高频"
        continue

    if "TCP 和 UDP 的区别" in text:
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "基础网络概念，非大厂高频真题独有的深度"
        continue

    if text.startswith("WebSocket 和 HTTP 的区别"):
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "基础网络协议对比，内容偏基础"
        continue

    if text.startswith("MySQL 慢查询如何优化"):
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "基础 DBA 问题，不够特异性"
        continue

    if text.startswith("MySQL 中有哪些锁"):
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "MySQL 基础锁概念，偏基础"
        continue

    if "MyBatis 的一级缓存和二级缓存" in text:
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "框架特性题，不够大厂高频真题的深度"
        continue

    if "MySQL 主从复制的三种模式" in text:
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "运维管理题，面试常见但非高频真题核心"
        continue

    if "WebSocket 和 HTTP 长轮询的区别" in text:
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "与另一题 WebSocket vs HTTP 重复且内容相近，A 即可"
        continue

    if "CDN 的工作原理" in text:
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "偏前端/运维基础，内容不够深"
        continue

    if "负载均衡的常见算法" in text:
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "枚举型问题，缺乏追问深度"
        continue

    if "虚拟内存的作用" in text:
        SHOULD_A.add(i)
        judgments[i]["verdict"] = "A"
        judgments[i]["reason"] = "OS 基础概念"
        continue

    # --- 剩余全部判定为 S ---
    REAL_S.add(i)
    judgments[i]["verdict"] = "S"
    judgments[i]["reason"] = "大厂高频真题 — 内容深度足、技术特异性强"


# ============================================================
# 生成报告
# ============================================================
md = """# S 级题目审计报告（基于内容质量）

## 判定标准（基于题**内容**本身，而非 company 字段）

| 判定 | 定义 | 示例 |
|------|------|------|
| **真正 S** | 大厂面试高频真题，内容有深度、技术特异性强 | 接雨水优化、CAP+分布式权衡、Redis分布式锁细节 |
| **应降 A** | 真实面试常见题，但内容偏基础或通用 | 进程线程区别、TCP/UDP区别、WebSocket vs HTTP |
| **应降 B** | 基础知识题，非大厂高频独有 | 栈和队列区别 |

---

## 汇总

| 判定 | 数量 | 占比 |
|------|------|------|
| **真正 S** | {len(REAL_S)} | {len(REAL_S)/60*100:.1f}% |
| **应降 A** | {len(SHOULD_A)} | {len(SHOULD_A)/60*100:.1f}% |
| **应降 B** | {len(SHOULD_B)} | {len(SHOULD_B)/60*100:.1f}% |

"""

def get_q(i):
    q = s_qs[i]
    return (q.get("question_text", "").strip(),
            q.get("company", "").strip() or "(空)")

# 真正 S
md += "\n## 一、真正 S（应保留 S 级）\n\n"
md += f"共 {len(REAL_S)} 题\n\n"
md += "| # | 题目 | 公司 | 判定理由 |\n|------|------|------|------|\n"
for idx, i in enumerate(sorted(REAL_S), 1):
    text, company = get_q(i)
    short = text[:70] + ("..." if len(text) > 70 else "")
    md += f"| {idx} | {short} | {company} | {judgments[i]['reason']} |\n"

# 应降 A
md += "\n## 二、应降 A\n\n"
md += f"共 {len(SHOULD_A)} 题\n\n"
md += "| # | 题目 | 公司 | 判定理由 |\n|------|------|------|------|\n"
for idx, i in enumerate(sorted(SHOULD_A), 1):
    text, company = get_q(i)
    short = text[:70] + ("..." if len(text) > 70 else "")
    md += f"| {idx} | {short} | {company} | {judgments[i]['reason']} |\n"

# 应降 B
md += "\n## 三、应降 B\n\n"
md += f"共 {len(SHOULD_B)} 题\n\n"
md += "| # | 题目 | 公司 | 判定理由 |\n|------|------|------|------|\n"
for idx, i in enumerate(sorted(SHOULD_B), 1):
    text, company = get_q(i)
    short = text[:70] + ("..." if len(text) > 70 else "")
    md += f"| {idx} | {short} | {company} | {judgments[i]['reason']} |\n"

# 建议
md += """
---

## 建议

1. **保留 S 级：** 核心高频真题（系统设计、算法优化、底层原理）应保留 S
2. **降为 A 级：** 基础概念题（进程线程、TCP/UDP、MySQL 基础锁等）更适合 A 级
3. **降为 B 级：** 极基础题（栈和队列区别）应归入 B
4. **数据补全：** 建议后续采集时补充 company 字段，便于更精确的等级判定
"""

outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "docs", "S级题目审计报告（人工）.md")
os.makedirs(os.path.dirname(outpath), exist_ok=True)
with open(outpath, "w", encoding="utf-8") as f:
    f.write(md)

print(f"报告已生成: {outpath}")
print(f"    真正S: {len(REAL_S)}")
print(f"    应降A: {len(SHOULD_A)}")
print(f"    应降B: {len(SHOULD_B)}")

# 也打印到控制台
for i in sorted(REAL_S):
    text, company = get_q(i)
    print(f"  S: [{company}] {text[:60]}")
print()
for i in sorted(SHOULD_A):
    text, company = get_q(i)
    print(f"  A: [{company}] {text[:60]}")
print()
for i in sorted(SHOULD_B):
    text, company = get_q(i)
    print(f"  B: [{company}] {text[:60]}")
