# -*- coding: utf-8 -*-
"""
分析 target_positions × topics × question_level × interview_stage 的关联关系。
只输出分析报告，不修改代码。
"""
import sys, os, json, sqlite3
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "position_topic_analysis.txt")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")


def p(*args, **kwargs):
    print(*args, **kwargs)
    with open(OUTPUT, "a", encoding="utf-8") as f:
        print(*args, **kwargs, file=f)


# 清空输出文件
open(OUTPUT, "w", encoding="utf-8").close()

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
all_rows = conn.execute("SELECT * FROM questions").fetchall()

ALL_POSITIONS = [
    "Python后端", "Java后端", "Go后端", "前端",
    "测试开发", "算法工程师", "AI工程师", "产品经理",
]

ALL_TOPICS = [
    "操作系统", "网络", "JVM", "并发编程", "Spring框架",
    "MySQL", "Redis", "消息队列", "系统设计", "微服务/容器化",
    "前端框架", "浏览器/JS", "前端工程化", "LLM/大模型", "Agent",
    "RAG", "模型训练/对齐", "数据结构与算法", "测试开发",
    "项目经验", "行为面试", "产品经理", "通用",
]

# position -> topic -> stats
pt_stats = defaultdict(lambda: defaultdict(lambda: {"count": 0, "S": 0, "A": 0, "B": 0, "C": 0}))
# position -> stage -> count
ps_stats = defaultdict(lambda: defaultdict(int))

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
    stage = (d.get("interview_stage") or "basic").strip()

    for pos in positions:
        for t in topics:
            pt_stats[pos][t]["count"] += 1
            pt_stats[pos][t][lev] += 1
        ps_stats[pos][stage] += 1

# ================================================================
# 1. 岗位 → Topic 映射矩阵
# ================================================================
p("=" * 70)
p("1. 岗位 — Topic 映射矩阵")
p("=" * 70)
p()

for pos in ALL_POSITIONS:
    p("【%s】" % pos)
    topics_sorted = sorted(pt_stats[pos].items(), key=lambda x: -x[1]["count"])
    for t, st in topics_sorted:
        if st["count"] >= 3:
            p("    %-22s %d题 (S%d A%d B%d C%d)" % (
                t, st["count"], st["S"], st["A"], st["B"], st["C"]))
    p()

# ================================================================
# 2. 岗位全量统计
# ================================================================
p("=" * 70)
p("2. 岗位全量统计（含 Stage 分布）")
p("=" * 70)
p()

STAGES = ["intro", "project", "basic", "advanced", "system_design", "behavior"]

for pos in ALL_POSITIONS:
    p("【%s】" % pos)
    p("  Topic分布:")
    p("    %-22s %5s %4s %4s %4s %4s" % ("Topic", "Count", "S", "A", "B", "C"))
    p("    " + "-" * 45)
    topics_sorted = sorted(pt_stats[pos].items(), key=lambda x: -x[1]["count"])
    for t, st in topics_sorted:
        if st["count"] > 0:
            p("    %-22s %5d %4d %4d %4d %4d" % (
                t, st["count"], st["S"], st["A"], st["B"], st["C"]))

    p("  Interview Stage分布:")
    pos_total = sum(ps_stats[pos].values())
    for s in STAGES:
        cnt = ps_stats[pos].get(s, 0)
        pct = cnt / pos_total * 100 if pos_total else 0
        p("    %-15s: %4d (%5.1f%%)" % (s, cnt, pct))
    p()

# ================================================================
# 3. 缺口分析
# ================================================================
p("=" * 70)
p("3. 缺口分析 — 应该覆盖但题量不足的 Topic")
p("=" * 70)
p()

