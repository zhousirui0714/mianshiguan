# -*- coding: utf-8 -*-
"""
岗位归类分析脚本

对 questions 表中所有题目按内容分类到 target_positions。
生成分析报告，不修改数据库。
"""
import sys, os, json, re
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

# ============================================================
# 岗位判定规则：关键词 → 岗位映射
# ============================================================

def classify_positions(text: str, company: str = "",
                       position_field: str = "",
                       source_type: str = "",
                       question_level: str = "") -> list:
    """
    根据题目内容 + 元数据判断目标岗位。
    一道题可属于多个岗位。
    """
    positions = set()
    t = text.lower()

    # ============================================================
    # Python 后端
    # ============================================================
    python_keywords = [
        "python", "django", "flask", "FastAPI", "celery",
        "python 装饰器", "python 生成器", "python 迭代器",
        "gIL", "全局解释器锁",
        "python 内存管理", "python 垃圾回收",
        "numpy", "pandas", "scipy",
        "asyncio", "协程",
    ]
    if any(kw.lower() in t for kw in python_keywords):
        positions.add("Python后端")

    # ============================================================
    # Java 后端
    # ============================================================
    java_keywords = [
        "java", "jvm", "spring", "mybatis", "dubbo",
        "tomcat", "servlet", "jdbc",
        "synchronized", "volatile", "reentrantlock",
        "threadpoolexecutor", "aqs",
        "concurrenthashmap", "hashmap",
        "jmm", "类加载", "类加载器",
        "gc", "垃圾回收", "垃圾收集",
        "java 内存", "jstack", "jmap", "jstat",
        "mybatis", "spring boot", "spring cloud",
        "nacos", "eureka",
        "netty", "bio", "nio",
        "锁升级", "偏向锁", "轻量级锁",
    ]
    if any(kw.lower() in t for kw in java_keywords):
        positions.add("Java后端")

    # ============================================================
    # Go 后端
    # ============================================================
    go_keywords = [
        "go ", "golang",
        "goroutine", "channel ", "select", "gmp",
        "go 的垃圾回收", "go 内存",
        "接口 ", "结构体", "切片", "map ",
        "协程", "gmp 模型",
        "context", "defer", "panic", "recover",
    ]
    if any(kw.lower() in t for kw in go_keywords):
        positions.add("Go后端")

    # ============================================================
    # 前端
    # ============================================================
    frontend_keywords = [
        "javascript", "js ", "ecmascript",
        "typescript", "ts ",
        "react", "vue", "vuex", "redux",
        "dom", "bom",
        "css", "html",
        "浏览器渲染", "浏览器缓存", "重绘", "回流",
        "webpack", "vite", "babel",
        "event loop", "事件循环",
        "promise", "async/await", "async await",
        "闭包", "原型链", "作用域链",
        "this 指向", "箭头函数",
        "node", "npm", "yarn",
        "flex", "grid", "盒模型",
        "bom", "web api",
        "虚拟 dom", "diff 算法",
        "ssr", "单页应用", "spa",
        "微前端",
    ]
    if any(kw.lower() in t for kw in frontend_keywords):
        positions.add("前端")

    # ============================================================
    # 测试开发
    # ============================================================
    test_keywords = [
        "测试", "用例", "自动化测试",
        "selenium", "appium", "pytest", "junit",
        "接口测试", "性能测试", "压力测试",
        "mock", "桩", "打桩",
        "ci/cd", "jenkins",
        "白盒", "黑盒", "灰盒",
        "单元测试", "集成测试", "e2e",
        "质量保障", "qa",
        "bug ", "缺陷",
        "测试框架", "测试覆盖率",
        "流量回放", "diffy",
        "链路追踪", "skywalking", "zipkin",
        "监控告警", "prometheus", "grafana",
        "压测", "jmeter", "loadrunner",
    ]
    if any(kw.lower() in t for kw in test_keywords):
        positions.add("测试开发")

    # ============================================================
    # 算法工程师
    # ============================================================
    algo_keywords = [
        "leetcode", "时间复杂度", "空间复杂度",
        "o(n)", "o(log", "o(1)", "o(n",
        "二叉树", "红黑树", "b+树", "b树", "avl",
        "链表", "堆", "栈", "队列", "哈希表",
        "快排", "归并排序", "冒泡", "插入排序",
        "动态规划", "dp ", "dfs", "bfs",
        "递归", "迭代",
        "滑动窗口", "双指针", "贪心",
        "二分查找", "二分法",
        "拓扑排序", "最短路径", "最小生成树",
        "并查集", "字典树", "trie",
        "反转链表", "接雨水", "lru",
        "排序算法", "查找算法",
        "字符串匹配", "kmp",
        "设计模式", "单例", "工厂模式",
        "算法题",
    ]
    if any(kw.lower() in t for kw in algo_keywords):
        positions.add("算法工程师")

    # ============================================================
    # AI 工程师
    # ============================================================
    ai_keywords = [
        "机器学习", "深度学习", "神经网络",
        "transformer", "bert", "gpt", "llm",
        "大模型", "大语言模型",
        "rnn", "cnn", "lstm", "attention",
        "moe", "混合专家",
        "模型训练", "模型推理", "模型部署",
        "loss", "损失函数", "梯度下降",
        "pytorch", "tensorflow",
        "nlp", "自然语言处理",
        "cv", "计算机视觉",
        "聚类", "分类", "回归",
        "过拟合", "欠拟合", "正则化",
        "embedding", "向量化",
        "prompt", "prompt engineering",
        "rag", "检索增强",
        "微调", "fine-tune", "sft",
        "强化学习", "rlhf",
        "召回", "粗排", "精排",
        "特征工程", "特征选择",
        "auc", "roc", "f1",
        "知识图谱",
        "推荐系统", "广告系统",
        "分词", "词向量",
        "生成对抗网络", "gan",
        "lora", "qlora",
        "vllm", "ollama",
        "langchain", "llamaindex",
        "softmax", "batch normalization",
        "dropout", "激活函数", "relu",
        "炼丹", "调参",
        "数据清洗", "数据标注",
        "a/b test", "ab test",
        "多模态",
    ]
    if any(kw.lower() in t for kw in ai_keywords):
        positions.add("AI工程师")

    # ============================================================
    # 产品经理
    # ============================================================
    pm_keywords = [
        "产品", "需求", "prd",
        "用户调研", "用户需求",
        "原型图", "axure", "figma", "sketch",
        "埋点", "数据分析",
        "a/b 测试", "ab测试", "灰度发布",
        "排期", "迭代", "敏捷", "scrum",
        "kpi", "北极星指标",
        "竞品分析", "市场分析",
        "商业模式", "商业价值",
        "roadmap", "路线图",
        "用户体验", "交互设计",
        "转化率", "留存", "日活", "dau", "mau",
        "增长", "运营",
        "项目管理",
    ]
    if any(kw.lower() in t for kw in pm_keywords):
        positions.add("产品经理")

    # ============================================================
    # 兜底判断：后端通用
    # ============================================================
    # 明显的后端技术问题但没有明确语言标签的，归入主流后端
    backend_general = [
        "mysql", "redis", "kafka", "rocketmq", "rabbitmq",
        "分布式", "微服务", "cap", "rpc",
        "数据库", "缓存", "消息队列",
        "索引", "事务", "锁",
        "dns", "cdn", "tcp", "udp", "http", "https",
        "架构", "高并发", "高可用",
        "docker", "kubernetes", "k8s",
        "api", "restful", "grpc",
        "elasticsearch", "mongodb",
        "consul", "nacos", "eureka",
    ]
    backend_general_match = any(kw.lower() in t for kw in backend_general)

    if backend_general_match:
        # 不明确语言的后端题 → 默认填 Python/Java/Go
        if "Python后端" not in positions:
            positions.add("Python后端")
        if "Java后端" not in positions:
            positions.add("Java后端")
        if "Go后端" not in positions:
            positions.add("Go后端")

    # ============================================================
    # 空集合兜底：面向所有岗位
    # ============================================================
    if not positions:
        # 基本都会进后端通用
        if backend_general_match:
            pass  # 已添加
        else:
            # 完全无法识别的，放在 Python 后端（默认）
            positions.add("Python后端")

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
    company = d.get("company", "") or ""
    position_field = d.get("position", "") or ""
    source_type = d.get("source_type", "") or ""
    q_level = d.get("question_level", "C") or "C"
    q_id = d.get("id", "")

    pos_list = classify_positions(text, company, position_field, source_type, q_level)
    results.append({
        "id": q_id,
        "text": text,
        "level": q_level.strip().upper(),
        "positions": pos_list,
    })

