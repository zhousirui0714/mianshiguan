"""
真实场景演示 — 多 Agent 代码审查团队

Orchestrator 收到审查任务 → 分解给 3 个专业 Worker → 汇总审查报告

运行:
    python -m src.agents.multi_agent.real_demo
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.agents.multi_agent.workers import WorkerAgent, OrchestratorAgent
from src.agents.multi_agent.bus import MessageBus
from src.agents.multi_agent.task import SubTask


# ==================== 示例代码（要被审查的） ====================

SAMPLE_CODE = """
def login(username, password):
    user = db.query("SELECT * FROM users WHERE name='" + username + "'")
    if user and user.password == password:
        token = create_token(username)
        return {"status": "ok", "token": token}
    return {"status": "fail"}

def transfer_money(from_user, to_user, amount):
    db.execute("UPDATE accounts SET balance = balance - " + str(amount) + " WHERE user='" + from_user + "'")
    db.execute("UPDATE accounts SET balance = balance + " + str(amount) + " WHERE user='" + to_user + "'")
    return True
"""


# ==================== 3 个专业 Worker ====================

def security_auditor(data, task):
    """安全检查员：检查 SQL 注入、密码安全、认证漏洞"""
    code = data.get("code", "")
    findings = []

    if "+ username +" in code or "+ from_user +" in code:
        findings.append("SQL 注入风险：直接拼接用户输入到 SQL 语句")
    if "password ==" in code:
        findings.append("密码明文比较：密码应使用 bcrypt/scrypt 哈希存储和验证")
    if "create_token" in code and "expire" not in code:
        findings.append("Token 无过期时间：应设置合理的过期策略")
    if "transfer_money" in code and "balance" in code:
        findings.append("转账操作无事务保护：可能导致金额不一致")

    return {
        "category": "安全",
        "risk_level": "高" if len(findings) > 2 else "中",
        "findings": findings,
        "fix_suggestions": [
            "使用参数化查询 (PreparedStatement) 防止 SQL 注入",
            "密码使用 bcrypt 哈希存储，使用 hash == stored_hash 验证",
            "Token 添加 exp 字段，设置 15 分钟过期",
            "转账操作包裹在数据库事务中",
        ],
    }


def performance_auditor(data, task):
    """性能检查员：检查 N+1 查询、缓存缺失、无索引查询"""
    code = data.get("code", "")
    findings = []

    if "SELECT *" in code:
        findings.append("使用 SELECT *：应明确指定需要的列，减少数据传输")
    if "query(" in code and "LIMIT" not in code.upper():
        findings.append("查询无 LIMIT：可能返回大量数据，应加分页")
    if "transfer_money" in code and "execute" in code:
        findings.append("两次 execute 非原子操作：应用事务包裹保证一致性")

    return {
        "category": "性能",
        "risk_level": "中",
        "findings": findings,
        "fix_suggestions": [
            "SELECT * 改为指定列名",
            "添加 LIMIT 分页",
            "使用 BEGIN/COMMIT 事务包裹转账操作",
        ],
    }


def style_auditor(data, task):
    """代码规范检查员：检查命名、错误处理、函数设计"""
    code = data.get("code", "")
    findings = []

    if "def login" in code and "try" not in code:
        findings.append("缺少异常处理：数据库查询可能抛异常，应 try/except")
    if "return True" in code and "except" not in code:
        findings.append("函数忽略错误：transfer_money 总是返回 True，应返回实际结果")
    if "print" not in code and len(code.split("\n")) > 5:
        findings.append("缺少日志记录：关键操作（登录/转账）应记录日志")

    return {
        "category": "代码规范",
        "risk_level": "中",
        "findings": findings,
        "fix_suggestions": [
            "添加 try/except 处理数据库异常",
            "transfer_money 返回操作结果字典，包含错误信息",
            "添加 logging 记录关键操作",
        ],
    }


# ==================== 自定义 Orchestrator 分解/汇总逻辑 ====================

def decompose_code_review(user_input: str, workers):
    """将审查任务分解，所有 Worker 审查同一份代码，但从不同角度"""
    code = user_input
    return [
        SubTask(
            description="安全性审查",
            assigned_worker="security",
            input_schema={"code": "str"},
            input_data={"code": code},
            output_schema={"category": "str", "risk_level": "str", "findings": "list", "fix_suggestions": "list"},
        ),
        SubTask(
            description="性能审查",
            assigned_worker="performance",
            input_schema={"code": "str"},
            input_data={"code": code},
            output_schema={"category": "str", "risk_level": "str", "findings": "list", "fix_suggestions": "list"},
        ),
        SubTask(
            description="代码规范审查",
            assigned_worker="style",
            input_schema={"code": "str"},
            input_data={"code": code},
            output_schema={"category": "str", "risk_level": "str", "findings": "list", "fix_suggestions": "list"},
        ),
    ]


def aggregate_code_review(user_input, subtasks, results):
    """汇总生成审查报告"""
    total_findings = 0
    report_lines = ["=" * 50,
                    "  代码审查报告",
                    "=" * 50, ""]

    for r in results:
        data = r.output_data
        report_lines.append(f"## {data.get('category', '')}  (风险: {data.get('risk_level', '')})")
        findings = data.get("findings", [])
        total_findings += len(findings)
        for i, f in enumerate(findings, 1):
            report_lines.append(f"  {i}. {f}")
        suggestions = data.get("fix_suggestions", [])
        if suggestions:
            report_lines.append(f"  建议修复:")
            for s in suggestions:
                report_lines.append(f"    -> {s}")
        report_lines.append("")

    report_lines.append(f"共发现 {total_findings} 个问题，涉及 3 个审查维度。")
    report_lines.append("=" * 50)

    report_text = "\n".join(report_lines)

    return {
        "summary": f"审查完成，共发现 {total_findings} 个问题",
        "report": report_text,
        "total_issues": total_findings,
    }


# ==================== 运行 ====================

if __name__ == "__main__":
    bus = MessageBus(verbose=True)

    # 创建 3 个专业 Worker
    workers = [
        WorkerAgent("security", "安全审查专家",
                     capability="SQL注入/密码安全/认证漏洞检测",
                     input_schema={"code": "str"},
                     output_schema={"category": "str", "findings": "list", "fix_suggestions": "list"},
                     handler=security_auditor),
        WorkerAgent("performance", "性能优化专家",
                     capability="N+1查询/缓存/索引优化",
                     input_schema={"code": "str"},
                     output_schema={"category": "str", "findings": "list", "fix_suggestions": "list"},
                     handler=performance_auditor),
        WorkerAgent("style", "代码规范专家",
                     capability="异常处理/命名/日志/函数设计",
                     input_schema={"code": "str"},
                     output_schema={"category": "str", "findings": "list", "fix_suggestions": "list"},
                     handler=style_auditor),
    ]

    # 创建 Orchestrator（自定义分解和汇总逻辑）
    orchestrator = OrchestratorAgent(
        "code_review_orch", "代码审查协调员",
        decompose_fn=decompose_code_review,
        aggregate_fn=aggregate_code_review,
    )

    # 执行
    result = orchestrator.execute(SAMPLE_CODE, workers, bus)

    # 打印报告
    print("\n" + result.aggregated["report"])
