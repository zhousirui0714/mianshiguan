"""
题库导入器 — 将解析后的题目写入 SQLite
"""

from typing import List, Dict


class Importer:
    """导入解析后的题目到数据库"""

    def __init__(self, db):
        self.db = db

    def import_questions(self, questions: List[Dict], scenario: str = "job_interview",
                         source_name: str = "") -> dict:
        """
        批量导入题目。

        返回: {success, skipped, errors}
        """
        count_success = 0
        count_skipped = 0
        errors = []

        for q in questions:
            try:
                result = self.db.add_question(
                    scenario_id=scenario,
                    category=q.get("category", "计算机基础"),
                    difficulty=q.get("difficulty", 3),
                    question_text=q.get("question", ""),
                    reference_answer=q.get("answer", ""),
                    tags=q.get("tags", []),
                    company=q.get("company", ""),
                    position=q.get("position", ""),
                    source=source_name,
                    year=q.get("year", "2025"),
                )
                if result["success"]:
                    count_success += 1
                else:
                    count_skipped += 1
            except Exception as e:
                errors.append(str(e))
                count_skipped += 1

        return {
            "success": count_success,
            "skipped": count_skipped,
            "errors": errors,
            "total": len(questions),
        }
