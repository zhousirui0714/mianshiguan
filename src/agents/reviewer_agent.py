"""
评审 Agent — 委员会评审中的独立评审员

每个 ReviewerAgent 拥有独立的评审立场（review_focus），
通过不同的 system prompt 实现差异化的评分视角：
- balanced: 均衡评分
- strict: 严苛高标准
- communication: 侧重表达沟通
- technical: 侧重技术深度
- encouraging: 鼓励性评分（找出亮点）
"""

import json
import time
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent
from src.agents.types import AgentIdentity, AgentOutput, AgentRole
from src.agents.llm_adapter import LLMAdapter


# 评审立场定义
REVIEW_FOCUS_INSTRUCTIONS = {
    "balanced": "请从各维度均衡评分，不偏向任何方面。全面考察候选人的综合表现。",
    "strict": (
        "请以极高标准进行评分。只有真正出色的回答才能获得高分。"
        "对任何模糊、笼统、缺乏具体细节的回答严格扣分。"
        "给出低分时不要犹豫，这能帮助候选人认识到差距。"
    ),
    "communication": (
        "请重点从表达清晰度、逻辑结构、沟通能力的角度评分。"
        "对表达流畅、结构清晰、有亮点的回答给予高分。"
        "对逻辑混乱或表达不清的回答如实反映。"
    ),
    "technical": (
        "请重点从技术深度和专业能力的角度进行严苛评分。"
        "关注技术细节的准确性、深度和广度。"
        "对技术上的错误或浅薄认知严格扣分。"
    ),
    "encouraging": (
        "请以鼓励成长为主进行评分，重点发现回答中的亮点和努力。"
        "即使回答不完美，也以建设性的方式指出改进方向，而非严厉批评。"
        "适合帮助初学者建立信心。"
    ),
}


class ReviewerAgent(BaseAgent):
    """
    独立评审 Agent。

    每个 ReviewerAgent 接收相同的面试对话数据，但以不同的 review_focus
    视角进行独立评分。所有 ReviewerAgent 的输出由 Orchestrator 汇总合成。
    """

    def __init__(
        self,
        identity: AgentIdentity,
        llm: LLMAdapter,
        review_focus: str = "balanced",
    ):
        super().__init__(identity, llm)
        self.review_focus = review_focus

    def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        """
        对一场完整面试进行独立评审。

        input_data 期望包含：
            - scenario_name: str — 场景名称，如 "求职面试"
            - qa_pairs: List[Dict] — 问答对 [{round, question, answer, score}, ...]
            - dimensions: List[Dict] — 评分维度 [{id, name, max_score, weight, description}, ...]
            - user_background: str — 用户背景信息
        """
        start = time.time()
        try:
            system_prompt = self._build_system_prompt(input_data)
            user_prompt = self._build_user_prompt(input_data)

            raw = self.llm.call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2000,
            )

            parsed = self._parse_json(raw)
            duration = time.time() - start

            return AgentOutput(
                agent_id=self.identity.id,
                role=AgentRole.REVIEWER,
                success=True,
                data=parsed,
                raw_response=raw,
                duration=duration,
            )
        except Exception as e:
            duration = time.time() - start
            return AgentOutput(
                agent_id=self.identity.id,
                role=AgentRole.REVIEWER,
                success=False,
                data={},
                error=str(e),
                duration=duration,
            )

    def _build_system_prompt(self, ctx: Dict[str, Any]) -> str:
        """构建评审员的 system prompt"""
        scenario = ctx.get("scenario_name", "面试")
        dims = ctx.get("dimensions", [])

        dims_desc = "\n".join([
            f"- {d.get('name', d.get('id', '?'))}"
            f"（满分{d.get('max_score', 100)}，权重{d.get('weight', 0)}%）："
            f"{d.get('description', '')}"
            for d in dims
        ]) if dims else "无预定义维度，请根据通用面试标准评分"

        focus_text = REVIEW_FOCUS_INSTRUCTIONS.get(
            self.review_focus, REVIEW_FOCUS_INSTRUCTIONS["balanced"]
        )

        return f"""你是{self.identity.title}，名叫{self.identity.name}。
{self.identity.system_prompt}

你正在对一场「{scenario}」模拟面试进行独立评审。

【评分维度】
{dims_desc}

【你的评审立场】
{focus_text}

【输出要求】
请严格按照以下 JSON 格式输出评审结果，不要输出任何 JSON 以外的内容：
{{
    "overall_score": <0-100的整数>,
    "dimension_scores": {{"维度名称": 分数, ...}},
    "strengths": ["具体优势1", "具体优势2", "具体优势3"],
    "improvements": ["具体改进建议1", "具体改进建议2", "具体改进建议3"],
    "overall_comment": "<80-150字的总体评价>",
    "confidence": <0.0-1.0，你对本次评分的自信程度>
}}

【评分原则】
- 各维度独立评分，严格按照评分标准
- 评语必须具体，引用面试者的实际回答作为依据
- 分数要有区分度，不要所有维度都给相同分数
- overall_score 应为各维度加权计算的结果"""

    def _build_user_prompt(self, ctx: Dict[str, Any]) -> str:
        """构建评审输入"""
        qa_pairs = ctx.get("qa_pairs", [])
        user_bg = ctx.get("user_background", "")

        qa_text = "\n\n".join([
            f"第{qa.get('round', i+1)}轮\n"
            f"问题：{qa.get('question', '（未记录）')}\n"
            f"回答：{qa.get('answer', '（未记录）')}\n"
            f"机器初评分：{qa.get('score', '未评分')}"
            for i, qa in enumerate(qa_pairs)
        ])

        bg_text = f"用户背景：\n{user_bg}\n\n" if user_bg else ""

        return f"""{bg_text}面试问答记录（共 {len(qa_pairs)} 轮）：

{qa_text}

请根据上述对话进行独立评审，输出 JSON 格式结果。"""

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        """从 LLM 原始响应中提取 JSON"""
        raw = raw.strip()

        # 尝试直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 提取 JSON 代码块
        import re
        # 尝试匹配 ```json ... ```
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
        if m:
            try:
                return json.loads(m.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试匹配最外层的 { ... }
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从 LLM 响应中解析 JSON: {raw[:200]}...")
