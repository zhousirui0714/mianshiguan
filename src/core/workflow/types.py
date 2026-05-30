"""工作流引擎类型定义"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime


@dataclass
class StageConfig:
    """流水线阶段配置"""
    name: str
    enabled: bool = True
    retry_count: int = 3
    retry_delay: float = 1.0  # seconds
    timeout: float = 30.0
    depends_on: List[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    """流水线配置"""
    stages: List[StageConfig] = field(default_factory=list)
    fail_fast: bool = False  # True: 某阶段失败则终止; False: 继续执行后续阶段
    async_mode: bool = False  # True: 异步执行; False: 同步

    def get_enabled_stages(self) -> List[StageConfig]:
        return [s for s in self.stages if s.enabled]


@dataclass
class StageResult:
    """阶段执行结果"""
    stage_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    retry_count: int = 0


@dataclass
class WorkflowContext:
    """工作流上下文（各阶段共享）"""
    user_id: str
    scenario_id: str
    conversation_id: str
    skill_id: str
    session: Any = None  # SkillSession
    report: Any = None   # FeedbackReport
    new_badges: List[Any] = field(default_factory=list)
    progress_updated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class PipelineResult:
    """流水线执行结果"""
    success: bool
    context: WorkflowContext
    stage_results: List[StageResult] = field(default_factory=list)
    total_duration: float = 0.0
