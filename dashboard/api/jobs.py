#!/usr/bin/env python3
"""
작업 관리 API
Job CRUD 및 실행 관리

수정 사항:
  - 2025-10-27: 라우팅 순서 수정 - /jobs/executions를 /{job_id} 앞으로 이동
"""
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage.models import Job, JobExecution, JobStatus, JobType
from dashboard.api.dependencies import get_database, CommonQueryParams
from dashboard.api import schemas
from core.logger import get_logger
from core.executor import ScriptExecutor

logger = get_logger()
router = APIRouter(prefix="/jobs", tags=["jobs"])


# ========== 작업(Job) CRUD ==========

@router.get("/", response_model=schemas.JobListResponse)
def list_jobs(
    db: Session = Depends(get_database),
    params: CommonQueryParams = Depends(),
    enabled: Optional[bool] = Query(None, description="활성화 상태 필터"),
    job_type: Optional[str] = Query(None, description="작업 유형 필터")
):
    """
    작업 목록 조회
    
    - **skip**: 건너뛸 레코드 수
    - **limit**: 조회할 레코드 수 (최대 1000)
    - **sort_by**: 정렬 기준 (id/name/created_at/updated_at)
    - **order**: 정렬 순서 (asc/desc)
    - **enabled**: 활성화 상태 필터
    - **job_type**: 작업 유형 필터
    """
    try:
        query = db.query(Job)
        
        # 필터 적용
        if enabled is not None:
            query = query.filter(Job.enabled == enabled)
        
        if job_type:
            query = query.filter(Job.job_type == JobType(job_type))
        
        # 전체 개수
        total = query.count()
        
        # 정렬
        order_column = getattr(Job, params.sort_by, Job.id)
        if params.order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # 페이지네이션
        jobs = query.offset(params.skip).limit(params.limit).all()
        
        return schemas.JobListResponse(total=total, items=jobs)
    
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )


# ========== 작업 실행 이력(JobExecution) - 구체적 경로를 먼저! ==========

@router.get("/executions", response_model=schemas.JobExecutionListResponse)
def list_all_executions(
    db: Session = Depends(get_database),
    params: CommonQueryParams = Depends(),
    status_filter: Optional[str] = Query(None, description="상태 필터")
):
    """
    ⭐ 전체 작업 실행 이력 조회 (프론트엔드용)
    
    모든 작업의 실행 이력을 조회합니다.
    """
    try:
        query = db.query(JobExecution)
        
        # 상태 필터
        if status_filter:
            try:
                status_enum = JobStatus(status_filter)
                query = query.filter(JobExecution.status == status_enum)
            except ValueError:
                valid_statuses = [s.value for s in JobStatus]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {valid_statuses}"
                )
        
        # 전체 개수
        total = query.count()
        
        # 정렬 (기본: 최신순)
        order_column = getattr(JobExecution, params.sort_by, JobExecution.started_at)
        if params.order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # 페이지네이션
        executions = query.offset(params.skip).limit(params.limit).all()
        
        # Job 이름 추가
        for execution in executions:
            if execution.job:
                execution.job_name = execution.job.name
        
        return schemas.JobExecutionListResponse(total=total, items=executions)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list executions: {str(e)}"
        )


@router.get("/executions/{execution_id}", response_model=schemas.JobExecutionResponse)
def get_execution(execution_id: int, db: Session = Depends(get_database)):
    """실행 이력 상세 조회"""
    execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )
    
    return execution


# ========== 작업(Job) 상세 조회 - path parameter는 나중에! ==========

