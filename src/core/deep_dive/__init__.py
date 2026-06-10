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
from typing import List, Optional, Dict, Any

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "deep_dive_topics.json")

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
    def initialize(context: dict, keyword: str) -> dict:
        """
        初始化深挖模式：
        1. 从配置获取 topic 信息
        2. 从 retrieved_questions 筛选候选题目
        3. 存入 context.deep_dive
        """
        topic_key = DeepDiveManager.keyword_to_topic(keyword)
        config = DeepDiveManager.load_config()
        topic_config = config.get(topic_key, {})

        display_name = topic_config.get("display_name", keyword)
        related_topics = topic_config.get("related_topics", [])
        max_depth = topic_config.get("max_depth", 3)

        # 从 retrieved_questions 筛选 topic 匹配的题目
        candidates = DeepDiveManager._filter_candidates(
            context.get("retrieved_questions", []),
            related_topics,
        )

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

            if isinstance(q_topics, list):
                match = any(rt in qt for rt in related_topics for qt in q_topics)

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

        for c in candidates:
            cid = c.get("id", "")
            text = c.get("question_text", "")
            if cid and cid not in asked_ids and text and text not in used:
                asked_ids.add(cid)
                deep_dive["asked_ids"] = list(asked_ids)
                deep_dive["depth"] = deep_dive.get("depth", 0) + 1

                context.setdefault("used_questions", []).append(text)

                print(f"[DeepDiveManager] 深挖出题 [{deep_dive['depth']}/{deep_dive['max_depth']}]: "
                      f"{text[:60]}...")
                return c

        print(f"[DeepDiveManager] 候选题目已用完，自动结束深挖")
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
