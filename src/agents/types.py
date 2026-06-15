"""多 Agent 协作系统的核心数据类型定义"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentRole(Enum):
    """Agent 角色类型"""
    EXAMINER = "examiner"        # 实时面试考官
    REVIEWER = "reviewer"        # 面试后独立评审员
    SYNTHESIZER = "synthesizer"  # 委员会主席（汇总合成）


class InterviewMode(Enum):
    """面试模式"""
    SINGLE = "single"            # 向后兼容的单 Agent 模式
    COMMITTEE = "committee"      # 委员会评审模式（面试后多 Agent 评分）


@dataclass
class AgentIdentity:
    """单个 Agent 的身份/人设定义"""
    id: str                                    # 唯一标识，如 "reviewer_strict"
    name: str                                  # 显示名称，如 "严苛评审员"
    title: str                                 # 头衔，如 "高级技术评审专家"
    role: AgentRole                            # examiner / reviewer / synthesizer
    system_prompt: str = ""                    # Agent 专属 system prompt
    style_tags: List[str] = field(default_factory=list)    # ["strict", "detail-oriented"]
    scoring_weights: Dict[str, float] = field(default_factory=dict)  # 维度权重覆盖


@dataclass
class AgentOutput:
    """单个 Agent 的执行结果"""
    agent_id: str
    role: AgentRole
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)   # 结构化结果
    raw_response: str = ""
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class ReviewSynthesis:
    """委员会综合评审结果"""
    overall_score: float
    score_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    dimensions: List[Dict[str, Any]] = field(default_factory=list)
    overall_comment: str = ""
    passed: bool = False
    agreement_score: float = 0.0               # 评分者间一致性 (0-1)
    individual_reports: List[AgentOutput] = field(default_factory=list)
