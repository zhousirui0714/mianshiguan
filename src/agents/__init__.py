"""
多 Agent 协作系统

提供：
- AgentOrchestrator: 并行 Agent 编排引擎
- CommitteeReviewManager: 委员会评审桥接层
- LLMAdapter: LLM 调用适配器（所有 Agent 共享）
- 各种 Agent 类型的基类和实现

使用示例：
    from src.agents import CommitteeReviewManager
    from src.agents.llm_adapter import LLMAdapter

    adapter = LLMAdapter(llm_client)
    manager = CommitteeReviewManager(adapter)
    input_data = manager.build_committee_input(session, skill_config)
    synthesis = manager.run_committee(input_data)
    report = manager.to_feedback_report(synthesis)
"""

from src.agents.types import (
    AgentRole,
    InterviewMode,
    AgentIdentity,
    AgentOutput,
    ReviewSynthesis,
)
from src.agents.llm_adapter import LLMAdapter
from src.agents.base_agent import BaseAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.orchestrator import AgentOrchestrator
from src.agents.committee import CommitteeReviewManager

__all__ = [
    # 类型
    "AgentRole",
    "InterviewMode",
    "AgentIdentity",
    "AgentOutput",
    "ReviewSynthesis",
    # 核心类
    "LLMAdapter",
    "BaseAgent",
    "ReviewerAgent",
    "AgentOrchestrator",
    "CommitteeReviewManager",
]
