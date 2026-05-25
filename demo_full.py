"""
个人极简面试官 - 完整演示程序

整合功能：
1. 用户注册/登录
2. 简历管理
3. 项目管理
4. AI追问生成（DeepSeek API）
5. 追问记录存储
"""

from src.services.database_service import DatabaseService
from src.services.llm_client import LLMClient
from src.utils.logger import Logger

def main():
    print("="*60)
    print("          个人极简面试官 - 完整演示          ")
    print("="*60)
    
    # 初始化服务
    db = DatabaseService()
    llm_client = LLMClient()
    logger = Logger()
    
    # 用户注册
    print("\n步骤1：用户注册")
    register_result = db.register_user(
        email="demo@example.com",
        password="demo123",
        username="demouser"
    )
    if register_result["success"]:
        user_id = register_result["user_id"]
        print("注册成功！用户ID: %s..." % user_id[:8])
    else:
        print("注册失败: %s" % register_result["error"])
        return
    
    # 用户登录
    print("\n步骤2：用户登录")
    login_result = db.login_user(email="demo@example.com", password="demo123")
    if login_result["success"]:
        print("登录成功！欢迎, %s" % login_result["username"])
    else:
        print("登录失败: %s" % login_result["error"])
        return
    
    # 创建简历
    print("\n步骤3：创建简历")
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
    if resume_result["success"]:
        resume_id = resume_result["resume_id"]
        print("简历创建成功！简历ID: %s..." % resume_id[:8])
    else:
        print("简历创建失败: %s" % resume_result["error"])
        return
    
    # 创建项目
    print("\n步骤4：创建项目")
    project_result = db.create_project(
        resume_id=resume_id,
        project_data={
            "name": "电商订单管理系统",
            "description": "负责订单模块的设计与开发，包含订单创建、支付、发货等核心功能。使用Spring Boot + MySQL + Redis技术栈，实现了高可用的分布式订单系统。",
            "tech_stack": ["Java", "Spring Boot", "MySQL", "Redis"],
            "project_time": "2023-01 至 2023-12",
            "responsibilities": "需求分析、架构设计、核心代码实现、性能优化",
            "results": "订单处理性能提升30%，系统稳定性达到99.9%"
        }
    )
    if project_result["success"]:
        project_id = project_result["project_id"]
        print("项目创建成功！项目ID: %s..." % project_id[:8])
    else:
        print("项目创建失败: %s" % project_result["error"])
        return
    
    # AI生成追问（带日志链路）
    print("\n步骤5：AI生成刁钻追问")
    request_id = logger.generate_request_id()
    
    # 记录进入日志
    logger.log_entry(
        request_id=request_id,
        endpoint="/api/questions/generate",
        method="POST",
        user_id=user_id,
        params={
            "project_id": project_id,
            "project_name": "电商订单管理系统",
            "tech_stack": ["Java", "Spring Boot", "MySQL", "Redis"]
        }
    )
    
    # 记录步骤日志 - 验证输入
    logger.log_step(request_id=request_id, step="validate_input", status="IN_PROGRESS")
    
    # 记录步骤日志 - 调用LLM
    logger.log_step(request_id=request_id, step="call_llm", status="IN_PROGRESS", details={"model": "deepseek-chat"})
    
    # 调用LLM生成追问
    try:
        result = llm_client.generate_questions_with_fallback(
            project_description="负责订单模块的设计与开发，包含订单创建、支付、发货等核心功能。使用Spring Boot + MySQL + Redis技术栈，实现了高可用的分布式订单系统。",
            tech_stack=["Java", "Spring Boot", "MySQL", "Redis"]
        )
        
        # 记录步骤日志 - 解析结果
        logger.log_step(request_id=request_id, step="parse_result", status="COMPLETED")
        
        questions = result.get("questions", [])
        
        # 保存追问记录到数据库
        save_result = db.create_question_record(project_id=project_id, questions=questions)
        if save_result["success"]:
            print("追问记录已保存！记录ID: %s..." % save_result["record_id"][:8])
        else:
            print("追问记录保存失败: %s" % save_result["error"])
        
        # 记录退出日志
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/questions/generate",
            success=True,
            latency_ms=0,
            result={"question_count": len(questions)}
        )
        
        # 展示生成的追问
        print("\n生成的刁钻追问：")
        for i, q in enumerate(questions, 1):
            print("\n%d. %s" % (i, q["question"]))
            print("   追问逻辑: %s" % q["logic"])
        
        # 从数据库查询验证
        print("\n从数据库查询追问记录：")
        records = db.get_question_records(project_id=project_id)
        if records:
            record = records[0]
            print("查询到 %d 条记录" % len(records))
            print("记录时间: %s" % record["created_at"])
    
    except Exception as e:
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/questions/generate",
            success=False,
            latency_ms=0,
            error=str(e)
        )
        print("生成失败: %s" % e)
    
    print("\n" + "="*60)
    print("              演示完成！              ")
    print("="*60)

if __name__ == "__main__":
    main()
