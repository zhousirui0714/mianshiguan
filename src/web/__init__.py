"""Flask 应用工厂"""
import os
from flask import Flask

from src.scenarios.manager import ScenarioManager
from src.services.llm_client import LLMClient
from src.core.database import DatabaseManager
from src.core.skill import registry as skill_registry, executor as skill_executor
from src.core.tool import registry as tool_registry, executor as tool_executor
from src.skills import init_skills
from src.tools import init_tools

from src.web import dependencies as deps
from src.web.blueprints.web import web_bp
from src.web.blueprints.api_examiner import examiner_bp
from src.web.blueprints.api_questions import questions_bp
from src.web.blueprints.api_badges import badges_bp
from src.web.blueprints.api_progress import progress_bp
from src.web.blueprints.api_skills import skills_bp


def create_app():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'interview-companion-secret-key')

    _init_dependencies()
    _register_blueprints(app)

    print("=" * 70)
    print("        面试成长伴侣 - 多场景面试模拟平台        ")
    print("=" * 70)
    print()
    print("支持场景：求职面试 | 教资面试 | 雅思口语 | 公务员面试 | 考研复试 | MBA面试")
    print()
    print("-> 访问地址：http://127.0.0.1:5000")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 70)
    print()

    return app


def _init_dependencies():
    deps.scenario_manager = ScenarioManager()
    deps.llm_client = LLMClient()

    deps.db = DatabaseManager()
    deps.db.seed_default_data()
    print(f"[app] SQLite 数据库就绪: {deps.db.db_path}")

    init_skills()
    print(f"[app] Skill 系统就绪，已注册 {len(skill_registry.get_all())} 个 Skill")

    init_tools()
    print(f"[app] Tool 系统就绪，已注册 {len(tool_registry.get_all())} 个 Tool")

    deps.skill_registry = skill_registry
    deps.skill_executor = skill_executor
    deps.tool_registry = tool_registry
    deps.tool_executor = tool_executor


def _register_blueprints(app):
    app.register_blueprint(web_bp)
    app.register_blueprint(examiner_bp, url_prefix='/api')
    app.register_blueprint(questions_bp, url_prefix='/api')
    app.register_blueprint(badges_bp, url_prefix='/api')
    app.register_blueprint(progress_bp, url_prefix='/api')
    app.register_blueprint(skills_bp, url_prefix='/api')
