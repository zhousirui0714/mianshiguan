"""公务员面试场景工具"""

from src.core.tool import BaseTool
from src.core.tool.types import ToolCallRequest, ToolCallResult


class PolicyKnowledgeCheckerTool(BaseTool):
    """政策理论检查工具"""

    KEY_POLICIES = {
        "economy": ["高质量发展", "供给侧改革", "双循环", "新发展格局", "共同富裕"],
        "society": ["乡村振兴", "基层治理", "民生保障", "公共服务", "社会治理"],
        "culture": ["文化自信", "社会主义核心价值观", "精神文明", "传统文化"],
        "ecology": ["绿水青山", "生态文明", "碳中和", "碳达峰", "绿色发展"],
        "governance": ["放管服", "数字政府", "依法治国", "全面从严治党", "治理现代化"],
    }

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        answer = request.arguments.get("user_answer", "")
        area = request.arguments.get("policy_area", "economy")

        policies = self.KEY_POLICIES.get(area, self.KEY_POLICIES["economy"])
        used = [p for p in policies if p in answer]

        total = len(policies)
        used_count = len(used)
        coverage = round(used_count / total * 100, 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "policy_area": area,
                "policies_used": used,
                "coverage": coverage,
                "total_related": total,
                "assessment": "政策理论运用充分" if coverage > 50 else "建议增加政策理论引用",
                "suggestion": f"可进一步引用{'、'.join([p for p in policies if p not in used])[:3]}..." if used_count < total else "政策引用全面",
            }
        )


class EmergencyResponseScorerTool(BaseTool):
    """应急处理评分工具"""

    DIMENSIONS = [
        {"name": "快速反应", "keywords": ["立即", "第一时间", "迅速", "马上", "紧急"]},
        {"name": "依法处理", "keywords": ["依法", "按规定", "政策", "法律", "程序"]},
        {"name": "以人为本", "keywords": ["安全", "生命", "安抚", "群众", "沟通"]},
        {"name": "上报机制", "keywords": ["上报", "汇报", "报告", "请示", "通报"]},
        {"name": "总结改进", "keywords": ["总结", "反思", "改进", "完善", "预防"]},
    ]

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        solution = request.arguments.get("user_solution", "")

        dimension_scores = {}
        for dim in self.DIMENSIONS:
            found = sum(1 for kw in dim["keywords"] if kw in solution)
            score = min(100, found * 25)
            dimension_scores[dim["name"]] = score

        total_score = round(sum(dimension_scores.values()) / len(dimension_scores), 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "total_score": total_score,
                "dimension_scores": dimension_scores,
                "strengths": [k for k, v in dimension_scores.items() if v >= 50],
                "improvements": [k for k, v in dimension_scores.items() if v < 50],
                "summary": f"应急处理评分 {total_score} 分，"
                           f"需加强方面：{', '.join(k for k, v in dimension_scores.items() if v < 50) or '无'}"
            }
        )


class DocumentWritingEvaluatorTool(BaseTool):
    """公文写作评估工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        doc_type = request.arguments.get("document_type", "report")
        content = request.arguments.get("content", "")

        checks = {
            "格式规范": any(kw in content for kw in ["标题", "正文", "落款", "日期"]),
            "语言得体": any(kw in content for kw in ["请", "建议", "要求", "通知", "报告"]),
            "结构完整": any(kw in content for kw in ["一、", "二、", "三、", "首先", "其次", "最后"]),
            "内容具体": len(content) > 100,
            "逻辑清晰": any(kw in content for kw in ["因此", "鉴于", "为了", "根据"]),
        }

        passed = sum(1 for v in checks.values() if v)
        score = round(passed / len(checks) * 100, 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "document_type": doc_type,
                "score": score,
                "checks": checks,
                "passed_items": passed,
                "total_items": len(checks),
                "summary": f"公文写作评分 {score} 分"
            }
        )
