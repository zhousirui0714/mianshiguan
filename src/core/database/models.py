"""数据库模型定义

数据模型：
- users: 用户表
- scenarios: 场景表
- questions: 题库表
- conversations: 对话/会话表
- messages: 消息记录表
- answers: 答题记录表
- progress: 成长档案表
- badges: 徽章定义表
- user_badges: 用户-徽章关联表

关联关系：
- users 1:N conversations, users 1:N answers, users 1:N progress
- scenarios 1:N questions, scenarios 1:N conversations, scenarios 1:N progress
- conversations 1:N messages, conversations 1:N answers
- users M:N badges (through user_badges)
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple


# ==================== 建表 DDL ====================

CREATE_TABLES_SQL = """
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 场景表
CREATE TABLE IF NOT EXISTS scenarios (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT DEFAULT '',
    description TEXT DEFAULT '',
    enabled INTEGER DEFAULT 1,
    max_rounds INTEGER DEFAULT 5,
    config_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 题库表
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL REFERENCES scenarios(id),
    category TEXT DEFAULT '',
    difficulty INTEGER DEFAULT 3,
    question_text TEXT NOT NULL,
    reference_answer TEXT DEFAULT '',
    tags TEXT DEFAULT '[]',
    company TEXT DEFAULT '',
    position TEXT DEFAULT '',
    source TEXT DEFAULT '',
    source_type TEXT DEFAULT 'ai_generated',
    year TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_questions_scenario ON questions(scenario_id);
CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_company ON questions(company);
CREATE INDEX IF NOT EXISTS idx_questions_position ON questions(position);

-- 对话/会话表
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    scenario_id TEXT NOT NULL REFERENCES scenarios(id),
    scenario_name TEXT DEFAULT '',
    status TEXT DEFAULT 'active',
    round_count INTEGER DEFAULT 0,
    user_background TEXT DEFAULT '',
    report_data TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_scenario ON conversations(scenario_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);

-- 消息记录表
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    msg_order INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

-- 答题记录表
CREATE TABLE IF NOT EXISTS answers (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    question_id TEXT REFERENCES questions(id),
    round INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    score REAL,
    dimension_scores TEXT DEFAULT '{}',
    feedback TEXT DEFAULT '',
    duration INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_answers_user ON answers(user_id);
CREATE INDEX IF NOT EXISTS idx_answers_conversation ON answers(conversation_id);
CREATE INDEX IF NOT EXISTS idx_answers_score ON answers(score);

-- 成长档案表
CREATE TABLE IF NOT EXISTS progress (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    scenario_id TEXT NOT NULL REFERENCES scenarios(id),
    total_practices INTEGER DEFAULT 0,
    total_answers INTEGER DEFAULT 0,
    avg_score REAL DEFAULT 0,
    max_score REAL DEFAULT 0,
    latest_scores TEXT DEFAULT '[]',
    last_practiced_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, scenario_id)
);
CREATE INDEX IF NOT EXISTS idx_progress_user ON progress(user_id);

-- 徽章定义表
CREATE TABLE IF NOT EXISTS badges (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    icon TEXT DEFAULT '🎯',
    category TEXT DEFAULT '',
    unlock_condition TEXT DEFAULT '{}',
    rarity TEXT DEFAULT 'common',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 用户-徽章关联表
CREATE TABLE IF NOT EXISTS user_badges (
    user_id TEXT NOT NULL REFERENCES users(id),
    badge_id TEXT NOT NULL REFERENCES badges(id),
    unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_new INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, badge_id)
);
CREATE INDEX IF NOT EXISTS idx_user_badges_user ON user_badges(user_id);

-- 面经表（爬虫数据）
CREATE TABLE IF NOT EXISTS interview_experiences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    position TEXT DEFAULT '',
    round TEXT DEFAULT '',
    questions TEXT DEFAULT '[]',
    content TEXT DEFAULT '',
    publish_date TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_exp_company ON interview_experiences(company_name);
CREATE INDEX IF NOT EXISTS idx_exp_position ON interview_experiences(position);
"""


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    """将 sqlite3 行转换为字典"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
