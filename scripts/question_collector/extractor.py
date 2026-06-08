"""
面试题提取器 - 从面经文本中提取面试问题

策略：
1. 规则提取：基于关键词和模式匹配（快速、无依赖）
2. LLM 提取：调用 Qwen API 从文本中提取问题（准确、但慢）
3. 混合模式：先用规则粗提，再用 LLM 补充

面试问题特征：
- 以"问"、"请"、"介绍"、"说说"、"谈谈"开头
- 包含"？"或"?"
- 面试题格式：数字 + 点 + 问题
"""

import re
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

from .config import EXTRACTOR_CONFIG, LLM_CONFIG
from .schema import CollectedQuestion
from .scrapers.dispatcher import scrape_url


# ================================================================
# 规则模式提取
# ================================================================

# 面试问题开头关键词
QUESTION_STARTS = [
    "请", "介绍", "说说", "谈谈", "讲", "描述", "解释", "阐述",
    "为什么", "如何", "怎么", "怎样", "什么是",
    "请介绍", "请说说", "请谈谈", "请描述", "请问",
    "你", "你的", "你觉得", "你认为", "你如何", "你怎么",
    "一个", "写一个", "实现", "设计",
]

# 面试问题常见模式
QUESTION_PATTERNS = [
    # "1. 问题" 格式
    re.compile(r'(?:^|\n)\s*(?:\d+[.、．])\s*([^\n]+[？?])\s*'),
    # "问：问题" 格式
    re.compile(r'(?:^|\n)\s*问[：:]\s*([^\n]+[？?])\s*'),
    # "问题：xxx" 格式
    re.compile(r'(?:^|\n)\s*(?:面试题|问题|真题)[：:]\s*([^\n]+[？?]?)\s*'),
    # "一面/二面/三面" + 问题
    re.compile(r'(?:^|\n)\s*(?:一面|二面|三面|终面|HR面|技术面)[：:：\s]*([^\n]+[？?]?)\s*'),
    # 关键词开头的问题
    re.compile(r'(?:^|\n)\s*(请[^\n]+[？?])'),
    re.compile(r'(?:^|\n)\s*(介绍[^\n]+[？?])'),
    re.compile(r'(?:^|\n)\s*(为什么[^\n]+[？?])'),
    re.compile(r'(?:^|\n)\s*(如何[^\n]+[？?])'),
    re.compile(r'(?:^|\n)\s*(说说[^\n]+[？?])'),
    re.compile(r'(?:^|\n)\s*(谈谈[^\n]+[？?])'),
]


def extract_by_rules(text: str) -> List[str]:
    """
    使用规则模式从文本中提取面试问题

    Args:
        text: 页面文本内容

    Returns:
        问题字符串列表
    """
    questions = []
    seen = set()

    for pattern in QUESTION_PATTERNS:
        matches = pattern.findall(text)
        for q in matches:
            q = q.strip()
            # 清洗
            q = re.sub(r'\s+', ' ', q)
            # 长度过滤
            if len(q) < EXTRACTOR_CONFIG["min_question_length"]:
                continue
            if len(q) > EXTRACTOR_CONFIG["max_question_length"]:
                continue
            # 去重
            key = q[:20]
            if key not in seen:
                seen.add(key)
                questions.append(q)

    return questions


# ================================================================
# LLM 提取（复用项目 Qwen API）
# ================================================================

