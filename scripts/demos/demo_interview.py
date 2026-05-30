"""
个人极简面试官 - 真实面试场景演示

流程：
1. 面试者介绍岗位需求
2. 面试者介绍自己
3. AI面试官生成针对性追问
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
    
    # 模拟用户输入（演示用）
    print("请介绍你要面试的岗位信息：")
    position = input("岗位名称：") or "Java后端开发工程师"
    tech_required = input("技术栈要求（用逗号分隔）：") or "Java, Spring Boot, MySQL, Redis"
    experience = input("经验要求：") or "3-5年"
    round_info = input("面试轮次：") or "一面（技术面）"
    
    print()
    print("你输入的岗位信息：")
    print("  ┌─────────────┐")
    print("  │ 岗位名称：%s │" % position)
    print("  │ 技术栈：%s   │" % tech_required)
    print("  │ 经验要求：%s   │" % experience)
    print("  │ 面试轮次：%s   │" % round_info)
    print("  └─────────────┘")
    print()
    
    # ------------------------------
    # 步骤2：面试者自我介绍
    # ------------------------------
    print("="*70)
    print("步骤2：面试者自我介绍")
    print("="*70)
    print()
    
    print("请介绍你自己：")
    name = input("姓名：") or "张三"
    years = input("工作年限：") or "3年"
    skills = input("核心技能（用逗号分隔）：") or "Java, Spring Boot, MySQL, Redis, 微服务"
    project = input("最近项目经历（简要描述）：") or "负责电商订单系统开发，使用Spring Boot + MySQL + Redis技术栈，实现了高可用的分布式订单系统。"
    
    print()
    print("你的自我介绍：")
    print("  面试官您好！我叫%s，有%s工作经验。" % (name, years))
    print("  核心技能包括：%s" % skills)
    print("  最近做的项目：%s" % project)
    print()
    
    # ------------------------------
    # 步骤3：AI面试官开始提问
    # ------------------------------
    print("="*70)
    print("步骤3：AI面试官提问")
    print("="*70)
    print()
    
    print_slow("AI面试官正在分析你的信息...")
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
    
    # 调用LLM生成追问
    prompt = f"""
    你是一位资深的{position}面试官，正在进行{round_info}。
    
    岗位要求：
    - 技术栈：{tech_required}
    - 经验要求：{experience}
    
    候选人信息：
    - 姓名：{name}
    - 工作年限：{years}
    - 核心技能：{skills}
    - 项目经历：{project}
    
    请根据以上信息，生成5个针对性的技术追问，考察候选人的真实能力。
    问题要刁钻，深入挖掘技术细节，针对简历中的模糊表述进行追问。
    
    输出格式为JSON：
    {{
        "questions": [
            {{"question": "xxx", "logic": "xxx"}},
            ...
        ]
    }}
    """
    
    logger.log_step(request_id=request_id, step="call_llm", status="IN_PROGRESS")
    
    try:
        result = llm_client.generate_questions_with_fallback(
            project_description=project,
            tech_stack=[t.strip() for t in tech_required.split(",")]
        )
        
        questions = result.get("questions", [])
        
        logger.log_step(request_id=request_id, step="parse_result", status="COMPLETED")
        
        # 展示AI提问
        print_slow("好的，根据你的情况，我有几个问题想请教：")
        print()
        
        for i, q in enumerate(questions, 1):
            print("-" * 50)
            print("问题 %d：" % i)
            print_slow(q["question"])
            print()
            print("追问逻辑：%s" % q["logic"])
            print()
            
            # 模拟思考时间
            if i < len(questions):
                print_slow("（请思考3秒后继续...）")
                time.sleep(1)
                print()
        
        logger.log_exit(
            request_id=request_id,
            endpoint="/api/interview/question",
            success=True,
            latency_ms=0,
            result={"question_count": len(questions)}
        )
        
        print("-" * 50)
        print_slow("以上就是本次面试的全部问题，感谢你的回答！")
        
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
