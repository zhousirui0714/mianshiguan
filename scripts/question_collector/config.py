"""
采集系统配置
"""

import os
import sys

# 将项目根目录加入 path（让 imports 能找到 src）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ================================================================
# 数据存储路径
# ================================================================

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "collected_questions")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 各阶段输出文件
RAW_JSON = os.path.join(OUTPUT_DIR, "01_raw.json")           # 原始提取结果
DEDUPED_JSON = os.path.join(OUTPUT_DIR, "02_deduped.json")   # 去重后
CLASSIFIED_JSON = os.path.join(OUTPUT_DIR, "03_classified.json")  # 分类后
GRADED_JSON = os.path.join(OUTPUT_DIR, "04_graded.json")     # 评级后
FINAL_JSON = os.path.join(OUTPUT_DIR, "05_final.json")       # 最终结果
ANSWERS_JSON = os.path.join(OUTPUT_DIR, "06_with_answers.json")   # 含答案
ALL_JSON = os.path.join(OUTPUT_DIR, "all_questions.json")    # 完整题库合稿

# 现有题库路径
EXISTING_DB = os.path.join(PROJECT_ROOT, "data", "interview.db")

# ================================================================
# 搜索引擎配置
# ================================================================

SEARCH_CONFIG = {
    # DuckDuckGo 搜索（免费，无需API Key）
    "duckduckgo": {
        "enabled": True,
        "timeout": 15,
        "max_results_per_query": 30,
        "delay_between_queries": 2.0,  # 秒
    },
    # 可选的 Bing Search API
    "bing": {
        "enabled": False,
        "api_key": os.getenv("BING_API_KEY", ""),
        "endpoint": "https://api.bing.microsoft.com/v7.0/search",
    },
}

# ================================================================
# 各场景搜索关键词
# ================================================================

SEARCH_QUERIES = {
    "job_interview": [
        # 牛客网面经
        "site:nowcoder.com 面经 2024 2025",
        "site:nowcoder.com 面试真题 后端 2025",
        "site:nowcoder.com 面试真题 前端 2025",
        "site:nowcoder.com 面试真题 算法 2025",
        "site:nowcoder.com 大厂面经 2025",
        # CSDN 面经
        "site:blog.csdn.net 面经 2024 2025 面试题",
        "site:blog.csdn.net 面试真题 大厂 2025",
        # 知乎面经
        "site:zhihu.com 面试经验 2025 面经",
        "site:zhihu.com 面试真题 大厂 2024 2025",
        # 通用补充
        "面经 2024 2025 面试真题 后端开发",
        "面经 2024 2025 面试真题 前端开发",
        "面经 2024 2025 面试真题 算法工程师",
        "大厂面试题 真实 2024 2025",
        "Java 面试题 真实面经 2025",
        "Python 面试题 真实面经 2025",
        "Go 面试题 真实面经 2025",
    ],
    "graduate_school": [
        "site:zhihu.com 考研复试 面试真题 2024 2025",
        "site:zhihu.com 复试经验 2025 面试问题",
        "考研复试 面试题 2024 2025 真实",
        "复试 面试 真题 计算机 2025",
        "考研复试 常见问题 2025",
        "研究生复试 面试 问题 2024 2025",
    ],
    "teacher_cert": [
        "site:zhihu.com 教资面试 真题 2024 2025",
        "教资面试 结构化 真题 2025",
        "教师资格证 面试 真题 2024 2025",
        "教资面试 试讲 真题 2025",
    ],
    "civil_service": [
        "site:zhihu.com 公务员面试 真题 2024 2025",
        "公务员面试 结构化 真题 2025",
        "省考 面试 真题 2024 2025",
        "国考 面试 真题 2025",
        "公务员 面试 真实题目 2024 2025",
    ],
    "mba_interview": [
        "site:zhihu.com MBA 面试 真题 2024 2025",
        "MBA 提前面试 真题 2025",
        "MBA 面试 真实问题 2024 2025",
        "商学院 面试 真题 2025",
    ],
    "ielts_speaking": [
        "site:zhihu.com 雅思口语 真题 2024 2025",
        "雅思口语 Part 1 真题 2025",
        "雅思口语 Part 2 真题 2025",
        "雅思口语 Part 3 真题 2025",
        "IELTS speaking questions 2024 2025",
        "雅思口语 题库 2025 真实",
    ],
}

# ================================================================
# 爬虫配置
# ================================================================

SCRAPER_CONFIG = {
    "request_timeout": 20,
    "request_delay": 1.5,              # 请求间隔（秒）
    "max_retries": 3,
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    },
}

# ================================================================
# 提取配置
# ================================================================

EXTRACTOR_CONFIG = {
    "min_question_length": 8,           # 问题最短字符数
    "max_question_length": 500,         # 问题最长字符数
    "use_llm_extraction": True,         # 是否使用LLM辅助提取
    "llm_per_page": True,              # 是否对每页内容调用LLM提取
}

# ================================================================
# 去重配置
# ================================================================

DEDUP_CONFIG = {
    "similarity_threshold": 0.85,       # 余弦相似度阈值（高于此值视为重复）
    "fuzzy_ratio_threshold": 80,        # 模糊匹配比率阈值
}

# ================================================================
# 评级标准
# ================================================================

GRADE_CONFIG = {
    "S": {
        "label": "真实高频题",
        "description": "在多个面经中重复出现，或来自高可信度来源",
        "min_occurrence": 2,
        "min_frequency": 4,
    },
    "A": {
        "label": "真实出现过",
        "description": "在面经中实际出现，来源可追溯",
        "min_occurrence": 1,
        "min_frequency": 1,
    },
    "B": {
        "label": "推测题",
        "description": "根据面经内容推断的可能问题，非原文直接出现",
        "min_occurrence": 0,
        "min_frequency": 0,
    },
    "C": {
        "label": "泛化题",
        "description": "通用问题，无法确认来源",
        "min_occurrence": 0,
        "min_frequency": 0,
    },
}

# 只保留S级和A级
KEEP_GRADES = ["S", "A"]

# ================================================================
# LLM 配置（复用项目已有的 iFlyTek Qwen API）
# ================================================================

LLM_CONFIG = {
    "api_url": "https://maas-api.cn-huabei-1.xf-yun.com/v2/chat/completions",
    "api_key": "6ad85b0f2b80ff7716b726b03010b5f5:NmViMmJmOWU1MTM5OTJlNmMyNDc5ZGQ2",
    "model": "xopqwen36v35b",
    "timeout": 60,
    "max_retries": 3,
}
