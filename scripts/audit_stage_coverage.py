# -*- coding: utf-8 -*-
"""审计各岗位在各面试阶段的题目覆盖情况"""
import sys, os, json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")

import sqlite3
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

all_rows = conn.execute("SELECT * FROM questions").fetchall()
print(f"总题数: {len(all_rows)}")

# ================================================================
# 统计：岗位 × 阶段
# ================================================================

# position -> stage -> count
pos_stage = defaultdict(lambda: defaultdict(int))
# stage -> count (全局)
stage_total = defaultdict(int)

all_positions = ["Python后端", "Java后端", "Go后端", "前端",
                 "测试开发", "算法工程师", "AI工程师", "产品经理"]

for r in all_rows:
    d = dict(r)
    tp_str = d.get("target_positions", "") or "[]"
    try:
        tps = json.loads(tp_str)
    except:
        tps = []
    stage = (d.get("interview_stage", "") or "basic").strip()
    stage_total[stage] += 1
    for p in tps:
        pos_stage[p][stage] += 1

# ================================================================
# 输出
# ================================================================

print("\n" + "=" * 60)
print("  Stage Coverage by Position")
print("=" * 60)

stages = ["intro", "project", "basic", "advanced", "system_design", "behavior"]
header = f"{'Position':14s}" + "".join(f"{s:14s}" for s in stages)
print(f"\n{header}")
print("-" * len(header))

for p in all_positions:
    row = f"{p:14s}"
    for s in stages:
        cnt = pos_stage[p].get(s, 0)
        row += f"{cnt:5d}{'':9s}"
    print(row)

print("\n" + "-" * len(header))
row = f"{'TOTAL':14s}"
for s in stages:
    cnt = stage_total.get(s, 0)
    row += f"{cnt:5d}{'':9s}"
print(row)

# ================================================================
# 覆盖不足检测
# ================================================================

print("\n" + "=" * 60)
print("  Coverage Warnings (< 5 questions per stage)")
print("=" * 60)

MIN_COUNT = 5
has_warning = False
for p in all_positions:
    for s in stages:
        cnt = pos_stage[p].get(s, 0)
        if cnt < MIN_COUNT:
            print(f"  WARNING: {p} - {s}: only {cnt} questions (min {MIN_COUNT})")
            has_warning = True

if not has_warning:
    print("  All positions have sufficient coverage across all stages.")

# ================================================================
# 阶段分布占比
# ================================================================

print("\n" + "=" * 60)
print("  Stage Distribution (Global)")
print("=" * 60)

total = len(all_rows)
for s in stages:
    cnt = stage_total.get(s, 0)
    pct = cnt / total * 100 if total else 0
    bar_len = int(pct / 2)
    bar = "#" * bar_len
    print(f"  {s:15s}: {cnt:5d} ({pct:5.1f}%) {bar}")

conn.close()
print("\n[audit_stage_coverage] Done")
