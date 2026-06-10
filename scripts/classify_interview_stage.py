# -*- coding: utf-8 -*-
"""
Classification Script: interview_stage

Classify all questions by interview stage based on text content.
Stages: intro, project, basic, advanced, system_design, behavior
"""
import sys, os, sqlite3
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")


def classify_stage(text: str, question_level: str = "",
                   company: str = "", category: str = "",
                   tags_str: str = "") -> str:
    """
    Classify a question into an interview stage.
    Priority chain: intro → system_design → behavior → project → advanced → basic
    """
    t = text.lower()

    # ================================================================
    # 1. intro: 自我介绍类
    # ================================================================
    if any(kw in t for kw in ["自我介绍", "介绍自己", "介绍一下你自己",
                                "做自我介绍", "介绍你的", "说说你自己",
                                "简单介绍一下你", "做一个自我介绍"]):
        return "intro"

    # ================================================================
    # 2. system_design: 系统设计类
    # ================================================================
    system_design_kw = [
        "设计一个", "系统设计", "架构设计",
        "高并发", "高可用", "秒杀系统",
        "分布式 id", "分布式锁", "分布式事务",
        "配置中心", "调度系统", "消息队列设计",
        "全链路", "灰度发布",
    ]
    if any(kw in t for kw in system_design_kw):
        return "system_design"

    # ================================================================
    # 3. behavior: 反问/行为类
    # ================================================================
    behavior_kw = [
        "你的优点", "你的缺点", "你的优势", "你的不足",
        "职业规划", "为什么选择", "还有什么问题",
        "谈谈你对", "你如何看待", "你觉得你",
        "你的期望", "你的性格", "你的抗压",
        "如何处理", "你最大的挑战", "最有成就感",
        "别人怎么评价", "核心竞争力",
        "你对加班", "你对薪资", "你的离职",
        "五年规划", "三年规划",
    ]
    if any(kw in t for kw in behavior_kw):
        return "behavior"

    # ================================================================
    # 4. project: 项目经验类
    # ================================================================
    project_kw = [
        "项目", "项目经验", "项目中", "项目经历",
        "你做过", "你实现", "你参与", "你负责",
        "你在项目中", "描述一个", "分享一个",
        "stsr法则", "star法则",
    ]
    if any(kw in t for kw in project_kw):
        return "project"

    # ================================================================
    # 5. system_design (secondary): 架构/系统关键词
    # ================================================================
    # 更宽松的系统设计检测
    sys_design_2nd = [
        "该如何设计", "如何实现一个", "怎么实现一个",
        "高可用 mysql", "高可用架构",
        "分库分表", "分布式",
    ]
    if any(kw in t for kw in sys_design_2nd):
        return "system_design"

    # ================================================================
    # 6. advanced: 高阶技术（深挖级）
    # ================================================================
    advanced_kw = [
        "底层原理", "源码分析", "源码实现",
        "jvm 调优", "jvm 优化",
        "full gc", "gc 调优",
        "分布式事务", "cap 权衡",
        "paxos", "raft", "一致性算法",
        "mysql 主从同步延迟", "mysql 分库分表",
        "redis 集群", "redis 哨兵", "redis 分片",
        "kafka 分区", "kafka 副本",
        "epoll 为什么高效", "零拷贝",
        "c10k", "c1000k",
        "tcp 拥塞控制",
        "https 握手",
        "http 2.0", "http 3.0", "quic",
        "synchronized 的底层",
        "cas 的原理",
        "lo ra", "qlo ra", "adalo ra",
        "transformer", "attention 机制",
        "moe", "混合专家",
        "rope", "位置编码",
        "强化学习", "rlhf", "sft",
        "模型量化", "模型压缩",
        "vllm", "tgi",
        "pre train", "continue pretrain",
        "灾难性遗忘",
        "全链路压测",
        "流量回放",
    ]
    if any(kw in t for kw in advanced_kw):
        return "advanced"

    # ================================================================
    # 7. project (secondary): 含"项目"但非明确问项目经验的
    # ================================================================
    if "项目" in t:
        return "project"

    # ================================================================
    # 8. behavior (secondary for AI questions about AI products)
    # ================================================================
    # Some PM questions might be caught here

    # ================================================================
    # 9. basic: 所有其他技术问题
    # ================================================================
    return "basic"


# ================================================================
# Main
# ================================================================
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Ensure column exists
try:
    conn.execute("ALTER TABLE questions ADD COLUMN interview_stage TEXT DEFAULT 'basic'")
    conn.commit()
    print("[migrate] 新增 interview_stage 列")
except sqlite3.OperationalError:
    pass

all_rows = conn.execute("SELECT * FROM questions").fetchall()
print(f"总题数: {len(all_rows)}")

stage_counts = defaultdict(int)
level_counts = defaultdict(lambda: defaultdict(int))
updated = 0

for row in all_rows:
    d = dict(row)
    text = d.get("question_text", "") or ""
    qid = d["id"]
    question_level = (d.get("question_level", "C") or "C").strip().upper()
    company = d.get("company", "") or ""
    category = d.get("category", "") or ""
    tags_str = d.get("tags", "") or ""

    stage = classify_stage(text, question_level, company, category, tags_str)
    stage_counts[stage] += 1
    level_counts[question_level][stage] += 1

    conn.execute(
        "UPDATE questions SET interview_stage = ? WHERE id = ?",
        (stage, qid)
    )
    updated += 1

conn.commit()

print(f"已更新: {updated}")
print()
print("阶段分布 (interview_stage):")
for s in ["intro", "project", "basic", "advanced", "system_design", "behavior"]:
    cnt = stage_counts.get(s, 0)
    pct = cnt / len(all_rows) * 100
    print(f"  {s:15s}: {cnt:4d} ({pct:5.1f}%)")

print()
print("等级 × 阶段交叉统计:")
print(f"  {'等级':5s} {'intro':6s} {'project':8s} {'basic':6s} {'advanced':9s} {'sys_design':11s} {'behavior':9s}")
for lev in ["S", "A", "B", "C"]:
    i = level_counts[lev].get("intro", 0)
    p = level_counts[lev].get("project", 0)
    b = level_counts[lev].get("basic", 0)
    a = level_counts[lev].get("advanced", 0)
    sd = level_counts[lev].get("system_design", 0)
    bh = level_counts[lev].get("behavior", 0)
    print(f"  {lev:5s}: {i:6d} {p:8d} {b:6d} {a:9d} {sd:11d} {bh:9d}")

conn.close()
print("\n[classify_interview_stage] Done")
