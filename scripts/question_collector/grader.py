"""
评级模块 - 对采集到的面试题进行 S/A/B/C 评级

评级标准：
S级：真实高频题 - 在多个面经中重复出现，或来自高可信度来源
A级：真实出现过  - 在面经中实际出现，来源可追溯
B级：推测题       - 根据面经推断的可能问题
C级：泛化题       - 通用问题，无法确认来源

只保留 S 级和 A 级进入正式题库。
"""

import re
from typing import List

from .schema import CollectedQuestion
from .config import GRADE_CONFIG, KEEP_GRADES


# ================================================================
# 可靠性评分 - 来源可信度
# ================================================================
# source 字段可能包含关键词，从中匹配可信度

SOURCE_RELIABILITY = {
    "牛客": 0.9,
    "nowcoder": 0.9,
    "CSDN": 0.8,
    "blog.csdn": 0.8,
    "知乎": 0.7,
    "zhihu": 0.7,
    "JavaGuide": 0.85,
    "CS-Notes": 0.85,
    "GitHub": 0.8,
    "面经": 0.8,
    "大厂": 0.8,
    "字节跳动": 0.9,
    "腾讯": 0.9,
    "阿里": 0.9,
    "美团": 0.9,
    "百度": 0.9,
    "通用": 0.6,
    "真题": 0.8,
    "面试": 0.7,
    "考研": 0.7,
    "复试": 0.7,
    "教资": 0.8,
    "公务员": 0.8,
    "MBA": 0.7,
    "IELTS": 0.8,
    "雅思": 0.8,
    "HR": 0.6,
    "default": 0.5,
}


def _source_reliability_score(question: CollectedQuestion) -> int:
    """
    根据 source 字段评估来源可信度

    Returns: 0-30
    """
    source = question.source
    if not source:
        return 10  # 无来源信息，给基准分

    max_rel = 0
    for keyword, reliability in SOURCE_RELIABILITY.items():
        if keyword in source:
            max_rel = max(max_rel, reliability)

    if max_rel == 0:
        max_rel = SOURCE_RELIABILITY["default"]

    return int(max_rel * 30)


def _specificity_score(text: str) -> int:
    """问题具体性评分 (0-20)"""
    score = 0

    # 英文技术名词（Java, Redis, MySQL, TCP 等）
    tech_terms = re.findall(r'\b[A-Z][a-zA-Z0-9+#]+\b', text)
    score += min(len(tech_terms) * 3, 9)

    # 数字（LeetCode 题号、版本号等）
    if re.search(r'\d+', text):
        score += 3

    # 缩写（JVM, LRU, HTTP, CAP 等）
    if re.search(r'\b[A-Z]{2,}\b', text):
        score += 3

    # 问题长度
    if len(text) >= 20: score += 1
    if len(text) >= 40: score += 2
    if len(text) >= 60: score += 2

    # 专有名词（问号前的具体内容）
    if re.search(r'[？?]', text):
        before_q = text.split('？')[0].split('?')[0]
        if len(before_q) >= 10:
            score += 2

    return min(score, 20)


def _occurrence_score(question: CollectedQuestion) -> int:
    """出现频率评分 (0-25)"""
    occ = question.occurrence_count
    freq = question.frequency

    base = 0
    if occ >= 5: base = 25
    elif occ >= 3: base = 22
    elif occ == 2: base = 18
    elif occ == 1: base = 12
    else: base = 5

    # frequency 加成
    base += freq * 1
    return min(base, 25)


def _relevance_score(question: CollectedQuestion) -> int:
    """
    场景相关度评分 (0-15)

    面试题天然与场景相关，只要不是明显不匹配就给予基础分。
    """
    text = question.question
    from .classifier import SCENARIO_KEYWORDS
    scenario_kws = SCENARIO_KEYWORDS.get(question.scenario, {}).get("keywords", [])

    # 基础分：每道面试题都至少与场景有关
    base = 5

    # 关键词匹配加成
    match_count = sum(1 for kw in scenario_kws if kw.lower() in text.lower())
    base += min(match_count * 2, 10)

    return min(base, 15)


def _detail_score(text: str) -> int:
    """细节丰富度评分 (0-10)"""
    score = 0

    if "。" in text or "." in text: score += 2  # 多句话
    if any(c in text for c in "，、：；"): score += 2  # 中文标点
    if "?" in text or "？" in text: score += 2  # 问句
    if "'" in text or '"' in text or '「' in text: score += 2  # 引用

    # 单词数（含中文）
    word_count = len(re.findall(r'[\w\u4e00-\u9fff]+', text))
    if word_count >= 20: score += 2

    return min(score, 10)


# ================================================================
# 评分
# ================================================================

def _score_question(question: CollectedQuestion) -> dict:
    """对单道题进行多维评分"""
    text = question.question

    scores = {
        "specificity": _specificity_score(text),
        "source_reliability": _source_reliability_score(question),
        "occurrence": _occurrence_score(question),
        "scenario_relevance": _relevance_score(question),
        "detail_level": _detail_score(text),
    }
    scores["total"] = sum(scores.values())
    return scores


# ================================================================
# 评级
# ================================================================

def grade_single(question: CollectedQuestion) -> str:
    """对单道题进行 S/A/B/C 评级"""
    scores = _score_question(question)
    total = scores["total"]
    occ = question.occurrence_count

    # S 级：高频 + 来源可靠
    if occ >= GRADE_CONFIG["S"]["min_occurrence"] and total >= 60:
        return "S"

    # A 级：真实出现
    if occ >= GRADE_CONFIG["A"]["min_occurrence"] and total >= 35:
        return "A"

    # B 级：推测题
    if total >= 20:
        return "B"

    return "C"


def grade_with_reason(question: CollectedQuestion) -> tuple:
    """评级并给出理由"""
    scores = _score_question(question)
    total = scores["total"]
    grade = grade_single(question)

    details = [f"{k}={v}" for k, v in scores.items() if k != "total"]
    score_detail = ", ".join(details)

    reason = f"总分{total}({score_detail}), 出现{question.occurrence_count}次"
    return grade, reason


# ================================================================
# 批量评级
# ================================================================

def grade_all(questions: List[CollectedQuestion]) -> List[CollectedQuestion]:
    """
    对题目列表评级并过滤（只保留 S 和 A 级）
    """
    result = []
    grade_counts = {"S": 0, "A": 0, "B": 0, "C": 0}

    for q in questions:
        grade, reason = grade_with_reason(q)
        q.grade = grade
        q.grade_reason = reason
        grade_counts[grade] = grade_counts.get(grade, 0) + 1

        if grade in KEEP_GRADES:
            result.append(q)

    print(f"\n  评级分布: S={grade_counts['S']} A={grade_counts['A']} "
          f"B={grade_counts['B']} C={grade_counts['C']}")
    print(f"  保留 S+A: {len(result)} 题 (移除 {len(questions) - len(result)} 题)")
    return result
