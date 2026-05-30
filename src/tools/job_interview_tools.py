"""求职面试场景工具"""

from src.core.tool import BaseTool, LLMToolMixin
from src.core.tool.types import ToolCallRequest, ToolCallResult


class ResumeAnalyzerTool(BaseTool, LLMToolMixin):
    """简历分析工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        resume = request.arguments.get("resume_text", "")

        # 尝试 LLM 分析
        llm_data = self._llm_analyze(
            prompt="请分析以下简历内容，提取关键信息。返回 JSON 格式："
                   '{"skills": ["技能1", "技能2", ...], '
                   '"experience_years": 年数, '
                   '"key_achievements": ["成就1", ...], '
                   '"summary": "简短总结"}',
            user_input=resume,
            system_prompt="你是一个专业的简历分析师，擅长从简历中提取关键信息并评估候选人的能力。",
        )

        if llm_data and "skills" in llm_data and "summary" in llm_data:
            return ToolCallResult(
                tool_id=self.tool_id,
                success=True,
                data={
                    "skills_found": llm_data.get("skills", []),
                    "skill_count": len(llm_data.get("skills", [])),
                    "experience_years": llm_data.get("experience_years", 0),
                    "key_achievements": llm_data.get("key_achievements", []),
                    "summary": llm_data.get("summary", "简历分析完成"),
                }
            )

        # 降级：关键词检测
        lines = resume.strip().split("\n")
        skills = [w for w in ["Python", "Java", "Go", "React", "Vue", "Docker", "K8s", "SQL"]
                  if w.lower() in resume.lower()]
        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "skills_found": skills,
                "skill_count": len(skills),
                "line_count": len(lines),
                "summary": f"检测到 {len(skills)} 项技术关键词，共 {len(lines)} 行内容",
            }
        )


class STARQuestionGeneratorTool(BaseTool):
    """STAR 法则问题生成工具"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        project = request.arguments.get("project_description", "")
        focus = request.arguments.get("focus_area", "challenge")

        questions = {
            "challenge": "在这个项目中，你遇到的最大技术挑战是什么？你是如何解决的？",
            "contribution": "请具体说明你在项目中的个人贡献，哪些部分是你独立完成的？",
            "result": "这个项目取得了什么样的成果？有没有可量化的数据？",
            "teamwork": "你在团队中承担什么角色？如何与团队成员协作？",
        }
        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "question": questions.get(focus, questions["challenge"]),
                "star_suggestion": "建议用 STAR 法则回答：Situation(背景) → Task(任务) → Action(行动) → Result(结果)",
            }
        )


class TechDepthCheckerTool(BaseTool, LLMToolMixin):
    """技术深度检查工具（LLM 增强版）"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        tech = request.arguments.get("tech_stack", "")
        desc = request.arguments.get("user_description", "")

        # 尝试 LLM 分析
        if desc.strip():
            llm_data = self._llm_analyze(
                prompt=f"用户声称掌握的技术栈：{tech}\n\n"
                       f"用户的描述：{desc}\n\n"
                       "请评估该用户的技术深度水平。返回 JSON 格式：\n"
                       '{"level": "初步了解|基本掌握|熟练应用|深入理解|专家级", '
                       '"score": 0-100, '
                       '"strengths": ["优势点1", ...], '
                       '"weaknesses": ["不足点1", ...], '
                       '"suggestion": "改进建议"}',
                user_input=desc,
                system_prompt="你是一个资深技术面试官，擅长评估候选人的技术深度。",
            )

            if llm_data and "level" in llm_data and "score" in llm_data:
                return ToolCallResult(
                    tool_id=self.tool_id,
                    success=True,
                    data={
                        "tech": tech,
                        "level": llm_data["level"],
                        "score": llm_data["score"],
                        "strengths": llm_data.get("strengths", []),
                        "weaknesses": llm_data.get("weaknesses", []),
                        "suggestion": llm_data.get("suggestion", ""),
                    }
                )

        # 降级：基于长度的规则评分
        desc_len = len(desc)
        if desc_len < 20:
            level = "初步了解"
            score = 30
        elif desc_len < 50:
            level = "基本掌握"
            score = 55
        elif desc_len < 100:
            level = "熟练应用"
            score = 75
        else:
            level = "深入理解"
            score = 90

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "tech": tech,
                "level": level,
                "score": score,
                "suggestion": "建议结合实际项目案例，说明技术选型的原因和实际效果" if score < 75 else "技术水平较好，可进一步展示架构设计能力",
            }
        )
