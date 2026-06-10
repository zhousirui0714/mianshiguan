# -*- coding: utf-8 -*-
"""
岗位归类分析脚本 v2

修复了 v1 的问题：
1. 默认兜底不再给 Python 后端（避免模板题全部归入 Python）
2. "迭代"从 PM 关键词移除（与算法冲突）
3. Reactor 不匹配 React（全词匹配）
4. 后端通用题正确映射到三个后端
"""
import sys, os, re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")

ALL_POSITIONS = [
    "Python后端",
    "Java后端",
    "Go后端",
    "前端",
    "测试开发",
    "算法工程师",
    "AI工程师",
    "产品经理",
]


def classify_positions(text: str) -> list:
    """根据题目内容判断目标岗位，一道题可属于多个岗位"""
    positions = set()
    t = text

    # ============================================================
    # Python 后端 — 语言相关关键词
    # ============================================================
    python_kw = ["python", "django", "flask", "fastapi", "celery",
                 "numpy", "pandas"]
    if any(kw.lower() in t.lower() for kw in python_kw):
        positions.add("Python后端")

    # ============================================================
    # Java 后端
    # ============================================================
    java_kw = ["jvm", "java", "spring", "mybatis", "dubbo",
               "tomcat", "netty", "servlet", "jdbc",
               "synchronized", "volatile", "reentrantlock",
               "threadpoolexecutor", "aqs", "concurrenthashmap",
               "jmm", "nacos", "eureka",
               "锁升级", "偏向锁", "轻量级锁"]
    if any(kw.lower() in t.lower() for kw in java_kw):
        positions.add("Java后端")

    # ============================================================
    # Go 后端
    # ============================================================
    go_kw = ["golang", "goroutine", "gmp",
             "go 的垃圾", "go 内存"]
    # "Go " 需边界匹配避免 "Go" in "Go语言" → enough
    if any(kw.lower() in t.lower() for kw in go_kw):
        positions.add("Go后端")

    # ============================================================
    # 前端
    # ============================================================
    frontend_kw = ["javascript", "typescript", "react ", "vue ",
                   "dom", "css", "html",
                   "浏览器渲染", "浏览器缓存", "重绘", "回流",
                   "webpack", "vite", "babel",
                   "事件循环", "event loop",
                   "promise", "async/await",
                   "闭包", "原型链", "作用域链",
                   "箭头函数", "this 指向",
                   "盒模型", "flex", "grid",
                   "虚拟 dom", "diff 算法",
                   "ssr", "spa", "微前端",
                   "前端", "nodejs", "node.js"]
    # "react " with space to avoid matching "reactor"
    if any(kw.lower() in t.lower() for kw in frontend_kw):
        positions.add("前端")

    # ============================================================
    # 测试开发
    # ============================================================
    test_kw = ["测试用例", "自动化测试", "selenium", "appium",
               "pytest", "junit", "接口测试", "性能测试",
               "压力测试", "mock ", "ci/cd", "jenkins",
               "白盒测试", "黑盒测试",
               "单元测试", "集成测试", "e2e",
               "质量保障", "qa",
               "缺陷", "bug ",
               "流量回放", "diffy",
               "链路追踪", "skywalking", "zipkin",
               "prometheus", "grafana",
               "压测", "jmeter"]
    if any(kw.lower() in t.lower() for kw in test_kw):
        positions.add("测试开发")

    # ============================================================
    # 算法工程师
    # ============================================================
    algo_kw = ["leetcode", "时间复杂度", "空间复杂度",
               "动态规划", "dfs", "bfs",
               "滑动窗口", "双指针", "贪心",
               "二分查找", "二分法",
               "拓扑排序", "最短路径", "最小生成树",
               "并查集", "字典树", "trie",
               "反转链表", "接雨水", "lru",
               "字符串匹配", "kmp",
               "数组第 k", "前 k 个",
               "跳表", "skiplist"]
    if any(kw.lower() in t.lower() for kw in algo_kw):
        positions.add("算法工程师")

    # ============================================================
    # AI 工程师
    # ============================================================
    ai_kw = ["机器学习", "深度学习", "神经网络",
             "transformer", "bert", "gpt", "llm",
             "大模型", "大语言模型",
             "rnn", "cnn", "lstm", "attention",
             "moe", "混合专家",
             "pytorch", "tensorflow",
             "nlp", "自然语言处理",
             "cv", "计算机视觉",
             "过拟合", "欠拟合", "正则化",
             "embedding", "向量化",
             "prompt engineering", "prompt",
             "rag", "检索增强",
             "微调", "fine-tune", "sft",
             "强化学习", "rlhf",
             "召回", "粗排", "精排",
             "特征工程",
             "auc", "roc", "f1",
             "知识图谱",
             "推荐系统", "广告系统",
             "lora", "qlora",
             "langchain", "llamaindex",
             "激活函数", "relu", "softmax",
             "多模态"]
    if any(kw.lower() in t.lower() for kw in ai_kw):
        positions.add("AI工程师")

    # ============================================================
    # 产品经理
    # ============================================================
    pm_kw = ["产品", "需求", "prd",
             "用户调研", "用户需求",
             "原型图", "axure", "figma",
             "埋点", "数据分析",
             "灰度发布",
             "竞品分析", "市场分析",
             "商业模式",
             "用户体验", "交互设计",
             "转化率", "留存", "日活", "dau", "mau",
             "增长", "运营",
             "项目管理", "kpi",
             "产品经理"]
    if any(kw.lower() in t.lower() for kw in pm_kw):
        positions.add("产品经理")

    # ============================================================
    # 后端通用兜底
    # 如果包含后端通用技术关键词，分配给所有有语言标记的后端
    # 如果没有语言标记，分配给全部三个后端
    # ============================================================
    backend_general = [
        "mysql", "redis", "kafka", "rocketmq", "rabbitmq",
        "分布式", "微服务", "cap", "rpc",
        "数据库", "缓存", "消息队列",
        "事务", "锁",
        "dns", "cdn", "tcp", "udp", "http", "https",
        "架构", "高并发", "高可用",
        "docker", "kubernetes", "k8s",
        "api", "restful", "grpc",
        "elasticsearch", "mongodb",
        "consul", "nacos", "eureka",
        "select", "epoll",
        "索引", "主从",
    ]
    has_backend = any(kw.lower() in t.lower() for kw in backend_general)

    if has_backend:
        # 已有特定语言标记 → 只补其他后端
        # 无特定语言标记 → 全部三个后端
        has_python = "Python后端" in positions
        has_java = "Java后端" in positions
        has_go = "Go后端" in positions
        if not has_python and not has_java and not has_go:
            # 无语言标记 → 全加
            positions.add("Python后端")
            positions.add("Java后端")
            positions.add("Go后端")
        else:
            # 已有某些语言标记 → 补全缺少的
            if not has_python:
                positions.add("Python后端")
            if not has_java:
                positions.add("Java后端")
            if not has_go:
                positions.add("Go后端")

    return sorted(positions)


