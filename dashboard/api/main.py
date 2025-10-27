"""
Dashboard API 메인 서버
FastAPI 애플리케이션
"""
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dashboard.api import jobs, monitoring
from storage.database import init_database
from core.logger import get_logger
from config import settings

logger = get_logger()

# FastAPI 앱 생성
app = FastAPI(
    title="Automation Platform API",
    description="크로스 플랫폼 시스템 자동화 및 모니터링 플랫폼 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 이벤트 핸들러 ==========

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("=" * 60)
    logger.info("🚀 Starting Dashboard API Server")
    logger.info("=" * 60)
    
    # 데이터베이스 초기화
    try:
        init_database()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    logger.info(f"📍 API Server: http://{settings.api_host}:{settings.api_port}")
    logger.info(f"📚 API Docs: http://{settings.api_host}:{settings.api_port}/docs")
    logger.info(f"🔧 Platform: {settings.platform}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("=" * 60)
    logger.info("🛑 Shutting down Dashboard API Server")
    logger.info("=" * 60)


# ========== 에러 핸들러 ==========

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """검증 예외 처리"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "status_code": 422
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500
        }
    )


# ========== 라우터 등록 ==========

# 작업 관리 API
app.include_router(jobs.router)

# 모니터링 API
app.include_router(monitoring.router)


# ========== 기본 엔드포인트 ==========

@app.get("/")
async def root():
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
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "platform": settings.platform,
        "api_version": "1.0.0"
    }


@app.get("/version")
async def version():
    """버전 정보"""
    return {
        "api_version": "1.0.0",
        "python_version": sys.version,
        "platform": settings.platform
    }


# ========== 메인 실행 ==========

def main():
    """메인 실행 함수"""
    try:
        logger.info("Starting uvicorn server...")
        
        uvicorn.run(
            "dashboard.api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.api_debug,
            log_level="info"
        )
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
