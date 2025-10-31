-- 슬랭 브릿지 데이터베이스 초기화 스크립트

-- 확장 설치
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 데이터베이스 및 사용자는 Docker Compose에서 자동 생성됨

-- 인덱스 생성 (테이블은 Alembic으로 생성)
-- CREATE INDEX IF NOT EXISTS idx_slangs_word ON slangs(word);
-- CREATE INDEX IF NOT EXISTS idx_slangs_frequency ON slangs(frequency DESC);
-- CREATE INDEX IF NOT EXISTS idx_slangs_category ON slangs(category);
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 초기 데이터 (옵션)
-- INSERT INTO slangs (word, meaning, frequency, category, source, first_seen, last_updated, created_at) VALUES
-- ('ㅇㅈ', '인정', 100, '일반', 'dcinside', NOW(), NOW(), NOW()),
-- ('ㄱㅅ', '감사', 90, '일반', 'dcinside', NOW(), NOW(), NOW());


