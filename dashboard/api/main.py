#!/usr/bin/env python3
"""
Dashboard API 서버
FastAPI 기반 REST API

수정 사항:
  - 2025-10-27: 전체 실행 이력 엔드포인트 추가
  - 2025-10-27: lifespan 이벤트로 변경 (deprecation 해결)
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.logger import get_logger

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작
    logger.info("=" * 60)
    logger.info("🚀 Dashboard API Server Starting")
    logger.info(f"   Platform: {settings.platform}")
    logger.info(f"   API Docs: http://{settings.api_host}:{settings.api_port}/docs")
    logger.info("=" * 60)
    
    yield
    
    # 종료
    logger.info("🛑 Dashboard API Server Shutting Down")


# FastAPI 앱 생성
app = FastAPI(
    title="Automation Platform API",
    description="자동화 플랫폼 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (import를 여기서)
try:
    from dashboard.api import jobs, monitoring
    app.include_router(jobs.router)
    app.include_router(monitoring.router)
    logger.info("✅ Routers loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load routers: {e}")
    raise


@app.get("/")
def root():
    """루트 엔드포인트"""
    return {
        "name": "Automation Platform API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "jobs": "/jobs",
            "monitoring": "/monitoring"
        }
    }


@app.get("/health")
def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "platform": settings.platform,
        "api_version": "1.0.0"
    }


def main():
    """메인 함수"""
    try:
        logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
        
        uvicorn.run(
            "dashboard.api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=False,  # reload는 False로 (안정성)
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()