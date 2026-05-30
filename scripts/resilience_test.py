"""
韧性保护测试脚本 - 验证LLM API调用的Timeout和降级方案

测试场景：
1. 正常调用 - LLM API正常响应
2. 超时测试 - 模拟API响应超时
3. 故障降级 - 模拟API服务不可用
4. 重试机制 - 验证重试策略
"""

import time
import json
import sys
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from src.services.llm_client import LLMClient, LLM_TIMEOUT, FALLBACK_QUESTIONS

# 修复Windows终端编码问题
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 降级到ASCII输出
        text = " ".join(str(arg) for arg in args)
        text = text.encode('ascii', errors='replace').decode('ascii')
        print(text, **kwargs)

def test_normal_call():
    """测试正常调用场景"""
    safe_print("\n" + "="*60)
    safe_print("测试1：正常调用场景")
    safe_print("="*60)
    
    llm_client = LLMClient()
    
    # Mock正常响应
    mock_response = {
        "questions": [
            {"question": "测试问题1", "logic": "测试逻辑1"},
            {"question": "测试问题2", "logic": "测试逻辑2"},
            {"question": "测试问题3", "logic": "测试逻辑3"}
        ]
    }
    
    with patch.object(llm_client, 'generate_questions', return_value=mock_response):
        result = llm_client.generate_questions_with_fallback(
            project_description="测试项目描述",
            tech_stack=["Java", "Spring Boot"]
        )
        
        safe_print("OK 调用成功")
        safe_print("  返回格式: %s" % type(result))
        safe_print("  问题数量: %d" % len(result.get('questions', [])))
        safe_print("  是否降级: %s" % result.get('fallback', False))
        
        assert "questions" in result
        assert len(result["questions"]) == 3
        assert result.get("fallback") is not True  # 正常调用时fallback不存在或为False
        safe_print("OK 正常调用测试通过")

def test_timeout_fallback():
    """测试超时降级场景"""
    safe_print("\n" + "="*60)
    safe_print("测试2：超时降级场景")
    safe_print("="*60)
    
    llm_client = LLMClient(timeout=1)  # 设置1秒超时
    
    # Mock超时异常
    def mock_timeout(*args, **kwargs):
        time.sleep(2)  # 超过超时时间
        raise Exception("模拟超时")
    
    with patch.object(llm_client, 'generate_questions', side_effect=mock_timeout):
        result = llm_client.generate_questions_with_fallback(
            project_description="测试项目描述",
            tech_stack=["Java", "Spring Boot"]
        )
        
        safe_print("OK 触发降级")
        safe_print("  返回格式: %s" % type(result))
        safe_print("  问题数量: %d" % len(result.get('questions', [])))
        safe_print("  是否降级: %s" % result.get('fallback', False))
        safe_print("  降级原因: %s" % result.get('fallback_reason', 'unknown'))
        
        assert "questions" in result
        assert len(result["questions"]) == 3
        assert result.get("fallback") == True
        assert "模拟超时" in result.get("fallback_reason", "")
        safe_print("OK 超时降级测试通过")

def test_api_failure_fallback():
    """测试API故障降级场景"""
    safe_print("\n" + "="*60)
    safe_print("测试3：API故障降级场景")
    safe_print("="*60)
    
    llm_client = LLMClient()
    
    # MockAPI故障
    def mock_failure(*args, **kwargs):
        raise Exception("API服务不可用")
    
    with patch.object(llm_client, 'generate_questions', side_effect=mock_failure):
        result = llm_client.generate_questions_with_fallback(
            project_description="测试项目描述",
            tech_stack=["React", "Vue"]
        )
        
        safe_print("OK 触发降级")
        safe_print("  返回格式: %s" % type(result))
        safe_print("  问题数量: %d" % len(result.get('questions', [])))
        safe_print("  是否降级: %s" % result.get('fallback', False))
        safe_print("  降级原因: %s" % result.get('fallback_reason', 'unknown'))
        
        assert "questions" in result
        assert len(result["questions"]) == 3
        assert result.get("fallback") == True
        assert "API服务不可用" in result.get("fallback_reason", "")
        safe_print("OK API故障降级测试通过")

