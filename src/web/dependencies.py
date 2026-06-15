"""
共享依赖注入模块

所有 Blueprint 通过本模块获取共享资源，避免循环导入。
"""

# 这些在 create_app() 中初始化
scenario_manager = None
db = None
llm_client = None
skill_registry = None
skill_executor = None
tool_registry = None
tool_executor = None

# Skill 会话存储
SKILL_SESSIONS = {}

# 考官信息
EXAMINERS = {
    'job_interview': {'name': '张经理', 'title': '资深技术面试官 | 10年行业经验'},
    'teacher_cert': {'name': '王老师', 'title': '资深教研员 | 教龄20年'},
    'ielts_speaking': {'name': 'Mr. Smith', 'title': 'IELTS Examiner | Cambridge Certified'},
    'civil_service': {'name': '李主任', 'title': '公务员面试考官 | 8年评审经验'},
    'graduate_school': {'name': '陈教授', 'title': '研究生导师 | 博士生导师'},
    'mba_interview': {'name': '刘总监', 'title': '商学院面试官 | 企业高管'}
}

MAX_ROUNDS = 5

# 多 Agent 协作
llm_adapter = None
