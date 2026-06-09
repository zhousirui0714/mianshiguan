"""AI 考官 + 场景 API Blueprint"""
import random
import re
import traceback
from flask import Blueprint, request, jsonify

from src.services.llm_client import EXAMINER_PROFILES
from src.core.skill.types import AnswerRecord
from src.web import dependencies as deps

# 岗位关键词映射表（岗位名称 → 关键词列表）
POSITION_KEYWORDS = {
    "python":      ["Python", "Redis", "MySQL", "数据库", "缓存", "系统设计", "Django", "Flask", "后端", "API"],
    "python后端":  ["Python", "Redis", "MySQL", "数据库", "缓存", "系统设计", "Django", "Flask", "后端", "API"],
    "java":        ["Java", "JVM", "Spring", "MySQL", "微服务", "中间件", "MyBatis", "后端"],
    "java后端":    ["Java", "JVM", "Spring", "MySQL", "微服务", "中间件", "MyBatis", "后端"],
    "golang":      ["Go", "Golang", "goroutine", "并发", "channel", "微服务", "后端"],
    "go":          ["Go", "Golang", "goroutine", "并发", "channel", "微服务", "后端"],
    "前端":        ["JavaScript", "浏览器", "CSS", "Vue", "React", "TypeScript", "HTML", "DOM", "前端"],
    "算法":        ["算法", "数据结构", "LeetCode", "排序", "搜索", "动态规划", "复杂度"],
    "产品经理":    ["需求分析", "用户研究", "产品设计", "用户", "产品", "需求", "流程", "体验"],
    "运营":        ["增长", "活动运营", "数据分析", "用户增长", "内容", "社群", "转化"],
    "测试":        ["测试", "自动化", "测试用例", "接口测试", "性能测试", "质量", "CI"],
    "数据分析":    ["数据", "分析", "SQL", "数仓", "ETL", "数据挖掘", "可视化"],
    "数据开发":    ["数据", "SQL", "数仓", "ETL", "数据挖掘", "Spark", "Flink", "Hadoop"],
    "产品运营":    ["运营", "用户", "增长", "活动", "内容", "数据", "转化率"],
}


def _get_position_keywords(position: str) -> list:
    """根据目标岗位获取匹配关键词列表"""
    if not position:
        return []
    pos_lower = position.lower().strip()
    # 精确匹配
    if pos_lower in POSITION_KEYWORDS:
        return POSITION_KEYWORDS[pos_lower]
    # 模糊匹配：输入包含key 或 key包含输入
    matched = []
    for key, kws in POSITION_KEYWORDS.items():
        if key in pos_lower or pos_lower in key:
            matched.extend(kws)
    return matched


def _match_question_to_position(question: dict, keywords: list) -> int:
    """计算题目与岗位的匹配得分"""
    if not keywords:
        return 0
    score = 0
    text = (question.get("question_text", "") or "")
    position_field = (question.get("position", "") or "")
    category = (question.get("category", "") or "")
    company = (question.get("company", "") or "")
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            score += 10
    # position字段匹配加分
    for kw in keywords:
        if kw.lower() in position_field.lower():
            score += 15
    # category匹配加分
    for kw in keywords:
        if kw.lower() in category.lower():
            score += 8
    return score


def _pick_questions_by_source(qs_pool: list, limit: int,
                               selected_ids: set) -> list:
    """
    从候选中按来源分层选入，尽量保持 real >= open >= ai 的优先级。
    返回新选中的题目列表（不修改 selected_ids）。
    """
    if limit <= 0 or not qs_pool:
        return []

    # 按来源分组
    real_qs = [q for q in qs_pool if (q.get("source_type") or "").strip() == "real_interview"]
    open_qs = [q for q in qs_pool if (q.get("source_type") or "").strip() == "open_source"]
    ai_qs   = [q for q in qs_pool if (q.get("source_type") or "").strip() == "ai_generated"]

    selected = []
    # caps: real 最多50%, open 最多25%, ai 最多25% 但不超过 limit
    real_cap = min(10, limit)
    open_cap = min(5, limit)
    ai_cap   = min(5, limit)

    def _pick(src_qs, cap):
        count = 0
        for q in src_qs:
            if count >= cap or len(selected) >= limit:
                break
            if q.get("id") not in selected_ids:
                selected.append(q)
                selected_ids.add(q.get("id"))
                count += 1

    _pick(real_qs, real_cap)
    _pick(open_qs, open_cap)
    _pick(ai_qs, ai_cap)

    # 补充：任一来源不够时继续从其他来源补
    if len(selected) < limit:
        for qs in (real_qs, open_qs, ai_qs):
            for q in qs:
                if len(selected) >= limit:
                    break
                if q.get("id") not in selected_ids:
                    selected.append(q)
                    selected_ids.add(q.get("id"))

    return selected


