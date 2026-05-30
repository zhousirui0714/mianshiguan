"""
数据库服务 - 模拟版本（用于演示）

功能：
1. 用户注册/登录
2. 简历和项目数据持久化
3. 追问记录存储
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

class DatabaseService:
    def __init__(self):
        # 模拟数据库表
        self.users = {}
        self.resumes = {}
        self.projects = {}
        self.question_records = {}
        self.question_details = {}
        # 新增：对话历史表
        self.conversations = {}
        self.conversation_messages = {}
        # 新增：题库表
        self.questions = {}
        # 新增：徽章表
        self.badge_master = {}
        self.user_badges = {}
        
        # 初始化预置数据
        self._init_default_questions()
        self._init_default_badges()
    
    # ==================== 用户管理 ====================
    
    def register_user(self, email: str, password: str, username: str) -> Dict[str, Any]:
        """用户注册"""
        try:
            user_id = str(uuid4())
            self.users[user_id] = {
                "id": user_id,
                "email": email,
                "password": password,  # 注意：实际生产中应加密存储
                "username": username,
                "created_at": datetime.now().isoformat()
            }
            return {
                "success": True,
                "user_id": user_id,
                "email": email,
                "username": username
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        try:
            for user_id, user in self.users.items():
                if user["email"] == email and user["password"] == password:
                    return {
                        "success": True,
                        "user_id": user_id,
                        "email": user["email"],
                        "username": user["username"],
                        "access_token": str(uuid4())
                    }
            return {"success": False, "error": "邮箱或密码错误"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户资料"""
        return self.users.get(user_id)
    
    # ==================== 简历管理 ====================
    
    def create_resume(self, user_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建简历"""
        try:
            resume_id = str(uuid4())
            self.resumes[resume_id] = {
                "id": resume_id,
                "user_id": user_id,
                "name": resume_data.get("name", ""),
                "email": resume_data.get("email", ""),
                "phone": resume_data.get("phone", ""),
                "education": resume_data.get("education", ""),
                "experience": resume_data.get("experience", ""),
                "skills": resume_data.get("skills", ""),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            return {"success": True, "resume_id": resume_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_resumes(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有简历"""
        return [r for r in self.resumes.values() if r["user_id"] == user_id]
    
    def update_resume(self, resume_id: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新简历"""
        try:
            if resume_id in self.resumes:
                self.resumes[resume_id].update({
                    k: v for k, v in resume_data.items() if k in ["name", "email", "phone", "education", "experience", "skills"]
                })
                self.resumes[resume_id]["updated_at"] = datetime.now().isoformat()
                return {"success": True}
            return {"success": False, "error": "简历不存在"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== 项目管理 ====================
    
    def create_project(self, resume_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建项目"""
        try:
            project_id = str(uuid4())
            self.projects[project_id] = {
                "id": project_id,
                "resume_id": resume_id,
                "name": project_data.get("name", ""),
                "description": project_data.get("description", ""),
                "tech_stack": project_data.get("tech_stack", []),
                "project_time": project_data.get("project_time", ""),
                "responsibilities": project_data.get("responsibilities", ""),
                "results": project_data.get("results", ""),
                "created_at": datetime.now().isoformat()
            }
            return {"success": True, "project_id": project_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_projects(self, resume_id: str) -> List[Dict[str, Any]]:
        """获取简历下所有项目"""
        return [p for p in self.projects.values() if p["resume_id"] == resume_id]
    
    # ==================== 追问记录管理 ====================
    
    def create_question_record(self, project_id: str, questions: List[Dict[str, str]]) -> Dict[str, Any]:
        """创建追问记录"""
        try:
            record_id = str(uuid4())
            # 创建主记录
            self.question_records[record_id] = {
                "id": record_id,
                "project_id": project_id,
                "question_count": len(questions),
                "created_at": datetime.now().isoformat()
            }
            # 创建每条追问详情
            for idx, q in enumerate(questions):
                detail_id = str(uuid4())
                self.question_details[detail_id] = {
                    "id": detail_id,
                    "record_id": record_id,
                    "question_text": q.get("question", ""),
                    "logic": q.get("logic", ""),
                    "order_index": idx + 1
                }
            return {"success": True, "record_id": record_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_question_records(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目的所有追问记录"""
        records = []
        for record_id, record in self.question_records.items():
            if record["project_id"] == project_id:
                # 获取详细问题
                details = [
                    d for d in self.question_details.values() 
                    if d["record_id"] == record_id
                ]
                details.sort(key=lambda x: x["order_index"])
                record_copy = record.copy()
                record_copy["questions"] = [{
                    "question": d["question_text"],
                    "logic": d["logic"]
                } for d in details]
                records.append(record_copy)
        return records
    
    # ==================== 对话历史管理 ====================
    
    def create_conversation(self, user_id: str, scenario_id: str, 
                           scenario_name: str, user_background: str = "") -> Dict[str, Any]:
        """创建新对话"""
        try:
            conversation_id = str(uuid4())
            self.conversations[conversation_id] = {
                "id": conversation_id,
                "user_id": user_id,
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "user_background": user_background,
                "status": "active",
                "round_count": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            return {"success": True, "conversation_id": conversation_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Dict[str, Any]:
        """添加消息到对话"""
        try:
            if conversation_id not in self.conversations:
                return {"success": False, "error": "对话不存在"}
            
            message_id = str(uuid4())
            conversation = self.conversations[conversation_id]
            
            # 获取当前消息序号
            messages = self.get_conversation_messages(conversation_id)
            message_order = len(messages) + 1
            
            # 更新对话轮次（每两条消息为一轮：用户+助手）
            if role == "assistant":
                conversation["round_count"] += 1
                conversation["updated_at"] = datetime.now().isoformat()
            
            self.conversation_messages[message_id] = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "order": message_order,
                "created_at": datetime.now().isoformat()
            }
            
            return {"success": True, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话的所有消息"""
        messages = [
            m for m in self.conversation_messages.values() 
            if m["conversation_id"] == conversation_id
        ]
        messages.sort(key=lambda x: x["order"])
        return messages
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取对话详情"""
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id].copy()
        conversation["messages"] = self.get_conversation_messages(conversation_id)
        return conversation
    
    def update_conversation_status(self, conversation_id: str, status: str) -> Dict[str, Any]:
        """更新对话状态"""
        try:
            if conversation_id not in self.conversations:
                return {"success": False, "error": "对话不存在"}
            
            self.conversations[conversation_id]["status"] = status
            self.conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有对话"""
        conversations = []
        for conv_id, conv in self.conversations.items():
            if conv["user_id"] == user_id:
                conv_copy = conv.copy()
                conv_copy["messages"] = self.get_conversation_messages(conv_id)
                conversations.append(conv_copy)
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations
    
    # ==================== 题库管理 ====================
    
    def _init_default_questions(self):
        """初始化预置题目数据"""
        default_questions = [
            # 求职面试题目
            {
                "scenario": "job_interview",
                "category": "自我介绍",
                "difficulty": 2,
                "question_text": "请做一个简短的自我介绍。",
                "reference_answer": "自我介绍应包含：1. 基本信息（姓名、学历、工作年限）；2. 核心技能和优势；3. 职业目标。建议控制在1-2分钟内，突出与岗位匹配的能力。",
                "tags": ["自我介绍", "沟通表达"]
            },
            {
                "scenario": "job_interview",
                "category": "专业技能",
                "difficulty": 4,
                "question_text": "请介绍一下你最熟悉的技术栈，并举例说明在项目中的应用。",
                "reference_answer": "考察技术深度和项目经验。应：1. 清晰说明技术栈；2. 结合具体项目案例；3. 说明解决的问题和取得的成果；4. 展示技术选型的思考过程。",
                "tags": ["技术栈", "项目经验"]
            },
            {
                "scenario": "job_interview",
                "category": "项目经验",
                "difficulty": 4,
                "question_text": "请描述一个你负责的最有挑战性的项目，遇到了什么困难，如何解决的？",
                "reference_answer": "建议使用STAR法则：Situation（背景）、Task（任务）、Action（行动）、Result（结果）。重点突出解决问题的能力和团队协作。",
                "tags": ["项目经验", "问题解决"]
            },
            {
                "scenario": "job_interview",
                "category": "应变能力",
                "difficulty": 3,
                "question_text": "如果你与同事意见不合，你会如何处理？",
                "reference_answer": "考察沟通协调能力。应：1. 保持冷静；2. 倾听对方观点；3. 寻找共同点；4. 寻求双赢方案；5. 必要时寻求上级协调。",
                "tags": ["团队协作", "沟通"]
            },
            {
                "scenario": "job_interview",
                "category": "职业规划",
                "difficulty": 3,
                "question_text": "你的职业规划是什么？为什么选择我们公司？",
                "reference_answer": "1. 展示对行业和自身发展的思考；2. 表达对公司的了解和认同；3. 说明公司如何帮助实现个人目标。",
                "tags": ["职业规划", "求职动机"]
            },
            # 教资面试题目
            {
                "scenario": "teacher_cert",
                "category": "教育理念",
                "difficulty": 3,
                "question_text": "你认为一名优秀的教师应该具备哪些素质？",
                "reference_answer": "1. 扎实的专业知识；2. 良好的沟通能力；3. 爱心和耐心；4. 创新教学方法；5. 持续学习的态度；6. 职业道德。",
                "tags": ["教育理念", "教师素养"]
            },
            {
                "scenario": "teacher_cert",
                "category": "课堂管理",
                "difficulty": 4,
                "question_text": "如果课堂上学生突然吵闹，你会如何处理？",
                "reference_answer": "1. 保持冷静，不要情绪化；2. 使用非语言信号提醒；3. 课后单独沟通了解原因；4. 建立课堂规则；5. 采用积极的课堂管理策略。",
                "tags": ["课堂管理", "应变能力"]
            },
            {
                "scenario": "teacher_cert",
                "category": "教学设计",
                "difficulty": 4,
                "question_text": "如何设计一堂生动有趣的语文课？",
                "reference_answer": "1. 明确教学目标；2. 导入环节吸引兴趣；3. 多样化教学方法（讨论、小组活动、多媒体）；4. 提问互动；5. 课堂小结和作业布置。",
                "tags": ["教学设计", "教学方法"]
            },
            # 雅思口语题目
            {
                "scenario": "ielts_speaking",
                "category": "个人经历",
                "difficulty": 2,
                "question_text": "Describe a book that you enjoyed reading. You should say: What the book was about, When you read it, Why you liked it.",
                "reference_answer": "IELTS Speaking Part 2 话题。要点：1. 书名和作者；2. 内容简介；3. 阅读时间和情境；4. 喜欢的原因（情节、人物、启示等）；5. 使用丰富的词汇和连接词。",
                "tags": ["口语", "描述"]
            },
            {
                "scenario": "ielts_speaking",
                "category": "观点表达",
                "difficulty": 4,
                "question_text": "Do you agree that technology is making people more isolated?",
                "reference_answer": "IELTS Speaking Part 3 话题。结构：1. 表达观点；2. 举例支持；3. 反方观点；4. 总结。使用连接词和高级词汇。",
                "tags": ["口语", "观点"]
            },
            # 公务员面试题目
            {
                "scenario": "civil_service",
                "category": "综合分析",
                "difficulty": 4,
                "question_text": "谈谈你对'空谈误国，实干兴邦'的理解。",
                "reference_answer": "1. 解释含义；2. 结合实际案例；3. 联系自身工作；4. 说明如何践行。注重政治素养和辩证思维。",
                "tags": ["综合分析", "政治素养"]
            },
            {
                "scenario": "civil_service",
                "category": "应急处理",
                "difficulty": 5,
                "question_text": "如果你是基层工作人员，遇到群体性事件该如何处理？",
                "reference_answer": "1. 保持冷静，控制现场；2. 倾听诉求，安抚情绪；3. 及时上报；4. 依法处理；5. 事后总结改进。强调依法办事和为民服务意识。",
                "tags": ["应急处理", "群众工作"]
            },
            # 考研复试题目
            {
                "scenario": "graduate_school",
                "category": "专业基础",
                "difficulty": 4,
                "question_text": "请简述你所学专业的主要研究方向和前沿动态。",
                "reference_answer": "1. 清晰阐述专业领域；2. 介绍主要研究方向；3. 列举前沿研究成果；4. 说明自己的兴趣点和研究潜力。",
                "tags": ["专业基础", "学术潜力"]
            },
            {
                "scenario": "graduate_school",
                "category": "科研能力",
                "difficulty": 5,
                "question_text": "如果你被录取，你的研究计划是什么？",
                "reference_answer": "1. 研究目标；2. 研究方法；3. 创新点；4. 预期成果；5. 时间规划。展示学术思维和研究潜力。",
                "tags": ["科研规划", "学术能力"]
            },
            # MBA面试题目
            {
                "scenario": "mba_interview",
                "category": "领导力",
                "difficulty": 4,
                "question_text": "请举例说明你在团队中的领导经历。",
                "reference_answer": "使用STAR法则：1. 背景和团队情况；2. 目标和挑战；3. 领导行动；4. 结果和影响。展示领导力、决策能力和团队管理能力。",
                "tags": ["领导力", "团队管理"]
            },
            {
                "scenario": "mba_interview",
                "category": "职业规划",
                "difficulty": 3,
                "question_text": "为什么要读MBA？MBA对你的职业发展有什么帮助？",
                "reference_answer": "1. 明确职业瓶颈；2. MBA能提供的价值（知识、人脉、平台）；3. 具体的职业目标；4. 目标院校的匹配度。",
                "tags": ["职业规划", "MBA"]
            }
        ]
        
        for idx, question in enumerate(default_questions):
            question_id = f"q_{idx + 1:04d}"
            self.questions[question_id] = {
                "id": question_id,
                **question,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
    
    def add_question(self, scenario: str, category: str, difficulty: int, 
                     question_text: str, reference_answer: str, tags: List[str]) -> Dict[str, Any]:
        """添加新题目"""
        try:
            question_id = str(uuid4())
            self.questions[question_id] = {
                "id": question_id,
                "scenario": scenario,
                "category": category,
                "difficulty": difficulty,
                "question_text": question_text,
                "reference_answer": reference_answer,
                "tags": tags,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            return {"success": True, "question_id": question_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_questions(self, scenario: str = None, category: str = None, 
                      difficulty: int = None, keyword: str = None) -> List[Dict[str, Any]]:
        """查询题目列表"""
        questions = list(self.questions.values())
        
        # 场景筛选
        if scenario:
            questions = [q for q in questions if q["scenario"] == scenario]
        
        # 分类筛选
        if category:
            questions = [q for q in questions if q["category"] == category]
        
        # 难度筛选
        if difficulty:
            questions = [q for q in questions if q["difficulty"] == difficulty]
        
        # 关键词搜索
        if keyword:
            keyword = keyword.lower()
            questions = [q for q in questions 
                        if keyword in q["question_text"].lower() or
                           keyword in q["category"].lower() or
                           any(keyword in tag.lower() for tag in q["tags"])]
        
        # 按创建时间排序
        questions.sort(key=lambda x: x["created_at"], reverse=True)
        return questions
    
    def get_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """获取单个题目详情"""
        return self.questions.get(question_id)
    
    def update_question(self, question_id: str, **kwargs) -> Dict[str, Any]:
        """更新题目信息"""
        try:
            if question_id not in self.questions:
                return {"success": False, "error": "题目不存在"}
            
            question = self.questions[question_id]
            for key, value in kwargs.items():
                if key in ["scenario", "category", "difficulty", "question_text", 
                          "reference_answer", "tags"]:
                    question[key] = value
            question["updated_at"] = datetime.now().isoformat()
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_question(self, question_id: str) -> Dict[str, Any]:
        """删除题目"""
        try:
            if question_id not in self.questions:
                return {"success": False, "error": "题目不存在"}
            
            del self.questions[question_id]
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_categories(self, scenario: str = None) -> List[str]:
        """获取所有分类"""
        categories = set()
        for q in self.questions.values():
            if scenario and q["scenario"] != scenario:
                continue
            categories.add(q["category"])
        return sorted(list(categories))
    
    def get_tags(self, scenario: str = None) -> List[str]:
        """获取所有标签"""
        tags = set()
        for q in self.questions.values():
            if scenario and q["scenario"] != scenario:
                continue
            tags.update(q["tags"])
        return sorted(list(tags))
    
    # ==================== 徽章管理 ====================
    
    def _init_default_badges(self):
        """初始化预置徽章数据"""
        badges = [
            # 新手入门
            {
                "id": "badge_001",
                "name": "初试啼声",
                "description": "完成第一次模拟练习，迈出成功的第一步！",
                "icon": "🐣",
                "category": "newbie",
                "unlock_condition": {"type": "first_practice"},
                "rarity": "common"
            },
            {
                "id": "badge_002",
                "name": "首战告捷",
                "description": "首次练习得分达到80分以上，实力不俗！",
                "icon": "🎯",
                "category": "newbie",
                "unlock_condition": {"type": "first_high_score", "threshold": 80},
                "rarity": "rare"
            },
            {
                "id": "badge_003",
                "name": "认真学习",
                "description": "查看5道题目解析，知识积累中...",
                "icon": "📚",
                "category": "newbie",
                "unlock_condition": {"type": "view_explanations", "count": 5},
                "rarity": "common"
            },
            # 坚持打卡
            {
                "id": "badge_004",
                "name": "三日打鱼",
                "description": "连续3天登录练习，养成好习惯！",
                "icon": "🔥",
                "category": "persistence",
                "unlock_condition": {"type": "streak", "days": 3},
                "rarity": "common"
            },
            {
                "id": "badge_005",
                "name": "持之以恒",
                "description": "累计完成10次练习，坚持不懈！",
                "icon": "💪",
                "category": "persistence",
                "unlock_condition": {"type": "total_practices", "count": 10},
                "rarity": "rare"
            },
            {
                "id": "badge_006",
                "name": "百日维新",
                "description": "连续30天登录，坚持就是胜利！",
                "icon": "🏆",
                "category": "persistence",
                "unlock_condition": {"type": "streak", "days": 30},
                "rarity": "legendary"
            },
            # 场景挑战
            {
                "id": "badge_007",
                "name": "求职达人",
                "description": "求职面试场景得分达到90分以上！",
                "icon": "🎤",
                "category": "scenario",
                "unlock_condition": {"type": "scenario_high_score", "scenario": "job_interview", "threshold": 90},
                "rarity": "epic"
            },
            {
                "id": "badge_008",
                "name": "教资通关",
                "description": "教资面试场景完成3次练习！",
                "icon": "🍎",
                "category": "scenario",
                "unlock_condition": {"type": "scenario_practices", "scenario": "teacher_cert", "count": 3},
                "rarity": "rare"
            },
            {
                "id": "badge_009",
                "name": "雅思突破",
                "description": "雅思口语场景完成5次练习！",
                "icon": "🌍",
                "category": "scenario",
                "unlock_condition": {"type": "scenario_practices", "scenario": "ielts_speaking", "count": 5},
                "rarity": "epic"
            },
            # 特殊成就
            {
                "id": "badge_010",
                "name": "越挫越勇",
                "description": "同一场景练习5次后，得分提升20分！",
                "icon": "🔄",
                "category": "special",
                "unlock_condition": {"type": "improvement", "scenario_count": 5, "improvement": 20},
                "rarity": "epic"
            },
            {
                "id": "badge_011",
                "name": "秒杀全场",
                "description": "30秒内完成答题且得分≥85分！",
                "icon": "⚡",
                "category": "special",
                "unlock_condition": {"type": "speed_score", "duration": 30, "threshold": 85},
                "rarity": "legendary"
            },
            {
                "id": "badge_012",
                "name": "全能选手",
                "description": "所有场景各完成1次练习！",
                "icon": "🎭",
                "category": "special",
                "unlock_condition": {"type": "all_scenarios"},
                "rarity": "legendary"
            }
        ]
        
        for badge in badges:
            self.badge_master[badge["id"]] = {
                **badge,
                "created_at": datetime.now().isoformat()
            }
    
    def get_all_badges(self) -> List[Dict[str, Any]]:
        """获取所有徽章"""
        return list(self.badge_master.values())
    
    def get_badge(self, badge_id: str) -> Optional[Dict[str, Any]]:
        """获取单个徽章详情"""
        return self.badge_master.get(badge_id)
    
    def get_user_badges(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户已解锁的徽章"""
        user_badge_ids = [ub["badge_id"] for ub in self.user_badges.values() if ub["user_id"] == user_id]
        badges = []
        for badge_id in user_badge_ids:
            badge = self.badge_master.get(badge_id)
            if badge:
                user_badge = next(ub for ub in self.user_badges.values() if ub["user_id"] == user_id and ub["badge_id"] == badge_id)
                badges.append({
                    **badge,
                    "unlocked_at": user_badge["unlocked_at"],
                    "is_new": user_badge["is_new"]
                })
        badges.sort(key=lambda x: x["unlocked_at"], reverse=True)
        return badges
    
    def unlock_badge(self, user_id: str, badge_id: str) -> Dict[str, Any]:
        """解锁徽章"""
        try:
            # 检查徽章是否存在
            if badge_id not in self.badge_master:
                return {"success": False, "error": "徽章不存在"}
            
            # 检查是否已解锁
            for ub in self.user_badges.values():
                if ub["user_id"] == user_id and ub["badge_id"] == badge_id:
                    return {"success": False, "error": "徽章已解锁"}
            
            # 创建解锁记录
            record_id = str(uuid4())
            self.user_badges[record_id] = {
                "id": record_id,
                "user_id": user_id,
                "badge_id": badge_id,
                "unlocked_at": datetime.now().isoformat(),
                "is_new": True
            }
            
            return {"success": True, "badge_id": badge_id}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def check_badge_unlock(self, user_id: str, scenario: str, score: int, duration: int = None) -> List[Dict[str, Any]]:
        """
        检查并解锁符合条件的徽章
        
        参数：
        - user_id: 用户ID
        - scenario: 场景ID
        - score: 得分
        - duration: 答题时长（秒）
        
        返回：新解锁的徽章列表
        """
        new_badges = []
        
        # 获取用户当前已解锁的徽章
        user_badge_ids = {ub["badge_id"] for ub in self.user_badges.values() if ub["user_id"] == user_id}
        
        # 获取用户的练习记录
        user_conversations = self.get_user_conversations(user_id)
        practice_count = len(user_conversations)
        
        # 检查每个徽章的解锁条件
        for badge in self.badge_master.values():
            if badge["id"] in user_badge_ids:
                continue
            
            condition = badge["unlock_condition"]
            unlocked = False
            
            # 根据条件类型判断
            if condition["type"] == "first_practice":
                unlocked = practice_count >= 1
            
            elif condition["type"] == "first_high_score":
                # 检查是否是第一次练习且得分达标
                if practice_count == 1 and score >= condition["threshold"]:
                    unlocked = True
            
            elif condition["type"] == "total_practices":
                unlocked = practice_count >= condition["count"]
            
            elif condition["type"] == "streak":
                # 简化处理：检查最近练习次数
                unlocked = practice_count >= condition["days"]
            
            elif condition["type"] == "scenario_high_score":
                if scenario == condition["scenario"] and score >= condition["threshold"]:
                    unlocked = True
            
            elif condition["type"] == "scenario_practices":
                scenario_count = sum(1 for conv in user_conversations if conv["scenario_id"] == condition["scenario"])
                unlocked = scenario_count >= condition["count"]
            
            elif condition["type"] == "speed_score":
                if duration and duration <= condition["duration"] and score >= condition["threshold"]:
                    unlocked = True
            
            elif condition["type"] == "all_scenarios":
                completed_scenarios = {conv["scenario_id"] for conv in user_conversations}
                all_scenarios = {"job_interview", "teacher_cert", "ielts_speaking", "civil_service", "graduate_school", "mba_interview"}
                unlocked = completed_scenarios >= all_scenarios
            
            elif condition["type"] == "view_explanations":
                # 简化处理：练习次数达到一定数量视为查看了解析
                unlocked = practice_count >= condition["count"]
            
            elif condition["type"] == "improvement":
                # 简化处理：同一场景练习次数达标
                scenario_count = sum(1 for conv in user_conversations if conv["scenario_id"] == scenario)
                unlocked = scenario_count >= condition["scenario_count"]
            
            if unlocked:
                result = self.unlock_badge(user_id, badge["id"])
                if result["success"]:
                    new_badges.append(badge)
        
        return new_badges
    
    def mark_badge_as_viewed(self, user_id: str, badge_id: str) -> Dict[str, Any]:
        """标记徽章已查看"""
        try:
            for ub in self.user_badges.values():
                if ub["user_id"] == user_id and ub["badge_id"] == badge_id:
                    ub["is_new"] = False
                    return {"success": True}
            return {"success": False, "error": "用户徽章记录不存在"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_new_badge_count(self, user_id: str) -> int:
        """获取用户未查看的新徽章数量"""
        return sum(1 for ub in self.user_badges.values() if ub["user_id"] == user_id and ub["is_new"])

# 导出
__all__ = ["DatabaseService"]
