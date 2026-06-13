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

_DEBUG_LOG = r"D:\zhousirui\新建文件夹 (2)\mianshiguan\debug_audit.log"
def _debug(msg: str):
    import sys
    with open(_DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()
    print(msg, flush=True)


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
        """生成欢迎语 + 第一个问题（融入用户背景）"""
        user_bg = session.context.get("user_background", "")
        return self._render_greeting(
            name=self.config.persona.name,
            title=self.config.persona.title,
            scenario=self.config.name,
            max_rounds=str(self.config.max_rounds),
            user_background=user_bg,
        )

    def _render_greeting(self, name: str, title: str, scenario: str,
                         max_rounds: str, user_background: str = "") -> str:
        """直接渲染欢迎语（融入用户背景）"""
        greeting = f"你好！我是{name}，{title}。\n\n欢迎参加{scenario}模拟面试。\n\n"

        if user_background:
            for line in user_background.split("\n"):
                line = line.strip()
                if line.startswith("目标岗位："):
                    greeting += f"我注意到你在准备{line.replace('目标岗位：', '')}的面试。\n"
                elif line.startswith("目标公司："):
                    greeting += f"目标公司是{line.replace('目标公司：', '')}，我会针对性地提问。\n"

        greeting += f"\n本次面试共有约{max_rounds}轮，准备好了吗？\n\n首先，请做一个简短的自我介绍，包括你的专业背景和求职方向。"
        return greeting

    # ==================== 问题生成 ====================

    def generate_question(self, session: SkillSession,
                          history: List[Dict[str, str]]) -> str:
        """生成下一轮问题：优先深挖 → 程序化选题 → LLM 自由生成

        所有路径最终都通过 LLM，确保：
        - 评价用户回答 + 根据上下文自然引入问题
        - 不会机械地套模板
        """
        next_question = None

        # 1. 检查是否在深挖模式中
        deep_dive = session.context.get("deep_dive", {})
        if deep_dive.get("active") and not deep_dive.get("exited"):
            if DeepDiveManager.should_continue(session.context):
                question = DeepDiveManager.select_question(session.context)
                if question:
                    next_question = question["question_text"]
            if not next_question:
                # 深挖结束（题目用完或达上限）
                session.context["deep_dive"]["active"] = False

        # 2. 确定当前面试阶段
        if next_question is None:
            next_stage = self._determine_next_stage(session)
            session.context["current_stage"] = next_stage

            # 3. 追踪每阶段轮次
            stage_rounds = session.context.setdefault("stage_rounds", {})
            stage_rounds[next_stage] = stage_rounds.get(next_stage, 0) + 1

            # 4. 程序化选题：从题库中选一个未使用的题目（按阶段过滤）
            next_question = self._select_next_bank_question(session)

        # 5. 通过 LLM 生成回复（即使有预设题目，也让 LLM 负责上下文衔接）
        if next_question:
            return self._llm_wrap_bank_question(session, history, next_question)
        else:
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
        cid = session.id[:8]
        # 深挖模式：由 DeepDiveManager 选题
        deep_dive = session.context.get("deep_dive", {})
        if deep_dive.get("active") and not deep_dive.get("exited"):
            if DeepDiveManager.should_continue(session.context):
                question = DeepDiveManager.select_question(session.context)
                if question:
                    _debug(f"[DEBUG][{cid}] _select_next_bank_question -> 深挖选题: "
                          f"topic={deep_dive.get('topic')} text={question['question_text'][:60]}")
                    return question["question_text"]
            session.context["deep_dive"]["active"] = False

        retrieved = session.context.get("retrieved_questions", [])
        if not retrieved:
            _debug(f"[DEBUG][{cid}] _select_next_bank_question -> 无题库，返回 None")
            return None

        current_stage = session.context.get("current_stage", "basic")
        used = set(session.context.get("used_questions", []))

        _debug(f"[DEBUG][{cid}] _select_next_bank_question: stage={current_stage} "
              f"retrieved={len(retrieved)} used={len(used)}")

        # 1. 优先选择匹配当前阶段的未使用题目
        stage_matched = 0
        for q in retrieved:
            text = q.get("question_text", "")
            stage = (q.get("interview_stage") or "basic").strip()
            if stage == current_stage and text and text not in used:
                _debug(f"[DEBUG][{cid}] _select_next_bank_question -> 阶段匹配命中: "
                      f"stage={stage} text={text[:60]}")
                return text
            if stage == current_stage:
                stage_matched += 1

        _debug(f"[DEBUG][{cid}] _select_next_bank_question -> 阶段匹配失败: "
              f"stage={current_stage} 共{stage_matched}题, 均不可用或已用")

        # 2. 无匹配当前阶段的题目 → 按岗位相关性评分选最优题目
        intro_keywords = ["自我介绍", "introduce yourself", "介绍一下你自己", "一分钟时间介绍"]
        # 软技能类问题（应排到后期轮次）
        soft_skill_keywords = ["意见不合", "同事", "团队合作", "团队协作", "处理冲突",
                               "leader 否定", "职业规划", "优缺点", "优点和缺点",
                               "为什么选择", "还有什么想问"]
        # 从用户背景提取技术关键词
        tech_keywords = self._extract_tech_keywords(session)

        candidates = []
        for q in retrieved:
            text = q.get("question_text", "")
            if not text or text in used:
                continue
            # 非 intro 阶段跳过自我介绍类题目
            if current_stage != "intro" and any(kw in text for kw in intro_keywords):
                continue

            score = 0
            # 技术关键词匹配加分
            for kw in tech_keywords:
                if kw.lower() in text.lower():
                    score += 15
            # 软技能题目在非 behavior 阶段扣分
            if current_stage not in ("behavior", "intro") and any(kw in text for kw in soft_skill_keywords):
                score -= 30
            # 题目难度等级加分（S>A>B>C）
            lev = (q.get("question_level") or "C").strip().upper()
            level_bonus = {"S": 10, "A": 6, "B": 3, "C": 0}.get(lev, 0)
            score += level_bonus

            candidates.append((score, q))

        # 按得分降序排列，选最高分
        candidates.sort(key=lambda x: -x[0])
        if candidates:
            best_score, best_q = candidates[0]
            text = best_q.get("question_text", "")
            _debug(f"[DEBUG][{cid}] _select_next_bank_question -> 评分降级命中: "
                  f"score={best_score} stage={current_stage} text={text[:60]}")
            return text

        _debug(f"[DEBUG][{cid}] _select_next_bank_question -> 全部已用，返回 None")
        return None

    def _llm_wrap_bank_question(self, session: SkillSession,
                                history: List[Dict[str, str]],
                                bank_question: str) -> str:
        """将题库问题交给 LLM 进行上下文包装

        LLM 负责：评价用户回答 + 根据对话上下文自然引入下一个问题。
        不会机械套模板，而是根据用户实际回答调整追问方向和措辞。
        """
        cid = session.id[:8]
        current_stage = session.context.get("current_stage", "")

        try:
            response = self.llm.examiner_chat(
                scenario_id=self.config.id,
                user_message=session.answers[-1].answer if session.answers else "",
                conversation_history=history,
                user_background=session.context.get("user_background", ""),
                next_question=bank_question,
                current_stage=current_stage,
            )
            return response if response else bank_question
        except Exception as e:
            _debug(f"[{cid}] LLM 包装题库问题失败，回退到原始题面: {e}")
            return bank_question

    def _llm_generate_free(self, session: SkillSession,
                           history: List[Dict[str, str]]) -> str:
        """题库已用完，LLM 自由生成新问题"""
        cid = session.id[:8]
        retrieved = session.context.get("retrieved_questions", [])
        used = session.context.get("used_questions", [])
        current_stage = session.context.get("current_stage", "")
        _debug(f"[DEBUG][{cid}] _llm_generate_free 进入: "
              f"retrieved_questions={len(retrieved)} used_questions={len(used)} "
              f"round={session.round} "
              f"stage={current_stage}")

        # 构建已覆盖话题的简要说明
        covered_text = ""
        if used:
            covered_text = "已讨论过的话题：\n" + "\n".join(f"- {q[:60]}..." for q in used[-3:])

        prompt = f"""请根据对话进展和当前面试阶段，提出下一个有深度的面试问题。

当前阶段：{current_stage}
{covered_text}

要求：
- 问题要有深度，能考察真实能力
- 与用户的背景和目标岗位相关
- 只输出问题本身，不要解释
- 每次只问一个问题"""
        try:
            response = self.llm.examiner_chat(
                scenario_id=self.config.id,
                user_message=prompt,
                conversation_history=history,
                user_background=session.context.get("user_background", ""),
                current_stage=current_stage,
            )
            return response if response else "请继续介绍你的相关经验。"
        except Exception as e:
            _debug(f"[{self.config.id}] LLM 调用失败，使用默认问题: {e}")
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

    def _extract_tech_keywords(self, session: SkillSession) -> list:
        """从用户背景中提取技术关键词，用于题目相关性评分"""
        user_bg = session.context.get("user_background", "")
        position = session.context.get("position", "")

        # 岗位关键词映射
        POSITION_KW_MAP = {
            "后端": ["Java", "Spring", "MySQL", "Redis", "微服务", "数据库", "系统设计",
                    "分布式", "高并发", "性能优化", "缓存", "消息队列"],
            "java": ["Java", "Spring", "MySQL", "Redis", "微服务", "数据库", "JVM",
                    "分布式", "高并发", "性能优化"],
            "python": ["Python", "Redis", "MySQL", "数据库", "缓存", "系统设计", "Django", "Flask"],
            "前端": ["JavaScript", "浏览器", "CSS", "Vue", "React", "TypeScript", "HTML",
                    "性能优化", "渲染", "DOM", "前端"],
            "产品经理": ["需求分析", "用户研究", "产品设计", "用户体验", "数据驱动",
                      "竞品分析", "项目管理"],
            "算法": ["算法", "数据结构", "排序", "搜索", "动态规划", "复杂度"],
            "测试": ["测试", "自动化", "测试用例", "接口测试", "性能测试", "质量"],
            "数据分析": ["数据", "SQL", "数仓", "ETL", "数据挖掘", "可视化"],
            "golang": ["Go", "Golang", "并发", "goroutine", "channel", "微服务"],
            "go": ["Go", "Golang", "并发", "goroutine", "channel", "微服务"],
        }

        keywords = set()
        pos_lower = position.lower().strip() if position else ""
        user_bg_lower = user_bg.lower() if user_bg else ""

        # 从岗位名称匹配关键词
        for key, kws in POSITION_KW_MAP.items():
            if key in pos_lower or key in user_bg_lower:
                keywords.update(kws)

        # 额外：从用户背景中提取具体提到的技术
        extra_tech = ["Java", "Spring", "MySQL", "Redis", "Kafka", "Docker",
                     "Kubernetes", "Python", "Go", "Vue", "React", "TypeScript",
                     "微服务", "分布式", "高并发", "系统设计", "架构"]
        for tech in extra_tech:
            if tech.lower() in user_bg_lower or tech.lower() in pos_lower:
                keywords.add(tech)

        return list(keywords)

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
