#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신조어 데이터베이스 초기화 스크립트
"""
import os
import sys
from database import Database

def reset_slangs():
    """신조어 테이블의 모든 데이터 삭제"""
    db = Database()
    
    # 현재 신조어 개수 확인
    stats = db.get_stats()
    total_count = stats['total_slangs']
    
    if total_count == 0:
        print("[INFO] 삭제할 신조어가 없습니다.")
        return
    
    # 확인 메시지
    print(f"[경고] 데이터베이스에서 {total_count}개의 신조어를 삭제합니다.")
    print("계속하시겠습니까? (yes/no): ", end='')
    
    # 자동 실행을 위해 명령줄 인자로 --yes 옵션 지원
    if '--yes' in sys.argv or '-y' in sys.argv:
        confirm = 'yes'
        print('yes (자동 확인)')
    else:
        confirm = input().strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("[취소] 초기화가 취소되었습니다.")
        return
    
    # 데이터베이스 연결
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    try:
        # 신조어 테이블의 모든 데이터 삭제
        cursor.execute('DELETE FROM slangs')
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"[OK] {deleted_count}개의 신조어가 삭제되었습니다.")
        print(f"[OK] 데이터베이스 경로: {db.db_path}")
        
    except Exception as e:
        print(f"[ERROR] 초기화 실패: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    reset_slangs()

