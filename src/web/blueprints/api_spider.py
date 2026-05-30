"""面经数据 API Blueprint"""
from flask import Blueprint, request, jsonify

from src.web import dependencies as deps

spider_bp = Blueprint('api_spider', __name__)


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
