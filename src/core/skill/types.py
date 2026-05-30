"""Skill 模块核心类型定义"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== 配置层类型 ====================

@dataclass
class PersonaConfig:
    """考官人设配置"""
    name: str
    title: str
    tone: str
    background: str
    greeting_template: str = ""
    system_prompt: str = ""


@dataclass
class ScoringDimension:
    """评分维度"""
    id: str
    name: str
    max_score: int = 100
    weight: int = 0
    description: str = ""


@dataclass
class ScoringConfig:
    """评分配置"""
    dimensions: List[ScoringDimension] = field(default_factory=list)
    passing_score: int = 60

    @property
    def total_weight(self) -> int:
        return sum(d.weight for d in self.dimensions)


@dataclass
class FeedbackTemplate:
    """反馈模板"""
    condition: str = ""
    template: str = ""


@dataclass
class FeedbackConfig:
    """反馈配置"""
    strengths_templates: List[FeedbackTemplate] = field(default_factory=list)
    improvements_templates: List[FeedbackTemplate] = field(default_factory=list)


@dataclass
class SkillConfig:
    """Skill 完整配置（从 YAML 加载）"""
    id: str
    name: str
    category: str = ""
    enabled: bool = True
    persona: PersonaConfig = field(default_factory=PersonaConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    tools: List[str] = field(default_factory=list)
    max_rounds: int = 5

    @classmethod
    def from_dict(cls, data: dict) -> "SkillConfig":
        """从嵌套 dict 构建（YAML 加载后的结构）"""
        persona_data = data.get("persona", {})
        scoring_data = data.get("scoring", {})
        feedback_data = data.get("feedback", {})

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            enabled=data.get("enabled", True),
            persona=PersonaConfig(
                name=persona_data.get("name", ""),
                title=persona_data.get("title", ""),
                tone=persona_data.get("tone", ""),
                background=persona_data.get("background", ""),
                greeting_template=persona_data.get("greeting_template", ""),
                system_prompt=persona_data.get("system_prompt", ""),
            ),
            scoring=ScoringConfig(
                dimensions=[
                    ScoringDimension(**d) for d in scoring_data.get("dimensions", [])
                ],
                passing_score=scoring_data.get("passing_score", 60),
            ),
            feedback=FeedbackConfig(
                strengths_templates=[
                    FeedbackTemplate(**t) for t in feedback_data.get("strengths_templates", [])
                ],
                improvements_templates=[
                    FeedbackTemplate(**t) for t in feedback_data.get("improvements_templates", [])
                ],
            ),
            tools=data.get("tools", []),
            max_rounds=data.get("max_rounds", 5),
        )


# ==================== 运行时类型 ====================

@dataclass
class AnswerRecord:
    """单轮答题记录"""
    round: int
    question: str
    answer: str
    score: Optional[float] = None
    feedback: str = ""
    duration: int = 0  # 耗时（秒）


@dataclass
class SkillSession:
    """Skill 会话"""
    id: str
    skill_id: str
    user_id: str
    started_at: datetime = field(default_factory=datetime.now)
    round: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    answers: List[AnswerRecord] = field(default_factory=list)


@dataclass
class EvaluationResult:
    """单次评分结果"""
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    comment: str = ""
    passed: bool = False


@dataclass
class FeedbackReport:
    """最终反馈报告"""
    overall_score: float = 0.0
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    dimension_scores: List[Dict[str, Any]] = field(default_factory=list)
    overall_comment: str = ""
    passed: bool = False
    new_badges: List[str] = field(default_factory=list)
