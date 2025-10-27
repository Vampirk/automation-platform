"""
모니터링 API
시스템 메트릭, 알림, 통계 조회
"""
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
import psutil
import socket

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.models import Job, JobExecution, Notification, SystemMetric, JobStatus
from dashboard.api.dependencies import get_database, CommonQueryParams
from dashboard.api import schemas
from core.logger import get_logger
from config import settings

logger = get_logger()
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# ========== 시스템 메트릭 ==========

@router.get("/metrics", response_model=schemas.SystemMetricListResponse)
def list_metrics(
    db: Session = Depends(get_database),
    params: CommonQueryParams = Depends(),
    hostname: Optional[str] = Query(None, description="호스트명 필터"),
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간")
):
    """
    시스템 메트릭 조회
    
    - **hostname**: 호스트명 필터
    - **start_time**: 시작 시간 (ISO 8601 형식)
    - **end_time**: 종료 시간 (ISO 8601 형식)
    """
    try:
        query = db.query(SystemMetric)
        
        # 필터 적용
        if hostname:
            query = query.filter(SystemMetric.hostname == hostname)
        
        if start_time:
            query = query.filter(SystemMetric.timestamp >= start_time)
        
        if end_time:
            query = query.filter(SystemMetric.timestamp <= end_time)
        
        # 전체 개수
        total = query.count()
        
        # 정렬 (기본: 최신순)
        order_column = getattr(SystemMetric, params.sort_by, SystemMetric.timestamp)
        if params.order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # 페이지네이션
        metrics = query.offset(params.skip).limit(params.limit).all()
        
        return schemas.SystemMetricListResponse(total=total, items=metrics)
    
    except Exception as e:
        logger.error(f"Error listing metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list metrics: {str(e)}"
        )


@router.get("/metrics/latest", response_model=schemas.SystemMetricResponse)
def get_latest_metric(
    db: Session = Depends(get_database),
    hostname: Optional[str] = Query(None, description="호스트명")
):
    """최신 시스템 메트릭 조회"""
    try:
        query = db.query(SystemMetric)
        
        if hostname:
            query = query.filter(SystemMetric.hostname == hostname)
        else:
            # 현재 호스트
            query = query.filter(SystemMetric.hostname == socket.gethostname())
        
        metric = query.order_by(desc(SystemMetric.timestamp)).first()
        
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No metrics found"
            )
        
        return metric
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest metric: {str(e)}"
        )


@router.get("/metrics/current", response_model=dict)
def get_current_system_metrics():
    """
    현재 시스템 메트릭 조회 (실시간)
    
    데이터베이스가 아닌 실시간 시스템 정보를 반환합니다.
    """
    try:
        # CPU 정보
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # 메모리 정보
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024 ** 3)
        memory_used_gb = memory.used / (1024 ** 3)
        memory_percent = memory.percent
        
        # 디스크 정보
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        
        # 네트워크 정보
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / (1024 ** 2)
        network_recv_mb = network.bytes_recv / (1024 ** 2)
        
        return {
            "hostname": socket.gethostname(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total_gb": round(memory_total_gb, 2),
                "used_gb": round(memory_used_gb, 2),
                "percent": memory_percent
            },
            "disk": {
                "total_gb": round(disk_total_gb, 2),
                "used_gb": round(disk_used_gb, 2),
                "percent": disk_percent
            },
            "network": {
                "sent_mb": round(network_sent_mb, 2),
                "recv_mb": round(network_recv_mb, 2)
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current metrics: {str(e)}"
        )


# ========== 알림 ==========

@router.get("/notifications", response_model=schemas.NotificationListResponse)
def list_notifications(
    db: Session = Depends(get_database),
    params: CommonQueryParams = Depends(),
    level: Optional[str] = Query(None, description="레벨 필터 (INFO/WARNING/ERROR/CRITICAL)"),
    channel: Optional[str] = Query(None, description="채널 필터"),
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간")
):
    """
    알림 목록 조회
    
    - **level**: 레벨 필터
    - **channel**: 채널 필터 (email/slack/discord)
    - **start_time**: 시작 시간
    - **end_time**: 종료 시간
    """
    try:
        query = db.query(Notification)
        
        # 필터 적용
        if level:
            query = query.filter(Notification.level == level.upper())
        
        if channel:
            query = query.filter(Notification.channel == channel)
        
        if start_time:
            query = query.filter(Notification.sent_at >= start_time)
        
        if end_time:
            query = query.filter(Notification.sent_at <= end_time)
        
        # 전체 개수
        total = query.count()
        
        # 정렬 (기본: 최신순)
        order_column = getattr(Notification, params.sort_by, Notification.sent_at)
        if params.order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # 페이지네이션
        notifications = query.offset(params.skip).limit(params.limit).all()
        
        return schemas.NotificationListResponse(total=total, items=notifications)
    
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}"
        )


