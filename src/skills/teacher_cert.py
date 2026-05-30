"""教资面试 Skill"""

import random
from typing import Dict, Any, Optional

from src.skills.base import LLMBasedSkill
from src.core.skill.types import SkillSession, AnswerRecord, EvaluationResult


class TeacherCertSkill(LLMBasedSkill):
    """教资面试 Skill — 支持结构化问答、试讲、答辩三环节"""

    def get_welcome_message(self, session: SkillSession) -> str:
        # 先调用父类模板
        msg = super().get_welcome_message(session)
        # 追加一个结构化的第一题
        questions = [
            "你为什么想当老师？",
            "你认为一名优秀的教师应该具备哪些素质？",
            "谈谈你对'有教无类'的理解。",
        ]
        return msg + "\n\n" + random.choice(questions)

    def evaluate_answer(self, session: SkillSession, answer: AnswerRecord) -> EvaluationResult:
        # 教资评分可以加入一些教育领域的特定逻辑
        result = super().evaluate_answer(session, answer)
        # 试讲环节可以增加额外的评分点
        return result
