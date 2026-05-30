"""
自动化工作流引擎

提供：
- PipelineEngine: 可配置的流水线执行引擎
- 预置阶段：评分 → 反馈生成 → 徽章检测 → 进度更新 → 通知
- 支持同步/异步执行、错误重试、可配置阶段
"""

import time
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.workflow.types import (
    StageConfig, PipelineConfig, StageResult,
    WorkflowContext, PipelineResult,
)
from src.core.workflow.stages import (
    Stage, ScoringStage, FeedbackStage,
    BadgeStage, ProgressStage, NotificationStage,
)


# ==================== 默认流水线配置 ====================

DEFAULT_PIPELINE = PipelineConfig(
    stages=[
        StageConfig(name="scoring", retry_count=3, retry_delay=0.5),
        StageConfig(name="feedback", retry_count=2, depends_on=["scoring"]),
        StageConfig(name="badge", retry_count=3, depends_on=["feedback"]),
        StageConfig(name="progress", retry_count=3, depends_on=["feedback"]),
        StageConfig(name="notification", retry_count=1, depends_on=["badge"]),
    ],
    fail_fast=False,
    async_mode=False,
)


# ==================== 阶段工厂 ====================

STAGE_FACTORY = {
    "scoring": ScoringStage,
    "feedback": FeedbackStage,
    "badge": BadgeStage,
    "progress": ProgressStage,
    "notification": NotificationStage,
}


# ==================== 流水线引擎 ====================

class PipelineEngine:
    """
    流水线执行引擎

    使用方式：
        engine = PipelineEngine()
        result = engine.run(ctx)
        # 或异步执行
        future = engine.run_async(ctx)
    """

    def __init__(self, config: PipelineConfig = None):
        self.config = config or DEFAULT_PIPELINE
        self._stages: Dict[str, Stage] = {}
        self._init_stages()

    def _init_stages(self) -> None:
        """初始化所有阶段"""
        for stage_config in self.config.stages:
            factory = STAGE_FACTORY.get(stage_config.name)
            if factory:
                self._stages[stage_config.name] = factory(stage_config)

    def run(self, ctx: WorkflowContext) -> PipelineResult:
        """
        同步执行流水线

        Args:
            ctx: 工作流上下文

        Returns:
            PipelineResult: 包含各阶段结果
        """
        ctx.started_at = datetime.now()
        results: List[StageResult] = []
        completed = set()

        for stage_config in self.config.get_enabled_stages():
            stage = self._stages.get(stage_config.name)
            if not stage:
                continue

            # 检查依赖是否全部完成
            deps = stage_config.depends_on
            if deps and not all(d in completed for d in deps):
                # 依赖阶段未执行或失败，跳过
                results.append(StageResult(
                    stage_name=stage_config.name,
                    success=False,
                    error=f"依赖阶段未完成: {deps}",
                ))
                if self.config.fail_fast:
                    break
                continue

            # 执行阶段
            result = stage.execute(ctx)
            results.append(result)

            if result.success:
                completed.add(stage_config.name)
            else:
                ctx.errors.append(f"[{stage_config.name}] {result.error}")
                if self.config.fail_fast:
                    break

        ctx.completed_at = datetime.now()
        total_duration = sum(r.duration for r in results)
        overall_success = all(r.success for r in results if r.stage_name in completed)

        return PipelineResult(
            success=overall_success,
            context=ctx,
            stage_results=results,
            total_duration=total_duration,
        )

    def run_async(self, ctx: WorkflowContext) -> threading.Thread:
        """
        异步执行流水线

        返回一个 threading.Thread，调用方可以 join() 等待完成
        """
        thread = threading.Thread(target=self.run, args=(ctx,), daemon=True)
        thread.start()
        return thread

    def add_stage(self, stage: Stage) -> None:
        """注册自定义阶段"""
        self._stages[stage.name] = stage

    def get_config(self) -> PipelineConfig:
        return self.config

    def update_config(self, config: PipelineConfig) -> None:
        """更新流水线配置"""
        self.config = config
        self._init_stages()


# ==================== 快捷函数 ====================

def create_interview_pipeline(
    user_id: str, scenario_id: str, conversation_id: str,
    skill_id: str, session=None, async_mode: bool = False,
) -> PipelineResult:
    """
    创建并运行面试完成后的工作流

    执行链：评分 → 反馈 → 徽章 → 进度 → 通知
    """
    engine = PipelineEngine(PipelineConfig(
        stages=DEFAULT_PIPELINE.stages,
        fail_fast=DEFAULT_PIPELINE.fail_fast,
        async_mode=async_mode,
    ))

    ctx = WorkflowContext(
        user_id=user_id,
        scenario_id=scenario_id,
        conversation_id=conversation_id,
        skill_id=skill_id,
        session=session,
    )

    if async_mode:
        engine.run_async(ctx)
        # 返回一个标记"已异步启动"的结果
        return PipelineResult(
            success=True,
            context=ctx,
            stage_results=[],
            total_duration=0,
        )
    else:
        return engine.run(ctx)


# 全局默认引擎
default_engine = PipelineEngine()
