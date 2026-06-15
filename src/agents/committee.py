"""
委员会评审管理器 — 连接现有 API 层和多 Agent 系统的桥接层

职责：
1. 将 SkillSession 转换为 Agent 可理解的输入格式
2. 管理默认评审员配置
3. 启动委员会评审并返回向后兼容的 FeedbackReport
"""

import os
import yaml
from typing import List, Dict, Any, Optional

from src.agents.types import (
    AgentIdentity,
    AgentRole,
    ReviewSynthesis,
)
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.orchestrator import AgentOrchestrator
from src.agents.llm_adapter import LLMAdapter
from src.core.skill.types import FeedbackReport, SkillSession, SkillConfig


# 默认委员会配置：3 位不同立场的评审员
DEFAULT_COMMITTEE = [
    {
        "id": "reviewer_balanced",
        "name": "综合评审员",
        "title": "资深面试评审专家",
        "review_focus": "balanced",
    },
    {
        "id": "reviewer_strict",
        "name": "严苛评审员",
        "title": "高级技术评审专家",
        "review_focus": "strict",
    },
    {
        "id": "reviewer_encouraging",
        "name": "成长型评审员",
        "title": "人才发展评审专家",
        "review_focus": "encouraging",
    },
]


class CommitteeReviewManager:
    """
    委员会评审管理器。

    使用方式：
        adapter = LLMAdapter(llm_client)
        manager = CommitteeReviewManager(adapter)

        # 构建输入
        input_data = manager.build_committee_input(session, skill_config)

        # 启动委员会
        synthesis = manager.run_committee(input_data)

        # 转为向后兼容格式
        report = manager.to_feedback_report(synthesis)
    """

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        committee_config: Optional[List[Dict[str, Any]]] = None,
        synthesis_mode: str = "llm",
    ):
        """
        Args:
            llm_adapter: 共享的 LLM 适配器
            committee_config: 自定义评审员列表（为 None 时使用默认 3 人委员会）
            synthesis_mode: 合成模式 — "llm" 或 "simple_average"
        """
        self.llm = llm_adapter
        self.committee_config = committee_config or DEFAULT_COMMITTEE
        self.synthesis_mode = synthesis_mode
        self._orchestrator: Optional[AgentOrchestrator] = None

    def _ensure_orchestrator(self, persona_base: Dict[str, str]) -> AgentOrchestrator:
        """懒初始化编排器 + 注册评审员"""
        orch = AgentOrchestrator(self.llm, max_workers=len(self.committee_config))

        for cfg in self.committee_config:
            if not cfg.get("enabled", True):
                continue

            identity = AgentIdentity(
                id=cfg["id"],
                name=cfg.get("name", persona_base.get("name", "评审员")),
                title=cfg.get("title", persona_base.get("title", "面试评审专家")),
                role=AgentRole.REVIEWER,
                system_prompt=(
                    f"你是{cfg.get('name', '评审员')}，{cfg.get('title', '面试评审专家')}。\n"
                    f"背景：{persona_base.get('background', '经验丰富的面试评审专家')}\n"
                    f"语气：{persona_base.get('tone', '专业、严谨')}"
                ),
                style_tags=[cfg.get("review_focus", "balanced")],
                scoring_weights=cfg.get("scoring_weights", {}),
            )

            reviewer = ReviewerAgent(
                identity=identity,
                llm=self.llm,
                review_focus=cfg.get("review_focus", "balanced"),
            )
            orch.register_reviewer(reviewer)

        return orch

    def build_committee_input(
        self,
        session: SkillSession,
        skill_config: SkillConfig,
    ) -> Dict[str, Any]:
        """
        将 SkillSession 转换为 Agent 输入格式。

        Args:
            session: 当前 Skill 会话
            skill_config: Skill 配置（含评分维度定义）

        Returns:
            标准化的委员会评审输入字典
        """
        qa_pairs = [
            {
                "round": i + 1,
                "question": a.question,
                "answer": a.answer,
                "score": a.score or 0,
            }
            for i, a in enumerate(session.answers)
        ]

        dimensions = [
            {
                "id": d.id,
                "name": d.name,
                "max_score": d.max_score,
                "weight": d.weight,
                "description": d.description,
            }
            for d in skill_config.scoring.dimensions
        ]

        return {
            "scenario_name": skill_config.name,
            "qa_pairs": qa_pairs,
            "dimensions": dimensions,
            "user_background": session.context.get("user_background", ""),
            "skill_id": skill_config.id,
            "total_rounds": len(session.answers),
        }

    def run_committee(
        self,
        input_data: Dict[str, Any],
    ) -> ReviewSynthesis:
        """
        启动委员会评审。

        Args:
            input_data: build_committee_input() 的输出

        Returns:
            ReviewSynthesis: 综合评审结果
        """
        persona_base = {
            "name": "评审委员会",
            "title": input_data.get("scenario_name", "面试") + "评审专家",
            "background": f"经验丰富的{input_data.get('scenario_name', '面试')}评审专家",
            "tone": "专业、严谨",
        }

        orch = self._ensure_orchestrator(persona_base)
        return orch.run_committee_review(input_data)

    def to_feedback_report(self, synthesis: ReviewSynthesis) -> FeedbackReport:
        """
        将 ReviewSynthesis 转为现有的 FeedbackReport 类型。

        这是向后兼容的关键桥接 — 后续的 BadgeStage / ProgressStage / NotificationStage
        只认 FeedbackReport，无需感知多 Agent。
        """
        return FeedbackReport(
            overall_score=synthesis.overall_score,
            strengths=synthesis.strengths,
            improvements=synthesis.improvements,
            dimension_scores=synthesis.dimensions,
            overall_comment=synthesis.overall_comment,
            passed=synthesis.passed,
            new_badges=[],
        )

    @classmethod
    def from_yaml(
        cls,
        llm_adapter: LLMAdapter,
        config_path: str,
    ) -> "CommitteeReviewManager":
        """
        从 YAML 配置文件创建 CommitteeReviewManager。

        配置文件格式见 config/agents/committee.yaml
        """
        if not os.path.isfile(config_path):
            print(f"[CommitteeReviewManager] 配置文件不存在: {config_path}，使用默认配置")
            return cls(llm_adapter)

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        committee_cfg = config.get("committee", {})
        reviewers = committee_cfg.get("reviewers", DEFAULT_COMMITTEE)
        synthesis_mode = committee_cfg.get("synthesis_mode", "llm")

        return cls(
            llm_adapter=llm_adapter,
            committee_config=reviewers,
            synthesis_mode=synthesis_mode,
        )