@router.get("/{job_id}", response_model=schemas.JobResponse)
def get_job(job_id: int, db: Session = Depends(get_database)):
    """작업 상세 조회"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return job


@router.post("/", response_model=schemas.JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_data: schemas.JobCreate, db: Session = Depends(get_database)):
    """작업 생성"""
    try:
        # 이름 중복 확인
        existing = db.query(Job).filter(Job.name == job_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job with name '{job_data.name}' already exists"
            )
        
        # 작업 생성
        job = Job(**job_data.dict())
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Job created: {job.name} (ID: {job.id})")
        return job
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@router.put("/{job_id}", response_model=schemas.JobResponse)
def update_job(job_id: int, job_data: schemas.JobUpdate, db: Session = Depends(get_database)):
    """작업 수정"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    try:
        # 업데이트할 필드만 수정
        update_data = job_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)
        
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Job updated: {job.name} (ID: {job.id})")
        return job
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}"
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_database)):
    """작업 삭제"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    try:
        db.delete(job)
        db.commit()
        logger.info(f"Job deleted: {job.name} (ID: {job.id})")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}"
        )


@router.post("/{job_id}/enable", response_model=schemas.JobResponse)
def enable_job(job_id: int, db: Session = Depends(get_database)):
    """작업 활성화"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job.enabled = True
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    
    logger.info(f"Job enabled: {job.name} (ID: {job.id})")
    return job


@router.post("/{job_id}/disable", response_model=schemas.JobResponse)
def disable_job(job_id: int, db: Session = Depends(get_database)):
    """작업 비활성화"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job.enabled = False
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    
    logger.info(f"Job disabled: {job.name} (ID: {job.id})")
    return job


@router.post("/{job_id}/execute", response_model=schemas.JobExecutionResponse)
def execute_job(job_id: int, db: Session = Depends(get_database)):
    """
    작업 즉시 실행
    
    스케줄과 무관하게 작업을 즉시 실행합니다.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    try:
        # 실행 이력 생성
        execution = JobExecution(
            job_id=job.id,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc)
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # 작업 실행
        executor = ScriptExecutor()
        result = executor.execute_script(
            script_path=job.script_path,
            timeout=job.timeout_seconds
        )
        
        # 실행 결과 업데이트
        execution.status = JobStatus.SUCCESS if result.get("success") else JobStatus.FAILED
        execution.completed_at = datetime.now(timezone.utc)
        execution.duration_seconds = result.get("duration")
        execution.stdout = result.get("stdout")
        execution.stderr = result.get("stderr")
        execution.exit_code = result.get("exit_code")
        execution.error_message = result.get("error")
        
        db.commit()
        db.refresh(execution)
        
        logger.info(f"Job executed: {job.name} (ID: {job.id}), Status: {execution.status.value}")
        return execution
    
    except Exception as e:
        logger.error(f"Error executing job: {e}")
        
        # 실행 실패 기록
        if execution:
            execution.status = JobStatus.FAILED
            execution.completed_at = datetime.now(timezone.utc)
            execution.error_message = str(e)
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute job: {str(e)}"
        )


@router.get("/{job_id}/executions", response_model=schemas.JobExecutionListResponse)
def list_job_executions(
    job_id: int,
    db: Session = Depends(get_database),
    params: CommonQueryParams = Depends(),
    status_filter: Optional[str] = Query(None, description="상태 필터")
):
    """특정 작업의 실행 이력 조회"""
    # Job 존재 확인
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    try:
        query = db.query(JobExecution).filter(JobExecution.job_id == job_id)
        
        # 상태 필터
        if status_filter:
            try:
                status_enum = JobStatus(status_filter)
                query = query.filter(JobExecution.status == status_enum)
            except ValueError:
                valid_statuses = [s.value for s in JobStatus]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Must be one of: {valid_statuses}"
                )
        
        # 전체 개수
        total = query.count()
        
        # 정렬 (기본: 최신순)
        order_column = getattr(JobExecution, params.sort_by, JobExecution.started_at)
        if params.order == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # 페이지네이션
        executions = query.offset(params.skip).limit(params.limit).all()
        
        return schemas.JobExecutionListResponse(total=total, items=executions)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing job executions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list job executions: {str(e)}"
        )