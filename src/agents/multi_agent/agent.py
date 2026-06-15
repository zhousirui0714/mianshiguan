"""Agent 基类 — 带 inbox/outbox 的可通信 Agent"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.agents.multi_agent.message import Message, MessageType, AgentState


class BaseAgent(ABC):
    """
    可通信的 Agent 基类。

    每个 Agent 有：
    - inbox: 收到的消息队列
    - 通过 bus.send() 发消息
    - process(msg) 处理收到的消息

    子类只需实现 process() 方法。
    """

    def __init__(self, agent_id: str, name: str = "", role: str = ""):
        self.agent_id = agent_id
        self.name = name or agent_id
        self.role = role
        self.inbox: List[Message] = []
        self.state = AgentState(agent_id=agent_id)
        self._bus = None  # 由 Orchestrator 注入

    # ---- 子类必须实现 ----

    @abstractmethod
    def process(self, message: Message) -> Optional[Message]:
        """
        处理收到的消息，返回要回复的消息（或 None 表示不回复）。

        Args:
            message: 收到的消息

        Returns:
            要发送的回复消息，或 None
        """
        ...

    # ---- 发送消息（通过 Bus） ----

    def send(self, to_agent: str, content: str,
             msg_type: MessageType = MessageType.SPEAK,
             metadata: Dict[str, Any] = None) -> Message:
        """发送消息给指定 Agent"""
        msg = Message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            type=msg_type,
            content=content,
            metadata=metadata or {},
        )
        self.state.messages_sent += 1
        if self._bus:
            self._bus.route(msg)
        return msg

    def broadcast(self, content: str,
                  msg_type: MessageType = MessageType.SPEAK) -> Message:
        """广播消息给所有 Agent"""
        return self.send(to_agent="", content=content, msg_type=msg_type)

    def ask(self, to_agent: str, question: str) -> Message:
        """向某个 Agent 提问"""
        return self.send(to_agent=to_agent, content=question, msg_type=MessageType.ASK)

    def reply(self, to_agent: str, answer: str) -> Message:
        """回复某个 Agent"""
        return self.send(to_agent=to_agent, content=answer, msg_type=MessageType.REPLY)

    # ---- 接收消息 ----

    def receive(self, message: Message) -> None:
        """从 Bus 接收消息（由 Bus 调用）"""
        self.inbox.append(message)
        self.state.messages_received += 1

    def has_mail(self) -> bool:
        """是否有未读消息"""
        return len(self.inbox) > 0

    def read_all(self) -> List[Message]:
        """取出所有未读消息并清空 inbox"""
        msgs = self.inbox[:]
        self.inbox.clear()
        return msgs

    # ---- 生命周期 ----

    def on_start(self) -> Optional[Message]:
        """Agent 启动时的初始化消息（可选）"""
        return None

    def on_stop(self) -> None:
        """Agent 停止时的清理"""
        self.state.is_active = False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.agent_id}: {self.name}>"
