-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nickname VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(255),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 徽章定义表
CREATE TABLE badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    description VARCHAR(200) NOT NULL,
    icon VARCHAR(100) NOT NULL,
    rarity VARCHAR(20) DEFAULT 'common',
    unlock_condition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户徽章收集表
CREATE TABLE user_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    badge_id UUID REFERENCES badges(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    review_record_id UUID,
    UNIQUE(user_id, badge_id)
);

-- 复盘记录表
CREATE TABLE review_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_name VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    interview_date DATE,
    crash_type VARCHAR(50) NOT NULL,
    quiz_answers JSON NOT NULL,
    badge_id UUID REFERENCES badges(id),
    action_items JSON NOT NULL,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 救援话术库
CREATE TABLE rescue_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    crash_type VARCHAR(50) NOT NULL,
    title VARCHAR(100) NOT NULL,
    script TEXT NOT NULL,
    tips TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX idx_review_records_user_id ON review_records(user_id);
CREATE INDEX idx_review_records_crash_type ON review_records(crash_type);
CREATE INDEX idx_rescue_scripts_crash_type ON rescue_scripts(crash_type);
