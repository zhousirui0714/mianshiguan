"""
Agent 编排器 — 多 Agent 并行执行引擎

职责：
1. 管理多个 Agent 的注册和生命周期
2. 并行执行 Agent（ThreadPoolExecutor）
3. 收集和合成 Agent 输出结果
4. 两级合成策略：LLM 元评估 + 简单平均（降级）
"""

import json
import statistics
import concurrent.futures
from typing import List, Dict, Any, Optional

from src.agents.types import (
    AgentIdentity,
    AgentOutput,
    AgentRole,
    ReviewSynthesis,
)
from src.agents.base_agent import BaseAgent
from src.agents.reviewer_agent import ReviewerAgent
from src.agents.llm_adapter import LLMAdapter


class AgentOrchestrator:
    """
    多 Agent 并行编排引擎。

    使用 ThreadPoolExecutor 实现并行执行（LLM 调用是 I/O 密集型）。

    使用方式：
        orch = AgentOrchestrator(llm_adapter)
        orch.register_reviewer(reviewer1)
        orch.register_reviewer(reviewer2)
        synthesis = orch.run_committee_review(input_data)
    """

    def __init__(self, llm_adapter: LLMAdapter, max_workers: int = 5):
        self.llm = llm_adapter
        self.max_workers = max_workers
        self._reviewers: Dict[str, ReviewerAgent] = {}

    def register_reviewer(self, agent: ReviewerAgent) -> None:
        """注册一个评审 Agent"""
        self._reviewers[agent.agent_id] = agent

    def unregister_reviewer(self, agent_id: str) -> bool:
        """注销一个评审 Agent"""
        if agent_id in self._reviewers:
            del self._reviewers[agent_id]
            return True
        return False

    @property
    def reviewer_count(self) -> int:
        return len(self._reviewers)

    def run_committee_review(
        self,
        input_data: Dict[str, Any],
        reviewer_ids: Optional[List[str]] = None,
    ) -> ReviewSynthesis:
        """
        启动委员会评审。

        1. 并行调用所有（或指定）ReviewerAgent
        2. 收集所有 AgentOutput
        3. 合成最终评审结果

        Args:
            input_data: 面试数据（由 CommitteeReviewManager.build_committee_input 构建）
            reviewer_ids: 指定哪些评审员参与，None 表示全部

        Returns:
            ReviewSynthesis: 综合评审结果

        Raises:
            ValueError: 没有可用的评审员
            RuntimeError: 所有评审员都失败了
        """
        # 确定参与评审的 Agent
        targets = reviewer_ids or list(self._reviewers.keys())
        agents_to_run = [
            self._reviewers[rid]
            for rid in targets
            if rid in self._reviewers
        ]
        if not agents_to_run:
            raise ValueError("没有可用的评审 Agent，请先 register_reviewer()")

        # 并行执行
        results: Dict[str, AgentOutput] = {}
        worker_count = min(self.max_workers, len(agents_to_run))

        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = {
                pool.submit(self._run_single_agent, agent, input_data): agent.agent_id
                for agent in agents_to_run
            }
            for future in concurrent.futures.as_completed(futures, timeout=120):
                agent_id = futures[future]
                try:
                    results[agent_id] = future.result(timeout=60)
                except Exception as e:
                    results[agent_id] = AgentOutput(
                        agent_id=agent_id,
                        role=AgentRole.REVIEWER,
                        success=False,
                        data={},
                        error=f"执行超时或异常: {str(e)}",
                    )

        # 检查是否有成功的结果
        successful = {k: v for k, v in results.items() if v.success}
        if not successful:
            raise RuntimeError(
                f"所有 {len(agents_to_run)} 位委员会评审员均评审失败"
            )

        # 合成
        return self._synthesize(input_data, results)

    def _run_single_agent(
        self, agent: BaseAgent, input_data: Dict[str, Any]
    ) -> AgentOutput:
        """执行单个 Agent（在线程池中调用）"""
        return agent.execute(input_data)

    # ==================== 合成策略 ====================

    def _synthesize(
        self,
        input_data: Dict[str, Any],
        all_results: Dict[str, AgentOutput],
    ) -> ReviewSynthesis:
        """
        Level 2 合成（LLM 元评估）。
        失败时降级到 Level 1（简单平均）。
        """
        try:
            return self._synthesize_with_llm(input_data, all_results)
        except Exception as e:
            print(f"[Orchestrator] LLM 合成失败，降级到简单平均: {e}")
            return self._synthesize_simple(input_data, all_results)

    def _synthesize_with_llm(
        self,
        input_data: Dict[str, Any],
        all_results: Dict[str, AgentOutput],
    ) -> ReviewSynthesis:
        """Level 2: LLM 元评估合成"""
        scenario = input_data.get("scenario_name", "面试")

        # 构建各评审员摘要
        summaries = []
        for agent_id, output in all_results.items():
            reviewer = self._reviewers.get(agent_id)
            focus_label = reviewer.review_focus if reviewer else "unknown"
            if output.success:
                d = output.data
                summaries.append(
                    f"### 评审员 [{focus_label}] {agent_id}\n"
                    f"- 总分: {d.get('overall_score', 'N/A')}\n"
                    f"- 维度评分: {json.dumps(d.get('dimension_scores', {}), ensure_ascii=False)}\n"
                    f"- 优势: {', '.join(d.get('strengths', []))}\n"
                    f"- 改进: {', '.join(d.get('improvements', []))}\n"
                    f"- 评价: {d.get('overall_comment', '')}\n"
                    f"- 自信度: {d.get('confidence', 'N/A')}\n"
                )
            else:
                summaries.append(
                    f"### 评审员 [{focus_label}] {agent_id}\n"
                    f"- 评审失败: {output.error}\n"
                )

        sys_prompt = f"""你是「{scenario}」评审委员会主席。
你的任务是汇总 {len(summaries)} 位独立评审员的意见，形成一份权威的最终评审报告。

要求：
1. 综合各评审员的分数，给出最终加权总分（0-100）
2. 从所有评审员的意见中提炼出最关键的 3-5 条优势和 3-5 条改进建议
3. 对每个评分维度分别汇总（可参考各评审员的维度分数）
4. 如果评审员之间有显著分歧（如某位评 90 分，另一位评 60 分），在总体评价中指出并给出你的判断
5. 总体评价要专业、有指导意义

输出严格 JSON 格式，不要输出任何其他内容：
{{
    "overall_score": <0-100>,
    "dimensions": [{{"name": "维度名", "score": 分数, "max_score": 满分, "comment": "维度评语"}}],
    "strengths": ["优势1", "优势2", ...],
    "improvements": ["建议1", "建议2", ...],
    "overall_comment": "<总体评价>"
}}"""

        user_prompt = (
            f"面试场景：{scenario}\n"
            f"共 {len(all_results)} 位评审员参与独立评审。\n\n"
            + "\n---\n".join(summaries)
            + "\n\n请汇总上述评审意见，输出最终评审报告 JSON。"
        )

        raw = self.llm.call(sys_prompt, user_prompt, temperature=0.2, max_tokens=2000)
        parsed = self._parse_json(raw)

        # 计算评分者间一致性
        agreement = self._calc_agreement(all_results)

        return ReviewSynthesis(
            overall_score=parsed.get("overall_score", 0),
            score_breakdown={
                aid: o.data.get("dimension_scores", {})
                for aid, o in all_results.items()
                if o.success
            },
            strengths=parsed.get("strengths", []),
            improvements=parsed.get("improvements", []),
            dimensions=parsed.get("dimensions", []),
            overall_comment=parsed.get("overall_comment", ""),
            passed=parsed.get("overall_score", 0) >= 60,
            agreement_score=agreement,
            individual_reports=list(all_results.values()),
        )

    def _synthesize_simple(
        self,
        input_data: Dict[str, Any],
        all_results: Dict[str, AgentOutput],
    ) -> ReviewSynthesis:
        """Level 1 降级：简单平均 + 去重合并"""
        successful = [o for o in all_results.values() if o.success]
        scores = [o.data.get("overall_score", 0) for o in successful]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        # 合并去重
        all_strengths: List[str] = []
        all_improvements: List[str] = []
        all_comments: List[str] = []
        for o in successful:
            all_strengths.extend(o.data.get("strengths", []))
            all_improvements.extend(o.data.get("improvements", []))
            comment = o.data.get("overall_comment", "")
            if comment:
                all_comments.append(f"[{o.agent_id}]: {comment}")

        strengths = self._deduplicate(all_strengths)[:5]
        improvements = self._deduplicate(all_improvements)[:5]

        agreement = self._calc_agreement(all_results)

        return ReviewSynthesis(
            overall_score=avg_score,
            score_breakdown={
                aid: o.data.get("dimension_scores", {})
                for aid, o in all_results.items()
                if o.success
            },
            strengths=strengths,
            improvements=improvements,
            dimensions=[],
            overall_comment=(
                f"本报告由 {len(successful)} 位独立评审员评分后综合生成。"
                f"评审一致性: {agreement:.0%}。\n\n"
                + "\n\n".join(all_comments[:3])
            ),
            passed=avg_score >= 60,
            agreement_score=agreement,
            individual_reports=list(all_results.values()),
        )

    # ==================== 工具方法 ====================

    def _calc_agreement(self, all_results: Dict[str, AgentOutput]) -> float:
        """计算评分者间一致性（1 - 变异系数，钳制到 [0, 1]）"""
        scores = [
            o.data.get("overall_score", 0)
            for o in all_results.values()
            if o.success
        ]
        if len(scores) < 2:
            return 1.0

        mean_score = sum(scores) / len(scores)
        if mean_score == 0:
            return 1.0

        std_dev = statistics.stdev(scores)
        agreement = max(0.0, 1.0 - (std_dev / mean_score))
        return min(agreement, 1.0)

    @staticmethod
    def _deduplicate(strings: List[str]) -> List[str]:
        """简单去重：去除互相包含的字符串"""
        unique: List[str] = []
        for s in strings:
            s_lower = s.lower()
            if not any(
                s_lower in u.lower() or u.lower() in s_lower
                for u in unique
            ):
                unique.append(s)
        return unique

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """解析 LLM 返回的 JSON"""
        import re
        raw = raw.strip()
        # 直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # 提取 ```json ... ``` 块
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
        if m:
            return json.loads(m.group(1).strip())
        # 提取 { ... }
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            return json.loads(m.group())
        raise ValueError(f"无法解析 JSON: {raw[:200]}")
