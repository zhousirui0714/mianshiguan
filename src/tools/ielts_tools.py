"""雅思口语场景工具"""

from src.core.tool import BaseTool, LLMToolMixin
from src.core.tool.types import ToolCallRequest, ToolCallResult


class PronunciationAnalyzerTool(BaseTool, LLMToolMixin):
    """发音分析工具（LLM 增强版）"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        text = request.arguments.get("speech_text", "")

        if text.strip():
            llm_data = self._llm_analyze(
                prompt="请分析以下英语口语文本的流利度和发音相关表现。返回 JSON：\n"
                       '{"fluency_score": 0-100, '
                       '"filler_count": 填充词数量, '
                       '"pace_assessment": "语速评估", '
                       '"suggestion": "改进建议"}',
                user_input=text,
                system_prompt="You are an IELTS speaking examiner. Analyze fluency and pronunciation aspects.",
            )

            if llm_data and "fluency_score" in llm_data:
                return ToolCallResult(
                    tool_id=self.tool_id,
                    success=True,
                    data={
                        "word_count": len(text.split()),
                        "filler_count": llm_data.get("filler_count", 0),
                        "fluency_score": float(llm_data["fluency_score"]),
                        "pace_assessment": llm_data.get("pace_assessment", ""),
                        "suggestion": llm_data.get("suggestion", ""),
                    }
                )

        # 降级：规则分析
        words = text.split()
        word_count = len(words)
        fillers = ["um", "uh", "er", "ah", "like", "well", "you know", "actually"]
        filler_count = sum(text.lower().count(f) for f in fillers)
        fluency_score = max(0, 100 - filler_count * 10)
        fluency_score = min(100, fluency_score + min(word_count * 2, 30))

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "word_count": word_count,
                "filler_count": filler_count,
                "fluency_score": round(fluency_score, 1),
                "suggestion": f"减少填充词（如 um, uh），当前使用了 {filler_count} 次" if filler_count > 2 else "流利度良好",
            }
        )


class VocabularyCheckerTool(BaseTool, LLMToolMixin):
    """词汇检查工具（LLM 增强版）"""

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        response_text = request.arguments.get("user_response", "")
        topic = request.arguments.get("topic", "general")

        if response_text.strip():
            llm_data = self._llm_analyze(
                prompt=f"话题：{topic}\n\n"
                       "请分析以下英语口语文本的词汇水平。返回 JSON：\n"
                       '{"total_words": 总词数, '
                       '"unique_words": 不重复词数, '
                       '"diversity_ratio": 词汇多样性百分比, '
                       '"advanced_words_used": ["高级词汇1", "高级词汇2", ...], '
                       '"band_estimate": "预估雅思分数段", '
                       '"suggestion": "改进建议"}',
                user_input=response_text,
                system_prompt="You are an IELTS vocabulary expert. Assess lexical resource accurately.",
            )

            if llm_data and "diversity_ratio" in llm_data and "band_estimate" in llm_data:
                return ToolCallResult(
                    tool_id=self.tool_id,
                    success=True,
                    data={
                        "total_words": llm_data.get("total_words", len(response_text.split())),
                        "unique_words": llm_data.get("unique_words", 0),
                        "diversity_ratio": float(llm_data["diversity_ratio"]),
                        "advanced_words_used": llm_data.get("advanced_words_used", []),
                        "advanced_count": len(llm_data.get("advanced_words_used", [])),
                        "band_estimate": llm_data["band_estimate"],
                        "suggestion": llm_data.get("suggestion", ""),
                    }
                )

        # 降级：规则检测
        words = response_text.lower().split()
        unique_words = set(words)
        diversity = round(len(unique_words) / max(len(words), 1) * 100, 1)
        advanced_words = [
            "demonstrate", "significant", "particularly", "consequently",
            "nevertheless", "furthermore", "moreover", "substantial",
            "inevitable", "phenomenon", "perspective", "comprehensive",
            "ultimately", "fundamental", "implication", "contribute",
        ]
        advanced_used = [w for w in advanced_words if w in response_text.lower().split()]

        def _estimate_band(diversity, advanced_count):
            if diversity > 70 and advanced_count >= 5:
                return "7.0+"
            elif diversity > 55 or advanced_count >= 3:
                return "6.0-6.5"
            else:
                return "5.0-5.5"

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "total_words": len(words),
                "unique_words": len(unique_words),
                "diversity_ratio": diversity,
                "advanced_words_used": advanced_used,
                "advanced_count": len(advanced_used),
                "band_estimate": _estimate_band(diversity, len(advanced_used)),
                "suggestion": "建议增加同义替换和高级词汇" if len(advanced_used) < 3 else "词汇使用较好",
            }
        )


class GrammarCheckerTool(BaseTool, LLMToolMixin):
    """语法检查工具（LLM 增强版）"""

    COMMON_MISTAKES = [
        ("he don't", "he doesn't"),
        ("she don't", "she doesn't"),
        ("more better", "better"),
        ("more easier", "easier"),
        ("most easiest", "easiest"),
        ("could of", "could have"),
        ("should of", "should have"),
        ("would of", "would have"),
        ("its not", "it's not"),
        ("your welcome", "you're welcome"),
        ("there is many", "there are many"),
        ("there is several", "there are several"),
        ("less people", "fewer people"),
        ("less mistakes", "fewer mistakes"),
    ]

    def execute(self, request: ToolCallRequest) -> ToolCallResult:
        text = request.arguments.get("user_response", "")

        if text.strip():
            llm_data = self._llm_analyze(
                prompt="请检查以下英语文本的语法错误。返回 JSON：\n"
                       '{"errors": [{"error": "错误描述", "suggestion": "修正建议", "context": "上下文"}], '
                       '"error_count": 错误数量, '
                       '"accuracy_level": "优秀|良好|一般|需提高", '
                       '"score": 0-100, '
                       '"summary": "总体评价"}',
                user_input=text,
                system_prompt="You are an English grammar expert. Identify grammar errors accurately.",
            )

            if llm_data and "error_count" in llm_data and "score" in llm_data:
                return ToolCallResult(
                    tool_id=self.tool_id,
                    success=True,
                    data={
                        "error_count": llm_data["error_count"],
                        "total_words": len(text.split()),
                        "score": llm_data["score"],
                        "accuracy": llm_data.get("accuracy_level", "良好"),
                        "errors": llm_data.get("errors", []),
                        "summary": llm_data.get("summary", "语法检查完成"),
                    }
                )

        # 降级：规则匹配
        text_lower = text.lower()
        errors = []
        for mistake, correction in self.COMMON_MISTAKES:
            if mistake in text_lower:
                errors.append({"error": mistake, "suggestion": correction})

        error_count = len(errors)
        total_words = len(text.split())
        error_rate = round(error_count / max(total_words, 1) * 100, 2)

        if error_rate < 1:
            accuracy = "优秀"
            score = 90
        elif error_rate < 3:
            accuracy = "良好"
            score = 75
        elif error_rate < 5:
            accuracy = "一般"
            score = 60
        else:
            accuracy = "需提高"
            score = 40

        return ToolCallResult(
            tool_id=self.tool_id,
            success=True,
            data={
                "error_count": error_count,
                "total_words": total_words,
                "error_rate": error_rate,
                "accuracy": accuracy,
                "score": score,
                "errors": errors,
                "summary": f"语法准确度 {accuracy}，发现 {error_count} 处常见错误",
            }
        )
