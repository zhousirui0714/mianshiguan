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


def demo_full():
    """完整演示"""
    print("\n" + "=" * 60)
    print("  多 Agent 通信骨架 — 完整演示")
    print("=" * 60)

    demo_round_table()
    demo_debate()
    demo_handoff()

    print("\n" + "=" * 60)
    print("  全部演示完成！")
    print("  ")
    print("  框架能力总结：")
    print("  [OK] Agent 之间通过 MessageBus 自由通信")
    print("  [OK] 支持点对点消息、广播消息")
    print("  [OK] 支持 ASK / REPLY / SPEAK / HANDOFF 消息类型")
    print("  [OK] 开箱即用的协作模式：圆桌讨论、辩论、任务交接")
    print("  [OK] 只需实现 BaseAgent.process() 即可创建新 Agent")
    print("=" * 60)


if __name__ == "__main__":
    demo_full()
