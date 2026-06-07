"""
数据库核心模块

提供：
- DatabaseManager: 基于 SQLite 的完整数据库操作
- 支持复杂关联查询
- 自动建表和迁移
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from src.core.database.models import CREATE_TABLES_SQL, dict_factory

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
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        # 确保 data 目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        """初始化数据库表"""
        conn = self._get_conn()
        try:
            # [迁移优先] 先加列再建索引，避免 CREATE INDEX 引用不存在的列报错
            try:
                conn.execute("ALTER TABLE conversations ADD COLUMN report_data TEXT DEFAULT '{}'")
                conn.commit()
            except sqlite3.OperationalError:
                pass
            for col in ['company TEXT', 'position TEXT', 'source TEXT', 'year TEXT']:
                try:
                    conn.execute(f"ALTER TABLE questions ADD COLUMN {col}")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass

            conn.executescript(CREATE_TABLES_SQL)
            conn.commit()
        finally:
            conn.close()

    # ==================== 用户管理 ====================

    def create_user(self, username: str, email: str, password_hash: str,
                    user_id: str = None) -> dict:
        conn = self._get_conn()
        try:
            user_id = user_id or str(uuid.uuid4())
            conn.execute(
                "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
                (user_id, username, email, password_hash)
            )
            conn.commit()
            return {"success": True, "user_id": user_id}
        except sqlite3.IntegrityError:
            return {"success": False, "error": "邮箱已存在"}
        finally:
            conn.close()

    def get_user(self, user_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        finally:
            conn.close()

    # ==================== 场景管理 ====================

    def create_scenario(self, scenario_id: str, name: str, category: str = "",
                        description: str = "", max_rounds: int = 5,
                        config_json: dict = None) -> dict:
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO scenarios (id, name, category, description, max_rounds, config_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (scenario_id, name, category, description, max_rounds,
                 json.dumps(config_json or {}, ensure_ascii=False))
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def get_scenario(self, scenario_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
            if row and row.get("config_json"):
                row["config"] = json.loads(row["config_json"])
            return row
        finally:
            conn.close()

    def get_all_scenarios(self) -> List[dict]:
        conn = self._get_conn()
        try:
            return conn.execute(
                "SELECT * FROM scenarios WHERE enabled = 1 ORDER BY name"
            ).fetchall()
        finally:
            conn.close()

    # ==================== 题库管理 ====================

    def add_question(self, scenario_id: str, category: str, difficulty: int,
                     question_text: str, reference_answer: str, tags: List[str] = None,
                     company: str = "", position: str = "", source: str = "",
                     year: str = "") -> dict:
        conn = self._get_conn()
        try:
            # 检查是否已存在相同问题
            existing = conn.execute(
                "SELECT id FROM questions WHERE scenario_id = ? AND question_text = ?",
                (scenario_id, question_text)
            ).fetchone()
            if existing:
                return {"success": True, "question_id": existing["id"]}

            qid = f"q_{uuid.uuid4().hex[:8]}"
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT INTO questions (id, scenario_id, category, difficulty, "
                "question_text, reference_answer, tags, company, position, "
                "source, year, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (qid, scenario_id, category, difficulty, question_text, reference_answer,
                 json.dumps(tags or [], ensure_ascii=False), company, position,
                 source, year, now, now)
            )
            conn.commit()
            return {"success": True, "question_id": qid}
        finally:
            conn.close()

    def get_questions(self, scenario_id: str = None, category: str = None,
                      difficulty: int = None, keyword: str = None,
                      company: str = None, position: str = None) -> List[dict]:
        conn = self._get_conn()
        try:
            sql = "SELECT * FROM questions WHERE 1=1"
            params = []
            if scenario_id:
                sql += " AND scenario_id = ?"
                params.append(scenario_id)
            if category:
                sql += " AND category = ?"
                params.append(category)
            if difficulty:
                sql += " AND difficulty = ?"
                params.append(difficulty)
            if keyword:
                sql += " AND (question_text LIKE ? OR reference_answer LIKE ?)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if company:
                sql += " AND company LIKE ?"
                params.append(f"%{company}%")
            if position:
                sql += " AND position LIKE ?"
                params.append(f"%{position}%")
            sql += " ORDER BY year DESC, created_at DESC"
            rows = conn.execute(sql, params).fetchall()
            # 解析 tags JSON
            for r in rows:
                if isinstance(r.get("tags"), str):
                    r["tags"] = json.loads(r["tags"])
            return rows
        finally:
            conn.close()

    def get_question(self, question_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM questions WHERE id = ?", (question_id,)
            ).fetchone()
            if row and isinstance(row.get("tags"), str):
                row["tags"] = json.loads(row["tags"])
            return row
        finally:
            conn.close()

    def update_question(self, question_id: str, **kwargs) -> dict:
        conn = self._get_conn()
        try:
            existing = conn.execute(
                "SELECT id FROM questions WHERE id = ?", (question_id,)
            ).fetchone()
            if not existing:
                return {"success": False, "error": "题目不存在"}

            allowed = ["scenario_id", "category", "difficulty",
                       "question_text", "reference_answer", "tags",
                       "company", "position", "source", "year"]
            updates = {}
            for k, v in kwargs.items():
                if k in allowed:
                    updates[k] = v
            if not updates:
                return {"success": True}

            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values())
            if "tags" in updates:
                idx = list(updates.keys()).index("tags")
                values[idx] = json.dumps(values[idx], ensure_ascii=False)

            now = datetime.now().isoformat()
            conn.execute(
                f"UPDATE questions SET {set_clause}, updated_at = ? WHERE id = ?",
                values + [now, question_id]
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def delete_question(self, question_id: str) -> dict:
        conn = self._get_conn()
        try:
            existing = conn.execute(
                "SELECT id FROM questions WHERE id = ?", (question_id,)
            ).fetchone()
            if not existing:
                return {"success": False, "error": "题目不存在"}
            conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def get_categories(self, scenario_id: str = None) -> List[str]:
        conn = self._get_conn()
        try:
            sql = "SELECT DISTINCT category FROM questions WHERE 1=1"
            params = []
            if scenario_id:
                sql += " AND scenario_id = ?"
                params.append(scenario_id)
            sql += " ORDER BY category"
            return [r["category"] for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()

    def get_tags(self, scenario_id: str = None) -> List[str]:
        conn = self._get_conn()
        try:
            sql = "SELECT tags FROM questions WHERE 1=1"
            params = []
            if scenario_id:
                sql += " AND scenario_id = ?"
                params.append(scenario_id)
            rows = conn.execute(sql, params).fetchall()
            tags = set()
            for r in rows:
                tag_list = json.loads(r["tags"]) if isinstance(r["tags"], str) else (r["tags"] or [])
                tags.update(tag_list)
            return sorted(tags)
        finally:
            conn.close()

    # ==================== 对话管理 ====================

    def create_conversation(self, user_id: str, scenario_id: str,
                            scenario_name: str = "", user_background: str = "",
                            conversation_id: str = None) -> dict:
        conn = self._get_conn()
        try:
            conv_id = conversation_id or str(uuid.uuid4())
            now = datetime.now().isoformat()
            # 自动创建用户（同一连接 + 事务，避免 FK 约束问题）
            existing_user = conn.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if not existing_user:
                conn.execute(
                    "INSERT OR IGNORE INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
                    (user_id, f"用户{user_id}", f"{user_id}@example.com", "auto")
                )
            conn.execute(
                "INSERT INTO conversations (id, user_id, scenario_id, scenario_name, "
                "user_background, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (conv_id, user_id, scenario_id, scenario_name, user_background, now, now)
            )
            conn.commit()
            return {"success": True, "conversation_id": conv_id}
        except sqlite3.IntegrityError as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if row:
                row["messages"] = self._get_messages(conn, conversation_id)
            return row
        finally:
            conn.close()

    def update_conversation_status(self, conversation_id: str, status: str) -> dict:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            conn.execute(
                "UPDATE conversations SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, conversation_id)
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def update_conversation_report(self, conversation_id: str, report_data: dict) -> dict:
        """保存面试报告数据到 conversations 表"""
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            conn.execute(
                "UPDATE conversations SET report_data = ?, updated_at = ? WHERE id = ?",
                (json.dumps(report_data, ensure_ascii=False), now, conversation_id)
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def get_user_conversations(self, user_id: str) -> List[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            ).fetchall()
            for row in rows:
                row["messages"] = self._get_messages(conn, row["id"])
            return rows
        finally:
            conn.close()

    def increment_conversation_round(self, conversation_id: str) -> None:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            conn.execute(
                "UPDATE conversations SET round_count = round_count + 1, updated_at = ? WHERE id = ?",
                (now, conversation_id)
            )
            conn.commit()
        finally:
            conn.close()

    def add_message(self, conversation_id: str, role: str, content: str) -> dict:
        conn = self._get_conn()
        try:
            mid = str(uuid.uuid4())
            # 获取当前最大序号
            max_order = conn.execute(
                "SELECT COALESCE(MAX(msg_order), 0) FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchone()["COALESCE(MAX(msg_order), 0)"]
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, msg_order, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (mid, conversation_id, role, content, max_order + 1, now)
            )
            conn.commit()
            if role == "assistant":
                self.increment_conversation_round(conversation_id)
            return {"success": True, "message_id": mid}
        finally:
            conn.close()

    def _get_messages(self, conn: sqlite3.Connection, conversation_id: str) -> List[dict]:
        return conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY msg_order",
            (conversation_id,)
        ).fetchall()

    # ==================== 答题管理 ====================

    def add_answer(self, user_id: str, conversation_id: str, question_id: Optional[str],
                   round_num: int, question_text: str, answer_text: str,
                   score: float = None, dimension_scores: dict = None,
                   feedback: str = "", duration: int = 0) -> dict:
        conn = self._get_conn()
        try:
            aid = str(uuid.uuid4())
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT INTO answers (id, user_id, conversation_id, question_id, round, "
                "question_text, answer_text, score, dimension_scores, feedback, duration, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, user_id, conversation_id, question_id, round_num,
                 question_text, answer_text, score,
                 json.dumps(dimension_scores or {}, ensure_ascii=False),
                 feedback, duration, now)
            )
            conn.commit()
            return {"success": True, "answer_id": aid}
        finally:
            conn.close()

    def get_conversation_answers(self, conversation_id: str) -> List[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM answers WHERE conversation_id = ? ORDER BY round",
                (conversation_id,)
            ).fetchall()
            for r in rows:
                if isinstance(r.get("dimension_scores"), str):
                    r["dimension_scores"] = json.loads(r["dimension_scores"])
            return rows
        finally:
            conn.close()

    def get_conversation_result(self, conversation_id: str) -> Optional[dict]:
        """获取面试结果数据（含答案聚合 + 报告 + 排名）"""
        conn = self._get_conn()
        try:
            # 1. 获取会话基本信息
            conv = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if not conv:
                return None

            # 2. 获取该会话的所有答题记录
            answers = conn.execute(
                "SELECT * FROM answers WHERE conversation_id = ? ORDER BY round",
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
            all_avgs = conn.execute(
                "SELECT avg_score FROM progress WHERE scenario_id = ? AND avg_score IS NOT NULL",
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
                    badge_rows = conn.execute(
                        """SELECT b.id, b.name, b.description, b.icon, b.rarity
                           FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
                           WHERE ub.user_id = ? AND ub.unlocked_at >= ?
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
            conn.close()

    def get_user_answers(self, user_id: str, scenario_id: str = None,
                         limit: int = 50) -> List[dict]:
        """获取用户答题记录（支持按场景筛选）"""
        conn = self._get_conn()
        try:
            sql = ("SELECT a.*, c.scenario_id FROM answers a "
                   "JOIN conversations c ON a.conversation_id = c.id "
                   "WHERE a.user_id = ?")
            params = [user_id]
            if scenario_id:
                sql += " AND c.scenario_id = ?"
                params.append(scenario_id)
            sql += " ORDER BY a.created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("dimension_scores"), str):
                    r["dimension_scores"] = json.loads(r["dimension_scores"])
            return rows
        finally:
            conn.close()

    # ==================== 成长档案 ====================

    def update_progress(self, user_id: str, scenario_id: str, score: float) -> dict:
        """更新用户在某场景的成长档案"""
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            existing = conn.execute(
                "SELECT * FROM progress WHERE user_id = ? AND scenario_id = ?",
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

                conn.execute(
                    "UPDATE progress SET total_practices = ?, total_answers = total_answers + 1, "
                    "avg_score = ?, max_score = ?, latest_scores = ?, last_practiced_at = ? "
                    "WHERE user_id = ? AND scenario_id = ?",
                    (new_total, round(new_avg, 1), new_max,
                     json.dumps(latest, ensure_ascii=False), now, user_id, scenario_id)
                )
            else:
                # 新建
                pid = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO progress (id, user_id, scenario_id, total_practices, total_answers, "
                    "avg_score, max_score, latest_scores, last_practiced_at, created_at) "
                    "VALUES (?, ?, ?, 1, 1, ?, ?, ?, ?, ?)",
                    (pid, user_id, scenario_id, round(score, 1), score,
                     json.dumps([score], ensure_ascii=False), now, now)
                )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def get_user_progress(self, user_id: str, scenario_id: str = None) -> List[dict]:
        """获取用户成长档案（支持按场景筛选）"""
        conn = self._get_conn()
        try:
            sql = ("SELECT p.*, s.name as scenario_name, s.category FROM progress p "
                   "JOIN scenarios s ON p.scenario_id = s.id WHERE p.user_id = ?")
            params = [user_id]
            if scenario_id:
                sql += " AND p.scenario_id = ?"
                params.append(scenario_id)
            sql += " ORDER BY s.name"
            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("latest_scores"), str):
                    r["latest_scores"] = json.loads(r["latest_scores"])
            return rows
        finally:
            conn.close()

    # ==================== 徽章管理 ====================

    def add_badge(self, badge_id: str, name: str, description: str, icon: str = "🎯",
                  category: str = "common", unlock_condition: dict = None,
                  rarity: str = "common") -> dict:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT OR IGNORE INTO badges (id, name, description, icon, category, unlock_condition, rarity, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (badge_id, name, description, icon, category,
                 json.dumps(unlock_condition or {}, ensure_ascii=False), rarity, now)
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def get_all_badges(self) -> List[dict]:
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT * FROM badges ORDER BY category, name").fetchall()
            for r in rows:
                if isinstance(r.get("unlock_condition"), str):
                    r["unlock_condition"] = json.loads(r["unlock_condition"])
            return rows
        finally:
            conn.close()

    def unlock_user_badge(self, user_id: str, badge_id: str) -> dict:
        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            conn.execute(
                "INSERT OR IGNORE INTO user_badges (user_id, badge_id, unlocked_at, is_new) "
                "VALUES (?, ?, ?, 1)",
                (user_id, badge_id, now)
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

    def get_user_badges(self, user_id: str) -> List[dict]:
        """获取用户已解锁的徽章（含徽章详情）"""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT b.*, ub.unlocked_at, ub.is_new FROM user_badges ub "
                "JOIN badges b ON ub.badge_id = b.id "
                "WHERE ub.user_id = ? ORDER BY ub.unlocked_at DESC",
                (user_id,)
            ).fetchall()
            return rows
        finally:
            conn.close()

    def get_user_new_badge_count(self, user_id: str) -> int:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM user_badges WHERE user_id = ? AND is_new = 1",
                (user_id,)
            ).fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def mark_badge_viewed(self, user_id: str, badge_id: str) -> dict:
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE user_badges SET is_new = 0 WHERE user_id = ? AND badge_id = ?",
                (user_id, badge_id)
            )
            conn.commit()
            return {"success": True}
        finally:
            conn.close()

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
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            scenario = conn.execute(
                "SELECT * FROM scenarios WHERE id = ?", (scenario_id,)
            ).fetchone()
            progress = conn.execute(
                "SELECT * FROM progress WHERE user_id = ? AND scenario_id = ?",
                (user_id, scenario_id)
            ).fetchone()
            recent_answers = conn.execute(
                "SELECT a.* FROM answers a "
                "JOIN conversations c ON a.conversation_id = c.id "
                "WHERE a.user_id = ? AND c.scenario_id = ? "
                "ORDER BY a.created_at DESC LIMIT 10",
                (user_id, scenario_id)
            ).fetchall()
            conversations = conn.execute(
                "SELECT * FROM conversations WHERE user_id = ? AND scenario_id = ? "
                "ORDER BY created_at DESC LIMIT 5",
                (user_id, scenario_id)
            ).fetchall()
            # 该场景下获得的徽章
            badges = conn.execute(
                "SELECT b.*, ub.unlocked_at FROM user_badges ub "
                "JOIN badges b ON ub.badge_id = b.id "
                "WHERE ub.user_id = ? AND b.category = 'scenario'",
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
            conn.close()

    def get_scenario_leaderboard(self, scenario_id: str, limit: int = 10) -> List[dict]:
        """排行榜：某场景下用户按照平均分排序"""
        conn = self._get_conn()
        try:
            return conn.execute(
                "SELECT p.user_id, u.username, p.avg_score, p.total_practices, p.max_score "
                "FROM progress p JOIN users u ON p.user_id = u.id "
                "WHERE p.scenario_id = ? AND p.total_practices > 0 "
                "ORDER BY p.avg_score DESC LIMIT ?",
                (scenario_id, limit)
            ).fetchall()
        finally:
            conn.close()

    def get_scenario_statistics(self, scenario_id: str) -> dict:
        """场景统计信息"""
        conn = self._get_conn()
        try:
            total_users = conn.execute(
                "SELECT COUNT(DISTINCT user_id) as cnt FROM progress WHERE scenario_id = ? "
                "AND total_practices > 0", (scenario_id,)
            ).fetchone()["cnt"]

            avg_stats = conn.execute(
                "SELECT AVG(avg_score) as avg_all, AVG(max_score) as avg_max, "
                "SUM(total_practices) as total_practices FROM progress WHERE scenario_id = ?",
                (scenario_id,)
            ).fetchone()

            total_questions = conn.execute(
                "SELECT COUNT(*) as cnt FROM questions WHERE scenario_id = ?",
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
            conn.close()

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
                r["badge_id"] for r in conn.execute(
                    "SELECT badge_id FROM user_badges WHERE user_id = ?", (user_id,)
                ).fetchall()
            }

            progress = conn.execute(
                "SELECT * FROM progress WHERE user_id = ? AND scenario_id = ?",
                (user_id, scenario_id)
            ).fetchone() or {}

            all_badges = conn.execute("SELECT * FROM badges").fetchall()
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
                    completed = conn.execute(
                        "SELECT COUNT(DISTINCT scenario_id) as cnt FROM progress "
                        "WHERE user_id = ? AND total_practices > 0", (user_id,)
                    ).fetchone()["cnt"]
                    unlocked = completed >= 6
                elif cond_type == "streak":
                    unlocked = (progress.get("total_practices", 0) or 0) >= (condition.get("days", 3) or 3)

                if unlocked:
                    conn.execute(
                        "INSERT OR IGNORE INTO user_badges (user_id, badge_id, unlocked_at, is_new) "
                        "VALUES (?, ?, datetime('now'), 1)",
                        (user_id, badge["id"])
                    )
                    new_badges.append(badge)

            conn.commit()
            return new_badges
        finally:
            conn.close()

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
            total_row = conn.execute(
                "SELECT COALESCE(SUM(total_practices), 0) as total_practices, "
                "COALESCE(AVG(avg_score), 0) as avg_score, "
                "COUNT(DISTINCT scenario_id) as scenario_count "
                "FROM progress WHERE user_id = ? AND total_practices > 0",
                (user_id,)
            ).fetchone()

            # 徽章总数
            badge_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM user_badges WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            # 最近练习日期
            last_date_row = conn.execute(
                "SELECT MAX(created_at) as last_date FROM answers WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            # 分数分布：从 progress.latest_scores 提取所有分数
            progress_rows = conn.execute(
                "SELECT latest_scores FROM progress WHERE user_id = ? AND total_practices > 0",
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
            conn.close()

    def get_dimension_trend(self, user_id: str) -> List[dict]:
        """
        获取各维度得分趋势（用于折线图）

        从 answers 表的 dimension_scores JSON 中提取每个维度的分数，
        按时间排序返回扁平列表。

        返回：[{date, dimension_name, score, scenario_id}, ...]
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT a.created_at, a.dimension_scores, c.scenario_id "
                "FROM answers a "
                "JOIN conversations c ON a.conversation_id = c.id "
                "WHERE a.user_id = ? AND a.dimension_scores IS NOT NULL "
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
            conn.close()

    def get_user_dashboard_stats(self, user_id: str) -> dict:
        """获取首页看板统计数据"""
        conn = self._get_conn()
        try:
            # 1. 累计练习时长（秒）
            duration_row = conn.execute(
                "SELECT COALESCE(SUM(duration), 0) as total_seconds FROM answers WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            total_seconds = duration_row["total_seconds"] if duration_row else 0

            # 2. 完成模拟次数
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM conversations WHERE user_id = ? AND status = 'finished'",
                (user_id,)
            ).fetchone()
            total_practices = count_row["cnt"] if count_row else 0

            # 3. 连续练习天数
            streak = self.get_user_streak(user_id)

            # 4. 最近 7 次练习得分趋势
            recent_scores = conn.execute(
                "SELECT score, created_at FROM answers WHERE user_id = ? AND score IS NOT NULL "
                "ORDER BY created_at DESC LIMIT 7",
                (user_id,)
            ).fetchall()

            # 5. 维度平均分（最近 10 次练习）
            last_answers = conn.execute(
                "SELECT dimension_scores FROM answers WHERE user_id = ? "
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
            badges = conn.execute(
                """SELECT b.id, b.name, b.description, b.icon, b.rarity, ub.unlocked_at
                   FROM user_badges ub JOIN badges b ON ub.badge_id = b.id
                   WHERE ub.user_id = ? ORDER BY ub.unlocked_at DESC LIMIT 3""",
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
            conn.close()

    def get_user_streak(self, user_id: str) -> int:
        """
        计算用户当前连续练习天数

        从 answers.created_at 获取所有练习日期（去重），
        从最近日期开始倒序计算连续天数。
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT DISTINCT DATE(created_at) as practice_date "
                "FROM answers WHERE user_id = ? ORDER BY practice_date DESC",
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
            conn.close()

    # ==================== 面经数据 ====================

    def save_interview_experience(self, data: dict) -> int:
        """保存一篇面经"""
        conn = self._get_conn()
        try:
            cur = conn.execute(
                """INSERT INTO interview_experiences
                   (company_name, position, round, questions, content, publish_date, source_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (data["company_name"], data.get("position", ""),
                 data.get("round", ""), json.dumps(data.get("questions", []), ensure_ascii=False),
                 data.get("content", ""), data.get("publish_date", ""),
                 data.get("source_url", ""))
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def experience_exists(self, source_url: str) -> bool:
        """检查面经是否已存在（避免重复）"""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT 1 FROM interview_experiences WHERE source_url = ?",
                (source_url,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def search_interview_experiences(self, company: str = "", position: str = "",
                                     limit: int = 10) -> list:
        """搜索面经，按公司+岗位模糊匹配"""
        conn = self._get_conn()
        try:
            sql = "SELECT * FROM interview_experiences WHERE 1=1"
            params = []
            if company:
                sql += " AND company_name LIKE ?"
                params.append(f"%{company}%")
            if position:
                sql += " AND position LIKE ?"
                params.append(f"%{position}%")
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            for r in rows:
                if isinstance(r.get("questions"), str):
                    r["questions"] = json.loads(r["questions"])
            return rows
        finally:
            conn.close()

    # ==================== 工具方法 ====================

    def seed_default_data(self) -> None:
        """填充默认数据（场景 + 题库 + 徽章）"""
        from src.core.database.seed import seed_scenarios, seed_questions, seed_badges
        seed_scenarios(self)
        seed_questions(self)
        seed_badges(self)
        print(f"[DB] 默认数据填充完成")


# 全局单例
default_manager = DatabaseManager()
