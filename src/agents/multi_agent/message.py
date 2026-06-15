"""多 Agent 通信骨架 — 消息类型定义"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class MessageType(Enum):
    """消息类型"""
    SPEAK = "speak"       # 发言（一对多）
    ASK = "ask"           # 提问（一对一，期待回复）
    REPLY = "reply"       # 回复（一对一）
    HANDOFF = "handoff"   # 任务交接
    VOTE = "vote"         # 投票
    SYSTEM = "system"     # 系统消息


@dataclass
class Message:
    """Agent 之间的消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_agent: str = ""      # 发送者 ID
    to_agent: str = ""        # 接收者 ID（空表示广播）
    type: MessageType = MessageType.SPEAK
    content: str = ""         # 消息正文
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __repr__(self) -> str:
        return f"<Msg {self.id[:6]} [{self.type.value}] {self.from_agent}→{self.to_agent or '*'}>"


@dataclass
class AgentState:
    """Agent 运行时状态"""
    agent_id: str
    is_active: bool = True
    messages_sent: int = 0
    messages_received: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
