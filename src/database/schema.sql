-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    current_position VARCHAR(100),
    experience_years INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 面试记录表
CREATE TABLE interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company VARCHAR(200) NOT NULL,
    position VARCHAR(200) NOT NULL,
    jd_text TEXT,
    interview_date DATE,
    round VARCHAR(50) DEFAULT '初试',
    format VARCHAR(50) DEFAULT '视频',
    status VARCHAR(50) DEFAULT '准备中',
    result VARCHAR(50) DEFAULT '未填写',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 面试问题记录表
CREATE TABLE interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID REFERENCES interviews(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT '其他',
    question_order INT,
    user_answer TEXT,
    self_rating INT CHECK (self_rating BETWEEN 1 AND 5),
    ai_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 模拟练习记录表
CREATE TABLE practice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    interview_id UUID REFERENCES interviews(id) ON DELETE SET NULL,
    session_type VARCHAR(50) NOT NULL,
    questions_count INT DEFAULT 0,
    overall_score INT CHECK (overall_score BETWEEN 0 AND 100),
    duration_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 练习问答记录表
CREATE TABLE practice_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES practice_sessions(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT '其他',
    user_answer TEXT,
    ai_feedback TEXT,
    score INT CHECK (score BETWEEN 0 AND 100),
    suggestions TEXT,
    question_order INT
);

-- 学习计划表
CREATE TABLE learning_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_position VARCHAR(200) NOT NULL,
    target_company VARCHAR(200),
    target_date DATE,
    current_level VARCHAR(50) DEFAULT '入门',
    focus_areas JSONB,
    status VARCHAR(50) DEFAULT '进行中',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习任务表
CREATE TABLE learning_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES learning_plans(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    task_title VARCHAR(200) NOT NULL,
    task_content TEXT,
    due_date DATE NOT NULL,
    estimated_minutes INT,
    status VARCHAR(50) DEFAULT '待开始',
    completed_at TIMESTAMP,
    priority VARCHAR(50) DEFAULT '中'
);

-- 问题库表
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) DEFAULT '其他',
    position_type VARCHAR(100),
    question_text TEXT NOT NULL,
    reference_answer TEXT,
    answer_points JSONB,
    difficulty VARCHAR(50) DEFAULT '中等',
    frequency INT DEFAULT 0,
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_interviews_user_id ON interviews(user_id);
CREATE INDEX idx_interview_questions_interview_id ON interview_questions(interview_id);
CREATE INDEX idx_practice_sessions_user_id ON practice_sessions(user_id);
CREATE INDEX idx_practice_sessions_interview_id ON practice_sessions(interview_id);
CREATE INDEX idx_practice_questions_session_id ON practice_questions(session_id);
CREATE INDEX idx_learning_plans_user_id ON learning_plans(user_id);
CREATE INDEX idx_learning_tasks_plan_id ON learning_tasks(plan_id);
CREATE INDEX idx_learning_tasks_due_date ON learning_tasks(due_date);
CREATE INDEX idx_questions_category ON questions(category);
CREATE INDEX idx_questions_position_type ON questions(position_type);