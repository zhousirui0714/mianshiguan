"""
面试翻车救援队 - Flask Web应用
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from src.services.review_service import ReviewService
from src.services.user_service import UserService
from src.utils.logger import Logger
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# 初始化服务
review_service = ReviewService()
user_service = UserService()
logger = Logger()

# 会话存储（内存模拟）
sessions = {}

@app.route('/')
def index():
    """首页/落地页"""
    return render_template('index.html')

@app.route('/start')
def start():
    """开始复盘 - 跳转登记页"""
    return redirect(url_for('checkin'))

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    """翻车登记页"""
    crash_types = review_service.get_crash_types()
    
    if request.method == 'POST':
        data = request.get_json()
        company_name = data.get('company_name')
        position = data.get('position')
        crash_type = data.get('crash_type')
        interview_date = data.get('interview_date')
        
        if not company_name or not position or not crash_type:
            return jsonify({'success': False, 'error': '请填写完整信息'})
        
        # 创建复盘会话
        session_id = str(uuid.uuid4())
        session_data = {
            'company_name': company_name,
            'position': position,
            'crash_type': crash_type,
            'interview_date': interview_date
        }
        sessions[session_id] = session_data
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'redirect': f'/quiz/{session_id}'
        })
    
    return render_template('checkin.html', crash_types=crash_types)

@app.route('/quiz/<session_id>', methods=['GET', 'POST'])
def quiz(session_id):
    """引导问答页"""
    if session_id not in sessions:
        return redirect(url_for('index'))
    
    session_data = sessions[session_id]
    crash_type = session_data['crash_type']
    
    if request.method == 'POST':
        data = request.get_json()
        answers = data.get('answers', {})
        
        # 保存答案到会话
        session_data['quiz_answers'] = answers
        sessions[session_id] = session_data
        
        return jsonify({
            'success': True,
            'redirect': f'/result/{session_id}'
        })
    
    questions = review_service._generate_quiz_questions(crash_type)
    return render_template('quiz.html', 
                         session_id=session_id,
                         questions=questions,
                         current_step=1,
                         total_steps=len(questions))

@app.route('/result/<session_id>')
def result(session_id):
    """复盘结果页"""
    if session_id not in sessions:
        return redirect(url_for('index'))
    
    session_data = sessions[session_id]
    
    # 生成徽章和行动建议
    badge = review_service.generate_badge(session_data['crash_type'])
    action_items = review_service.generate_action_items(session_data['crash_type'])
    rescue_scripts = review_service.get_rescue_scripts(session_data['crash_type'])
    
    result_data = {
        'company_name': session_data['company_name'],
        'position': session_data['position'],
        'crash_type': session_data['crash_type'],
        'crash_type_label': review_service.crash_types.get(session_data['crash_type']),
        'badge': badge,
        'action_items': action_items,
        'rescue_scripts': rescue_scripts[:2]  # 取前两条
    }
    
    return render_template('result.html', result=result_data)

@app.route('/badges')
def badges():
    """徽章收藏馆"""
    all_badges = review_service.get_all_badges()
    
    # 按稀有度分组
    rarity_order = {'legendary': 0, 'epic': 1, 'rare': 2, 'common': 3}
    all_badges.sort(key=lambda x: rarity_order.get(x['rarity'], 3))
    
    return render_template('badges.html', badges=all_badges)

@app.route('/rescue')
def rescue():
    """救援话术库"""
    scripts = review_service.get_all_rescue_scripts()
    crash_types = review_service.get_crash_types()
    
    # 按翻车类型分组
    grouped_scripts = {}
    for crash_type in crash_types:
        key = crash_type['value']
        grouped_scripts[key] = {
            'label': crash_type['label'],
            'scripts': [s for s in scripts if s['crash_type'] == key]
        }
    
    return render_template('rescue.html', grouped_scripts=grouped_scripts, crash_types=crash_types)

@app.route('/user/profile')
def user_profile():
    """个人中心"""
    return render_template('profile.html')

@app.route('/api/crash-types')
def api_crash_types():
    """获取翻车类型列表"""
    return jsonify({'success': True, 'data': review_service.get_crash_types()})

@app.route('/api/start-review', methods=['POST'])
def api_start_review():
    """开始复盘"""
    data = request.get_json()
    company_name = data.get('company_name')
    position = data.get('position')
    crash_type = data.get('crash_type')
    
    if not company_name or not position or not crash_type:
        return jsonify({'success': False, 'error': '请填写完整信息'})
    
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'company_name': company_name,
        'position': position,
        'crash_type': crash_type
    }
    
    return jsonify({
        'success': True,
        'session_id': session_id
    })

@app.route('/api/submit-quiz/<session_id>', methods=['POST'])
def api_submit_quiz(session_id):
    """提交问答"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': '会话不存在'})
    
    data = request.get_json()
    sessions[session_id]['quiz_answers'] = data.get('answers', {})
    
    return jsonify({'success': True})

@app.route('/api/get-result/<session_id>')
def api_get_result(session_id):
    """获取复盘结果"""
    if session_id not in sessions:
        return jsonify({'success': False, 'error': '会话不存在'})
    
    session_data = sessions[session_id]
    badge = review_service.generate_badge(session_data['crash_type'])
    action_items = review_service.generate_action_items(session_data['crash_type'])
    rescue_scripts = review_service.get_rescue_scripts(session_data['crash_type'])
    
    return jsonify({
        'success': True,
        'data': {
            'badge': badge,
            'action_items': action_items,
            'rescue_scripts': rescue_scripts
        }
    })

@app.route('/api/user/badges')
def api_user_badges():
    """获取用户徽章"""
    user_id = request.args.get('user_id', 'default_user')
    badges = user_service.get_user_badges(user_id)
    return jsonify({'success': True, 'data': badges})

@app.route('/api/user/add-badge', methods=['POST'])
def api_add_badge():
    """添加徽章"""
    data = request.get_json()
    user_id = data.get('user_id', 'default_user')
    badge = data.get('badge')
    
    success = user_service.add_user_badge(user_id, badge)
    return jsonify({'success': success})

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({'status': 'healthy', 'service': 'interview-rescue-team'})

if __name__ == '__main__':
    print("="*70)
    print("          面试翻车救援队 - Web服务          ")
    print("="*70)
    print()
    print("-> 访问地址：http://127.0.0.1:5000")
    print()
    print("按 Ctrl+C 停止服务")
    print("="*70)
    print()
    
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
