"""徽章管理 API Blueprint"""
from flask import Blueprint, request, jsonify

from src.web import dependencies as deps

badges_bp = Blueprint('api_badges', __name__)


@badges_bp.route('/badges')
def get_all_badges_api():
    try:
        badges = deps.db.get_all_badges()
        return jsonify({'success': True, 'data': badges})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@badges_bp.route('/user/<user_id>/badges')
def get_user_badges(user_id):
    try:
        badges = deps.db.get_user_badges(user_id)
        return jsonify({'success': True, 'data': badges})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@badges_bp.route('/badge/check-unlock', methods=['POST'])
def check_badge_unlock():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        scenario = data.get('scenario')
        score = data.get('score', 0)
        duration = data.get('duration')

        if not scenario:
            return jsonify({'success': False, 'error': '缺少场景参数'}), 400

        new_badges = deps.db.check_and_unlock_badges(user_id, scenario, score, duration)
        return jsonify({'success': True, 'new_badges': new_badges})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@badges_bp.route('/badge/<badge_id>/mark-viewed', methods=['POST'])
def mark_badge_viewed(badge_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        result = deps.db.mark_badge_viewed(user_id, badge_id)
        if result['success']:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': result['error']}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@badges_bp.route('/user/<user_id>/badges/new-count')
def get_user_new_badge_count_api(user_id):
    try:
        count = deps.db.get_user_new_badge_count(user_id)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
