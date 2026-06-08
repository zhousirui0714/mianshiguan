"""题库管理 API Blueprint"""
from flask import Blueprint, request, jsonify

from src.web import dependencies as deps

questions_bp = Blueprint('api_questions', __name__)


@questions_bp.route('/questions')
def get_questions():
    try:
        scenario = request.args.get('scenario')
        category = request.args.get('category')
        difficulty = request.args.get('difficulty', type=int)
        keyword = request.args.get('keyword')
        company = request.args.get('company')
        position = request.args.get('position')
        year = request.args.get('year')

        questions = deps.db.get_questions(
            scenario_id=scenario, category=category,
            difficulty=difficulty, keyword=keyword,
            company=company, position=position, year=year
        )
        return jsonify({'success': True, 'data': questions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/<question_id>')
def get_question_detail(question_id):
    try:
        question = deps.db.get_question(question_id)
        if not question:
            return jsonify({'success': False, 'error': '题目不存在'}), 404
        return jsonify({'success': True, 'data': question})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions', methods=['POST'])
def add_question():
    try:
        data = request.get_json()
        required_fields = ['scenario', 'category', 'difficulty', 'question_text', 'reference_answer']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少字段: {field}'}), 400

        result = deps.db.add_question(
            scenario_id=data['scenario'], category=data['category'],
            difficulty=data['difficulty'], question_text=data['question_text'],
            reference_answer=data['reference_answer'], tags=data.get('tags', []),
            company=data.get('company', ''), position=data.get('position', ''),
            source=data.get('source', ''), year=data.get('year', '')
        )

        if result['success']:
            return jsonify({'success': True, 'question_id': result['question_id']}), 201
        return jsonify({'success': False, 'error': result['error']}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/<question_id>', methods=['PUT'])
def update_question(question_id):
    try:
        data = request.get_json()
        result = deps.db.update_question(question_id, **data)
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': result['error']}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    try:
        result = deps.db.delete_question(question_id)
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': result['error']}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/categories')
def get_question_categories():
    try:
        scenario = request.args.get('scenario')
        categories = deps.db.get_categories(scenario_id=scenario)
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/companies')
def get_question_companies():
    try:
        scenario = request.args.get('scenario')
        companies = deps.db.get_companies(scenario_id=scenario)
        return jsonify({'success': True, 'data': companies})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/positions')
def get_question_positions():
    try:
        scenario = request.args.get('scenario')
        positions = deps.db.get_positions(scenario_id=scenario)
        return jsonify({'success': True, 'data': positions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/years')
def get_question_years():
    try:
        scenario = request.args.get('scenario')
        years = deps.db.get_years(scenario_id=scenario)
        return jsonify({'success': True, 'data': years})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@questions_bp.route('/questions/tags')
def get_question_tags():
    try:
        scenario = request.args.get('scenario')
        tags = deps.db.get_tags(scenario_id=scenario)
        return jsonify({'success': True, 'data': tags})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
