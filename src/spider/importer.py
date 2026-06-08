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

        def _sanitize(val, default=""):
            """清洗字段值：None 字符串和 NoneType -> 默认值"""
            if val is None:
                return default
            if isinstance(val, str) and val.lower() in ("none", "null", "n/a"):
                return default
            return val

        for q in questions:
            try:
                result = self.db.add_question(
                    scenario_id=scenario,
                    category=_sanitize(q.get("category"), "计算机基础"),
                    difficulty=q.get("difficulty", 3) or 3,
                    question_text=_sanitize(q.get("question"), ""),
                    reference_answer=_sanitize(q.get("answer"), ""),
                    tags=q.get("tags", []),
                    company=_sanitize(q.get("company")),
                    position=_sanitize(q.get("position")),
                    source=_sanitize(source_name),
                    year=_sanitize(q.get("year"), "2025"),
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
