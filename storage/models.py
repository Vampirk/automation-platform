"""
데이터베이스 모델 정의
SQLAlchemy ORM 사용
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, 
    DateTime, Float, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship
import enum


Base = declarative_base()


class JobStatus(enum.Enum):
    """작업 상태"""
    PENDING = "pending"      # 대기 중
    RUNNING = "running"      # 실행 중
    SUCCESS = "success"      # 성공
    FAILED = "failed"        # 실패
    CANCELLED = "cancelled"  # 취소됨


class JobType(enum.Enum):
    """작업 유형"""
    MONITORING = "monitoring"        # 시스템 모니터링
    LOG_ANALYSIS = "log_analysis"   # 로그 분석
    SECURITY = "security"           # 보안 점검
    ACCOUNT = "account"             # 계정 관리
    BACKUP = "backup"               # 백업
    CUSTOM = "custom"               # 사용자 정의


class Job(Base):
    """
    작업 정보 테이블
    스케줄링할 작업들의 메타데이터 저장
    """
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # 작업 유형
    job_type = Column(SQLEnum(JobType), default=JobType.CUSTOM)
    
    # 실행 정보
    script_path = Column(String(500), nullable=False)  # 스크립트 경로
    script_args = Column(Text, nullable=True)  # JSON 형태의 인자
    
    # 스케줄 정보 (Cron 표현식)
    cron_expression = Column(String(100), nullable=True)
    # 예: "0 * * * *" (매시간)
    # 예: "0 0 * * *" (매일 자정)
    
    # 실행 설정
    enabled = Column(Boolean, default=True)  # 활성화 여부
    max_retries = Column(Integer, default=3)  # 최대 재시도 횟수
    timeout_seconds = Column(Integer, default=300)  # 타임아웃 (초)
    priority = Column(Integer, default=5)  # 우선순위 (1-10, 높을수록 우선)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)  # 생성자
    
    # 관계
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, name='{self.name}', enabled={self.enabled})>"


class JobExecution(Base):
    """
    작업 실행 이력 테이블
    모든 작업 실행 결과 기록
    """
    __tablename__ = "job_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # 실행 정보
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # 결과 정보
    stdout = Column(Text, nullable=True)  # 표준 출력
    stderr = Column(Text, nullable=True)  # 표준 에러
    exit_code = Column(Integer, nullable=True)  # 종료 코드
    error_message = Column(Text, nullable=True)  # 에러 메시지
    
    # 재시도 정보
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False)
    
    # 실행 환경
    hostname = Column(String(200), nullable=True)  # 실행된 호스트
    platform = Column(String(50), nullable=True)  # 플랫폼 (windows/linux)
    
    # 관계
    job = relationship("Job", back_populates="executions")
    
    def __repr__(self):
        return (
            f"<JobExecution(id={self.id}, job_id={self.job_id}, "
            f"status={self.status.value}, duration={self.duration_seconds}s)>"
        )


class Notification(Base):
    """
    알림 이력 테이블
    발송된 모든 알림 기록
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 알림 정보
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR, CRITICAL
    
    # 채널 정보
    channel = Column(String(50), nullable=False)  # email, slack, discord
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # 발송 결과
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    
    # 연관 정보
    job_execution_id = Column(Integer, ForeignKey("job_executions.id"), nullable=True)
    
    def __repr__(self):
        return (
            f"<Notification(id={self.id}, channel='{self.channel}', "
            f"level='{self.level}', success={self.success})>"
        )


class SystemMetric(Base):
    """
    시스템 메트릭 테이블
    시스템 모니터링 데이터 저장
    """
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 시간 정보
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    hostname = Column(String(200), nullable=False, index=True)
    
    # CPU 메트릭
    cpu_percent = Column(Float, nullable=True)
    cpu_count = Column(Integer, nullable=True)
    
    # 메모리 메트릭
    memory_total_gb = Column(Float, nullable=True)
    memory_used_gb = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    
    # 디스크 메트릭
    disk_total_gb = Column(Float, nullable=True)
    disk_used_gb = Column(Float, nullable=True)
    disk_percent = Column(Float, nullable=True)
    
    # 네트워크 메트릭
    network_sent_mb = Column(Float, nullable=True)
    network_recv_mb = Column(Float, nullable=True)
    
    def __repr__(self):
        return (
            f"<SystemMetric(timestamp={self.timestamp}, "
            f"cpu={self.cpu_percent}%, mem={self.memory_percent}%, "
            f"disk={self.disk_percent}%)>"
        )


class Config(Base):
    """
    설정 저장 테이블
    동적 설정을 데이터베이스에 저장
    """
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<Config(key='{self.key}', value='{self.value}')>"


if __name__ == "__main__":
    # 테스트: 모델 구조 출력
    print("📊 Database Models:")
    print("=" * 60)
    
    models = [Job, JobExecution, Notification, SystemMetric, Config]
    for model in models:
        print(f"\n🔹 {model.__name__}")
        print(f"   Table: {model.__tablename__}")
        print("   Columns:")
        for column in model.__table__.columns:
            print(f"      - {column.name}: {column.type}")
