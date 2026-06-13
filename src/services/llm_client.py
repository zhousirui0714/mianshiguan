import json
import time
import os
from dotenv import load_dotenv
import httpx
from typing import Optional, List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 加载环境变量
load_dotenv()

# LLM API配置
LLM_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key")
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

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

# 考官人设配置
EXAMINER_PROFILES = {
    "job_interview": {
        "name": "张经理",
        "title": "资深技术面试官",
        "tone": "专业、严谨但友好",
        "background": "10年互联网行业经验，曾担任多家大厂技术面试官，擅长挖掘候选人的技术深度和项目经验"
    },
    "teacher_cert": {
        "name": "王老师",
        "title": "资深教研员",
        "tone": "温和、耐心、鼓励",
        "background": "20年教龄，多次参与教师资格证面试评审工作，熟悉教资面试评分标准"
    },
    "ielts_speaking": {
        "name": "Mr. Smith",
        "title": "IELTS Examiner",
        "tone": "专业、礼貌、标准",
        "background": "Cambridge Certified IELTS Examiner with 8 years of experience in assessing speaking tests"
    },
    "civil_service": {
        "name": "李主任",
        "title": "公务员面试考官",
        "tone": "庄重、严谨、正式",
        "background": "8年公务员面试评审经验，熟悉结构化面试流程和评分标准"
    },
    "graduate_school": {
        "name": "陈教授",
        "title": "研究生导师",
        "tone": "学术、严谨、专业",
        "background": "博士生导师，多年研究生复试面试经验，注重考察学术潜力和专业基础"
    },
    "mba_interview": {
        "name": "刘总监",
        "title": "商学院面试官",
        "tone": "专业、犀利、注重结果",
        "background": "企业高管，多次担任顶尖商学院MBA面试官，关注领导力和职业规划"
    }
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
            "model": LLM_MODEL,
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
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def examiner_chat(self, scenario_id: str, user_message: str,
                     conversation_history: List[Dict[str, str]],
                     user_background: str = "",
                     retrieved_questions: list = None,
                     used_questions: list = None,
                     next_question: str = "",
                     current_stage: str = "") -> str:
        """
        AI考官聊天接口

        Args:
            scenario_id: 场景ID
            user_message: 用户消息
            conversation_history: 对话历史 ([{"role": "...", "content": "..."}, ...])
            user_background: 用户背景信息
            next_question: 系统预设的下一个问题（如果提供，LLM应围绕它展开）
            current_stage: 当前面试阶段（intro/project/basic/advanced/system_design/behavior）

        Returns:
            AI考官的回复内容
        """
        # 获取考官人设
        profile = EXAMINER_PROFILES.get(scenario_id, EXAMINER_PROFILES["job_interview"])
        scenario_name = profile["title"]
        examiner_name = profile["name"]
        tone = profile["tone"]
        background = profile["background"]

        # 构建已覆盖话题摘要
        covered_topics = ""
        assistant_msgs = [m for m in conversation_history if m.get("role") == "assistant"]
        if assistant_msgs:
            recent_questions = [m["content"][:80] for m in assistant_msgs[-3:]]
            covered_topics = "已提问过的话题：\n" + "\n".join(f"- {q}" for q in recent_questions)

        # 阶段提示
        stage_hint = ""
        if current_stage:
            stage_map = {
                "intro": "自我介绍阶段，了解候选人基本背景",
                "project": "项目经验深挖阶段，针对简历中的项目追问技术细节",
                "basic": "基础知识考察阶段，考察岗位所需的核心技术能力",
                "advanced": "进阶能力考察阶段，考察系统设计和高阶技能",
                "system_design": "系统设计阶段，考察架构能力和技术视野",
                "behavior": "行为面试阶段，考察软技能和团队协作",
            }
            stage_desc = stage_map.get(current_stage, current_stage)
            stage_hint = f"\n当前面试阶段：{stage_desc}"

        # 预设问题提示
        question_hint = ""
        if next_question:
            question_hint = f"""
【预设问题】
下一轮你应当围绕以下问题展开提问：
"{next_question}"

请先用1-2句话简要评价用户的回答，然后自然地提出这个问题。
你可以用自己的话重新组织问题，但核心考察点不要偏离。
"""

        # 构建系统提示词
        system_prompt = f"""你是一位{scenario_name}，名叫{examiner_name}。
背景：{background}
语气要求：{tone}

【你的角色】
你正在进行一场真实的一对一面试。你的核心任务是：
1. 先具体评价用户刚才的回答（1-2句话，明确指出具体亮点或不足，不要泛泛说"回答得很好"）
2. 然后提出下一个面试问题（每次只问一个问题）

【追问原则 - 最重要】
- 你必须根据用户刚才回答的**具体内容**来追问深挖
- 如果用户回答中提到了某个技术细节、项目经验、具体数据，请追问那个点
- 如果用户回答模糊笼统，请要求他给出具体例子
- 不要机械地跳到下一个话题，要像一个真正的面试官那样顺着对话自然深入
- 每一轮问题都应该和前面的对话有逻辑关联

【面试规则】
- 每次回复只包含：具体评价 + 一个面试问题
- 问题要有深度，能考察真实能力
- 不要一次问多个问题
- 不要说"如果你准备好了我们就开始"之类的废话
- 不要自我评价或解释你在做什么

{stage_hint}

【用户背景信息】
{user_background}

{covered_topics}
{question_hint}

请像一个真实的面试官那样自然地提问。""".strip()

        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # 添加对话历史
        for msg in conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # 添加用户当前消息
        messages.append({
            "role": "user",
            "content": user_message
        })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 800
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
                
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"].strip()
                return ""
        except httpx.TimeoutException:
            raise Exception(f"LLM API请求超时（{self.timeout}秒）")
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API返回错误: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"LLM API调用失败: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def generate_evaluation_report(self, scenario_id: str, 
                                  conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        生成面试评估报告
        
        Args:
            scenario_id: 场景ID
            conversation_history: 完整对话历史
        
        Returns:
            结构化评估报告字典
        """
        profile = EXAMINER_PROFILES.get(scenario_id, EXAMINER_PROFILES["job_interview"])
        scenario_name = profile["title"]
        
        # 构建对话历史文本
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in conversation_history
        ])
        
        system_prompt = f"""
你是一位专业的{scenario_name}面试评估专家。

请根据以下对话历史，生成一份结构化的面试评估报告：

要求：
1. 综合得分（0-100分）
2. 优势分析（3-5条）
3. 改进建议（3-5条）
4. 各维度评分（沟通表达、专业能力、逻辑思维等）
5. 总体评价（用换行分段，避免长段落，关键结论短句表达）

输出格式为JSON：
{{
    "overall_score": 得分,
    "strengths": ["优势1", "优势2", "优势3"],
    "improvements": ["建议1", "建议2", "建议3"],
    "dimensions": [
        {{"name": "维度名称", "score": 分数, "max_score": 100, "comment": "评价"}}
    ],
    "overall_comment": "总体评价"
}}
        """.strip()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"对话历史：\n{conversation_text}"}
            ],
            "temperature": 0.4,
            "max_tokens": 2000
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
                
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    message_content = response_data["choices"][0]["message"]["content"].strip()
                    try:
                        return json.loads(message_content)
                    except json.JSONDecodeError:
                        # 如果不是JSON，返回格式化后的报告
                        return {
                            "overall_score": 80,
                            "strengths": ["回答较为流畅", "思路清晰"],
                            "improvements": ["建议增加实例", "加强专业知识"],
                            "dimensions": [],
                            "overall_comment": message_content,
                            "raw_content": message_content
                        }
                return {}
        except httpx.TimeoutException:
            raise Exception(f"LLM API请求超时（{self.timeout}秒）")
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API返回错误: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"LLM API调用失败: {str(e)}")

    # ==================== LLM 评分 ====================

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def score_answer(self, scenario_id: str, question: str, answer: str,
                     dimensions: List[Dict[str, Any]], persona_name: str = "",
                     persona_title: str = "") -> Dict[str, Any]:
        """
        调用 LLM 对答案进行多维度评分

        Args:
            scenario_id: 场景 ID（用于获取人设）
            question: 面试问题
            answer: 用户回答
            dimensions: 评分维度列表，每项包含 id, name, max_score, weight, description
            persona_name: 考官姓名
            persona_title: 考官头衔

        Returns:
            {
                "dimension_scores": {"维度id": 分数},
                "total_score": 加权总分,
                "comment": "评语",
                "passed": 是否通过
            }
        """
        profile = EXAMINER_PROFILES.get(scenario_id, EXAMINER_PROFILES["job_interview"])
        examiner_name = persona_name or profile["name"]
        examiner_title = persona_title or profile["title"]

        # 构建评分维度描述
        dims_desc = "\n".join([
            f"- {d.get('name', d.get('id', d['id']))}（满分{d.get('max_score', 100)}，权重{d.get('weight', 0)}%）：{d.get('description', '')}"
            for d in dimensions
        ])

        system_prompt = f"""你是一位专业的{examiner_title}，名叫{examiner_name}。
你需要对面试者的回答进行多维度评分。

评分维度：
{dims_desc}

评分要求：
1. 每个维度独立评分（0-满分）
2. 参考评分标准给分，严格评判
3. 评语要具体、有针对性，指出优缺点
4. 输出严格 JSON 格式

输出格式：
{{
    "dimension_scores": {{"维度id1": 分数1, "维度id2": 分数2, ...}},
    "comment": "综合评语",
    "strengths": ["优势点1", "优势点2"],
    "weaknesses": ["不足点1", "不足点2"]
}}"""

        user_prompt = f"""面试问题：{question}

面试者回答：{answer}

请根据上述评分维度进行评分。"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1000
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout)) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"].strip()
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError:
                        # 尝试提取 JSON 块
                        import re
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group())
                        else:
                            raise ValueError("LLM 返回不是有效 JSON")
                    return result
                return {}
        except Exception as e:
            raise Exception(f"LLM 评分调用失败: {str(e)}")

    # ==================== LLM 反馈报告 ====================

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def generate_skill_feedback(self, scenario_id: str, skill_name: str,
                                 qa_pairs: List[Dict[str, str]],
                                 dimensions: List[Dict[str, Any]],
                                 persona_name: str = "",
                                 persona_title: str = "") -> Dict[str, Any]:
        """
        调用 LLM 生成完整的面试反馈报告

        Args:
            scenario_id: 场景 ID
            skill_name: 场景名称
            qa_pairs: 问答对列表 [{"question": "...", "answer": "...", "score": 分数}, ...]
            dimensions: 评分维度列表
            persona_name: 考官姓名
            persona_title: 考官头衔

        Returns:
            {
                "overall_score": 总分,
                "strengths": ["优势1", ...],
                "improvements": ["建议1", ...],
                "dimensions": [{"name": "...", "score": ..., "max_score": ..., "comment": "..."}, ...],
                "overall_comment": "总体评价"
            }
        """
        profile = EXAMINER_PROFILES.get(scenario_id, EXAMINER_PROFILES["job_interview"])
        examiner_name = persona_name or profile["name"]
        examiner_title = persona_title or profile["title"]

        # 构建问答历史
        qa_text = "\n\n".join([
            f"第{i+1}轮\n问题：{qa['question']}\n回答：{qa['answer']}\n得分：{qa.get('score', '未评分')}"
            for i, qa in enumerate(qa_pairs)
        ])

        dims_desc = "\n".join([
            f"- {d.get('name', d.get('id', d['id']))}（满分{d.get('max_score', 100)}，权重{d.get('weight', 0)}%）：{d.get('description', '')}"
            for d in dimensions
        ])

        system_prompt = f"""你是一位专业的{examiner_title}，名叫{examiner_name}。
请根据一场完整的{skill_name}模拟面试记录，生成最终评估报告。

评分维度定义：
{dims_desc}

问答记录：
{qa_text}

请输出 JSON 格式的评估报告：
{{
    "overall_score": 综合评分（0-100）,
    "strengths": ["优势点1", "优势点2", "优势点3"],
    "improvements": ["改进建议1", "改进建议2", "改进建议3"],
    "dimensions": [
        {{"name": "维度名称", "score": 维度分数, "max_score": 满分, "comment": "维度评语"}}
    ],
    "overall_comment": "总体评价和建议"
}}

要求：
1. 综合评分基于各维度加权计算
2. 优势和改进各 3-5 条，具体且有针对性
3. 总体评价要全面、中肯，有指导意义"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请为以下{skill_name}模拟面试生成评估报告：\n\n{qa_text}"}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout)) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"].strip()
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        import re
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                        return {
                            "overall_score": 75,
                            "strengths": ["回答较为流畅"],
                            "improvements": ["建议增加具体实例"],
                            "dimensions": [],
                            "overall_comment": content,
                        }
                return {}
        except Exception as e:
            raise Exception(f"LLM 反馈报告生成失败: {str(e)}")

    # ==================== LLM + Tool 协作 ====================

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    def chat_with_tools(self, scenario_id: str, user_message: str,
                        conversation_history: List[Dict[str, str]],
                        tools: List[Dict[str, Any]],
                        user_background: str = "",
                        retrieved_questions: list = None,
                        used_questions: list = None,
                        next_question: str = "",
                        current_stage: str = "") -> Dict[str, Any]:
        """
        AI考官聊天（支持工具调用）

        在 examiner_chat 的基础上，告知 LLM 可用工具。
        LLM 可在回复中包含工具调用请求，由调用方执行。

        Args:
            scenario_id: 场景 ID
            user_message: 用户消息
            conversation_history: 对话历史
            tools: 可用工具列表 [{"id": "...", "name": "...", "description": "...", "parameters": [...]}]
            user_background: 用户背景
            next_question: 系统预设的下一个问题
            current_stage: 当前面试阶段

        Returns:
            {
                "response": 回复内容,
                "tool_calls": [{"tool_id": "...", "arguments": {...}}] 或 None
            }
        """
        profile = EXAMINER_PROFILES.get(scenario_id, EXAMINER_PROFILES["job_interview"])
        scenario_name = profile["title"]
        examiner_name = profile["name"]
        tone = profile["tone"]
        background = profile["background"]

        # 构建工具描述
        tools_desc = ""
        if tools:
            tools_desc = "\n\n你有以下工具可以使用：\n"
            for t in tools:
                params_desc = ", ".join([
                    f"{p.get('name', '?')}({'必填' if p.get('required') else '可选'})"
                    for p in t.get("parameters", [])
                ])
                tools_desc += f"- {t.get('name', t.get('id', '?'))}: {t.get('description', '')}。参数：{params_desc}\n"
            tools_desc += (
                "\n如果你觉得需要调用工具来分析用户回答，"
                "请在回复中在最后一行附上 JSON 格式的工具调用：\n"
                "TOOL_CALL: {\"tool_id\": \"工具ID\", \"arguments\": {...}}\n"
            )

        # 已覆盖话题
        covered_topics = ""
        assistant_msgs = [m for m in conversation_history if m.get("role") == "assistant"]
        if assistant_msgs:
            recent_questions = [m["content"][:80] for m in assistant_msgs[-3:]]
            covered_topics = "已提问过的话题：\n" + "\n".join(f"- {q}" for q in recent_questions)

        # 阶段提示
        stage_hint = ""
        if current_stage:
            stage_map = {
                "intro": "自我介绍阶段，了解候选人基本背景",
                "project": "项目经验深挖阶段，针对简历中的项目追问技术细节",
                "basic": "基础知识考察阶段，考察岗位所需的核心技术能力",
                "advanced": "进阶能力考察阶段，考察系统设计和高阶技能",
                "system_design": "系统设计阶段，考察架构能力和技术视野",
                "behavior": "行为面试阶段，考察软技能和团队协作",
            }
            stage_desc = stage_map.get(current_stage, current_stage)
            stage_hint = f"\n当前面试阶段：{stage_desc}"

        # 预设问题提示
        question_hint = ""
        if next_question:
            question_hint = f"""
