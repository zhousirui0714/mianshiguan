# -*- coding: utf-8 -*-
"""扩库后审计报告生成"""
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
# 统计
# ================================================================

# 1. 来源分布
source_count = defaultdict(int)
for r in all_rows:
    d = dict(r)
    src = d.get("source", "") or "未知"
    source_count[src] += 1

# Top 20
top20 = sorted(source_count.items(), key=lambda x: -x[1])[:20]

# 2. source_type 分布
st_count = defaultdict(int)
for r in all_rows:
    st = dict(r).get("source_type", "unknown") or "unknown"
    st_count[st] += 1

# 3. 岗位 × 等级 (用 target_positions)
tp_level = defaultdict(lambda: defaultdict(int))
qs_with_tp = 0
for r in all_rows:
    d = dict(r)
    tp_str = d.get("target_positions", "") or "[]"
    try:
        tps = json.loads(tp_str)
    except:
        tps = []
    if tps:
        qs_with_tp += 1
    lev = (d.get("question_level", "C") or "C").strip().upper()
    for p in tps:
        tp_level[p][lev] += 1

# 4. scenario 统计
scenario_count = defaultdict(int)
for r in all_rows:
    sid = dict(r).get("scenario_id", "unknown")
    scenario_count[sid] += 1

# ================================================================
# 输出
# ================================================================
print("\n" + "=" * 60)
print("  专项扩库完成报告")
print("=" * 60)

print(f"\n  总题数: {len(all_rows)}")
print(f"  有 target_positions 标记: {qs_with_tp}")

print(f"\n  场景分布:")
for sid, cnt in sorted(scenario_count.items(), key=lambda x: -x[1]):
    print(f"    {sid}: {cnt}")

print(f"\n  source_type 分布:")
total = len(all_rows)
for st in ["real_interview", "open_source", "ai_generated"]:
    cnt = st_count.get(st, 0)
    pct = cnt / total * 100 if total else 0
    print(f"    {st}: {cnt} ({pct:.1f}%)")

print(f"\n  real_interview 占比: {st_count.get('real_interview', 0)/total*100:.1f}%")

print(f"\n  岗位 × 等级分布（基于 target_positions）:")
all_positions = ["Python后端", "Java后端", "Go后端", "前端",
                 "测试开发", "算法工程师", "AI工程师", "产品经理"]
print(f"  {'岗位':12s} {'S级':5s} {'A级':5s} {'B级':5s} {'C级':5s} {'S+A':5s}")
for p in all_positions:
    s = tp_level[p].get("S", 0)
    a = tp_level[p].get("A", 0)
    b = tp_level[p].get("B", 0)
    c = tp_level[p].get("C", 0)
    sa = s + a
    flag = "充足" if sa >= 20 else "不足"
    print(f"  {p:12s} {s:4d}  {a:4d}  {b:4d}  {c:4d}  {sa:4d}  {flag}")

print(f"\n  Top 20 来源统计:")
for i, (src, cnt) in enumerate(top20, 1):
    print(f"  {i:2d}. {src:45s} {cnt}")

# 扩库前数据（静态记录）
before = 1146
after = len(all_rows)
new_count = after - before
print(f"\n  扩库前: {before} → 扩库后: {after} (+{new_count})")

conn.close()
