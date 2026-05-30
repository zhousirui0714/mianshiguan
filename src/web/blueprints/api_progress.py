"""成长档案 & 数据分析 API Blueprint"""
from flask import Blueprint, request, jsonify

from src.web import dependencies as deps

progress_bp = Blueprint('api_progress', __name__)


@progress_bp.route('/user/<user_id>/progress')
def get_user_progress(user_id):
    try:
        scenario_id = request.args.get('scenario_id')
        progress_data = deps.db.get_user_progress(user_id, scenario_id)
        return jsonify({'success': True, 'data': progress_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@progress_bp.route('/user/<user_id>/scenario-detail/<scenario_id>')
def get_user_scenario_detail(user_id, scenario_id):
    try:
        data = deps.db.get_user_scenario_detail(user_id, scenario_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@progress_bp.route('/leaderboard/<scenario_id>')
def get_leaderboard(scenario_id):
    try:
        limit = request.args.get('limit', 10, type=int)
        data = deps.db.get_scenario_leaderboard(scenario_id, limit)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@progress_bp.route('/statistics/<scenario_id>')
def get_scenario_statistics(scenario_id):
    try:
        data = deps.db.get_scenario_statistics(scenario_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@progress_bp.route('/user/<user_id>/answers')
def get_user_answers_api(user_id):
    try:
        scenario_id = request.args.get('scenario_id')
        limit = request.args.get('limit', 20, type=int)
        data = deps.db.get_user_answers(user_id, scenario_id, limit)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 数据可视化 API ====================

@progress_bp.route('/user/<user_id>/summary')
def get_user_summary(user_id):
    """用户聚合概览（成长中心顶部统计卡片）"""
    try:
        data = deps.db.get_user_summary(user_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@progress_bp.route('/user/<user_id>/dimension-trend')
def get_user_dimension_trend(user_id):
    """各维度得分趋势"""
    try:
        data = deps.db.get_dimension_trend(user_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@progress_bp.route('/user/<user_id>/streak')
def get_user_streak(user_id):
    """用户连续练习天数"""
    try:
        streak = deps.db.get_user_streak(user_id)
        return jsonify({'success': True, 'streak': streak})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
