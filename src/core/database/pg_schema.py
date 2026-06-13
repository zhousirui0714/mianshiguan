"""
PostgreSQL 建表 DDL（Supabase / PostgreSQL）

与 SQLite 版本的主要差异：
1. TEXT PRIMARY KEY → TEXT PRIMARY KEY（不变）
2. AUTOINCREMENT → SERIAL（仅 interview_experiences）
3. datetime('now') → NOW()
4. 移除 PRAGMA（PG 不需要）
5. CHECK 约束（PG 原生支持）
6. 时间戳列保持 TEXT 类型（兼容现有 datetime.now().isoformat() 调用）
"""

CREATE_TABLES_PG = """
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    avatar TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT NOW()
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
    created_at TEXT NOT NULL DEFAULT NOW()
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
    question_level TEXT DEFAULT 'C',
    interview_stage TEXT DEFAULT 'basic',
    topics TEXT DEFAULT '[]',
    year TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT NOW(),
    updated_at TEXT NOT NULL DEFAULT NOW()
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
    created_at TEXT NOT NULL DEFAULT NOW(),
    updated_at TEXT NOT NULL DEFAULT NOW()
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
    created_at TEXT NOT NULL DEFAULT NOW()
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
    created_at TEXT NOT NULL DEFAULT NOW()
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
    created_at TEXT NOT NULL DEFAULT NOW(),
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
    created_at TEXT NOT NULL DEFAULT NOW()
);

-- 用户-徽章关联表
CREATE TABLE IF NOT EXISTS user_badges (
    user_id TEXT NOT NULL REFERENCES users(id),
    badge_id TEXT NOT NULL REFERENCES badges(id),
    unlocked_at TEXT NOT NULL DEFAULT NOW(),
    is_new INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, badge_id)
);
CREATE INDEX IF NOT EXISTS idx_user_badges_user ON user_badges(user_id);

-- 面经表（爬虫数据）
CREATE TABLE IF NOT EXISTS interview_experiences (
    id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    position TEXT DEFAULT '',
    round TEXT DEFAULT '',
    questions TEXT DEFAULT '[]',
    content TEXT DEFAULT '',
    publish_date TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_exp_company ON interview_experiences(company_name);
CREATE INDEX IF NOT EXISTS idx_exp_position ON interview_experiences(position);
"""
