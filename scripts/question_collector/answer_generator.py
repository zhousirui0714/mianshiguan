"""
答案生成模块 - 为每道题生成3个级别的答案

使用项目已有的 Qwen API 生成符合真实面试场景的答案。

级别：
- 基础（60分）：回答基本正确，但缺乏深度和细节
- 良好（80分）：回答充分，有具体例子，结构完整
- 高分（95分）：回答出色，有深度洞察，表达专业
"""

import json
import re
import time
from typing import List, Optional

import httpx

from .schema import CollectedQuestion
from .config import LLM_CONFIG


def generate_answers(
    question: CollectedQuestion,
    max_retries: int = 2,
) -> CollectedQuestion:
    """
    为单道题生成 3 个级别的答案

    如果 API 调用失败，保留空字符串（可后续单独补充）。
    """
    scenario_names = {
        "job_interview": "求职技术面试",
        "teacher_cert": "教师资格证面试",
        "civil_service": "公务员结构化面试",
        "graduate_school": "考研复试面试",
        "mba_interview": "MBA商学院面试",
        "ielts_speaking": "雅思口语考试",
    }
    scenario_name = scenario_names.get(question.scenario, question.scenario)

    prompt = f"""你是一位资深的{scenario_name}面试辅导专家。请为以下面试题生成3个级别的回答。

面试题：{question.question}
所属类别：{question.category}
难度等级：{question.difficulty}/5

要求：
1. 三个级别分别为：基础回答(60分)、良好回答(80分)、高分回答(95分)
2. 回答要符合真实面试场景的表达方式，不要像AI作文
3. 基础回答控制在1分钟，良好回答1-2分钟，高分回答2-3分钟
4. 使用真实面试者会用的语言，包括适当的语气词、停顿自然
5. 不使用过于华丽的词汇

输出JSON格式：
{{
    "basic": {{
        "answer": "基础回答内容...",
        "duration_seconds": 60
    }},
    "good": {{
        "answer": "良好回答内容...",
        "duration_seconds": 90
    }},
    "excellent": {{
        "answer": "高分回答内容...",
        "duration_seconds": 150
    }}
}}"""

    headers = {
        "Authorization": f"Bearer {LLM_CONFIG['api_key']}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": LLM_CONFIG["model"],
        "messages": [
            {
                "role": "system",
                "content": f"你是{scenario_name}面试辅导专家，擅长根据真实面试场景提供不同水平的示范回答。回答要自然、真实、有层次。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 3000,
    }

    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=httpx.Timeout(LLM_CONFIG["timeout"])) as client:
                resp = client.post(LLM_CONFIG["api_url"], headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()

                # 提取 JSON
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
                if json_match:
                    content = json_match.group(1).strip()
                result = json.loads(content)

                question.answer_basic = result.get("basic", {}).get("answer", "")
                question.answer_good = result.get("good", {}).get("answer", "")
                question.answer_excellent = result.get("excellent", {}).get("answer", "")
                return question

        except Exception as e:
            if attempt < max_retries:
                wait = (attempt + 1) * 5
                print(f"    重试 {attempt + 1}/{max_retries}: {e}")
                time.sleep(wait)
            else:
                print(f"    [失败] 答案生成失败: {e}")

    return question


def generate_all_answers(
    questions: List[CollectedQuestion],
    max_questions: int = 100,
) -> List[CollectedQuestion]:
    """
    批量生成答案

    Args:
        questions: 题目列表
        max_questions: 每次最多生成答案的题数（API 有调用限制）

    Returns:
        包含答案的题目列表
    """
    result = []
    total = min(len(questions), max_questions)

    print(f"\n{'='*60}")
    print(f"开始生成答案: {total} 题")
    print(f"{'='*60}")

    for i, q in enumerate(questions[:max_questions]):
        print(f"  [{i+1}/{total}] {q.question[:40]}...")
        updated = generate_answers(q)
        result.append(updated)
        # API 调用间隔
        time.sleep(1.5)

    print(f"\n答案生成完成: {len(result)} 题")
    return result + questions[max_questions:]
