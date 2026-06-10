# -*- coding: utf-8 -*-
"""
Position Routing Weight System — 设计方案
只输出报告，不修改代码。
"""
import sys, os, json, sqlite3
from collections import defaultdict

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "position_routing_weights.txt")
open(OUTPUT, "w", encoding="utf-8").close()


def p(*args, **kwargs):
    print(*args, **kwargs)
    with open(OUTPUT, "a", encoding="utf-8") as f:
        print(*args, **kwargs, file=f)


# ================================================================
# 权重设计方案
# ================================================================

WEIGHTS = {
    "Python后端": {
        "系统设计": 20,
        "MySQL": 20,
        "Redis": 15,
        "数据结构与算法": 10,
        "操作系统": 10,
        "网络": 10,
        "项目经验": 5,
        "消息队列": 5,
        "并发编程": 5,
    },
    "Java后端": {
        "JVM": 15,
        "Spring框架": 15,
        "并发编程": 15,
        "MySQL": 15,
        "Redis": 10,
        "系统设计": 10,
        "数据结构与算法": 10,
        "项目经验": 5,
        "网络": 5,
    },
    "Go后端": {
        "系统设计": 20,
        "MySQL": 15,
        "Redis": 15,
        "操作系统": 15,
        "并发编程": 10,
        "网络": 10,
        "数据结构与算法": 10,
        "消息队列": 5,
    },
    "前端": {
        "浏览器/JS": 25,
        "前端框架": 25,
        "前端工程化": 10,
        "CSS": 10,
        "数据结构与算法": 10,
        "网络": 10,
        "项目经验": 5,
        "操作系统": 5,
    },
    "测试开发": {
        "测试开发": 30,
        "系统设计": 15,
        "MySQL": 10,
        "操作系统": 10,
        "网络": 10,
        "数据结构与算法": 10,
        "Redis": 5,
        "消息队列": 5,
        "项目经验": 5,
    },
    "算法工程师": {
        "数据结构与算法": 35,
        "系统设计": 15,
        "操作系统": 10,
        "网络": 10,
        "LLM/大模型": 10,
        "项目经验": 10,
        "数学/ML基础": 10,
    },
    "AI工程师": {
        "LLM/大模型": 30,
        "Agent": 20,
        "RAG": 15,
        "模型训练/对齐": 15,
        "系统设计": 10,
        "数据结构与算法": 5,
        "项目经验": 5,
    },
    "产品经理": {
        "产品经理": 30,
        "项目经验": 20,
        "行为面试": 20,
        "系统设计": 15,
        "数据分析": 10,
        "通用": 5,
    },
}

# ================================================================
# 验证：权重总和 = 100%
# ================================================================
p("=" * 70)
p("Position Routing Weight System v1")
p("=" * 70)
p()

