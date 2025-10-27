# Automation Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Vampirk/automation-platform)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

크로스 플랫폼 보안 운영 자동화 시스템. Windows와 Linux 환경에서 시스템 모니터링, 보안 점검, 로그 분석, 계정 관리 작업을 스케줄링 기반으로 자동화합니다.

## 목차

- [개요](#개요)
- [시스템 아키텍처](#시스템-아키텍처)
- [주요 기능](#주요-기능)
- [설치](#설치)
- [사용법](#사용법)
- [API 문서](#api-문서)
- [테스트](#테스트)
- [프로젝트 구조](#프로젝트-구조)

## 개요

### 프로젝트 목적

반복적인 보안 운영 및 시스템 관리 작업을 자동화하여 운영 효율성을 증대하고 휴먼 에러를 감소시킵니다. 스케줄 기반 작업 실행, 실시간 모니터링, 이상 탐지, 리포트 생성 기능을 제공합니다.

### 기술 스택

- **언어**: Python 3.10+
- **프레임워크**: FastAPI (REST API), APScheduler (작업 스케줄링)
- **데이터베이스**: SQLAlchemy ORM (SQLite/PostgreSQL 지원)
- **모니터링**: psutil (시스템 메트릭)
- **로깅**: loguru (구조화된 로깅)
- **프론트엔드**: Vanilla JavaScript, Chart.js

### 시스템 요구사항

- Python 3.10 이상
- 운영체제: Windows 10/11, Ubuntu 20.04+, RHEL/CentOS 7+
- 메모리: 최소 2GB RAM
- 디스크: 최소 500MB 여유 공간

## 시스템 아키텍처
```
┌─────────────────────────────────────────────────────────┐
│                     Web Dashboard                       │
│              (HTML/CSS/JS + Chart.js)                   │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP/REST API
┌───────────────────────┴─────────────────────────────────┐
│                    FastAPI Server                       │
│              (Jobs API / Monitoring API)                │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────┴──────┐ ┌─────┴──────┐ ┌─────┴──────┐
│  Scheduler   │ │  Database  │ │   Logger   │
│ (APScheduler)│ │ (SQLAlchemy│ │  (loguru)  │
└───────┬──────┘ └────────────┘ └────────────┘
        │
┌───────┴──────────────────────────────────────────┐
│              Automation Scripts                   │
├────────────┬──────────────┬─────────────┬────────┤
│ Monitoring │   Security   │ Log Analysis│ Account│
│  Scripts   │   Checker    │   Scripts   │  Mgmt  │
└────────────┴──────────────┴─────────────┴────────┘
```

## 주요 기능

### 1. 작업 스케줄링

- Cron 표현식 기반 작업 스케줄링
- 데이터베이스에서 작업 자동 로드
- 작업 활성화/비활성화, 즉시 실행
- 실행 이력 자동 저장 (시작/종료 시간, 출력, 에러)

### 2. 시스템 모니터링

- CPU, 메모리, 디스크 사용률 실시간 수집
- 네트워크 송수신 트래픽 측정
- 임계치 기반 알림 생성
- 메트릭 데이터베이스 저장 및 추이 분석

### 3. 보안 점검

- **포트 스캔**: 멀티스레드 기반 포트 상태 점검 (quick/range/full 모드)
- **파일 권한 검사**: world-writable, SUID/SGID, SSH 키 권한 검증
- **종합 보안 점검**: 파일 권한, SSH 설정, 포트, 방화벽 통합 검사
- 보안 점수 산출 (0-100)

### 4. 로그 분석

- **실시간 로그 감시**: watchdog 기반 파일 변경 감지
- **패턴 탐지**: 17가지 사전 정의 패턴 (로그인 실패, 권한 거부, 메모리 부족 등)
- **이상 패턴 탐지**: 반복 로그인 실패, 비정상 시간대 활동
- **리포트 생성**: 일별/주별 요약 리포트 (텍스트/JSON 형식)

### 5. 계정 관리

- UID 0 비root 계정 탐지
- sudo 권한 이상 탐지
- 장기 미사용 계정 탐지 (90일+)
- 계정 정책 위반 보고

### 6. REST API

- 작업 CRUD (생성, 조회, 수정, 삭제)
- 작업 실행 이력 조회 및 필터링
- 시스템 메트릭 조회
- 알림 조회 및 통계
- OpenAPI (Swagger) 문서 자동 생성

### 7. 웹 대시보드

- 실시간 시스템 상태 모니터링
- 작업 관리 인터페이스
- 실행 이력 조회 및 상태 추적
- 차트 기반 데이터 시각화 (Chart.js)

## 설치

### 1. 저장소 복제
```bash
git clone https://github.com/Vampirk/automation-platform.git
cd automation-platform
```

### 2. 가상환경 생성 및 활성화

**Linux/macOS**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

주요 패키지:
- apscheduler: 작업 스케줄러
- fastapi: REST API 프레임워크
- uvicorn: ASGI 서버
- sqlalchemy: ORM
- pydantic: 데이터 검증
- psutil: 시스템 메트릭
- loguru: 로깅
- watchdog: 파일 시스템 감시

### 4. 환경 설정
```bash
cp .env.example .env
```

`.env` 파일 주요 설정:
```env
PROJECT_NAME=automation-platform
PLATFORM=auto
DATABASE_URL=sqlite:///./data/automation.db
LOG_LEVEL=INFO
LOG_FILE=logs/automation.log
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. 데이터베이스 초기화
```bash
python -c "from storage import init_database; init_database()"
```

## 사용법

### 스케줄러 실행
```bash
python main.py
```

등록된 모든 작업이 Cron 표현식에 따라 자동 실행됩니다.

### 작업 등록
```bash
python register_jobs.py
```

사전 정의된 작업(시스템 모니터링, 보안 점검, 로그 분석 등)을 데이터베이스에 등록합니다.

### 개별 스크립트 실행

**시스템 모니터링**
```bash
python scripts/monitoring/system_monitor.py
```

**보안 점검**
```bash
# 종합 보안 점검
sudo python scripts/security/security_checker.py

# 포트 스캔 (빠른 스캔)
python scripts/security/port_scanner.py --mode quick

# 파일 권한 검사
sudo python scripts/security/permission_checker.py --mode critical
```

**로그 분석**
```bash
# 실시간 로그 감시
sudo python scripts/log_analysis/log_analyzer.py

# 패턴 탐지
sudo python scripts/log_analysis/pattern_detector.py

# 리포트 생성
sudo python scripts/log_analysis/report_generator.py
```

**계정 관리**
```bash
# 계정 정책 검사
sudo python scripts/account_mgmt/account_checker.py

# 장기 미사용 계정 탐지
sudo python scripts/account_mgmt/inactive_finder.py
```

### API 서버 실행
```bash
python dashboard/api/main.py
```

또는
```bash
uvicorn dashboard.api.main:app --host 0.0.0.0 --port 8000
```

API 문서: `http://localhost:8000/docs`

### 웹 대시보드 실행
```bash
cd dashboard/frontend
python -m http.server 8080
```

브라우저에서 `http://localhost:8080` 접속

## API 문서

### 엔드포인트 개요

**작업 관리 (`/jobs`)**
- `GET /jobs` - 작업 목록 조회
- `POST /jobs` - 작업 생성
- `GET /jobs/{job_id}` - 작업 상세 조회
- `PUT /jobs/{job_id}` - 작업 수정
- `DELETE /jobs/{job_id}` - 작업 삭제
- `POST /jobs/{job_id}/execute` - 작업 즉시 실행
- `POST /jobs/{job_id}/enable` - 작업 활성화
- `POST /jobs/{job_id}/disable` - 작업 비활성화
- `GET /jobs/executions` - 전체 실행 이력 조회
- `GET /jobs/{job_id}/executions` - 특정 작업 실행 이력 조회

**모니터링 (`/monitoring`)**
- `GET /monitoring/metrics` - 시스템 메트릭 목록 조회
- `GET /monitoring/metrics/current` - 현재 시스템 메트릭 조회
- `GET /monitoring/notifications` - 알림 목록 조회
- `GET /monitoring/stats` - 대시보드 통계 조회
- `GET /monitoring/health` - 시스템 건강 상태 조회

상세한 API 문서는 서버 실행 후 `http://localhost:8000/docs`에서 확인할 수 있습니다.

### 예제: 작업 생성
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily_monitoring",
    "description": "일일 시스템 모니터링",
    "job_type": "monitoring",
    "script_path": "scripts/monitoring/system_monitor.py",
    "cron_expression": "0 0 * * *",
    "enabled": true,
    "timeout_seconds": 300
  }'
```

### 예제: 작업 실행
```bash
curl -X POST http://localhost:8000/jobs/1/execute
```

## 테스트

### 보안 점검 테스트
```bash
cd scripts/security
chmod +x test_security.sh
./test_security.sh
```

6개 자동화 테스트 실행:
1. 종합 보안 점검
2. 포트 스캔 (빠른 모드)
3. 포트 스캔 (범위 모드)
4. 파일 권한 검사 (중요 파일)
5. SSH 키 권한 검사
6. 모듈 import 테스트

### 로그 분석 테스트

**빠른 테스트 (3개 테스트, 약 10초)**
```bash
cd scripts/log_analysis
chmod +x quick_test.sh
./quick_test.sh
```

**전체 테스트 (10개 테스트, 약 60초)**
```bash
chmod +x test_log_analysis.sh
./test_log_analysis.sh
```

테스트 항목:
1. 기본 패턴 탐지
2. IP 주소 추적
3. 타임스탬프 파싱
4. 시간대별 활동 분석
5. 반복 로그인 실패 탐지
6. 새벽 시간대 활동 탐지
7. 리포트 생성 (텍스트)
8. 리포트 생성 (JSON)
9. 실시간 로그 감시 (10초)
10. 모듈 import 테스트

### 데이터베이스 조회
```bash
sqlite3 data/automation.db "SELECT id, name, enabled FROM jobs;"
sqlite3 data/automation.db "SELECT * FROM job_executions ORDER BY started_at DESC LIMIT 10;"
sqlite3 data/automation.db "SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10;"
```

## 프로젝트 구조
```
automation-platform/
├── main.py                         # 메인 진입점
├── register_jobs.py                # 작업 등록 스크립트
├── Pipfile                         # Pipenv 의존성 정의
├── Pipfile.lock                    # Pipenv 잠금 파일
├── .env                            # 환경 변수
├── .env.example                    # 환경 변수 템플릿
├── start-dashboard.sh              # 대시보드 시작 스크립트 (Linux/Mac)
├── start-dashboard.bat             # 대시보드 시작 스크립트 (Windows)
│
├── config/                         # 설정 관리
│   ├── __init__.py
│   └── settings.py                # Pydantic 기반 설정
│
├── core/                           # 핵심 엔진
│   ├── __init__.py
│   ├── logger.py                  # 로깅 시스템 (loguru)
│   ├── scheduler.py               # 작업 스케줄러 (APScheduler)
│   └── executor.py                # 작업 실행기
│
├── storage/                        # 데이터 저장
│   ├── __init__.py
│   ├── database.py                # DB 연결 관리
│   └── models.py                  # 데이터 모델 (SQLAlchemy ORM)
│
├── scripts/                        # 자동화 스크립트
│   ├── monitoring/                # 시스템 모니터링
│   │   ├── __init__.py
│   │   ├── system_monitor.py     # CPU/메모리/디스크 모니터링
│   │   └── README.md
│   │
│   ├── security/                  # 보안 점검
│   │   ├── __init__.py
│   │   ├── security_checker.py   # 종합 보안 점검
│   │   ├── port_scanner.py       # 포트 스캔
│   │   ├── permission_checker.py # 파일 권한 검사
│   │   ├── test_security.sh      # 자동화 테스트 스크립트
│   │   └── README.md
│   │
│   ├── log_analysis/              # 로그 분석
│   │   ├── __init__.py
│   │   ├── log_analyzer.py       # 실시간 로그 감시
│   │   ├── pattern_detector.py   # 이상 패턴 탐지
│   │   ├── report_generator.py   # 리포트 생성
│   │   ├── quick_test.sh         # 빠른 테스트 스크립트
│   │   ├── test_log_analysis.sh  # 전체 테스트 스크립트
│   │   ├── TEST_GUIDE.md
│   │   └── README.md
│   │
│   └── account_mgmt/              # 계정 관리
│       ├── __init__.py
│       ├── account_checker.py    # 계정 정책 검사
│       ├── inactive_finder.py    # 장기 미사용 계정 탐지
│       └── README.md
│
├── dashboard/                      # 웹 대시보드
│   ├── api/                       # REST API (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI 메인 서버
│   │   ├── dependencies.py       # 공통 의존성 (DB 세션)
│   │   ├── schemas.py            # Pydantic 스키마
│   │   ├── jobs.py               # 작업 관리 API
│   │   ├── monitoring.py         # 모니터링 API
│   │   ├── start_api.sh          # API 서버 시작 (Linux/Mac)
│   │   ├── start_api.bat         # API 서버 시작 (Windows)
│   │   └── README.md
│   │
│   └── frontend/                  # 프론트엔드
│       ├── index.html            # 메인 HTML
│       ├── style.css             # 스타일시트
│       ├── app.js                # JavaScript (API 연동)
│       └── README.md
│
├── logs/                           # 로그 파일
│   └── automation.log
│
├── data/                           # 데이터베이스 파일
│   └── automation.db              # SQLite 데이터베이스
│
├── reports/                        # 생성된 리포트
│   ├── logs/                      # 로그 분석 리포트
│   └── security/                  # 보안 점검 리포트
│
├── LICENSE                         # 라이센스 파일
├── README.md                       # 프로젝트 문서 (이 파일)
├── PROJECT_SUMMARY.md              # 프로젝트 요약
└── SCRIPT_TEST_STATUS.md           # 테스트 현황
```

### 주요 파일 설명

**루트 디렉토리**
- `main.py`: 스케줄러를 실행하는 메인 진입점
- `register_jobs.py`: 사전 정의된 작업을 데이터베이스에 등록
- `start-dashboard.sh/bat`: 프론트엔드와 백엔드를 동시에 실행하는 통합 스크립트

**설정 및 핵심**
- `config/settings.py`: 환경 변수 기반 설정 관리 (Pydantic)
- `core/scheduler.py`: APScheduler 기반 작업 스케줄링
- `core/executor.py`: 스크립트 실행 및 결과 기록
- `core/logger.py`: 구조화된 로깅 시스템

**데이터 저장**# 프로젝트 구조
```
automation-platform/
├── main.py                     # 메인 진입점
├── register_jobs.py            # 작업 등록 스크립트
├── config/                     # 설정 관리
│   ├── __init__.py
│   └── settings.py
├── core/                       # 핵심 엔진
│   ├── __init__.py
│   ├── logger.py              # 로깅 시스템
│   ├── scheduler.py           # 작업 스케줄러
│   └── executor.py            # 작업 실행기
├── storage/                    # 데이터 저장
│   ├── __init__.py
│   ├── database.py            # DB 연결 관리
│   └── models.py              # 데이터 모델 (ORM)
├── scripts/                    # 자동화 스크립트
│   ├── monitoring/            # 시스템 모니터링
│   │   ├── __init__.py
│   │   └── system_monitor.py
│   ├── security/              # 보안 점검
│   │   ├── __init__.py
│   │   ├── security_checker.py
│   │   ├── port_scanner.py
│   │   ├── permission_checker.py
│   │   └── test_security.sh
│   ├── log_analysis/          # 로그 분석
│   │   ├── __init__.py
│   │   ├── log_analyzer.py
│   │   ├── pattern_detector.py
│   │   ├── report_generator.py
│   │   ├── quick_test.sh
│   │   └── test_log_analysis.sh
│   └── account_mgmt/          # 계정 관리
│       ├── __init__.py
│       ├── account_checker.py
│       └── inactive_finder.py
├── dashboard/                  # 웹 대시보드
│   ├── api/                   # REST API
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── schemas.py
│   │   ├── jobs.py
│   │   └── monitoring.py
│   └── frontend/              # 프론트엔드
│       ├── index.html
│       ├── style.css
│       └── app.js
├── logs/                       # 로그 파일
├── data/                       # 데이터베이스 파일
├── reports/                    # 생성된 리포트
├── .env                        # 환경 변수
├── requirements.txt            # Python 의존성
└── README.md
```스트 (10개)

**생성 디렉토리**
- `logs/`: 애플리케이션 로그 파일 저장
- `data/`: SQLite 데이터베이스 파일 저장
- `reports/`: 자동 생성된 리포트 저장 (로그 분석, 보안 점검)

## 구현 현황

### 완료된 기능

- 기반 인프라 (설정, 로깅, 데이터베이스)
- 작업 스케줄러 시스템
- 시스템 모니터링 스크립트
- 보안 점검 스크립트 (100% 테스트 완료)
- 로그 분석 스크립트 (100% 테스트 완료)
- 계정 관리 스크립트
- REST API 서버
- 웹 대시보드

### 테스트 현황

- 보안 점검: 6개 자동화 테스트
- 로그 분석: 13개 자동화 테스트
- 전체 테스트 커버리지: 67%

## 라이센스

MIT License

## 문의

GitHub: https://github.com/Vampirk/automation-platform

## 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [APScheduler 문서](https://apscheduler.readthedocs.io/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [Chart.js 문서](https://www.chartjs.org/)