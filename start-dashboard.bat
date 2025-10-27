@echo off
REM 자동화 플랫폼 - 빠른 시작 스크립트 (Windows)
REM Frontend + Backend 동시 실행

echo ========================================
echo 🚀 자동화 플랫폼 시작
echo ========================================
echo.

REM 백엔드 API 서버 시작
echo 📡 백엔드 API 서버 시작 중...
echo    포트: 8000
start "Backend API" cmd /k "python dashboard\api\main.py"
echo.

REM 잠시 대기
timeout /t 3 /nobreak > nul

REM 프론트엔드 서버 시작
echo 🎨 프론트엔드 서버 시작 중...
echo    포트: 8080
cd dashboard\frontend
start "Frontend Server" cmd /k "python -m http.server 8080"
cd ..\..
echo.

REM 접속 정보
echo ========================================
echo ✅ 모든 서버가 시작되었습니다!
echo ========================================
echo.
echo 📊 프론트엔드 대시보드:
echo    http://localhost:8080
echo.
echo 📡 백엔드 API:
echo    http://localhost:8000
echo    API 문서: http://localhost:8000/docs
echo.
echo ========================================
echo 브라우저에서 자동으로 열립니다...
echo 종료하려면 각 창을 닫으세요
echo ========================================
echo.

REM 브라우저 자동 열기
timeout /t 2 /nobreak > nul
start http://localhost:8080

pause
