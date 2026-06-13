"""
为非 ICT 行业生成面试题并导入题库
用法: python scripts/generate_industry_questions.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()
import httpx

LLM_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

INDUSTRIES = {
    "healthcare": {
        "name": "医疗健康",
        "companies": ["协和医院", "华西医院", "瑞金医院", "中山医院"],
        "positions": ["临床医生", "护士", "药剂师", "医学研究员", "医疗管理"],
        "topics": ["临床知识", "医患沟通", "病例分析", "医疗伦理", "公共卫生"],
        "count": 15,
    },
    "finance": {
        "name": "金融投资",
        "companies": ["中金公司", "中信证券", "招商银行", "普华永道"],
        "positions": ["金融分析师", "投资顾问", "会计师", "风险管理", "投行分析师"],
        "topics": ["财务分析", "投资策略", "风险管理", "估值模型", "客户沟通"],
        "count": 15,
    },
    "legal": {
        "name": "法律法务",
        "companies": ["金杜律所", "中伦律所", "君合律所"],
        "positions": ["律师", "法务专员", "合规专员", "知识产权顾问"],
        "topics": ["民商法", "合同法", "公司法", "诉讼实务", "法律文书"],
        "count": 12,
    },
    "architecture": {
        "name": "建筑地产",
        "companies": ["中建集团", "万科地产", "保利发展", "同济设计院"],
        "positions": ["建筑设计师", "土木工程师", "结构工程师", "项目经理"],
        "topics": ["建筑设计", "施工管理", "城市规划", "绿色建筑", "项目协调"],
        "count": 12,
    },
    "fmcg": {
        "name": "快消零售",
        "companies": ["宝洁", "联合利华", "雀巢", "京东", "欧莱雅"],
        "positions": ["品牌经理", "市场营销", "销售经理", "供应链管理"],
        "topics": ["品牌管理", "渠道策略", "消费者洞察", "供应链管理", "数据分析"],
        "count": 15,
    },
    "hr": {
        "name": "人力资源",
        "companies": ["华为", "宝洁", "万科", "美的", "招商银行"],
        "positions": ["HRBP", "招聘经理", "薪酬福利", "组织发展", "培训经理"],
        "topics": ["招聘面试", "绩效管理", "员工关系", "组织发展", "劳动法"],
        "count": 12,
    },
    "education": {
        "name": "教育培训",
        "companies": ["新东方", "好未来", "中公教育", "作业帮"],
        "positions": ["课程顾问", "教学主管", "教研员", "学科教师", "留学顾问"],
        "topics": ["教学设计", "学情分析", "家校沟通", "教育理念", "学生心理"],
        "count": 12,
    },
    "media": {
        "name": "文化传媒",
        "companies": ["新华社", "抖音", "小红书", "B站", "奥美广告"],
        "positions": ["记者", "编辑", "内容运营", "新媒体运营", "品牌策划"],
        "topics": ["内容创作", "选题策划", "媒体伦理", "用户增长", "品牌传播"],
        "count": 12,
    },
}

PROMPT = """Generate {count} high-quality interview questions for "{position}" position in the {industry} industry.

Reference companies: {companies}
Topic areas: {topics}

Each question should cover at least one of:
- Self-introduction & motivation
- Professional knowledge & skills
- Case analysis / scenario handling
- Behavioral questions (teamwork, stress, etc.)
- Industry awareness & career planning

Requirements:
1. Some questions should mention real company names for authenticity
2. Each question must include: question text, reference answer (100-200 words), difficulty (1-5)
3. Mix of difficulty levels: easy (intro/motivation), medium (knowledge), hard (case analysis)

Output strictly as JSON array (in English, with Chinese company names preserved):
[
  {{
    "question": "Interview question in Chinese",
    "answer": "Reference answer in Chinese (100-200 chars)",
    "difficulty": 3,
    "category": "Category name in Chinese",
    "company": "Company name or empty",
    "position": "{position}"
  }}
]"""


def generate_questions(industry, position, companies, topics, count):
    prompt = PROMPT.format(
        industry=industry, position=position, count=count,
        companies=", ".join(companies), topics=", ".join(topics),
    )
    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "You are a senior HR interviewer expert. Output strictly valid JSON array. Questions and answers should be in Chinese. Company names should be in Chinese."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 4000,
    }
    try:
        with httpx.Client(timeout=httpx.Timeout(90)) as client:
            r = client.post(LLM_API_URL, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"].strip()
                start = content.find("[")
                end = content.rfind("]") + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
                return json.loads(content)
            return []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def import_questions(db, questions, position, company_default):
    count = 0
    for q in questions:
        if not isinstance(q, dict) or not q.get("question"):
            continue
        q_text = q["question"].strip()
        answer = q.get("answer", q.get("reference_answer", "")).strip()
        difficulty = int(q.get("difficulty", 3))
        category = q.get("category", "industry")
        company = q.get("company", "") or company_default or ""
        result = db.add_question(
            scenario_id="job_interview", category=category, difficulty=difficulty,
            question_text=q_text, reference_answer=answer,
            tags=[category] if category else [],
            company=company, position=position, source="industry_questions",
            year="2025", source_type="ai_generated", question_level="A",
            interview_stage="basic",
        )
        if result["success"]:
            count += 1
    return count


def main():
    if not LLM_API_KEY or LLM_API_KEY == "your-api-key":
        print("Error: DEEPSEEK_API_KEY not set in .env")
        return

    os.environ.pop("SUPABASE_DB_URL", None)
    from src.core.database import DatabaseManager
    db = DatabaseManager()

    before = len(db.get_questions())
    print(f"Current questions: {before}")
    total_added = 0

    for key, cfg in INDUSTRIES.items():
        name = cfg["name"]
        companies = cfg["companies"]
        per_pos = max(3, cfg["count"] // len(cfg["positions"]))
        print(f"\n>>> {name} ({key})")
        for pos in cfg["positions"]:
            print(f"  {pos} ({per_pos}q)...", end=" ", flush=True)
            qs = generate_questions(name, pos, companies, cfg["topics"], per_pos)
            if qs:
                n = import_questions(db, qs, pos, companies[0])
                print(f"OK: {n}")
                total_added += n
            else:
                print("FAIL")
            time.sleep(1.5)

    after = len(db.get_questions())
    print(f"\nDone! +{total_added} (total: {before} -> {after})")


if __name__ == "__main__":
    main()
