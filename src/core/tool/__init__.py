"""
Tool Calling 核心引擎

提供：
- BaseTool: 工具的抽象基类
- LLMToolMixin: 为工具提供 LLM 分析能力的 Mixin
- ToolRegistry: 全局注册中心，支持按场景查询
- ToolExecutor: 统一执行入口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from src.core.tool.types import (
    ToolDefinition, ToolParameter,
    ToolCallRequest, ToolCallResult,
)


# ==================== 抽象基类 ====================

class BaseTool(ABC):
    """所有工具的抽象基类"""

    def __init__(self, definition: ToolDefinition):
        if not definition.id:
            raise ValueError("ToolDefinition.id 不能为空")
        self.definition = definition

    @abstractmethod
    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        """执行工具逻辑"""
        ...

    def validate(self, request: ToolCallRequest) -> Optional[str]:
        """参数校验，返回 None 表示通过，返回字符串表示错误信息"""
        for param in self.definition.parameters:
            if param.required and param.name not in request.arguments:
                return f"缺少必要参数: {param.name}"
            value = request.arguments.get(param.name)
            if value is not None and param.enum and value not in param.enum:
                return f"参数 {param.name} 的值 {value} 不在允许范围内: {param.enum}"
        return None

    @property
    def tool_id(self) -> str:
        return self.definition.id

    def __repr__(self) -> str:
        return f"<Tool {self.definition.id}: {self.definition.name}>"


# ==================== LLM Tool Mixin ====================

class LLMToolMixin:
    """
    为工具提供 LLM 分析能力的 Mixin

    使用方式：
        class MyTool(BaseTool, LLMToolMixin):
            def execute(self, request):
                result = self._llm_analyze(
                    prompt="分析用户的技术描述...",
                    user_input=request.arguments.get("description", ""),
                    system_prompt="你是一个技术分析师...",
                )
                return ToolCallResult(...)
    """

    def _llm_analyze(self, prompt: str, user_input: str,
                      system_prompt: str = "",
                      temperature: float = 0.3,
                      max_tokens: int = 500) -> Optional[Dict[str, Any]]:
        """
        调用 LLM 进行分析

        Args:
            prompt: 分析提示
            user_input: 用户输入
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            解析后的 JSON 字典，失败返回 None
        """
        try:
            from src.services.llm_client import LLMClient, LLM_MODEL
            llm = LLMClient()

            headers = {
                "Authorization": f"Bearer {llm.api_key}",
                "Content-Type": "application/json"
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": f"{prompt}\n\n{user_input}"})

            payload = {
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            import httpx
            with httpx.Client(timeout=httpx.Timeout(llm.timeout)) as client:
                response = client.post(llm.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"].strip()
                    import json, re
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                        return {"raw_analysis": content}
            return None
        except Exception as e:
            print(f"[LLMToolMixin] LLM 分析失败: {e}")
            return None


# ==================== 注册中心 ====================

class ToolRegistry:
    """
    Tool 注册中心

    功能：
    - 注册/注销 Tool
    - 按工具 ID、场景 ID 查询
    - 支持动态加载
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        tool_id = tool.definition.id
        if tool_id in self._tools:
            print(f"[ToolRegistry] Tool '{tool_id}' 已存在，将被覆盖")
        self._tools[tool_id] = tool

    def unregister(self, tool_id: str) -> bool:
        if tool_id in self._tools:
            del self._tools[tool_id]
            return True
        return False

    def get(self, tool_id: str) -> Optional[BaseTool]:
        return self._tools.get(tool_id)

    def get_all(self) -> List[BaseTool]:
        return list(self._tools.values())

    def get_by_skill(self, skill_id: str) -> List[BaseTool]:
        """获取某场景所有关联的工具"""
        return [
            t for t in self._tools.values()
            if skill_id in t.definition.skill_ids and t.definition.enabled
        ]

    def get_by_category(self, category: str) -> List[BaseTool]:
        return [
            t for t in self._tools.values()
            if t.definition.category == category and t.definition.enabled
        ]

    def list_definitions(self, skill_id: Optional[str] = None) -> List[dict]:
        """获取工具定义列表（前端用）"""
        tools = self.get_by_skill(skill_id) if skill_id else self.get_all()
        return [t.definition.to_dict() for t in tools if t.definition.enabled]


# ==================== 统一执行器 ====================

class ToolExecutor:
    """
    工具统一执行入口

    支持同步执行，内置参数校验和错误处理。
    """

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        tool = self._registry.get(request.tool_id)
        if not tool:
            return ToolCallResult(
                tool_id=request.tool_id,
                success=False,
                error=f"Tool '{request.tool_id}' 未注册",
            )

        # 参数校验
        validation_error = tool.validate(request)
        if validation_error:
            return ToolCallResult(
                tool_id=request.tool_id,
                success=False,
                error=validation_error,
            )

        # 执行
        try:
            result = tool.execute(request)
            return result
        except Exception as e:
            return ToolCallResult(
                tool_id=request.tool_id,
                success=False,
                error=str(e),
            )


# ==================== 快捷访问 ====================

registry = ToolRegistry()
executor = ToolExecutor(registry)
