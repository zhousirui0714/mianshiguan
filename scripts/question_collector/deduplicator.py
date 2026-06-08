"""
去重模块 - 内部去重 + 与现有题库去重

去重策略：
1. 指纹去重：MD5(fingerprint) 精确匹配
2. 前缀去重：前20-30字符匹配
3. 模糊去重：Levenshtein 比率（高于阈值视为重复）
"""

import re
import hashlib
from typing import List, Set, Tuple
from difflib import SequenceMatcher

from .config import DEDUP_CONFIG, EXISTING_DB
from .schema import CollectedQuestion


# ================================================================
# 指纹生成
# ================================================================

def _normalize(text: str) -> str:
    """归一化文本用于去重比较"""
    text = text.strip()
    # 去除标点符号差异
    text = re.sub(r'[？?]', '', text)
    text = re.sub(r'[，,]', '', text)
    text = re.sub(r'[。.]', '', text)
    text = re.sub(r'[\s]+', ' ', text)
    return text.lower()


def fingerprint_exact(text: str) -> str:
    """精确指纹：MD5 归一化全文"""
    return hashlib.md5(_normalize(text).encode('utf-8')).hexdigest()


def fingerprint_prefix(text: str, length: int = 25) -> str:
    """前缀指纹：取前 N 个字符的归一化版本"""
    prefix = _normalize(text)[:length]
    return hashlib.md5(prefix.encode('utf-8')).hexdigest()


# ================================================================
# 模糊相似度
# ================================================================

def similarity_ratio(a: str, b: str) -> float:
    """Levenshtein 相似度比率"""
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


# ================================================================
# 内部去重
# ================================================================

class InternalDeduplicator:
    """内部去重器 - 对同一批次采集的题目去重"""

    def __init__(self):
        self._exact_seen: Set[str] = set()
        self._prefix_seen: Set[str] = set()
        self._all_questions: List[str] = []

    def is_duplicate(self, question: CollectedQuestion) -> Tuple[bool, str]:
        """
        检查是否重复

        Returns:
            (is_dup, reason)
        """
        text = question.question

        # 1. 精确指纹匹配
        fp = fingerprint_exact(text)
        if fp in self._exact_seen:
            return (True, "exact_match")

        # 2. 前缀指纹匹配
        prefix_fp = fingerprint_prefix(text)
        if prefix_fp in self._prefix_seen:
            return (True, "prefix_match")

        # 3. 模糊匹配
        for existing in self._all_questions:
            ratio = similarity_ratio(text, existing)
            if ratio >= DEDUP_CONFIG["similarity_threshold"]:
                return (True, f"fuzzy_match({ratio:.2f})")

        return (False, "")

    def add(self, question: CollectedQuestion):
        """将题目加入去重索引"""
        text = question.question
        self._exact_seen.add(fingerprint_exact(text))
        self._prefix_seen.add(fingerprint_prefix(text))
        self._all_questions.append(text)

    def deduplicate(self, questions: List[CollectedQuestion]) -> List[CollectedQuestion]:
        """
        对题目列表进行内部去重

        Returns:
            去重后的题目列表（已合并 occurrence_count）
        """
        result = []
        count_map = {}  # fp -> total occurrence_count

        for q in questions:
            is_dup, reason = self.is_duplicate(q)
            if not is_dup:
                self.add(q)
                result.append(q)
                fp = fingerprint_exact(q.question)
                count_map[fp] = q.occurrence_count
            else:
                # 合并 occurrence_count
                fp = fingerprint_exact(q.question)
                if fp in count_map:
                    count_map[fp] += q.occurrence_count

        # 更新 occurrence_count
        for q in result:
            fp = fingerprint_exact(q.question)
            q.occurrence_count = count_map.get(fp, 1)

        removed = len(questions) - len(result)
        if removed > 0:
            print(f"    内部去重: 移除 {removed} 条重复")
        return result


# ================================================================
# 与现有题库去重
# ================================================================

class DatabaseDeduplicator:
    """与现有 SQLite 题库去重"""

    def __init__(self, db_path: str = EXISTING_DB):
        self.db_path = db_path
        self._existing_prefixes: Set[str] = set()

    def load_existing(self):
        """从数据库加载现有题目前缀指纹"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT question_text FROM questions")
            rows = cur.fetchall()
            conn.close()

            for (text,) in rows:
                if text:
                    self._existing_prefixes.add(fingerprint_prefix(text))
            print(f"    已加载 {len(self._existing_prefixes)} 条现有题目")
        except Exception as e:
            print(f"    [警告] 加载现有题库失败: {e}")

    def is_in_database(self, question: CollectedQuestion) -> bool:
        """检查是否已在数据库中"""
        prefix_fp = fingerprint_prefix(question.question)
        return prefix_fp in self._existing_prefixes

    def deduplicate(self, questions: List[CollectedQuestion]) -> List[CollectedQuestion]:
        """过滤掉已在数据库中的题目"""
        self.load_existing()
        result = []
        for q in questions:
            if not self.is_in_database(q):
                result.append(q)
        removed = len(questions) - len(result)
        if removed > 0:
            print(f"    数据库去重: 移除 {removed} 条已存在的题目")
        return result
