"""
작업 스케줄러 - 크로스 플랫폼 지원
APScheduler를 사용한 Cron 스타일 스케줄링
Windows/Linux 모두 지원
"""
import platform
from datetime import datetime
from typing import Callable, Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import (
    EVENT_JOB_EXECUTED, EVENT_JOB_ERROR,
    EVENT_JOB_ADDED, EVENT_JOB_REMOVED
)

# ⚠️ 순환 참조 방지: 최상단에서는 config와 logger만 import
# storage 관련은 함수 내에서만 import
from config import settings
from core.logger import get_logger

logger = get_logger()


class JobScheduler:
    """
    작업 스케줄러 클래스
    - Cron 표현식 기반 스케줄링
    - 백그라운드 실행
    - 작업 실행 이력 자동 기록
    - 크로스 플랫폼 지원
    """
    
    def __init__(self):
        self.scheduler = None
        self._running = False
        self._job_map: Dict[str, int] = {}  # APScheduler job_id -> DB job_id
    
    def initialize(self):
        """스케줄러 초기화"""
        if self.scheduler is not None:
            logger.warning("Scheduler already initialized")
            return
        
        # BackgroundScheduler 생성 (별도 스레드에서 실행)
        self.scheduler = BackgroundScheduler(
            timezone=settings.scheduler_timezone,
            job_defaults={
                'coalesce': True,  # 놓친 실행을 하나로 통합
                'max_instances': settings.max_concurrent_jobs,
                'misfire_grace_time': 60  # 최대 60초 지연 허용
            }
        )
        
        # 이벤트 리스너 등록
        self.scheduler.add_listener(
            self._on_job_executed,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._on_job_error,
            EVENT_JOB_ERROR
        )
        self.scheduler.add_listener(
            self._on_job_added,
            EVENT_JOB_ADDED
        )
        self.scheduler.add_listener(
            self._on_job_removed,
            EVENT_JOB_REMOVED
        )
        
        logger.info(
            f"Scheduler initialized (timezone: {settings.scheduler_timezone}, "
            f"platform: {settings.platform})"
        )
    
    def start(self):
        """스케줄러 시작"""
        if self.scheduler is None:
            self.initialize()
        
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self.scheduler.start()
        self._running = True
        logger.info("✅ Scheduler started")
    
    def stop(self):
        """스케줄러 정지"""
        if not self._running:
            logger.warning("Scheduler not running")
            return
        
        self.scheduler.shutdown(wait=True)
        self._running = False
        logger.info("⏹️  Scheduler stopped")
    
    def add_job(
        self,
        func: Callable,
        job_id: str,
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        run_date: Optional[datetime] = None,
        args: tuple = None,
        kwargs: dict = None,
        **scheduler_kwargs
    ) -> str:
        """
        작업 추가
        
        Args:
            func: 실행할 함수
            job_id: 작업 고유 ID
            cron_expression: Cron 표현식 (예: "0 * * * *")
            interval_seconds: 주기 실행 (초)
            run_date: 특정 시각 1회 실행
            args: 함수 위치 인자
            kwargs: 함수 키워드 인자
            
        Returns:
            APScheduler job ID
        """
        if self.scheduler is None:
            self.initialize()
        
        # 트리거 결정
        trigger = None
        if cron_expression:
            trigger = CronTrigger.from_crontab(
                cron_expression,
                timezone=settings.scheduler_timezone
            )
            logger.info(f"Using Cron trigger: {cron_expression}")
        elif interval_seconds:
            trigger = IntervalTrigger(
                seconds=interval_seconds,
                timezone=settings.scheduler_timezone
            )
            logger.info(f"Using Interval trigger: {interval_seconds}s")
        elif run_date:
            trigger = DateTrigger(
                run_date=run_date,
                timezone=settings.scheduler_timezone
            )
            logger.info(f"Using Date trigger: {run_date}")
        else:
            raise ValueError("Must provide cron_expression, interval_seconds, or run_date")
        
        # 작업 추가
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            args=args or (),
            kwargs=kwargs or {},
            replace_existing=True,
            **scheduler_kwargs
        )
        
        logger.info(f"✅ Job added: {job_id}")
        return job.id
    
    def remove_job(self, job_id: str):
        """작업 제거"""
        if self.scheduler is None:
            logger.error("Scheduler not initialized")
            return
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"❌ Job removed: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
    
    def pause_job(self, job_id: str):
        """작업 일시 정지"""
        if self.scheduler is None:
            logger.error("Scheduler not initialized")
            return
        
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"⏸️  Job paused: {job_id}")
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
    
    def resume_job(self, job_id: str):
        """작업 재개"""
        if self.scheduler is None:
            logger.error("Scheduler not initialized")
            return
        
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"▶️  Job resumed: {job_id}")
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
    
    def get_jobs(self) -> list:
        """모든 등록된 작업 목록"""
        if self.scheduler is None:
            return []
        
        return self.scheduler.get_jobs()
    
    def get_job(self, job_id: str):
        """특정 작업 정보"""
        if self.scheduler is None:
            return None
        
        return self.scheduler.get_job(job_id)
    
    def is_running(self) -> bool:
        """스케줄러 실행 상태"""
        return self._running
    
    # 이벤트 핸들러들
    def _on_job_executed(self, event):
        """작업 실행 완료 이벤트"""
        logger.info(f"Job executed successfully: {event.job_id}")
    
    def _on_job_error(self, event):
        """작업 실행 에러 이벤트"""
        logger.error(
            f"Job execution failed: {event.job_id}",
            exception=str(event.exception)
        )
    
    def _on_job_added(self, event):
        """작업 추가 이벤트"""
        logger.debug(f"Job added to scheduler: {event.job_id}")
    
    def _on_job_removed(self, event):
        """작업 제거 이벤트"""
        logger.debug(f"Job removed from scheduler: {event.job_id}")
    
    def load_jobs_from_database(self):
        """
        데이터베이스에서 활성화된 작업들을 스케줄러에 로드
        ⚠️ storage import는 여기서만 수행 (순환 참조 방지)
        """
        # 함수 내에서 import (lazy import)
        from storage import db, Job
        from core.executor import JobExecutor
        
        with db.session_scope() as session:
            # 활성화된 작업들만 조회
            jobs = session.query(Job).filter(Job.enabled == True).all()
            
            logger.info(f"Loading {len(jobs)} jobs from database")
            
            executor = JobExecutor()
            
            for job in jobs:
                try:
                    # 실행 함수 생성
                    def job_func(job_id=job.id):
                        executor.execute_job(job_id)
                    
                    # 스케줄러에 추가
                    self.add_job(
                        func=job_func,
                        job_id=str(job.id),
                        cron_expression=job.cron_expression
                    )
                    
                    logger.info(f"Loaded job: {job.name} (ID: {job.id})")
                except Exception as e:
                    logger.error(f"Failed to load job {job.name}: {e}")


# 전역 스케줄러 인스턴스
scheduler = JobScheduler()


if __name__ == "__main__":
    # 테스트
    def test_job():
        print("Test job executed!")
    
    print("=" * 60)
    print("🧪 Scheduler Test")
    print("=" * 60)
    
    # 스케줄러 초기화 및 시작
    scheduler.initialize()
    scheduler.start()
    
    # 10초마다 실행되는 테스트 작업 추가
    scheduler.add_job(
        func=test_job,
        job_id="test_job",
        interval_seconds=10
    )
    
    print("\n✅ Test job added (runs every 10 seconds)")
    print("Press Ctrl+C to stop\n")
    
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping scheduler...")
        scheduler.stop()
        print("✅ Scheduler stopped")