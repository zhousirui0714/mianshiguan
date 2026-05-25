"""
个人极简面试官 - Flask Web应用
"""

from flask import Flask, render_template, request, jsonify
from src.services.llm_client import LLMClient
from src.utils.logger import Logger
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# 初始化服务
llm_client = LLMClient()
logger = Logger()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/api/interview/start', methods=['POST'])
def start_interview():
    """开始面试"""
    data = request.json
    request_id = logger.generate_request_id()
    
    logger.log_entry(
        request_id=request_id,
        endpoint="/api/interview/start",
        method="POST",
        params=data
    )
    
    # 返回初始问题
    try:
        result = llm_client.generate_questions_with_fallback(
            project_description=data.get('projectDesc', ''),
            tech_stack=data.get('techStack', '').split(',')
        )
        
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/interview/start",
            success=True,
            latency_ms=0,
            result=result
        )
        
        return jsonify({
            'success': True,
            'question': result.get('questions', [])[0] if result.get('questions') else None,
            'request_id': request_id
        })
    except Exception as e:
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/interview/start",
            success=False,
            latency_ms=0,
            error=str(e)
        )
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/interview/question', methods=['POST'])
def get_question():
    """获取下一个问题"""
    data = request.json
    request_id = logger.generate_request_id()
    
    logger.log_entry(
        request_id=request_id,
        endpoint="/api/interview/question",
        method="POST",
        params=data
    )
    
    try:
        # 根据历史对话生成下一个问题
        conversation = data.get('conversation', [])
        project_desc = data.get('projectDesc', '')
        
        # 简化逻辑：直接生成新问题
        result = llm_client.generate_questions_with_fallback(
            project_description=project_desc,
            tech_stack=data.get('techStack', '').split(',')
        )
        
        question = result.get('questions', [{}])[0] if result.get('questions') else {
            'question': '请详细描述一下你的项目经历？',
            'logic': '考察项目经验'
        }
        
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/interview/question",
            success=True,
            latency_ms=0,
            result=question
        )
        
        return jsonify({
            'success': True,
            'question': question,
            'request_id': request_id
        })
    except Exception as e:
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/interview/question",
            success=False,
            latency_ms=0,
            error=str(e)
        )
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'healthy', 'service': 'interview-assistant'})

if __name__ == '__main__':
    print("="*70)
    print("          个人极简面试官 - Web服务          ")
    print("="*70)
    print()
    print("🌐 访问地址：http://127.0.0.1:5000")
    print()
    print("按 Ctrl+C 停止服务")
    print("="*70)
    print()
    
    app.run(debug=True, host='127.0.0.1', port=5000)
