import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

class Logger:
    @staticmethod
    def _get_timestamp() -> str:
        return datetime.utcnow().isoformat() + "Z"
    
    @staticmethod
    def _get_trace_id() -> str:
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_request_id() -> str:
        return str(uuid.uuid4())
    
    @staticmethod
    def log_entry(
        request_id: str,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        log = {
            "timestamp": Logger._get_timestamp(),
            "level": "INFO",
            "request_id": request_id,
            "stage": "ENTRY",
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "params": params,
            "message": "Entering endpoint"
        }
        print(json.dumps(log, ensure_ascii=False))
    
    @staticmethod
    def log_step(
        request_id: str,
        step: str,
        status: str = "IN_PROGRESS",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        log = {
            "timestamp": Logger._get_timestamp(),
            "level": "DEBUG",
            "request_id": request_id,
            "stage": "STEP",
            "step": step,
            "status": status,
            "details": details,
            "message": f"Processing step: {step}"
        }
        print(json.dumps(log, ensure_ascii=False))
    
    @staticmethod
    def log_exit(
        request_id: str,
        endpoint: str,
        success: bool,
        latency_ms: int,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        log = {
            "timestamp": Logger._get_timestamp(),
            "level": "INFO" if success else "ERROR",
            "request_id": request_id,
            "stage": "EXIT",
            "endpoint": endpoint,
            "success": success,
            "latency_ms": latency_ms,
            "error": error,
            "result": result,
            "message": "Exiting endpoint" if success else f"Endpoint failed: {error}"
        }
        print(json.dumps(log, ensure_ascii=False))
    
    @staticmethod
    def log_error(
        request_id: str,
        step: str,
        error: str,
        stack_trace: Optional[str] = None
    ) -> None:
        log = {
            "timestamp": Logger._get_timestamp(),
            "level": "ERROR",
            "request_id": request_id,
            "stage": "ERROR",
            "step": step,
            "error": error,
            "stack_trace": stack_trace,
            "message": f"Error occurred in step: {step}"
        }
        print(json.dumps(log, ensure_ascii=False))