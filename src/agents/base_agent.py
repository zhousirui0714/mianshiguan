"""Agent 抽象基类 — 所有 Agent 的统一接口"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any

from src.agents.types import AgentIdentity, AgentOutput
from src.agents.llm_adapter import LLMAdapter


class BaseAgent(ABC):
    """
    所有 Agent 的抽象基类。

    每个 Agent 持有：
    - identity: 人设/身份定义
    - llm: 共享的 LLM 适配器（不独占 API 连接）
    """

    def __init__(self, identity: AgentIdentity, llm: LLMAdapter):
        if not identity.id:
            raise ValueError("AgentIdentity.id 不能为空")
        self.identity = identity
        self.llm = llm

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        """执行 Agent 任务，子类必须实现"""
        ...

    def _make_output(
        self,
        success: bool,
        data: Dict[str, Any] = None,
        raw_response: str = "",
        error: str = None,
        duration: float = 0.0,
    ) -> AgentOutput:
        """快捷构造 AgentOutput"""
        return AgentOutput(
            agent_id=self.identity.id,
            role=self.identity.role,
            success=success,
            data=data or {},
            raw_response=raw_response,
            error=error,
            duration=duration,
        )

    @property
    def agent_id(self) -> str:
        return self.identity.id

    @property
    def role(self):
        return self.identity.role

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.identity.id}: {self.identity.name}>"
