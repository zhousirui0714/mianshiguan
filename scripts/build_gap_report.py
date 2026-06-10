# -*- coding: utf-8 -*-
"""
Step 2-4: Coverage Score + Auto Grade + Gap Analysis

Reads:  coverage_matrix.json
Output: coverage_report.md, gap_report.json
"""
import sys, os, json, math
from collections import defaultdict

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
MATRIX_PATH = os.path.join(OUTPUT_DIR, "coverage_matrix.json")

with open(MATRIX_PATH, "r", encoding="utf-8") as f:
    matrix = json.load(f)

# Scoring
SCORE_MAP = {"S": 4, "A": 3, "B": 2, "C": 1}

ALL_POSITIONS = sorted(matrix.keys())

# coverage_report.md
report_lines = []
report_lines.append("# Coverage Report\n")
report_lines.append("| Position | Topic | S | A | B | C | Score | Status |\n")
report_lines.append("|----------|-------|---|---|---|-------|--------|--------|\n")

# gap data
gaps = {}  # position -> list of gap dicts

# stats
pass_count = 0
warn_count = 0
fail_count = 0

for pos in ALL_POSITIONS:
    pos_gaps = []
    for topic, stage_dict in sorted(matrix[pos].items()):
        # Sum across all stages
        s = sum(stage_dict[stage].get("S", 0) for stage in stage_dict)
        a = sum(stage_dict[stage].get("A", 0) for stage in stage_dict)
        b = sum(stage_dict[stage].get("B", 0) for stage in stage_dict)
        c = sum(stage_dict[stage].get("C", 0) for stage in stage_dict)

        score = s * SCORE_MAP["S"] + a * SCORE_MAP["A"] + b * SCORE_MAP["B"] + c * SCORE_MAP["C"]
        sa_count = s + a

        # Grade
        if sa_count >= 20:
            status = "PASS"
            pass_count += 1
        elif sa_count >= 10:
            status = "WARN"
            warn_count += 1
        else:
            status = "FAIL"
            fail_count += 1

        report_lines.append(f"| {pos} | {topic} | {s} | {a} | {b} | {c} | {score} | {status} |\n")

        # Gap data (only WARN and FAIL)
        if status in ("WARN", "FAIL"):
            missing_sa = max(20 - sa_count, 0)
            pos_gaps.append({
                "topic": topic,
                "status": status,
                "S": s,
                "A": a,
                "B": b,
                "C": c,
                "score": score,
                "sa_count": sa_count,
                "missing_sa": missing_sa,
            })

    if pos_gaps:
        gaps[pos] = pos_gaps

# Summary section
report_lines.append(f"\n## Summary\n\n")
report_lines.append(f"- **PASS**: {pass_count}\n")
report_lines.append(f"- **WARN**: {warn_count}\n")
report_lines.append(f"- **FAIL**: {fail_count}\n")
report_lines.append(f"- **Total Position x Topic**: {pass_count + warn_count + fail_count}\n")

# Write coverage_report.md
report_path = os.path.join(OUTPUT_DIR, "coverage_report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.writelines(report_lines)
print(f"Coverage report: {report_path}")

# Write gap_report.json
gap_path = os.path.join(OUTPUT_DIR, "gap_report.json")
with open(gap_path, "w", encoding="utf-8") as f:
    json.dump(gaps, f, ensure_ascii=False, indent=2)
print(f"Gap report: {gap_path}")

# Print stats for parent script consumption
print(f"\nStats:")
print(f"  PASS: {pass_count}")
print(f"  WARN: {warn_count}")
print(f"  FAIL: {fail_count}")
print(f"  Total: {pass_count + warn_count + fail_count}")
