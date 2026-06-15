"""消息总线 — Agent 之间的消息路由中心

全局单例，所有 Agent 通过 Bus 收发消息。
Bus 不关心消息内容，只负责路由和日志。
"""

from typing import Dict, List, Optional, Callable
from src.agents.multi_agent.message import Message


class MessageBus:
    """
    消息总线 — Agent 通信的唯一通道。

    特性：
    - 点对点路由（to_agent 指定）
    - 广播路由（to_agent 为空）
    - 消息日志（可开关）
    - 拦截器（hook，用于调试/监控）
    """

    def __init__(self, verbose: bool = True):
        self._agents: Dict[str, any] = {}  # agent_id → BaseAgent
        self._log: List[Message] = []
        self._interceptors: List[Callable] = []
        self.verbose = verbose

    def register(self, agent) -> None:
        """注册 Agent 到总线"""
        self._agents[agent.agent_id] = agent
        agent._bus = self
        if self.verbose:
            print(f"[Bus] 注册: {agent}")

    def unregister(self, agent_id: str) -> None:
        """移除 Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            if self.verbose:
                print(f"[Bus] 注销: {agent_id}")

    def route(self, message: Message) -> None:
        """路由一条消息"""
        self._log.append(message)

        # 运行拦截器
        for hook in self._interceptors:
            try:
                hook(message)
            except Exception:
                pass

        if self.verbose:
            direction = f"→{message.to_agent}" if message.to_agent else "→*"
            print(f"[Bus] {message.from_agent} {direction} [{message.type.value}] "
                  f"{message.content[:60]}{'...' if len(message.content) > 60 else ''}")

        # 广播
        if not message.to_agent:
            for aid, agent in self._agents.items():
                if aid != message.from_agent:
                    agent.receive(message)
        # 点对点
        elif message.to_agent in self._agents:
            self._agents[message.to_agent].receive(message)

    def broadcast(self, sender_id: str, content: str, msg_type=None) -> Message:
        """便捷广播"""
        from src.agents.multi_agent.message import MessageType
        msg = Message(
            from_agent=sender_id,
            to_agent="",
            type=msg_type or MessageType.SPEAK,
            content=content,
        )
        self.route(msg)
        return msg

    def add_interceptor(self, fn: Callable) -> None:
        """添加消息拦截器（用于日志/监控/调试）"""
        self._interceptors.append(fn)

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    @property
    def agent_ids(self) -> List[str]:
        return list(self._agents.keys())

    @property
    def message_count(self) -> int:
        return len(self._log)

    def summary(self) -> str:
        """总线状态摘要"""
        return (f"MessageBus: {self.agent_count} agents, "
                f"{self.message_count} messages routed")
