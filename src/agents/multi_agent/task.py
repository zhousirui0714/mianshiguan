"""任务分解模式 — 领域类型定义

Orchestrator 接收用户输入 → 拆分成子任务 → 分发给 Worker → 汇总结果
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time
import uuid


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class SubTask:
    """
    Orchestrator 拆分的子任务。

    input_schema: 定义 Worker 接收什么格式的输入
    output_schema: 定义 Worker 必须返回什么格式的输出
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""                              # 人类可读的任务描述
    assigned_worker: str = ""                          # 分配给哪个 Worker
    input_schema: Dict[str, str] = field(default_factory=dict)   # {字段名: 类型}
    input_data: Dict[str, Any] = field(default_factory=dict)     # 实际输入数据
    output_schema: Dict[str, str] = field(default_factory=dict)  # {字段名: 类型}
    status: TaskStatus = TaskStatus.PENDING

    def __repr__(self):
        return f"<SubTask {self.id} [{self.status.value}] →{self.assigned_worker}>"


@dataclass
class TaskResult:
    """Worker 返回的子任务结果"""
    task_id: str
    worker_id: str
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.DONE
    error: str = ""
    duration: float = 0.0

    def is_valid(self, schema: Dict[str, str]) -> bool:
        """验证 output_data 是否符合 output_schema"""
        for field, expected_type in schema.items():
            if field not in self.output_data:
                return False
            actual = self.output_data[field]
            if expected_type == "str" and not isinstance(actual, str):
                return False
            if expected_type == "int" and not isinstance(actual, int):
                return False
            if expected_type == "float" and not isinstance(actual, (int, float)):
                return False
            if expected_type == "list" and not isinstance(actual, list):
                return False
            if expected_type == "dict" and not isinstance(actual, dict):
                return False
        return True

    def __repr__(self):
        return f"<Result {self.task_id} [{self.status.value}] from {self.worker_id}>"


@dataclass
class DecomposeResult:
    """一次完整的任务分解 + 执行 + 汇总的结果"""
    user_input: str
    subtasks: List[SubTask] = field(default_factory=list)
    results: List[TaskResult] = field(default_factory=list)
    aggregated: Dict[str, Any] = field(default_factory=dict)
    total_duration: float = 0.0
    success_count: int = 0
    error_count: int = 0
