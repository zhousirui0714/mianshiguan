"""
数据库核心模块

提供：
- DatabaseManager: 基于 SQLite / PostgreSQL 的完整数据库操作
- 支持复杂关联查询
- 自动建表和迁移
- 自动检测 SUPABASE_DB_URL 环境变量，优先使用 PostgreSQL
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from src.core.database.models import CREATE_TABLES_SQL, dict_factory

# 整合 PostgreSQL 异常类型（如果可用）
try:
    import psycopg2
    _PG_INTEGRITY_ERROR = psycopg2.IntegrityError
except ImportError:
    _PG_INTEGRITY_ERROR = None

# 默认数据库路径
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data", "interview.db"
)


class DatabaseManager:
    """
    数据库管理器

    封装所有数据库操作，支持：
    - 自动建表
    - 用户/场景/题库管理
    - 对话/消息/答题管理
    - 成长档案/徽章管理
    - 复杂关联查询

    后端选择：检测 SUPABASE_DB_URL 环境变量
    - 有：使用 psycopg2 直连 Supabase PostgreSQL
    - 无：使用原有 SQLite
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.use_pg = False
        self.pg_pool = None

        # 检测 PostgreSQL 环境
        pg_url = os.environ.get("SUPABASE_DB_URL", "")
        if pg_url and pg_url.startswith("postgresql"):
            try:
                from src.core.database.pg_connection import PgConnectionPool
                self.pg_pool = PgConnectionPool(db_url=pg_url)
                self.use_pg = True
                self._init_pg_db()
            except Exception as e:
                import sys, traceback
                print(f"[DB] PostgreSQL 连接失败，回退到 SQLite: {e}", file=sys.stderr, flush=True)
                traceback.print_exc(file=sys.stderr)
                self.use_pg = False
                self.pg_pool = None

        if not self.use_pg:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self._init_db()
        # 设置异常类型元组
        self.IntegrityError = (
            (sqlite3.IntegrityError, psycopg2.IntegrityError)
            if _PG_INTEGRITY_ERROR
            else sqlite3.IntegrityError
        )

    # ==================== 连接管理 ====================

    def _get_conn(self):
        """获取数据库连接（PG 或 SQLite）"""
        if self.use_pg:
            return self.pg_pool.getconn()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = dict_factory
        self._execute(conn,"PRAGMA journal_mode=WAL")
        self._execute(conn,"PRAGMA foreign_keys=ON")
        return conn

    def _release_conn(self, conn) -> None:
        """归还数据库连接"""
        if self.use_pg:
            self.pg_pool.putconn(conn)
        else:
            conn.close()

    def _execute(self, conn, sql, params=None):
        """执行 SQL（自动适配 PG cursor 或 SQLite connection）

        PG 使用 %s 占位符，SQLite 使用 ? 占位符。
        本方法在 SQLite 模式下自动将 %s 替换为 ?。
        """
        if self.use_pg:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur
        # SQLite: 将 %s 占位符转换为 ?
        sqlite_sql = sql.replace("%s", "?")
        return conn.execute(sqlite_sql, params or [])

    def _init_pg_db(self) -> None:
        """初始化 PostgreSQL 数据库表"""
        from src.core.database.pg_schema import CREATE_TABLES_PG
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute(CREATE_TABLES_PG)
            conn.commit()
        finally:
            self._release_conn(conn)

    def _init_db(self) -> None:
        """初始化 SQLite 数据库表"""
        conn = self._get_conn()
        try:
            # [迁移优先] 先加列再建索引，避免 CREATE INDEX 引用不存在的列报错
            try:
                self._execute(conn,"ALTER TABLE conversations ADD COLUMN report_data TEXT DEFAULT '{}'")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            for col in ['company TEXT', 'position TEXT', 'source TEXT', 'year TEXT',
                         "source_type TEXT DEFAULT 'ai_generated'",
                         "question_level TEXT DEFAULT 'C'",
                         "interview_stage TEXT DEFAULT 'basic'",
                         "topics TEXT DEFAULT '[]'"]:
                try:
                    self._execute(conn,f"ALTER TABLE questions ADD COLUMN {col}")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass

            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()
        finally:
            self._release_conn(conn)

    # ==================== 用户管理 ====================

    def create_user(self, username: str, email: str, password_hash: str,
                    user_id: str = None) -> dict:
        conn = self._get_conn()
        try:
            user_id = user_id or str(uuid.uuid4())
            self._execute(conn,
                "INSERT INTO users (id, username, email, password_hash) VALUES (%s, %s, %s, %s)",
                (user_id, username, email, password_hash)
            )
            conn.commit()
            return {"success": True, "user_id": user_id}
        except self.IntegrityError:
            return {"success": False, "error": "邮箱已存在"}
        finally:
            self._release_conn(conn)

    def get_user(self, user_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            return self._execute(conn,"SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
        finally:
            self._release_conn(conn)

    def get_user_by_email(self, email: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            return self._execute(conn,"SELECT * FROM users WHERE email = %s", (email,)).fetchone()
        finally:
            self._release_conn(conn)

    # ==================== 场景管理 ====================

    def create_scenario(self, scenario_id: str, name: str, category: str = "",
                        description: str = "", max_rounds: int = 5,
                        config_json: dict = None) -> dict:
        conn = self._get_conn()
        try:
            self._execute(conn,
                "INSERT INTO scenarios (id, name, category, description, max_rounds, config_json) "
                "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                (scenario_id, name, category, description, max_rounds,
                 json.dumps(config_json or {}, ensure_ascii=False))
            )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def get_scenario(self, scenario_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            row = self._execute(conn,"SELECT * FROM scenarios WHERE id = %s", (scenario_id,)).fetchone()
            if row and row.get("config_json"):
                row["config"] = json.loads(row["config_json"])
            return row
        finally:
            self._release_conn(conn)

    def get_all_scenarios(self) -> List[dict]:
        conn = self._get_conn()
        try:
            return self._execute(conn,
                "SELECT * FROM scenarios WHERE enabled = 1 ORDER BY name"
            ).fetchall()
        finally:
            self._release_conn(conn)

    # ==================== 题库管理 ====================

    def add_question(self, scenario_id: str, category: str, difficulty: int,
                     question_text: str, reference_answer: str, tags: List[str] = None,
                     company: str = "", position: str = "", source: str = "",
                     year: str = "", source_type: str = "ai_generated",
                     question_level: str = "C",
                     interview_stage: str = "basic") -> dict:
        conn = self._get_conn()
        try:
            # 检查是否已存在相同问题
            existing = self._execute(conn,
                "SELECT id FROM questions WHERE scenario_id = %s AND question_text = %s",
                (scenario_id, question_text)
            ).fetchone()
            if existing:
                return {"success": True, "question_id": existing["id"]}

            qid = f"q_{uuid.uuid4().hex[:8]}"
            now = datetime.now().isoformat()
            self._execute(conn,
                "INSERT INTO questions (id, scenario_id, category, difficulty, "
                "question_text, reference_answer, tags, company, position, "
                "source, source_type, year, question_level, interview_stage, "
                "created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (qid, scenario_id, category, difficulty, question_text, reference_answer,
                 json.dumps(tags or [], ensure_ascii=False), company, position,
                 source, source_type, year, question_level, interview_stage, now, now)
            )
            conn.commit()
            return {"success": True, "question_id": qid}
        finally:
            self._release_conn(conn)

    def get_questions(self, scenario_id: str = None, category: str = None,
                      difficulty: int = None, keyword: str = None,
                      company: str = None, position: str = None,
                      year: str = None, source_type: str = None) -> List[dict]:
        conn = self._get_conn()
        try:
            sql = "SELECT * FROM questions WHERE 1=1"
            params = []
            if scenario_id:
                sql += " AND scenario_id = %s"
                params.append(scenario_id)
            if category:
                sql += " AND category = %s"
                params.append(category)
            if difficulty:
                sql += " AND difficulty = %s"
                params.append(difficulty)
            if keyword:
                sql += " AND (question_text LIKE %s OR reference_answer LIKE %s)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if company:
                sql += " AND company LIKE %s"
                params.append(f"%{company}%")
            if position:
                sql += " AND position LIKE %s"
                params.append(f"%{position}%")
            if year:
                sql += " AND year = %s"
                params.append(year)
            if source_type:
                sql += " AND source_type = %s"
                params.append(source_type)
            sql += " ORDER BY year DESC, created_at DESC"
            rows = self._execute(conn,sql, params).fetchall()
            # 解析 tags JSON
            for r in rows:
                if isinstance(r.get("tags"), str):
                    r["tags"] = json.loads(r["tags"])
            return rows
        finally:
            self._release_conn(conn)

    def search_questions_broad(self, keywords: List[str],
                                scenario_id: str = None,
                                limit: int = 20) -> List[dict]:
        """宽泛搜索：同时匹配题目、标签、分类、公司、岗位等字段"""
        if not keywords:
            return []
        conn = self._get_conn()
        try:
            # 构建多字段 OR 条件
            clauses = []
            params = []
            for kw in keywords:
                kw_param = f"%{kw}%"
                clauses.append(
                    "(question_text LIKE %s OR reference_answer LIKE %s OR "
                    "category LIKE %s OR company LIKE %s OR position LIKE %s OR "
                    "tags LIKE %s)"
                )
                params.extend([kw_param, kw_param, kw_param, kw_param, kw_param, kw_param])

            sql = "SELECT * FROM questions WHERE " + " OR ".join(clauses)
            if scenario_id:
                sql += " AND scenario_id = %s"
                params.append(scenario_id)
            sql += (" ORDER BY CASE question_level "
                    "WHEN 'S' THEN 0 WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END "
                    "LIMIT %s")
            params.append(limit)

            rows = self._execute(conn,sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("tags"), str):
                    r["tags"] = json.loads(r["tags"])
            return rows
        finally:
            self._release_conn(conn)

    def search_questions_targeted(self, company: str = "",
                                   position: str = "",
                                   scenario_id: str = None,
                                   limit: int = 20) -> List[dict]:
        """按公司+岗位精确搜索，优先返回真实企业真题

        级联策略：公司AND岗位 → 公司OR岗位 → 返回空列表
        """
        conn = self._get_conn()
        try:
            all_rows = []
            seen_ids = set()

            for cascade in ["AND", "OR"]:
                if len(all_rows) >= limit:
                    break
                if cascade == "AND" and (not company or not position):
                    continue  # 没有两个条件时跳过 AND

                sql = "SELECT * FROM questions WHERE 1=1"
                params = []

                if cascade == "AND":
                    sql += " AND company LIKE %s AND position LIKE %s"
                    params.extend([f"%{company}%", f"%{position}%"])
                else:
                    conditions = []
                    if company:
                        conditions.append("company LIKE %s")
                        params.append(f"%{company}%")
                    if position:
                        conditions.append("position LIKE %s")
                        params.append(f"%{position}%")
                    if conditions:
                        sql += " AND (" + " OR ".join(conditions) + ")"

                if scenario_id:
                    sql += " AND scenario_id = %s"
                    params.append(scenario_id)

                # 真实面经优先 + S/A 级优先
                sql += (" ORDER BY CASE source_type "
                        "WHEN 'real_interview' THEN 0 WHEN 'open_source' THEN 1 ELSE 2 END, "
                        "CASE question_level "
                        "WHEN 'S' THEN 0 WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END "
                        "LIMIT %s")
                params.append(limit)

                rows = self._execute(conn,sql, params).fetchall()
                for r in rows:
                    rid = r["id"]
                    if rid not in seen_ids:
                        seen_ids.add(rid)
                        all_rows.append(r)
                        if len(all_rows) >= limit:
                            break

            for r in all_rows:
                if isinstance(r.get("tags"), str):
                    r["tags"] = json.loads(r["tags"])
            return all_rows[:limit]
        finally:
            self._release_conn(conn)

    def get_top_questions(self, scenario_id: str = None,
                          limit: int = 20) -> List[dict]:
        """获取评分最高的题目（兜底展示用）"""
        conn = self._get_conn()
        try:
            sql = ("SELECT * FROM questions WHERE 1=1")
            params = []
            if scenario_id:
                sql += " AND scenario_id = %s"
                params.append(scenario_id)
            sql += (" ORDER BY CASE question_level "
                    "WHEN 'S' THEN 0 WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END "
                    "LIMIT %s")
            params.append(limit)
            rows = self._execute(conn,sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("tags"), str):
                    r["tags"] = json.loads(r["tags"])
            return rows
        finally:
            self._release_conn(conn)

    def get_question(self, question_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            row = self._execute(conn,
                "SELECT * FROM questions WHERE id = %s", (question_id,)
            ).fetchone()
            if row and isinstance(row.get("tags"), str):
                row["tags"] = json.loads(row["tags"])
            return row
        finally:
            self._release_conn(conn)

    def update_question(self, question_id: str, **kwargs) -> dict:
        conn = self._get_conn()
        try:
            existing = self._execute(conn,
                "SELECT id FROM questions WHERE id = %s", (question_id,)
            ).fetchone()
            if not existing:
                return {"success": False, "error": "题目不存在"}

            allowed = ["scenario_id", "category", "difficulty",
                       "question_text", "reference_answer", "tags",
                       "company", "position", "source", "year",
                       "source_type", "question_level",
                       "interview_stage", "target_positions"]
            updates = {}
            for k, v in kwargs.items():
                if k in allowed:
                    updates[k] = v
            if not updates:
                return {"success": True}

            set_clause = ", ".join(f"{k} = %s" for k in updates)
            values = list(updates.values())
            if "tags" in updates:
                idx = list(updates.keys()).index("tags")
                values[idx] = json.dumps(values[idx], ensure_ascii=False)

            now = datetime.now().isoformat()
            self._execute(conn,
                f"UPDATE questions SET {set_clause}, updated_at = %s WHERE id = %s",
                values + [now, question_id]
            )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def delete_question(self, question_id: str) -> dict:
        conn = self._get_conn()
        try:
            existing = self._execute(conn,
                "SELECT id FROM questions WHERE id = %s", (question_id,)
            ).fetchone()
            if not existing:
                return {"success": False, "error": "题目不存在"}
            self._execute(conn,"DELETE FROM questions WHERE id = %s", (question_id,))
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def get_categories(self, scenario_id: str = None) -> List[str]:
        conn = self._get_conn()
        try:
            sql = "SELECT DISTINCT category FROM questions WHERE 1=1"
            params = []
            if scenario_id:
                sql += " AND scenario_id = %s"
                params.append(scenario_id)
            sql += " ORDER BY category"
            return [r["category"] for r in self._execute(conn,sql, params).fetchall()]
        finally:
            self._release_conn(conn)

    def get_distinct_values(self, field: str, scenario_id: str = None) -> List[str]:
        """获取某字段的非重复有效值（用于筛选下拉框）"""
        conn = self._get_conn()
        try:
            sql = f"SELECT DISTINCT {field} FROM questions WHERE {field} IS NOT NULL AND {field} != ''"
            params = []
            if scenario_id:
                sql += " AND scenario_id = %s"
                params.append(scenario_id)
            sql += f" ORDER BY {field}"
            return [r[field] for r in self._execute(conn,sql, params).fetchall()]
        finally:
            self._release_conn(conn)

    def get_companies(self, scenario_id: str = None) -> List[str]:
        return self.get_distinct_values("company", scenario_id)

    def get_positions(self, scenario_id: str = None) -> List[str]:
        return self.get_distinct_values("position", scenario_id)

    def get_years(self, scenario_id: str = None) -> List[str]:
        return self.get_distinct_values("year", scenario_id)

    def get_tags(self, scenario_id: str = None) -> List[str]:
        conn = self._get_conn()
        try:
            sql = "SELECT tags FROM questions WHERE 1=1"
            params = []
            if scenario_id:
                sql += " AND scenario_id = %s"
                params.append(scenario_id)
            rows = self._execute(conn,sql, params).fetchall()
            tags = set()
            for r in rows:
                tag_list = json.loads(r["tags"]) if isinstance(r["tags"], str) else (r["tags"] or [])
                tags.update(tag_list)
            return sorted(tags)
        finally:
            self._release_conn(conn)

    # ==================== 对话管理 ====================

    def create_conversation(self, user_id: str, scenario_id: str,
                            scenario_name: str = "", user_background: str = "",
                            conversation_id: str = None) -> dict:
        conn = self._get_conn()
        try:
            conv_id = conversation_id or str(uuid.uuid4())
            now = datetime.now().isoformat()
            # 自动创建用户（同一连接 + 事务，避免 FK 约束问题）
            existing_user = self._execute(conn,
                "SELECT id FROM users WHERE id = %s", (user_id,)
            ).fetchone()
            if not existing_user:
                self._execute(conn,
                    "INSERT INTO users (id, username, email, password_hash) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                    (user_id, f"用户{user_id}", f"{user_id}@example.com", "auto")
                )
            self._execute(conn,
                "INSERT INTO conversations (id, user_id, scenario_id, scenario_name, "
                "user_background, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (conv_id, user_id, scenario_id, scenario_name, user_background, now, now)
            )
            conn.commit()
            return {"success": True, "conversation_id": conv_id}
        except self.IntegrityError as e:
            return {"success": False, "error": str(e)}
        finally:
            self._release_conn(conn)

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            row = self._execute(conn,
                "SELECT * FROM conversations WHERE id = %s", (conversation_id,)
            ).fetchone()
            if row:
                row["messages"] = self._get_messages(conn, conversation_id)
            return row
        finally:
            self._release_conn(conn)

    def update_conversation_status(self, conversation_id: str, status: str) -> dict:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            self._execute(conn,
                "UPDATE conversations SET status = %s, updated_at = %s WHERE id = %s",
                (status, now, conversation_id)
            )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def update_conversation_report(self, conversation_id: str, report_data: dict) -> dict:
        """保存面试报告数据到 conversations 表"""
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            self._execute(conn,
                "UPDATE conversations SET report_data = %s, updated_at = %s WHERE id = %s",
                (json.dumps(report_data, ensure_ascii=False), now, conversation_id)
            )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def get_user_conversations(self, user_id: str) -> List[dict]:
        conn = self._get_conn()
        try:
            rows = self._execute(conn,
                "SELECT * FROM conversations WHERE user_id = %s ORDER BY updated_at DESC",
                (user_id,)
            ).fetchall()
            for row in rows:
                row["messages"] = self._get_messages(conn, row["id"])
            return rows
        finally:
            self._release_conn(conn)

    def increment_conversation_round(self, conversation_id: str) -> None:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            self._execute(conn,
                "UPDATE conversations SET round_count = round_count + 1, updated_at = %s WHERE id = %s",
                (now, conversation_id)
            )
            conn.commit()
        finally:
            self._release_conn(conn)

    def add_message(self, conversation_id: str, role: str, content: str) -> dict:
        conn = self._get_conn()
        try:
            mid = str(uuid.uuid4())
            # 获取当前最大序号
            max_order = self._execute(conn,
                "SELECT COALESCE(MAX(msg_order), 0) AS max_order FROM messages WHERE conversation_id = %s",
                (conversation_id,)
            ).fetchone()["max_order"]
            now = datetime.now().isoformat()
            self._execute(conn,
                "INSERT INTO messages (id, conversation_id, role, content, msg_order, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (mid, conversation_id, role, content, max_order + 1, now)
            )
            conn.commit()
            if role == "assistant":
                self.increment_conversation_round(conversation_id)
            return {"success": True, "message_id": mid}
        finally:
            self._release_conn(conn)

    def _get_messages(self, conn: sqlite3.Connection, conversation_id: str) -> List[dict]:
        return self._execute(conn,
            "SELECT * FROM messages WHERE conversation_id = %s ORDER BY msg_order",
            (conversation_id,)
        ).fetchall()

    # ==================== 答题管理 ====================

    def add_answer(self, user_id: str, conversation_id: str, question_id: Optional[str],
                   round_num: int, question_text: str, answer_text: str,
                   score: float = None, dimension_scores: dict = None,
                   feedback: str = "", duration: int = 0) -> dict:
        conn = self._get_conn()
        try:
            # 防重复：检查是否已存在相同 conversation + round 的答案
            existing = self._execute(conn,
                "SELECT id FROM answers WHERE conversation_id = %s AND round = %s",
                (conversation_id, round_num)
            ).fetchone()
            if existing:
                return {"success": True, "answer_id": existing["id"], "skipped": True}

            aid = str(uuid.uuid4())
            now = datetime.now().isoformat()
            self._execute(conn,
                "INSERT INTO answers (id, user_id, conversation_id, question_id, round, "
                "question_text, answer_text, score, dimension_scores, feedback, duration, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (aid, user_id, conversation_id, question_id, round_num,
                 question_text, answer_text, score,
                 json.dumps(dimension_scores or {}, ensure_ascii=False),
                 feedback, duration, now)
            )
            conn.commit()
            return {"success": True, "answer_id": aid}
        finally:
            self._release_conn(conn)

    def get_conversation_answers(self, conversation_id: str) -> List[dict]:
        conn = self._get_conn()
        try:
            rows = self._execute(conn,
                "SELECT * FROM answers WHERE conversation_id = %s ORDER BY round",
                (conversation_id,)
            ).fetchall()
            for r in rows:
                if isinstance(r.get("dimension_scores"), str):
                    r["dimension_scores"] = json.loads(r["dimension_scores"])
            return rows
        finally:
            self._release_conn(conn)

    def get_conversation_result(self, conversation_id: str) -> Optional[dict]:
        """获取面试结果数据（含答案聚合 + 报告 + 排名）"""
        conn = self._get_conn()
        try:
            # 1. 获取会话基本信息
            conv = self._execute(conn,
                "SELECT * FROM conversations WHERE id = %s", (conversation_id,)
            ).fetchone()
            if not conv:
                return None

            # 2. 获取该会话的所有答题记录
            answers = self._execute(conn,
                "SELECT * FROM answers WHERE conversation_id = %s ORDER BY round",
                (conversation_id,)
            ).fetchall()

            # 3. 解析 report_data
            report_data = {}
            raw_report = conv.get("report_data", "{}")
            if isinstance(raw_report, str) and raw_report.strip():
                try:
                    report_data = json.loads(raw_report)
                except json.JSONDecodeError:
                    report_data = {}

            # 4. 计算各项指标
            total_rounds = len(answers)
            total_duration = sum(a.get("duration", 0) or 0 for a in answers)
            total_duration_min = round(total_duration / 60, 1)

            # 总分：优先用 report_data 中的 overall_score，否则从 answers 计算
            overall_score = report_data.get("overall_score")
            if overall_score is None:
                scores = [a["score"] for a in answers if a.get("score") is not None]
                overall_score = round(sum(scores) / len(scores), 1) if scores else 0

            # 维度分：聚合所有 answer 的 dimension_scores，取平均值
            dim_agg = {}
            dim_count = {}
            for a in answers:
                raw = a.get("dimension_scores", "{}")
                dims = {}
                if isinstance(raw, str) and raw.strip():
                    try:
                        dims = json.loads(raw)
                    except json.JSONDecodeError:
                        dims = {}
                elif isinstance(raw, dict):
                    dims = raw
                for k, v in dims.items():
                    if isinstance(v, (int, float)):
                        dim_agg.setdefault(k, 0)
                        dim_agg[k] += v
                        dim_count.setdefault(k, 0)
                        dim_count[k] += 1

            dimensions = []
            for name in sorted(dim_agg.keys()):
                avg = round(dim_agg[name] / dim_count[name], 1) if dim_count.get(name) else 0
                dimensions.append({"name": name, "score": avg, "max_score": 100})

            # 5. 百分比排名
            scenario_id = conv.get("scenario_id", "")
            all_avgs = self._execute(conn,
                "SELECT avg_score FROM progress WHERE scenario_id = %s AND avg_score IS NOT NULL",
                (scenario_id,)
            ).fetchall()
            percentile = 50.0
            if all_avgs:
                all_scores = sorted([r["avg_score"] for r in all_avgs])
                below = sum(1 for s in all_scores if s < overall_score)
                percentile = round(below / len(all_scores) * 100, 1) if all_scores else 50.0

            # 6. 新解锁徽章（本次会话期间解锁的徽章）
            new_badges = report_data.get("new_badges", [])
            if not new_badges:
                # fallback: 从数据库查询
                user_id = conv.get("user_id", "")
                conv_created = conv.get("created_at", "")
                if user_id and conv_created:
                    badge_rows = self._execute(conn,
                        """SELECT b.id, b.name, b.description, b.icon, b.rarity
                           FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
                           WHERE ub.user_id = %s AND ub.unlocked_at >= %s
                           ORDER BY ub.unlocked_at DESC""",
                        (user_id, conv_created)
                    ).fetchall()
                    new_badges = badge_rows

            # 7. 组装返回
            result = {
                "conversation_id": conversation_id,
                "scenario_id": scenario_id,
                "scenario_name": conv.get("scenario_name", ""),
                "status": conv.get("status", ""),
                "created_at": conv.get("created_at", ""),
                "round_count": total_rounds or conv.get("round_count", 0),
                "total_duration": total_duration,
                "total_duration_min": total_duration_min,
                "overall_score": overall_score,
                "percentile": percentile,
                "dimensions": dimensions,
                "strengths": report_data.get("strengths", []),
                "improvements": report_data.get("improvements", []),
                "overall_comment": report_data.get("overall_comment", ""),
                "new_badges": new_badges,
                "answers": [
                    {
                        "round": a["round"],
                        "question": a.get("question_text", ""),
                        "answer": a.get("answer_text", ""),
                        "score": a.get("score"),
                        "feedback": a.get("feedback", ""),
                    }
                    for a in answers
                ],
            }
            return result
        finally:
            self._release_conn(conn)

    def get_user_answers(self, user_id: str, scenario_id: str = None,
                         limit: int = 50) -> List[dict]:
        """获取用户答题记录（支持按场景筛选）"""
        conn = self._get_conn()
        try:
            sql = ("SELECT a.*, c.scenario_id FROM answers a "
                   "JOIN conversations c ON a.conversation_id = c.id "
                   "WHERE a.user_id = %s")
            params = [user_id]
            if scenario_id:
                sql += " AND c.scenario_id = %s"
                params.append(scenario_id)
            sql += " ORDER BY a.created_at DESC LIMIT %s"
            params.append(limit)
            rows = self._execute(conn,sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("dimension_scores"), str):
                    r["dimension_scores"] = json.loads(r["dimension_scores"])
            return rows
        finally:
            self._release_conn(conn)

    # ==================== 成长档案 ====================

    def update_progress(self, user_id: str, scenario_id: str, score: float) -> dict:
        """更新用户在某场景的成长档案"""
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            existing = self._execute(conn,
                "SELECT * FROM progress WHERE user_id = %s AND scenario_id = %s",
                (user_id, scenario_id)
            ).fetchone()

            if existing:
                # 更新
                new_total = existing["total_practices"] + 1
                new_avg = (existing["avg_score"] * existing["total_practices"] + score) / new_total
                new_max = max(existing["max_score"], score)
                # 最近10次分数
                latest = json.loads(existing["latest_scores"]) if existing["latest_scores"] else []
                latest.append(score)
                latest = latest[-10:]

                self._execute(conn,
                    "UPDATE progress SET total_practices = %s, total_answers = total_answers + 1, "
                    "avg_score = %s, max_score = %s, latest_scores = %s, last_practiced_at = %s "
                    "WHERE user_id = %s AND scenario_id = %s",
                    (new_total, round(new_avg, 1), new_max,
                     json.dumps(latest, ensure_ascii=False), now, user_id, scenario_id)
                )
            else:
                # 新建
                pid = str(uuid.uuid4())
                self._execute(conn,
                    "INSERT INTO progress (id, user_id, scenario_id, total_practices, total_answers, "
                    "avg_score, max_score, latest_scores, last_practiced_at, created_at) "
                    "VALUES (%s, %s, %s, 1, 1, %s, %s, %s, %s, %s)",
                    (pid, user_id, scenario_id, round(score, 1), score,
                     json.dumps([score], ensure_ascii=False), now, now)
                )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def get_user_progress(self, user_id: str, scenario_id: str = None) -> List[dict]:
        """获取用户成长档案（支持按场景筛选）"""
        conn = self._get_conn()
        try:
            sql = ("SELECT p.*, s.name as scenario_name, s.category FROM progress p "
                   "JOIN scenarios s ON p.scenario_id = s.id WHERE p.user_id = %s")
            params = [user_id]
            if scenario_id:
                sql += " AND p.scenario_id = %s"
                params.append(scenario_id)
            sql += " ORDER BY s.name"
            rows = self._execute(conn,sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("latest_scores"), str):
                    r["latest_scores"] = json.loads(r["latest_scores"])
            return rows
        finally:
            self._release_conn(conn)

    # ==================== 徽章管理 ====================

    def add_badge(self, badge_id: str, name: str, description: str, icon: str = "🎯",
                  category: str = "common", unlock_condition: dict = None,
                  rarity: str = "common") -> dict:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            self._execute(conn,
                "INSERT INTO badges (id, name, description, icon, category, unlock_condition, rarity, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                (badge_id, name, description, icon, category,
                 json.dumps(unlock_condition or {}, ensure_ascii=False), rarity, now)
            )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def get_all_badges(self) -> List[dict]:
        conn = self._get_conn()
        try:
            rows = self._execute(conn,"SELECT * FROM badges ORDER BY category, name").fetchall()
            for r in rows:
                if isinstance(r.get("unlock_condition"), str):
                    r["unlock_condition"] = json.loads(r["unlock_condition"])
            return rows
        finally:
            self._release_conn(conn)

    def unlock_user_badge(self, user_id: str, badge_id: str) -> dict:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            self._execute(conn,
                "INSERT INTO user_badges (user_id, badge_id, unlocked_at, is_new) "
                "VALUES (%s, %s, %s, 1) ON CONFLICT (user_id, badge_id) DO NOTHING",
                (user_id, badge_id, now)
            )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    def get_user_badges(self, user_id: str) -> List[dict]:
        """获取用户已解锁的徽章（含徽章详情）"""
        conn = self._get_conn()
        try:
            rows = self._execute(conn,
                "SELECT b.*, ub.unlocked_at, ub.is_new FROM user_badges ub "
                "JOIN badges b ON ub.badge_id = b.id "
                "WHERE ub.user_id = %s ORDER BY ub.unlocked_at DESC",
                (user_id,)
            ).fetchall()
            return rows
        finally:
            self._release_conn(conn)

    def get_user_new_badge_count(self, user_id: str) -> int:
        conn = self._get_conn()
        try:
            row = self._execute(conn,
                "SELECT COUNT(*) as cnt FROM user_badges WHERE user_id = %s AND is_new = 1",
                (user_id,)
            ).fetchone()
            return row["cnt"] if row else 0
        finally:
            self._release_conn(conn)

    def mark_badge_viewed(self, user_id: str, badge_id: str) -> dict:
        conn = self._get_conn()
        try:
            self._execute(conn,
                "UPDATE user_badges SET is_new = 0 WHERE user_id = %s AND badge_id = %s",
                (user_id, badge_id)
            )
            conn.commit()
            return {"success": True}
        finally:
            self._release_conn(conn)

    # ==================== 复杂关联查询 ====================

    def get_user_scenario_detail(self, user_id: str, scenario_id: str) -> dict:
        """
        复杂查询：某用户在某场景的完整学习档案

        返回：
        - user: 用户信息
        - scenario: 场景信息
        - progress: 成长档案
        - recent_answers: 最近答题记录（含评分）
        - conversations: 对话历史
        - badges: 已获得的徽章
        - total_badges: 该场景相关徽章总数
        """
        conn = self._get_conn()
        try:
            user = self._execute(conn,"SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
            scenario = self._execute(conn,
                "SELECT * FROM scenarios WHERE id = %s", (scenario_id,)
            ).fetchone()
            progress = self._execute(conn,
                "SELECT * FROM progress WHERE user_id = %s AND scenario_id = %s",
                (user_id, scenario_id)
            ).fetchone()
            recent_answers = self._execute(conn,
                "SELECT a.* FROM answers a "
                "JOIN conversations c ON a.conversation_id = c.id "
                "WHERE a.user_id = %s AND c.scenario_id = %s "
                "ORDER BY a.created_at DESC LIMIT 10",
                (user_id, scenario_id)
            ).fetchall()
            conversations = self._execute(conn,
                "SELECT * FROM conversations WHERE user_id = %s AND scenario_id = %s "
                "ORDER BY created_at DESC LIMIT 5",
                (user_id, scenario_id)
            ).fetchall()
            # 该场景下获得的徽章
            badges = self._execute(conn,
                "SELECT b.*, ub.unlocked_at FROM user_badges ub "
                "JOIN badges b ON ub.badge_id = b.id "
                "WHERE ub.user_id = %s AND b.category = 'scenario'",
                (user_id,)
            ).fetchall()

            return {
                "user": user,
                "scenario": scenario,
                "progress": progress,
                "recent_answers": recent_answers,
                "conversations": conversations,
                "badges": badges,
            }
        finally:
            self._release_conn(conn)

    def get_scenario_leaderboard(self, scenario_id: str, limit: int = 10) -> List[dict]:
        """排行榜：某场景下用户按照平均分排序"""
        conn = self._get_conn()
        try:
            return self._execute(conn,
                "SELECT p.user_id, u.username, p.avg_score, p.total_practices, p.max_score "
                "FROM progress p JOIN users u ON p.user_id = u.id "
                "WHERE p.scenario_id = %s AND p.total_practices > 0 "
                "ORDER BY p.avg_score DESC LIMIT %s",
                (scenario_id, limit)
            ).fetchall()
        finally:
            self._release_conn(conn)

    def get_scenario_statistics(self, scenario_id: str) -> dict:
        """场景统计信息"""
        conn = self._get_conn()
        try:
            total_users = self._execute(conn,
                "SELECT COUNT(DISTINCT user_id) as cnt FROM progress WHERE scenario_id = %s "
                "AND total_practices > 0", (scenario_id,)
            ).fetchone()["cnt"]

            avg_stats = self._execute(conn,
                "SELECT AVG(avg_score) as avg_all, AVG(max_score) as avg_max, "
                "SUM(total_practices) as total_practices FROM progress WHERE scenario_id = %s",
                (scenario_id,)
            ).fetchone()

            total_questions = self._execute(conn,
                "SELECT COUNT(*) as cnt FROM questions WHERE scenario_id = %s",
                (scenario_id,)
            ).fetchone()["cnt"]

            return {
                "scenario_id": scenario_id,
                "total_users": total_users or 0,
                "avg_score": round(avg_stats["avg_all"] or 0, 1),
                "avg_max_score": round(avg_stats["avg_max"] or 0, 1),
                "total_practices": avg_stats["total_practices"] or 0,
                "total_questions": total_questions,
            }
        finally:
            self._release_conn(conn)

    def check_and_unlock_badges(self, user_id: str, scenario_id: str, score: float,
                                 duration: int = None) -> List[dict]:
        """
        自动检测并解锁符合条件的徽章

        返回新解锁的徽章列表
        """
        new_badges = []
        conn = self._get_conn()
        try:
            user_badge_ids = {
                r["badge_id"] for r in self._execute(conn,
                    "SELECT badge_id FROM user_badges WHERE user_id = %s", (user_id,)
                ).fetchall()
            }

            progress = self._execute(conn,
                "SELECT * FROM progress WHERE user_id = %s AND scenario_id = %s",
                (user_id, scenario_id)
            ).fetchone() or {}

            all_badges = self._execute(conn,"SELECT * FROM badges").fetchall()
            for badge in all_badges:
                if badge["id"] in user_badge_ids:
                    continue

                condition = json.loads(badge["unlock_condition"]) if badge["unlock_condition"] else {}
                cond_type = condition.get("type", "")

                unlocked = False
                if cond_type == "first_practice":
                    unlocked = (progress.get("total_practices", 0) or 0) >= 1
                elif cond_type == "first_high_score":
                    unlocked = score >= (condition.get("threshold", 80) or 80)
                elif cond_type == "total_practices":
                    unlocked = (progress.get("total_practices", 0) or 0) >= (condition.get("count", 10) or 10)
                elif cond_type == "scenario_high_score":
                    unlocked = (scenario_id == condition.get("scenario") and
                                score >= (condition.get("threshold", 90) or 90))
                elif cond_type == "scenario_practices":
                    unlocked = (scenario_id == condition.get("scenario") and
                                (progress.get("total_practices", 0) or 0) >= (condition.get("count", 3) or 3))
                elif cond_type == "speed_score":
                    unlocked = (duration is not None and
                                duration <= (condition.get("duration", 30) or 30) and
                                score >= (condition.get("threshold", 85) or 85))
                elif cond_type == "improvement":
                    latest_scores = json.loads(progress.get("latest_scores", "[]")) if isinstance(progress.get("latest_scores"), str) else (progress.get("latest_scores") or [])
                    if len(latest_scores) >= (condition.get("scenario_count", 5) or 5):
                        old_avg = sum(latest_scores[:-1]) / (len(latest_scores) - 1)
                        unlocked = (score - old_avg) >= (condition.get("improvement", 20) or 20)
                elif cond_type == "view_explanations":
                    unlocked = (progress.get("total_practices", 0) or 0) >= (condition.get("count", 5) or 5)
                elif cond_type == "all_scenarios":
                    completed = self._execute(conn,
                        "SELECT COUNT(DISTINCT scenario_id) as cnt FROM progress "
                        "WHERE user_id = %s AND total_practices > 0", (user_id,)
                    ).fetchone()["cnt"]
                    unlocked = completed >= 6
                elif cond_type == "streak":
                    unlocked = (progress.get("total_practices", 0) or 0) >= (condition.get("days", 3) or 3)

                if unlocked:
                    now_ts = datetime.now().isoformat()
                    self._execute(conn,
                        "INSERT INTO user_badges (user_id, badge_id, unlocked_at, is_new) "
                        "VALUES (%s, %s, %s, 1) ON CONFLICT (user_id, badge_id) DO NOTHING",
                        (user_id, badge["id"], now_ts)
                    )
                    new_badges.append(badge)

            conn.commit()
            return new_badges
        finally:
            self._release_conn(conn)

    # ==================== 数据可视化查询 ====================

    def get_user_summary(self, user_id: str) -> dict:
        """
        获取用户聚合概览（成长中心顶部统计卡片用）

        返回：
        - total_practices: 总练习次数
        - avg_score: 所有场景平均分的均值
        - total_badges: 徽章总数
        - scenario_count: 有练习记录的场景数
        - score_distribution: { "<60": N, "60-69": N, "70-79": N, "80-89": N, "90-100": N }
        - last_practice_date: 最近练习日期
        """
        conn = self._get_conn()
        try:
            # 总练习次数
            total_row = self._execute(conn,
                "SELECT COALESCE(SUM(total_practices), 0) as total_practices, "
                "COALESCE(AVG(avg_score), 0) as avg_score, "
                "COUNT(DISTINCT scenario_id) as scenario_count "
                "FROM progress WHERE user_id = %s AND total_practices > 0",
                (user_id,)
            ).fetchone()

            # 徽章总数
            badge_row = self._execute(conn,
                "SELECT COUNT(*) as cnt FROM user_badges WHERE user_id = %s",
                (user_id,)
            ).fetchone()

            # 最近练习日期
            last_date_row = self._execute(conn,
                "SELECT MAX(created_at) as last_date FROM answers WHERE user_id = %s",
                (user_id,)
            ).fetchone()

            # 分数分布：从 progress.latest_scores 提取所有分数
            progress_rows = self._execute(conn,
                "SELECT latest_scores FROM progress WHERE user_id = %s AND total_practices > 0",
                (user_id,)
            ).fetchall()

            distribution = {"<60": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
            for row in progress_rows:
                scores = row.get("latest_scores")
                if isinstance(scores, str):
                    scores = json.loads(scores)
                if isinstance(scores, list):
                    for s in scores:
                        s = float(s)
                        if s < 60:
                            distribution["<60"] += 1
                        elif s < 70:
                            distribution["60-69"] += 1
                        elif s < 80:
                            distribution["70-79"] += 1
                        elif s < 90:
                            distribution["80-89"] += 1
                        else:
                            distribution["90-100"] += 1

            return {
                "total_practices": total_row["total_practices"] or 0,
                "avg_score": round(total_row["avg_score"] or 0, 1),
                "total_badges": badge_row["cnt"] or 0,
                "scenario_count": total_row["scenario_count"] or 0,
                "score_distribution": distribution,
                "last_practice_date": last_date_row["last_date"] if last_date_row else None,
            }
        finally:
            self._release_conn(conn)

    def get_dimension_trend(self, user_id: str) -> List[dict]:
        """
        获取各维度得分趋势（用于折线图）

        从 answers 表的 dimension_scores JSON 中提取每个维度的分数，
        按时间排序返回扁平列表。

        返回：[{date, dimension_name, score, scenario_id}, ...]
        """
        conn = self._get_conn()
        try:
            rows = self._execute(conn,
                "SELECT a.created_at, a.dimension_scores, c.scenario_id "
                "FROM answers a "
                "JOIN conversations c ON a.conversation_id = c.id "
                "WHERE a.user_id = %s AND a.dimension_scores IS NOT NULL "
                "AND a.dimension_scores != '{}' AND a.dimension_scores != '' "
                "ORDER BY a.created_at ASC",
                (user_id,)
            ).fetchall()

            result = []
            for row in rows:
                raw = row.get("dimension_scores")
                if isinstance(raw, str):
                    try:
                        dims = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        continue
                elif isinstance(raw, dict):
                    dims = raw
                else:
                    continue

                if not dims:
                    continue

                for dim_name, score in dims.items():
                    try:
                        result.append({
                            "date": row["created_at"],
                            "dimension_name": dim_name,
                            "score": float(score),
                            "scenario_id": row.get("scenario_id", ""),
                        })
                    except (ValueError, TypeError):
                        continue

            return result
        finally:
            self._release_conn(conn)

    def get_user_dashboard_stats(self, user_id: str) -> dict:
        """获取首页看板统计数据"""
        conn = self._get_conn()
        try:
            # 1. 累计练习时长（秒）
            duration_row = self._execute(conn,
                "SELECT COALESCE(SUM(duration), 0) as total_seconds FROM answers WHERE user_id = %s",
                (user_id,)
            ).fetchone()
            total_seconds = duration_row["total_seconds"] if duration_row else 0

            # 2. 完成模拟次数
            count_row = self._execute(conn,
                "SELECT COUNT(*) as cnt FROM conversations WHERE user_id = %s AND status = 'finished'",
                (user_id,)
            ).fetchone()
            total_practices = count_row["cnt"] if count_row else 0

            # 3. 连续练习天数
            streak = self.get_user_streak(user_id)

            # 4. 最近 7 次练习得分趋势
            recent_scores = self._execute(conn,
                "SELECT score, created_at FROM answers WHERE user_id = %s AND score IS NOT NULL "
                "ORDER BY created_at DESC LIMIT 7",
                (user_id,)
            ).fetchall()

            # 5. 维度平均分（最近 10 次练习）
            last_answers = self._execute(conn,
                "SELECT dimension_scores FROM answers WHERE user_id = %s "
                "AND dimension_scores IS NOT NULL AND dimension_scores != '{}' AND dimension_scores != '' "
                "ORDER BY created_at DESC LIMIT 10",
                (user_id,)
            ).fetchall()

            dim_agg = {}
            dim_count = {}
            for ans in last_answers:
                raw = ans.get("dimension_scores", "{}")
                dims = {}
                if isinstance(raw, str) and raw.strip():
                    try:
                        dims = json.loads(raw)
                    except json.JSONDecodeError:
                        dims = {}
                elif isinstance(raw, dict):
                    dims = raw
                for k, v in dims.items():
                    if isinstance(v, (int, float)):
                        dim_agg.setdefault(k, 0)
                        dim_agg[k] += v
                        dim_count.setdefault(k, 0)
                        dim_count[k] += 1

            dimensions = []
            # 固定维度顺序
            dim_order = ["流利度", "词汇", "语法", "发音"]
            for name in dim_order:
                if name in dim_agg:
                    avg = round(dim_agg[name] / dim_count[name], 1) if dim_count.get(name) else 0
                    dimensions.append({"name": name, "score": avg, "max_score": 100})
            # 补充不在固定顺序中的维度
            for name in sorted(dim_agg.keys()):
                if name not in dim_order:
                    avg = round(dim_agg[name] / dim_count[name], 1) if dim_count.get(name) else 0
                    dimensions.append({"name": name, "score": avg, "max_score": 100})

            # 6. 最新 3 枚徽章
            badges = self._execute(conn,
                """SELECT b.id, b.name, b.description, b.icon, b.rarity, ub.unlocked_at
                   FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
                   WHERE ub.user_id = %s ORDER BY ub.unlocked_at DESC LIMIT 3""",
                (user_id,)
            ).fetchall()

            return {
                "total_seconds": total_seconds,
                "total_practices": total_practices,
                "streak_days": streak,
                "dimensions": dimensions,
                "recent_scores": [
                    {"score": r["score"], "date": r["created_at"]}
                    for r in reversed(recent_scores)
                ],
                "badges": badges,
            }
        finally:
            self._release_conn(conn)

    def get_user_streak(self, user_id: str) -> int:
        """
        计算用户当前连续练习天数

        从 answers.created_at 获取所有练习日期（去重），
        从最近日期开始倒序计算连续天数。
        """
        conn = self._get_conn()
        try:
            rows = self._execute(conn,
                "SELECT DISTINCT DATE(created_at) as practice_date "
                "FROM answers WHERE user_id = %s ORDER BY practice_date DESC",
                (user_id,)
            ).fetchall()

            if not rows:
                return 0

            from datetime import datetime, timedelta
            streak = 0
            today = datetime.now().date()

            for i, row in enumerate(rows):
                try:
                    d = datetime.strptime(row["practice_date"], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    continue

                if i == 0:
                    # 检查最近练习日期是否在今天或昨天（连续才计数）
                    if (today - d).days > 1:
                        return 0
                    streak = 1
                else:
                    prev = datetime.strptime(rows[i - 1]["practice_date"], "%Y-%m-%d").date()
                    if (prev - d).days == 1:
                        streak += 1
                    else:
                        break

            return streak
        finally:
            self._release_conn(conn)

    # ==================== 面经数据 ====================

    def save_interview_experience(self, data: dict) -> int:
        """保存一篇面经"""
        conn = self._get_conn()
        try:
            cur = self._execute(conn,
                """INSERT INTO interview_experiences
                   (company_name, position, round, questions, content, publish_date, source_url)
                   VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (data["company_name"], data.get("position", ""),
                 data.get("round", ""), json.dumps(data.get("questions", []), ensure_ascii=False),
                 data.get("content", ""), data.get("publish_date", ""),
                 data.get("source_url", ""))
            )
            row = cur.fetchone()
            conn.commit()
            return row["id"]
        finally:
            self._release_conn(conn)

    def experience_exists(self, source_url: str) -> bool:
        """检查面经是否已存在（避免重复）"""
        conn = self._get_conn()
        try:
            row = self._execute(conn,
                "SELECT 1 FROM interview_experiences WHERE source_url = %s",
                (source_url,)
            ).fetchone()
            return row is not None
        finally:
            self._release_conn(conn)

    def search_interview_experiences(self, company: str = "", position: str = "",
                                     limit: int = 10) -> list:
        """搜索面经，按公司+岗位模糊匹配"""
        conn = self._get_conn()
        try:
            sql = "SELECT * FROM interview_experiences WHERE 1=1"
            params = []
            if company:
                sql += " AND company_name LIKE %s"
                params.append(f"%{company}%")
            if position:
                sql += " AND position LIKE %s"
                params.append(f"%{position}%")
            sql += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            rows = self._execute(conn,sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("questions"), str):
                    r["questions"] = json.loads(r["questions"])
            return rows
        finally:
            self._release_conn(conn)

    # ==================== 工具方法 ====================

    def seed_default_data(self) -> None:
        """填充默认数据（场景 + 题库 + 徽章）"""
        if self.use_pg:
            from src.core.database.pg_seed import seed_all_pg
            seed_all_pg(self)
        else:
            from src.core.database.seed import seed_scenarios, seed_questions, seed_badges
            seed_scenarios(self)
            seed_questions(self)
            seed_badges(self)
            print(f"[DB] 默认数据填充完成")


# 全局单例
default_manager = DatabaseManager()
