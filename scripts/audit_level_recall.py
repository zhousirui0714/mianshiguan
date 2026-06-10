# -*- coding: utf-8 -*-
"""
Audit Script: 验证等级召回系统实际效果

统计 100 次 _weighted_question_recall() 的 retrieved_questions 组成。
不修改任何代码，只做审计和统计。
"""
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database import DatabaseManager
from src.web.blueprints.api_examiner import _weighted_question_recall

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")


def main():
    db = DatabaseManager(DB_PATH)

    scenario_id = "job_interview"
    N = 100

    # ============================================================
    # 1. DB 全量统计（作为基准）
    # ============================================================
    all_qs = db.get_questions(scenario_id=scenario_id)
    total = len(all_qs)
    level_counts = {"S": 0, "A": 0, "B": 0, "C": 0}
    for q in all_qs:
        lev = (q.get("question_level") or "C").strip().upper()
        if lev not in level_counts:
            lev = "C"
        level_counts[lev] += 1

    print("=" * 60)
    print(f"  全量题库统计（{scenario_id}）")
    print("=" * 60)
    print(f"  总数: {total}")
    for lev in ["S", "A", "B", "C"]:
        pct = level_counts[lev] / total * 100 if total else 0
        print(f"  [{lev}] {level_counts[lev]} 题 ({pct:.1f}%)")

    # ============================================================
    # 2. 100 次随机召回模拟
    # ============================================================
    print()
    print("=" * 60)
    print(f"  100 次随机召回统计")
    print("=" * 60)

    all_results = []  # list of dict: {level: count}

    for i in range(N):
        # 固定 seed，保证每次独立随机
        random.seed(i + 42)
        retrieved = _weighted_question_recall(
            db, scenario_id=scenario_id,
            target_position="",
            target_company="",
            limit=20
        )

        counts = {"S": 0, "A": 0, "B": 0, "C": 0}
        for q in retrieved:
            lev = (q.get("question_level") or "C").strip().upper()
            if lev not in counts:
                lev = "C"
            counts[lev] += 1
        counts["total"] = len(retrieved)
        all_results.append(counts)

    # ============================================================
    # 3. 平均统计
    # ============================================================
    print()
    print("-" * 60)
    print("  3. 平均每次召回组成")
    print("-" * 60)
    avg = {"S": 0, "A": 0, "B": 0, "C": 0}
    for r in all_results:
        for lev in ["S", "A", "B", "C"]:
            avg[lev] += r[lev]
    N_actual = len(all_results)
    for lev in ["S", "A", "B", "C"]:
        avg[lev] /= N_actual

    total_avg = sum(avg.values())
    print(f"  平均召回总数: {total_avg:.1f}")
    for lev in ["S", "A", "B", "C"]:
        pct = avg[lev] / total_avg * 100 if total_avg else 0
        print(f"  [{lev}] 平均 {avg[lev]:.1f} 题 ({pct:.1f}%)")

    # ============================================================
    # 4. 输出 10 次样例
    # ============================================================
    print()
    print("-" * 60)
    print("  4. 10 次样例明细")
    print("-" * 60)
    for i in range(10):
        r = all_results[i]
        src_info = ""
        if r["B"] > 0 or r["C"] > 0:
            reasons = []
            if r["B"] > 0:
                reasons.append(f"B={r['B']}（S+A 不足以填满20题）")
            if r["C"] > 0:
                reasons.append(f"C={r['C']}（S+A+B 仍不足以填满20题）")
            src_info = "  ← 含非S/A级: " + "; ".join(reasons)
        print(f"  第{i+1:2d}次:  S={r['S']:2d}  A={r['A']:2d}  B={r['B']:2d}  C={r['C']:2d}{src_info}")

    # ============================================================
    # 5. 极端值统计
    # ============================================================
    print()
    print("-" * 60)
    print("  5. 极端值统计")
    print("-" * 60)
    s_values = [r["S"] for r in all_results]
    a_values = [r["A"] for r in all_results]
    b_values = [r["B"] for r in all_results]
    c_values = [r["C"] for r in all_results]
    print(f"  S: min={min(s_values)}, max={max(s_values)}, avg={sum(s_values)/N:.1f}")
    print(f"  A: min={min(a_values)}, max={max(a_values)}, avg={sum(a_values)/N:.1f}")
    print(f"  B: min={min(b_values)}, max={max(b_values)}, avg={sum(b_values)/N:.1f}")
    print(f"  C: min={min(c_values)}, max={max(c_values)}, avg={sum(c_values)/N:.1f}")

    # ============================================================
    # 6. 判断结论
    # ============================================================
    print()
    print("=" * 60)
    print("  6. 结论判断")
    print("=" * 60)

    # 检查是否有任何 B/C 出现
    has_b = any(r["B"] > 0 for r in all_results)
    has_c = any(r["C"] > 0 for r in all_results)
    b_ratio = sum(r["B"] for r in all_results) / (N * 20) * 100
    c_ratio = sum(r["C"] for r in all_results) / (N * 20) * 100
    sa_only_ratio = sum(1 for r in all_results if r["B"] == 0 and r["C"] == 0) / N * 100

    print(f"\n  纯 S+A 占比: {sa_only_ratio:.1f}%（{sum(1 for r in all_results if r['B'] == 0 and r['C'] == 0)}/{N} 次）")
    print(f"  含 B 级占比:  {b_ratio:.1f}%")
    print(f"  含 C 级占比:  {c_ratio:.1f}%")

    if sa_only_ratio == 100:
        print("\n  [结论] 完全满足：100% 只使用 S+A 级题目")
    elif b_ratio > 0 and c_ratio == 0:
        print(f"\n  [结论] 基本满足：{sa_only_ratio:.1f}% 的会话只使用 S+A")
        print(f"         出现 B 级 ({b_ratio:.1f}%) — S+A 数量不足以填满 20 题时自动回退")
    elif c_ratio > 0:
        print(f"\n  [结论] 部分满足：{sa_only_ratio:.1f}% 的会话只使用 S+A")
        print(f"         出现 B 级 ({b_ratio:.1f}%)、C 级 ({c_ratio:.1f}%) — S+A+B 仍不足以填满 20 题")
    else:
        print("\n  [结论] 未知状态，请检查代码")

    # ============================================================
    # 7. B/C 出现时的具体原因
    # ============================================================
    if has_b or has_c:
        print()
        print("-" * 60)
        print("  7. B/C 出现原因分析")
        print("-" * 60)
        b_trials = [i for i, r in enumerate(all_results) if r["B"] > 0]
        c_trials = [i for i, r in enumerate(all_results) if r["C"] > 0]
        print(f"  出现 B 的次数: {len(b_trials)}/{N}")
        print(f"  出现 C 的次数: {len(c_trials)}/{N}")
        # 分析单次最大 B/C 情况
        max_b = max(b_values)
        max_c = max(c_values)
        print(f"  单次最多 B: {max_b} 题")
        print(f"  单次最多 C: {max_c} 题")
        # 原因说明
        print()
        print("  原因:")
        print("  a) job_interview 场景的 S 级全部来自 real_interview，")
        print("     且 _pick_questions_by_source() 对 real_interview 有 10 题上限。")
        print("     S 级中 real_interview 可能超过 10 题但只有最多 10 题被选入，")
        print("     剩余名额分配给 A 级。")
        print("  b) 当 S+A 可用的 non-ai 来源题目不足 20 题时，")
        print("     系统自动回退到 B 级补充。")
        print("  c) 如果 B 级仍不足，继续回退到 C 级。")

    print()
    print("[audit] 完成")


if __name__ == "__main__":
    main()
