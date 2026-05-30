"""MBA 面试场景工具"""

from src.core.tool import BaseTool
from src.core.tool.types import ToolCallRequest, ToolCallResult


class LeadershipAnalyzerTool(BaseTool):
    """领导力分析工具"""

    LEADERSHIP_STYLES = {
        "变革型": ["愿景", "变革", "激励", "鼓舞", "创新"],
        "事务型": ["目标", "考核", "奖惩", "规则", "标准"],
        "服务型": ["团队", "成长", "授权", "支持", "服务"],
        "民主型": ["讨论", "共识", "意见", "投票", "协商"],
        "教练型": ["培养", "指导", "反馈", "辅导", "成长"],
    }

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        desc = request.arguments.get("experience_description", "")

        style_scores = {}
        for style, keywords in self.LEADERSHIP_STYLES.items():
            found = sum(1 for kw in keywords if kw in desc)
            style_scores[style] = found

        dominant = max(style_scores, key=style_scores.get)
        total_indicators = sum(style_scores.values())

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "dominant_style": dominant,
                "style_scores": style_scores,
                "total_leadership_indicators": total_indicators,
                "assessment": f"主要领导风格为{dominant}型，展现出一定的团队管理意识" if total_indicators > 0 else "建议补充具体的领导经历",
                "suggestion": "建议在描述中加入具体的数据和案例来支撑领导力表现",
            }
        )


class CareerPlanEvaluatorTool(BaseTool):
    """职业规划评估工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        goal = request.arguments.get("career_goal", "")
        current = request.arguments.get("current_status", "")
        mba_exp = request.arguments.get("mba_expectation", "")

        checks = {
            "目标明确": len(goal) > 20,
            "现状清晰": len(current) > 20,
            "MBA 价值": len(mba_exp) > 15,
            "逻辑连贯": any(kw in goal for kw in ["短期", "长期", "阶段", "规划"]) or
                       any(kw in current for kw in ["目前", "当前", "现有"]),
            "可行性": any(kw in mba_exp for kw in ["资源", "平台", "人脉", "知识", "能力"]),
        }

        passed = sum(1 for v in checks.values() if v)
        score = round(passed / len(checks) * 100, 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "score": score,
                "checks": checks,
                "summary": f"职业规划评估 {score} 分",
                "suggestion": "建议将职业目标与MBA学习内容更紧密地结合" if not checks["MBA 价值"] else "职业规划清晰",
            }
        )


class CaseAnalysisScorerTool(BaseTool):
    """案例分析评分工具"""

    DIMENSIONS = [
        {"name": "问题识别", "keywords": ["问题", "挑战", "困境", "矛盾", "风险"]},
        {"name": "分析框架", "keywords": ["框架", "模型", "维度", "SWOT", "波特", "PEST"]},
        {"name": "数据支撑", "keywords": ["数据", "比例", "增长", "下降", "市场"]},
        {"name": "解决方案", "keywords": ["建议", "方案", "策略", "措施", "路径"]},
        {"name": "可执行性", "keywords": ["实施", "阶段", "资源", "时间", "步骤"]},
    ]

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        analysis = request.arguments.get("user_analysis", "")

        dimension_scores = {}
        for dim in self.DIMENSIONS:
            found = sum(1 for kw in dim["keywords"] if kw in analysis)
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
                "summary": f"案例分析评分 {total_score} 分",
            }
        )
