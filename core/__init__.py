"""코어 모듈"""
from .logger import get_logger, info, debug, warning, error, critical

# ⚠️ 순환 참조 방지: scheduler와 executor는 필요할 때 import
# from .scheduler import scheduler, JobScheduler
# from .executor import JobExecutor

__all__ = [
    "get_logger", "info", "debug", "warning", "error", "critical",
]

# Lazy import를 위한 helper 함수
def get_scheduler():
    """스케줄러 인스턴스 반환 (lazy import)"""
    from .scheduler import scheduler
    return scheduler

def get_executor():
    """실행기 클래스 반환 (lazy import)"""
    from .executor import JobExecutor
    return JobExecutor
