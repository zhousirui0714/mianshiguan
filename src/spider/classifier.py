"""
自动分类器 — 根据题目内容匹配分类和标签
"""

import re
from typing import List, Tuple

from src.spider.config import CATEGORY_KEYWORDS, DEFAULT_CATEGORY


class Classifier:
    """基于关键词匹配的自动分类器"""

    def classify(self, question: str, answer: str = "",
                 default_cat: str = None) -> Tuple[str, List[str]]:
        """
        对一道题进行分类。

        返回: (category, [tag1, tag2, ...])
        """
        combined = f"{question} {answer}".lower()

        # 计算每个分类的匹配分数
        scores = {}
        matched_keywords = {}

        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = 0
            matched = []
            for kw in keywords:
                # 中文关键词直接匹配
                if kw.lower() in combined:
                    score += 1
                    matched.append(kw)
            if score > 0:
                scores[cat] = score
                matched_keywords[cat] = matched

        if not scores:
            return (default_cat or DEFAULT_CATEGORY, [default_cat or DEFAULT_CATEGORY])

        # 按分数排序取最高分
        best_cat = max(scores, key=scores.get)

        # 标签 = 匹配到的关键词（取前 3 个最有区分度的）
        tags = matched_keywords.get(best_cat, [])[:3]
        # 加上分类名作为标签
        tags = [best_cat] + tags

        return (best_cat, tags)

    def batch_classify(self, questions: List[dict]) -> List[dict]:
        """批量分类"""
        for q in questions:
            cat, tags = self.classify(
                q.get("question", ""),
                q.get("answer", ""),
                q.get("default_cat"),
            )
            q["category"] = cat
            q["tags"] = tags
        return questions
