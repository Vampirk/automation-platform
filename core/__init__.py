"""코어 모듈"""
from .logger import get_logger, info, debug, warning, error, critical

# ⚠️ 순환 참조 방지: scheduler와 executor는 절대 여기서 import하지 않음
# 필요한 곳에서 직접 import하거나 lazy import 함수 사용

__all__ = [
    "get_logger", "info", "debug", "warning", "error", "critical",
]

# Lazy import를 위한 helper 함수들
def get_scheduler():
    """스케줄러 인스턴스 반환 (lazy import)"""
    from .scheduler import scheduler
    return scheduler

def get_job_scheduler_class():
    """JobScheduler 클래스 반환 (lazy import)"""
    from .scheduler import JobScheduler
    return JobScheduler

def get_executor():
    """실행기 클래스 반환 (lazy import)"""
    from .executor import JobExecutor
    return JobExecutor