for pos, topics in WEIGHTS.items():
    total = sum(topics.values())
    valid = "OK" if total == 100 else "ERROR: sum=%d" % total
    p("【%s】  total=%d%%  [%s]" % (pos, total, valid))
    p("-" * 55)
    for t, w in sorted(topics.items(), key=lambda x: -x[1]):
        bar = "#" * (w // 2)
        p("  %-22s %3d%% %s" % (t, w, bar))
    p()

# ================================================================
# 与现状对比
# ================================================================
p("=" * 70)
p("与当前题库对比 — 估算覆盖是否充足")
p("=" * 70)
p()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
all_rows = conn.execute("SELECT * FROM questions").fetchall()

pt_stats = defaultdict(lambda: defaultdict(lambda: {"count": 0, "S": 0, "A": 0, "B": 0, "C": 0}))
for r in all_rows:
    d = dict(r)
    tp_str = (d.get("target_positions") or "[]").strip()
    try:
        positions = json.loads(tp_str)
    except:
        positions = []
    topics_str = (d.get("topics") or "[]").strip()
    try:
        topics = json.loads(topics_str)
    except:
        topics = []
    lev = (d.get("question_level") or "C").strip().upper()

    for pos in positions:
        for t in topics:
            pt_stats[pos][t]["count"] += 1
            pt_stats[pos][t][lev] += 1

for pos, design_topics in WEIGHTS.items():
    p("【%s】" % pos)
    p("  %-22s %5s %5s %5s  %s" % ("设计Topic", "权重", "现有题数", "S级", "评估"))
    p("  " + "-" * 65)
    for t, w in sorted(design_topics.items(), key=lambda x: -x[1]):
        actual = pt_stats[pos].get(t, {}).get("count", 0)
        actual_s = pt_stats[pos].get(t, {}).get("S", 0)
        # 粗略评估：权重 * 1.5 为最低期望题数
        needed = max(3, int(w * 0.15))  # 至少需要权重*0.15道题
        status = "充足" if actual >= needed else ("不足" if actual > 0 else "缺失")
        # 对于权重>=15的Topic，需要至少3道S级
        s_status = ""
        if w >= 15 and actual_s < 3:
            s_status = " (缺S级)"
        p("  %-22s %3d%% %5d  %3dS  %s%s" % (t, w, actual, actual_s, status, s_status))
    p()

# ================================================================
# 原因说明
# ================================================================
p("=" * 70)
p("权重设计原因")
p("=" * 70)
p()

EXPLANATIONS = {
    "Python后端": """
后端通用技术栈。MySQL 和 Redis 是数据层核心（合计35%），
系统设计（20%）涵盖分布式/微服务/架构题，
数据结构与算法（10%）覆盖手撕代码轮。
Python 面试中并发编程（5%）权重低于 Java，因 GIL 使并发不是 Python 主要考点。
项目经验（5%）用于项目深挖轮。
""",
    "Java后端": """
Java 专属技术栈占 45%（JVM 15% + Spring 15% + 并发编程 15%），
这是 Java 面试区别于其他后端的关键。
MySQL 15% + Redis 10% = 25% 是数据层标配，
系统设计 10% 覆盖架构轮次。
JVM 含 GC 调优、内存模型等高阶追问。
""",
    "Go后端": """
Go 面试侧重系统底层和并发模型。
系统设计（20%）最高，因为 Go 常用于中间件和基础架构开发。
操作系统（15%）高于其他后端，因 Go 面试常问 GMP 模型、协程调度。
并发编程（10%）反映 goroutine 核心地位。
消息队列（5%）= Kafka 在 Go 生态中的应用。
""",
    "前端": """
浏览器/JS（25%）+ 前端框架（25%）= 50% 是前端面试绝对核心。
前端工程化（10%）反映构建工具面试分量上升。
CSS（10%）独立出来因为布局/动画仍是面试考点。
数据结构与算法（10%）覆盖前端手撕代码。
网络（10%）含 HTTP/CDN/浏览器缓存。
""",
    "测试开发": """
测试开发（30%）是专业核心，含自动化框架、CI/CD、质量保障。
系统设计（15%）覆盖测开架构面（测试平台设计、全链路压测）。
MySQL/Redis（15%）和技术基础（OS 10% + 网络 10%）占总题库 35%，
因为测试开发也需要懂被测系统的技术栈。
数据结构与算法（10%）覆盖手撕代码。
""",
    "算法工程师": """
数据结构与算法（35%）是算法面试绝对核心，含 LeetCode 手撕。
系统设计（15%）覆盖大规模系统设计（推荐系统、搜索架构）。
OS（10%）+ 网络（10%）= 20% 是计算机基础。
LLM/大模型（10%）反映近年 AI 面试趋势变化。
数学/ML基础（10%）含概率统计、损失函数、评估指标。
""",
    "AI工程师": """
LLM/大模型（30%）是 AI 工程师面试核心，
Agent（20%）+ RAG（15%）+ 模型训练/对齐（15%）= 50% 覆盖 AI 三大方向。
系统设计（10%）覆盖 AI 架构面（推理服务、训练平台）。
数据结构与算法（5%）手撕算法权重低于算法工程师岗。
项目经验（5%）用于 AI 项目深挖。
""",
    "产品经理": """
产品经理（30%）是专业核心，含需求分析、PRD、用户体验。
项目经验（20%）+ 行为面试（20%）= 40% 覆盖经历深挖和行为面。
系统设计（15%）是 PM 面试常考的逻辑题（设计一个功能）。
数据分析（10%）含埋点、转化率、A/B 测试。
""",
}

for pos, explanation in EXPLANATIONS.items():
    p("【%s】%s" % (pos, explanation.strip()))
    p()

# ================================================================
# 总结
# ================================================================
p("=" * 70)
p("总结")
p("=" * 70)
p("""
设计原则：
1. 专有技术栈优先：Java（JVM/Spring/并发）、AI（LLM/Agent/RAG）等差异化权重
2. 通用基础共享：MySQL、Redis、OS、网络 在所有技术岗中占 30-50%
3. 项目经验统一占 5%：作为 project 阶段触发
4. 数据结构与算法保持 10%：S 级算法题可在任何一轮使用
5. 所有岗位权重总和 = 100%

缺口（按权重补题优先级）：
  P0 - 测试开发：MySQL/Redis/OS/网络 均为 0 题
  P1 - 前端：工程化 9 题(S0)、网络 3 题(S0)
  P1 - 后端：Redis S 级不足、项目经验仅 4 题
  P1 - AI工程师：RAG S 级不足、系统设计 2 题

推荐召回逻辑：
  1. 用户选择 Python后端 → 查 Python后端的权重表
  2. 按权重比例从各 topic 中选取未用题目
  3. S 级题优先于 A 级，依此类推
  4. 权重为 5% 的 Topic（项目经验等）关键词触发时提高
""")

conn.close()
p("报告已保存: %s" % OUTPUT)
