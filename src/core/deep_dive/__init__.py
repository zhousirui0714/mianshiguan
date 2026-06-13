"""
DeepDiveManager — 项目深挖管理器

管理 5 个主题（Redis/MySQL/Kafka/Agent/RAG）的多轮追问生命周期：
- 初始化深挖会话
- 从 retrieved_questions 筛选 topic 级题目
- 按 S/A/B/C 优先级选题
- 支持用户主动退出
- 深挖结束后自动恢复常规流程
"""

import json
import os
import sqlite3
from typing import List, Optional, Dict, Any

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "deep_dive_topics.json")
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "../../../data/interview.db")
_DEBUG_LOG = r"D:\zhousirui\新建文件夹 (2)\mianshiguan\debug_audit.log"
def _debug(msg: str):
    with open(_DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
        f.flush()

_KEYWORD_TO_TOPIC = {
    "redis": "redis",
    "mysql": "mysql",
    "kafka": "kafka",
    "rag": "rag",
    "agent": "agent",
}


class DeepDiveManager:
    """项目深挖管理器（纯静态方法，无 DB 依赖）"""

    @staticmethod
    def load_config() -> dict:
        """加载深挖主题配置"""
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[DeepDiveManager] 加载配置失败: {e}")
            return {}

    @staticmethod
    def keyword_to_topic(keyword: str) -> Optional[str]:
        """将检测到的关键词映射为配置中的 topic key"""
        return _KEYWORD_TO_TOPIC.get(keyword.lower())

    @staticmethod
    def should_enter(keyword: str, context: dict) -> bool:
        """
        检查是否应该进入深挖模式：
        1. keyword 有对应的配置
        2. 当前不在深挖中
        """
        topic_key = DeepDiveManager.keyword_to_topic(keyword)
        if not topic_key:
            return False

        config = DeepDiveManager.load_config()
        if topic_key not in config:
            return False

        deep_dive = context.get("deep_dive", {})
        if deep_dive.get("active"):
            return False

        return True

    @staticmethod
    def initialize(context: dict, keyword: str, cid: str = "????") -> dict:
        """
        初始化深挖模式：
        1. 从配置获取 topic 信息
        2. 从 retrieved_questions 筛选候选题目
        3. 存入 context.deep_dive
        """
        topic_key = DeepDiveManager.keyword_to_topic(keyword)
        config = DeepDiveManager.load_config()
        topic_config = config.get(topic_key, {})
        context["_cid"] = cid

        display_name = topic_config.get("display_name", keyword)
        related_topics = topic_config.get("related_topics", [])
        max_depth = topic_config.get("max_depth", 3)

        # 从 retrieved_questions 筛选 topic 匹配的题目
        retrieved = context.get("retrieved_questions", [])
        _debug(f"[DEBUG][{cid}] DeepDive.initialize: topic={topic_key} "
              f"related={related_topics} retrieved_count={len(retrieved)}")
        # 打印前5道题排查问题
        for i, q in enumerate(retrieved[:5]):
            t = q.get("question_text", "")
            tp = q.get("topics", "")
            _debug(f"[DEBUG][{cid}] DeepDive.initialize: retrieved[{i}] text={t[:50]} topics={str(tp)[:60]}")

        candidates = DeepDiveManager._filter_candidates(
            retrieved,
            related_topics,
        )

        # DB 兜底：retrieved_questions 中没有足够 topic 题时，直接从 DB 查询
        if len(candidates) < max_depth:
            db_candidates = DeepDiveManager._fetch_db_topic_questions(
                topic_key, cid
            )
            _debug(f"[DEBUG][{cid}] DeepDive.initialize: DB兜底查询到 {len(db_candidates)} 题")
            existing_ids = {c["id"] for c in candidates if c["id"]}
            for q in db_candidates:
                if q["id"] and q["id"] not in existing_ids:
                    candidates.append(q)
                    existing_ids.add(q["id"])

            # 重新排序
            level_order = {"S": 0, "A": 1, "B": 2, "C": 3}
            candidates.sort(key=lambda x: level_order.get(x.get("level", "C"), 99))

        _debug(f"[DEBUG][{cid}] DeepDive.initialize: 最终候选 {len(candidates)} 题")

        context["deep_dive"] = {
            "active": True,
            "topic": topic_key,
            "display_name": display_name,
            "depth": 0,
            "max_depth": max_depth,
            "asked_ids": [],
            "exited": False,
            "candidates": candidates,
        }

        print(f"[DeepDiveManager] 进入深挖: {display_name}, "
              f"候选 {len(candidates)} 题, 计划 {max_depth} 轮")
        _debug(f"[DEBUG][{cid}] DeepDive.initialize -> 完成: 候选{len(candidates)}题, max_depth={max_depth}")
        return context

    @staticmethod
    def _filter_candidates(retrieved: List[dict],
                           related_topics: List[str]) -> List[Dict[str, Any]]:
        """
        从 retrieved_questions 中筛选 topic 匹配的题目。
        先用 topics 字段匹配，若候选不足则用问题文本关键词匹配作为兜底。
        """
        candidates = []
        seen_texts = set()
        level_order = {"S": 0, "A": 1, "B": 2, "C": 3}

        for q in retrieved:
            text = q.get("question_text", "")
            if not text or text in seen_texts:
                continue

            # 检查 topics 字段是否匹配
            match = False
            q_topics = q.get("topics", "")
            if isinstance(q_topics, str):
                try:
                    q_topics = json.loads(q_topics)
                except (json.JSONDecodeError, TypeError):
                    q_topics = []

            if not match and isinstance(q_topics, list):
                match = any(rt in qt for rt in related_topics for qt in q_topics)
                if match:
                    _debug(f"[FILTER] 话题匹配命中: text={text[:40]} topics={q_topics} related={related_topics}")

            # 兜底：文本关键词匹配（topics 字段未命中但问题文本包含相关关键词）
            if not match:
                text_lower = text.lower()
                for rt in related_topics:
                    if rt.lower() in text_lower:
                        match = True
                        _debug(f"[FILTER] 文本兜底命中: text={text[:40]} keyword={rt}")
                        break
                if not match:
                    continue

            seen_texts.add(text)
            lev = (q.get("question_level") or "C").strip().upper()
            if lev not in ("S", "A", "B", "C"):
                lev = "C"

            candidates.append({
                "id": q.get("id", ""),
                "question_text": text,
                "question_level": lev,
                "interview_stage": q.get("interview_stage", "basic"),
                "level": lev,
            })

        # 按 S/A/B/C 排序
        candidates.sort(key=lambda x: level_order.get(x.get("level", "C"), 99))
        return candidates[:15]

    @staticmethod
    def _fetch_db_topic_questions(topic_key: str,
                                   cid: str = "????") -> List[Dict[str, Any]]:
        """从 DB 查询指定 topic 的题目（兜底用）

        优先使用注入的 db_query_func（支持 PostgreSQL），
        回退到直接 sqlite3 读取（兼容旧版）。
        """
        topic_display = topic_key.capitalize()

        # 优先使用注入的查询函数（支持 PG）
        db_func = getattr(DeepDiveManager, 'db_query_func', None)
        if db_func is not None:
            try:
                # 使用 LIKE 宽泛搜索 topics 字段
                all_qs = db_func()
                keyword = topic_display.lower()
                result = []
                for q in all_qs:
                    topics = q.get('topics', '')
                    if isinstance(topics, str):
                        topics = json.loads(topics) if topics else []
                    if not isinstance(topics, list):
                        topics = []
                    # 匹配 topic 名称
                    if keyword in json.dumps(topics).lower() or keyword in (q.get('category', '') or '').lower():
                        lev = (q.get("question_level") or "C").strip().upper()
                        if lev not in ("S", "A", "B", "C"):
                            lev = "C"
                        result.append({
                            "id": q["id"],
                            "question_text": q["question_text"],
                            "question_level": lev,
                            "interview_stage": q.get("interview_stage") or "basic",
                            "level": lev,
                        })
                    if len(result) >= 15:
                        break
                _debug(f"[DEBUG][{cid}] _fetch_db_topic_questions (注入): "
                      f"topic={topic_display} 查到{len(result)}题")
                return result
            except Exception as e:
                _debug(f"[DEBUG][{cid}] _fetch_db_topic_questions 注入查询异常: {e}")

        # 回退：直接 sqlite3 读取
        db_path = os.path.abspath(_DB_PATH)
        if not os.path.exists(db_path):
            _debug(f"[DEBUG][{cid}] _fetch_db_topic_questions: DB不存在 {db_path}")
            return []

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.execute("""
                SELECT id, question_text, question_level, interview_stage
                FROM questions
                WHERE topics LIKE ?
                ORDER BY
                    CASE question_level WHEN 'S' THEN 0 WHEN 'A' THEN 1 WHEN 'B' THEN 2 ELSE 3 END
                LIMIT 15
            """, (f'%{topic_display}%',))
            rows = cur.fetchall()
            conn.close()

            result = []
            for r in rows:
                lev = (r["question_level"] or "C").strip().upper()
                if lev not in ("S", "A", "B", "C"):
                    lev = "C"
                result.append({
                    "id": r["id"],
                    "question_text": r["question_text"],
                    "question_level": lev,
                    "interview_stage": r["interview_stage"] or "basic",
                    "level": lev,
                })
            _debug(f"[DEBUG][{cid}] _fetch_db_topic_questions: "
                  f"topic={topic_display} 查到{len(result)}题")
            return result
        except Exception as e:
            _debug(f"[DEBUG][{cid}] _fetch_db_topic_questions 异常: {e}")
            return []

    @staticmethod
    def select_question(context: dict) -> Optional[Dict[str, Any]]:
        """
        从候选列表中选取下一个题目：
        1. 按 S/A/B/C 优先级选取未使用题目
        2. 更新 depth 和 asked_ids
        3. 返回题目 dict 或 None（无可用题目时）
        """
        deep_dive = context.get("deep_dive", {})
        if not deep_dive.get("active") or deep_dive.get("exited"):
            return None

        candidates = deep_dive.get("candidates", [])
        asked_ids = set(deep_dive.get("asked_ids", []))
        used = set(context.get("used_questions", []))

        topic = deep_dive.get("topic", "?")
        # Try to get conversation_id from context (injected upstream)
        cid = context.get("_cid", "????")

        _debug(f"[DEBUG][{cid}] DeepDive.select_question: topic={topic} "
              f"candidates={len(candidates)} asked_ids={len(asked_ids)} used={len(used)} "
              f"depth={deep_dive.get('depth',0)}/{deep_dive.get('max_depth',3)}")

        for c in candidates:
            cid_q = c.get("id", "")
            text = c.get("question_text", "")
            if cid_q and cid_q not in asked_ids and text and text not in used:
                asked_ids.add(cid_q)
                deep_dive["asked_ids"] = list(asked_ids)
                deep_dive["depth"] = deep_dive.get("depth", 0) + 1

                context.setdefault("used_questions", []).append(text)

                _debug(f"[DEBUG][{cid}] DeepDive.select_question -> 命中: "
                      f"[{c.get('level','?')}] {text[:60]}")
                _debug(f"[DEBUG][{cid}] DeepDive.select_question: question_id={cid_q}")
                return c

        _debug(f"[DEBUG][{cid}] DeepDive.select_question -> 无可用候选，自动结束深挖")
        deep_dive["active"] = False
        return None

    @staticmethod
    def should_continue(context: dict) -> bool:
        """检查深挖是否应继续"""
        deep_dive = context.get("deep_dive", {})
        if not deep_dive.get("active"):
            return False
        if deep_dive.get("exited"):
            return False
        if deep_dive.get("depth", 0) >= deep_dive.get("max_depth", 3):
            return False
        # 检查是否还有未用题目
        candidates = deep_dive.get("candidates", [])
        asked_ids = set(deep_dive.get("asked_ids", []))
        remaining = any(c.get("id", "") not in asked_ids
                        and c.get("question_text", "")
                        for c in candidates)
        return remaining

    @staticmethod
    def check_exit(user_message: str, topic_config: dict) -> bool:
        """检查用户消息是否包含退出关键词"""
        exit_keywords = topic_config.get("exit_keywords", [])
        msg_lower = user_message.lower()
        for kw in exit_keywords:
            if kw.lower() in msg_lower:
                return True
        return False

    @staticmethod
    def exit(context: dict) -> dict:
        """退出深挖模式"""
        deep_dive = context.get("deep_dive", {})
        if deep_dive:
            deep_dive["active"] = False
            deep_dive["exited"] = True
            print(f"[DeepDiveManager] 用户主动退出深挖: {deep_dive.get('display_name', '')}")
        return context