@router.get("/notifications/{notification_id}", response_model=schemas.NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_database)):
    """알림 상세 조회"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    
    return notification


# ========== 대시보드 통계 ==========

@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_database)):
    """대시보드 통계 조회"""
    try:
        # 작업 통계
        total_jobs = db.query(Job).count()
        enabled_jobs = db.query(Job).filter(Job.enabled == True).count()
        
        # 실행 통계
        total_executions = db.query(JobExecution).count()
        success_executions = db.query(JobExecution).filter(
            JobExecution.status == JobStatus.SUCCESS
        ).count()
        failed_executions = db.query(JobExecution).filter(
            JobExecution.status == JobStatus.FAILED
        ).count()
        
        # 성공률 계산
        success_rate = (success_executions / total_executions * 100) if total_executions > 0 else 0.0
        
        # 알림 통계
        total_notifications = db.query(Notification).count()
        critical_notifications = db.query(Notification).filter(
            Notification.level == "CRITICAL"
        ).count()
        
        return schemas.DashboardStats(
            total_jobs=total_jobs,
            enabled_jobs=enabled_jobs,
            total_executions=total_executions,
            success_executions=success_executions,
            failed_executions=failed_executions,
            success_rate=round(success_rate, 2),
            total_notifications=total_notifications,
            critical_notifications=critical_notifications
        )
    
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get("/health", response_model=schemas.SystemHealthStatus)
def get_system_health(db: Session = Depends(get_database)):
    """시스템 건강 상태 조회"""
    try:
        # 최신 메트릭 조회
        latest_metric = db.query(SystemMetric).order_by(
            desc(SystemMetric.timestamp)
        ).first()
        
        if not latest_metric:
            # 메트릭이 없으면 현재 상태 사용
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
        else:
            cpu_percent = latest_metric.cpu_percent
            memory_percent = latest_metric.memory_percent
            disk_percent = latest_metric.disk_percent
        
        # 상태 판정
        def get_status(value, threshold_warning=80, threshold_critical=90):
            if value is None:
                return "unknown"
            if value >= threshold_critical:
                return "critical"
            if value >= threshold_warning:
                return "warning"
            return "healthy"
        
        cpu_status = get_status(cpu_percent, settings.cpu_threshold, 95)
        memory_status = get_status(memory_percent, settings.memory_threshold, 95)
        disk_status = get_status(disk_percent, settings.disk_threshold, 95)
        
        # 전체 상태 판정
        if "critical" in [cpu_status, memory_status, disk_status]:
            overall_status = "critical"
        elif "warning" in [cpu_status, memory_status, disk_status]:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return schemas.SystemHealthStatus(
            status=overall_status,
            cpu_status=cpu_status,
            memory_status=memory_status,
            disk_status=disk_status,
            last_check=latest_metric.timestamp if latest_metric else datetime.now(timezone.utc),
            current_cpu=cpu_percent,
            current_memory=memory_percent,
            current_disk=disk_percent
        )
    
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )


@router.get("/executions/recent", response_model=schemas.JobExecutionListResponse)
def get_recent_executions(
    db: Session = Depends(get_database),
    limit: int = Query(10, ge=1, le=100, description="조회할 레코드 수")
):
    """최근 작업 실행 이력 조회"""
    try:
        executions = db.query(JobExecution).order_by(
            desc(JobExecution.started_at)
        ).limit(limit).all()
        
        total = db.query(JobExecution).count()
        
        return schemas.JobExecutionListResponse(total=total, items=executions)
    
    except Exception as e:
        logger.error(f"Error getting recent executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent executions: {str(e)}"
        )


@router.get("/notifications/recent", response_model=schemas.NotificationListResponse)
def get_recent_notifications(
    db: Session = Depends(get_database),
    limit: int = Query(10, ge=1, le=100, description="조회할 레코드 수"),
    min_level: Optional[str] = Query(None, description="최소 레벨 (INFO/WARNING/ERROR/CRITICAL)")
):
    """최근 알림 조회"""
    try:
        query = db.query(Notification)
        
        # 레벨 필터
        if min_level:
            level_order = ["INFO", "WARNING", "ERROR", "CRITICAL"]
            if min_level.upper() in level_order:
                min_idx = level_order.index(min_level.upper())
                allowed_levels = level_order[min_idx:]
                query = query.filter(Notification.level.in_(allowed_levels))
        
        notifications = query.order_by(
            desc(Notification.sent_at)
        ).limit(limit).all()
        
        total = db.query(Notification).count()
        
        return schemas.NotificationListResponse(total=total, items=notifications)
    
    except Exception as e:
        logger.error(f"Error getting recent notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent notifications: {str(e)}"
        )
