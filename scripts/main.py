import argparse
import json
import time
from typing import List, Dict, Any

from src.services.interview_service import InterviewService

def main():
    parser = argparse.ArgumentParser(description="测试追问生成服务")
    parser.add_argument("--iterations", type=int, default=1, help="测试次数")
    args = parser.parse_args()
    
    service = InterviewService()
    
    # 测试用项目数据
    test_projects = [
        {
            "project_id": "test-project-1",
            "project_name": "电商订单管理系统",
            "project_description": "基于Spring Boot和Vue.js开发的电商订单管理系统，负责订单创建、支付、发货全流程。使用Redis做缓存，MySQL做持久化存储，支持百万级订单处理。",
            "tech_stack": ["Java", "Spring Boot", "Vue.js", "MySQL", "Redis"]
        },
        {
            "project_id": "test-project-2",
            "project_name": "实时数据分析平台",
            "project_description": "使用Python和Spark构建的实时数据分析平台，处理用户行为日志，进行实时统计和可视化展示。",
            "tech_stack": ["Python", "Spark", "Kafka", "Elasticsearch"]
        },
        {
            "project_id": "test-project-3",
            "project_name": "移动端社交App",
            "project_description": "React Native开发的社交应用，支持用户注册、发布动态、点赞评论等功能，集成了IM即时通讯。",
            "tech_stack": ["React Native", "Node.js", "MongoDB", "Socket.io"]
        }
    ]
    
    for i in range(args.iterations):
        print(f"\n{'='*50}")
        print(f"测试 #{i+1}")
        print(f"{'='*50}")
        
        project = test_projects[i % len(test_projects)]
        
        print(f"\n请求参数:")
        print(f"  项目ID: {project['project_id']}")
        print(f"  项目名称: {project['project_name']}")
        print(f"  技术栈: {', '.join(project['tech_stack'])}")
        print(f"  描述长度: {len(project['project_description'])} 字符")
        
        print(f"\n处理中...")
        start_time = time.time()
        
        response = service.generate_questions(
            project_id=project["project_id"],
            project_name=project["project_name"],
            project_description=project["project_description"],
            tech_stack=project["tech_stack"],
            user_id="test-user-001"
        )
        
        latency = time.time() - start_time
        
        print(f"\n响应结果:")
        print(f"  请求ID: {response.request_id}")
        print(f"  成功: {response.success}")
        print(f"  耗时: {response.latency_ms}ms ({latency:.2f}秒)")
        
        if response.success and response.questions:
            print(f"\n生成的追问:")
            for idx, q in enumerate(response.questions, 1):
                print(f"\n  {idx}. {q.question}")
                print(f"     追问逻辑: {q.logic}")
        
        print(f"\n{'='*50}")

if __name__ == "__main__":
    main()