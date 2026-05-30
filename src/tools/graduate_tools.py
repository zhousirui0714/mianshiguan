"""考研复试场景工具"""

from src.core.tool import BaseTool
from src.core.tool.types import ToolCallRequest, ToolCallResult


class ResearchProposalEvaluatorTool(BaseTool):
    """研究计划评估工具"""

    DIMENSIONS = [
        {"name": "问题意识", "keywords": ["问题", "gap", "空白", "不足", "挑战"]},
        {"name": "方法设计", "keywords": ["方法", "实验", "模型", "分析", "数据"]},
        {"name": "创新性", "keywords": ["创新", "首次", "新方法", "改进", "突破"]},
        {"name": "可行性", "keywords": ["可行", "条件", "资源", "时间", "基础"]},
        {"name": "学术价值", "keywords": ["意义", "价值", "贡献", "应用", "影响"]},
    ]

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        plan = request.arguments.get("research_plan", "")
        field = request.arguments.get("field", "")

        dimension_scores = {}
        for dim in self.DIMENSIONS:
            found = sum(1 for kw in dim["keywords"] if kw in plan)
            score = min(100, found * 25)
            dimension_scores[dim["name"]] = score

        total_score = round(sum(dimension_scores.values()) / len(dimension_scores), 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "field": field,
                "total_score": total_score,
                "dimension_scores": dimension_scores,
                "suggestion": self._get_suggestion(dimension_scores),
            }
        )

    def _get_suggestion(self, scores: dict) -> str:
        weak = [k for k, v in scores.items() if v < 50]
        if weak:
            return f"建议加强{'、'.join(weak)}方面的阐述"
        return "研究计划较为完整"


class LiteratureReviewCheckerTool(BaseTool):
    """文献综述检查工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        review = request.arguments.get("review_text", "")
        field = request.arguments.get("field", "")

        checks = {
            "研究背景": any(kw in review for kw in ["背景", "现状", "发展", "趋势"]),
            "文献梳理": any(kw in review for kw in ["文献", "研究", "学者", "等人"]),
            "分类评述": any(kw in review for kw in ["类", "方面", "角度", "层面"]),
            "不足分析": any(kw in review for kw in ["不足", "局限", "问题", "空白"]),
            "研究定位": any(kw in review for kw in ["本文", "本研究", "本课题", "本文研究"]),
        }

        passed = sum(1 for v in checks.values() if v)
        score = round(passed / len(checks) * 100, 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "field": field,
                "score": score,
                "checks": checks,
                "summary": f"文献综述完整性 {score} 分",
                "suggestion": "建议增加对现有研究不足的分析" if not checks["不足分析"] else "文献综述较为全面",
            }
        )


class AcademicExpressionCheckerTool(BaseTool):
    """学术表达检查工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        text = request.arguments.get("text", "")

        checks = {
            "术语规范": any(kw in text for kw in ["定义", "概念", "理论", "范式", "模型"]),
            "逻辑连接": any(kw in text for kw in ["因此", "然而", "此外", "总之", "基于"]),
            "数据支撑": any(kw in text for kw in ["数据", "比例", "统计", "实验", "案例"]),
            "客观表达": any(kw in text for kw in ["可能", "通常", "一般", "倾向于", "研究表明"]),
        }

        passed = sum(1 for v in checks.values() if v)
        score = round(passed / len(checks) * 100, 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "score": score,
                "checks": checks,
                "suggestion": "建议增加逻辑连接词和客观表达" if score < 75 else "学术表达规范",
            }
        )
