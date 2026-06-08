#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动题库扩充工具

从多个 GitHub 开源题库拉取面试题，自动解析分类、去重后导入 SQLite。

用法:
    python update_questions.py                  # 全量更新
    python update_questions.py --sources 0 2    # 只更新指定索引的数据源（见 config.py SOURCES）
    python update_questions.py --list           # 列出可用数据源
    python update_questions.py --dry-run        # 试运行（不写入数据库）

流程:
    1. 列出数据源 → 2. 拉取 Markdown 文件 → 3. 解析提取 Q&A → 4. 自动分类 → 5. 去重 → 6. 导入
"""

import argparse
import sys
import os
import time

# 项目根目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import DatabaseManager
from src.spider.github_source import GitHubSource, REMOTE_SOURCES
from src.spider.local_data import SOURCES_LOCAL
from src.spider.parser import QuestionParser
from src.spider.classifier import Classifier
from src.spider.dedup import Deduplicator
from src.spider.importer import Importer
# 合并所有数据源用于列表显示
ALL_SOURCES = (
    [{"repo": s["repo"], "type": "远程", "file": ", ".join(s["files"]),
      "default_cat": s["default_cat"]} for s in REMOTE_SOURCES] +
    [{"repo": s["repo"], "type": "本地", "file": s["file_path"],
      "default_cat": s["default_cat"]} for s in SOURCES_LOCAL]
)


def list_sources():
    """列出所有可用数据源"""
    print("=" * 70)
    print(f"{'#':<4} {'类型':<6} {'仓库/文件':<50} {'分类':<10}")
    print("-" * 70)
    for idx, src in enumerate(ALL_SOURCES):
        label = f"{src['repo']}/{src['file']}"[:48]
        print(f"  {idx:<2} {src['type']:<4} {label:<50} {src['default_cat']:<10}")
    print("=" * 70)
    print(f"共 {len(ALL_SOURCES)} 个数据文件（{len(REMOTE_SOURCES)} 远程 + {len(SOURCES_LOCAL)} 本地）")


def run_update(db, source_indices=None, dry_run=False):
    """执行题库更新"""
    github = GitHubSource()
    parser = QuestionParser()
    classifier = Classifier()
    importer = Importer(db)

    # 获取数据库已有题目（用于去重）
    existing = db.get_questions()
    dedup = Deduplicator(existing)
    print(f"数据库已有题目: {len(existing)} 道")

    # 1. 拉取所有文件
    t0 = time.time()
    all_files = github.fetch_all()
    t1 = time.time()
    print(f"\n  → 共获取 {len(all_files)} 个 Markdown 文件（耗时 {t1-t0:.1f}s）")

    # 如果指定了 --sources，按索引过滤
    if source_indices is not None:
        selected_repos = set()
        for idx in source_indices:
            if 0 <= idx < len(ALL_SOURCES):
                selected_repos.add(ALL_SOURCES[idx]["repo"])
        files = [f for f in all_files if f["source_name"] in selected_repos]
        print(f"  → 过滤后保留 {len(files)} 个文件（对应 {len(selected_repos)} 个数据源）")
    else:
        files = all_files

    if not files:
        print("  没有获取到任何文件。")
        return

    # 2. 按源分组解析 + 分类 + 去重
    by_source = {}
    for f in files:
        key = f["source_name"]
        if key not in by_source:
            by_source[key] = {"files": [], "default_cat": f["default_cat"]}
        by_source[key]["files"].append(f)

    total_new = 0
    total_skipped = 0
    source_results = []

    for repo, src_data in by_source.items():
        print(f"\n{'=' * 60}")
        print(f"  数据源: {repo}")
        print(f"{'=' * 60}")

        # 解析
        all_parsed = []
        for f in src_data["files"]:
            try:
                parsed = parser.parse(f["content"], f["source_name"])
                for q in parsed:
                    q["default_cat"] = f.get("default_cat", src_data["default_cat"])
                all_parsed.extend(parsed)
            except Exception as e:
                print(f"  ⚠ 解析失败 [{f['file_path']}]: {e}")

        if not all_parsed:
            print(f"  → 未提取到结构化题目")
            source_results.append({"repo": repo, "files": len(src_data["files"]),
                                   "parsed": 0, "new": 0})
            continue

        print(f"  → 解析出 {len(all_parsed)} 道候选题目")

        # 自动分类
        all_parsed = classifier.batch_classify(all_parsed)

        # 去重
        new_questions = dedup.filter(all_parsed)
        skipped_count = len(all_parsed) - len(new_questions)
        print(f"  → 去重后新增 {len(new_questions)} 道（跳过 {skipped_count} 道重复）")

        # 导入
        if dry_run:
            print(f"  → [试运行] 将导入 {len(new_questions)} 道（未写入数据库）")
        else:
            result = importer.import_questions(
                new_questions, scenario="job_interview", source_name=repo,
            )
            total_new += result["success"]
            total_skipped += result["skipped"]
            print(f"  → 导入完成: 成功 {result['success']}, 跳过 {result['skipped']}")
            if result["errors"]:
                print(f"  ⚠ 错误: {len(result['errors'])} 个")

        source_results.append({
            "repo": repo,
            "files": len(src_data["files"]),
            "parsed": len(all_parsed),
            "new": len(new_questions),
        })

    # 汇总报告
    print(f"\n{'=' * 60}")
    print(f"  更新完成报告")
    print(f"{'=' * 60}")
    print(f"  {'数据源':<40} {'文件':<6} {'解析':<6} {'新增':<6}")
    print(f"  {'-' * 58}")
    for r in source_results:
        print(f"  {r['repo']:<40} {r['files']:<6} {r['parsed']:<6} {r['new']:<6}")
    print(f"  {'-' * 58}")
    if not dry_run:
        print(f"  总计新增: {total_new} 道题目")
    print(f"  总跳过（重复）: {total_skipped} 道")
    db_total = len(db.get_questions())
    print(f"  当前题库总量: {db_total} 道")
    print(f"{'=' * 60}")


def main():
    # Windows 终端 UTF-8 支持
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description="自动题库扩充 — 从 GitHub 开源题库拉取面试题",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python update_questions.py              全量更新
  python update_questions.py --sources 0 2 只更新索引 0 和 2 的数据源
  python update_questions.py --list        列出数据源
  python update_questions.py --dry-run     试运行
        """,
    )
    parser.add_argument("--sources", nargs="+", type=int, default=None,
                        help="数据源索引（多个用空格分隔，默认全量）")
    parser.add_argument("--list", action="store_true",
                        help="列出所有可用数据源")
    parser.add_argument("--dry-run", action="store_true",
                        help="试运行（只解析不写入数据库）")

    args = parser.parse_args()

    if args.list:
        list_sources()
        return

    print("+=================================================+")
    print("|    自动题库扩充 - 面试成长伴侣                   |")
    print("+=================================================+")
    print()

    db = DatabaseManager()
    run_update(db, source_indices=args.sources, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
