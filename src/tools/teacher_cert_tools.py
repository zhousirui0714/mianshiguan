"""教资面试场景工具"""

from src.core.tool import BaseTool, LLMToolMixin
from src.core.tool.types import ToolCallRequest, ToolCallResult


class LessonPlanScorerTool(BaseTool, LLMToolMixin):
    """教案评分工具（LLM 增强版）"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        plan = request.arguments.get("lesson_plan", "")

        if plan.strip():
            llm_data = self._llm_analyze(
                prompt="请评估以下教案的完整性和质量。返回 JSON：\n"
                       '{"score": 0-100, '
                       '"checks": {"教学目标": true/false, "教学过程": true/false, '
                       '"教学方法": true/false, "板书设计": true/false, "作业布置": true/false}, '
                       '"missing": ["缺少的元素1", ...], '
                       '"summary": "评价", '
                       '"suggestion": "改进建议"}',
                user_input=plan,
                system_prompt="你是一个资深教研员，擅长评估教案质量。",
            )

            if llm_data and "score" in llm_data:
                checks = llm_data.get("checks", {})
                missing = llm_data.get("missing", [])
                return ToolCallResult(
                    tool_id=self.tool_id,
                    success=True,
                    data={
                        "score": float(llm_data["score"]),
                        "checks": checks,
                        "passed_items": sum(1 for v in checks.values() if v),
                        "total_items": len(checks),
                        "missing": missing,
                        "suggestion": llm_data.get("suggestion", ""),
                        "summary": llm_data.get("summary", f"教案评估完成，得分 {llm_data['score']} 分"),
                    }
                )

        # 降级：关键词检测
        checks = {
            "教学目标": any(kw in plan for kw in ["目标", "目的", "要求"]),
            "教学过程": any(kw in plan for kw in ["导入", "讲解", "练习", "小结"]),
            "教学方法": any(kw in plan for kw in ["方法", "讨论", "活动", "互动"]),
            "板书设计": "板书" in plan or "板書" in plan,
            "作业布置": "作业" in plan or "练习" in plan,
        }
        passed = sum(1 for v in checks.values() if v)
        score = round(passed / len(checks) * 100, 1)
        missing = [k for k, v in checks.items() if not v]

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "score": score,
                "checks": checks,
                "passed_items": passed,
                "total_items": len(checks),
                "missing": missing,
                "summary": f"教案完整性评分 {score} 分"
                           + (f"，缺少: {', '.join(missing)}" if missing else "，结构完整"),
            }
        )


class BlackboardDesignCheckerTool(BaseTool):
    """板书设计检查工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        design = request.arguments.get("board_design", "")

        checks = {
            "结构清晰": any(kw in design for kw in ["结构", "层次", "框架", "大纲"]),
            "重点突出": any(kw in design for kw in ["重点", "关键", "核心"]),
            "逻辑连贯": any(kw in design for kw in ["逻辑", "顺序", "流程"]),
            "视觉辅助": any(kw in design for kw in ["图表", "箭头", "符号", "颜色"]),
            "板面布局": any(kw in design for kw in ["布局", "分区", "板块"]),
        }

        passed = sum(1 for v in checks.values() if v)
        score = round(passed / len(checks) * 100, 1)

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "score": score,
                "checks": checks,
                "suggestion": "建议增加层次结构和重点标记" if score < 60 else "板书设计合理",
            }
        )


class TeachingMethodEvaluatorTool(BaseTool):
    """教学方法评估工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        method = request.arguments.get("method_description", "")
        student_level = request.arguments.get("student_level", "middle")

        methods_found = []
        for m in ["讲授", "讨论", "演示", "练习", "游戏", "案例", "项目", "探究"]:
            if m in method:
                methods_found.append(m)

        diversity = len(methods_found)
        if diversity >= 4:
            level = "丰富"
            score = 90
        elif diversity >= 2:
            level = "中等"
            score = 65
        else:
            level = "单一"
            score = 40

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "methods_found": methods_found,
                "method_count": diversity,
                "diversity_level": level,
                "score": score,
                "student_level": student_level,
                "suggestion": "建议结合多种教学方法提高课堂互动性" if diversity < 3 else "教学方法多样，效果良好",
            }
        )
