"""
存储模块 - 将采集数据保存为 JSON 格式

同时提供导入到主项目 SQLite 数据库的功能。
"""

import json
import os
from typing import List, Dict, Optional

from .schema import CollectedQuestion
from .config import OUTPUT_DIR


# ================================================================
# JSON 存储
# ================================================================

def save_questions(questions: List[CollectedQuestion], filepath: str):
    """
    将题目列表保存为 JSON 文件

    Args:
        questions: 题目列表
        filepath: 输出文件路径
    """
    data = [q.to_dict() for q in questions]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存: {filepath} ({len(questions)} 题)")


def load_questions(filepath: str) -> List[dict]:
    """从 JSON 文件加载题目"""
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_by_scenario(
    questions: List[CollectedQuestion],
    base_path: str = "",
) -> Dict[str, str]:
    """
    按场景分别保存为独立文件

    Args:
        questions: 题目列表
        base_path: 基础路径（不含文件名）

    Returns:
        {scenario: filepath, ...}
    """
    if not base_path:
        base_path = os.path.join(OUTPUT_DIR, "by_scenario")
    os.makedirs(base_path, exist_ok=True)

    # 按场景分组
    grouped: Dict[str, list] = {}
    for q in questions:
        sc = q.scenario
        if sc not in grouped:
            grouped[sc] = []
        grouped[sc].append(q)

    result = {}
    for scenario, qs in grouped.items():
        filename = f"{scenario}.json"
        filepath = os.path.join(base_path, filename)
        save_questions(qs, filepath)
        result[scenario] = filepath

    return result


def generate_report(questions: List[CollectedQuestion]) -> dict:
    """
    生成采集统计报告

    Returns:
        报告字典
    """
    scenarios = {}
    grades = {}
    total = len(questions)
    with_answers = sum(
        1 for q in questions if q.answer_basic or q.answer_good or q.answer_excellent
    )

    for q in questions:
        scenarios[q.scenario] = scenarios.get(q.scenario, 0) + 1
        grades[q.grade] = grades.get(q.grade, 0) + 1

    return {
        "total": total,
        "with_answers": with_answers,
        "scenarios": dict(sorted(scenarios.items(), key=lambda x: -x[1])),
        "grades": dict(sorted(grades.items())),
    }


def print_report(questions: List[CollectedQuestion]):
    """打印采集报告到控制台"""
    report = generate_report(questions)
    print(f"\n{'='*60}")
    print(f"采集报告")
    print(f"{'='*60}")
    print(f"总计: {report['total']} 题")
    print(f"已生成答案: {report['with_answers']} 题")
    print(f"\n场景分布:")
    for sc, count in report["scenarios"].items():
        print(f"  {sc}: {count} 题")
    print(f"\n评级分布:")
    for grade, count in report["grades"].items():
        pct = count / report["total"] * 100 if report["total"] else 0
        print(f"  {grade}: {count} 题 ({pct:.1f}%)")
    print(f"{'='*60}")


# ================================================================
# 导入到主项目 SQLite
# ================================================================

def import_to_database(
    questions: List[CollectedQuestion],
    db_path: str = "",
) -> int:
    """
    将采集的题目导入到主项目的 SQLite 数据库

    Args:
        questions: 题目列表（需要已通过 S/A 评级和去重）
        db_path: 数据库路径

    Returns:
        导入的题目数
    """
    if not db_path:
        from .config import EXISTING_DB
        db_path = EXISTING_DB

    import sqlite3
    import uuid
    from datetime import datetime

    sc_map = {
        "job_interview": "求职面试",
        "graduate_school": "考研复试",
        "teacher_cert": "教资面试",
        "civil_service": "公务员面试",
        "mba_interview": "MBA面试",
        "ielts_speaking": "雅思口语",
    }

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    imported = 0
    skipped = 0

    for q in questions:
        # 查重（使用 question_text 前30字符）
        prefix = q.question[:30].strip()
        cur.execute(
            "SELECT id FROM questions WHERE substr(question_text,1,30) = ?",
            (prefix,),
        )
        if cur.fetchone():
            skipped += 1
            continue

        # 获取 scenario_id
        cur.execute("SELECT id FROM scenarios WHERE id = ?", (q.scenario,))
        scenario_row = cur.fetchone()
        if not scenario_row:
            skipped += 1
            continue

        # 优先级：用采集的答案作为 reference_answer
        # 有高分用高分，有良好用良好，有基础用基础
        answer = q.answer_excellent or q.answer_good or q.answer_basic or ""

        question_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # 构建 tags
        tags = json.dumps([q.category, q.grade] + q.tags, ensure_ascii=False)

        cur.execute(
            """INSERT INTO questions
            (id, scenario_id, category, difficulty, question_text, reference_answer,
             tags, created_at, updated_at, company, position, source, year, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                question_id,
                q.scenario,
                q.category,
                q.difficulty,
                q.question,
                answer,
                tags,
                now,
                now,
                q.school_or_company,
                "",        # position 留空（采集时通常没有）
                f"{q.source} | {q.source_url}" if q.source_url else q.source,
                str(q.year),
                "real_interview",
            ),
        )
        imported += 1

    conn.commit()
    conn.close()

    print(f"\n导入完成: 新增 {imported} 题, 跳过 {skipped} 题 (已存在)")
    return imported
