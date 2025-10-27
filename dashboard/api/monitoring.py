#!/usr/bin/env python3
"""
모니터링 API
시스템 메트릭, 알림, 통계 조회

수정 사항:
  - 2025-10-27: /monitoring/recent 엔드포인트 추가
"""
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.models import Job, JobExecution, JobStatus, SystemMetric, Notification
from dashboard.api.dependencies import get_database, CommonQueryParams
from dashboard.api import schemas
from core.logger import get_logger
import psutil
import socket

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
    """시스템 메트릭 목록 조회"""
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


@router.get("/metrics/current")
def get_current_metrics():
    """현재 시스템 메트릭 조회 (실시간)"""
    try:
        # 실시간 메트릭 수집
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024 ** 3)
        memory_used_gb = memory.used / (1024 ** 3)
        memory_percent = memory.percent
        
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        
        net_io = psutil.net_io_counters()
        network_sent_mb = net_io.bytes_sent / (1024 ** 2)
        network_recv_mb = net_io.bytes_recv / (1024 ** 2)
        
        return {
            "hostname": socket.gethostname(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {
                "percent": round(cpu_percent, 2),
                "count": cpu_count
            },
            "memory": {
                "total_gb": round(memory_total_gb, 2),
                "used_gb": round(memory_used_gb, 2),
                "percent": round(memory_percent, 2)
            },
            "disk": {
                "total_gb": round(disk_total_gb, 2),
                "used_gb": round(disk_used_gb, 2),
                "percent": round(disk_percent, 2)
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
    """알림 목록 조회"""
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


# ========== 통계 ==========

@router.get("/stats")
def get_stats(db: Session = Depends(get_database)):
    """대시보드 통계"""
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
        success_rate = 0
        if total_executions > 0:
            success_rate = round((success_executions / total_executions) * 100, 2)
        
        # 알림 통계
        total_notifications = db.query(Notification).count()
        critical_notifications = db.query(Notification).filter(
            Notification.level == 'CRITICAL'
        ).count()
        
        return {
            "total_jobs": total_jobs,
            "enabled_jobs": enabled_jobs,
            "total_executions": total_executions,
            "success_executions": success_executions,
            "failed_executions": failed_executions,
            "success_rate": success_rate,
            "total_notifications": total_notifications,
            "critical_notifications": critical_notifications
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/health")
def get_health(db: Session = Depends(get_database)):
    """시스템 건강 상태"""
    try:
        # 최신 메트릭 조회
        latest_metric = db.query(SystemMetric).order_by(
            desc(SystemMetric.timestamp)
        ).first()
        
        if not latest_metric:
            return {
                "status": "unknown",
                "message": "No metrics available"
            }
        
        # 임계치 체크
        cpu_status = "healthy"
        memory_status = "healthy"
        disk_status = "healthy"
        
        if latest_metric.cpu_percent > 95:
            cpu_status = "critical"
        elif latest_metric.cpu_percent > 80:
            cpu_status = "warning"
        
        if latest_metric.memory_percent > 95:
            memory_status = "critical"
        elif latest_metric.memory_percent > 85:
            memory_status = "warning"
        
        if latest_metric.disk_percent > 95:
            disk_status = "critical"
        elif latest_metric.disk_percent > 90:
            disk_status = "warning"
        
        # 전체 상태 판단
        overall_status = "healthy"
        if "critical" in [cpu_status, memory_status, disk_status]:
            overall_status = "critical"
        elif "warning" in [cpu_status, memory_status, disk_status]:
            overall_status = "warning"
        
        return {
            "status": overall_status,
            "cpu_status": cpu_status,
            "memory_status": memory_status,
            "disk_status": disk_status,
            "last_check": latest_metric.timestamp.isoformat(),
            "current_cpu": latest_metric.cpu_percent,
            "current_memory": latest_metric.memory_percent,
            "current_disk": latest_metric.disk_percent
        }
    
    except Exception as e:
        logger.error(f"Error getting health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health: {str(e)}"
        )


# ========== 최근 데이터 (프론트엔드용) ==========

@router.get("/recent")
def get_recent_data(
    db: Session = Depends(get_database),
    type: str = Query(..., description="데이터 타입 (executions/notifications/metrics)"),
    limit: int = Query(10, ge=1, le=100, description="조회 개수")
):
    """
    ⭐ 최근 데이터 조회 (프론트엔드용)
    
    대시보드에서 최근 실행 이력, 알림 등을 간단하게 조회
    """
    try:
        if type == "executions":
            # 최근 실행 이력
            executions = db.query(JobExecution).order_by(
                desc(JobExecution.started_at)
            ).limit(limit).all()
            
            # Job 이름 추가
            result = []
            for exec in executions:
                exec_dict = {
                    "id": exec.id,
                    "job_id": exec.job_id,
                    "job_name": exec.job.name if exec.job else "Unknown",
                    "status": exec.status.value,
                    "started_at": exec.started_at.isoformat() if exec.started_at else None,
                    "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                    "duration_seconds": exec.duration_seconds
                }
                result.append(exec_dict)
            
            return result
        
        elif type == "notifications":
            # 최근 알림
            notifications = db.query(Notification).order_by(
                desc(Notification.sent_at)
            ).limit(limit).all()
            
            return [
                {
                    "id": notif.id,
                    "title": notif.title,
                    "message": notif.message,
                    "level": notif.level,
                    "channel": notif.channel,
                    "sent_at": notif.sent_at.isoformat() if notif.sent_at else None
                }
                for notif in notifications
            ]
        
        elif type == "metrics":
            # 최근 메트릭
            metrics = db.query(SystemMetric).order_by(
                desc(SystemMetric.timestamp)
            ).limit(limit).all()
            
            return [
                {
                    "id": metric.id,
                    "timestamp": metric.timestamp.isoformat() if metric.timestamp else None,
                    "hostname": metric.hostname,
                    "cpu_percent": metric.cpu_percent,
                    "memory_percent": metric.memory_percent,
                    "disk_percent": metric.disk_percent
                }
                for metric in metrics
            ]
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type '{type}'. Must be one of: executions, notifications, metrics"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recent data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent data: {str(e)}"
        )