# ============================================================
# 统计
# ============================================================

# 1. 岗位 → 题量
pos_count = defaultdict(int)
for r in results:
    for p in r["positions"]:
        pos_count[p] += 1

# 2. 交叉统计：岗位 × 等级
pos_level = defaultdict(lambda: defaultdict(int))
for r in results:
    for p in r["positions"]:
        pos_level[p][r["level"]] += 1

# 3. 场景内统计
scenario_count = defaultdict(lambda: defaultdict(int))
for row in all_rows:
    d = dict(row)
    sid = d.get("scenario_id", "unknown")
    lev = (d.get("question_level") or "C").strip().upper()

# ============================================================
# 输出报告
# ============================================================

report_lines = []
report_lines.append("# 题目岗位归类分析报告")
report_lines.append("")
report_lines.append("## 总览")
report_lines.append("")
report_lines.append(f"- 总题数: {len(all_rows)}")
report_lines.append(f"- 岗位分类数: {len(ALL_POSITIONS)}")
report_lines.append(f"- 一道题可归属多个岗位")
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

report_lines.append("## 3. S 级题目 × 岗位分布（核心数据）")
report_lines.append("")
s_total = sum(1 for r in results if r["level"] == "S")
report_lines.append(f"S 级总题数: {s_total}")
report_lines.append("")
report_lines.append("| 岗位 | S 级题量 | 占 S 级比例 | 示意 |")
report_lines.append("|------|:--------:|:-----------:|------|")
for p in ALL_POSITIONS:
    s_cnt = pos_level[p].get("S", 0)
    pct = s_cnt / s_total * 100 if s_total else 0
    bar = "█" * int(pct / 5) + "░" * max(0, 20 - int(pct / 5))
    report_lines.append(f"| **{p}** | {s_cnt} | {pct:.1f}% | {bar} |")
