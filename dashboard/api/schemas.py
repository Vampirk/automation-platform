"""
API 요청/응답 스키마
Pydantic 모델 정의
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ========== 작업(Job) 스키마 ==========

class JobBase(BaseModel):
    """작업 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=200, description="작업 이름")
    description: Optional[str] = Field(None, description="작업 설명")
    job_type: str = Field(..., description="작업 유형 (monitoring/security/account 등)")
    script_path: str = Field(..., description="스크립트 경로")
    script_args: Optional[str] = Field(None, description="스크립트 인자 (JSON)")
    cron_expression: Optional[str] = Field(None, description="Cron 표현식")
    enabled: bool = Field(default=True, description="활성화 여부")
    max_retries: int = Field(default=3, ge=0, le=10, description="최대 재시도 횟수")
    timeout_seconds: int = Field(default=300, ge=10, le=3600, description="타임아웃 (초)")
    priority: int = Field(default=5, ge=1, le=10, description="우선순위 (1-10)")


class JobCreate(JobBase):
    """작업 생성 요청"""
    created_by: Optional[str] = Field(None, description="생성자")


class JobUpdate(BaseModel):
    """작업 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    job_type: Optional[str] = None
    script_path: Optional[str] = None
    script_args: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=10, le=3600)
    priority: Optional[int] = Field(None, ge=1, le=10)


class JobResponse(JobBase):
    """작업 응답"""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    """작업 목록 응답"""
    total: int
    items: List[JobResponse]


# ========== 작업 실행(JobExecution) 스키마 ==========

class JobExecutionBase(BaseModel):
    """작업 실행 기본 스키마"""
    job_id: int
    status: str = Field(..., description="상태 (pending/running/success/failed)")


class JobExecutionResponse(JobExecutionBase):
    """작업 실행 응답"""
    id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    is_retry: bool = False
    hostname: Optional[str] = None
    platform: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class JobExecutionListResponse(BaseModel):
    """작업 실행 목록 응답"""
    total: int
    items: List[JobExecutionResponse]


# ========== 알림(Notification) 스키마 ==========

class NotificationBase(BaseModel):
    """알림 기본 스키마"""
    title: str = Field(..., max_length=200)
    message: str
    level: str = Field(default="INFO", description="레벨 (INFO/WARNING/ERROR/CRITICAL)")
    channel: str = Field(..., max_length=50, description="채널 (email/slack/discord)")


class NotificationCreate(NotificationBase):
    """알림 생성 요청"""
    job_execution_id: Optional[int] = None


class NotificationResponse(NotificationBase):
    """알림 응답"""
    id: int
    sent_at: datetime
    success: bool = False
    error_message: Optional[str] = None
    job_execution_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """알림 목록 응답"""
    total: int
    items: List[NotificationResponse]


# ========== 시스템 메트릭(SystemMetric) 스키마 ==========

class SystemMetricBase(BaseModel):
    """시스템 메트릭 기본 스키마"""
    hostname: str
    cpu_percent: Optional[float] = None
    cpu_count: Optional[int] = None
    memory_total_gb: Optional[float] = None
    memory_used_gb: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_total_gb: Optional[float] = None
    disk_used_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    network_sent_mb: Optional[float] = None
    network_recv_mb: Optional[float] = None


class SystemMetricResponse(SystemMetricBase):
    """시스템 메트릭 응답"""
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SystemMetricListResponse(BaseModel):
    """시스템 메트릭 목록 응답"""
    total: int
    items: List[SystemMetricResponse]


# ========== 통계 스키마 ==========

class DashboardStats(BaseModel):
    """대시보드 통계"""
    total_jobs: int = Field(..., description="전체 작업 수")
    enabled_jobs: int = Field(..., description="활성화된 작업 수")
    total_executions: int = Field(..., description="전체 실행 횟수")
    success_executions: int = Field(..., description="성공한 실행 횟수")
    failed_executions: int = Field(..., description="실패한 실행 횟수")
    success_rate: float = Field(..., description="성공률 (%)")
    total_notifications: int = Field(..., description="전체 알림 수")
    critical_notifications: int = Field(..., description="긴급 알림 수")


class SystemHealthStatus(BaseModel):
    """시스템 건강 상태"""
    status: str = Field(..., description="상태 (healthy/warning/critical)")
    cpu_status: str = Field(..., description="CPU 상태")
    memory_status: str = Field(..., description="메모리 상태")
    disk_status: str = Field(..., description="디스크 상태")
    last_check: datetime = Field(..., description="마지막 확인 시간")
    current_cpu: Optional[float] = Field(None, description="현재 CPU 사용률 (%)")
    current_memory: Optional[float] = Field(None, description="현재 메모리 사용률 (%)")
    current_disk: Optional[float] = Field(None, description="현재 디스크 사용률 (%)")


# ========== 일반 응답 스키마 ==========

class MessageResponse(BaseModel):
    """일반 메시지 응답"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str
    detail: Optional[str] = None
    status_code: int
