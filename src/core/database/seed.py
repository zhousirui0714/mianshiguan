"""默认数据填充"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.database import DatabaseManager

# 场景 ID 映射（与 Skill 系统 YAML 配置保持一致）
SCENARIO_IDS = {
    "job_interview": "求职面试",
    "teacher_cert": "教资面试",
    "ielts_speaking": "雅思口语",
    "civil_service": "公务员面试",
    "graduate_school": "考研复试",
    "mba_interview": "MBA面试",
}


def seed_scenarios(db: "DatabaseManager") -> None:
    """填充场景数据"""
    for sid, sname in SCENARIO_IDS.items():
        db.create_scenario(sid, sname)


def seed_questions(db: "DatabaseManager") -> None:
    """填充预置题库"""
    questions = [
        # 求职面试
        ("job_interview", "自我介绍", 2, "请做一个简短的自我介绍。",
         "自我介绍应包含：1. 基本信息；2. 核心技能和优势；3. 职业目标。"),
        ("job_interview", "专业技能", 4, "请介绍一下你最熟悉的技术栈，并举例说明在项目中的应用。",
         "应：1. 清晰说明技术栈；2. 结合具体项目案例；3. 说明解决的问题和取得的成果。"),
        ("job_interview", "项目经验", 4, "请描述一个你负责的最有挑战性的项目。",
         "建议使用STAR法则：Situation-Task-Action-Result。"),
        ("job_interview", "应变能力", 3, "如果你与同事意见不合，你会如何处理？",
         "考察沟通协调能力，应展示倾听、寻求共识的能力。"),
        ("job_interview", "职业规划", 3, "你的职业规划是什么？为什么选择我们公司？",
         "展示对行业和自身发展的思考，表达对公司的了解和认同。"),

        # 教资面试
        ("teacher_cert", "教育理念", 3, "你认为一名优秀的教师应该具备哪些素质？",
         "1. 专业知识；2. 沟通能力；3. 爱心和耐心；4. 创新教学方法。"),
        ("teacher_cert", "课堂管理", 4, "如果课堂上学生突然吵闹，你会如何处理？",
         "1. 保持冷静；2. 使用非语言信号；3. 课后沟通；4. 建立课堂规则。"),
        ("teacher_cert", "教学设计", 4, "如何设计一堂生动有趣的课？",
         "1. 明确教学目标；2. 多样化教学方法；3. 互动环节；4. 课堂小结。"),

        # 雅思口语
        ("ielts_speaking", "个人经历", 2, "Describe a book that you enjoyed reading.",
         "Part 2话题。包含：书名、内容、阅读时间、喜欢的原因。"),
        ("ielts_speaking", "观点表达", 4, "Do you agree that technology is making people more isolated?",
         "Part 3话题。结构化回答：观点+举例+反方+总结。"),

        # 公务员面试
        ("civil_service", "综合分析", 4, "谈谈你对'空谈误国，实干兴邦'的理解。",
         "1. 解释含义；2. 结合实际；3. 联系自身；4. 说明如何践行。"),
        ("civil_service", "应急处理", 5, "如果你遇到群体性事件该如何处理？",
         "1. 保持冷静；2. 倾听诉求；3. 及时上报；4. 依法处理。"),

        # 考研复试
        ("graduate_school", "专业基础", 4, "请简述你所学专业的主要研究方向和前沿动态。",
         "1. 清晰阐述专业领域；2. 介绍主要研究方向；3. 列举前沿成果。"),
        ("graduate_school", "科研能力", 5, "如果你被录取，你的研究计划是什么？",
         "1. 研究目标；2. 研究方法；3. 创新点；4. 预期成果。"),

        # MBA面试
        ("mba_interview", "领导力", 4, "请举例说明你在团队中的领导经历。",
         "使用STAR法则，展示领导力和决策能力。"),
        ("mba_interview", "职业规划", 3, "为什么要读MBA？对你有什么帮助？",
         "1. 职业瓶颈；2. MBA价值；3. 具体目标。"),
    ]

    count = 0
    for scenario_id, category, diff, question, answer in questions:
        result = db.add_question(scenario_id, category, diff, question, answer,
                                  tags=[category])
        if result["success"]:
            count += 1
    print(f"[Seed] 已填充 {count} 道题目")


def seed_badges(db: "DatabaseManager") -> None:
    """填充徽章数据"""
    badges = [
        ("badge_001", "初试啼声", "完成第一次模拟练习", "🐣", "newbie",
         {"type": "first_practice"}, "common"),
        ("badge_002", "首战告捷", "首次练习得分80以上", "🎯", "newbie",
         {"type": "first_high_score", "threshold": 80}, "rare"),
        ("badge_003", "认真学习", "完成5道题目", "📚", "newbie",
         {"type": "total_practices", "count": 5}, "common"),
        ("badge_004", "持之以恒", "完成10次练习", "💪", "persistence",
         {"type": "total_practices", "count": 10}, "rare"),
        ("badge_007", "求职达人", "求职面试得分90以上", "🎤", "scenario",
         {"type": "scenario_high_score", "scenario": "job_interview", "threshold": 90}, "epic"),
        ("badge_008", "教资通关", "教资面试完成3次", "🍎", "scenario",
         {"type": "scenario_practices", "scenario": "teacher_cert", "count": 3}, "rare"),
        ("badge_009", "雅思突破", "雅思口语完成5次", "🌍", "scenario",
         {"type": "scenario_practices", "scenario": "ielts_speaking", "count": 5}, "epic"),
        ("badge_012", "全能选手", "所有场景各完成1次", "🎭", "special",
         {"type": "all_scenarios"}, "legendary"),
    ]

    count = 0
    for badge_id, name, desc, icon, category, condition, rarity in badges:
        result = db.add_badge(badge_id, name, desc, icon, category, condition, rarity)
        if result["success"]:
            count += 1
    print(f"[Seed] 已填充 {count} 个徽章")
