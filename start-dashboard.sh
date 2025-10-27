#!/bin/bash

# 자동화 플랫폼 - 빠른 시작 스크립트
# Frontend + Backend 동시 실행

echo "========================================"
echo "🚀 자동화 플랫폼 시작"
echo "========================================"
echo ""

# 프로젝트 루트 경로
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 1. 백엔드 API 서버 시작
echo "📡 백엔드 API 서버 시작 중..."
echo "   포트: 8000"
python dashboard/api/main.py &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
echo ""

# 잠시 대기 (서버 시작 시간)
sleep 3

# 2. 프론트엔드 서버 시작
echo "🎨 프론트엔드 서버 시작 중..."
echo "   포트: 8080"
cd dashboard/frontend
python -m http.server 8080 &
FRONTEND_PID=$!
echo "   PID: $FRONTEND_PID"
echo ""

# 3. 접속 정보 출력
echo "========================================"
echo "✅ 모든 서버가 시작되었습니다!"
echo "========================================"
echo ""
echo "📊 프론트엔드 대시보드:"
echo "   http://localhost:8080"
echo ""
echo "📡 백엔드 API:"
echo "   http://localhost:8000"
echo "   API 문서: http://localhost:8000/docs"
echo ""
echo "========================================"
echo "종료하려면 Ctrl+C를 누르세요"
echo "========================================"
echo ""

# 프로세스 ID 저장
echo $BACKEND_PID > /tmp/automation-backend.pid
echo $FRONTEND_PID > /tmp/automation-frontend.pid

# 신호 처리
cleanup() {
    echo ""
    echo "⏹️  서버를 종료합니다..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f /tmp/automation-backend.pid
    rm -f /tmp/automation-frontend.pid
    echo "✅ 종료 완료"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 브라우저 자동 열기 (선택적)
if command -v xdg-open > /dev/null; then
    sleep 2
    xdg-open http://localhost:8080 2>/dev/null
elif command -v open > /dev/null; then
    sleep 2
    open http://localhost:8080 2>/dev/null
fi

# 무한 대기
wait
