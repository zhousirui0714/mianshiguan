"""
百工面试题自动采集系统 - 主控流程

完整流水线：
1. 搜索：通过 DuckDuckGo 搜索真实面经页面
2. 抓取：爬取页面内容
3. 提取：从页面中提取面试问题
4. 去重：内部去重 + 与现有题库去重
5. 分类：按场景和类别分类
6. 评级：S/A/B/C 评级，只保留 S 和 A
7. 存储：保存 JSON + 导入数据库
8. 答案生成：为每道题生成 3 级答案（可选）

用法：
    python -m scripts.question_collector.main --all
    python -m scripts.question_collector.main --search-only
    python -m scripts.question_collector.main --scenario job_interview
    python -m scripts.question_collector.main --import-db
"""

import sys
import os
import argparse
import time
from datetime import datetime

# 确保能找到项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from .config import (
    OUTPUT_DIR, RAW_JSON, DEDUPED_JSON, CLASSIFIED_JSON,
    GRADED_JSON, FINAL_JSON, ANSWERS_JSON, ALL_JSON,
)
from .schema import CollectedQuestion
from .searcher import search_all_scenarios, save_search_results
from .extractor import extract_all_pages
from .deduplicator import InternalDeduplicator, DatabaseDeduplicator
from .classifier import classify_all
from .grader import grade_all
from .answer_generator import generate_all_answers
from .storage import (
    save_questions, load_questions, save_by_scenario,
    print_report, import_to_database,
)


SEARCH_RESULTS_JSON = os.path.join(OUTPUT_DIR, "00_search_results.json")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="百工面试题自动采集系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python -m scripts.question_collector.main --all
  python -m scripts.question_collector.main --search-only
  python -m scripts.question_collector.main --scenario job_interview
  python -m scripts.question_collector.main --import-db
  python -m scripts.question_collector.main --generate-answers
        """,
    )

    parser.add_argument(
        "--all", action="store_true",
        help="执行完整流水线（搜索→抓取→提取→去重→分类→评级→存储）",
    )
    parser.add_argument(
        "--search-only", action="store_true",
        help="仅执行搜索阶段",
    )
    parser.add_argument(
        "--scenario", type=str, default=None,
        help="仅处理指定场景（如 job_interview）",
    )
    parser.add_argument(
        "--max-pages", type=int, default=50,
        help="每个场景最多抓取页数 (默认: 50)",
    )
    parser.add_argument(
        "--max-questions", type=int, default=100,
        help="每次最多处理题数 (默认: 100)",
    )
    parser.add_argument(
        "--import-db", action="store_true",
        help="将评级后的题目导入数据库",
    )
    parser.add_argument(
        "--generate-answers", action="store_true",
        help="为采集的题目生成3级答案",
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="不使用 LLM 辅助提取（仅规则提取）",
    )

    return parser.parse_args()


def run_search(scenarios=None):
    """阶段1：搜索"""
    print(f"\n{'#'*60}")
    print(f"# 阶段1：搜索面经页面")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = search_all_scenarios(scenarios=scenarios)
    save_search_results(results, SEARCH_RESULTS_JSON)
    return results


def run_extract(search_results, use_llm=True, max_pages=50):
    """阶段2：抓取+提取"""
    print(f"\n{'#'*60}")
    print(f"# 阶段2：抓取页面 + 提取面试题")
    print(f"{'#'*60}")

    all_questions = extract_all_pages(
        search_results, use_llm=use_llm, max_pages_per_scenario=max_pages
    )

    # 合并所有场景
    flat_questions = []
    for sc, qs in all_questions.items():
        flat_questions.extend(qs)

    save_questions(flat_questions, RAW_JSON)
    print(f"原始提取: {len(flat_questions)} 题")
    return flat_questions


def run_dedup(questions):
    """阶段3：去重"""
    print(f"\n{'#'*60}")
    print(f"# 阶段3：去重")
    print(f"{'#'*60}")

    # 内部去重
    internal_dedup = InternalDeduplicator()
    questions = internal_dedup.deduplicate(questions)

    # 与数据库去重
    db_dedup = DatabaseDeduplicator()
    questions = db_dedup.deduplicate(questions)

    save_questions(questions, DEDUPED_JSON)
    print(f"去重后: {len(questions)} 题")
    return questions


def run_classify(questions):
    """阶段4：分类"""
    print(f"\n{'#'*60}")
    print(f"# 阶段4：分类（场景 + 类别）")
    print(f"{'#'*60}")

    questions = classify_all(questions)
    save_questions(questions, CLASSIFIED_JSON)
    return questions


def run_grade(questions):
    """阶段5：评级"""
    print(f"\n{'#'*60}")
    print(f"# 阶段5：S/A/B/C 评级")
    print(f"{'#'*60}")

    questions = grade_all(questions)

    # 保存所有评级结果 + 仅保留S/A
    save_questions(questions, GRADED_JSON)

    # 按场景保存
    save_by_scenario(questions)

    print_report(questions)
    return questions


def run_answers(questions, max_questions=100):
    """阶段6：生成答案（可选）"""
    print(f"\n{'#'*60}")
    print(f"# 阶段6：生成3级答案")
    print(f"{'#'*60}")

    questions = generate_all_answers(questions, max_questions=max_questions)
    save_questions(questions, ANSWERS_JSON)
    return questions


def run_import(questions):
    """阶段7：导入数据库"""
    print(f"\n{'#'*60}")
    print(f"# 阶段7：导入数据库")
    print(f"{'#'*60}")

    imported = import_to_database(questions)
    return imported


def main():
    """主入口"""
    args = parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           百工面试题自动采集系统 v1.0                         ║
║           目标: 3000+ 真实面经面试题                          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    scenarios = [args.scenario] if args.scenario else None

    # 完整流水线
    if args.all:
        results = run_search(scenarios)
        questions = run_extract(results, use_llm=not args.no_llm, max_pages=args.max_pages)
        questions = run_dedup(questions)
        questions = run_classify(questions)
        questions = run_grade(questions)

        # 保存最终结果
        save_questions(questions, FINAL_JSON)
        print(f"\n✅ 采集完成! 最终保留 {len(questions)} 题")

        # 可选导入数据库
        if input("\n是否导入数据库? (y/n): ").lower() == 'y':
            run_import(questions)

        # 可选生成答案
        if input("是否生成3级答案? (y/n, 使用Qwen API): ").lower() == 'y':
            questions = run_answers(questions, max_questions=args.max_questions)
            save_questions(questions, ALL_JSON)

    elif args.search_only:
        run_search(scenarios)

    elif args.import_db:
        # 从 FINAL_JSON 导入
        questions_data = load_questions(FINAL_JSON)
        if questions_data:
            questions = [CollectedQuestion(**d) for d in questions_data]
            run_import(questions)

    elif args.generate_answers:
        # 从 FINAL_JSON 加载并生成答案
        questions_data = load_questions(FINAL_JSON)
        if questions_data:
            questions = [CollectedQuestion(**d) for d in questions_data]
            questions = run_answers(questions, max_questions=args.max_questions)
            save_questions(questions, ALL_JSON)

    else:
        print("请指定操作模式: --all / --search-only / --import-db / --generate-answers")
        print("使用 --help 查看帮助")


if __name__ == "__main__":
    main()
