# -*- coding: utf-8 -*-
"""
回填所有现有题目的 target_positions 字段。
使用 v2 的分类逻辑，不重复新增题目。
"""
import sys, os, json, sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "interview.db")

# ================================================================
# 分类逻辑（同 audit_target_positions_v2.py）
# ================================================================

def classify_positions(text: str) -> list:
    """根据题目内容判断目标岗位，一道题可属于多个岗位。"""
    positions = set()
    t = text

    # Python 后端
    python_kw = ["python", "django", "flask", "fastapi", "celery", "numpy", "pandas"]
    if any(kw.lower() in t.lower() for kw in python_kw):
        positions.add("Python后端")

    # Java 后端
    java_kw = ["jvm", "java", "spring", "mybatis", "dubbo", "tomcat", "netty",
               "servlet", "jdbc", "synchronized", "volatile", "reentrantlock",
               "threadpoolexecutor", "aqs", "concurrenthashmap", "jmm",
               "nacos", "eureka", "锁升级", "偏向锁", "轻量级锁"]
    if any(kw.lower() in t.lower() for kw in java_kw):
        positions.add("Java后端")

    # Go 后端
    go_kw = ["golang", "goroutine", "gmp", "go 的垃圾", "go 内存"]
    if any(kw.lower() in t.lower() for kw in go_kw):
        positions.add("Go后端")

    # 前端
    frontend_kw = ["javascript", "typescript", "react ", "vue ",
                   "dom", "css", "html", "浏览器渲染", "浏览器缓存",
                   "webpack", "vite", "babel", "事件循环", "event loop",
                   "promise", "async/await", "闭包", "原型链",
                   "盒模型", "虚拟 dom", "diff 算法", "ssr", "spa", "微前端",
                   "前端", "nodejs", "node.js"]
    if any(kw.lower() in t.lower() for kw in frontend_kw):
        positions.add("前端")

    # 测试开发
    test_kw = ["测试用例", "自动化测试", "selenium", "appium", "pytest", "junit",
               "接口测试", "性能测试", "压力测试", "mock ", "ci/cd", "jenkins",
               "白盒测试", "黑盒测试", "单元测试", "集成测试", "e2e",
               "质量保障", "qa", "缺陷", "bug ", "流量回放", "diffy",
               "链路追踪", "skywalking", "zipkin", "prometheus", "grafana",
               "压测", "jmeter"]
    if any(kw.lower() in t.lower() for kw in test_kw):
        positions.add("测试开发")

    # 算法工程师
    algo_kw = ["leetcode", "时间复杂度", "空间复杂度", "动态规划", "dfs", "bfs",
               "滑动窗口", "双指针", "贪心", "二分查找", "二分法",
               "拓扑排序", "最短路径", "最小生成树", "并查集", "字典树", "trie",
               "反转链表", "接雨水", "lru", "字符串匹配", "kmp",
               "数组第 k", "前 k 个", "跳表", "skiplist"]
    if any(kw.lower() in t.lower() for kw in algo_kw):
        positions.add("算法工程师")

    # AI 工程师
    ai_kw = ["机器学习", "深度学习", "神经网络", "transformer", "bert", "gpt",
             "llm", "大模型", "大语言模型", "rnn", "cnn", "lstm", "attention",
             "moe", "混合专家", "pytorch", "tensorflow", "nlp", "自然语言处理",
             "cv", "计算机视觉", "过拟合", "欠拟合", "embedding",
             "prompt", "rag", "检索增强", "微调", "fine-tune", "sft",
             "强化学习", "rlhf", "召回", "粗排", "精排", "特征工程",
             "auc", "roc", "f1", "知识图谱", "推荐系统",
             "lora", "qlora", "langchain", "激活函数", "relu", "softmax",
             "多模态", "agent", "sft"]
    if any(kw.lower() in t.lower() for kw in ai_kw):
        positions.add("AI工程师")

    # 产品经理
    pm_kw = ["产品需求", "prd", "用户调研", "用户需求", "原型图",
             "axure", "figma", "埋点", "灰度发布", "竞品分析", "商业模式",
             "用户体验", "交互设计", "转化率", "留存", "日活", "dau", "mau",
             "增长", "运营", "项目管理", "kpi", "产品经理"]
    if any(kw.lower() in t.lower() for kw in pm_kw):
        positions.add("产品经理")

    # 后端通用兜底
    backend_general = [
        "mysql", "redis", "kafka", "rocketmq", "rabbitmq",
        "分布式", "微服务", "cap", "rpc",
        "数据库", "缓存", "消息队列", "事务", "锁",
        "dns", "cdn", "tcp", "udp", "http", "https",
        "架构", "高并发", "高可用",
        "docker", "kubernetes", "k8s",
        "api", "restful", "grpc",
        "elasticsearch", "mongodb",
        "consul", "nacos", "eureka",
        "select", "epoll", "索引", "主从",
    ]
    has_backend = any(kw.lower() in t.lower() for kw in backend_general)

    if has_backend:
        has_python = "Python后端" in positions
        has_java = "Java后端" in positions
        has_go = "Go后端" in positions
        if not has_python and not has_java and not has_go:
            positions.add("Python后端")
            positions.add("Java后端")
            positions.add("Go后端")
        else:
            if not has_python:
                positions.add("Python后端")
            if not has_java:
                positions.add("Java后端")
            if not has_go:
                positions.add("Go后端")

    return sorted(positions)


# ================================================================
# 回填
# ================================================================

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

all_rows = conn.execute("SELECT * FROM questions").fetchall()
print(f"总题数: {len(all_rows)}")

updated = 0
skipped = 0
stats = {}

for row in all_rows:
    d = dict(row)
    qid = d["id"]
    text = d.get("question_text", "") or ""

    # 检查是否已有 target_positions
    existing_tp = d.get("target_positions", "") or ""
    if existing_tp and existing_tp != "[]":
        # 已有有效值，跳过
        skipped += 1
        continue

    pos_list = classify_positions(text)
    tp_str = json.dumps(pos_list, ensure_ascii=False)

    conn.execute(
        "UPDATE questions SET target_positions = ? WHERE id = ?",
        (tp_str, qid)
    )
    updated += 1

    for p in pos_list:
        stats[p] = stats.get(p, 0) + 1

conn.commit()
conn.close()

print(f"已更新: {updated}")
print(f"已跳过（已有标记）: {skipped}")
print()
print("岗位分布（回填后）:")
for p in sorted(stats.keys(), key=lambda x: -stats[x]):
    print(f"  {p}: {stats[p]}")
