import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # 현재 파일 기준으로 data 디렉토리 찾기
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            data_dir = os.path.join(parent_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "slangs.db")
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 신조어 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slangs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                meaning TEXT,
                examples TEXT,
                usage_count INTEGER DEFAULT 1,
                method TEXT DEFAULT 'enhanced',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 기존 테이블에 method 컬럼 추가 (마이그레이션)
        try:
            cursor.execute('ALTER TABLE slangs ADD COLUMN method TEXT DEFAULT \'enhanced\'')
        except sqlite3.OperationalError:
            pass  # 이미 컬럼이 있으면 무시
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                newsletter_subscribed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 구독자 테이블 (이메일용 - 기존 호환성)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # 신조어별 영상 매핑 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS slang_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slang_word TEXT NOT NULL,
                video_id TEXT NOT NULL,
                video_title TEXT,
                video_thumbnail TEXT,
                video_duration INTEGER,
                view_count INTEGER,
                like_count INTEGER,
                caption_match_times TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(slang_word, video_id)
            )
        ''')
        
        # 인덱스 추가
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_slang_videos_word ON slang_videos(slang_word)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_slang_videos_video_id ON slang_videos(video_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, username: str, password: str, email: str = None) -> bool:
        """사용자 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password, email)
                VALUES (?, ?, ?)
            ''', (username, password, email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
        finally:
            conn.close()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """사용자 조회 (사용자 이름으로)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password, email, newsletter_subscribed
            FROM users WHERE username = ?
        ''', (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'email': row[3],
                'newsletter_subscribed': bool(row[4])
            }
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """사용자 조회 (이메일로)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password, email, newsletter_subscribed
            FROM users WHERE email = ?
        ''', (email,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'email': row[3],
                'newsletter_subscribed': bool(row[4])
            }
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """사용자 ID로 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, newsletter_subscribed
            FROM users WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'username': row[1],
                'email': row[2],
                'newsletter_subscribed': bool(row[3])
            }
        return None
    
    def toggle_newsletter_subscription(self, user_id: int) -> bool:
        """뉴스레터 구독 토글"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 현재 상태 확인
            cursor.execute('SELECT newsletter_subscribed FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            new_status = not bool(row[0])
            
            cursor.execute('''
                UPDATE users SET newsletter_subscribed = ? WHERE id = ?
            ''', (new_status, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error toggling subscription: {e}")
            return False
        finally:
            conn.close()
    
    def get_newsletter_subscription_status(self, user_id: int) -> bool:
        """뉴스레터 구독 상태 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT newsletter_subscribed FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return bool(row[0]) if row else False
    
    def add_slang(self, word: str, meaning: str = "", examples: List[str] = None, 
                  usage_count: int = 1, method: str = 'enhanced') -> bool:
        """신조어 추가"""
        if examples is None:
            examples = []
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 기존 단어가 있으면 usage_count 확인
            cursor.execute('SELECT usage_count FROM slangs WHERE word = ?', (word,))
            existing = cursor.fetchone()
            
            if existing:
                existing_count = existing[0]
                # 기존 단어면 usage_count를 업데이트
                # 기존 값이 1 (기본값)이면 무조건 새로운 값으로 교체
                if existing_count is None or existing_count == 0 or existing_count == 1:
                    # 기존 값이 기본값이면 무조건 새로운 값으로 교체
                    new_count = usage_count if usage_count > 0 else 1
                    print(f"[DB 업데이트] '{word}': 기존값 {existing_count} -> 새값 {usage_count}로 교체")
                else:
                    # 둘 다 유효한 값이면 더 큰 값 사용
                    new_count = max(existing_count, usage_count)
                    if new_count != existing_count:
                        print(f"[DB 업데이트] '{word}': {existing_count} -> {new_count}로 업데이트")
                cursor.execute('''
                    UPDATE slangs 
                    SET meaning = ?, examples = ?, usage_count = ?, method = ?, updated_at = ?
                    WHERE word = ?
                ''', (meaning, json.dumps(examples, ensure_ascii=False), new_count, method, datetime.now(), word))
            else:
                # 새 단어면 추가
                actual_usage_count = usage_count if usage_count > 0 else 1
                cursor.execute('''
                    INSERT INTO slangs (word, meaning, examples, usage_count, method, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (word, meaning, json.dumps(examples, ensure_ascii=False), actual_usage_count, method, datetime.now()))
                print(f"[DB 추가] '{word}': {actual_usage_count}회로 저장")
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding slang: {e}")
            return False
        finally:
            conn.close()
    
    def get_slang_by_word(self, word: str) -> Optional[Dict]:
        """특정 신조어 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT word, meaning, examples, usage_count, method, updated_at
            FROM slangs
            WHERE word = ?
        ''', (word,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            word, meaning, examples_json, usage_count, method, updated_at = row
            examples = json.loads(examples_json) if examples_json else []
            return {
                'word': word,
                'meaning': meaning or '',
                'examples': examples,
                'usage_count': usage_count or 1,
                'method': method or 'enhanced',
                'updated_at': updated_at
            }
        return None
    
    def get_ranking(self, limit: int = 20, period: Optional[str] = None) -> List[Dict]:
        """신조어 랭킹 조회
        
        Args:
            limit: 반환할 최대 개수
            period: 시간 필터 ('today', 'week', 'month', None=전체)
        
        정렬: usage_count 내림차순 (높은 사용 횟수 우선), 동일하면 updated_at 내림차순
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 시간 필터 조건 구성
        date_filter = ""
        if period == 'today':
            date_filter = "AND DATE(updated_at) = DATE('now')"
        elif period == 'week':
            date_filter = "AND updated_at >= datetime('now', '-7 days')"
        elif period == 'month':
            date_filter = "AND updated_at >= datetime('now', '-30 days')"
        
        # 모든 데이터 가져오기 (시간 필터 적용)
        query = f'''
            SELECT word, meaning, examples, usage_count, method, updated_at
            FROM slangs
            WHERE 1=1 {date_filter}
            ORDER BY 
                CASE WHEN usage_count IS NULL OR usage_count = 0 THEN 1 ELSE usage_count END DESC,
                updated_at DESC
        '''
        cursor.execute(query)
        
        results = []
        for row in cursor.fetchall():
            word, meaning, examples_json, usage_count, method, updated_at = row
            examples = json.loads(examples_json) if examples_json else []
            # usage_count가 None이거나 0이면 1로 처리
            actual_count = usage_count if usage_count and usage_count > 0 else 1
            results.append({
                'word': word,
                'meaning': meaning,
                'examples': examples,
                'usage_count': actual_count,
                'method': method or 'enhanced',  # None이면 enhanced로 처리
                'updated_at': updated_at
            })
        
        conn.close()
        
        # limit 적용 (Python 레벨에서)
        return results[:limit]
    
    def add_subscriber(self, email: str) -> bool:
        """구독자 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO subscribers (email, is_active, subscribed_at)
                VALUES (?, 1, ?)
            ''', (email, datetime.now()))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding subscriber: {e}")
            return False
        finally:
            conn.close()
    
    def remove_subscriber(self, email: str) -> bool:
        """구독자 제거"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE subscribers SET is_active = 0 WHERE email = ?
            ''', (email,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing subscriber: {e}")
            return False
        finally:
            conn.close()
    
    def get_active_subscribers(self) -> List[str]:
        """활성 구독자 목록 조회 (기존 subscribers 테이블)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email FROM subscribers WHERE is_active = 1
        ''')
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_newsletter_subscribers(self) -> List[str]:
        """뉴스레터 구독자 이메일 목록 조회 (users 테이블)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT email FROM users 
            WHERE newsletter_subscribed = 1 AND email IS NOT NULL AND email != ''
        ''')
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def add_slang_video(self, slang_word: str, video_id: str, video_title: str = None, 
                       video_thumbnail: str = None, video_duration: int = None,
                       view_count: int = None, like_count: int = None, 
                       caption_match_times: List[float] = None) -> bool:
        """신조어별 영상 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            match_times_json = json.dumps(caption_match_times) if caption_match_times else None
            cursor.execute('''
                INSERT OR REPLACE INTO slang_videos 
                (slang_word, video_id, video_title, video_thumbnail, video_duration,
                 view_count, like_count, caption_match_times, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (slang_word, video_id, video_title, video_thumbnail, video_duration,
                  view_count, like_count, match_times_json, datetime.now()))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding slang video: {e}")
            return False
        finally:
            conn.close()
    
    def get_videos_for_word(self, slang_word: str, limit: int = 5) -> List[Dict]:
        """특정 신조어의 영상 목록 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT video_id, video_title, video_thumbnail, video_duration,
                   view_count, like_count, caption_match_times
            FROM slang_videos
            WHERE slang_word = ?
            ORDER BY view_count DESC
            LIMIT ?
        ''', (slang_word, limit))
        
        results = []
        for row in cursor.fetchall():
            video_id, title, thumbnail, duration, views, likes, match_times_json = row
            match_times = json.loads(match_times_json) if match_times_json else []
            results.append({
                'video_id': video_id,
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'view_count': views,
                'like_count': likes,
                'match_times': match_times
            })
        
        conn.close()
        return results
    
    def get_stats(self) -> Dict:
        """통계 정보 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 총 신조어 수
        cursor.execute('SELECT COUNT(*) FROM slangs')
        total_slangs = cursor.fetchone()[0]
        
        # 총 구독자 수
        cursor.execute('SELECT COUNT(*) FROM subscribers WHERE is_active = 1')
        total_subscribers = cursor.fetchone()[0]
        
        # 최근 업데이트된 신조어
        cursor.execute('''
            SELECT COUNT(*) FROM slangs 
            WHERE updated_at >= datetime('now', '-7 days')
        ''')
        recent_slangs = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_slangs': total_slangs,
            'total_subscribers': total_subscribers,
            'recent_slangs': recent_slangs
        }

