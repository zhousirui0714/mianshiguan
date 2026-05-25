"""
个人极简面试官 - 完全手动演示版

特点：
1. 所有内容都需要手动输入
2. AI提问后会暂停，等待用户按回车继续
3. 用户可以自由输入回答
4. 支持随时结束面试

使用方法：
1. 运行脚本
2. 按提示输入岗位信息和自我介绍
3. 看到AI提问后，按回车继续
4. 输入你的回答
5. 循环直到结束
"""

from src.services.llm_client import LLMClient
from src.utils.logger import Logger

def main():
    print("="*70)
    print("          个人极简面试官 - 手动演示          ")
    print("="*70)
    print()
    
    # 初始化服务
    llm_client = LLMClient()
    logger = Logger()
    request_id = logger.generate_request_id()
    
    # ------------------------------
    # 步骤1：输入岗位需求
    # ------------------------------
    print("="*70)
    print("步骤1：请输入你要面试的岗位信息")
    print("="*70)
    print()
    
    position = input("岗位名称：").strip()
    while not position:
        position = input("请输入岗位名称：").strip()
    
    tech_required = input("技术栈要求（用逗号分隔）：").strip()
    if not tech_required:
        tech_required = "Java, Spring Boot, MySQL, Redis"
    
    experience = input("经验要求：").strip()
    if not experience:
        experience = "3-5年"
    
    print()
    print("岗位信息已记录：")
    print("  ┌─────────────┐")
    print("  │ 岗位：%s    │" % position)
    print("  │ 技术栈：%s  │" % tech_required)
    print("  │ 经验：%s     │" % experience)
    print("  └─────────────┘")
    print()
    
    # ------------------------------
    # 步骤2：输入自我介绍
    # ------------------------------
    print("="*70)
    print("步骤2：请输入你的自我介绍")
    print("="*70)
    print()
    
    name = input("姓名：").strip()
    if not name:
        name = "张三"
    
    years = input("工作年限：").strip()
    if not years:
        years = "3年"
    
    skills = input("核心技能（用逗号分隔）：").strip()
    if not skills:
        skills = "Java, Spring Boot, MySQL, Redis"
    
    project = input("最近项目经历（简要描述）：").strip()
    while not project:
        project = input("请输入项目经历：").strip()
    
    print()
    print("你的自我介绍：")
    print("  面试官您好！我叫%s，有%s工作经验。" % (name, years))
    print("  核心技能：%s" % skills)
    print("  项目经历：%s" % project)
    print()
    
    # ------------------------------
    # 步骤3：开始面试
    # ------------------------------
    print("="*70)
    print("步骤3：开始面试")
    print("="*70)
    print()
    
    input("按回车键开始面试...")
    print()
    
    print("AI面试官：好的，感谢你的介绍！让我开始提问。")
    print()
    
    # 历史对话记录
    conversation_history = [project]
    max_questions = 5
    question_count = 0
    
    while question_count < max_questions:
        # 生成问题
        try:
            result = llm_client.generate_questions_with_fallback(
                project_description=" ".join(conversation_history),
                tech_stack=[t.strip() for t in tech_required.split(",")]
            )
            
            if result.get("questions") and len(result["questions"]) > 0:
                question = result["questions"][0]
            else:
                question = {
                    "question": "请详细描述你在项目中遇到的最大技术挑战是什么？",
                    "logic": "考察解决问题的能力"
                }
            
            # 显示问题
            print("-" * 50)
            print("AI面试官（问题%d）：" % (question_count + 1))
            print(question["question"])
            print()
            print("追问逻辑：%s" % question["logic"])
            print()
            
            # 等待用户按回车
            input("按回车键继续...")
            print()
            
            # 获取用户回答
            print("请输入你的回答：")
            answer = input("你：").strip()
            
            if answer.lower() in ["结束", "quit", "exit", "q"]:
                print("AI面试官：好的，面试结束。感谢你的参与！")
                break
            
            if not answer:
                answer = "这是一个很好的问题，我会从几个方面来回答..."
            
            print()
            print("你：%s" % answer)
            print()
            
            # 添加到历史
            conversation_history.append(answer)
            question_count += 1
            
            if question_count < max_questions:
                input("按回车键继续下一个问题...")
                print()
        
        except Exception as e:
            print("提问生成失败：%s" % e)
            break
    
    # 结束面试
    logger.log_exit(
        request_id=request_id,
        endpoint="/api/interview/manual",
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
