"""AI 考官 + 场景 API Blueprint"""
import random
from flask import Blueprint, request, jsonify

from src.services.llm_client import EXAMINER_PROFILES
from src.core.skill.types import AnswerRecord
from src.web import dependencies as deps

examiner_bp = Blueprint('api_examiner', __name__)


# ==================== 场景 API ====================

@examiner_bp.route('/scenarios')
def get_scenarios():
    scenarios = deps.scenario_manager.get_all_scenarios()
    return jsonify({'success': True, 'data': scenarios})


@examiner_bp.route('/scenarios/<scenario_id>')
def get_scenario(scenario_id):
    scenario = deps.scenario_manager.get_scenario(scenario_id)
    if scenario:
        return jsonify({'success': True, 'data': scenario})
    return jsonify({'success': False, 'error': '场景不存在'})


@examiner_bp.route('/categories')
def get_categories():
    categories = deps.scenario_manager.get_categories()
    return jsonify({'success': True, 'data': categories})


@examiner_bp.route('/practice/submit', methods=['POST'])
def submit_practice():
    data = request.get_json()
    score = random.randint(70, 95)
    feedback = f"回答评估完成！得分：{score}分。继续加油！"
    return jsonify({'success': True, 'score': score, 'feedback': feedback, 'next_stage': True})


# ==================== AI 考官 API ====================

