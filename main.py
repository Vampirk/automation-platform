#!/usr/bin/env python3
"""
Automation Platform - 메인 애플리케이션
크로스 플랫폼 자동화 스크립트 실행 시스템
"""
import sys
import signal
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import settings, print_settings
from core.logger import get_logger
# ⚠️ 순환 참조 방지: scheduler는 필요할 때 import
# from core.scheduler import scheduler
from storage import init_database, db, Job, JobType

logger = get_logger()


class AutomationPlatform:
    """자동화 플랫폼 메인 클래스"""
    
    def __init__(self):
        self.running = False
        self.scheduler = None
        
        # 시그널 핸들러 등록 (Ctrl+C 처리)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (Ctrl+C 등)"""
        logger.info(f"\n⚠️  Signal {signum} received. Shutting down...")
        self.stop()
        sys.exit(0)
    
    def initialize(self):
        """플랫폼 초기화"""
        logger.info("=" * 60)
        logger.info("🚀 Automation Platform Initializing")
        logger.info("=" * 60)
        
        # 설정 출력
        print_settings()
        
        # 데이터베이스 초기화
        logger.info("Initializing database...")
        init_database()
        
        # 스케줄러 초기화 (lazy import)
        logger.info("Initializing scheduler...")
        from core.scheduler import scheduler
        self.scheduler = scheduler
        self.scheduler.initialize()
        
        logger.info("✅ Platform initialized successfully")
    
    def setup_default_jobs(self):
        """기본 작업 설정 (초기 실행 시)"""
        with db.session_scope() as session:
            # 기존 작업 확인
            count = session.query(Job).count()
            
            if count == 0:
                logger.info("Setting up default jobs...")
                
                # 시스템 모니터링 작업 (5분마다)
                monitoring_job = Job(
                    name="system_monitoring",
                    description="시스템 리소스 모니터링 (CPU, 메모리, 디스크)",
                    job_type=JobType.MONITORING,
                    script_path="scripts/monitoring/system_monitor.py",
                    cron_expression="*/5 * * * *",  # 5분마다
                    enabled=True,
                    timeout_seconds=60,
                    priority=8
                )
                session.add(monitoring_job)
                
                logger.info("✅ Default jobs created")
            else:
                logger.info(f"Found {count} existing job(s)")
    
    def start(self):
        """플랫폼 시작"""
        if self.running:
            logger.warning("Platform already running")
            return
        
        logger.info("=" * 60)
        logger.info("▶️  Starting Automation Platform")
        logger.info("=" * 60)
        
        # 데이터베이스에서 작업 로드
        logger.info("Loading jobs from database...")
        self.scheduler.load_jobs_from_database()
        
        # 스케줄러 시작
        self.scheduler.start()
        
        self.running = True
        logger.info("=" * 60)
        logger.info("✅ Platform started successfully")
        logger.info("=" * 60)
        logger.info("💡 Press Ctrl+C to stop")
        logger.info("")
    
    def stop(self):
        """플랫폼 정지"""
        if not self.running:
            return
        
        logger.info("=" * 60)
        logger.info("⏹️  Stopping Automation Platform")
        logger.info("=" * 60)
        
        # 스케줄러 정지
        if self.scheduler:
            self.scheduler.stop()
        
        self.running = False
        logger.info("✅ Platform stopped")
    
    def run(self):
        """플랫폼 실행 (무한 루프)"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()


def main():
    """메인 함수"""
    platform = AutomationPlatform()
    
    try:
        # 초기화
        platform.initialize()
        
        # 기본 작업 설정
        platform.setup_default_jobs()
        
        # 시작
        platform.start()
        
        # 실행
        platform.run()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())