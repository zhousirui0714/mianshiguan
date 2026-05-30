"""Skill + Tool Calling API Blueprint"""
from flask import Blueprint, request, jsonify

from src.web import dependencies as deps

skills_bp = Blueprint('api_skills', __name__)


@skills_bp.route('/skills')
def get_skills():
    skills = deps.skill_registry.get_enabled()
    return jsonify({
        'success': True,
        'data': [
            {
                'id': s.config.id, 'name': s.config.name,
                'category': s.config.category, 'max_rounds': s.config.max_rounds,
                'persona_name': s.config.persona.name,
                'persona_title': s.config.persona.title,
                'dimensions': [
                    {'name': d.name, 'weight': d.weight}
                    for d in s.config.scoring.dimensions
                ],
            }
            for s in skills
        ]
    })


@skills_bp.route('/skills/<skill_id>')
def get_skill_detail(skill_id):
    skill = deps.skill_registry.get(skill_id)
    if not skill:
        return jsonify({'success': False, 'error': 'Skill 未注册'}), 404
    return jsonify({
        'success': True,
        'data': {
            'id': skill.config.id, 'name': skill.config.name,
            'category': skill.config.category,
            'persona': {
                'name': skill.config.persona.name,
                'title': skill.config.persona.title,
                'tone': skill.config.persona.tone,
            },
            'scoring': {
                'dimensions': [
                    {'id': d.id, 'name': d.name, 'max_score': d.max_score, 'weight': d.weight}
                    for d in skill.config.scoring.dimensions
                ],
                'passing_score': skill.config.scoring.passing_score,
            },
            'max_rounds': skill.config.max_rounds,
        }
    })


@skills_bp.route('/tools')
def get_tools():
    skill_id = request.args.get('skill_id')
    tools = deps.tool_registry.list_definitions(skill_id)
    return jsonify({'success': True, 'data': tools})


@skills_bp.route('/tools/<tool_id>')
def get_tool_detail(tool_id):
    tool = deps.tool_registry.get(tool_id)
    if not tool:
        return jsonify({'success': False, 'error': 'Tool 未注册'}), 404
    return jsonify({'success': True, 'data': tool.definition.to_dict()})


@skills_bp.route('/tools/call', methods=['POST'])
def call_tool():
    try:
        data = request.get_json()
        if not data or not data.get('tool_id'):
            return jsonify({'success': False, 'error': '缺少 tool_id'}), 400

        from src.core.tool.types import ToolCallRequest
        req = ToolCallRequest(
            tool_id=data['tool_id'],
            arguments=data.get('arguments', {}),
            context=data.get('context', {}),
        )
        result = deps.tool_executor.execute(req)
        return jsonify({
            'success': result.success,
            'data': result.data,
            'error': result.error,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@skills_bp.route('/tools/skills/<skill_id>')
def get_skill_tools(skill_id):
    tools = deps.tool_registry.list_definitions(skill_id)
    return jsonify({'success': True, 'data': tools})


@skills_bp.route('/health')
def health_check():
    skill_count = len(deps.skill_registry.get_all())
    tool_count = len(deps.tool_registry.get_all())
    return jsonify({
        'status': 'healthy',
        'service': 'interview-companion-multi-scenario',
        'skills_registered': skill_count,
        'tools_registered': tool_count,
    })
