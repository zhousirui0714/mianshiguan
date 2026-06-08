#!/usr/bin/env python
"""
百工面试题自动采集系统 - CLI 入口

用法：
    python scripts/run_collector.py seed          # 生成种子题库并导入
    python scripts/run_collector.py search        # 在线搜索面经
    python scripts/run_collector.py pipeline      # 完整流水线
    python scripts/run_collector.py answers       # 为已采集题目生成答案
    python scripts/run_collector.py stats         # 查看题库统计
    python scripts/run_collector.py import <file> # 从 JSON 文件导入
"""

import sys
import os
import json

# 将项目根目录加入 path
ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def cmd_seed():
    """生成种子题库并导入"""
    sys.stdout.reconfigure(encoding="utf-8")

    from scripts.question_collector.seed_data import generate_seed_file
    from scripts.question_collector.schema import CollectedQuestion
    from scripts.question_collector.deduplicator import InternalDeduplicator, DatabaseDeduplicator
    from scripts.question_collector.classifier import classify_all
    from scripts.question_collector.grader import grade_all
    from scripts.question_collector.storage import save_questions, import_to_database, print_report
    from scripts.question_collector.config import GRADED_JSON

    print("=" * 60)
    print("生成种子题库...")
    print("=" * 60)
    seed_path = os.path.join(ROOT, "data", "collected_questions", "seed_questions.json")
    generate_seed_file(seed_path)

    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = [CollectedQuestion(**d) for d in data]
    questions = InternalDeduplicator().deduplicate(questions)
    questions = DatabaseDeduplicator().deduplicate(questions)
    questions = classify_all(questions)
    questions = grade_all(questions)

    print_report(questions)
    save_questions(questions, GRADED_JSON)

    print("\n导入数据库...")
    imported = import_to_database(questions)
    print(f"\n✅ 完成! 新增 {imported} 题到数据库")

    print(f"\n提示: 可继续运行 python scripts/run_collector.py answers 生成答案")


def cmd_search():
    """在线搜索面经"""
    sys.stdout.reconfigure(encoding="utf-8")
    from scripts.question_collector.searcher import search_all_scenarios, save_search_results
    from scripts.question_collector.config import SEARCH_RESULTS_JSON

    print("=" * 60)
    print("搜索面经页面...")
    print("=" * 60)
    results = search_all_scenarios()
    save_search_results(results, SEARCH_RESULTS_JSON)

    print(f"\n搜索完成! 继续运行: python scripts/run_collector.py pipeline")


def cmd_pipeline():
    """完整流水线：搜索 -> 抓取 -> 提取 -> 去重 -> 分类 -> 评级 -> 导入"""
    sys.stdout.reconfigure(encoding="utf-8")
    from scripts.question_collector.searcher import search_all_scenarios, save_search_results
    from scripts.question_collector.extractor import extract_all_pages
    from scripts.question_collector.deduplicator import InternalDeduplicator, DatabaseDeduplicator
    from scripts.question_collector.classifier import classify_all
    from scripts.question_collector.grader import grade_all
    from scripts.question_collector.storage import save_questions, import_to_database, print_report
    from scripts.question_collector.schema import CollectedQuestion
    from scripts.question_collector.config import (
        SEARCH_RESULTS_JSON, RAW_JSON, DEDUPED_JSON,
        CLASSIFIED_JSON, GRADED_JSON,
    )

    # 1. 搜索
    print("=" * 60)
    print("阶段 1/5: 搜索面经")
    print("=" * 60)
    results = search_all_scenarios()
    save_search_results(results, SEARCH_RESULTS_JSON)

    # 2. 提取
    print("\n" + "=" * 60)
    print("阶段 2/5: 提取面试题")
    print("=" * 60)
    all_questions = extract_all_pages(results, use_llm=True, max_pages_per_scenario=30)
    flat = [q for qs in all_questions.values() for q in qs]
    save_questions(flat, RAW_JSON)

    # 3. 去重
    print("\n" + "=" * 60)
    print("阶段 3/5: 去重")
    print("=" * 60)
    questions = InternalDeduplicator().deduplicate(flat)
    questions = DatabaseDeduplicator().deduplicate(questions)
    save_questions(questions, DEDUPED_JSON)

    # 4. 分类+评级
    print("\n" + "=" * 60)
    print("阶段 4/5: 分类 + 评级")
    print("=" * 60)
    questions = classify_all(questions)
    questions = grade_all(questions)
    save_questions(questions, GRADED_JSON)

    # 5. 导入
    print("\n" + "=" * 60)
    print("阶段 5/5: 导入数据库")
    print("=" * 60)
    imported = import_to_database(questions)

    print(f"\n{'=' * 60}")
    print(f"✅ 流水线完成!")
    print(f"  采集: {len(flat)} 题")
    print(f"  去重后: {len(questions)} 题")
    print(f"  导入数据库: {imported} 题")
    print(f"{'=' * 60}")


