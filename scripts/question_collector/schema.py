"""
数据模型定义 - 采集题目的标准 Schema
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json
import hashlib

# ================================================================
# 标准题目 Schema
# ================================================================
# 每道采集到的题目使用此结构存储
# ================================================================

@dataclass
class CollectedQuestion:
    """
    采集题目的标准数据模型

    必填字段：
        question:       面试问题原文
        scenario:       适用场景（job_interview / teacher_cert / 等）

    真实性相关：
        authenticity:   真实性标记（real / inferred）
        source:         来源描述
        source_url:     原文链接（必须可访问）
        occurrence_count: 出现次数（多条相同问题合并时累加）

    分类相关：
        category:      题目分类（如：算法/Java/结构化面试/英语口语）
        difficulty:    难度 1-5
        frequency:     出现频率 1-5

    评级相关（由 grader 模块计算）：
        grade:         评级（S/A/B/C）
        grade_reason:  评级理由

    答案相关（由 answer_generator 模块生成）：
        answer_basic:   普通回答（60分水平）
        answer_good:    良好回答（80分水平）
        answer_excellent: 高分回答（95分水平）

    元信息：
        school_or_company: 对应学校/公司
        year:          面试年份
        tags:          标签列表
    """
    # --- 核心字段 ---
    question: str
    scenario: str

    # --- 真实性 ---
    authenticity: str = "real"          # "real" | "inferred"
    source: str = ""
    source_url: str = ""
    occurrence_count: int = 1

    # --- 分类 ---
    category: str = ""
    difficulty: int = 3                 # 1-5
    frequency: int = 3                  # 1-5

    # --- 评级 ---
    grade: str = "C"                    # "S" | "A" | "B" | "C"
    grade_reason: str = ""

    # --- 答案 ---
    answer_basic: str = ""              # 60分
    answer_good: str = ""               # 80分
    answer_excellent: str = ""          # 95分

    # --- 元信息 ---
    school_or_company: str = ""
    year: int = 2025
    tags: list = field(default_factory=list)
    collected_at: str = ""

    def to_dict(self) -> dict:
        """转为可序列化的字典"""
        return asdict(self)

    def to_json(self) -> str:
        """转为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def fingerprint(self) -> str:
        """生成内容指纹用于去重"""
        # 归一化：去空格、转小写（非英文保留原样）
        text = self.question.strip()
        text = ' '.join(text.split())
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def short_fingerprint(self) -> str:
        """短指纹用于快速去重"""
        # 取前20个字符的去空格版本
        key = self.question.strip()[:30]
        key = ' '.join(key.split())
        return hashlib.md5(key.encode('utf-8')).hexdigest()[:12]


# ================================================================
# 批量采集结果
# ================================================================

@dataclass
class CollectionResult:
    """一次批量采集的结果"""
    total_found: int = 0
    new_questions: list = field(default_factory=list)
    duplicates_skipped: int = 0
    low_grade_filtered: int = 0
    errors: list = field(default_factory=list)
    sources_used: list = field(default_factory=list)


# ================================================================
# 平台来源定义
# ================================================================

PLATFORM_INFO = {
    "nowcoder": {
        "name": "牛客网",
        "url": "https://www.nowcoder.com",
        "description": "牛客网面经",
        "scenarios": ["job_interview"],
    },
    "zhihu": {
        "name": "知乎",
        "url": "https://www.zhihu.com",
        "description": "知乎面试经验/复试经验",
        "scenarios": ["job_interview", "graduate_school", "civil_service", "mba_interview"],
    },
    "csdn": {
        "name": "CSDN",
        "url": "https://blog.csdn.net",
        "description": "CSDN面试题博客",
        "scenarios": ["job_interview"],
    },
    "xiaohongshu": {
        "name": "小红书",
        "url": "https://www.xiaohongshu.com",
        "description": "小红书面经/复试经验",
        "scenarios": ["job_interview", "graduate_school", "civil_service"],
    },
    "gaoxiao": {
        "name": "高校论坛",
        "url": "",
        "description": "高校考研/复试经验帖",
        "scenarios": ["graduate_school"],
    },
    "ielts": {
        "name": "雅思口语",
        "url": "",
        "description": "雅思口语题库/回忆",
        "scenarios": ["ielts_speaking"],
    },
}
