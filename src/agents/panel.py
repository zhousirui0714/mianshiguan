"""
面板面试编排器 — 多考官实时面试

职责：
1. 管理面板考官阵容（3 位不同风格的考官）
2. 决定每轮谁发言、谁插话
3. 面试结束后主持协商评分

使用方式：
    panel = PanelOrchestrator(llm_adapter, scenario_id)
    panel_info = panel.start_panel()

    # 每轮对话
    result = panel.decide_speakers(user_message, history, user_background)

    # 结束时
    score_result = panel.negotiate_score(history, dimensions)
"""

import json
import re
from typing import List, Dict, Any, Optional

from src.agents.llm_adapter import LLMAdapter
from src.services.llm_client import EXAMINER_PROFILES


# 面板考官模板 — 基于场景考官 + 差异化角色
PANEL_EXAMINERS = [
    {
        "id": "panel_lead",
        "name": "主考官",
        "role": "lead",
        "focus": "主导面试流程，全面评估候选人",
        "interjection_frequency": 0,  # 必定发言，无需插话
    },
    {
        "id": "panel_strict",
        "name": "严苛考官",
        "role": "strict",
        "focus": "挑剔技术细节，追问模糊回答，不给面子",
        "interjection_frequency": 0.4,  # 40% 概率想插话
    },
    {
        "id": "panel_encouraging",
        "name": "成长型考官",
        "role": "encouraging",
        "focus": "关注潜力和学习能力，挖掘候选人亮点",
        "interjection_frequency": 0.3,
    },
]


