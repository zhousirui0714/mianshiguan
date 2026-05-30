"""
面试成长伴侣 - Flask Web应用
多场景面试模拟平台
"""
from src.web import create_app, socketio

app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
