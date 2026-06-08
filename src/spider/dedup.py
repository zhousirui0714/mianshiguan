"""
去重模块 — 精确去重 + 相似度去重

规则:
1. 题目完全一样 → 跳过
2. 文本相似度 > 90% → 跳过
"""

import difflib
from typing import List, Dict, Set


class Deduplicator:
    """
    题库去重器。
    同时支持精确去重（字符串比对）和模糊去重（SequenceMatcher）。
    """

    SIMILARITY_THRESHOLD = 0.90  # 相似度阈值

    def __init__(self, existing_questions: List[Dict] = None):
        """
        existing_questions: 数据库中已有的题目列表 [{question_text, ...}]
        """
        self._exact_set: Set[str] = set()
        self._question_texts: List[str] = []
        if existing_questions:
            for q in existing_questions:
                text = self._normalize(q.get("question_text", "") or "")
                self._exact_set.add(text)
                self._question_texts.append(text)

    def filter(self, candidates: List[Dict]) -> List[Dict]:
        """
        过滤：只返回通过去重的新题目。

        candidates: [{question, ...}, ...]
        返回: [{question, ...}, ...] 只包含新题目
        """
        new_questions = []
        skipped_exact = 0
        skipped_similar = 0

        for c in candidates:
            text = c.get("question", "").strip()
            if not text:
                continue

            norm = self._normalize(text)

            # 1. 精确去重
            if norm in self._exact_set:
                skipped_exact += 1
                continue

            # 2. 模糊去重
            is_similar = False
            for existing in self._question_texts:
                ratio = difflib.SequenceMatcher(None, norm, existing).ratio()
                if ratio >= self.SIMILARITY_THRESHOLD:
                    is_similar = True
                    break

            if is_similar:
                skipped_similar += 1
                continue

            # 通过去重
            new_questions.append(c)
            self._exact_set.add(norm)
            self._question_texts.append(norm)

        return new_questions

    def get_stats(self) -> dict:
        """返回去重统计信息"""
        return {
            "total_existing": len(self._exact_set),
        }

    @staticmethod
    def _normalize(text: str) -> str:
        """标准化文本用于比对"""
        text = text.strip()
        # 去掉标点符号
        import string
        for p in string.punctuation + "，。！？、；：“”‘’（）【】《》":
            text = text.replace(p, "")
        # 去掉空格
        text = "".join(text.split())
        # 转小写
        text = text.lower()
        return text