def extract_by_llm(text: str, scenario: str) -> List[Dict[str, str]]:
    """
    调用 LLM 从面经文本中提取结构化面试问题

    Args:
        text: 面经文本
        scenario: 场景 ID

    Returns:
        [{"question": "...", "category": "...", "difficulty": 3}, ...]
    """
    if not text or len(text.strip()) < 50:
        return []

    # 截取前 6000 字符（API token 限制）
    text = text[:6000]

    scenario_names = {
        "job_interview": "求职面试（Java/Go/Python/前端/算法等）",
        "graduate_school": "考研复试（计算机/各专业）",
        "teacher_cert": "教师资格证面试",
        "civil_service": "公务员面试（结构化面试）",
        "mba_interview": "MBA提前面试/商学院面试",
        "ielts_speaking": "雅思口语考试",
    }
    scenario_name = scenario_names.get(scenario, scenario)

    import httpx

    headers = {
        "Authorization": f"Bearer {LLM_CONFIG['api_key']}",
        "Content-Type": "application/json",
    }

    system_prompt = f"""你是一个面试题提取专家。请从下面的面经文本中，提取出真实的面试问题。

场景：{scenario_name}

要求：
1. 只提取文本中**明确出现**的面试问题
2. 不要编造、不要泛化、不要推测
3. 如果文本中没有明确的问题，返回空数组
4. 每道题标注：问题原文、类别、难度(1-5)
5. 输出 JSON 数组格式：[{{"question":"...", "category":"...", "difficulty":3}}]

注意：
- "类别"必须是具体的：如 Java/数据库/算法/项目经历/行为面试/结构化/英语口语/专业知识
- 如果是面试复盘（面经），提取面试官实际问的问题
- 难度：1=基础 2=简单 3=中等 4=较难 5=极难"""

    payload = {
        "model": LLM_CONFIG["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"以下是面经文本，请提取面试问题：\n\n{text}"},
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    try:
        with httpx.Client(timeout=httpx.Timeout(LLM_CONFIG["timeout"])) as client:
            resp = client.post(LLM_CONFIG["api_url"], headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()

            # 尝试解析 JSON
            # 有时 LLM 会返回 markdown 代码块
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                content = json_match.group(1).strip()

            questions = json.loads(content)
            if isinstance(questions, list):
                return questions
            return []
    except Exception as e:
        print(f"    LLM 提取失败: {e}")
        return []


# ================================================================
# 主提取流程
# ================================================================

def extract_questions_from_page(
    page: dict,
    scenario: str,
    use_llm: bool = True,
) -> List[CollectedQuestion]:
    """
    从单个搜索结果页面提取面试题

    Args:
        page: 搜索结果 {"title": "...", "url": "...", "snippet": "..."}
        scenario: 场景 ID
        use_llm: 是否使用 LLM 辅助提取

    Returns:
        面试题列表
    """
    url = page["url"]
    snippet = page.get("snippet", "")
    title = page.get("title", "")

    # 1. 抓取页面
    print(f"  抓取: {url[:80]}...")
    scraped = scrape_url(url)

    if not scraped["success"]:
        print(f"    [失败] {scraped['error']}")
        # 用搜索摘要作为后备
        text = f"{title}\n{snippet}"
    else:
        text = scraped["content"]
        print(f"    内容长度: {len(text)} 字符")

    if not text or len(text) < 20:
        return []

    # 2. 规则提取
    rule_questions = extract_by_rules(text)
    print(f"    规则提取: {len(rule_questions)} 题")

    # 3. LLM 提取
    llm_questions = []
    if use_llm and EXTRACTOR_CONFIG["use_llm_extraction"]:
        llm_results = extract_by_llm(text, scenario)
        llm_questions = [r["question"] for r in llm_results if "question" in r]
        print(f"    LLM 提取: {len(llm_questions)} 题")
        time.sleep(1)  # API 调用间隔

    # 4. 合并去重
    seen = set()
    all_questions = []

    for q_text in rule_questions + llm_questions:
        key = q_text[:20]
        if key in seen:
            continue
        seen.add(key)

        # 查找对应的分类和难度（来自LLM结果）
        category = ""
        difficulty = 3
        for r in llm_results if llm_results else []:
            if r.get("question", "")[:20] == key:
                category = r.get("category", "")
                difficulty = r.get("difficulty", 3)
                break

        collected = CollectedQuestion(
            question=q_text,
            scenario=scenario,
            authenticity="real",
            source=scraped.get("platform", "web"),
            source_url=url,
            occurrence_count=1,
            category=category,
            difficulty=difficulty,
            collected_at=datetime.now().isoformat(),
        )
        all_questions.append(collected)

    return all_questions


def extract_all_pages(
    search_results: Dict[str, list],
    use_llm: bool = True,
    max_pages_per_scenario: int = 50,
) -> Dict[str, List[CollectedQuestion]]:
    """
    从所有搜索结果中提取面试题

    Args:
        search_results: {scenario: [page, ...], ...}
        use_llm: 是否使用 LLM
        max_pages_per_scenario: 每个场景最多抓取页数

    Returns:
        {scenario: [CollectedQuestion, ...], ...}
    """
    result = {}
    total_questions = 0
    total_pages = 0

    for scenario, pages in search_results.items():
        print(f"\n{'='*60}")
        print(f"提取场景: {scenario} ({len(pages)} 个页面)")
        print(f"{'='*60}")

        scenario_questions = []
        for i, page in enumerate(pages[:max_pages_per_scenario]):
            print(f"\n  [{i+1}/{min(len(pages), max_pages_per_scenario)}]")
            questions = extract_questions_from_page(page, scenario, use_llm)
            scenario_questions.extend(questions)
            total_pages += 1

            # 每个页面间隔
            time.sleep(0.5)

        print(f"\n  场景 '{scenario}' 提取完成: {len(scenario_questions)} 题")
        result[scenario] = scenario_questions
        total_questions += len(scenario_questions)

    print(f"\n{'='*60}")
    print(f"提取完成! 共处理 {total_pages} 个页面, 提取 {total_questions} 题")
    print(f"{'='*60}")
    return result
