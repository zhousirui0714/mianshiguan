"""
个人极简面试官 - 多轮面试演示（预设数据）

流程：
1. 面试者介绍岗位需求
2. 面试者自我介绍
3. AI面试官提问 → 面试者回答 → AI继续追问（多轮）
4. 结束面试
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
    print("          个人极简面试官 - 多轮面试演示          ")
    print("="*70)
    print()
    
    # 初始化服务
    llm_client = LLMClient()
    logger = Logger()
    request_id = logger.generate_request_id()
    
    # ------------------------------
    # 预设数据
    # ------------------------------
    position = "Java后端开发工程师"
    tech_required = "Java, Spring Boot, MySQL, Redis"
    experience = "3-5年"
    name = "张三"
    years = "3年"
    skills = "Java, Spring Boot, MySQL, Redis, 微服务"
    project = "负责电商订单系统开发，使用Spring Boot + MySQL + Redis技术栈，实现了高可用的分布式订单系统，订单处理性能提升30%。"
    
    # 预设的回答
    preset_answers = [
        "我们主要使用MySQL，做了索引优化和分库分表。",
        "我们用了Redis做缓存，采用读写分离策略。",
        "我们做了限流和熔断，使用了Hystrix框架。"
    ]
    
    # ------------------------------
    # 步骤1：面试者介绍岗位需求
    # ------------------------------
    print("="*70)
    print("步骤1：面试者介绍目标岗位")
    print("="*70)
    print()
    
    print_slow("面试者：我想面试贵公司的「%s」岗位。" % position)
    print_slow("这个岗位要求掌握%s，需要%s经验。" % (tech_required, experience))
    print()
    
    # ------------------------------
    # 步骤2：面试者自我介绍
    # ------------------------------
    print("="*70)
    print("步骤2：面试者自我介绍")
    print("="*70)
    print()
    
    print_slow("面试者：面试官您好！我叫%s，有%s工作经验。" % (name, years))
    print_slow("核心技能包括：%s" % skills)
    print_slow("最近做的项目：%s" % project)
    print()
    
    # ------------------------------
    # 步骤3：多轮面试对话
    # ------------------------------
    print("="*70)
    print("步骤3：多轮面试")
    print("="*70)
    print()
    
    print_slow("AI面试官：好的，感谢你的介绍！让我开始提问。")
    print()
    
    max_questions = 3
    
    for i in range(max_questions):
        logger.log_step(request_id=request_id, step="question_%d" % (i + 1), status="IN_PROGRESS")
        
        try:
            # 生成问题
            result = llm_client.generate_questions_with_fallback(
                project_description=project,
                tech_stack=[t.strip() for t in tech_required.split(",")]
            )
            
            if result.get("questions") and len(result["questions"]) > 0:
                question = result["questions"][0]
            else:
                question = {
                    "question": "请介绍你的项目经验。",
                    "logic": "考察项目经验"
                }
            
            logger.log_step(request_id=request_id, step="question_%d" % (i + 1), status="COMPLETED")
            
            # 显示问题
            print("-" * 50)
            print("AI面试官（问题%d）：" % (i + 1))
            print_slow(question["question"])
            print()
            print("追问逻辑：%s" % question["logic"])
            print()
            
            # 模拟思考时间
            time.sleep(1)
            
            # 显示回答
            answer = preset_answers[i] if i < len(preset_answers) else "这是一个很好的问题。"
            print_slow("面试者：%s" % answer)
            print()
            
            # 更新项目描述（模拟根据回答调整追问方向）
            project = project + " " + answer
            
            if i < max_questions - 1:
                print_slow("AI面试官：好的，我明白了。让我继续提问...")
                time.sleep(2)
                print()
        
        except Exception as e:
            print("提问生成失败：%s" % e)
            break
    
    # 结束面试
    logger.log_exit(
        request_id=request_id,
        endpoint="/api/interview/multi-round",
        success=True,
        latency_ms=0,
        result={"question_count": max_questions}
    )
    
    print("-" * 50)
    print_slow("AI面试官：以上就是本次面试的全部问题，感谢你的回答！")
    print()
    
    print("="*70)
    print("              面试结束！              ")
    print("="*70)
    print("本次面试共提问%d个问题" % max_questions)

if __name__ == "__main__":
    main()
