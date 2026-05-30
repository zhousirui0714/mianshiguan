"""流水线阶段实现"""

import time
import traceback
from typing import Optional

from src.core.workflow.types import (
    StageConfig, StageResult, WorkflowContext,
)


# ==================== 阶段基类 ====================

class Stage:
    """流水线阶段基类"""

    def __init__(self, config: StageConfig):
        self.config = config

    def execute(self, ctx: WorkflowContext) -> StageResult:
        """执行阶段（含重试逻辑）"""
        start = time.time()
        last_error = None

        for attempt in range(self.config.retry_count + 1):
            try:
                if attempt > 0:
                    time.sleep(self.config.retry_delay)
                result = self.run(ctx)
                duration = time.time() - start
                return StageResult(
                    stage_name=self.config.name,
                    success=True,
                    data=result,
                    duration=duration,
                    retry_count=attempt,
                )
            except Exception as e:
                last_error = e
                if attempt < self.config.retry_count:
                    continue

        duration = time.time() - start
        return StageResult(
            stage_name=self.config.name,
            success=False,
            error=f"{last_error}\n{traceback.format_exc()}",
            duration=duration,
            retry_count=self.config.retry_count,
        )

    def run(self, ctx: WorkflowContext) -> Optional[dict]:
        """阶段实际逻辑（子类实现）"""
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.config.name


# ==================== 具体阶段实现 ====================

class ScoringStage(Stage):
    """评分阶段：评估所有未评分的答案"""

    def run(self, ctx: WorkflowContext) -> Optional[dict]:
        if not ctx.session:
            return {"scored": 0, "message": "无会话数据"}

        skill = _get_skill(ctx.skill_id)
        if not skill:
            raise ValueError(f"Skill '{ctx.skill_id}' 未注册")

        scored_count = 0
        for i, answer in enumerate(ctx.session.answers):
            if answer.score is None:
                result = skill.evaluate_answer(ctx.session, answer)
                answer.score = result.total_score
                answer.feedback = result.comment
                ctx.session.answers[i] = answer
                scored_count += 1

        return {
            "scored": scored_count,
            "total_answers": len(ctx.session.answers),
        }


class FeedbackStage(Stage):
    """反馈生成阶段：生成结构化反馈报告"""

    def run(self, ctx: WorkflowContext) -> Optional[dict]:
        skill = _get_skill(ctx.skill_id)
        if not skill:
            raise ValueError(f"Skill '{ctx.skill_id}' 未注册")

        ctx.report = skill.generate_feedback(ctx.session)

        return {
            "overall_score": ctx.report.overall_score,
            "strengths_count": len(ctx.report.strengths),
            "improvements_count": len(ctx.report.improvements),
            "passed": ctx.report.passed,
        }


class BadgeStage(Stage):
    """徽章检测阶段：检查并解锁徽章"""

    def run(self, ctx: WorkflowContext) -> Optional[dict]:
        from src.core.database import DatabaseManager
        db = DatabaseManager()

        score = ctx.report.overall_score if ctx.report else 0
        unclocked = db.check_and_unlock_badges(ctx.user_id, ctx.scenario_id, score)
        ctx.new_badges = [b["name"] for b in unclocked]

        return {
            "new_badges": ctx.new_badges,
            "count": len(unclocked),
        }


class ProgressStage(Stage):
    """进度更新阶段：更新用户成长档案"""

    def run(self, ctx: WorkflowContext) -> Optional[dict]:
        from src.core.database import DatabaseManager
        db = DatabaseManager()

        score = ctx.report.overall_score if ctx.report else 0
        db.update_progress(ctx.user_id, ctx.scenario_id, score)
        ctx.progress_updated = True

        # 同时保存每条答题记录到 answers 表
        if ctx.session and ctx.session.answers:
            saved = 0
            # 从报告提取维度分
            dim_scores_from_report = {}
            if ctx.report and ctx.report.dimension_scores:
                for d in ctx.report.dimension_scores:
                    if isinstance(d, dict):
                        dim_scores_from_report[d.get('name', '')] = d.get('score', 0)
            for i, answer in enumerate(ctx.session.answers):
                db.add_answer(
                    user_id=ctx.user_id,
                    conversation_id=ctx.conversation_id,
                    question_id=None,
                    round_num=i + 1,
                    question_text=answer.question or '',
                    answer_text=answer.answer or '',
                    score=answer.score or score,
                    dimension_scores=dim_scores_from_report or None,
                    feedback=answer.feedback or '',
                )
                saved += 1

        return {
            "score": score,
            "updated": True,
        }


class NotificationStage(Stage):
    """通知阶段：准备新徽章通知"""

    def run(self, ctx: WorkflowContext) -> Optional[dict]:
        if ctx.new_badges:
            return {
                "notifications": [
                    {"type": "badge_unlocked", "badge_name": b}
                    for b in ctx.new_badges
                ],
                "count": len(ctx.new_badges),
            }
        return {"notifications": [], "count": 0}


# ==================== 辅助函数 ====================

_skill_cache = {}

def _get_skill(skill_id: str):
    """获取 Skill 实例（带缓存）"""
    if skill_id not in _skill_cache:
        from src.core.skill import registry
        _skill_cache[skill_id] = registry.get(skill_id)
    return _skill_cache.get(skill_id)
