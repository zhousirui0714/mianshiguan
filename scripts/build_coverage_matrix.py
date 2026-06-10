# -*- coding: utf-8 -*-
"""
Step 1: Build Coverage Matrix

Output: coverage_matrix.json
  position × topic × stage × level
"""
import sys, os, json, sqlite3
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
all_rows = conn.execute("SELECT * FROM questions").fetchall()
total = len(all_rows)

ALL_POSITIONS = [
    "Python后端", "Java后端", "Go后端", "前端",
    "测试开发", "算法工程师", "AI工程师", "产品经理",
]

STAGES = ["intro", "project", "basic", "advanced", "system_design", "behavior"]

# position -> topic -> stage -> {S, A, B, C}
matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {"S": 0, "A": 0, "B": 0, "C": 0})))

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

    # Normalize level
    if lev not in ["S", "A", "B", "C"]:
        lev = "C"

    for pos in positions:
        if pos not in ALL_POSITIONS:
            continue
        for topic in topics:
            matrix[pos][topic][stage][lev] += 1

# Convert to plain dict for JSON serialization
output = {}
for pos in ALL_POSITIONS:
    output[pos] = {}
    for topic, stage_dict in matrix[pos].items():
        output[pos][topic] = {}
        for stage in STAGES:
            output[pos][topic][stage] = dict(stage_dict[stage])

# Write
output_path = os.path.join(OUTPUT_DIR, "coverage_matrix.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"总题数: {total}")
print(f"输出: {output_path}")
print(f"覆盖矩阵: {len(output)} 个岗位")

# Quick summary
for pos in ALL_POSITIONS:
    topic_count = len(output[pos])
    total_cells = sum(
        sum(stage_levels.values())
        for topic_data in output[pos].values()
        for stage_levels in topic_data.values()
    )
    print(f"  {pos}: {topic_count} 个 topic, {total_cells} 题")

conn.close()