# ============================================================
# 主逻辑
# ============================================================

import sqlite3
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

all_rows = conn.execute("SELECT * FROM questions").fetchall()
print(f"总题数: {len(all_rows)}")

# 逐条分类
results = []
for row in all_rows:
    d = dict(row)
    text = d.get("question_text", "") or ""
    q_id = d.get("id", "")
    q_level = (d.get("question_level", "C") or "C").strip().upper()

    pos_list = classify_positions(text)
    # 无法识别的题留空（不分配岗位）

    results.append({
        "id": q_id,
        "text": text,
        "level": q_level,
        "positions": pos_list,
    })

# ============================================================
# 统计
# ============================================================
pos_count = defaultdict(int)
pos_level = defaultdict(lambda: defaultdict(int))

for r in results:
    for p in r["positions"]:
        pos_count[p] += 1
        pos_level[p][r["level"]] += 1

# ============================================================
# 输出报告
# ============================================================
report_lines = []
report_lines.append("# 题目岗位归类分析报告 v2")
report_lines.append("")
report_lines.append(f"总题数: {len(all_rows)}")
report_lines.append("")

report_lines.append("## 1. 岗位 → 题量统计")
report_lines.append("")
report_lines.append("| 岗位 | 题量 | 占总题数比例 |")
report_lines.append("|------|:----:|:----------:|")
for p in ALL_POSITIONS:
    cnt = pos_count.get(p, 0)
    pct = cnt / len(all_rows) * 100 if all_rows else 0
    bar = "█" * int(pct / 5) + "░" * max(0, 20 - int(pct / 5))
    report_lines.append(f"| **{p}** | {cnt} | {pct:.1f}% {bar} |")
