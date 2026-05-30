"""Tool Calling 模块核心类型定义"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Awaitable


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str = ""
    required: bool = True
    enum: List[str] = field(default_factory=list)
    default: Any = None


@dataclass
class ToolDefinition:
    """工具定义（描述工具的名称、参数等元信息）"""
    id: str
    name: str
    description: str
    category: str = ""  # 工具分类
    parameters: List[ToolParameter] = field(default_factory=list)
    skill_ids: List[str] = field(default_factory=list)  # 关联的场景
    enabled: bool = True

    def to_dict(self) -> dict:
        """转为 JSON 友好的字典（给前端展示用）"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [
                {"name": p.name, "type": p.type, "description": p.description,
                 "required": p.required, "enum": p.enum}
                for p in self.parameters
            ],
            "skill_ids": self.skill_ids,
        }


@dataclass
class ToolCallRequest:
    """工具调用请求"""
    tool_id: str
    arguments: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)  # 调用上下文（如 session、user_id 等）


@dataclass
class ToolCallResult:
    """工具调用结果"""
    tool_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
