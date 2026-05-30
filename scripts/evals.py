"""
Evals脚本 - 评估LLM生成追问的质量

评估指标：
1. 格式合规率 - 检查返回是否为有效JSON且包含正确结构
2. 内容准确率 - 检查问题是否符合要求（刁钻、有深度、有追问逻辑）
"""

import json
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime

# 模拟LLM响应（用于测试）
def mock_llm_response(project_description: str, tech_stack: List[str]) -> Dict[str, Any]:
    """模拟LLM响应，包含各种情况"""
    responses = [
        # 正常响应
        {
            "questions": [
                {"question": "你在项目中遇到的最大技术挑战是什么？如何解决的？", "logic": "考察问题解决能力"},
                {"question": "项目的性能瓶颈在哪里？如何优化的？", "logic": "考察性能优化意识"},
                {"question": "如果重新设计，你会做哪些改进？", "logic": "考察复盘能力"}
            ]
        },
        # 正常响应2
        {
            "questions": [
                {"question": "数据库的索引设计是怎样的？为什么这样设计？", "logic": "考察数据库设计能力"},
                {"question": "如何保证系统的高可用性？", "logic": "考察系统稳定性意识"},
                {"question": "接口的幂等性是如何保证的？", "logic": "考察接口设计能力"}
            ]
        },
        # 格式错误 - 缺少logic字段
        {
            "questions": [
                {"question": "技术栈选择的理由是什么？"},
                {"question": "项目中的难点是什么？"},
                {"question": "如何进行测试的？"}
            ]
        },
        # 格式错误 - 不是JSON（模拟API返回异常）
        None,
        # 正常响应3
        {
            "questions": [
                {"question": "缓存策略是什么？有没有缓存击穿问题？", "logic": "考察缓存设计"},
                {"question": "分布式事务是如何处理的？", "logic": "考察分布式系统知识"},
                {"question": "代码质量如何保证？有哪些CI/CD流程？", "logic": "考察工程实践"}
            ]
        },
        # 正常响应4
        {
            "questions": [
                {"question": "用户量增长时如何扩容？", "logic": "考察系统扩展性"},
                {"question": "如何处理接口超时？", "logic": "考察容错设计"},
                {"question": "日志和监控是怎么做的？", "logic": "考察运维意识"}
            ]
        },
        # 问题数量不对（只有2个）
        {
            "questions": [
                {"question": "技术选型的考虑因素有哪些？", "logic": "考察技术决策能力"},
                {"question": "项目中的安全措施有哪些？", "logic": "考察安全意识"}
            ]
        },
        # 正常响应5
        {
            "questions": [
                {"question": "如何保证数据一致性？", "logic": "考察数据处理能力"},
                {"question": "并发场景下的问题如何解决？", "logic": "考察并发处理能力"},
                {"question": "如何进行代码review？", "logic": "考察团队协作"}
            ]
        },
        # 空响应
        {"questions": []},
        # 正常响应6
        {
            "questions": [
                {"question": "微服务之间如何通信？", "logic": "考察架构设计"},
                {"question": "如何处理服务降级？", "logic": "考察系统韧性"},
                {"question": "单元测试覆盖率是多少？", "logic": "考察测试意识"}
            ]
        }
    ]
    return random.choice(responses)

def validate_format(response: Dict[str, Any]) -> Tuple[bool, str]:
    """
    验证响应格式是否合规
    
    Returns:
        (是否合规, 错误信息)
    """
    if response is None:
        return False, "响应为空（非JSON格式）"
    
    if not isinstance(response, dict):
        return False, "响应不是字典格式"
    
    if "questions" not in response:
        return False, "缺少questions字段"
    
    questions = response.get("questions", [])
    if not isinstance(questions, list):
        return False, "questions不是数组格式"
    
    if len(questions) != 3:
        return False, f"问题数量不正确：期望3个，实际{len(questions)}个"
    
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            return False, f"第{i+1}个问题不是字典格式"
        if "question" not in q:
            return False, f"第{i+1}个问题缺少question字段"
        if not isinstance(q.get("question"), str) or len(q.get("question")) < 10:
            return False, f"第{i+1}个问题内容过短或不是字符串"
    
    return True, "格式合规"

