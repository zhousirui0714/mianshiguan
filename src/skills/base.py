"""Skill 基础实现 — 复用现有 LLMClient"""

import json
import random
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.core.skill import BaseSkill
from src.core.skill.types import (
    SkillConfig, SkillSession, AnswerRecord,
    EvaluationResult, FeedbackReport,
)
from src.services.llm_client import LLMClient
from src.core.deep_dive import DeepDiveManager


class LLMBasedSkill(BaseSkill):
    """
    基于 LLM 的 Skill 基础实现

    封装了通用的：
    - 会话创建
    - 欢迎语生成（基于模板）
    - LLM 调用（复用 LLMClient）
    - 评分逻辑
    - 反馈报告生成

    子类只需重写：
    - get_system_prompt() 或复写个别方法做定制
    """

    def __init__(self, config: SkillConfig):
        super().__init__(config)
        self.llm = LLMClient()

    # ==================== 会话管理 ====================

    def create_session(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> SkillSession:
        return SkillSession(
            id=str(uuid.uuid4()),
            skill_id=self.config.id,
            user_id=user_id,
            started_at=datetime.now(),
            round=0,
            context=context or {},
        )

    # ==================== 欢迎语 ====================

    def get_welcome_message(self, session: SkillSession) -> str:
        """生成欢迎语 + 第一个问题"""
        return self._render_greeting(
            name=self.config.persona.name,
            title=self.config.persona.title,
            scenario=self.config.name,
            max_rounds=str(self.config.max_rounds),
        )

    def _render_greeting(self, name: str, title: str, scenario: str, max_rounds: str) -> str:
        """直接渲染欢迎语（避免模板引擎问题）"""
        return (f"你好！我是{name}，{title}。\n\n"
                f"欢迎参加{scenario}模拟面试。我们将进行约{max_rounds}轮的面试。\n\n"
                f"首先，请做一个简短的自我介绍。")

    # ==================== 问题生成 ====================

    def generate_question(self, session: SkillSession,
                          history: List[Dict[str, str]]) -> str:
        """生成下一轮问题：优先深挖 → 程序化选题 → LLM 自由生成"""
        # 1. 检查是否在深挖模式中
        deep_dive = session.context.get("deep_dive", {})
        if deep_dive.get("active") and not deep_dive.get("exited"):
            if DeepDiveManager.should_continue(session.context):
                question = DeepDiveManager.select_question(session.context)
                if question:
                    return question["question_text"]
            # 深挖结束（题目用完或达上限）
            session.context["deep_dive"]["active"] = False

        # 2. 确定当前面试阶段
        next_stage = self._determine_next_stage(session)
        session.context["current_stage"] = next_stage

        # 3. 追踪每阶段轮次
        stage_rounds = session.context.setdefault("stage_rounds", {})
        stage_rounds[next_stage] = stage_rounds.get(next_stage, 0) + 1

        # 4. 程序化选题：从题库中选一个未使用的题目（按阶段过滤）
        bank_text = self._select_next_bank_question(session)
        if bank_text:
            return bank_text

        # 5. 题库已用完 → LLM 自由生成
        return self._llm_generate_free(session, history)

    def _determine_next_stage(self, session: SkillSession) -> str:
        """
        确定下一个面试阶段。
        优先级：项目关键词检测 > 轮次映射
        """
        # 关键词检测覆盖：如果用户上一轮回答中包含项目技术关键词，进入 project
        pending_keywords = session.context.pop("pending_project_keywords", [])
        if pending_keywords:
            session.context.setdefault("project_keywords_detected", []).extend(pending_keywords)
            return "project"

        # 默认基于轮次映射
        round_num = session.round + 1  # 1-indexed
        if round_num == 1:
            return "intro"
        elif round_num == 2:
            return "project"
        elif 3 <= round_num <= 5:
            return "basic"
        elif 6 <= round_num <= 7:
            return "advanced"
        elif 8 <= round_num <= 9:
            return "system_design"
        else:
            return "behavior"

    def _select_next_bank_question(self,
                                   session: SkillSession) -> Optional[str]:
        """程序化选择下一个未使用的题库题目（深挖优先 → 阶段匹配）"""
        # 深挖模式：由 DeepDiveManager 选题
        deep_dive = session.context.get("deep_dive", {})
        if deep_dive.get("active") and not deep_dive.get("exited"):
            if DeepDiveManager.should_continue(session.context):
                question = DeepDiveManager.select_question(session.context)
                if question:
                    return question["question_text"]
            session.context["deep_dive"]["active"] = False

        retrieved = session.context.get("retrieved_questions", [])
        if not retrieved:
            return None

        current_stage = session.context.get("current_stage", "basic")
        used = set(session.context.get("used_questions", []))

        # 1. 优先选择匹配当前阶段的未使用题目
        for q in retrieved:
            text = q.get("question_text", "")
            stage = (q.get("interview_stage") or "basic").strip()
            if text and text not in used and stage == current_stage:
                return text

        # 2. 无匹配当前阶段的题目 → 选任意未使用题目（降级兜底）
        for q in retrieved:
            text = q.get("question_text", "")
            if text and text not in used:
                return text

        return None

    def _llm_generate_free(self, session: SkillSession,
                           history: List[Dict[str, str]]) -> str:
        """题库已用完，LLM 自由生成新问题"""
        system_prompt = self.get_system_prompt(session)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({
            "role": "user",
            "content": "请根据对话进展，提出下一个面试问题。只输出问题本身，不要解释。"
        })
        try:
            response = self.llm.examiner_chat(
                scenario_id=self.config.id,
                user_message=messages[-1]["content"],
                conversation_history=history,
                user_background=session.context.get("user_background", ""),
                # 不传 retrieved_questions 和 used_questions，LLM 自由发挥
            )
            return response if response else "请继续介绍你的相关经验。"
        except Exception as e:
            print(f"[{self.config.id}] LLM 调用失败，使用默认问题: {e}")
            return self._get_default_question(session.round)

    # ==================== 评分 ====================

    def evaluate_answer(self, session: SkillSession, answer: AnswerRecord) -> EvaluationResult:
        """对答案评分（优先 LLM，失败时降级为规则评分）"""
        dimensions = self.config.scoring.dimensions
        if not dimensions:
            return EvaluationResult(total_score=0, passed=False, comment="")

        # 尝试 LLM 评分
        try:
            dims_dict = [
                {
                    "id": d.id, "name": d.name,
                    "max_score": d.max_score, "weight": d.weight,
                    "description": d.description,
                }
                for d in dimensions
            ]
            # 从对话历史中找到当前问题
            question = answer.question or "请介绍一下你自己"

            llm_result = self.llm.score_answer(
                scenario_id=self.config.id,
                question=question,
                answer=answer.answer,
                dimensions=dims_dict,
                persona_name=self.config.persona.name,
                persona_title=self.config.persona.title,
            )

            dimension_scores = {
                k: float(v) for k, v in llm_result.get("dimension_scores", {}).items()
            }

            # 如果没有 LLM 返回的维度分，退回到规则评分
            if not dimension_scores:
                raise ValueError("LLM 未返回维度评分")

            # 计算加权总分
            total_weight = sum(d.weight for d in dimensions)
            if total_weight > 0:
                weighted = sum(
                    min((dimension_scores.get(d.id, 0) / d.max_score) * d.weight, d.weight)
                    for d in dimensions
                )
                total_score = weighted
            else:
                total_score = sum(dimension_scores.values()) / len(dimension_scores)

            passed = total_score >= self.config.scoring.passing_score
            llm_comment = llm_result.get("comment", "")
            if not llm_comment:
                llm_comment = f"当前得分 {total_score:.1f} 分。{'请继续下一题。' if passed else '请再接再厉。'}"

            return EvaluationResult(
                dimension_scores=dimension_scores,
                total_score=round(total_score, 1),
                comment=llm_comment,
                passed=passed,
            )

        except Exception as e:
            print(f"[{self.config.id}] LLM 评分失败，使用规则评分降级: {e}")

        # ===== 降级：规则评分（原逻辑） =====
        return self._rule_based_evaluate(answer, dimensions)

    def _rule_based_evaluate(self, answer: AnswerRecord,
                              dimensions: List) -> EvaluationResult:
        """基于规则的降级评分"""
        dimension_scores = {}
        for dim in dimensions:
            base = random.uniform(50, 85)
            length_bonus = min(15, len(answer.answer) / 10)
            score = min(dim.max_score, base + length_bonus)
            dimension_scores[dim.id] = round(score, 1)

        total_weight = sum(d.weight for d in dimensions)
        if total_weight > 0:
            weighted = sum(
                (dimension_scores.get(d.id, 0) / d.max_score) * d.weight
                for d in dimensions
            )
            total_score = weighted
        else:
            total_score = sum(dimension_scores.values()) / len(dimension_scores)

        passed = total_score >= self.config.scoring.passing_score
        comment = (f"当前得分 {total_score:.1f} 分。"
                   f"{'请继续下一题。' if passed else '请再接再厉。'}")

        return EvaluationResult(
            dimension_scores=dimension_scores,
            total_score=round(total_score, 1),
            comment=comment,
            passed=passed,
        )

    # ==================== 反馈报告 ====================

    def generate_feedback(self, session: SkillSession) -> FeedbackReport:
        """生成最终反馈报告（优先 LLM，失败时降级为模板匹配）"""
        if not session.answers:
            return FeedbackReport(
                overall_comment="未完成面试，无法生成报告。",
            )

        # 确保所有答案都已评分
        for i, answer in enumerate(session.answers):
            if answer.score is None:
                result = self.evaluate_answer(session, answer)
                answer.score = result.total_score
                answer.feedback = result.comment
                session.answers[i] = answer

        # ===== 尝试 LLM 生成反馈报告 =====
        try:
            qa_pairs = [
                {
                    "question": a.question,
                    "answer": a.answer,
                    "score": a.score or 0,
                }
                for a in session.answers
            ]
            dims_dict = [
                {
                    "id": d.id, "name": d.name,
                    "max_score": d.max_score, "weight": d.weight,
                    "description": d.description,
                }
                for d in self.config.scoring.dimensions
            ]

            llm_result = self.llm.generate_skill_feedback(
                scenario_id=self.config.id,
                skill_name=self.config.name,
                qa_pairs=qa_pairs,
                dimensions=dims_dict,
                persona_name=self.config.persona.name,
                persona_title=self.config.persona.title,
            )

            overall_score = float(llm_result.get("overall_score", 0))
            strengths = llm_result.get("strengths", [])
            improvements = llm_result.get("improvements", [])
            llm_dimensions = llm_result.get("dimensions", [])
            overall_comment = llm_result.get("overall_comment", "")
            passed = overall_score >= self.config.scoring.passing_score

            # 构建 dimension_scores 格式
            dimension_scores = []
            for d in llm_dimensions:
                dimension_scores.append({
                    "name": d.get("name", ""),
                    "score": float(d.get("score", 0)),
                    "max_score": float(d.get("max_score", 100)),
                    "comment": d.get("comment", ""),
                })

            return FeedbackReport(
                overall_score=round(overall_score, 1),
                strengths=strengths or ["表达清晰，思路有条理"],
                improvements=improvements or ["建议多进行模拟练习"],
                dimension_scores=dimension_scores,
                overall_comment=(overall_comment
                    or f"本次{self.config.name}模拟结束！总分 {overall_score:.1f} 分。"
                       f"{'恭喜通过！' if passed else '继续加油！'}"
                       f"共有 {len(session.answers)} 轮答题记录。"),
                passed=passed,
            )

        except Exception as e:
            print(f"[{self.config.id}] LLM 反馈报告生成失败，使用模板降级: {e}")

        # ===== 降级：模板匹配（原逻辑） =====
        return self._template_based_feedback(session)

    def _template_based_feedback(self, session: SkillSession) -> FeedbackReport:
        """基于模板的降级反馈报告（原 generate_feedback 逻辑）"""
        total_scores = [a.score or 0 for a in session.answers if a.score is not None]
        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0

        dimension_scores = []
        for dim in self.config.scoring.dimensions:
            dimension_scores.append({
                "name": dim.name,
                "score": round(avg_score, 1),
                "max_score": dim.max_score,
                "comment": f"{dim.name}表现{'良好' if avg_score >= 60 else '有待提高'}",
            })

        strengths = self._match_feedback_templates(
            self.config.feedback.strengths_templates, avg_score
        ) or ["表达清晰，思路有条理"]

        improvements = self._match_feedback_templates(
            self.config.feedback.improvements_templates, avg_score
        ) or ["建议多进行模拟练习"]

        passed = avg_score >= self.config.scoring.passing_score

        return FeedbackReport(
            overall_score=round(avg_score, 1),
            strengths=strengths,
            improvements=improvements,
            dimension_scores=dimension_scores,
            overall_comment=f"本次{self.config.name}模拟结束！"
                           f"总分 {avg_score:.1f} 分。"
                           f"{'恭喜通过！' if passed else '继续加油！'}"
                           f"共有 {len(session.answers)} 轮答题记录。",
            passed=passed,
        )

    # ==================== System Prompt ====================

    def get_system_prompt(self, session: SkillSession) -> str:
        """构建带人设的 system prompt"""
        template_str = self.config.persona.system_prompt
        return self._render_template(template_str, {
            "name": self.config.persona.name,
            "title": self.config.persona.title,
            "tone": self.config.persona.tone,
            "background": self.config.persona.background,
            "scenario": self.config.name,
            "max_rounds": str(self.config.max_rounds),
        })

    # ==================== 工具方法 ====================

    def _render_template(self, template_str: str, variables: Dict[str, str]) -> str:
        """渲染 {{变量}} 模板（支持 Jinja2 风格的 {{var}} 语法）"""
        result = template_str
        for key, value in variables.items():
            result = result.replace("{{" + key + "}}", value)
        return result

    def _get_default_question(self, round_num: int) -> str:
        """LLM 不可用时的兜底问题"""
        fallback = [
            "请介绍一下你自己，包括你的专业背景和相关经验。",
            "请描述一个你参与过的最有挑战性的项目。",
            "你的职业规划是什么？",
            "你如何看待自己最大的优势和不足？",
            "你还有什么想问我们的吗？",
        ]
        idx = min(round_num, len(fallback) - 1)
        return fallback[idx]

    def _match_feedback_templates(self, templates: list, score: float) -> List[str]:
        """匹配反馈模板（简单基于分数阈值）"""
        results = []
        for t in templates:
            try:
                # 解析 condition 格式如 "tech >= 80"
                parts = t.condition.split()
                if len(parts) == 3:
                    threshold = float(parts[2])
                    if score >= threshold:
                        results.append(t.template)
            except (ValueError, IndexError):
                pass
        return results
