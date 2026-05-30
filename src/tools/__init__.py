"""
工具初始化入口

调用 init_tools() 注册所有预置工具。
新增场景的工具只需在这里添加。
"""

from src.core.tool import registry as tool_registry
from src.core.tool.types import ToolDefinition, ToolParameter

# 导入工具实现
from .job_interview_tools import (
    ResumeAnalyzerTool, STARQuestionGeneratorTool, TechDepthCheckerTool
)
from .teacher_cert_tools import (
    LessonPlanScorerTool, BlackboardDesignCheckerTool, TeachingMethodEvaluatorTool
)
from .ielts_tools import (
    PronunciationAnalyzerTool, VocabularyCheckerTool, GrammarCheckerTool
)
from .civil_service_tools import (
    PolicyKnowledgeCheckerTool, EmergencyResponseScorerTool, DocumentWritingEvaluatorTool
)
from .graduate_tools import (
    ResearchProposalEvaluatorTool, LiteratureReviewCheckerTool, AcademicExpressionCheckerTool
)
from .mba_tools import (
    LeadershipAnalyzerTool, CareerPlanEvaluatorTool, CaseAnalysisScorerTool
)


def init_tools() -> int:
    """初始化并注册所有工具"""
    count = 0

    # ===== 求职面试工具 =====
    tools_job = [
        ResumeAnalyzerTool(ToolDefinition(
            id="resume-analyzer",
            name="简历分析",
            description="分析用户简历的关键信息，提取技能、经验和亮点",
            category="analysis",
            skill_ids=["job-interview"],
            parameters=[
                ToolParameter(name="resume_text", type="string", description="简历文本"),
            ],
        )),
        STARQuestionGeneratorTool(ToolDefinition(
            id="star-question-generator",
            name="STAR 问题生成",
            description="根据用户项目经历，生成 STAR 法则追问问题",
            category="question",
            skill_ids=["job-interview"],
            parameters=[
                ToolParameter(name="project_description", type="string", description="项目描述"),
                ToolParameter(name="focus_area", type="string", description="关注方向", required=False,
                              enum=["challenge", "contribution", "result", "teamwork"]),
            ],
        )),
        TechDepthCheckerTool(ToolDefinition(
            id="tech-depth-checker",
            name="技术深度检查",
            description="评估用户对某项技术的掌握深度",
            category="evaluation",
            skill_ids=["job-interview"],
            parameters=[
                ToolParameter(name="tech_stack", type="string", description="技术栈名称"),
                ToolParameter(name="user_description", type="string", description="用户对该技术的描述"),
            ],
        )),
    ]
    for t in tools_job:
        tool_registry.register(t)
        count += 1

    # ===== 教资面试工具 =====
    tools_teacher = [
        LessonPlanScorerTool(ToolDefinition(
            id="lesson-plan-scorer",
            name="教案评分",
            description="评估教案设计的完整性和合理性",
            category="evaluation",
            skill_ids=["teacher-cert"],
            parameters=[
                ToolParameter(name="lesson_plan", type="string", description="教案内容"),
                ToolParameter(name="subject", type="string", description="学科", required=False),
            ],
        )),
        BlackboardDesignCheckerTool(ToolDefinition(
            id="blackboard-checker",
            name="板书设计检查",
            description="检查板书设计的结构、逻辑和视觉效果",
            category="evaluation",
            skill_ids=["teacher-cert"],
            parameters=[
                ToolParameter(name="board_design", type="string", description="板书设计描述"),
            ],
        )),
        TeachingMethodEvaluatorTool(ToolDefinition(
            id="teaching-method-evaluator",
            name="教学方法评估",
            description="评估教学方法的多样性和有效性",
            category="evaluation",
            skill_ids=["teacher-cert"],
            parameters=[
                ToolParameter(name="method_description", type="string", description="教学方法描述"),
                ToolParameter(name="student_level", type="string", description="学生水平",
                              enum=["elementary", "middle", "high", "college"]),
            ],
        )),
    ]
    for t in tools_teacher:
        tool_registry.register(t)
        count += 1

    # ===== 雅思口语工具 =====
    tools_ielts = [
        PronunciationAnalyzerTool(ToolDefinition(
            id="pronunciation-analyzer",
            name="发音分析",
            description="分析英语发音的准确度、流利度和语调",
            category="analysis",
            skill_ids=["ielts-speaking"],
            parameters=[
                ToolParameter(name="speech_text", type="string", description="口语文本"),
                ToolParameter(name="ipa_transcription", type="string", description="音标标注", required=False),
            ],
        )),
        VocabularyCheckerTool(ToolDefinition(
            id="vocabulary-checker",
            name="词汇检查",
            description="检查词汇多样性、准确性和高级词汇使用",
            category="analysis",
            skill_ids=["ielts-speaking"],
            parameters=[
                ToolParameter(name="user_response", type="string", description="用户回答文本"),
                ToolParameter(name="topic", type="string", description="话题"),
            ],
        )),
        GrammarCheckerTool(ToolDefinition(
            id="grammar-checker",
            name="语法检查",
            description="检查语法错误的类型和频率",
            category="analysis",
            skill_ids=["ielts-speaking"],
            parameters=[
                ToolParameter(name="user_response", type="string", description="用户回答文本"),
            ],
        )),
    ]
    for t in tools_ielts:
        tool_registry.register(t)
        count += 1

    # ===== 公务员面试工具 =====
    tools_civil = [
        PolicyKnowledgeCheckerTool(ToolDefinition(
            id="policy-checker",
            name="政策理论检查",
            description="评估回答中的政策理论运用是否准确",
            category="evaluation",
            skill_ids=["civil-service"],
            parameters=[
                ToolParameter(name="user_answer", type="string", description="用户回答"),
                ToolParameter(name="policy_area", type="string", description="政策领域",
                              enum=["economy", "society", "culture", "ecology", "governance"]),
            ],
        )),
        EmergencyResponseScorerTool(ToolDefinition(
            id="emergency-scorer",
            name="应急处理评分",
            description="评估应急处理方案的合理性、全面性和可操作性",
            category="evaluation",
            skill_ids=["civil-service"],
            parameters=[
                ToolParameter(name="scenario", type="string", description="突发事件场景描述"),
                ToolParameter(name="user_solution", type="string", description="用户提出的解决方案"),
            ],
        )),
        DocumentWritingEvaluatorTool(ToolDefinition(
            id="document-evaluator",
            name="公文写作评估",
            description="评估公文写作的格式规范性、内容完整性和语言得体性",
            category="evaluation",
            skill_ids=["civil-service"],
            parameters=[
                ToolParameter(name="document_type", type="string", description="公文类型",
                              enum=["notice", "report", "plan", "summary", "proposal"]),
                ToolParameter(name="content", type="string", description="公文内容"),
            ],
        )),
    ]
    for t in tools_civil:
        tool_registry.register(t)
        count += 1

    # ===== 考研复试工具 =====
    tools_graduate = [
        ResearchProposalEvaluatorTool(ToolDefinition(
            id="research-proposal-evaluator",
            name="研究计划评估",
            description="评估研究计划的可行性、创新性和学术价值",
            category="evaluation",
            skill_ids=["graduate-school"],
            parameters=[
                ToolParameter(name="research_plan", type="string", description="研究计划"),
                ToolParameter(name="field", type="string", description="研究领域"),
            ],
        )),
        LiteratureReviewCheckerTool(ToolDefinition(
            id="literature-review-checker",
            name="文献综述检查",
            description="评估文献综述的全面性和分析深度",
            category="evaluation",
            skill_ids=["graduate-school"],
            parameters=[
                ToolParameter(name="review_text", type="string", description="文献综述内容"),
                ToolParameter(name="field", type="string", description="研究领域"),
            ],
        )),
        AcademicExpressionCheckerTool(ToolDefinition(
            id="academic-expression-checker",
            name="学术表达检查",
            description="检查学术表达的规范性、逻辑性和专业性",
            category="analysis",
            skill_ids=["graduate-school"],
            parameters=[
                ToolParameter(name="text", type="string", description="学术文本"),
            ],
        )),
    ]
    for t in tools_graduate:
        tool_registry.register(t)
        count += 1

    # ===== MBA 面试工具 =====
    tools_mba = [
        LeadershipAnalyzerTool(ToolDefinition(
            id="leadership-analyzer",
            name="领导力分析",
            description="分析用户展现的领导力特质和风格",
            category="analysis",
            skill_ids=["mba-interview"],
            parameters=[
                ToolParameter(name="experience_description", type="string", description="领导经历描述"),
            ],
        )),
        CareerPlanEvaluatorTool(ToolDefinition(
            id="career-plan-evaluator",
            name="职业规划评估",
            description="评估职业规划的清晰度、合理性和可行性",
            category="evaluation",
            skill_ids=["mba-interview"],
            parameters=[
                ToolParameter(name="career_goal", type="string", description="职业目标"),
                ToolParameter(name="current_status", type="string", description="当前职业状态"),
                ToolParameter(name="mba_expectation", type="string", description="对 MBA 的期望"),
            ],
        )),
        CaseAnalysisScorerTool(ToolDefinition(
            id="case-analysis-scorer",
            name="案例分析评分",
            description="评估商业案例分析的深度、逻辑和创新性",
            category="evaluation",
            skill_ids=["mba-interview"],
            parameters=[
                ToolParameter(name="case_description", type="string", description="案例描述"),
                ToolParameter(name="user_analysis", type="string", description="用户的分析"),
            ],
        )),
    ]
    for t in tools_mba:
        tool_registry.register(t)
        count += 1

    print(f"[Tools] 完成: 共注册 {count} 个 Tool")
    return count
