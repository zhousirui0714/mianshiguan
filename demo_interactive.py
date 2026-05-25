"""
个人极简面试官 - 交互式多轮面试演示

流程：
1. 面试者输入岗位需求
2. 面试者输入自我介绍
3. AI面试官提问 → 面试者回答 → AI继续追问（循环）
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
    print("          个人极简面试官 - 交互式面试          ")
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
    print("步骤1：请介绍你要面试的岗位")
    print("="*70)
    print()
    
    position = input("岗位名称：").strip() or "Java后端开发工程师"
    tech_required = input("技术栈要求（用逗号分隔）：").strip() or "Java, Spring Boot, MySQL, Redis"
    experience = input("经验要求：").strip() or "3-5年"
    
    print()
    print("岗位信息已记录：")
    print("  ┌─────────────┐")
    print("  │ 岗位：%s    │" % position)
    print("  │ 技术栈：%s  │" % tech_required)
    print("  │ 经验：%s     │" % experience)
    print("  └─────────────┘")
    print()
    
    # ------------------------------
    # 步骤2：面试者自我介绍
    # ------------------------------
    print("="*70)
    print("步骤2：请做自我介绍")
    print("="*70)
    print()
    
    name = input("姓名：").strip() or "张三"
    years = input("工作年限：").strip() or "3年"
    skills = input("核心技能（用逗号分隔）：").strip() or "Java, Spring Boot, MySQL, Redis"
    project = input("最近项目经历：").strip() or "负责电商订单系统开发，使用Spring Boot + MySQL + Redis技术栈。"
    
    print()
    print("你的自我介绍：")
    print("  面试官您好！我叫%s，有%s工作经验。" % (name, years))
    print("  核心技能：%s" % skills)
    print("  项目经历：%s" % project)
    print()
    
    # ------------------------------
    # 步骤3：多轮面试对话
    # ------------------------------
    print("="*70)
    print("步骤3：开始面试")
    print("="*70)
    print()
    
    print_slow("AI面试官：好的，感谢你的介绍！让我开始提问。")
    print()
    
    # 历史对话记录
    conversation_history = [
        {
            "role": "user",
            "content": "我要面试%s岗位，需要%s经验，技术栈要求%s。我叫%s，有%s经验，技能包括%s。项目经历：%s" % 
                       (position, experience, tech_required, name, years, skills, project)
        }
    ]
    
    max_questions = 5
    question_count = 0
    
    while question_count < max_questions:
        # 生成问题
        logger.log_step(request_id=request_id, step="generate_question_%d" % (question_count + 1), status="IN_PROGRESS")
        
        # 构建上下文prompt
        context = "\n".join([
            "%s: %s" % (item["role"], item["content"]) 
            for item in conversation_history
        ])
        
        prompt = f"""
        你是一位资深的{position}面试官。请根据以下对话历史，生成下一个针对性的技术追问。
        
        对话历史：
        {context}
        
        要求：
        1. 问题要针对候选人的回答进行追问，深入挖掘技术细节
        2. 问题要刁钻，考察真实能力
        3. 每个问题附带简短的追问逻辑说明
        4. 输出格式为JSON：
        {{
            "question": "xxx",
            "logic": "xxx"
        }}
        """
        
        try:
            result = llm_client.generate_questions_with_fallback(
                project_description=project,
                tech_stack=[t.strip() for t in tech_required.split(",")]
            )
            
            # 使用第一个问题
            if result.get("questions") and len(result["questions"]) > 0:
                current_question = result["questions"][0]
            else:
                # 降级问题
                current_question = {
                    "question": "请详细描述你在项目中遇到的最大技术挑战是什么？",
                    "logic": "考察解决问题的能力"
                }
            
            logger.log_step(request_id=request_id, step="generate_question_%d" % (question_count + 1), status="COMPLETED")
            
            # 显示问题
            print("-" * 50)
            print("AI面试官（问题%d）：" % (question_count + 1))
            print_slow(current_question["question"])
            print()
            print("追问逻辑：%s" % current_question["logic"])
            print()
            
            # 添加到历史
            conversation_history.append({
                "role": "assistant",
                "content": current_question["question"]
            })
            
            # 获取用户回答
            print("请输入你的回答（按回车继续，输入'结束'或'quit'退出）：")
            answer = input("你：").strip()
            
            if answer.lower() in ["结束", "quit", "exit"]:
                print_slow("AI面试官：好的，面试结束。感谢你的参与！")
                break
            
            if not answer:
                answer = "这是一个很好的问题，我会从几个方面来回答..."
            
            print()
            print_slow("你：%s" % answer)
            print()
            
            # 添加到历史
            conversation_history.append({
                "role": "user",
                "content": answer
            })
            
            question_count += 1
            
            if question_count < max_questions:
                print_slow("AI面试官：让我思考一下...")
                time.sleep(1)
                print()
        
        except Exception as e:
            print("提问生成失败：%s" % e)
            break
    
    # 结束面试
    logger.log_exit(
        request_id=request_id,
        endpoint="/api/interview/chat",
        success=True,
        latency_ms=0,
        result={"question_count": question_count}
    )
    
    print()
    print("="*70)
    print("              面试结束！              ")
    print("="*70)
    print("本次面试共提问%d个问题" % question_count)

if __name__ == "__main__":
    main()
