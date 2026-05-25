"""
数据库功能测试脚本

测试内容：
1. 用户注册/登录
2. 简历数据持久化
3. 项目数据持久化
4. 追问记录存储
"""

from src.services.database_service import DatabaseService

def test_database():
    print("=== 数据库功能测试 ===")
    db = DatabaseService()
    
    # 1. 测试用户注册
    print("\n1. 用户注册测试")
    register_result = db.register_user(
        email="test@example.com",
        password="test123456",
        username="testuser"
    )
    print(f"注册结果: {register_result}")
    
    if register_result["success"]:
        user_id = register_result["user_id"]
        
        # 2. 测试用户登录
        print("\n2. 用户登录测试")
        login_result = db.login_user(
            email="test@example.com",
            password="test123456"
        )
        print(f"登录结果: {login_result}")
        
        if login_result["success"]:
            # 3. 测试创建简历
            print("\n3. 创建简历测试")
            resume_result = db.create_resume(
                user_id=user_id,
                resume_data={
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "phone": "13800138000",
                    "education": "本科",
                    "experience": "3年后端开发经验",
                    "skills": "Java, Spring Boot, MySQL, Redis"
                }
            )
            print(f"创建简历结果: {resume_result}")
            
            if resume_result["success"]:
                resume_id = resume_result["resume_id"]
                
                # 4. 测试创建项目
                print("\n4. 创建项目测试")
                project_result = db.create_project(
                    resume_id=resume_id,
                    project_data={
                        "name": "电商订单管理系统",
                        "description": "负责订单模块的设计与开发，包含订单创建、支付、发货等功能",
                        "tech_stack": ["Java", "Spring Boot", "MySQL", "Redis"],
                        "project_time": "2023-01 至 2023-12",
                        "responsibilities": "需求分析、架构设计、核心代码实现",
                        "results": "订单处理性能提升30%"
                    }
                )
                print(f"创建项目结果: {project_result}")
                
                if project_result["success"]:
                    project_id = project_result["project_id"]
                    
                    # 5. 测试创建追问记录
                    print("\n5. 创建追问记录测试")
                    questions = [
                        {
                            "question": "你在项目中使用的数据库是什么？如何进行数据库优化的？",
                            "logic": "考察后端开发者的数据库设计和优化能力"
                        },
                        {
                            "question": "项目中有没有使用缓存？缓存策略是什么？",
                            "logic": "考察后端开发者对缓存的理解"
                        },
                        {
                            "question": "如果系统突然遇到高并发场景，你的服务会如何应对？",
                            "logic": "考察后端开发者的高并发处理能力"
                        }
                    ]
                    record_result = db.create_question_record(
                        project_id=project_id,
                        questions=questions
                    )
                    print(f"创建追问记录结果: {record_result}")
                    
                    # 6. 测试查询追问记录
                    print("\n6. 查询追问记录测试")
                    records = db.get_question_records(project_id=project_id)
                    print(f"查询到 {len(records)} 条追问记录")
                    if records:
                        for i, record in enumerate(records):
                            print(f"\n记录 {i+1}:")
                            print(f"  时间: {record['created_at']}")
                            print(f"  问题数量: {record['question_count']}")
                            for j, q in enumerate(record.get('questions', [])):
                                print(f"  问题 {j+1}: {q['question']}")
                                print(f"  逻辑: {q['logic']}")
        
        # 7. 测试获取用户所有简历
        print("\n7. 获取用户简历列表测试")
        resumes = db.get_resumes(user_id=user_id)
        print(f"用户 {user_id} 共有 {len(resumes)} 份简历")
        
    print("\n=== 数据库测试完成 ===")

if __name__ == "__main__":
    test_database()
