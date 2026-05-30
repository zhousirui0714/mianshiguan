"""
面试成长伴侣 - Flask Web应用
多场景面试模拟平台
"""
from src.web import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
