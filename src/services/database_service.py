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

# 导出
__all__ = ["DatabaseService"]
