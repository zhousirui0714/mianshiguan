"""页面路由 Blueprint"""
import json
from flask import Blueprint, render_template, request, redirect, url_for

from src.web import dependencies as deps

web_bp = Blueprint('web', __name__)


SIDEBAR_ITEMS = [
    {'id': 'home',      'label': '首页',       'icon': '🏠', 'url': '/'},
    {'id': 'questions', 'label': '题库中心',   'icon': '📚', 'url': '/question-bank'},
    {'id': 'learning',  'label': '学习计划',   'icon': '📅', 'url': '/learning-plan'},
    {'id': 'growth',    'label': '成长中心',   'icon': '📈', 'url': '/growth'},
    {'id': 'mock',      'label': '模拟练习',   'icon': '✍️', 'url': '/mock-exam'},
    {'id': 'badges',    'label': '成就徽章',   'icon': '🏆', 'url': '/badges'},
]

SIDEBAR_EXTRA = [
    {'id': 'settings', 'label': '设置', 'icon': '⚙️', 'url': '#'},
    {'id': 'help',     'label': '帮助中心', 'icon': '❓', 'url': '#'},
]


@web_bp.route('/')
def index():
    scenarios = deps.scenario_manager.get_all_scenarios()
    scenarios_json = json.dumps([s for s in scenarios], ensure_ascii=False)
    return render_template('index.html',
                           scenarios=scenarios, scenarios_json=scenarios_json,
                           active_page='home', sidebar_items=SIDEBAR_ITEMS,
                           sidebar_extra_nav=SIDEBAR_EXTRA)


@web_bp.route('/question-bank')
def question_bank_page():
    return render_template('questions.html',
                           active_page='questions', sidebar_items=SIDEBAR_ITEMS)


@web_bp.route('/badges')
def badges_page():
    return render_template('achievements.html',
                           active_page='badges', sidebar_items=SIDEBAR_ITEMS)


@web_bp.route('/learning-plan')
def learning_plan_page():
    return render_template('learning_plan.html',
                           active_page='learning', sidebar_items=SIDEBAR_ITEMS)


@web_bp.route('/growth')
def growth_page():
    return render_template('growth.html')


@web_bp.route('/mock-exam')
def mock_exam_page():
    return render_template('mock_exam.html',
                           active_page='mock', sidebar_items=SIDEBAR_ITEMS)


@web_bp.route('/chat/<scenario_id>')
def examiner_chat_page(scenario_id):
    scenario = deps.scenario_manager.get_scenario(scenario_id)
    if not scenario:
        return redirect(url_for('web.index'))
    return render_template('examiner_chat.html', scenario_id=scenario_id)


@web_bp.route('/result/<conversation_id>')
def interview_result_page(conversation_id):
    return render_template('interview_result.html', conversation_id=conversation_id)


@web_bp.route('/practice/<scenario_id>')
def practice(scenario_id):
    from src.scenarios.manager import MockDataGenerator

    scenario = deps.scenario_manager.get_scenario(scenario_id)
    if not scenario:
        return redirect(url_for('web.index'))

    stage = int(request.args.get('stage', 0))
    session_data = MockDataGenerator.generate_practice_session(scenario_id)
    stages = session_data['stages']
    questions = session_data['questions']

    current_stage = min(stage, len(stages) - 1)
    current_question_index = min(stage, len(questions) - 1)
    current_question = questions[current_question_index]['q']

    examiner = deps.EXAMINERS.get(scenario_id, deps.EXAMINERS['job_interview'])
    show_video = scenario_id in ['teacher_cert', 'graduate_school']

    tips = {
        'job_interview': '面试时保持自信，使用STAR法则回答行为问题，突出你的技术能力和项目经验。',
        'teacher_cert': '试讲时注意板书设计和师生互动环节，把握好时间节奏。',
        'ielts_speaking': 'Speak clearly and fluently. Use a variety of vocabulary and sentence structures.',
        'civil_service': '回答时要体现政府工作思维，注意政策理论知识的运用。',
        'graduate_school': '展示你的专业基础和科研潜力，表达清晰的学术规划。',
        'mba_interview': '突出你的职业成就和领导力，清晰表达短期和长期职业目标。'
    }

    return render_template('practice.html',
                           scenario=scenario, scenario_id=scenario_id,
                           stages=stages,
                           stages_with_index=[(s, i) for i, s in enumerate(stages)],
                           current_stage=current_stage,
                           current_question=current_question,
                           question_hint=questions[current_question_index].get('hint'),
                           examiner_name=examiner['name'],
                           examiner_title=examiner['title'],
                           show_video=show_video,
                           scenario_tips=tips.get(scenario_id, ''),
                           remaining_time='20:30', elapsed_time='03:45',
                           has_next=stage < len(stages) - 1)


@web_bp.route('/report/<scenario_id>')
def report(scenario_id):
    from src.scenarios.manager import MockDataGenerator

    scenario = deps.scenario_manager.get_scenario(scenario_id)
    if not scenario:
        return redirect(url_for('web.index'))

    report_data = MockDataGenerator.generate_practice_report(scenario_id)
    dimensions_with_index = [(d, i) for i, d in enumerate(report_data['dimensions'])]

    return render_template('report.html',
                           scenario=scenario, scenario_id=scenario_id,
                           report=report_data,
                           dimensions_with_index=dimensions_with_index,
                           practice_count=5, avg_score=82)


@web_bp.route('/auth/login')
def login():
    return render_template('login.html')


@web_bp.route('/auth/register')
def register():
    return render_template('register.html')


@web_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@web_bp.route('/interviews')
def interviews():
    return render_template('interviews.html', interviews=[])


@web_bp.route('/interviews/new')
def new_interview():
    return render_template('new_interview.html')


@web_bp.route('/questions')
def questions():
    return render_template('questions.html', categorized={})


@web_bp.route('/profile')
def profile():
    user = {
        'name': '面试达人', 'email': 'user@example.com',
        'current_position': '产品经理', 'experience_years': 3,
        'created_at': '2026-01-15', 'interview_count': 8,
        'practice_count': 15, 'streak_days': 7, 'badge_count': 5,
        'skills': {'technical': 85, 'communication': 78,
                   'projects': 82, 'adaptation': 75}
    }
    return render_template('profile.html', user=user)