【预设问题】
下一轮你应当围绕以下问题展开提问：
"{next_question}"

请先用1-2句话简要评价用户的回答，然后自然地提出这个问题。
你可以用自己的话重新组织问题，但核心考察点不要偏离。
"""

        system_prompt = f"""你是一位{scenario_name}，名叫{examiner_name}。
背景：{background}
语气要求：{tone}

【你的角色】
你正在进行一场真实的一对一面试。你的核心任务是：
1. 先简要评价用户刚才的回答（1-2句话，具体指出亮点或不足）
2. 然后提出下一个面试问题（每次只问一个问题）

【面试规则】
- 每次回复只包含：简短评价 + 一个面试问题
- 问题要有深度，能考察真实能力，不要问泛泛而谈的问题
- 根据用户的实际回答进行追问深挖，而不是机械地走流程
- 不要一次问多个问题
- 不要说"如果你准备好了我们就开始"之类的废话
- 不要自我评价或解释你在做什么

{stage_hint}

【用户背景信息】
{user_background}

{covered_topics}
{question_hint}
{tools_desc}

请像一个真实的面试官那样自然地提问。""".strip()

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 800
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout)) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

                if "choices" in response_data and len(response_data["choices"]) > 0:
                    content = response_data["choices"][0]["message"]["content"].strip()

                    # 检查是否有工具调用请求
                    tool_calls = None
                    import re
                    tool_match = re.search(r'TOOL_CALL:\s*(\{.*?\})', content, re.DOTALL)
                    if tool_match:
                        try:
                            tool_calls = json.loads(tool_match.group(1))
                            # 从回复中移除 TOOL_CALL 行
                            content = re.sub(r'\nTOOL_CALL:\s*\{.*?\}', '', content, flags=re.DOTALL).strip()
                        except json.JSONDecodeError:
                            pass

                    return {
                        "response": content,
                        "tool_calls": [tool_calls] if tool_calls else None,
                    }
                return {"response": "", "tool_calls": None}
        except httpx.TimeoutException:
            raise Exception(f"LLM API请求超时（{self.timeout}秒）")
        except httpx.HTTPStatusError as e:
            raise Exception(f"LLM API返回错误: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"LLM API调用失败: {str(e)}")


    # ==================== AI 参考答案生成 ====================

    def generate_model_answer(self, question: str, scenario_id: str = "",
                              user_background: str = "") -> str:
        """
        生成一道面试题的 AI 参考答案

        Args:
            question: 面试问题
            scenario_id: 场景 ID（用于适配风格）
            user_background: 用户背景（让答案更有针对性）

        Returns:
            AI 生成的参考答案文本
        """
        profile = EXAMINER_PROFILES.get(scenario_id, EXAMINER_PROFILES["job_interview"])
        scenario_name = profile["title"]

        context_hint = ""
        if user_background:
            # 只取最关键的行避免 prompt 过长
            lines = [l.strip() for l in user_background.split("\n") if l.strip()
                     and any(l.startswith(p) for p in
                             ["目标岗位", "目标公司", "个人简历", "报考", "目标院校", "目标专业"])]
            if lines:
                context_hint = "【用户背景】\n" + "\n".join(lines[:6]) + "\n\n"

        system_prompt = f"""你是一位经验丰富的{scenario_name}面试辅导专家。

{context_hint}请针对以下面试问题，生成一份高质量的参考答案。

要求：
1. 使用 STAR 法则（情境-任务-行动-结果）结构回答（适用于行为类问题）
2. 内容要具体、有深度，展示真实的技术能力和思考过程
3. 语气专业自信，但不傲慢
4. 长度控制在 150-300 字，不要太长
5. 直接输出答案内容，不要包含"参考答案："之类的标题前缀
6. 不要使用 markdown 格式，用纯文本"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"面试问题：{question}\n\n请生成参考答案。"}
            ],
            "temperature": 0.5,
            "max_tokens": 800
        }

        try:
            with httpx.Client(timeout=httpx.Timeout(self.timeout)) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()

                if "choices" in response_data and len(response_data["choices"]) > 0:
                    return response_data["choices"][0]["message"]["content"].strip()
                return ""
        except Exception as e:
            print(f"[LLM] 生成参考答案失败: {e}")
            return ""


# 导出
__all__ = ["LLMClient", "LLM_TIMEOUT", "FALLBACK_QUESTIONS", "EXAMINER_PROFILES"]
