import schedule
import time
import threading
from datetime import datetime
from database import Database
from email_service import EmailService

def run_scheduled_crawl():
    """스케줄된 크롤링 실행"""
    try:
        print(f"[SCHEDULED] {datetime.now()} - 자동 크롤링 시작")
        from crawler import Crawler
        crawler = Crawler()
        result = crawler.crawl_and_analyze()
        
        # 데이터베이스에 저장
        db = Database()
        added_count = 0
        for slang_data in result:
            if db.add_slang(
                slang_data['word'], 
                slang_data['meaning'], 
                slang_data['examples']
            ):
                added_count += 1
        
        print(f"[SCHEDULED] 크롤링 완료! {added_count}개 신조어 추가")
        
    except Exception as e:
        print(f"[SCHEDULED ERROR] 크롤링 실패: {e}")

def run_scheduled_newsletter():
    """스케줄된 뉴스레터 발송"""
    try:
        print(f"[SCHEDULED] {datetime.now()} - 자동 뉴스레터 발송 시작")
        
        db = Database()
        email_service = EmailService()
        
        # 상위 5개 신조어 조회
        top_slangs = db.get_ranking(5)
        
        # 뉴스레터 구독자 조회 (users 테이블)
        subscribers = db.get_newsletter_subscribers()
        
        if not subscribers:
            print("[SCHEDULED] 구독자가 없어 뉴스레터 발송을 건너뜁니다.")
            return
        
        if not top_slangs:
            print("[SCHEDULED] 신조어가 없어 뉴스레터 발송을 건너뜁니다.")
            return
        
        # 이메일 발송
        success = email_service.send_newsletter(subscribers, top_slangs)
        
        if success:
            print(f"[SCHEDULED] 뉴스레터 발송 완료! {len(subscribers)}명에게 발송")
        else:
            print("[SCHEDULED ERROR] 뉴스레터 발송 실패")
        
    except Exception as e:
        print(f"[SCHEDULED ERROR] 뉴스레터 발송 실패: {e}")

def start_scheduler():
    """스케줄러 시작"""
    # 매일 오전 9시에 크롤링 실행
    schedule.every().day.at("09:00").do(run_scheduled_crawl)
    
    # 매주 월요일 오전 10시에 뉴스레터 발송
    schedule.every().monday.at("10:00").do(run_scheduled_newsletter)
    
    print("[SCHEDULER] 스케줄러 시작됨")
    print("[SCHEDULER] - 매일 09:00: 자동 크롤링")
    print("[SCHEDULER] - 매주 월요일 10:00: 뉴스레터 발송")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크

def start_scheduler_thread():
    """스케줄러를 별도 스레드에서 실행"""
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