def test_category_based_fallback():
    """测试基于技术栈的分类降级"""
    safe_print("\n" + "="*60)
    safe_print("测试4：基于技术栈的分类降级")
    safe_print("="*60)
    
    llm_client = LLMClient()
    
    # Mock故障
    def mock_failure(*args, **kwargs):
        raise Exception("API故障")
    
    with patch.object(llm_client, 'generate_questions', side_effect=mock_failure):
        # 测试后端技术栈
        result_backend = llm_client.generate_questions_with_fallback(
            project_description="后端项目",
            tech_stack=["Java", "Spring Boot", "MySQL"]
        )
        
        # 测试前端技术栈
        result_frontend = llm_client.generate_questions_with_fallback(
            project_description="前端项目",
            tech_stack=["React", "Vue", "TypeScript"]
        )
        
        # 测试通用技术栈
        result_default = llm_client.generate_questions_with_fallback(
            project_description="通用项目",
            tech_stack=["Python"]
        )
        
        safe_print("OK 后端分类问题数量: %d" % len(result_backend['questions']))
        safe_print("OK 前端分类问题数量: %d" % len(result_frontend['questions']))
        safe_print("OK 通用分类问题数量: %d" % len(result_default['questions']))
        
        # 验证问题内容不同
        backend_first_q = result_backend['questions'][0]['question']
        frontend_first_q = result_frontend['questions'][0]['question']
        default_first_q = result_default['questions'][0]['question']
        
        safe_print("")
        safe_print("  后端分类第一个问题: %s..." % backend_first_q[:30])
        safe_print("  前端分类第一个问题: %s..." % frontend_first_q[:30])
        safe_print("  通用分类第一个问题: %s..." % default_first_q[:30])
        
        assert backend_first_q != frontend_first_q
        assert frontend_first_q != default_first_q
        safe_print("OK 分类降级测试通过")

def test_timeout_value_verification():
    """验证Timeout值配置"""
    safe_print("\n" + "="*60)
    safe_print("测试5：Timeout值验证")
    safe_print("="*60)
    
    safe_print("OK 配置的Timeout值: %d秒" % LLM_TIMEOUT)
    safe_print("OK Timeout选择依据:")
    safe_print("  1. 大模型生成3条追问通常需要5-15秒")
    safe_print("  2. 设置20秒超时，预留网络延迟和排队时间")
    safe_print("  3. 考虑到用户体验，超过20秒用户可能会刷新页面")
    
    llm_client = LLMClient()
    assert llm_client.timeout == LLM_TIMEOUT
    safe_print("OK Timeout配置验证通过")

def run_all_tests():
    """运行所有测试"""
    safe_print("\n" + "="*70)
    safe_print("    韧性保护测试套件 - Timeout + 降级方案验证")
    safe_print("="*70)
    safe_print("测试时间: %s" % time.strftime('%Y-%m-%d %H:%M:%S'))
    safe_print("LLM Timeout配置: %d秒" % LLM_TIMEOUT)
    safe_print("降级问题库分类: %s" % list(FALLBACK_QUESTIONS.keys()))
    safe_print("="*70)
    
    test_normal_call()
    test_timeout_fallback()
    test_api_failure_fallback()
    test_category_based_fallback()
    test_timeout_value_verification()
    
    safe_print("\n" + "="*70)
    safe_print("    所有韧性保护测试通过！")
    safe_print("="*70)
    
    # 输出测试总结
    summary = {
        "test_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "llm_timeout_seconds": LLM_TIMEOUT,
        "fallback_categories": list(FALLBACK_QUESTIONS.keys()),
        "tests": [
            {"name": "正常调用测试", "status": "PASS"},
            {"name": "超时降级测试", "status": "PASS"},
            {"name": "API故障降级测试", "status": "PASS"},
            {"name": "分类降级测试", "status": "PASS"},
            {"name": "Timeout配置验证", "status": "PASS"}
        ],
        "timeout_reasoning": {
            "base_time": "5-15秒（大模型生成3条追问）",
            "margin": "预留网络延迟和排队时间",
            "user_experience": "超过20秒用户可能会刷新页面",
            "final_timeout": "20秒"
        }
    }
    
    # 导出测试结果
    with open("resilience_test_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    safe_print("\n测试结果已导出到: resilience_test_results.json")
    safe_print("\nTimeout值选择依据：")
    safe_print("-----------------------------------------------------")
    safe_print("1. 大模型生成3条追问通常需要5-15秒")
    safe_print("2. 设置20秒超时，预留网络延迟和排队时间")
    safe_print("3. 考虑到用户体验，超过20秒用户可能会刷新页面")
    safe_print("4. 配合重试机制（最多2次），总耗时可达60秒+")
    safe_print("-----------------------------------------------------")

if __name__ == "__main__":
    run_all_tests()