report_lines.append("")

report_lines.append("## 4. 各岗位 S+A 级可用题量")
report_lines.append("")
report_lines.append("| 岗位 | S+A 合计 | 是否充足(>=20) |")
report_lines.append("|------|:--------:|:--------------:|")
worst_positions = []
for p in ALL_POSITIONS:
    sa = pos_level[p].get("S", 0) + pos_level[p].get("A", 0)
    status = "充足" if sa >= 20 else ("不足" if sa >= 10 else "严重不足")
    report_lines.append(f"| **{p}** | {sa} | {status} |")
    if sa < 20:
        worst_positions.append((p, sa))
report_lines.append("")

report_lines.append("## 5. 覆盖率不足的岗位（S+A < 20）")
report_lines.append("")
if worst_positions:
    report_lines.append("| 岗位 | S+A 题量 | 建议 |")
    report_lines.append("|------|:--------:|------|")
    for p, sa in sorted(worst_positions, key=lambda x: x[1]):
        if sa < 5:
            suggestion = "急需补充：几乎无该岗位专用题"
        elif sa < 10:
            suggestion = "需重点补充：单次面试可能不够"
        elif sa < 15:
            suggestion = "建议补充：边缘情况可能缺题"
        else:
            suggestion = "勉强达标：建议持续补充"
        report_lines.append(f"| **{p}** | {sa} | {suggestion} |")
else:
    report_lines.append("所有岗位 S+A 题量均 >= 20，覆盖率充足。")
report_lines.append("")

# 示例：各岗位 S 级题目的内容样本
report_lines.append("## 6. 各岗位 S 级题目示例")
report_lines.append("")
for p in ALL_POSITIONS:
    samples = [r for r in results if p in r["positions"] and r["level"] == "S"][:3]
    report_lines.append(f"### {p}（S 级示例）")
    if samples:
        for s in samples:
            report_lines.append(f"- {s['text'][:70]}")
    else:
        report_lines.append("- （无 S 级题目）")
    report_lines.append("")

# 保存报告
outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "docs", "岗位归类分析报告.md")
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
    print(f"  {p:12s}  总计={total:4d}  S={s:3d}  A={a:3d}")
