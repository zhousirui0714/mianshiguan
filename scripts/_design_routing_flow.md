# Position Routing Runtime Flow — 架构设计

> 纯设计文档，不涉及代码实现。

---

## 1. 数据流图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Position Routing Flow                        │
└─────────────────────────────────────────────────────────────────────┘

  用户选择岗位
       │
       ▼
┌──────────────────┐
│  1. Session Init │  ← 加载权重表、初始化预算
│     TopicRouter  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────┐
│  2. Topic Router  │────▶│  权重表查询      │
│     get_next()    │     │  Position→Topic  │
└────────┬─────────┘     │  剩余预算递减     │
         │               └─────────────────┘
         ▼
┌──────────────────┐     ┌─────────────────┐
│  3. Stage Filter  │────▶│  当前阶段匹配    │
│                    │     │  intro/project/  │
│                    │     │  basic/advanced/ │
│                    │     │  system_design/  │
│                    │     │  behavior        │
└────────┬─────────┘     └─────────────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────┐
│  4. Level Filter  │────▶│  S级优先         │
│                    │     │  → A级          │
│                    │     │  → B级          │
│                    │     │  → C级          │
└────────┬─────────┘     └─────────────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────┐
│  5. Final Select  │────▶│  去重检查        │
│     pick_one()    │     │  + 随机扰动      │
└────────┬─────────┘     └─────────────────┘
         │
         ▼
    ┌─────────┐
    │  出题    │
    └─────────┘


  用户回答
       │
       ▼
┌──────────────────┐
│  6. Post-Answer   │  ← Project Keyword Detection
│     Feedback      │  ← 预算调整（可选）
└────────┬─────────┘
         │
         ▼
    ┌─────────┐
    │  下一轮   │ ──▶ 回到 Step 2
    └─────────┘
```

---

## 2. Session 新增字段

```python
session.context = {
    # === 已有字段 ===
    "position": "AI工程师",          # 用户选择岗位
    "current_stage": "intro",        # 当前面试阶段
    "stage_rounds": {"intro": 1},    # 每阶段轮次计数
    "retrieved_questions": [...],    # 预加载的题目列表
    "used_questions": [...],         # 已使用的题目
    "project_keywords_detected": [], # 检测到的项目关键词

    # === 新增字段 ===
    # 1. 权重预算
    "topic_budget": {                 # 每轮出题后递减
        "LLM/大模型": 30,            # ← 初始值=权重
        "Agent": 20,
        "RAG": 15,
        "模型训练/对齐": 15,
        "系统设计": 10,
        "数据结构与算法": 5,
        "项目经验": 5,
        "通用": 5,                   # 兜底预算
    },

    # 2. 轮次统计
    "topic_served": {                 # 每轮记录实际出题的 topic
        "LLM/大模型": 5,             # 已出 5 题
        "Agent": 3,
        "RAG": 2,
        ...
    },

    # 3. 路由状态
    "current_topic": "LLM/大模型",    # 当前轮选中的 topic
    "topic_fallback_count": 0,        # 连续降级次数（用于触发 LLM 兜底）

    # 4. 权重覆盖（keyword 触发时的临时调整）
    "weight_overrides": {             # 临时提升某些 topic 权重
        "项目经验": +20,              # 检测到 project keyword 时触发
    },
}
```

### 初始化流程

```
用户选择 "AI工程师"
    │
    ▼
加载 weight_table["AI工程师"]
    │
    ▼
topic_budget = weight_table 的副本（深拷贝）
topic_served = {} (全 0)
current_topic = null
topic_fallback_count = 0
weight_overrides = {}
```

---

## 3. Router 接口设计

```
┌─────────────────────────────────────────┐
│            TopicRouter                   │
├─────────────────────────────────────────┤
│  + get_next_topic(session) → str        │
│  + select_question(session) → Question  │
│  + record_answer(session, topic) → void │
│  + adjust_weight(session, delta) → void │
│  + get_budget_remaining(session) → dict │
└─────────────────────────────────────────┘
```

### 3.1 `get_next_topic(session) → topic_name`

选择下一个 topic 的核心逻辑：

```
输入: session.context
输出: topic_name

算法:
1. 检查 weight_overrides
   - 如果有临时权重提升（如项目经验 +20）
   - 将对应 topic 的剩余预算提升
   - 清除 weight_overrides（一次性）

2. 计算所有 topic 的 "选择优先级"
   score(t) = topic_budget[t] / sum(all_budgets) * 100
            + bonus(t)            # 同 level 随机扰动
            - penalty(t)           # 连续多轮未选到，降低

3. 选择 score 最高的 topic
   - 如果 max(score) == 0 → 所有预算耗尽
   - 返回 None 触发 Fallback

4. 如果选中的 topic 在数据库中已无未用题目
   - 该 topic 预算置 0
   - 重新选择（goto step 2）

5. 返回 topic_name
```

### 3.2 `select_question(session) → Question`

```
输入: session
输出: 选中的题目文本 | None

算法:
topic = get_next_topic(session)
if topic is None:
    return fallback_select(session)

# Stage Filter
stage = session.context["current_stage"]
stage_candidates = [
    q for q in retrieved_questions
    if q.topics contains topic
    and q.interview_stage == stage
    and q.text not in used_questions
]

# Level Filter: 优先 S → A → B → C
for level in ["S", "A", "B", "C"]:
    level_matched = [q for q in stage_candidates if q.level == level]
    if level_matched:
        # 同 level 内随机选一个（避免连续性）
        selected = random.choice(level_matched)
        # 扣减预算
        topic_budget[topic] -= 1
        topic_served[topic] += 1
        return selected.text