def cmd_answers():
    """为已采集题目生成 3 级答案"""
    sys.stdout.reconfigure(encoding="utf-8")
    from scripts.question_collector.schema import CollectedQuestion
    from scripts.question_collector.answer_generator import generate_all_answers
    from scripts.question_collector.storage import save_questions, load_questions, import_to_database
    from scripts.question_collector.config import GRADED_JSON, ANSWERS_JSON

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=20, help="最多生成答案的题数")
    args, _ = parser.parse_known_args()

    questions_data = load_questions(GRADED_JSON)
    if not questions_data:
        print("没有已评级的题目，请先运行 seed 或 pipeline")
        return

    questions = [CollectedQuestion(**d) for d in questions_data]
    print(f"为 {min(len(questions), args.max)} 题生成 3 级答案...")
    questions = generate_all_answers(questions, max_questions=args.max)
    save_questions(questions, ANSWERS_JSON)

    print(f"\n导入数据库（含答案）...")
    imported = import_to_database(questions)
    print(f"✅ 完成! {imported} 题已更新答案")


def cmd_stats():
    """查看题库统计"""
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(ROOT, "data", "interview.db"))
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM questions")
        total = cur.fetchone()[0]

        print("=" * 60)
        print(f"📊 题库统计 (总计 {total} 题)")
        print("=" * 60)

        cur.execute("SELECT source_type, COUNT(*) FROM questions GROUP BY source_type ORDER BY COUNT(*) DESC")
        print("\n来源分布:")
        for r in cur.fetchall():
            print(f"  {r[0]}: {r[1]} 题")

        cur.execute("""
            SELECT s.name, COUNT(q.id)
            FROM scenarios s
            LEFT JOIN questions q ON s.id = q.scenario_id
            GROUP BY s.id ORDER BY COUNT(q.id) DESC
        """)
        print("\n场景分布:")
        for r in cur.fetchall():
            print(f"  {r[0]}: {r[1]} 题")

        cur.execute("SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty ORDER BY difficulty")
        print("\n难度分布:")
        for r in cur.fetchall():
            print(f"  难度{r[0]}: {r[1]} 题")

        conn.close()
    except Exception as e:
        print(f"错误: {e}")


def cmd_import(filepath):
    """从 JSON 文件导入题目"""
    sys.stdout.reconfigure(encoding="utf-8")
    from scripts.question_collector.schema import CollectedQuestion
    from scripts.question_collector.deduplicator import InternalDeduplicator, DatabaseDeduplicator
    from scripts.question_collector.classifier import classify_all
    from scripts.question_collector.grader import grade_all
    from scripts.question_collector.storage import import_to_database, save_questions, print_report

    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = [CollectedQuestion(**d) for d in data]
    print(f"加载: {len(questions)} 题")

    questions = InternalDeduplicator().deduplicate(questions)
    questions = DatabaseDeduplicator().deduplicate(questions)
    questions = classify_all(questions)
    questions = grade_all(questions)
    print_report(questions)

    if input("\n是否导入数据库? (y/n): ").lower() == "y":
        imported = import_to_database(questions)
        print(f"导入完成: +{imported} 题")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    commands = {
        "seed": cmd_seed,
        "search": cmd_search,
        "pipeline": cmd_pipeline,
        "answers": cmd_answers,
        "stats": cmd_stats,
    }

    if cmd in commands:
        commands[cmd]()
    elif cmd == "import" and len(sys.argv) >= 3:
        cmd_import(sys.argv[2])
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
