"""认证 API Blueprint"""
from flask import Blueprint, request, jsonify, session

from werkzeug.security import generate_password_hash, check_password_hash

from src.web import dependencies as deps

auth_bp = Blueprint('api_auth', __name__)


@auth_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '')

    if not username or not email or not password:
        return jsonify({'success': False, 'error': '请填写所有必填项'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'error': '密码至少 6 位'}), 400

    existing = deps.db.get_user_by_email(email)
    if existing:
        return jsonify({'success': False, 'error': '该邮箱已注册'}), 409

    hashed = generate_password_hash(password)
    result = deps.db.create_user(username, email, hashed)
    if not result['success']:
        return jsonify({'success': False, 'error': result.get('error', '注册失败')}), 500

    session['user_id'] = result['user_id']
    return jsonify({
        'success': True,
        'user': {'id': result['user_id'], 'username': username, 'email': email},
    })


@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'success': False, 'error': '请填写邮箱和密码'}), 400

    user = deps.db.get_user_by_email(email)
    if not user:
        return jsonify({'success': False, 'error': '该邮箱尚未注册，请先注册账号'}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': '密码错误，请重新输入'}), 401

    session['user_id'] = user['id']
    return jsonify({
        'success': True,
        'user': {'id': user['id'], 'username': user['username'], 'email': user['email']},
    })


@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@auth_bp.route('/auth/me')
def me():
    """查询当前登录状态"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False})
    user = deps.db.get_user(user_id)
    if not user:
        session.clear()
        return jsonify({'logged_in': False})
    return jsonify({
        'logged_in': True,
        'user': {'id': user['id'], 'username': user['username'], 'email': user['email']},
    })