# 如果当前 stage 无匹配 → 降级：同 topic 任意 stage
stage_candidates = [
    q for q in retrieved_questions
    if q.topics contains topic
    and q.text not in used_questions
]
for level in ["S", "A", "B", "C"]:
    level_matched = [q for q in stage_candidates if q.level == level]
    if level_matched:
        selected = random.choice(level_matched)
        topic_budget[topic] -= 1
        return selected.text

# 如果该 topic 完全无可用题目 → topic 预算置 0，重新选 topic
topic_budget[topic] = 0
return select_question(session)  # 递归重试
```

---

## 4. Fallback 策略

### 4.1 Topic 级别 Fallback（4 级降级）

```
Level 0: 正常路由
  按权重选中 topic → stage 过滤 → level 过滤 → 出题

Level 1: 当前 topic 在当前 stage 无题
  → 同 topic，任意 stage 找题

Level 2: 当前 topic 完全无题
  → 该 topic 预算置 0，重新选下一个高权重 topic

Level 3: 所有 topic 均无可用题
  → 忽略 topic，按 interview_stage 从全库选未用题
  → callback: _select_next_bank_question(session) 现有逻辑

Level 4: 题库完全用完
  → LLM 自由生成
  → callback: _llm_generate_free(session, history)
```

### 4.2 Stage Fallback

```
当前 stage 在该 topic 下无题
    │
    ▼
依次尝试降级 stage：
1. 同 topic + 任意 stage
2. 同 topic + 降级 stage（例如 basic 题在 advanced 轮使用）
3. 任意 topic + 任意 stage（无视阶段）
```

### 4.3 Keyword 触发的权重提升

```
用户回答中包含 project keyword（Redis/MySQL/Kafka/RAG/Agent）
    │
    ▼
1. topic_budget["项目经验"] += 20（临时提升）
2. current_stage = "project"（强制切换到 project 阶段）
3. weight_overrides["项目经验"] = +20
4. 下一轮 get_next_topic() 优先选中项目经验
```

---

## 5. 去重策略

### 5.1 三层次去重

```
┌─────────────────────────────────────────┐
│            Dedup Strategy                │
├─────────────────────────────────────────┤
│  Level 1: 文本层去重                      │
│    used_questions = Set[question_text]    │
│    ≥ 10 字完全匹配即判重                  │
├─────────────────────────────────────────┤
│  Level 2: 语义层去重（可选）               │
│    同一 topic 在同一 stage 内              │
│    不连续出相同知识点的问题                 │
│    例如：不出两道 Redis 持久化题            │
├─────────────────────────────────────────┤
│  Level 3: 轮次去重                         │
│    同一 topic 不连续出 2 次                │
│    如果上次是 MySQL，这次优先选其他 topic    │
│    当 budget 充足时，轮询各 topic           │
└─────────────────────────────────────────┘
```

### 5.2 权重预算与去重的互动

```
正面例子:
  Python后端 第 5 轮
    budget: MySQL=15, Redis=12, 系统设计=16, ...
    上次 topic = MySQL
    → 算 score 时 MySQL 加 penalty
    → 本轮选 Redis（权重第二高且未连续）
    → 出 Redis 持久化题（S 级）
    → budget["Redis"] -= 1

预算耗尽场景:
  第 20 轮，所有 topic budget 接近 0
    → 无视 topic，按 stage 出题
    → 如果 stage 也无题 → LLM 自由生成
```

---

## 6. 完整一轮的数据流

```
┌────────────────────────────────────────────────────┐
│                  One Interview Round                 │
├────────────────────────────────────────────────────┤
│                                                     │
│  1. 用户回答上一题                                     │
│     ├─ 评分（已有逻辑）                                │
│     └─ Project Keyword Detection                     │
│         └─ 如果命中 → weight_overrides + stage 切换    │
│                                                     │
│  2. round += 1                                       │
│                                                     │
│  3. 确定 current_stage（_determine_next_stage）        │
│     ├─ 默认：按轮次映射                                │
│     └─ 覆盖：weight_overrides 中的 project keyword    │
│                                                     │
│  4. TopicRouter.get_next_topic(session)               │
│     ├─ 读 topic_budget                               │
│     ├─ 算权重 score                                  │
│     ├─ 应用 overrides                                │
│     └─ 返回 topic_name                                │
│                                                     │
│  5. TopicRouter.select_question(session)              │
│     ├─ Stage Filter（current_stage ∩ topic）          │
│     ├─ Level Filter（S → A → B → C）                 │
│     ├─ Dedup Check（used_questions 过滤）              │
│     ├─ Fallback（4 级降级）                            │
│     └─ 返回 question_text                             │
│                                                     │
│  6. 记录状态                                          │
│     ├─ topic_served[topic] += 1                      │
│     ├─ topic_budget[topic] -= 1                      │
│     └─ used_questions.add(question_text)              │
│                                                     │
│  7. 组合 LLM 评价 + 出题，返回给用户                    │
│                                                     │
└────────────────────────────────────────────────────┘
```

---

## 7. 边界情况处理

| 场景 | 处理方式 |
|------|----------|
| 用户连续答对 S 级题 | 正常出题，不调整权重（避免正反馈循环） |
| 用户连续答错 C 级题 | 正常出题，不降级（面试系统不因表现改变出题） |
| 某 topic 题已用完但 budget 未耗尽 | 该 topic 预算置 0，剩余预算重分配给其他 topic |
| 所有 topic 题用完 | 第 4 级 Fallback：LLM 自由生成 |
| keyword 连续触发（每轮都说 Redis） | weight_overrides 一次性消耗，不累积 |
| 权重 5% 的 topic 无 S 级题 | 自动降级到 A 级，该 topic 不受影响 |
| 岗位切换（面试中改变 position） | 重新初始化 topic_budget，保留 used_questions |
