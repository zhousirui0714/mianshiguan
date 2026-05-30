"""复盘服务 - 处理翻车类型识别、徽章生成、行动建议"""

import uuid
import random
from src.database.data_init import BADGES_DATA, RESCUE_SCRIPTS_DATA, ACTION_SUGGESTIONS, CRASH_TYPES, QUIZ_QUESTIONS, BADGE_MODIFIERS, BADGE_SUFFIXES

class ReviewService:
    def __init__(self):
        self.badges = {badge['name']: badge for badge in BADGES_DATA}
        self.rescue_scripts = RESCUE_SCRIPTS_DATA
        self.action_suggestions = ACTION_SUGGESTIONS
        self.crash_types = CRASH_TYPES
        self.quiz_questions = QUIZ_QUESTIONS
        self.badge_modifiers = BADGE_MODIFIERS
        self.badge_suffixes = BADGE_SUFFIXES
    
    def identify_crash_type(self, description):
        """根据用户描述识别翻车类型"""
        description = description.lower()
        
        keywords = {
            'wrong_words': ['说错', '说错话', '说错了', '表述错误', '表达错误', '口误'],
            'stuck': ['卡壳', '卡住', '卡住了', '停顿', '不知道', '想不起来', '忘词'],
            'cant_answer': ['不会', '不会答', '答不上', '不知道', '没接触', '不懂'],
            'nervous': ['紧张', '慌了', '发挥失常', '手抖', '心跳加速', '声音颤']
        }
        
        for crash_type, kw_list in keywords.items():
            for kw in kw_list:
                if kw in description:
                    return crash_type
        
        return 'other'
    
    def generate_badge(self, crash_type, user_stats=None):
        """根据翻车类型和用户统计生成徽章"""
        if user_stats is None:
            user_stats = {}
        
        review_count = user_stats.get('total_reviews', 0)
        crash_type_count = user_stats.get('crash_type_counts', {}).get(crash_type, 0)
        same_company_count = user_stats.get('same_company_count', 0)
        consecutive_days = user_stats.get('consecutive_days', 0)
        
        # 稀有度判定
        rarity = 'common'
        if crash_type_count >= 10 or consecutive_days >= 7:
            rarity = 'epic'
        elif crash_type_count >= 3:
            rarity = 'rare'
        
        # 检查特殊成就
        if same_company_count >= 3:
            return self.badges.get('面试不死鸟')
        
        if consecutive_days >= 7:
            return self.badges.get('连续作战王')
        
        # 根据翻车类型返回对应徽章
        badge_map = {
            'wrong_words': {'common': '嘴瓢新手', 'rare': '嘴瓢收藏家'},
            'stuck': {'common': '卡壳新手', 'rare': '卡壳终结者'},
            'cant_answer': {'common': '首翻勇士', 'rare': '复盘达人'},
            'nervous': {'common': '紧张新手', 'rare': '复盘达人'},
            'other': {'common': '首翻勇士', 'rare': '复盘达人'}
        }
        
        if review_count == 0:
            return self.badges.get('首翻勇士')
        
        if crash_type in badge_map:
            badge_name = badge_map[crash_type].get(rarity, badge_map[crash_type]['common'])
            return self.badges.get(badge_name, self.badges.get('首翻勇士'))
        
        return self.badges.get('首翻勇士')
    
    def generate_action_items(self, crash_type):
        """根据翻车类型生成行动建议"""
        suggestions = self.action_suggestions.get(crash_type, self.action_suggestions['other'])
        # 随机抽取3条
        if len(suggestions) > 3:
            return random.sample(suggestions, 3)
        return suggestions
    
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
        """生成引导问答题目 - 随机抽取3-5题"""
        num_questions = random.randint(3, 5)
        selected_questions = random.sample(self.quiz_questions, min(num_questions, len(self.quiz_questions)))
        
        # 确保问题顺序随机
        random.shuffle(selected_questions)
        
        return selected_questions
    
    def get_all_badges(self):
        """获取所有徽章列表"""
        return BADGES_DATA
    
    def get_all_rescue_scripts(self):
        """获取所有救援话术"""
        return self.rescue_scripts
    
    def get_crash_types(self):
        """获取所有翻车类型"""
        return [{'value': k, 'label': v} for k, v in self.crash_types.items()]