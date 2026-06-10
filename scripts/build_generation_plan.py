# -*- coding: utf-8 -*-
"""
Step 5-6: Question Generation Plan + Top 20 Gaps

Reads:  gap_report.json
Output: question_generation_plan.json, top_gaps.md
"""
import sys, os, json

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
GAP_PATH = os.path.join(OUTPUT_DIR, "gap_report.json")

with open(GAP_PATH, "r", encoding="utf-8") as f:
    gaps = json.load(f)

# Build generation plan
plan = {}
all_gaps_flat = []  # for top 20 sorting

for pos, pos_gaps in gaps.items():
    plan[pos] = {}
    for g in pos_gaps:
        topic = g["topic"]
        status = g["status"]
        missing_sa = g["missing_sa"]

        if status == "PASS":
            continue

        # Priority
        if status == "FAIL":
            priority = "P0"
        else:
            priority = "P1"

        # Split missing_sa into S and A needs
        # Roughly 1 S : 2 A ratio for a balanced question set
        if missing_sa <= 0:
            continue

        need_s = max(1, round(missing_sa * 0.3))
        need_a = missing_sa - need_s

        plan[pos][topic] = {
            "need_S": need_s,
            "need_A": need_a,
            "priority": priority,
            "missing_sa": missing_sa,
        }

        all_gaps_flat.append({
            "position": pos,
            "topic": topic,
            "status": status,
            "missing_sa": missing_sa,
            "priority": priority,
        })

# Write question_generation_plan.json
plan_path = os.path.join(OUTPUT_DIR, "question_generation_plan.json")
with open(plan_path, "w", encoding="utf-8") as f:
    json.dump(plan, f, ensure_ascii=False, indent=2)
print(f"Generation plan: {plan_path}")

# Top 20 gaps by missing_sa descending
all_gaps_flat.sort(key=lambda x: (-x["missing_sa"], x["position"], x["topic"]))
top20 = all_gaps_flat[:20]

# Write top_gaps.md
top_lines = []
top_lines.append("# Top 20 Gaps\n\n")
top_lines.append("| Rank | Position | Topic | Status | Missing SA | Priority |\n")
top_lines.append("|------|----------|-------|--------|------------|----------|\n")
for i, g in enumerate(top20, 1):
    top_lines.append(f"| {i} | {g['position']} | {g['topic']} | {g['status']} | {g['missing_sa']} | {g['priority']} |\n")

top_path = os.path.join(OUTPUT_DIR, "top_gaps.md")
with open(top_path, "w", encoding="utf-8") as f:
    f.writelines(top_lines)
print(f"Top gaps: {top_path}")

# Final stats
total_missing_sa = sum(g["missing_sa"] for g in all_gaps_flat)
total_need_s = sum(plan[pos][t]["need_S"] for pos in plan for t in plan[pos])
total_need_a = sum(plan[pos][t]["need_A"] for pos in plan for t in plan[pos])

print(f"\n=== Final Stats ===")
print(f"PASS count: {sum(1 for g in all_gaps_flat if g['status'] == 'PASS')}")
print(f"WARN count: {sum(1 for g in all_gaps_flat if g['status'] == 'WARN')}")
print(f"FAIL count: {sum(1 for g in all_gaps_flat if g['status'] == 'FAIL')}")
print(f"Total gaps: {len(all_gaps_flat)}")
print(f"Total missing SA: {total_missing_sa}")
print(f"Total S/A questions needed: {total_need_s} S + {total_need_a} A = {total_need_s + total_need_a}")
print(f"\nTop 5 gaps:")
for g in top20[:5]:
    print(f"  {g['position']} / {g['topic']}: missing {g['missing_sa']} SA ({g['status']})")
