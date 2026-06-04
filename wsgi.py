"""
百工模拟考场 - WSGI 入口（Render 部署用）
"""
import os
import sys

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.web import create_app

app = create_app()

if __name__ == '__main__':
    import eventlet
    eventlet.monkey_patch()
    from flask_socketio import SocketIO
    from src.web import socketio
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
