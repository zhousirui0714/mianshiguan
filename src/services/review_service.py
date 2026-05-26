"""复盘服务 - 处理翻车类型识别、徽章生成、行动建议"""

import uuid
from src.database.data_init import BADGES_DATA, RESCUE_SCRIPTS_DATA, ACTION_SUGGESTIONS, CRASH_TYPES

class ReviewService:
    def __init__(self):
        self.badges = {badge['name']: badge for badge in BADGES_DATA}
        self.rescue_scripts = RESCUE_SCRIPTS_DATA
        self.action_suggestions = ACTION_SUGGESTIONS
        self.crash_types = CRASH_TYPES
    
    def identify_crash_type(self, description):
        """根据用户描述识别翻车类型"""
        description = description.lower()
        
        keywords = {
            'wrong_words': ['说错', '说错话', '说错了', '表述错误', '表达错误', '口误'],
            'stuck': ['卡壳', '卡住', '卡住了', '停顿', '不知道', '想不起来'],
            'cant_answer': ['不会', '不会答', '答不上', '不知道', '没接触'],
            'nervous': ['紧张', '慌了', '发挥失常', '手抖', '心跳加速']
        }
        
        for crash_type, kw_list in keywords.items():
            for kw in kw_list:
                if kw in description:
                    return crash_type
        
        return 'other'
    
    def generate_badge(self, crash_type, review_count=1):
        """根据翻车类型和复盘次数生成徽章"""
        badge_map = {
            'wrong_words': '说错话大师',
            'stuck': '卡壳终结者',
            'cant_answer': '诚实勇敢',
            'nervous': '抗压能手',
            'other': '初出茅庐'
        }
        
        # 根据条件返回不同徽章
        if review_count >= 5:
            return self.badges.get('复盘达人')
        if crash_type in badge_map:
            return self.badges.get(badge_map[crash_type])
        return self.badges.get('初出茅庐')
    
    def generate_action_items(self, crash_type):
        """根据翻车类型生成行动建议"""
        return self.action_suggestions.get(crash_type, self.action_suggestions['other'])
    
    def get_rescue_scripts(self, crash_type):
        """获取对应翻车类型的救援话术"""
        return [script for script in self.rescue_scripts if script['crash_type'] == crash_type]
    
    def create_review_session(self, user_id, company_name, position, crash_type):
        """创建复盘会话"""
        session_id = str(uuid.uuid4())
        return {
            'session_id': session_id,
            'user_id': user_id,
            'company_name': company_name,
            'position': position,
            'crash_type': crash_type,
            'crash_type_label': self.crash_types.get(crash_type, crash_type),
            'quiz_questions': self._generate_quiz_questions(crash_type)
        }
    
    def _generate_quiz_questions(self, crash_type):
        """生成引导问答题目"""
        base_questions = [
            {
                'id': 'q1',
                'question': '这次面试中，你最不满意自己表现的是哪个环节？',
                'type': 'text'
            },
            {
                'id': 'q2',
                'question': '如果重新来一次，你会如何改进这个环节？',
                'type': 'text'
            },
            {
                'id': 'q3',
                'question': '这个经历给你最大的教训是什么？',
                'type': 'text'
            }
        ]
        
        return base_questions
    
    def get_all_badges(self):
        """获取所有徽章列表"""
        return BADGES_DATA
    
    def get_all_rescue_scripts(self):
        """获取所有救援话术"""
        return self.rescue_scripts
    
    def get_crash_types(self):
        """获取所有翻车类型"""
        return [{'value': k, 'label': v} for k, v in self.crash_types.items()]
