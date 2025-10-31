import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = "../data/slangs.db"):
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
    
    def add_slang(self, word: str, meaning: str = "", examples: List[str] = None) -> bool:
        """신조어 추가"""
        if examples is None:
            examples = []
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO slangs (word, meaning, examples, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (word, meaning, json.dumps(examples, ensure_ascii=False), datetime.now()))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding slang: {e}")
            return False
        finally:
            conn.close()
    
    def get_ranking(self, limit: int = 20) -> List[Dict]:
        """신조어 랭킹 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT word, meaning, examples, usage_count, updated_at
            FROM slangs
            ORDER BY usage_count DESC, updated_at DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            word, meaning, examples_json, usage_count, updated_at = row
            examples = json.loads(examples_json) if examples_json else []
            results.append({
                'word': word,
                'meaning': meaning,
                'examples': examples,
                'usage_count': usage_count,
                'updated_at': updated_at
            })
        
        conn.close()
        return results
    
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

