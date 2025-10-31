from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Celery 앱 생성
celery_app = Celery(
    "slang_bridge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.crawler_tasks", "app.tasks.newsletter_tasks"]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분
)

# 주기적 작업 스케줄
celery_app.conf.beat_schedule = {
    # 매시간 크롤링
    "crawl-dcinside-hourly": {
        "task": "app.tasks.crawler_tasks.crawl_and_update_slangs",
        "schedule": crontab(minute=0),  # 매시간 정각
    },
    # 매주 월요일 오전 9시 뉴스레터 발송
    "send-weekly-newsletter": {
        "task": "app.tasks.newsletter_tasks.send_weekly_newsletter_task",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),  # 월요일 09:00
    },
    # 매일 자정 랭킹 업데이트
    "update-rankings-daily": {
        "task": "app.tasks.crawler_tasks.update_rankings",
        "schedule": crontab(hour=0, minute=0),  # 자정
    },
}


