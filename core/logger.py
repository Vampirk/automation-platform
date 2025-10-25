"""
로깅 시스템 - 크로스 플랫폼 지원
구조화된 로깅, 자동 로테이션, 컨텍스트 정보 추가
"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from config import settings


class Logger:
    """
    통합 로거 클래스
    - 파일과 콘솔에 동시 출력
    - 자동 로테이션
    - 구조화된 로깅
    - 크로스 플랫폼 지원
    """
    
    def __init__(self):
        self._configured = False
        self.logger = logger
    
    def configure(self):
        """로거 설정 초기화"""
        if self._configured:
            return
        
        # 기본 핸들러 제거
        logger.remove()
        
        # 콘솔 출력 설정 (색상 포함, 크로스 플랫폼)
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            level=settings.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # 파일 출력 설정
        log_path = settings.get_log_path()
        logger.add(
            log_path,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            level=settings.log_level,
            rotation=settings.log_rotation,
            retention=settings.log_retention,
            compression="zip",  # 압축 저장
            encoding="utf-8",
            enqueue=True,  # 비동기 로깅 (멀티스레드 안전)
            backtrace=True,
            diagnose=True
        )
        
        self._configured = True
        logger.info(f"Logger initialized on {settings.platform} platform")
    
    def get_logger(self):
        """로거 인스턴스 반환"""
        if not self._configured:
            self.configure()
        return self.logger


# 전역 로거 인스턴스
_logger_instance = Logger()


def get_logger():
    """
    전역 로거 가져오기
    Returns:
        loguru.Logger 인스턴스
    """
    return _logger_instance.get_logger()


# 편의 함수들
def debug(message: str, **kwargs):
    """디버그 로그"""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs):
    """정보 로그"""
    get_logger().info(message, **kwargs)


def warning(message: str, **kwargs):
    """경고 로그"""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs):
    """에러 로그"""
    get_logger().error(message, **kwargs)


def critical(message: str, **kwargs):
    """치명적 에러 로그"""
    get_logger().critical(message, **kwargs)


def log_job_start(job_id: str, job_name: str):
    """작업 시작 로그"""
    info(f"🚀 Job started", job_id=job_id, job_name=job_name)


def log_job_success(job_id: str, job_name: str, duration: float):
    """작업 성공 로그"""
    info(
        f"✅ Job completed successfully", 
        job_id=job_id, 
        job_name=job_name,
        duration_seconds=round(duration, 2)
    )


def log_job_failure(job_id: str, job_name: str, error_msg: str):
    """작업 실패 로그"""
    error(
        f"❌ Job failed",
        job_id=job_id,
        job_name=job_name,
        error=error_msg
    )


def log_platform_info():
    """플랫폼 정보 로그"""
    platform_info = settings.get_platform_info()
    info(
        f"Platform: {platform_info['system']} {platform_info['release']} "
        f"({platform_info['machine']})"
    )
    info(f"Python: {platform_info['python_version']}")


if __name__ == "__main__":
    # 테스트
    logger = get_logger()
    
    log_platform_info()
    
    debug("디버그 메시지 테스트")
    info("정보 메시지 테스트")
    warning("경고 메시지 테스트")
    
    # 구조화된 로깅 테스트
    log_job_start("job-001", "test_job")
    log_job_success("job-001", "test_job", 1.23)
    log_job_failure("job-002", "failed_job", "Connection timeout")
    
    print(f"\n✅ 로그 파일 저장 위치: {settings.get_log_path()}")
