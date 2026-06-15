"""
任务分解模式的 Agent 实现

- WorkerAgent: 接收子任务 → 处理 → 返回 TaskResult
- OrchestratorAgent: 接收用户输入 → 分解 → 分发 → 收集 → 汇总
"""

import time
from typing import List, Dict, Callable, Optional

from src.agents.multi_agent.agent import BaseAgent
from src.agents.multi_agent.bus import MessageBus
from src.agents.multi_agent.message import Message, MessageType
from src.agents.multi_agent.task import SubTask, TaskResult, TaskStatus, DecomposeResult


class WorkerAgent(BaseAgent):
    """
    Worker Agent — 执行子任务。

    每个 Worker 有明确的：
    - capability: 能力描述（如 "文本分析", "代码审查"）
    - input_schema: 接受的输入格式 {字段: 类型}
    - output_schema: 输出的格式 {字段: 类型}
    - handler: 处理函数 fn(input_data) -> output_data
    """

    def __init__(
        self,
        agent_id: str,
        name: str = "",
        capability: str = "",
        input_schema: Dict[str, str] = None,
        output_schema: Dict[str, str] = None,
        handler: Callable = None,
    ):
        super().__init__(agent_id, name, role="worker")
        self.capability = capability
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}
        self._handler = handler or self._default_handler

    def process(self, message: Message) -> Optional[Message]:
        """处理收到的子任务"""
        if message.type != MessageType.ASK:
            return None

        # 从消息中提取任务数据
        task_data = message.metadata.get("task", {})
        task_id = task_data.get("id", "unknown")
        input_data = task_data.get("input_data", {})

        start = time.time()

        try:
            # 执行任务
            output_data = self._handler(input_data, task_data)
            duration = time.time() - start

            result = TaskResult(
                task_id=task_id,
                worker_id=self.agent_id,
                output_data=output_data,
                status=TaskStatus.DONE,
                duration=duration,
            )

            # 验证输出格式
            if self.output_schema and not result.is_valid(self.output_schema):
                result.status = TaskStatus.ERROR
                result.error = f"输出不符合 schema: {self.output_schema}"

        except Exception as e:
            duration = time.time() - start
            result = TaskResult(
                task_id=task_id,
                worker_id=self.agent_id,
                status=TaskStatus.ERROR,
                error=str(e),
                duration=duration,
            )

        return self.reply(
            to_agent=message.from_agent,
            answer=f"[{self.name}] 完成任务: {task_data.get('description', task_id)}",
            metadata={"result": result},
        )

    @staticmethod
    def _default_handler(input_data: Dict, task_data: Dict) -> Dict:
        """默认处理：原样返回输入"""
        return {"received": input_data, "worker_note": f"任务完成"}

    def __repr__(self):
        return f"<Worker {self.agent_id}: {self.name} ({self.capability[:30]})>"


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent — 任务分解 + 分发 + 汇总。

    工作流：
    1. receive_request(user_input) → decompose → List[SubTask]
    2. 分发 subtask 给对应 Worker
    3. 等待所有 Worker 返回
    4. aggregate(results) → 汇总输出
    """

    def __init__(
        self,
        agent_id: str = "orchestrator",
        name: str = "Orchestrator",
        decompose_fn: Callable = None,
        aggregate_fn: Callable = None,
    ):
        super().__init__(agent_id, name, role="orchestrator")
        self._decompose_fn = decompose_fn or self._default_decompose
        self._aggregate_fn = aggregate_fn or self._default_aggregate
        self._pending_results: Dict[str, TaskResult] = {}

    # ========== 核心流程 ==========

    def execute(
        self,
        user_input: str,
        workers: List[WorkerAgent],
        bus: MessageBus,
    ) -> DecomposeResult:
        """
        完整执行：接收输入 → 分解 → 分发 → 收集 → 汇总

        Args:
            user_input: 用户请求
            workers: Worker Agent 列表
            bus: 消息总线

        Returns:
            DecomposeResult 包含完整的执行记录
        """
        overall_start = time.time()

        # 注册所有 Worker
        for w in workers:
            bus.register(w)
        bus.register(self)

        print(f"\n{'=' * 55}")
        print(f"  [Orchestrator] 收到任务: {user_input[:60]}...")
        print(f"  [Orchestrator] 可用 Worker: {len(workers)} 个")

        # 1. 分解
        subtasks = self._decompose_fn(user_input, workers)
        print(f"  [Orchestrator] 分解为 {len(subtasks)} 个子任务:")
        for st in subtasks:
            print(f"    - {st.id}: {st.description[:50]} → {st.assigned_worker}")

        # 2. 分发并执行
        for st in subtasks:
            st.status = TaskStatus.RUNNING
            worker = next((w for w in workers if w.agent_id == st.assigned_worker), None)
            if not worker:
                st.status = TaskStatus.ERROR
                continue

            # 构建任务消息
            task_msg = Message(
                from_agent=self.agent_id,
                to_agent=st.assigned_worker,
                type=MessageType.ASK,
                content=f"请执行: {st.description}",
                metadata={
                    "task": {
                        "id": st.id,
                        "description": st.description,
                        "input_data": st.input_data,
                        "input_schema": st.input_schema,
                    }
                },
            )
            bus.route(task_msg)
            print(f"  [Orchestrator] 分发 {st.id} → {st.assigned_worker}")

            # 立刻让 Worker 处理并回传结果
            reply = worker.process(task_msg)
            if reply:
                reply.from_agent = worker.agent_id
                bus.route(reply)

        # 3. 收集结果
        results = self._collect_results(subtasks)

        # 4. 汇总
        aggregated = self._aggregate_fn(user_input, subtasks, results)

        total_duration = time.time() - overall_start
        success = sum(1 for r in results if r.status == TaskStatus.DONE)
        errors = sum(1 for r in results if r.status == TaskStatus.ERROR)

        print(f"  [Orchestrator] 完成: {success}/{len(subtasks)} 成功, {errors} 失败 ({total_duration:.2f}s)")
        print(f"{'=' * 55}\n")

        return DecomposeResult(
            user_input=user_input,
            subtasks=subtasks,
            results=results,
            aggregated=aggregated,
            total_duration=total_duration,
            success_count=success,
            error_count=errors,
        )

    def _collect_results(self, subtasks: List[SubTask]) -> List[TaskResult]:
        """从 inbox 收集所有 Worker 的返回结果"""
        results: List[TaskResult] = []
        task_ids = {st.id for st in subtasks}

        # 读 inbox 直到收集齐所有结果
        for _ in range(len(subtasks)):
            msgs = self.read_all()
            for msg in msgs:
                result_data = msg.metadata.get("result")
                if result_data is None:
                    continue
                # result_data 可能是 TaskResult 实例或 dict
                if isinstance(result_data, TaskResult):
                    tr = result_data
                elif isinstance(result_data, dict):
                    tr = TaskResult(**result_data)
                else:
                    continue
                if tr.task_id in task_ids:
                    results.append(tr)
                    task_ids.discard(tr.task_id)

        return results

    def process(self, message: Message) -> Optional[Message]:
        """收到 Worker 回复时记录结果"""
        return None  # Orchestrator 不主动回复，通过 _collect_results 批量处理

    # ========== 默认分解/汇总（可替换） ==========

    @staticmethod
    def _default_decompose(user_input: str, workers: List[WorkerAgent]) -> List[SubTask]:
        """默认分解：按 Worker 数量平均拆分，每个 Worker 一个子任务"""
        n = len(workers)
        parts = user_input.split("，") if "，" in user_input else [user_input]

        # 确保至少有 n 个子任务
        while len(parts) < n:
            parts.append(parts[-1] if parts else user_input)

        subtasks = []
        for i, worker in enumerate(workers):
            subtasks.append(SubTask(
                description=f"处理第{i+1}部分: {parts[min(i, len(parts)-1)][:40]}",
                assigned_worker=worker.agent_id,
                input_schema=worker.input_schema,
                input_data={"index": i, "content": parts[min(i, len(parts)-1)], "worker_count": n},
                output_schema=worker.output_schema,
            ))
        return subtasks

    @staticmethod
    def _default_aggregate(user_input: str, subtasks: List[SubTask],
                           results: List[TaskResult]) -> Dict:
        """默认汇总：合并所有 Worker 的 output_data"""
        merged = {}
        for r in results:
            if r.status == TaskStatus.DONE:
                merged[r.worker_id] = r.output_data
            else:
                merged[r.worker_id] = {"error": r.error}
        return {
            "summary": f"处理完成: {sum(1 for r in results if r.status == TaskStatus.DONE)}/{len(results)} 个子任务成功",
            "details": merged,
        }
