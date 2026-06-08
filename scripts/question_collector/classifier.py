"""
分类模块 - 对面试题进行场景 + 类别分类

1. 场景分类：确认题目属于哪个面试场景
2. 类别分类：确认题目属于哪个技术/能力类别

策略：
- 关键词匹配（快速）
- LLM 辅助（准确）
"""

import re
from typing import List, Optional

from .schema import CollectedQuestion
from .config import LLM_CONFIG


# ================================================================
# 场景关键词
# ================================================================

SCENARIO_KEYWORDS = {
    "job_interview": {
        "keywords": [
            "技术面试", "一面", "二面", "三面", "HR面",
            "Java", "Python", "Go", "C++", "前端", "后端",
            "算法题", "LeetCode", "项目经历", "技术栈",
            "Spring", "MySQL", "Redis", "分布式", "微服务",
            "数据结构", "操作系统", "网络", "设计模式",
        ],
        "weight": 1,
    },
    "teacher_cert": {
        "keywords": [
            "教资", "教师资格", "结构化面试", "试讲",
            "学生", "课堂", "教学", "班主任", "板书",
            "新课标", "素质教育", "德育", "教案",
            "导入", "讲授", "互动",
        ],
        "weight": 1,
    },
    "civil_service": {
        "keywords": [
            "公务员", "结构化面试", "综合分析", "应急处理",
            "人际关系", "组织管理", "社会现象", "政策理解",
            "基层", "群众", "服务", "行政", "执法",
            "乡村振兴", "脱贫攻坚", "疫情", "民生",
        ],
        "weight": 1,
    },
    "graduate_school": {
        "keywords": [
            "考研", "复试", "研究生", "导师", "科研",
            "论文", "研究方向", "学术", "专业基础",
            "为什么读研", "未来规划", "本科项目",
            "英语自我介绍", "专业英语", "文献",
        ],
        "weight": 1,
    },
    "mba_interview": {
        "keywords": [
            "MBA", "商学院", "管理", "领导力", "职业规划",
            "团队管理", "创业", "商业案例", "战略",
            "行业分析", "商业模式", "核心竞争力",
            "为什么读MBA", "管理经验",
        ],
        "weight": 1,
    },
    "ielts_speaking": {
        "keywords": [
            "IELTS", "雅思", "口语", "Part 1", "Part 2", "Part 3",
            "Describe", "What do you think", "Do you like",
            "hometown", "study", "work", "hobby",
            "English", "speaking",
        ],
        "weight": 1,
    },
}

# ================================================================
# 类别关键词
# ================================================================

CATEGORY_KEYWORDS = {
    "Java": ["Java", "JVM", "Spring", "MyBatis", "Hibernate", "Maven", "Gradle"],
    "Python": ["Python", "Django", "Flask", "FastAPI", "pandas", "numpy"],
    "Go": ["Go", "Golang", "goroutine", "channel", "Gin"],
    "前端": ["JavaScript", "TypeScript", "React", "Vue", "CSS", "HTML", "前端"],
    "算法": ["算法", "排序", "链表", "二叉树", "动态规划", "DFS", "BFS", "LeetCode"],
    "数据库": ["MySQL", "Redis", "MongoDB", "SQL", "索引", "事务", "分库分表"],
    "操作系统": ["进程", "线程", "内存", "Linux", "epoll", "select", "IO"],
    "网络": ["TCP", "HTTP", "HTTPS", "DNS", "网络协议", "WebSocket"],
    "系统设计": ["分布式", "微服务", "高并发", "设计", "架构"],
    "项目深挖": ["项目", "STAR", "挑战", "难点", "成就"],
    "行为面试": ["优缺点", "职业规划", "团队合作", "冲突"],
    "结构化面试": ["综合分析", "应急处理", "人际关系", "组织管理"],
    "英语口语": ["Describe", "What", "Do you", "hometown", "hobby"],
    "专业知识": ["专业基础", "研究方向", "学术"],
    "管理": ["领导力", "团队管理", "战略", "商业模式"],
}


# ================================================================
# 场景分类
# ================================================================

def classify_scenario(question: CollectedQuestion) -> str:
    """
    根据题目内容判断最可能的场景

    如果题目已有场景（来自搜索时指定的场景），
    但内容明显不符合，则修正。

    Returns:
        场景 ID
    """
    current = question.scenario
    text = question.question

    scores = {}
    for scenario, info in SCENARIO_KEYWORDS.items():
        score = 0
        for kw in info["keywords"]:
            if kw.lower() in text.lower():
                score += info["weight"]
        if score > 0:
            scores[scenario] = score

    if not scores:
        return current

    # 取得分最高的场景
    best = max(scores, key=scores.get)

    # 如果当前场景得分也不错（至少最高分的50%），保持原场景
    if current in scores:
        if scores[current] >= scores[best] * 0.5:
            return current

    return best


# ================================================================
# 类别分类
# ================================================================

def classify_category(question: CollectedQuestion) -> str:
    """
    根据题目内容判断类别

    Returns:
        类别名称
    """
    text = question.question
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in text.lower():
                score += 1
        if score > 0:
            scores[category] = score

    if not scores:
        # 根据场景返回默认类别
        defaults = {
            "job_interview": "计算机基础",
            "teacher_cert": "结构化面试",
            "civil_service": "结构化面试",
            "graduate_school": "专业知识",
            "mba_interview": "管理",
            "ielts_speaking": "英语口语",
        }
        return defaults.get(question.scenario, "通用")

    return max(scores, key=scores.get)


# ================================================================
# 批量分类
# ================================================================

def classify_all(questions: List[CollectedQuestion]) -> List[CollectedQuestion]:
    """
    对题目列表进行场景 + 类别分类

    Returns:
        分类后的题目列表（修正场景、补充类别）
    """
    for q in questions:
        q.scenario = classify_scenario(q)
        if not q.category:
            q.category = classify_category(q)

    print(f"  分类完成: {len(questions)} 题")
    return questions