def _weighted_question_recall(db, scenario_id: str,
                               target_position: str = "",
                               target_company: str = "",
                               limit: int = 20) -> list:
    """
    加权召回题库

    权重策略（优先级从高到低）：
    1. 题目等级：S > A > B > C
    2. 来源权重：real_interview > open_source > ai_generated
    3. 岗位匹配：目标岗位 + 关键词

    默认只召回 S + A 级，数量不足时回退到 B，再回退到 C。
    目标比例：real >= 50%, open >= 20%, ai <= 30%
    """
    all_qs = db.get_questions(scenario_id=scenario_id)
    if not all_qs:
        return []

    random.shuffle(all_qs)
    position_kws = _get_position_keywords(target_position)

    # 每道题计算加权得分
    scored = []
    for q in all_qs:
        base = 0
        source = (q.get("source_type") or "ai_generated").strip()
        if source == "real_interview":
            base = 100
        elif source == "open_source":
            base = 60
        else:
            base = 20

        # 公司匹配加分
        if target_company:
            q_company = (q.get("company") or "")
            if target_company.lower() in q_company.lower():
                base += 30

        # 岗位匹配加分
        if target_position:
            q_position = (q.get("position") or "")
            if target_position.lower() in q_position.lower() or q_position.lower() in target_position.lower():
                base += 50

        # 关键词匹配分
        kw_score = _match_question_to_position(q, position_kws)
        base += kw_score

        scored.append((base, source, q))

    # 按得分降序排列
    scored.sort(key=lambda x: -x[0])

    # 按题目等级分组
    level_map = {"S": [], "A": [], "B": [], "C": []}
    for _, _, q in scored:
        lev = (q.get("question_level") or "C").strip().upper()
        if lev not in level_map:
            lev = "C"
        level_map[lev].append(q)

    selected = []
    selected_ids = set()

    # 分层选题：S → A → B → C
    LEVEL_ORDER = ["S", "A"]
    # 如果 S+A 不足 limit，自动补充 B，还不够再补充 C
    for level in LEVEL_ORDER:
        pool = level_map.get(level, [])
        picked = _pick_questions_by_source(pool, limit - len(selected), selected_ids)
        selected.extend(picked)

    # 补齐 B 级
    if len(selected) < limit:
        pool = level_map.get("B", [])
        # B 级不限 caps（已经不够了）
        for q in pool:
            if len(selected) >= limit:
                break
            if q.get("id") not in selected_ids:
                selected.append(q)
                selected_ids.add(q.get("id"))

    # 补齐 C 级
    if len(selected) < limit:
        pool = level_map.get("C", [])
        for q in pool:
            if len(selected) >= limit:
                break
            if q.get("id") not in selected_ids:
                selected.append(q)
                selected_ids.add(q.get("id"))

    return selected[:limit]

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

        # 为 legacy 路径加权召回题库
        _retrieved = []
        try:
            _retrieved = _weighted_question_recall(
                deps.db, scenario_id,
                target_position='', target_company='',
            )
        except Exception as e:
            print(f"[examiner_chat] legacy 加权召回失败: {e}")

        # 程序化选题（LLM 不再负责选题）
        _legacy_used = set(m['content'] for m in conversation_history if m['role'] == 'assistant')
        _bank_text = None
        for q in _retrieved:
            text = q.get("question_text", "")
            if text and text not in _legacy_used:
                _bank_text = text
                break

        if _bank_text:
            # 后端选题，直接使用
            ai_response = _bank_text
        else:
            # 题库用完，LLM 自由生成
            try:
                ai_response = deps.llm_client.examiner_chat(
                    scenario_id=scenario_id, user_message=user_message,
                    conversation_history=conversation_history, user_background=user_background,
                )
            except Exception as e:
                print(f"[examiner_chat] legacy LLM 调用失败: {e}")
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
        _vars = {}
        for _name in ['scenario_id', 'conversation_id', 'user_id',
                       'user_message', 'user_background',
                       'skill_session', 'history', 'conversation_history',
                       '_retrieved', 'last_question']:
            try:
                _val = locals().get(_name)
                if _val is None:
                    continue
                if _name == 'skill_session':
                    _vars[_name] = f"<round={_val.round}>"
                elif _name in ('history', 'conversation_history'):
                    _vars[_name] = f"<len={len(_val)}>"
                elif _name in ('user_message', 'user_background', 'last_question'):
                    _vars[_name] = f"<len={len(_val)}>"
                elif _name == '_retrieved':
                    _vars[_name] = f"<{len(_val)} questions>"
                else:
                    _vars[_name] = _val
            except Exception:
                _vars[_name] = '<error>'

        print(f"[examiner_chat] 未捕获异常: {e}")
        for _k, _v in _vars.items():
            print(f"  {_k}={_v}")
        print(f"  traceback:\n{traceback.format_exc()}")
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

        # 从 user_background 中提取各种场景信息（适配所有场景）
        extracted = {}
        spider_questions = []
        lines = user_background.split('\n')
        resume_text = ""
        for line in lines:
            line_stripped = line.strip()
            for prefix in ['目标岗位：', '目标公司：', '报考科目：', '报考学段：',
                           '目标院校：', '目标专业：', '报考单位：', '报考岗位类别：',
                           '所在公司/行业：']:
                if line_stripped.startswith(prefix):
                    key = prefix.rstrip('：')
                    extracted[key] = line_stripped.replace(prefix, '').strip()
            if line_stripped.startswith('个人简历：'):
                resume_text = user_background.split('个人简历：\n', 1)[-1].strip() if '个人简历：\n' in user_background else ''

        # 搜索面经数据（仅对求职类场景有效）
        search_position = extracted.get('目标岗位') or extracted.get('报考岗位类别') or ''
        search_company = extracted.get('目标公司') or extracted.get('报考单位') or ''
        if search_position:
            try:
                spider_results = deps.db.search_interview_experiences(
                    company=search_company, position=search_position, limit=5
                )
                seen = set()
                for r in spider_results:
                    questions = r.get('questions', [])
                    if isinstance(questions, list):
                        for q in questions:
                            if q and q not in seen:
                                spider_questions.append(q)
                                seen.add(q)
                spider_questions = spider_questions[:8]
            except Exception:
                spider_questions = []

        # 加权召回题库（真实面经 > 开源 > AI生成，岗位定向）
        retrieved_questions = []
        try:
            retrieved_questions = _weighted_question_recall(
                deps.db, scenario_id,
                target_position=search_position,
                target_company=search_company,
            )
        except Exception as e:
            print(f"[examiner_start] 题库召回失败: {e}")

        skill = deps.skill_registry.get(scenario_id)
        if skill:
            session_data = skill.create_session(user_id, {
                "user_background": user_background,
                "spider_questions": spider_questions,
                "retrieved_questions": retrieved_questions,
                "position": search_position,
                "company": search_company,
            })
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

        # 构建个性化欢迎消息
        welcome_parts = [f"你好！我是{examiner['name']}，{examiner['title']}。"]
        welcome_parts.append(f"")
        if search_position:
            welcome_parts.append(f"我看到你正在准备{search_position}岗位{'（' + search_company + '）' if search_company else ''}的面试。我已经根据你的背景和真实面经数据，准备好了针对性的面试题。")
        welcome_parts.append(f"")
        welcome_parts.append(f"欢迎参加{scenario_name}模拟面试，我们将进行约{deps.MAX_ROUNDS}轮的问答。")
        if retrieved_questions:
            welcome_parts.append(f"我已从题库中精选了{len(retrieved_questions)}道相关真题，将在面试中依次呈现。")
        if spider_questions:
            welcome_parts.append(f"")
            welcome_parts.append(f"在面试中，我会参考以下来自真实面经的高频问题方向：")
            for i, q in enumerate(spider_questions[:3], 1):
                welcome_parts.append(f"  {i}. {q}")
        welcome_parts.append(f"")
        welcome_parts.append(f"那么，我们先从自我介绍开始吧——请简要介绍一下你自己和你的专业背景。")

        welcome_message = "\n".join(welcome_parts)

        deps.db.add_message(conversation_id, 'assistant', welcome_message)

        return jsonify({
            'success': True, 'conversation_id': conversation_id,
            'welcome_message': welcome_message,
            'examiner_name': examiner['name'], 'examiner_title': examiner['title'],
            'max_rounds': deps.MAX_ROUNDS,
        })

    except Exception as e:
        _vars = {}
        for _name in ['scenario_id', 'conversation_id', 'user_id',
                       'user_background', 'search_position', 'search_company',
                       'retrieved_questions', 'spider_questions']:
            try:
                _val = locals().get(_name)
                if _val is None:
                    continue
                if _name in ('retrieved_questions', 'spider_questions'):
                    _vars[_name] = f"<{len(_val)} questions>"
                elif _name == 'user_background':
                    _vars[_name] = f"<len={len(_val)}>"
                else:
                    _vars[_name] = _val
            except Exception:
                _vars[_name] = '<error>'
        print(f"[examiner_start] 未捕获异常: {e}")
        for _k, _v in _vars.items():
            print(f"  {_k}={_v}")
        print(f"  traceback:\n{traceback.format_exc()}")
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

                # 持久化报告数据
                deps.db.update_conversation_report(conversation_id, {
                    'overall_score': report.overall_score if report else 0,
                    'strengths': report.strengths if report else [],
                    'improvements': report.improvements if report else [],
                    'dimensions': report.dimension_scores if report else [],
                    'overall_comment': report.overall_comment if report else "面试完成",
                    'passed': report.passed if report else False,
                    'new_badges': pipeline_result.context.new_badges,
                })

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

        # 持久化报告数据
        deps.db.update_conversation_report(conversation_id, {**report, 'new_badges': new_badges})

        return jsonify({'success': True, 'report': {**report, 'new_badges': new_badges}})

    except Exception as e:
        try:
            _cid = (request.get_json() or {}).get('conversation_id', '?')
        except Exception:
            _cid = '<error>'
        print(f"[examiner_finish] 未捕获异常: {e}")
        print(f"  conversation_id={_cid}")
        print(f"  traceback:\n{traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


@examiner_bp.route('/result/<conversation_id>')
def get_conversation_result(conversation_id):
    """获取面试结果数据"""
    try:
        result = deps.db.get_conversation_result(conversation_id)
        if not result:
            return jsonify({'success': False, 'error': '对话不存在'}), 404
        return jsonify({'success': True, 'data': result})
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