class PanelOrchestrator:
    """面板面试编排引擎"""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        scenario_id: str = "job_interview",
        examiners: Optional[List[Dict[str, Any]]] = None,
    ):
        self.llm = llm_adapter
        self.scenario_id = scenario_id
        self.scenario_profile = EXAMINER_PROFILES.get(scenario_id, EXAMINER_PROFILES["job_interview"])
        self.examiners = examiners or PANEL_EXAMINERS
        self._interjection_counter = 0  # 用于控制插话节奏

    # ==================== 启动面板 ====================

    def start_panel(self) -> Dict[str, Any]:
        """返回面板面试的初始化信息"""
        lead = self.examiners[0]
        return {
            "mode": "panel",
            "panel_members": [
                {
                    "id": e["id"],
                    "name": e["name"],
                    "role": e["role"],
                    "focus": e["focus"],
                }
                for e in self.examiners
            ],
            "lead_examiner": {
                "id": lead["id"],
                "name": lead["name"],
                "title": self.scenario_profile["title"],
            },
            "examiner_name": lead["name"],
            "examiner_title": self.scenario_profile["title"],
        }

    # ==================== 决定谁发言 ====================

    def decide_speakers(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        user_background: str = "",
        interview_style: str = "",
    ) -> Dict[str, Any]:
        """
        决定本轮谁发言。

        逻辑：
        1. 主考官始终发言（通过现有的 examiner_chat 生成回复）
        2. 每 2-3 轮检查其他考官是否想插话
        3. 插话考官不会每次都出现，给用户喘息空间

        Returns:
            {
                "response": "主考官回复内容",
                "examiner_name": "主考官",
                "interjections": [
                    {"name": "严苛考官", "content": "追问内容"},
                ]  # 可能为空
            }
        """
        lead = self.examiners[0]

        # 1. 主考官始终回复
        lead_profile = self.scenario_profile
        system_prompt = self._build_examiner_prompt(
            base_profile=lead_profile,
            panel_role="lead",
            user_background=user_background,
            interview_style=interview_style,
            conversation_history=conversation_history,
        )

        lead_response = self._call_examiner(
            system_prompt=system_prompt,
            user_message=user_message,
            history=conversation_history,
        )

        # 2. 检查是否需要插话
        interjections = []
        self._interjection_counter += 1

        # 每 2 轮检查一次，避免太频繁
        if self._interjection_counter >= 2 and len(conversation_history) >= 4:
            self._interjection_counter = 0
            interjections = self._check_interjections(
                user_message=user_message,
                lead_response=lead_response,
                conversation_history=conversation_history,
                user_background=user_background,
            )

        return {
            "response": lead_response,
            "examiner_name": lead["name"],
            "interjections": interjections,
            "panel_members": [
                {"id": e["id"], "name": e["name"], "role": e["role"]}
                for e in self.examiners
            ],
        }

    def _build_examiner_prompt(
        self,
        base_profile: Dict[str, str],
        panel_role: str,
        user_background: str,
        interview_style: str,
        conversation_history: List[Dict[str, str]],
    ) -> str:
        """构建考官 system prompt"""
        from src.services.llm_client import LLMClient

        # 使用现有模板但不走 examiner_chat 的完整路径
        style_hint = ""
        if interview_style and hasattr(LLMClient, 'INTERVIEW_STYLES'):
            styles = getattr(LLMClient, 'INTERVIEW_STYLES', {})
            if interview_style in styles:
                style_hint = f"\n【面试风格：{styles[interview_style]['name']}】\n{styles[interview_style]['prompt']}\n"

        bg_hint = f"\n【用户背景信息】\n{user_background}\n" if user_background else ""

        return f"""你是{base_profile['title']}，名叫{base_profile['name']}。
背景：{base_profile['background']}
语气要求：{base_profile['tone']}
{style_hint}
【你的角色】
你正在进行一场真实的一对一面试。你是面试委员会的主考官，负责控制面试节奏。

【追问原则 - 最重要】
- 你必须根据用户刚才回答的**具体内容**来追问深挖
- 如果用户回答中提到了某个技术细节、项目经验、具体数据，请追问那个点
- 如果用户回答模糊笼统，请要求他给出具体例子
- 不要机械地跳到下一个话题，要像一个真正的面试官那样顺着对话自然深入

【防幻觉规则 - 最高优先级】
- **绝对禁止编造用户的简历内容、项目经历、技能或任何经历**
- 你只能引用用户在对话中**实际说过**的信息
- 不确定用户是否有某项经验时，用询问语气提问

【面试规则】
- 每次回复只包含：1-2句简要评价 + 一个面试问题
- 问题要有深度，能考察真实能力
- 不要一次问多个问题{bg_hint}
请像一个真实的面试官那样自然地提问。"""

    def _call_examiner(
        self,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]],
    ) -> str:
        """调用 LLM 生成考官回复"""
        try:
            # 构建简洁的 user prompt
            history_text = ""
            if history:
                recent = history[-6:]  # 只取最近 6 条，控制 token
                history_text = "\n".join([
                    f"{'面试者' if m['role'] == 'user' else '你'}: {m['content'][:300]}"
                    for m in recent
                ])

            user_prompt = f"对话历史：\n{history_text}\n\n面试者刚才说：{user_message}\n\n请回复。"
            raw = self.llm.call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.5,
                max_tokens=800,
            )
            return raw.strip()
        except Exception as e:
            print(f"[Panel] 考官回复生成失败: {e}")
            return f"请继续，接下来我想了解一下你的相关经验。"

    def _check_interjections(
        self,
        user_message: str,
        lead_response: str,
        conversation_history: List[Dict[str, str]],
        user_background: str,
    ) -> List[Dict[str, str]]:
        """
        检查其他考官是否想插话。

        策略：逐个询问非主考官，用简短 LLM 调用判断
        如果回答质量不高（模糊/回避/错误），严苛考官更可能插话
        """
        # 只检查 1 位非主考官（轮流来，避免开销大）
        non_leads = [e for e in self.examiners if e["role"] != "lead"]
        if not non_leads:
            return []

        # 轮换选择插话考官
        idx = (self._interjection_counter // 2) % len(non_leads)
        examiner = non_leads[min(idx, len(non_leads) - 1)]

        try:
            should_interject = self._should_interject(
                examiner=examiner,
                user_message=user_message,
                lead_response=lead_response,
                conversation_history=conversation_history,
            )
        except Exception:
            return []

        if not should_interject:
            return []

        # 生成插话内容
        try:
            content = self._generate_interjection(
                examiner=examiner,
                user_message=user_message,
                lead_response=lead_response,
                conversation_history=conversation_history,
            )
            if content and len(content) > 5:
                return [{"name": examiner["name"], "content": content}]
        except Exception as e:
            print(f"[Panel] 插话生成失败: {e}")

        return []

    def _should_interject(
        self,
        examiner: Dict[str, Any],
        user_message: str,
        lead_response: str,
        conversation_history: List[Dict[str, str]],
    ) -> bool:
        """判断某位考官是否应该插话"""
        prompt = f"""你是面试委员会中的「{examiner['name']}」，你的风格是：{examiner['focus']}。

面试者刚回答了一个问题。
主考官的回复是："{lead_response[:200]}"
面试者的回答是："{user_message[:300]}"

请判断：你是否需要插话追问面试者？
- 如果面试者的回答有技术漏洞、模糊表述、或值得深挖的点，返回 YES
- 如果回答已经足够充分，返回 NO

只回复 YES 或 NO。"""

        raw = self.llm.call(
            system_prompt="你是一位面试官。只回复 YES 或 NO。",
            user_prompt=prompt,
            temperature=0.1,
            max_tokens=5,
        )
        return "YES" in raw.upper()

    def _generate_interjection(
        self,
        examiner: Dict[str, Any],
        user_message: str,
        lead_response: str,
        conversation_history: List[Dict[str, str]],
    ) -> str:
        """生成插话内容"""
        prompt = f"""你是面试委员会中的「{examiner['name']}」，你的风格是：{examiner['focus']}。

面试者刚回答了："{user_message[:400]}"
主考官回复了："{lead_response[:200]}"

请你插话追问面试者一个简短的问题（1-2 句话）。
- 不要重复主考官已经问过的
- 聚焦你的评审视角（{examiner['focus']}）
- 问题要具体、有深度

直接说你的问题，不要加任何前缀或后缀。"""

        raw = self.llm.call(
            system_prompt=f"你是一位面试官，名叫{examiner['name']}。你的风格是{examiner['focus']}。只输出你的追问，不加前缀。",
            user_prompt=prompt,
            temperature=0.5,
            max_tokens=200,
        )
        return raw.strip()

    # ==================== 协商评分 ====================

    def negotiate_score(
        self,
        conversation_history: List[Dict[str, str]],
        user_background: str = "",
        dimensions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        面试结束后，3 位考官协商评分。

        流程：
        1. 每位考官独立打分
        2. 主席（主考官）主持协商，汇总各方意见
        3. 输出最终分数 + 协商摘要 + 各考官独立分
        """
        scenario = self.scenario_profile["name"]

        # 构建对话摘要
        conv_summary = self._build_conversation_summary(conversation_history)

        dims_desc = ""
        if dimensions:
            dims_desc = "\n".join([
                f"- {d.get('name', d.get('id', '?'))}（满分{d.get('max_score', 100)}，权重{d.get('weight', 0)}%）"
                for d in dimensions
            ])

        # 构建协商 prompt
        system_prompt = f"""你是一个面试评审委员会，由以下 3 位考官组成：

1. {self.examiners[0]['name']}（主考官）— {self.examiners[0]['focus']}
2. {self.examiners[1]['name']}（严苛型）— {self.examiners[1]['focus']}
3. {self.examiners[2]['name']}（成长型）— {self.examiners[2]['focus']}

你们刚刚共同面试了一位{scenario}候选人。现在请你们进行评分协商。

评分维度：
{dims_desc if dims_desc else '通用面试评分标准（技术能力、沟通表达、逻辑思维、综合素质）'}

请模拟 3 位考官进行简短的协商讨论（2-3 轮对话），然后输出最终结果 JSON。

协商过程格式：
[{self.examiners[0]['name']}]：发表你的评分意见（1-2句）
[{self.examiners[1]['name']}]：发表你的评分意见（1-2句）
[{self.examiners[2]['name']}]：发表你的评分意见（1-2句）
[{self.examiners[0]['name']}]：综合大家意见，提出最终分数

最终结果 JSON（严格遵守格式）：
FINAL_RESULT: {{"overall_score": <0-100>, "strengths": ["优势1", "优势2", "优势3"], "improvements": ["建议1", "建议2", "建议3"], "individual_scores": [{{"name": "{self.examiners[0]['name']}", "score": <分数>}}, {{"name": "{self.examiners[1]['name']}", "score": <分数>}}, {{"name": "{self.examiners[2]['name']}", "score": <分数>}}], "agreement_level": "<high/medium/low>", "negotiation_summary": "<50-100字的协商摘要>"}}"""

        user_prompt = f"面试对话记录：\n{conv_summary}\n\n请开始评分协商。"

        try:
            raw = self.llm.call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2000,
            )

            # 提取最终结果 JSON
            result = self._parse_negotiation_result(raw)
            result["raw_negotiation"] = raw
            return result
        except Exception as e:
            print(f"[Panel] 协商评分失败: {e}")
            return {
                "overall_score": 75,
                "strengths": ["完成了面试"],
                "improvements": ["建议重试获取详细评分"],
                "individual_scores": [
                    {"name": e["name"], "score": 75} for e in self.examiners
                ],
                "agreement_level": "unknown",
                "negotiation_summary": f"协商过程出现技术问题，使用默认评分。",
                "fallback": True,
            }

    def _build_conversation_summary(self, history: List[Dict[str, str]]) -> str:
        """构建对话摘要（截断过长内容）"""
        if not history:
            return "（无对话记录）"

        lines = []
        for i, m in enumerate(history[-20:]):  # 最多 20 条
            role = "面试官" if m["role"] == "assistant" else "面试者"
            content = m["content"][:300]
            lines.append(f"[{role}] {content}")

        return "\n".join(lines)

    def _parse_negotiation_result(self, raw: str) -> Dict[str, Any]:
        """从协商文本中提取 FINAL_RESULT JSON"""
        import re

        # 尝试找 FINAL_RESULT 标记
        match = re.search(r'FINAL_RESULT:\s*(\{.*\})', raw, re.DOTALL)
        if match:
            return json.loads(match.group(1))

        # 尝试找最后一个 JSON 对象
        matches = list(re.finditer(r'\{[^{}]*\}', raw))
        if matches:
            try:
                return json.loads(matches[-1].group())
            except json.JSONDecodeError:
                pass

        # 找嵌套 JSON
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError("无法解析协商结果")

    def build_welcome_message(
        self,
        user_background: str = "",
        position: str = "",
        company: str = "",
    ) -> str:
        """生成面板面试的欢迎消息"""
        members_desc = "、".join([e["name"] for e in self.examiners])

        lines = [
            f"欢迎参加本次委员会面试！我是{self.examiners[0]['name']}，担任本次面试的主考官。",
            f"",
            f"今天的面试委员会由 3 位考官组成：",
        ]
        for e in self.examiners:
            lines.append(f"  · {e['name']} — {e['focus']}")
        lines.append("")
        lines.append(f"面试过程中主要由我来提问，其他考官也会不时追问。请放松，展示真实的自己。")
        if position:
            lines.append(f"")
            lines.append(f"我看到你正在准备{position}岗位{'（' + company + '）' if company else ''}的面试。")

        lines.append(f"")
        lines.append(f"那么，我们先从自我介绍开始吧——请简要介绍一下你自己。")

        return "\n".join(lines)
