"""
설정 관리 모듈 - 크로스 플랫폼 지원
Windows/Linux 환경에서 모두 동작하도록 설계
"""
import platform
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 전역 설정"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 플랫폼 정보
    platform: str = Field(default="auto", description="운영체제 플랫폼")
    
    # 데이터베이스
    database_url: str = Field(
        default="sqlite:///./data/automation.db",
        description="데이터베이스 연결 URL"
    )
    
    # 로깅
    log_level: str = Field(default="INFO", description="로그 레벨")
    log_file: str = Field(default="logs/automation.log", description="로그 파일 경로")
    log_rotation: str = Field(default="500 MB", description="로그 로테이션 크기")
    log_retention: str = Field(default="30 days", description="로그 보관 기간")
    
    # 스케줄러
    scheduler_timezone: str = Field(default="Asia/Seoul", description="스케줄러 타임존")
    max_concurrent_jobs: int = Field(default=10, description="최대 동시 실행 작업 수")
    
    # 이메일 알림
    email_enabled: bool = Field(default=False, description="이메일 알림 활성화")
    email_smtp_host: str = Field(default="smtp.gmail.com", description="SMTP 호스트")
    email_smtp_port: int = Field(default=587, description="SMTP 포트")
    email_from: str = Field(default="automation@example.com", description="발신자 이메일")
    email_password: str = Field(default="", description="이메일 비밀번호")
    email_to: str = Field(default="admin@example.com", description="수신자 이메일")
    
    # Slack 알림
    slack_enabled: bool = Field(default=False, description="Slack 알림 활성화")
    slack_webhook_url: str = Field(default="", description="Slack 웹훅 URL")
    
    # 모니터링 임계치
    cpu_threshold: int = Field(default=80, description="CPU 사용률 임계치 (%)")
    memory_threshold: int = Field(default=85, description="메모리 사용률 임계치 (%)")
    disk_threshold: int = Field(default=90, description="디스크 사용률 임계치 (%)")
    
    # API 서버
    api_host: str = Field(default="0.0.0.0", description="API 서버 호스트")
    api_port: int = Field(default=8000, description="API 서버 포트")
    api_debug: bool = Field(default=False, description="디버그 모드")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 플랫폼 자동 감지
        if self.platform == "auto":
            self.platform = self._detect_platform()
    
    @staticmethod
    def _detect_platform() -> str:
        """
        현재 실행 중인 플랫폼 감지
        Returns:
            'windows', 'linux', 'darwin' (macOS) 등
        """
        system = platform.system().lower()
        return system
    
    def is_windows(self) -> bool:
        """Windows 플랫폼 여부"""
        return self.platform == "windows"
    
    def is_linux(self) -> bool:
        """Linux 플랫폼 여부"""
        return self.platform == "linux"
    
    def is_macos(self) -> bool:
        """macOS 플랫폼 여부"""
        return self.platform == "darwin"
    
    def get_base_path(self) -> Path:
        """
        프로젝트 루트 경로 반환 (크로스 플랫폼)
        Returns:
            Path 객체
        """
        return Path(__file__).parent.parent.absolute()
    
    def get_log_path(self) -> Path:
        """로그 파일의 절대 경로"""
        base = self.get_base_path()
        log_path = base / self.log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path
    
    def get_data_path(self) -> Path:
        """데이터 디렉토리 절대 경로"""
        base = self.get_base_path()
        data_path = base / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path
    
    def get_database_path(self) -> Optional[Path]:
        """
        SQLite 데이터베이스 파일 경로 (SQLite인 경우만)
        Returns:
            Path 객체 또는 None (SQLite가 아닌 경우)
        """
        if self.database_url.startswith("sqlite"):
            db_file = self.database_url.replace("sqlite:///", "")
            if db_file.startswith("./"):
                return self.get_base_path() / db_file[2:]
            return Path(db_file)
        return None
    
    def get_platform_info(self) -> dict:
        """
        플랫폼 상세 정보 반환
        Returns:
            플랫폼 정보 딕셔너리
        """
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "detected_platform": self.platform
        }


# 전역 설정 인스턴스
settings = Settings()


# 설정 정보 출력 함수
def print_settings():
    """현재 설정 정보 출력 (디버깅용)"""
    print("=" * 60)
    print("📋 Automation Platform Settings")
    print("=" * 60)
    print(f"🖥️  Platform: {settings.platform}")
    print(f"🐍 Python: {platform.python_version()}")
    print(f"📂 Base Path: {settings.get_base_path()}")
    print(f"📊 Database: {settings.database_url}")
    print(f"📝 Log File: {settings.get_log_path()}")
    print(f"⏰ Timezone: {settings.scheduler_timezone}")
    print(f"🔔 Email Alert: {'✅' if settings.email_enabled else '❌'}")
    print(f"💬 Slack Alert: {'✅' if settings.slack_enabled else '❌'}")
    print("=" * 60)


if __name__ == "__main__":
    # 테스트 실행
    print_settings()
    print("\n🔍 Detailed Platform Info:")
    import json
    print(json.dumps(settings.get_platform_info(), indent=2))