def evaluate_content(response: Dict[str, Any]) -> Tuple[int, str]:
    """
    评估内容质量
    
    Returns:
        (分数0-100, 评估说明)
    """
    questions = response.get("questions", [])
    
    score = 0
    reasons = []
    
    # 每个问题的基础分
    base_score = 33
    
    for i, q in enumerate(questions):
        # 检查问题长度
        q_text = q.get("question", "")
        if len(q_text) >= 20:
            score += base_score // 3
        else:
            reasons.append(f"第{i+1}个问题过短")
        
        # 检查是否有追问逻辑
        if "logic" in q and q.get("logic") and len(q.get("logic")) >= 5:
            score += base_score // 3
        else:
            reasons.append(f"第{i+1}个问题缺少或过短的追问逻辑")
        
        # 检查问题质量（是否有深度）
        deep_keywords = ["如何", "为什么", "什么", "怎样", "难点", "挑战", "优化", "设计"]
        if any(keyword in q_text for keyword in deep_keywords):
            score += base_score // 3
        else:
            reasons.append(f"第{i+1}个问题缺乏深度")
    
    # 确保分数在0-100之间
    score = min(100, max(0, score))
    
    if score >= 90:
        comment = "优秀：问题质量高，有深度"
    elif score >= 70:
        comment = "良好：基本符合要求"
    elif score >= 50:
        comment = "及格：存在一些不足"
    else:
        comment = "不及格：需要改进"
    
    if reasons:
        comment += f" | 问题：{'; '.join(reasons)}"
    
    return score, comment

def run_evals(num_runs: int = 15) -> Dict[str, Any]:
    """
    运行Evals评估
    
    Args:
        num_runs: 运行次数
    
    Returns:
        评估结果统计
    """
    print(f"{'='*60}")
    print(f"开始Evals评估，运行 {num_runs} 次")
    print(f"{'='*60}")
    
    results = {
        "total_runs": num_runs,
        "format_passes": 0,
        "format_failures": 0,
        "content_scores": [],
        "timestamps": [],
        "details": []
    }
    
    test_project = {
        "project_description": "基于Spring Boot和Vue.js开发的电商订单管理系统，负责订单创建、支付、发货全流程。",
        "tech_stack": ["Java", "Spring Boot", "Vue.js", "MySQL", "Redis"]
    }
    
    for i in range(num_runs):
        print(f"\n--- 测试 #{i+1} ---")
        
        timestamp = datetime.now().isoformat()
        response = mock_llm_response(
            test_project["project_description"],
            test_project["tech_stack"]
        )
        
        # 格式验证
        format_ok, format_msg = validate_format(response)
        print(f"格式验证: {'通过' if format_ok else '失败'} - {format_msg}")
        
        if format_ok:
            results["format_passes"] += 1
            # 内容评估
            content_score, content_comment = evaluate_content(response)
            results["content_scores"].append(content_score)
            print(f"内容评分: {content_score}/100 - {content_comment}")
            
            # 打印生成的问题
            for j, q in enumerate(response.get("questions", [])):
                print(f"  Q{j+1}: {q.get('question', '')[:50]}...")
        else:
            results["format_failures"] += 1
            results["content_scores"].append(0)
        
        results["timestamps"].append(timestamp)
        results["details"].append({
            "run": i+1,
            "timestamp": timestamp,
            "format_ok": format_ok,
            "format_msg": format_msg,
            "content_score": results["content_scores"][-1] if format_ok else 0
        })
    
    # 计算统计结果
    avg_content_score = sum(results["content_scores"]) / num_runs
    format_pass_rate = (results["format_passes"] / num_runs) * 100
    
    print(f"\n{'='*60}")
    print("Evals评估结果统计")
    print(f"{'='*60}")
    print(f"总测试次数: {num_runs}")
    print(f"格式合规率: {format_pass_rate:.1f}% ({results['format_passes']}/{num_runs})")
    print(f"平均内容准确率: {avg_content_score:.1f}/100")
    print(f"最高内容评分: {max(results['content_scores'])}/100")
    print(f"最低内容评分: {min([s for s in results['content_scores'] if s > 0] + [0])}/100")
    
    return results

def export_results(results: Dict[str, Any], filename: str = "evals_results.json"):
    """导出评估结果到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n评估结果已导出到: {filename}")

if __name__ == "__main__":
    results = run_evals(num_runs=15)
    export_results(results)
    
    # 打印统计表格
    print("\n" + "="*60)
    print("Evals统计表格")
    print("="*60)
    print(f"| {'指标':<20} | {'数值':<30} |")
    print(f"|{'-'*22}|{'-'*32}|")
    print(f"| 总测试次数         | {results['total_runs']:<30} |")
    print(f"| 格式合规率         | {((results['format_passes']/results['total_runs'])*100):.1f}% ({results['format_passes']}/{results['total_runs']}) |")
    print(f"| 平均内容准确率     | {sum(results['content_scores'])/results['total_runs']:.1f}/100 |")
    print(f"| 最高内容评分       | {max(results['content_scores'])}/100 |")
    print(f"| 最低内容评分       | {min([s for s in results['content_scores'] if s > 0] + [0])}/100 |")
    print(f"|{'-'*22}|{'-'*32}|")