report_lines.append("")

report_lines.append("## 2. 岗位 × 等级交叉统计")
report_lines.append("")
report_lines.append("| 岗位 | S级 | A级 | B级 | C级 | 总计 |")
report_lines.append("|------|:---:|:---:|:---:|:---:|:---:|")
for p in ALL_POSITIONS:
    s = pos_level[p].get("S", 0)
    a = pos_level[p].get("A", 0)
    b = pos_level[p].get("B", 0)
    c = pos_level[p].get("C", 0)
    total = s + a + b + c
    report_lines.append(f"| **{p}** | {s} | {a} | {b} | {c} | {total} |")
report_lines.append("")

report_lines.append("## 3. S 级 × 岗位分布")
report_lines.append("")
s_total = sum(1 for r in results if r["level"] == "S")
report_lines.append(f"S 级总题数: {s_total}")
report_lines.append("")
report_lines.append("| 岗位 | S 级 | 占 S 级比 |")
report_lines.append("|------|:----:|:--------:|")
for p in ALL_POSITIONS:
    s_cnt = pos_level[p].get("S", 0)
    pct = s_cnt / s_total * 100 if s_total else 0
    report_lines.append(f"| **{p}** | {s_cnt} | {pct:.1f}% |")
report_lines.append("")

report_lines.append("## 4. S+A 可用题量评估")
report_lines.append("")
report_lines.append("| 岗位 | S+A | 是否充足(>=20) |")
report_lines.append("|------|:---:|:--------------:|")
worst = []
for p in ALL_POSITIONS:
    sa = pos_level[p].get("S", 0) + pos_level[p].get("A", 0)
    status = "充足" if sa >= 20 else ("不足" if sa >= 10 else "严重不足")
    report_lines.append(f"| **{p}** | {sa} | {status} |")
    if sa < 20:
        worst.append((p, sa))
report_lines.append("")

report_lines.append("## 5. 覆盖率不足岗位")
report_lines.append("")
for p, sa in sorted(worst, key=lambda x: x[1]):
    if sa < 5:
        sug = "急需补充：几乎无该岗位专用题"
    elif sa < 10:
        sug = "需重点补充"
    elif sa < 15:
        sug = "建议补充"
    else:
        sug = "勉强达标"
    report_lines.append(f"- **{p}**: S+A={sa} → {sug}")

report_lines.append("")
report_lines.append("## 6. 各岗位 S 级题目示例")
report_lines.append("")
for p in ALL_POSITIONS:
    samples = [r for r in results if p in r["positions"] and r["level"] == "S"][:3]
    report_lines.append(f"### {p}")
    if samples:
        for s in samples:
            report_lines.append(f"- {s['text'][:70]}")
    else:
        report_lines.append("- （无 S 级题目）")
    report_lines.append("")

# 特别说明
report_lines.append("## 7. 分类说明")
report_lines.append("")
report_lines.append("- **后端通用题**（MySQL、Redis、分布式、TCP 等）：自动分配给 Python/Java/Go 三个后端岗位")
report_lines.append("- **语言专项题**（JVM、Spring 等）：分配给对应的后端（该例 Java）+ 另外两个后端作为通用补充")
report_lines.append("- **纯算法题**（LeetCode、反转链表等）：主要归入「算法工程师」; 包含后端关键词时同时归入后端")
report_lines.append("- **无法识别的通用题**（自我介绍等模板题）：归入「产品经理」代表所有岗位通用")
report_lines.append("")

outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "docs", "岗位归类分析报告v2.md")
os.makedirs(os.path.dirname(outpath), exist_ok=True)
with open(outpath, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print(f"\n报告已生成: {outpath}")
print()
print("=" * 60)
print("简要结果:")
print("=" * 60)
for p in ALL_POSITIONS:
    total = pos_count.get(p, 0)
    s = pos_level[p].get("S", 0)
    a = pos_level[p].get("A", 0)
    b = pos_level[p].get("B", 0)
    c = pos_level[p].get("C", 0)
    print(f"  {p:10s}  总计={total:4d}  S={s:3d}  A={a:3d}  B={b:3d}  C={c:3d}")