POS_EXPECTED_TOPICS = {
    "Python后端": [
        "MySQL", "Redis", "操作系统", "网络", "系统设计",
        "并发编程", "项目经验", "消息队列", "数据结构与算法",
    ],
    "Java后端": [
        "JVM", "Spring框架", "MySQL", "Redis", "操作系统",
        "网络", "并发编程", "系统设计", "消息队列", "数据结构与算法",
        "项目经验",
    ],
    "Go后端": [
        "操作系统", "网络", "系统设计", "MySQL", "Redis",
        "消息队列", "并发编程", "数据结构与算法", "项目经验",
    ],
    "前端": [
        "前端框架", "浏览器/JS", "前端工程化", "网络",
        "操作系统", "数据结构与算法", "项目经验",
    ],
    "测试开发": [
        "测试开发", "MySQL", "Redis", "操作系统", "网络",
        "系统设计", "项目经验", "消息队列",
    ],
    "算法工程师": [
        "数据结构与算法", "操作系统", "网络", "系统设计", "项目经验",
    ],
    "AI工程师": [
        "LLM/大模型", "Agent", "RAG", "模型训练/对齐",
        "系统设计", "数据结构与算法", "项目经验", "操作系统",
    ],
    "产品经理": [
        "产品经理", "项目经验", "行为面试", "系统设计",
    ],
}

MIN_COUNT = 5
MIN_S = 3

for pos in ALL_POSITIONS:
    expected = POS_EXPECTED_TOPICS.get(pos, [])
    gaps = []
    for t in expected:
        st = pt_stats[pos].get(t, {"count": 0, "S": 0, "A": 0, "B": 0, "C": 0})
        if st["count"] < MIN_COUNT or st["S"] < MIN_S:
            reasons = []
            if st["count"] == 0:
                reasons.append("无题")
            elif st["count"] < MIN_COUNT:
                reasons.append("仅%d题" % st["count"])
            if st["S"] < MIN_S:
                reasons.append("仅%d道S级" % st["S"])
            gaps.append((t, st["count"], st["S"], st["A"], "; ".join(reasons)))

    if gaps:
        p("【%s】缺少:" % pos)
        for t, cnt, s, a, reason in gaps:
            p("    %-22s 当前%d题(S%d A%d) — %s" % (t, cnt, s, a, reason))
    else:
        p("【%s】覆盖充足" % pos)
    p()

# ================================================================
# 4. S/A/B/C 汇总
# ================================================================
p("=" * 70)
p("4. 各岗位 S/A/B/C 总量 & Deep Dive 就绪数")
p("=" * 70)
p("%-15s %6s %5s %5s %5s %5s %6s %s" % (
    "岗位", "总题数", "S", "A", "B", "C", "S占比", "DeepDive可用"))
p("-" * 65)

for pos in ALL_POSITIONS:
    total_st = {"count": 0, "S": 0, "A": 0, "B": 0, "C": 0}
    dd_ready = 0
    for t, st in pt_stats[pos].items():
        total_st["count"] += st["count"]
        for k in ["S", "A", "B", "C"]:
            total_st[k] += st[k]
        if t != "通用" and st["count"] >= 10 and st["S"] >= 3:
            dd_ready += 1

    s_pct = total_st["S"] / total_st["count"] * 100 if total_st["count"] else 0
    p("%-15s %6d %5d %5d %5d %5d  %5.1f%%  %d个" % (
        pos, total_st["count"], total_st["S"], total_st["A"],
        total_st["B"], total_st["C"], s_pct, dd_ready))

# ================================================================
# 5. 矩阵表（可读格式）
# ================================================================
p()
p("=" * 70)
p("5. 岗位 × Topic 矩阵（数字=题量）")
p("=" * 70)
p()

# Header
header = "%-20s" % "岗位 \\ Topic"
for t in ALL_TOPICS:
    header += "%5s" % t[:5]
p(header)
p("-" * (20 + 6 * len(ALL_TOPICS)))

for pos in ALL_POSITIONS:
    row = "%-20s" % pos
    for t in ALL_TOPICS:
        cnt = pt_stats[pos].get(t, {}).get("count", 0)
        if cnt >= 10:
            row += "%5d" % cnt
        elif cnt > 0:
            row += "  %d " % cnt
        else:
            row += "    ."
    p(row)

conn.close()
p()
p("报告已生成: %s" % OUTPUT)
