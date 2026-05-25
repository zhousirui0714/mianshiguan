import time
import json
from typing import List, Dict, Any, Optional
from uuid import uuid4

from src.models import Project, QuestionRecord, GenerateQuestionsRequest, GenerateQuestionsResponse
from src.utils.logger import Logger
from src.services.llm_client import LLMClient

class InterviewService:
    def __init__(self):
        self.llm_client = LLMClient()
    
    def generate_questions(
        self,
        project_id: str,
        project_name: str,
        project_description: str,
        tech_stack: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> GenerateQuestionsResponse:
        """
        生成刁钻追问的核心方法
        
        Args:
            project_id: 项目ID
            project_name: 项目名称
            project_description: 项目描述
            tech_stack: 技术栈列表
            user_id: 用户ID
        
        Returns:
            包含3条刁钻追问的响应
        """
        start_time = time.time()
        request_id = str(uuid4())
        endpoint = "/api/questions/generate"
        
        # 步骤1：进入日志
        Logger.log_entry(
            request_id=request_id,
            endpoint=endpoint,
            method="POST",
            user_id=user_id,
            params={
                "project_id": project_id,
                "project_name": project_name,
                "tech_stack": tech_stack
            }
        )
        
        try:
            # 步骤2：验证输入
            Logger.log_step(
                request_id=request_id,
                step="validate_input",
                status="IN_PROGRESS",
                details={"project_id": project_id, "has_description": len(project_description) > 0}
            )
            
            if not project_description or len(project_description.strip()) < 10:
                raise ValueError("项目描述过短，无法生成有效追问")
            
            Logger.log_step(
                request_id=request_id,
                step="validate_input",
                status="COMPLETED",
                details={"result": "valid"}
            )
            
            # 步骤3：调用LLM生成追问
            Logger.log_step(
                request_id=request_id,
                step="call_llm",
                status="IN_PROGRESS",
                details={"tech_stack": tech_stack, "description_length": len(project_description)}
            )
            
            result = self.llm_client.generate_questions_with_fallback(
                project_description=project_description,
                tech_stack=tech_stack or []
            )
            
            fallback_used = result.get("fallback", False)
            if fallback_used:
                Logger.log_step(
                    request_id=request_id,
                    step="call_llm",
                    status="FALLBACK",
                    details={"reason": result.get("fallback_reason", "unknown")}
                )
            else:
                Logger.log_step(
                    request_id=request_id,
                    step="call_llm",
                    status="COMPLETED",
                    details={"question_count": len(result.get("questions", []))}
                )
            
            # 步骤4：解析结果
            Logger.log_step(
                request_id=request_id,
                step="parse_result",
                status="IN_PROGRESS"
            )
            
            questions = []
            for q in result.get("questions", []):
                questions.append(QuestionRecord(
                    question=q.get("question", ""),
                    logic=q.get("logic", "")
                ))
            
            if len(questions) != 3:
                Logger.log_step(
                    request_id=request_id,
                    step="parse_result",
                    status="WARNING",
                    details={"expected": 3, "actual": len(questions)}
                )
            
            Logger.log_step(
                request_id=request_id,
                step="parse_result",
                status="COMPLETED",
                details={"question_count": len(questions)}
            )
            
            # 步骤5：出口日志（成功）
            latency_ms = int((time.time() - start_time) * 1000)
            Logger.log_exit(
                request_id=request_id,
                endpoint=endpoint,
                success=True,
                latency_ms=latency_ms,
                result={
                    "project_id": project_id,
                    "question_count": len(questions),
                    "fallback_used": fallback_used
                }
            )
            
            return GenerateQuestionsResponse(
                success=True,
                project_id=project_id,
                questions=questions,
                request_id=request_id,
                latency_ms=latency_ms
            )
        
        except Exception as e:
            # 出口日志（失败）
            latency_ms = int((time.time() - start_time) * 1000)
            Logger.log_error(
                request_id=request_id,
                step="generate_questions",
                error=str(e)
            )
            Logger.log_exit(
                request_id=request_id,
                endpoint=endpoint,
                success=False,
                latency_ms=latency_ms,
                error=str(e)
            )
            
            return GenerateQuestionsResponse(
                success=False,
                project_id=project_id,
                questions=[],
                request_id=request_id,
                latency_ms=latency_ms
            )

# 导出
__all__ = ["InterviewService"]