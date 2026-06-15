"""
多 Agent 通信框架 — 可运行演示

演示内容：
1. 3 个 Agent 的圆桌讨论
2. 2 个 Agent 的辩论
3. Agent 之间的任务交接

运行方式：
    cd mianshiguan
    python -m src.agents.multi_agent.demo
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.agents.multi_agent.message import Message, MessageType
from src.agents.multi_agent.agent import BaseAgent
from src.agents.multi_agent.bus import MessageBus
from src.agents.multi_agent.patterns import round_table, debate, handoff


# ==================== 示例 Agent ====================

class EchoAgent(BaseAgent):
    """回显 Agent — 收到什么就回什么"""

    def process(self, message: Message):
        msg_type = message.type
        sender = message.from_agent

        if msg_type == MessageType.ASK:
            return self.reply(
                to_agent=sender,
                answer=f"收到你的问题：「{message.content[:50]}」，我的回答是：这是对问题的回应。",
            )
        elif msg_type == MessageType.HANDOFF:
            return self.reply(
                to_agent=sender,
                answer=f"已接收任务：「{message.content[:50]}」，{self.name} 开始处理。",
            )
        else:
            return self.send(
                to_agent="",
                content=f"[{self.name}] 收到来自 {sender} 的消息：{message.content[:50]}",
                msg_type=MessageType.SPEAK,
            )


class ThinkAgent(BaseAgent):
    """思考型 Agent — 收到消息后输出自己的思考"""

    def __init__(self, agent_id: str, name: str = "", role: str = "",
                 perspective: str = ""):
        super().__init__(agent_id, name, role)
        self.perspective = perspective or f"我是{name}，我从自己的角度分析问题"

    def process(self, message: Message):
        prefix = self.perspective

        if message.type == MessageType.ASK:
            return self.reply(
                to_agent=message.from_agent,
                answer=f"[{self.name}] {prefix}。针对「{message.content[:60]}」，我认为关键在于把握好核心要点，从实际出发给出解决方案。",
            )
        elif message.type == MessageType.SPEAK:
            # 听到别人发言，发表自己的看法
            return self.send(
                to_agent="",
                content=f"[{self.name}] 听到了 {message.from_agent} 的发言，{prefix}。我的补充是：这个观点值得深入探讨。",
                msg_type=MessageType.SPEAK,
            )
        else:
            return self.reply(
                to_agent=message.from_agent,
                answer=f"[{self.name}] 收到。{prefix}。",
            )


# ==================== 演示 ====================

def demo_round_table():
    """演示1：圆桌讨论"""
    print("\n" + "=" * 60)
    print("  演示 1：圆桌讨论 — 3 位 Agent 轮流发言")
    print("=" * 60)

    bus = MessageBus(verbose=True)

    agents = [
        ThinkAgent("agent_1", "Alice", "架构师", "作为架构师，我关注系统的整体设计和可扩展性"),
        ThinkAgent("agent_2", "Bob", "开发者", "作为开发者，我关注代码实现和工程实践"),
        ThinkAgent("agent_3", "Carol", "测试工程师", "作为测试工程师，我关注质量和边界条件"),
    ]

    messages = round_table(
        agents=agents,
        bus=bus,
        topic="如何设计一个高可用的用户认证系统？",
        rounds=2,
        delay=0.3,
    )

    print(f"\n[结果] 圆桌讨论完成，共 {len(messages)} 条发言")
    print(f"[Bus] {bus.summary()}")


def demo_debate():
    """演示2：辩论"""
    print("\n" + "=" * 60)
    print("  演示 2：辩论 — 正反方 3 轮交锋")
    print("=" * 60)

    bus = MessageBus(verbose=True)

    pro = ThinkAgent("pro", "正方", "乐观派", "我认为 AI 将大幅提升人类工作效率，创造更多机会")
    con = ThinkAgent("con", "反方", "审慎派", "我认为 AI 带来的风险不容忽视，需要严格监管")

    messages = debate(
        pro_agent=pro,
        con_agent=con,
        bus=bus,
        topic="AI 是否会取代大部分人类工作？",
        rounds=2,
        delay=0.3,
    )

    print(f"\n[结果] 辩论完成，共 {len(messages)} 条发言")
    print(f"[Bus] {bus.summary()}")


def demo_handoff():
    """演示3：任务交接"""
    print("\n" + "=" * 60)
    print("  演示 3：任务交接 — Agent A → Agent B")
    print("=" * 60)

    bus = MessageBus(verbose=True)

    manager = ThinkAgent("mgr", "Manager", "管理者", "我负责分配任务")
    worker = EchoAgent("worker", "Worker", "执行者")

    messages = handoff(
        from_agent=manager,
        to_agent=worker,
        bus=bus,
        task="请完成用户模块的代码审查，重点检查认证逻辑的安全性。",
    )

    print(f"\n[结果] 任务交接完成，共 {len(messages)} 条消息")
    print(f"[Bus] {bus.summary()}")


def demo_task_decompose():
    """演示4：任务分解 — Orchestrator 分解 → 3个Worker执行 → 汇总"""
    print("\n" + "=" * 60)
    print("  演示 4：Orchestrator 任务分解 → Worker 执行 → 汇总")
    print("=" * 60)

    from src.agents.multi_agent.workers import WorkerAgent, OrchestratorAgent

    bus = MessageBus(verbose=True)

    # 定义 3 个 Worker，每个有明确的输入/输出 schema
    worker1 = WorkerAgent(
        agent_id="w1",
        name="文本分析器",
        capability="提取关键信息和主题",
        input_schema={"content": "str", "index": "int"},
        output_schema={"topics": "list", "sentiment": "str", "key_phrases": "list"},
        handler=lambda data, task: {
            "topics": ["用户认证", "安全性", "会话管理"],
            "sentiment": "正面",
            "key_phrases": [data.get("content", "")[:30]],
        },
    )

    worker2 = WorkerAgent(
        agent_id="w2",
        name="代码审查员",
        capability="分析技术和实现细节",
        input_schema={"content": "str", "index": "int"},
        output_schema={"tech_stack": "list", "risks": "list", "score": "int"},
        handler=lambda data, task: {
            "tech_stack": ["Python", "JWT", "Redis"],
            "risks": ["token过期未处理", "密码未加盐"],
            "score": 75,
        },
    )

    worker3 = WorkerAgent(
        agent_id="w3",
        name="合规检查员",
        capability="检查是否符合规范标准",
        input_schema={"content": "str", "index": "int"},
        output_schema={"compliant": "str", "issues": "list", "recommendations": "list"},
        handler=lambda data, task: {
            "compliant": "部分合规",
            "issues": ["缺少二次验证", "密码策略过弱"],
            "recommendations": ["建议启用MFA", "密码最小长度12位"],
        },
    )

    # 创建 Orchestrator
    orchestrator = OrchestratorAgent(
        agent_id="orch",
        name="Orchestrator",
    )

    # 执行：用户输入 → 分解 → 分发 → 汇总
    result = orchestrator.execute(
        user_input="审查用户登录系统的安全性，检查认证流程、密码策略、会话管理",
        workers=[worker1, worker2, worker3],
        bus=bus,
    )

    print(f"[结果] 任务分解完成！")
    print(f"  子任务数: {len(result.subtasks)}")
    print(f"  成功: {result.success_count}, 失败: {result.error_count}")
    print(f"  总耗时: {result.total_duration:.3f}s")
    print(f"  汇总结果:")
    for worker_id, output in result.aggregated.get("details", {}).items():
        print(f"    [{worker_id}]: {list(output.keys()) if isinstance(output, dict) else output}")


def demo_full():
    """完整演示"""
    print("\n" + "=" * 60)
    print("  多 Agent 通信骨架 — 完整演示")
    print("=" * 60)

    demo_round_table()
    demo_debate()
    demo_handoff()
    demo_task_decompose()

    print("\n" + "=" * 60)
    print("  全部演示完成！")
    print("  ")
    print("  框架能力总结：")
    print("  [OK] Agent 之间通过 MessageBus 自由通信")
    print("  [OK] 支持点对点消息、广播消息")
    print("  [OK] 支持 ASK / REPLY / SPEAK / HANDOFF 消息类型")
    print("  [OK] 开箱即用的协作模式：圆桌讨论、辩论、任务交接")
    print("  [OK] Orchestrator 任务分解 + Worker 执行 + 结果汇总")
    print("  [OK] 每个 Worker 有明确的 input_schema / output_schema")
    print("  [OK] 只需实现 BaseAgent.process() 即可创建新 Agent")
    print("=" * 60)


if __name__ == "__main__":
    demo_full()
