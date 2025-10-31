-- 슬랭 브릿지 데이터베이스 스키마
-- 참고용 (실제 테이블은 Alembic 마이그레이션으로 생성)

-- 신조어 테이블
CREATE TABLE IF NOT EXISTS slangs (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) UNIQUE NOT NULL,
    meaning TEXT,
    usage_examples JSONB DEFAULT '[]',
    frequency INTEGER DEFAULT 0,
    rank INTEGER DEFAULT 0,
    rank_change INTEGER DEFAULT 0,
    category VARCHAR(50),
    source VARCHAR(100),
    trend_data JSONB DEFAULT '[]',
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    is_subscribed BOOLEAN DEFAULT TRUE,
    subscription_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 뉴스레터 발송 기록 테이블
CREATE TABLE IF NOT EXISTS newsletters (
    id SERIAL PRIMARY KEY,
    sent_date TIMESTAMP WITH TIME ZONE NOT NULL,
    top_slangs JSONB DEFAULT '[]',
    recipient_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_slangs_word ON slangs(word);
CREATE INDEX IF NOT EXISTS idx_slangs_frequency ON slangs(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_slangs_category ON slangs(category);
CREATE INDEX IF NOT EXISTS idx_slangs_last_updated ON slangs(last_updated);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_subscribed ON users(is_subscribed);


