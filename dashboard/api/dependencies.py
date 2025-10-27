#!/usr/bin/env python3
"""
API 의존성 및 공통 파라미터
"""
import sys
from pathlib import Path
from typing import Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storage import db


def get_database() -> Session:
    """
    데이터베이스 세션 의존성
    
    FastAPI의 Depends와 함께 사용됩니다.
    """
    with db.session_scope() as session:
        yield session


class CommonQueryParams:
    """
    공통 쿼리 파라미터
    
    페이지네이션 및 정렬에 사용됩니다.
    """
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
        limit: int = Query(100, ge=1, le=1000, description="조회할 레코드 수"),
        sort_by: str = Query("id", description="정렬 기준"),
        order: str = Query("desc", regex="^(asc|desc)$", description="정렬 순서")
    ):
        self.skip = skip
        self.limit = limit
        self.sort_by = sort_by
        self.order = order