"""用户服务 - 用户管理和徽章收集"""

import uuid

class UserService:
    def __init__(self):
        # 模拟数据库
        self.users = {}
        self.user_badges = {}
        self.review_records = {}
    
    def create_user(self, nickname, email=None, avatar_url=None):
        """创建用户"""
        user_id = str(uuid.uuid4())
        user = {
            'id': user_id,
            'nickname': nickname,
            'email': email,
            'avatar_url': avatar_url,
            'created_at': str(uuid.uuid1())[:19]  # 简化时间戳
        }
        self.users[user_id] = user
        return user
    
    def get_user(self, user_id):
        """获取用户信息"""
        return self.users.get(user_id)
    
    def get_or_create_user(self, user_info):
        """获取或创建用户"""
        # 简单实现：如果没有用户ID，创建新用户
        if not user_info.get('user_id'):
            return self.create_user(user_info.get('nickname', '用户'))
        return self.get_user(user_info['user_id'])
    
    def add_user_badge(self, user_id, badge):
        """为用户添加徽章"""
        if user_id not in self.user_badges:
            self.user_badges[user_id] = []
        
        # 检查是否已拥有该徽章
        if badge['name'] not in [b['name'] for b in self.user_badges[user_id]]:
            self.user_badges[user_id].append(badge)
            return True
        return False
    
    def get_user_badges(self, user_id):
        """获取用户已解锁的徽章"""
        return self.user_badges.get(user_id, [])
    
    def add_review_record(self, user_id, record):
        """添加复盘记录"""
        record_id = str(uuid.uuid4())
        record['id'] = record_id
        record['user_id'] = user_id
        
        if user_id not in self.review_records:
            self.review_records[user_id] = []
        
        self.review_records[user_id].append(record)
        return record
    
    def get_user_review_count(self, user_id):
        """获取用户复盘次数"""
        return len(self.review_records.get(user_id, []))
    
    def get_user_review_records(self, user_id):
        """获取用户所有复盘记录"""
        return self.review_records.get(user_id, [])
