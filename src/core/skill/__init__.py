"""
Skill 核心引擎

提供：
- SkillRegistry: 全局注册中心，支持动态注册/卸载/按分类查询
- SkillExecutor: 统一执行入口，解耦调用方与具体 Skill 实现
"""

import os
import yaml
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from src.core.skill.types import (
    SkillConfig,
    SkillSession,
    AnswerRecord,
    EvaluationResult,
    FeedbackReport,
)


# ==================== 抽象基类 ====================

class BaseSkill(ABC):
    """所有 Skill 的抽象基类"""

    def __init__(self, config: SkillConfig):
        if not config.id:
            raise ValueError("SkillConfig.id 不能为空")
        self.config = config

    @abstractmethod
    def create_session(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> SkillSession:
        """创建新的面试会话"""
        ...

    @abstractmethod
    def get_welcome_message(self, session: SkillSession) -> str:
        """生成欢迎语 + 第一个问题"""
        ...

    @abstractmethod
    def generate_question(self, session: SkillSession, history: List[Dict[str, str]]) -> str:
        """根据对话历史生成下一轮问题"""
        ...

    @abstractmethod
    def evaluate_answer(self, session: SkillSession, answer: AnswerRecord) -> EvaluationResult:
        """对单轮答案评分"""
        ...

    @abstractmethod
    def generate_feedback(self, session: SkillSession) -> FeedbackReport:
        """生成最终反馈报告"""
        ...

    @abstractmethod
    def get_system_prompt(self, session: SkillSession) -> str:
        """构建带人设的 system prompt"""
        ...

    def __repr__(self) -> str:
        return f"<Skill {self.config.id}: {self.config.name}>"


# ==================== 注册中心 ====================

class SkillRegistry:
    """
    Skill 注册中心

    功能：
    - 注册/注销 Skill（运行时动态）
    - 按 ID、分类查询
    - 从 YAML 配置文件目录批量加载
    - 事件通知（供热切换使用）
    """

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._listeners: set = set()

    def register(self, skill: BaseSkill) -> None:
        """注册一个 Skill 实例"""
        skill_id = skill.config.id
        if skill_id in self._skills:
            print(f"[SkillRegistry] Skill '{skill_id}' 已存在，将被覆盖")
        self._skills[skill_id] = skill
        self._emit("SKILL_REGISTERED", skill_id)

    def unregister(self, skill_id: str) -> bool:
        """注销一个 Skill"""
        if skill_id in self._skills:
            del self._skills[skill_id]
            self._emit("SKILL_UNREGISTERED", skill_id)
            return True
        return False

    def get(self, skill_id: str) -> Optional[BaseSkill]:
        """根据 ID 获取 Skill"""
        return self._skills.get(skill_id)

    def get_all(self) -> List[BaseSkill]:
        """获取所有注册的 Skill"""
        return list(self._skills.values())

    def get_by_category(self, category: str) -> List[BaseSkill]:
        """按分类获取"""
        return [s for s in self._skills.values() if s.config.category == category]

    def get_enabled(self) -> List[BaseSkill]:
        """获取所有启用的 Skill"""
        return [s for s in self._skills.values() if s.config.enabled]

    def load_from_config(self, config_dir: str, skill_factory=None) -> int:
        """
        从 YAML 配置目录批量加载并注册 Skill

        Args:
            config_dir: YAML 文件目录路径
            skill_factory: 可选，接收 SkillConfig 返回 BaseInstance 的工厂函数
                           为 None 时只加载配置不创建实例

        Returns:
            成功注册的 Skill 数量
        """
        if not os.path.isdir(config_dir):
            print(f"[SkillRegistry] 配置目录不存在: {config_dir}")
            return 0

        count = 0
        for filename in sorted(os.listdir(config_dir)):
            if not filename.endswith((".yaml", ".yml")):
                continue

            filepath = os.path.join(config_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not data or not data.get("id"):
                    print(f"[SkillRegistry] 跳过无效配置文件: {filename}")
                    continue

                config = SkillConfig.from_dict(data)

                if skill_factory:
                    skill = skill_factory(config)
                    self.register(skill)
                    count += 1
                else:
                    print(f"[SkillRegistry] 已加载配置: {config.id} ({config.name})，等待注册")

            except Exception as e:
                print(f"[SkillRegistry] 加载 {filename} 失败: {e}")

        return count

    def on_change(self, listener) -> callable:
        """监听注册/注销事件，返回取消监听的函数"""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def _emit(self, event_type: str, skill_id: str) -> None:
        for listener in self._listeners:
            try:
                listener({"type": event_type, "skill_id": skill_id})
            except Exception:
                pass


# ==================== 统一执行器 ====================

class SkillExecutor:
    """
    Skill 统一执行入口

    对外暴露统一接口，内部从 Registry 获取具体 Skill。
    调用方无需关心 Skill 的实现细节。
    """

    def __init__(self, registry: SkillRegistry):
        self._registry = registry

    def start_interview(self, skill_id: str, user_id: str,
                        context: Optional[Dict[str, Any]] = None) -> dict:
        """开始一场面试：创建会话 + 返回欢迎语"""
        skill = self._get_skill(skill_id)
        session = skill.create_session(user_id, context)
        welcome = skill.get_welcome_message(session)

        return {
            "session": session,
            "welcome_message": welcome,
        }

    def chat(self, skill_id: str, session: SkillSession,
             user_message: str, history: List[Dict[str, str]]) -> dict:
        """处理一轮对话：评分 + 生成下一问"""
        skill = self._get_skill(skill_id)

        # 评分上一轮
        evaluation = None
        if history and session.answers:
            last_answer = session.answers[-1]
            evaluation = skill.evaluate_answer(session, last_answer)
            last_answer.score = evaluation.total_score
            last_answer.feedback = evaluation.comment
            session.answers[-1] = last_answer

        # 生成下一轮问题
        session.round += 1
        next_question = skill.generate_question(session, history)

        # 构建回复
        response = next_question
        if evaluation and evaluation.comment:
            response = f"{evaluation.comment}\n\n{next_question}"

        return {
            "response": response,
            "round": session.round,
            "evaluation": evaluation,
            "is_finished": session.round >= skill.config.max_rounds,
        }

    def chat_with_tools(self, skill_id: str, session: SkillSession,
                         user_message: str, history: List[Dict[str, str]],
                         tools: List[Any] = None) -> dict:
        """
        处理一轮对话（LLM + Tool 集成版）

        流程：评分 → LLM 生成回复（可附带工具调用）→ 执行工具 → 返回结果

        Args:
            skill_id: Skill ID
            session: 当前会话
            user_message: 用户消息
            history: 对话历史
            tools: 可用工具列表

        Returns:
            {"response": "LLM回复", "round": n, "tool_results": [...], "is_finished": bool}
        """
        skill = self._get_skill(skill_id)

        # 评分上一轮
        evaluation = None
        if history and session.answers:
            last_answer = session.answers[-1]
            evaluation = skill.evaluate_answer(session, last_answer)
            last_answer.score = evaluation.total_score
            last_answer.feedback = evaluation.comment
            session.answers[-1] = last_answer

        session.round += 1

        # 使用 LLM + Tool 集成聊天
        tool_results = []
        if tools:
            # 构建工具定义给 LLM
            tool_defs = []
            for t in tools:
                if hasattr(t, 'definition'):
                    d = t.definition
                    params_data = [
                        {"name": p.name, "description": p.description,
                         "type": p.type, "required": p.required, "enum": p.enum}
                        for p in d.parameters
                    ]
                    tool_defs.append({
                        "id": d.id,
                        "name": d.name,
                        "description": d.description,
                        "parameters": params_data,
                    })

            try:
                llm_result = skill.llm.chat_with_tools(
                    scenario_id=skill_id,
                    user_message=user_message,
                    conversation_history=history,
                    tools=tool_defs,
                    user_background=session.context.get("user_background", ""),
                )

                response_text = llm_result.get("response", "")
                tool_calls = llm_result.get("tool_calls")

                # 执行 LLM 请求的工具调用
                if tool_calls:
                    for tc in tool_calls:
                        if isinstance(tc, dict) and "tool_id" in tc:
                            try:
                                from src.core.tool import executor as tool_exec
                                from src.core.tool.types import ToolCallRequest
                                req = ToolCallRequest(
                                    tool_id=tc["tool_id"],
                                    arguments=tc.get("arguments", {}),
                                    context={"skill_id": skill_id, "session_id": session.id},
                                )
                                tool_result = tool_exec.execute(req)
                                tool_results.append({
                                    "tool_id": tc["tool_id"],
                                    "success": tool_result.success,
                                    "data": tool_result.data,
                                })
                            except Exception as te:
                                tool_results.append({
                                    "tool_id": tc["tool_id"],
                                    "success": False,
                                    "error": str(te),
                                })

                # 如果有工具结果，追加到回复中
                if tool_results:
                    response_text += "\n\n[工具分析结果]\n"
                    for tr in tool_results:
                        if tr.get("success") and tr.get("data"):
                            summary = tr["data"].get("summary") or tr["data"].get("suggestion") or ""
                            response_text += f"- {tr.get('tool_id', '')}: {summary}\n"

                response = response_text
                if evaluation and evaluation.comment:
                    response = f"{evaluation.comment}\n\n{response_text}"

                return {
                    "response": response,
                    "round": session.round,
                    "evaluation": evaluation,
                    "tool_results": tool_results,
                    "is_finished": session.round >= skill.config.max_rounds,
                }

            except Exception as llm_err:
                print(f"[SkillExecutor] chat_with_tools 失败，降级到普通 chat: {llm_err}")

        # 降级：普通 chat（无工具集成）
        return self.chat(skill_id, session, user_message, history)

    def finish_interview(self, skill_id: str, session: SkillSession) -> FeedbackReport:
        """结束面试，生成反馈报告"""
        skill = self._get_skill(skill_id)
        return skill.generate_feedback(session)

    def _get_skill(self, skill_id: str) -> BaseSkill:
        skill = self._registry.get(skill_id)
        if not skill:
            raise ValueError(f"Skill '{skill_id}' 未注册")
        return skill


# ==================== 快捷访问 ====================

# 全局单例
registry = SkillRegistry()
executor = SkillExecutor(registry)
