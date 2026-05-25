import json
import time
import os
from dotenv import load_dotenv
import httpx
from typing import Optional, List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 加载环境变量
load_dotenv()

# DeepSeek API配置
LLM_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key")

# Timeout配置 - 选择依据：
# 1. 大模型生成3条追问通常需要5-15秒
# 2. 设置20秒超时，预留网络延迟和排队时间
# 3. 考虑到用户体验，超过20秒用户可能会刷新页面
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "20"))  # 秒

# 降级问答库 - 当LLM服务不可用时使用
FALLBACK_QUESTIONS = {
    "default": [
        {
            "question": "请详细描述你在这个项目中遇到的最大技术挑战是什么？你是如何解决的？",
            "logic": "考察应聘者对项目难点的理解和解决问题的能力"
        },
        {
            "question": "这个项目中你负责的模块与其他模块是如何交互的？有没有遇到过接口调用的问题？",
            "logic": "考察应聘者对系统架构和接口设计的理解"
        },
        {
            "question": "如果让你重新设计这个项目的某个部分，你会怎么做？为什么？",
            "logic": "考察应聘者的复盘能力和技术视野"
        }
    ],
    "backend": [
        {
            "question": "你在项目中使用的数据库是什么？如何进行数据库优化的？",
            "logic": "考察后端开发者的数据库设计和优化能力"
        },
        {
            "question": "项目中有没有使用缓存？缓存策略是什么？有没有遇到过缓存一致性问题？",
            "logic": "考察后端开发者对缓存的理解和实践经验"
        },
        {
            "question": "如果系统突然遇到高并发场景，你的服务会如何应对？有没有做过载保护？",
            "logic": "考察后端开发者的系统稳定性和高并发处理能力"
        }
    ],
    "frontend": [
        {
            "question": "项目中遇到过哪些性能瓶颈？你是如何优化的？",
            "logic": "考察前端开发者的性能优化能力"
        },
        {
            "question": "如何处理复杂的状态管理？有没有使用状态管理库？为什么选择它？",
            "logic": "考察前端开发者对状态管理的理解"
        },
        {
            "question": "项目中有没有做过响应式设计？如何适配不同屏幕尺寸？",
            "logic": "考察前端开发者的响应式设计经验"
        }
    ]
}

class LLMClient:
    def __init__(
        self,
        api_url: str = LLM_API_URL,
        api_key: str = LLM_API_KEY,
        timeout: int = LLM_TIMEOUT
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def generate_questions(self, project_description: str, tech_stack: List[str]) -> Dict[str, Any]:
        """
        调用LLM生成刁钻追问
        
        Args:
            project_description: 项目描述
            tech_stack: 技术栈列表
        
        Returns:
            包含问题和逻辑的字典
        
        Raises:
            Exception: 当重试后仍然失败时抛出
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建prompt
        prompt = f"""
        你是一位资深的互联网大厂技术面试官，请针对以下项目描述生成3个刁钻的技术追问：
        
        项目描述：
        {project_description}
        
        技术栈：{', '.join(tech_stack)}
        
        要求：
        1. 问题要刁钻，深入挖掘技术细节
        2. 针对项目中的模糊表述、技术盲区进行追问
        3. 每个问题附带简要的追问逻辑说明
        4. 输出格式为JSON，包含questions数组，每个元素有question和logic字段
        
        示例输出格式：
        {{
            "questions": [
                {{"question": "xxx", "logic": "xxx"}},
                {{"question": "xxx", "logic": "xxx"}},
                {{"question": "xxx", "logic": "xxx"}}
            ]
        }}
        """
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的互联网大厂技术面试官，擅长深挖项目细节和技术盲区。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout)) as client:
                response = client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                response_data = response.json()
                
                # 解析 DeepSeek API 返回格式
                # DeepSeek 返回格式: {"choices": [{"message": {"content": "..."}}]}
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    message_content = response_data["choices"][0]["message"]["content"]
                    # 尝试解析为JSON
                    try:
                        return json.loads(message_content.strip())
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，返回原始内容
                        return {"questions": [], "raw_content": message_content}
                return response_data
        except httpx.TimeoutException:
            raise Exception(f"LLM API请求超时（{self.timeout}秒）")
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API返回错误: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"LLM API调用失败: {str(e)}")
    
    def generate_questions_with_fallback(self, project_description: str, tech_stack: List[str]) -> Dict[str, Any]:
        """
        调用LLM生成追问，带降级方案
        
        Args:
            project_description: 项目描述
            tech_stack: 技术栈列表
        
        Returns:
            包含问题和逻辑的字典（可能是降级结果）
        """
        try:
            result = self.generate_questions(project_description, tech_stack)
            # 验证返回格式
            if "questions" in result and isinstance(result["questions"], list):
                return result
            else:
                raise ValueError("LLM返回格式不符合要求")
        except Exception as e:
            # 降级到预设问题库
            category = self._determine_category(tech_stack)
            return {
                "questions": FALLBACK_QUESTIONS[category],
                "fallback": True,
                "fallback_reason": str(e)
            }
    
    def _determine_category(self, tech_stack: List[str]) -> str:
        """根据技术栈确定问题类别"""
        frontend_keywords = ["react", "vue", "angular", "javascript", "typescript", "frontend"]
        backend_keywords = ["java", "python", "go", "backend", "spring", "node"]
        
        tech_lower = [tech.lower() for tech in tech_stack]
        
        if any(keyword in tech_lower for keyword in frontend_keywords):
            return "frontend"
        elif any(keyword in tech_lower for keyword in backend_keywords):
            return "backend"
        else:
            return "default"

# 导出
__all__ = ["LLMClient", "LLM_TIMEOUT", "FALLBACK_QUESTIONS"]
