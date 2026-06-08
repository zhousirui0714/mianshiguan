"""面经数据 API Blueprint"""
import json
import os
import sys
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Any

from flask import Blueprint, request, jsonify

from src.web import dependencies as deps

spider_bp = Blueprint('api_spider', __name__)

# 采集系统状态
_collector_status = {
    "running": False,
    "progress": "",
    "started_at": None,
    "finished_at": None,
    "result": None,
    "error": None,
}


@spider_bp.route('/interview/search')
def search_interview_experiences():
    """搜索面经，按公司+岗位模糊匹配

    Query params:
        company (str): 公司名
        position (str): 岗位名
        limit (int): 返回条数，默认 10
    """
    try:
        company = request.args.get('company', '').strip()
        position = request.args.get('position', '').strip()
        limit = request.args.get('limit', 10, type=int)
        limit = min(max(limit, 1), 50)  # 限制 1-50 条

        rows = deps.db.search_interview_experiences(company, position, limit)

        # 格式化为前端友好结构
        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "company_name": r["company_name"],
                "position": r["position"],
                "round": r["round"],
                "questions": r.get("questions", []),
                "source_url": r.get("source_url", ""),
                "created_at": r.get("created_at", ""),
            })

        return jsonify({
            'success': True,
            'data': results,
            'total': len(results),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@spider_bp.route('/interview/companies')
def list_companies():
    """获取面经中出现的所有公司列表"""
    try:
        from src.spider.nowcoder_spider import KNOWN_COMPANIES
        return jsonify({
            'success': True,
            'data': KNOWN_COMPANIES,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ================================================================
# 自动采集系统 API
# ================================================================

def _collector_worker(scenarios: List[str], max_pages: int, use_llm: bool):
    """后台采集线程"""
    global _collector_status
    try:
        # 动态导入（避免启动时加载）
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from scripts.question_collector.searcher import search_all_scenarios
        from scripts.question_collector.extractor import extract_all_pages
        from scripts.question_collector.deduplicator import InternalDeduplicator, DatabaseDeduplicator
        from scripts.question_collector.classifier import classify_all
        from scripts.question_collector.grader import grade_all
        from scripts.question_collector.storage import save_questions, import_to_database, print_report
        from scripts.question_collector.schema import CollectedQuestion
        from scripts.question_collector.config import (
            SEARCH_RESULTS_JSON, RAW_JSON, DEDUPED_JSON,
            CLASSIFIED_JSON, GRADED_JSON, FINAL_JSON,
        )

        _collector_status["progress"] = "搜索面经页面..."
        results = search_all_scenarios(scenarios=scenarios)
        from scripts.question_collector.searcher import save_search_results
        save_search_results(results, SEARCH_RESULTS_JSON)

        _collector_status["progress"] = "抓取页面并提取面试题..."
        all_questions = extract_all_pages(results, use_llm=use_llm, max_pages_per_scenario=max_pages)
        flat_questions = []
        for sc, qs in all_questions.items():
            flat_questions.extend(qs)
        save_questions(flat_questions, RAW_JSON)

        _collector_status["progress"] = "去重..."
        questions = InternalDeduplicator().deduplicate(flat_questions)
        questions = DatabaseDeduplicator().deduplicate(questions)
        save_questions(questions, DEDUPED_JSON)

        _collector_status["progress"] = "分类..."
        questions = classify_all(questions)
        save_questions(questions, CLASSIFIED_JSON)

        _collector_status["progress"] = "评级..."
        questions = grade_all(questions)
        save_questions(questions, GRADED_JSON)

        _collector_status["progress"] = "导入数据库..."
        imported = import_to_database(questions)

        _collector_status["result"] = {
            "total_collected": len(flat_questions),
            "after_dedup": len(questions),
            "imported_to_db": imported,
            "s_grades": sum(1 for q in questions if q.grade == "S"),
            "a_grades": sum(1 for q in questions if q.grade == "A"),
        }
        _collector_status["progress"] = "完成"
        _collector_status["running"] = False
        _collector_status["finished_at"] = datetime.now().isoformat()

    except Exception as e:
        _collector_status["error"] = str(e)
        _collector_status["running"] = False
        _collector_status["finished_at"] = datetime.now().isoformat()


@spider_bp.route('/collector/start', methods=['POST'])
def start_collector():
    """启动自动采集（后台运行）"""
    global _collector_status

    if _collector_status["running"]:
        return jsonify({'success': False, 'error': '采集任务已在运行中'}), 400

    data = request.get_json(silent=True) or {}
    scenarios = data.get("scenarios", None)
    max_pages = data.get("max_pages", 30)
    use_llm = data.get("use_llm", True)

    _collector_status = {
        "running": True,
        "progress": "启动中...",
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "result": None,
        "error": None,
    }

    thread = threading.Thread(
        target=_collector_worker,
        args=(scenarios, max_pages, use_llm),
        daemon=True,
    )
    thread.start()

    return jsonify({
        'success': True,
        'message': '采集任务已启动',
        'status': _collector_status,
    })


@spider_bp.route('/collector/status')
def collector_status():
    """获取采集任务状态"""
    global _collector_status
    return jsonify({
        'success': True,
        'data': _collector_status,
    })


@spider_bp.route('/collector/stats')
def collector_stats():
    """获取题库统计信息"""
    try:
        import sqlite3
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "interview.db"
        )
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM questions")
        total = cur.fetchone()[0]

        cur.execute("SELECT source_type, COUNT(*) FROM questions GROUP BY source_type")
        sources = {r[0]: r[1] for r in cur.fetchall()}

        cur.execute("""
            SELECT s.name, COUNT(q.id)
            FROM scenarios s
            LEFT JOIN questions q ON s.id = q.scenario_id
            GROUP BY s.id
            ORDER BY COUNT(q.id) DESC
        """)
        scenarios = {r[0]: r[1] for r in cur.fetchall()}

        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'total_questions': total,
                'source_distribution': sources,
                'scenario_distribution': scenarios,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@spider_bp.route('/collector/seed', methods=['POST'])
def import_seed_questions():
    """导入种子题库到数据库"""
    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from scripts.question_collector.schema import CollectedQuestion
        from scripts.question_collector.deduplicator import InternalDeduplicator, DatabaseDeduplicator
        from scripts.question_collector.classifier import classify_all
        from scripts.question_collector.grader import grade_all
        from scripts.question_collector.storage import save_questions, import_to_database

        seed_path = os.path.join(project_root, "data", "collected_questions", "seed_questions.json")
        if not os.path.exists(seed_path):
            return jsonify({'success': False, 'error': '种子文件不存在，请先生成'}), 404

        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        questions = [CollectedQuestion(**d) for d in data]
        questions = InternalDeduplicator().deduplicate(questions)
        questions = DatabaseDeduplicator().deduplicate(questions)
        questions = classify_all(questions)
        questions = grade_all(questions)
        imported = import_to_database(questions)

        return jsonify({
            'success': True,
            'data': {
                'total': len(questions),
                'imported': imported,
                's_grades': sum(1 for q in questions if q.grade == "S"),
                'a_grades': sum(1 for q in questions if q.grade == "A"),
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@spider_bp.route('/collector/generate-answers', methods=['POST'])
def generate_answers():
    """为采集的题目生成 3 级答案"""
    import time as _time

    data = request.get_json(silent=True) or {}
    max_questions = data.get("max_questions", 20)
    answer_type = data.get("type", "graded")  # graded or all

    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from scripts.question_collector.schema import CollectedQuestion
        from scripts.question_collector.answer_generator import generate_all_answers
        from scripts.question_collector.storage import save_questions, load_questions, import_to_database
        from scripts.question_collector.config import FINAL_JSON, ANSWERS_JSON, ALL_JSON

        # 加载已评级的题目
        graded_path = os.path.join(project_root, "data", "collected_questions", "04_graded.json")
        questions_data = load_questions(graded_path)
        if not questions_data:
            return jsonify({'success': False, 'error': '没有已评级的题目'}), 404

        questions = [CollectedQuestion(**d) for d in questions_data]
        questions = generate_all_answers(questions, max_questions=max_questions)
        save_questions(questions, ANSWERS_JSON)

        # 导入到数据库（带上答案）
        imported = import_to_database(questions)

        return jsonify({
            'success': True,
            'data': {
                'generated': min(len(questions), max_questions),
                'imported_to_db': imported,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
