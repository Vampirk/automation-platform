"""
API 공통 의존성
데이터베이스 세션, 인증 등
"""
import sys
from pathlib import Path
from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage import db, get_db
from core.logger import get_logger

logger = get_logger()


def get_database() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 제공
    
    FastAPI dependency로 사용:
        @app.get("/jobs")
        def get_jobs(db: Session = Depends(get_database)):
            ...
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


# API 키 검증 (선택적)
API_KEY_HEADER = "X-API-Key"


def verify_api_key(api_key: str = None) -> bool:
    """
    API 키 검증 (선택적 기능)
    
    Args:
        api_key: API 키
        
    Returns:
        검증 성공 여부
    """
    # TODO: 실제 API 키 검증 로직 구현
    # 현재는 모든 요청 허용
    return True


def get_current_user(api_key: str = None):
    """
    현재 사용자 정보 조회 (선택적)
    
    Args:
        api_key: API 키
        
    Returns:
        사용자 정보
    """
    # TODO: 실제 사용자 인증 로직 구현
    return {"username": "admin", "role": "admin"}


class CommonQueryParams:
    """
    공통 쿼리 파라미터
    페이지네이션, 정렬 등
    """
    
    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "id",
        order: str = "desc"
    ):
        """
        Args:
            skip: 건너뛸 레코드 수
            limit: 조회할 레코드 수 (최대 1000)
            sort_by: 정렬 기준 컬럼
            order: 정렬 순서 (asc/desc)
        """
        self.skip = skip
        self.limit = min(limit, 1000)  # 최대 1000개로 제한
        self.sort_by = sort_by
        self.order = order.lower()
        
        if self.order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="order must be 'asc' or 'desc'"
            )
