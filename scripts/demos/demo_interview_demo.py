"""
个人极简面试官 - 预设场景演示

流程：
1. 面试者介绍岗位需求
2. 面试者自我介绍
3. AI面试官生成针对性追问

使用预设数据，无需用户输入
"""

from src.services.llm_client import LLMClient
from src.utils.logger import Logger
import time

def print_slow(text, delay=0.02):
    """慢速打印，模拟对话效果"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def main():
    print("="*70)
    print("          个人极简面试官 - 真实面试场景演示          ")
    print("="*70)
    print()
    
    # 初始化服务
    llm_client = LLMClient()
    logger = Logger()
    request_id = logger.generate_request_id()
    
    # ------------------------------
    # 步骤1：面试者介绍岗位需求
    # ------------------------------
    print("="*70)
    print("步骤1：面试者介绍目标岗位")
    print("="*70)
    print()
    
    # 预设数据
    position = "Java后端开发工程师"
    tech_required = "Java, Spring Boot, MySQL, Redis"
    experience = "3-5年"
    round_info = "一面（技术面）"
    
    print_slow("面试者：我想面试贵公司的「Java后端开发工程师」岗位。")
    print_slow("这个岗位要求：%s，需要%s经验，我现在参加的是%s。" % (tech_required, experience, round_info))
    print()
    
    # ------------------------------
    # 步骤2：面试者自我介绍
    # ------------------------------
    print("="*70)
    print("步骤2：面试者自我介绍")
    print("="*70)
    print()
    
    # 预设数据
    name = "张三"
    years = "3年"
    skills = "Java, Spring Boot, MySQL, Redis, 微服务"
    project = "负责电商订单系统开发，使用Spring Boot + MySQL + Redis技术栈，实现了高可用的分布式订单系统，订单处理性能提升30%。"
    
    print_slow("面试官您好！我叫%s，有%s工作经验。" % (name, years))
    print_slow("核心技能包括：%s" % skills)
    print_slow("最近做的项目：%s" % project)
    print()
    
    # ------------------------------
    # 步骤3：AI面试官开始提问
    # ------------------------------
    print("="*70)
    print("步骤3：AI面试官提问")
    print("="*70)
    print()
    
    print_slow("AI面试官：好的，感谢你的介绍。让我分析一下...")
    print()
    
    # 记录日志
    logger.log_entry(
        request_id=request_id,
        endpoint="/api/interview/question",
        method="POST",
        params={
            "position": position,
            "tech_required": tech_required,
            "candidate_name": name,
            "experience": years,
            "skills": skills,
            "project": project
        }
    )
    
    logger.log_step(request_id=request_id, step="call_llm", status="IN_PROGRESS")
    
    try:
        result = llm_client.generate_questions_with_fallback(
            project_description=project,
            tech_stack=[t.strip() for t in tech_required.split(",")]
        )
        
        questions = result.get("questions", [])
        
        logger.log_step(request_id=request_id, step="parse_result", status="COMPLETED")
        
        # 展示AI提问
        print_slow("AI面试官：根据你的情况，我有几个问题想请教：")
        print()
        
        for i, q in enumerate(questions, 1):
            print("-" * 50)
            print("问题 %d：" % i)
            print_slow(q["question"])
            print()
            print_slow("追问逻辑：%s" % q["logic"])
            print()
            
            # 模拟思考时间
            if i < len(questions):
                print_slow("（请思考...）")
                time.sleep(2)
                print()
        
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/interview/question",
            success=True,
            latency_ms=0,
            result={"question_count": len(questions)}
        )
        
        print("-" * 50)
        print_slow("AI面试官：以上就是本次面试的全部问题，感谢你的回答！")
        
    except Exception as e:
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/interview/question",
            success=False,
            latency_ms=0,
            error=str(e)
        )
        print("提问生成失败：%s" % e)
    
    print()
    print("="*70)
    print("              演示完成！              ")
    print("="*70)

if __name__ == "__main__":
    main()
