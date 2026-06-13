"""
PostgreSQL 种子数据填充

重用 src.core.database.seed 中的数据常量，使用 PostgreSQL 的
INSERT ... ON CONFLICT DO NOTHING 实现幂等插入。
"""

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.database import DatabaseManager


def _seed_scenarios_pg(cur) -> int:
    """幂等插入 6 个场景"""
    from src.core.database.seed import SCENARIO_IDS

    count = 0
    for sid, sname in SCENARIO_IDS.items():
        cur.execute(
            "INSERT INTO scenarios (id, name) VALUES (%s, %s) "
            "ON CONFLICT (id) DO NOTHING",
            (sid, sname),
        )
        count += cur.rowcount  # rowcount = 0 表示跳过
    print(f"[PG Seed] 已填充 {count} 个新场景（跳过 {len(SCENARIO_IDS) - count} 个已存在）")
    return count


def _seed_questions_pg(cur, db) -> int:
    """幂等插入所有题目（硬编码 + JSON 文件）

    调用 DatabaseManager.add_question() 来复用去重逻辑，
    并额外从 JSON 文件导入。
    """
    from src.core.database.seed import (
        QUESTIONS, CATEGORY_TO_STAGE, seed_questions,
    )
    # 直接调用原有的 seed_questions 函数，它内部使用 db.add_question()
    # add_question 已经包含重复检查逻辑
    seed_questions(db)
    return 0  # 计数由 seed_questions 内部打印


def _seed_badges_pg(cur) -> int:
    """幂等插入 8 个徽章"""
    badges = [
        ("badge_001", "初试啼声", "完成第一次模拟练习", "🐣", "newbie",
         {"type": "first_practice"}, "common"),
        ("badge_002", "首战告捷", "首次练习得分80以上", "🎯", "newbie",
         {"type": "first_high_score", "threshold": 80}, "rare"),
        ("badge_003", "认真学习", "完成5道题目", "📚", "newbie",
         {"type": "total_practices", "count": 5}, "common"),
        ("badge_004", "持之以恒", "完成10次练习", "💪", "persistence",
         {"type": "total_practices", "count": 10}, "rare"),
        ("badge_007", "求职达人", "求职面试得分90以上", "🎤", "scenario",
         {"type": "scenario_high_score", "scenario": "job_interview", "threshold": 90}, "epic"),
        ("badge_008", "教资通关", "教资面试完成3次", "🍎", "scenario",
         {"type": "scenario_practices", "scenario": "teacher_cert", "count": 3}, "rare"),
        ("badge_009", "雅思突破", "雅思口语完成5次", "🌍", "scenario",
         {"type": "scenario_practices", "scenario": "ielts_speaking", "count": 5}, "epic"),
        ("badge_012", "全能选手", "所有场景各完成1次", "🎭", "special",
         {"type": "all_scenarios"}, "legendary"),
    ]

    count = 0
    for badge_id, name, desc, icon, category, condition, rarity in badges:
        cur.execute(
            "INSERT INTO badges (id, name, description, icon, category, "
            "unlock_condition, rarity) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING",
            (badge_id, name, desc, icon, category,
             json.dumps(condition, ensure_ascii=False), rarity),
        )
        count += cur.rowcount
    print(f"[PG Seed] 已填充 {count} 个新徽章（跳过 {len(badges) - count} 个已存在）")
    return count


def seed_all_pg(db: "DatabaseManager") -> None:
    """一键填充所有 PostgreSQL 种子数据"""
    conn = db._get_conn()
    try:
        cur = conn.cursor()
        _seed_scenarios_pg(cur)
        conn.commit()
        _seed_questions_pg(cur, db)
        _seed_badges_pg(cur)
        conn.commit()
        print("[PG Seed] PostgreSQL 默认数据填充完成")
    finally:
        db._release_conn(conn)
