"""
多 Agent 通信骨架

提供可运行的多 Agent 消息传递基础设施：
- Message / MessageType: 消息类型
- BaseAgent: 可通信 Agent 基类（inbox/outbox）
- MessageBus: 消息路由总线
- patterns: 协作模式（圆桌讨论 / 辩论 / 任务交接）

使用方式：
    from src.agents.multi_agent import MessageBus, BaseAgent
    from src.agents.multi_agent.patterns import round_table

    bus = MessageBus()
    agents = [MyAgent("a1", "Alice"), MyAgent("a2", "Bob")]
    round_table(agents, bus, topic="讨论话题", rounds=2)

运行演示：
    python -m src.agents.multi_agent.demo
"""

from src.agents.multi_agent.message import Message, MessageType, AgentState
from src.agents.multi_agent.agent import BaseAgent
from src.agents.multi_agent.bus import MessageBus
from src.agents.multi_agent.patterns import round_table, debate, handoff

__all__ = [
    "Message", "MessageType", "AgentState",
    "BaseAgent", "MessageBus",
    "round_table", "debate", "handoff",
]