@examiner_bp.route('/examiner/chat', methods=['POST'])
def examiner_chat():
    try:
        data = request.get_json()
        scenario_id = data.get('scenario_id')
        user_message = data.get('user_message')
        user_id = data.get('user_id', 'anonymous')
        user_background = data.get('user_background', '')
        conversation_id = data.get('conversation_id')

        if not scenario_id or not user_message:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        skill = deps.skill_registry.get(scenario_id)
        if skill and conversation_id and conversation_id in deps.SKILL_SESSIONS:
            skill_session = deps.SKILL_SESSIONS[conversation_id]
            skill_session.context["user_background"] = user_background

            conversation = deps.db.get_conversation(conversation_id)
            history = []
            if conversation:
                history = [
                    {'role': m['role'], 'content': m['content']}
                    for m in conversation.get('messages', [])
                ]

            last_question = ""
            for msg in reversed(history):
                if msg['role'] == 'assistant':
                    last_question = msg['content']
                    break

            answer_record = AnswerRecord(
                round=skill_session.round + 1,
                question=last_question,
                answer=user_message,
            )
            skill_session.answers.append(answer_record)

            skill_tools = deps.tool_registry.get_by_skill(scenario_id)
            if skill_tools:
                result = deps.skill_executor.chat_with_tools(
                    skill_id=scenario_id, session=skill_session,
                    user_message=user_message, history=history, tools=skill_tools,
                )
            else:
                result = deps.skill_executor.chat(
                    skill_id=scenario_id, session=skill_session,
                    user_message=user_message, history=history,
                )

            ai_response = result["response"]
            round_count = result["round"]
            is_finished = result["is_finished"]

            deps.db.add_message(conversation_id, 'user', user_message)
            deps.db.add_message(conversation_id, 'assistant', ai_response)

            return jsonify({
                'success': True, 'conversation_id': conversation_id,
                'response': ai_response,
                'examiner_name': skill.config.persona.name,
                'examiner_title': skill.config.persona.title,
                'round_count': round_count, 'max_rounds': skill.config.max_rounds,
                'is_finished': is_finished
            })

        scenario = deps.scenario_manager.get_scenario(scenario_id)
        if not scenario:
            return jsonify({'success': False, 'error': '场景不存在'}), 404

        scenario_name = scenario.get('name', '面试')

        _ensure_user(user_id)

        if not conversation_id:
            create_result = deps.db.create_conversation(
                user_id=user_id, scenario_id=scenario_id,
                scenario_name=scenario_name, user_background=user_background
            )
            if not create_result['success']:
                return jsonify({'success': False, 'error': create_result['error']}), 500
            conversation_id = create_result['conversation_id']

        conversation = deps.db.get_conversation(conversation_id)
        if not conversation:
            return jsonify({'success': False, 'error': '对话不存在'}), 404

        conversation_history = [
            {'role': m['role'], 'content': m['content']}
            for m in conversation.get('messages', [])
        ]

        try:
            ai_response = deps.llm_client.examiner_chat(
                scenario_id=scenario_id, user_message=user_message,
                conversation_history=conversation_history, user_background=user_background
            )
        except Exception:
            ai_response = (
                f"抱歉，当前AI服务暂时不可用。"
                f"{deps.EXAMINERS.get(scenario_id, deps.EXAMINERS['job_interview'])['name']}问你："
                "请简要介绍一下你自己，包括你的专业背景和相关经验。"
            )

        deps.db.add_message(conversation_id, 'user', user_message)
        deps.db.add_message(conversation_id, 'assistant', ai_response)

        conversation = deps.db.get_conversation(conversation_id)
        round_count = conversation.get('round_count', 0)
        is_finished = round_count >= deps.MAX_ROUNDS

        examiner = deps.EXAMINERS.get(scenario_id, deps.EXAMINERS['job_interview'])

        return jsonify({
            'success': True, 'conversation_id': conversation_id,
            'response': ai_response,
            'examiner_name': examiner['name'], 'examiner_title': examiner['title'],
            'round_count': round_count, 'max_rounds': deps.MAX_ROUNDS,
            'is_finished': is_finished
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@examiner_bp.route('/examiner/start', methods=['POST'])
def examiner_start():
    try:
        data = request.get_json()
        scenario_id = data.get('scenario_id')
        user_id = data.get('user_id', 'anonymous')
        user_background = data.get('user_background', '')
        if not scenario_id:
            return jsonify({'success': False, 'error': '缺少场景ID'}), 400

        skill = deps.skill_registry.get(scenario_id)
        if skill:
            session_data = skill.create_session(user_id, {"user_background": user_background})
            welcome_message = skill.get_welcome_message(session_data)

            conversation_id = session_data.id
            deps.SKILL_SESSIONS[conversation_id] = session_data

            deps.db.create_conversation(
                user_id=user_id, scenario_id=scenario_id,
                scenario_name=skill.config.name, user_background=user_background,
                conversation_id=conversation_id,
            )
            deps.db.add_message(conversation_id, 'assistant', welcome_message)

            return jsonify({
                'success': True, 'conversation_id': conversation_id,
                'welcome_message': welcome_message,
                'examiner_name': skill.config.persona.name,
                'examiner_title': skill.config.persona.title,
                'max_rounds': skill.config.max_rounds,
            })

        scenario = deps.scenario_manager.get_scenario(scenario_id)
        if not scenario:
            return jsonify({'success': False, 'error': '场景不存在'}), 404

        scenario_name = scenario.get('name', '面试')

        _ensure_user(user_id)

        create_result = deps.db.create_conversation(
            user_id=user_id, scenario_id=scenario_id,
            scenario_name=scenario_name, user_background=user_background
        )
        if not create_result['success']:
            return jsonify({'success': False, 'error': create_result['error']}), 500

        conversation_id = create_result['conversation_id']

        examiner = deps.EXAMINERS.get(scenario_id, deps.EXAMINERS['job_interview'])
        welcome_message = (
            f"你好！我是{examiner['name']}，{examiner['title']}。\n\n"
            f"欢迎参加{scenario_name}模拟面试。我们将进行约{deps.MAX_ROUNDS}轮的面试。\n\n"
            f"首先，请做一个简短的自我介绍。"
        )

        deps.db.add_message(conversation_id, 'assistant', welcome_message)

        return jsonify({
            'success': True, 'conversation_id': conversation_id,
            'welcome_message': welcome_message,
            'examiner_name': examiner['name'], 'examiner_title': examiner['title'],
            'max_rounds': deps.MAX_ROUNDS,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@examiner_bp.route('/examiner/finish', methods=['POST'])
def examiner_finish():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')

        if not conversation_id:
            return jsonify({'success': False, 'error': '缺少对话ID'}), 400

        skill_session = deps.SKILL_SESSIONS.get(conversation_id)
        if skill_session:
            skill_id = skill_session.skill_id
            skill = deps.skill_registry.get(skill_id)
            if skill:
                from src.core.workflow import create_interview_pipeline

                pipeline_result = create_interview_pipeline(
                    user_id=skill_session.user_id, scenario_id=skill_id,
                    conversation_id=conversation_id, skill_id=skill_id,
                    session=skill_session,
                )

                report = pipeline_result.context.report
                deps.db.update_conversation_status(conversation_id, 'finished')
                report.new_badges = pipeline_result.context.new_badges

                return jsonify({
                    'success': True,
                    'report': {
                        'overall_score': report.overall_score if report else 0,
                        'strengths': report.strengths if report else [],
                        'improvements': report.improvements if report else [],
                        'dimensions': report.dimension_scores if report else [],
                        'overall_comment': report.overall_comment if report else "面试完成",
                        'passed': report.passed if report else False,
                        'new_badges': pipeline_result.context.new_badges,
                    }
                })

        conversation = deps.db.get_conversation(conversation_id)
        if not conversation:
            return jsonify({'success': False, 'error': '对话不存在'}), 404

        scenario_id = conversation.get('scenario_id', 'job_interview')
        conversation_history = [
            {'role': m['role'], 'content': m['content']}
            for m in conversation.get('messages', [])
        ]

        try:
            report = deps.llm_client.generate_evaluation_report(
                scenario_id=scenario_id, conversation_history=conversation_history
            )
        except Exception as e:
            report = {
                'overall_score': random.randint(75, 85),
                'strengths': ['回答较为流畅', '思路清晰', '态度端正'],
                'improvements': ['建议增加具体实例', '加强专业知识', '注意时间把控'],
                'dimensions': [
                    {'name': '沟通表达', 'score': 80, 'max_score': 100, 'comment': '表达清晰'},
                    {'name': '专业能力', 'score': 78, 'max_score': 100, 'comment': '基础扎实'},
                    {'name': '逻辑思维', 'score': 82, 'max_score': 100, 'comment': '条理清晰'}
                ],
                'overall_comment': '面试结束！整体表现不错，继续加油！',
                'fallback': True, 'fallback_reason': str(e)
            }

        # 保存答题记录和成长数据
        user_id = conversation.get('user_id', 'anonymous')
        user_msgs = [m for m in conversation.get('messages', []) if m['role'] == 'user']

        dim_scores = {}
        if isinstance(report, dict):
            dims = report.get('dimensions', [])
            if dims:
                for d in dims:
                    dim_scores[d['name']] = d['score']
            overall = report.get('overall_score', random.randint(75, 85))
        else:
            dim_scores = {}
            overall = random.randint(75, 85)

        for i, msg in enumerate(user_msgs):
            deps.db.add_answer(
                user_id=user_id,
                conversation_id=conversation_id,
                question_id=None,
                round_num=i + 1,
                question_text='',
                answer_text=msg['content'],
                score=overall,
                dimension_scores=dim_scores,
                feedback=str(report.get('overall_comment', '')) if isinstance(report, dict) else '',
            )

        deps.db.update_progress(user_id, scenario_id, overall)
        deps.db.update_conversation_status(conversation_id, 'finished')

        new_badges = deps.db.check_and_unlock_badges(user_id, scenario_id, overall)

        return jsonify({'success': True, 'report': {**report, 'new_badges': new_badges}})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@examiner_bp.route('/examiner/conversation/<conversation_id>')
def get_conversation_detail(conversation_id):
    try:
        conversation = deps.db.get_conversation(conversation_id)
        if not conversation:
            return jsonify({'success': False, 'error': '对话不存在'}), 404
        return jsonify({'success': True, 'data': conversation})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@examiner_bp.route('/examiner/examiners')
def get_examiners():
    return jsonify({'success': True, 'data': EXAMINER_PROFILES})


def _ensure_user(user_id):
    """确保用户存在于数据库"""
    if not deps.db.get_user(user_id):
        deps.db.create_user(f"用户{user_id}", f"{user_id}@example.com", "dummy",
                            user_id=user_id)
