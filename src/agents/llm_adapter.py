"""
LLM 适配器 — 所有 Agent 共享的 LLM 调用接口

包装现有 LLMClient，提供：
- 通用 call() 方法（自定义 system prompt）
- 向后兼容的 legacy 方法（保留现有 examiner_chat 等调用路径）
- 共享 API key 和连接池
"""

import json
import httpx
from typing import List, Dict, Any, Optional

from src.services.llm_client import LLMClient, LLM_MODEL, LLM_API_URL, LLM_API_KEY


class LLMAdapter:
    """
    薄封装层，让 Agent 不直接依赖 LLMClient 的具体方法签名。
    所有 Agent 共享同一个 LLMAdapter 实例，共享 API 配置。
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self._client = llm_client or LLMClient()
        self.api_url = self._client.api_url
        self.api_key = self._client.api_key
        self.timeout = self._client.timeout

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.4,
        max_tokens: int = 2000,
    ) -> str:
        """
        通用 LLM 调用 — Agent 自定义 system prompt 和 user prompt。

        Args:
            system_prompt: Agent 专属 system prompt
            user_prompt: 用户/任务描述
            history: 可选对话历史
            temperature: 温度参数
            max_tokens: 最大输出 token 数

        Returns:
            原始响应文本（调用方负责解析 JSON）

        Raises:
            httpx.TimeoutException: 请求超时
            httpx.HTTPStatusError: API 错误
            Exception: 其他错误
        """
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        with httpx.Client(timeout=httpx.Timeout(self.timeout)) as client:
            response = client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()

        return ""

    # ==================== 向后兼容的 Legacy 方法 ====================

    def legacy_examiner_chat(
        self,
        scenario_id: str,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        **kwargs,
    ) -> str:
        """委托给现有 LLMClient.examiner_chat，保持完全兼容"""
        return self._client.examiner_chat(
            scenario_id=scenario_id,
            user_message=user_message,
            conversation_history=conversation_history,
            **kwargs,
        )

    def legacy_generate_evaluation_report(
        self,
        scenario_id: str,
        conversation_history: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """委托给现有 LLMClient.generate_evaluation_report"""
        return self._client.generate_evaluation_report(
            scenario_id=scenario_id,
            conversation_history=conversation_history,
        )

    def legacy_generate_skill_feedback(
        self,
        scenario_id: str,
        skill_name: str,
        qa_pairs: List[Dict[str, str]],
        dimensions: List[Dict[str, Any]],
        persona_name: str = "",
        persona_title: str = "",
    ) -> Dict[str, Any]:
        """委托给现有 LLMClient.generate_skill_feedback"""
        return self._client.generate_skill_feedback(
            scenario_id=scenario_id,
            skill_name=skill_name,
            qa_pairs=qa_pairs,
            dimensions=dimensions,
            persona_name=persona_name,
            persona_title=persona_title,
        )

    def legacy_score_answer(
        self,
        scenario_id: str,
        question: str,
        answer: str,
        dimensions: List[Dict[str, Any]],
        persona_name: str = "",
        persona_title: str = "",
    ) -> Dict[str, Any]:
        """委托给现有 LLMClient.score_answer"""
        return self._client.score_answer(
            scenario_id=scenario_id,
            question=question,
            answer=answer,
            dimensions=dimensions,
            persona_name=persona_name,
            persona_title=persona_title,
        )
