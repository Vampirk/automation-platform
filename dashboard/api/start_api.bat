@echo off
REM Automation Platform - Dashboard API 서버 시작 스크립트 (Windows)
REM 작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
REM 작성일: 2025-10-26

setlocal enabledelayedexpansion

echo ============================================================
echo 🚀 Starting Automation Platform Dashboard API
echo ============================================================

REM 프로젝트 루트 디렉토리
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM 1. 가상환경 확인
if not exist "venv\" (
    echo ⚠️  Virtual environment not found. Creating...
    python -m venv venv
    echo ✅ Virtual environment created
)

REM 2. 가상환경 활성화
echo 📦 Activating virtual environment...
call venv\Scripts\activate.bat

REM 3. 의존성 설치 확인
echo 📚 Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo ⚠️  FastAPI not installed. Installing dependencies...
    pip install -r requirements.txt
    echo ✅ Dependencies installed
) else (
    echo ✅ Dependencies already installed
)

REM 4. 데이터베이스 초기화 확인
if not exist "data\automation.db" (
    echo ⚠️  Database not found. Initializing...
    python storage\database.py
    echo ✅ Database initialized
)

REM 5. API 서버 시작
echo ============================================================
echo 🚀 Starting API Server...
echo ============================================================
echo 📍 API Server: http://0.0.0.0:8000
echo 📚 API Docs: http://0.0.0.0:8000/docs
echo 📖 ReDoc: http://0.0.0.0:8000/redoc
echo ============================================================
echo Press Ctrl+C to stop the server
echo.

REM API 서버 실행
set PYTHONPATH=%PROJECT_ROOT%
python dashboard\api\main.py

REM 종료 메시지
echo ============================================================
echo ✅ API Server stopped
echo ============================================================

pause
