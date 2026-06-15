"""页面路由 Blueprint"""
import json
from flask import Blueprint, render_template, request, redirect, url_for

from src.web import dependencies as deps

web_bp = Blueprint('web', __name__)


_HOME_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 12l9-9 9 9"/><path d="M5 10v9a1 1 0 001 1h3v-5a1 1 0 011-1h2a1 1 0 011 1v5h3a1 1 0 001-1v-9"/></svg>'
_DOC_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
_CLOCK_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
_TREND_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>'
_EDIT_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>'
_STAR_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'
_GEAR_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>'
_HELP_SVG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'

SIDEBAR_ITEMS = [
    {'id': 'home',      'label': '首页',       'icon': _HOME_SVG, 'url': '/'},
    {'id': 'scenarios', 'label': '场景中心',   'icon': _DOC_SVG, 'url': '/scenarios'},
    {'id': 'practice',  'label': '模拟面试',   'icon': _EDIT_SVG, 'url': '/scenarios'},
    {'id': 'questions', 'label': '真题题库',   'icon': _DOC_SVG, 'url': '/question-bank'},
    {'id': 'growth',    'label': '成长中心',   'icon': _TREND_SVG, 'url': '/growth'},
]

SIDEBAR_EXTRA = [
    {'id': 'settings', 'label': '设置', 'icon': _GEAR_SVG, 'url': '#'},
    {'id': 'help',     'label': '帮助中心', 'icon': _HELP_SVG, 'url': '#'},
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


@web_bp.route('/scenarios')
def scenarios_page():
    raw = deps.scenario_manager.scenarios
    scenarios = []
    for sid, data in raw.items():
        data['id'] = sid
        scenarios.append(data)
    categories = sorted(set(s.get('category', '') for s in scenarios))
    return render_template('scenarios.html', scenarios=scenarios, categories=categories)


@web_bp.route('/growth')
def growth_page():
    return render_template('growth.html')


@web_bp.route('/mock-exam')
def mock_exam_page():
    return render_template('mock_exam.html',
                           active_page='mock', sidebar_items=SIDEBAR_ITEMS)


@web_bp.route('/setup/<scenario_id>')
def interview_setup_page(scenario_id):
    scenario = deps.scenario_manager.get_scenario(scenario_id)
    if not scenario:
        return redirect(url_for('web.index'))
    # 雅思口语不需要填写岗位/公司等求职信息，直接进入聊天
    if scenario_id == 'ielts_speaking':
        return redirect(url_for('web.ielts_chat_page'))
    return render_template('interview_setup.html',
                           scenario_id=scenario_id,
                           scenario_name=scenario.get('name', '面试'))


@web_bp.route('/chat/<scenario_id>')
def examiner_chat_page(scenario_id):
    scenario = deps.scenario_manager.get_scenario(scenario_id)
    if not scenario:
        return redirect(url_for('web.index'))
    return render_template('examiner_chat.html', scenario_id=scenario_id)


@web_bp.route('/result/<conversation_id>')
def interview_result_page(conversation_id):
    return render_template('interview_result.html', conversation_id=conversation_id)


@web_bp.route('/ielts-chat')
def ielts_chat_page():
    """雅思口语实时语音考试页面"""
    return render_template('ielts_chat.html')


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
    db_info = {
        'use_pg': deps.db.use_pg,
        'db_type': 'PostgreSQL (Supabase)' if deps.db.use_pg else 'SQLite（本地临时存储）',
        'pg_error': getattr(deps.db, 'pg_error', None),
    }
    return render_template('login.html', db_info=db_info)


@web_bp.route('/auth/register')
def register():
    return render_template('register.html')


@web_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@web_bp.route('/interviews')
def interviews():
    """面试记录列表 — 展示用户所有历史面试会话"""
    from flask import session
    import json as _json

    uid = session.get('user_id')
    interviews = []

    if uid:
        try:
            convs = deps.db.get_user_conversations(uid)
            for c in (convs or []):
                # 提取岗位和公司信息
                bg = c.get('user_background', '') or ''
                position = ''
                company = ''
                for line in bg.split('\n'):
                    line = line.strip()
                    if line.startswith('目标岗位：'):
                        position = line.replace('目标岗位：', '').strip()
                    elif line.startswith('目标公司：'):
                        company = line.replace('目标公司：', '').strip()

                # 解析报告数据
                report = {}
                raw = c.get('report_data', '{}')
                if isinstance(raw, str) and raw.strip():
                    try:
                        report = _json.loads(raw)
                    except _json.JSONDecodeError:
                        pass
                elif isinstance(raw, dict):
                    report = raw

                # 统计消息轮数
                msgs = c.get('messages', []) or []
                user_msgs = [m for m in msgs if m.get('role') == 'user']
                round_count = len(user_msgs)

                # 场景名称映射
                scenario_map = {
                    'job_interview': '💼 求职面试',
                    'teacher_cert': '📚 教资面试',
                    'ielts_speaking': '🗣️ 雅思口语',
                    'civil_service': '🏛️ 公务员面试',
                    'graduate_school': '🎓 考研复试',
                    'mba_interview': '💎 MBA面试',
                }
                scenario_display = scenario_map.get(
                    c.get('scenario_id', ''), c.get('scenario_name', '模拟面试')
                )

                interviews.append({
                    'id': c.get('id', ''),
                    'scenario': scenario_display,
                    'position': position or '未指定岗位',
                    'company': company or '',
                    'status': c.get('status', 'active'),
                    'round_count': round_count,
                    'created_at': (c.get('created_at') or '')[:10] if c.get('created_at') else '',
                    'overall_score': report.get('overall_score'),
                    'passed': report.get('passed', False),
                    'new_badges': len(report.get('new_badges', [])) if isinstance(report.get('new_badges'), list) else 0,
                })
        except Exception as e:
            print(f"[interviews] 加载面试记录失败: {e}")

    return render_template('interviews.html', interviews=interviews, active_nav='interviews')


@web_bp.route('/interviews/new')
def new_interview():
    return render_template('new_interview.html')


@web_bp.route('/questions')
def questions():
    return render_template('questions.html', categorized={})


@web_bp.route('/profile')
def profile():
    from flask import g
    user = None

    if g.get('current_user'):
        uid = g.current_user['id']
        # 获取用户基础信息
        user = deps.db.get_user(uid)
        if user:
            user['name'] = user.get('username', '')
            # 获取统计数据
            try:
                summary = deps.db.get_user_summary(uid)
                user['interview_count'] = deps.db.get_user_conversations(uid)
                user['interview_count'] = len(user['interview_count']) if isinstance(user['interview_count'], list) else 0
                user['practice_count'] = summary.get('total_practices', 0)
                user['streak_days'] = deps.db.get_user_streak(uid)
                user['badge_count'] = summary.get('total_badges', 0)
            except Exception:
                user['practice_count'] = 0
                user['streak_days'] = 0
                user['badge_count'] = 0
                user['interview_count'] = 0

            # 获取最近一次面试的背景信息
            try:
                convs = deps.db.get_user_conversations(uid)
                if convs:
                    latest = convs[0]
                    bg = latest.get('user_background', '')
                    for line in bg.split('\n'):
                        line = line.strip()
                        if line.startswith('目标岗位：'):
                            user['current_position'] = line.replace('目标岗位：', '')
                if 'current_position' not in user:
                    user['current_position'] = '未设置'
            except Exception:
                user['current_position'] = '未设置'

            if 'experience_years' not in user:
                user['experience_years'] = 0

            # 获取真实维度评分（从最近面试报告）
            try:
                dims = deps.db.get_dimension_trend(uid)
                skill_scores = {}
                if dims:
                    # 取每个维度的最新分数
                    for d in dims:
                        name = d.get('dimension_name', '')
                        score = d.get('score', 0)
                        if name and score:
                            skill_scores[name] = round(score, 1)
                user['skill_scores'] = skill_scores
            except Exception:
                user['skill_scores'] = {}

    if not user:
        # 未登录时使用游客数据
        user = {
            'name': '游客', 'email': '',
            'current_position': '未设置', 'experience_years': 0,
            'created_at': '', 'interview_count': 0,
            'practice_count': 0, 'streak_days': 0, 'badge_count': 0,
        }

    return render_template('profile.html', user=user)
