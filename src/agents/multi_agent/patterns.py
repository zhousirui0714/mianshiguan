"""
协作模式 — 基于消息总线的多 Agent 协作模式

提供开箱即用的协作范式：
- round_table: 圆桌讨论（每个 Agent 轮流发言）
- debate: 辩论（正反方交替发言）
- handoff: 任务交接（Agent A → Agent B）
"""

import time
from typing import List, Optional, Callable
from src.agents.multi_agent.message import Message, MessageType
from src.agents.multi_agent.agent import BaseAgent
from src.agents.multi_agent.bus import MessageBus


def round_table(
    agents: List[BaseAgent],
    bus: MessageBus,
    topic: str,
    rounds: int = 2,
    process_fn: Callable = None,
    delay: float = 0.0,
) -> List[Message]:
    """
    圆桌讨论 — 每个 Agent 轮流就一个话题发言。

    流程：
    1. 系统广播话题
    2. 每个 Agent 收到消息后调用 process()，返回自己的发言
    3. 发言通过 Bus 广播给所有人
    4. 下一轮 Agent 基于之前的发言继续讨论

    Args:
        agents: 参与讨论的 Agent 列表
        bus: 共享消息总线
        topic: 讨论话题
        rounds: 讨论轮数
        process_fn: 可选，覆盖 Agent.process() 的自定义处理函数
        delay: 每轮间隔（秒），用于演示时展示效果

    Returns:
        所有发言的 Message 列表
    """
    all_messages: List[Message] = []

    # 注册所有 Agent
    for agent in agents:
        bus.register(agent)

    # 广播讨论话题
    bus.broadcast("system", f"【圆桌讨论】话题：{topic}", MessageType.SYSTEM)

    for r in range(rounds):
        round_msgs: List[Message] = []

        for agent in agents:
            # 收集本轮其他 Agent 的发言
            context = "\n".join([
                f"[{m.from_agent}]: {m.content[:100]}"
                for m in round_msgs
            ])

            # 构建消息：上轮发言 + 当前话题
            msg = Message(
                from_agent="system",
                to_agent=agent.agent_id,
                type=MessageType.ASK,
                content=f"第{r+1}轮讨论，话题：{topic}",
                metadata={"round": r + 1, "context": context},
            )

            # Agent 处理
            if process_fn:
                reply = process_fn(agent, msg)
            else:
                reply = agent.process(msg)

            if reply:
                reply.from_agent = agent.agent_id
                reply.to_agent = ""  # 广播
                bus.route(reply)
                round_msgs.append(reply)
                all_messages.append(reply)

            if delay:
                time.sleep(delay)

    return all_messages


def debate(
    pro_agent: BaseAgent,
    con_agent: BaseAgent,
    bus: MessageBus,
    topic: str,
    rounds: int = 3,
    delay: float = 0.0,
) -> List[Message]:
    """
    辩论模式 — 正反方交替发言。

    正方先发言，反方回应，交替进行。

    Returns:
        所有发言的 Message 列表
    """
    bus.register(pro_agent)
    bus.register(con_agent)
    all_msgs: List[Message] = []

    # 发起辩论
    bus.broadcast("system", f"【辩论开始】辩题：{topic}", MessageType.SYSTEM)
    bus.broadcast("system", f"正方：{pro_agent.name} | 反方：{con_agent.name}", MessageType.SYSTEM)

    last_msg: Optional[Message] = None

    for r in range(rounds):
        # 正方发言
        msg = Message(
            from_agent=con_agent.agent_id if last_msg else "system",
            to_agent=pro_agent.agent_id,
            type=MessageType.ASK,
            content=last_msg.content if last_msg else f"请正方就'{topic}'发表观点",
            metadata={"round": r + 1, "side": "pro"},
        )
        pro_reply = pro_agent.process(msg)
        if pro_reply:
            pro_reply.from_agent = pro_agent.agent_id
            bus.route(pro_reply)
            all_msgs.append(pro_reply)

        if delay:
            time.sleep(delay)

        # 反方发言
        msg2 = Message(
            from_agent=pro_agent.agent_id,
            to_agent=con_agent.agent_id,
            type=MessageType.ASK,
            content=pro_reply.content if pro_reply else f"请反方就'{topic}'发表观点",
            metadata={"round": r + 1, "side": "con"},
        )
        con_reply = con_agent.process(msg2)
        if con_reply:
            con_reply.from_agent = con_agent.agent_id
            bus.route(con_reply)
            all_msgs.append(con_reply)
            last_msg = con_reply

        if delay:
            time.sleep(delay)

    bus.broadcast("system", f"【辩论结束】共 {rounds} 轮", MessageType.SYSTEM)
    return all_msgs


def handoff(
    from_agent: BaseAgent,
    to_agent: BaseAgent,
    bus: MessageBus,
    task: str,
) -> List[Message]:
    """
    任务交接 — Agent A 将任务交给 Agent B。

    A 发送 HANDOFF → B 收到后处理 → B 可以回复确认
    """
    bus.register(from_agent)
    bus.register(to_agent)

    all_msgs: List[Message] = []

    # A 交接任务
    msg = from_agent.send(
        to_agent=to_agent.agent_id,
        content=task,
        msg_type=MessageType.HANDOFF,
        metadata={"from_name": from_agent.name},
    )
    all_msgs.append(msg)

    # B 接收并处理
    to_agent.receive(msg)
    reply = to_agent.process(msg)
    if reply:
        reply.from_agent = to_agent.agent_id
        reply.to_agent = from_agent.agent_id
        bus.route(reply)
        all_msgs.append(reply)

    return all_msgs
