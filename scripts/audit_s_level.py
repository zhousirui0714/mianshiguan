# -*- coding: utf-8 -*-
"""导出全部 S 级题目，供人工审计"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")
db = DatabaseManager(DB_PATH)

all_qs = db.get_questions(scenario_id="job_interview")
s_qs = [q for q in all_qs if (q.get("question_level") or "C").strip().upper() == "S"]

print(f"S 级总数: {len(s_qs)}")
print()

for i, q in enumerate(s_qs, 1):
    text = q.get("question_text", "").strip()
    company = q.get("company", "").strip() or "(空)"
    position = q.get("position", "").strip() or "(空)"
    source_type = q.get("source_type", "").strip() or "(空)"
    print(f"--- 第{i}题 ---")
    print(f"题目: {text[:120]}")
    print(f"公司: {company}  |  岗位: {position}  |  来源: {source_type}")
    print()
