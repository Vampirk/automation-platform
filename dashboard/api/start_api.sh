#!/bin/bash

# Automation Platform - Dashboard API 서버 시작 스크립트
# 작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
# 작성일: 2025-10-26

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🚀 Starting Automation Platform Dashboard API${NC}"
echo -e "${BLUE}============================================================${NC}"

# 1. 가상환경 확인
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# 2. 가상환경 활성화
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# 3. 의존성 설치 확인
echo -e "${BLUE}📚 Checking dependencies...${NC}"
if ! pip show fastapi > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  FastAPI not installed. Installing dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# 4. 데이터베이스 초기화 확인
if [ ! -f "$PROJECT_ROOT/data/automation.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found. Initializing...${NC}"
    python storage/database.py
    echo -e "${GREEN}✅ Database initialized${NC}"
fi

# 5. API 서버 시작
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}🚀 Starting API Server...${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📍 API Server: http://0.0.0.0:8000${NC}"
echo -e "${BLUE}📚 API Docs: http://0.0.0.0:8000/docs${NC}"
echo -e "${BLUE}📖 ReDoc: http://0.0.0.0:8000/redoc${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# API 서버 실행
PYTHONPATH="$PROJECT_ROOT" python dashboard/api/main.py

# 종료 메시지
echo -e "${BLUE}============================================================${NC}"
echo -e "${GREEN}✅ API Server stopped${NC}"
echo -e "${BLUE}============================================================${NC}"
