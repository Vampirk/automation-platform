# 🚀 Automation Platform - 프로젝트 요약

## ✅ 완료된 작업

### 1️⃣ **크로스 플랫폼 기반 구조** ✅
- **Windows/Linux 모두 지원** - 플랫폼 자동 감지 및 설정
- Python 3.10+ 호환
- 경로 처리는 `pathlib` 사용 (크로스 플랫폼)
- 플랫폼별 스크립트 실행 지원 (.py, .sh, .ps1, .bat)

### 2️⃣ **핵심 인프라** ✅
- **설정 관리 시스템** (`config/settings.py`)
  - 환경 변수 기반 설정 (.env)
  - pydantic으로 검증
  - 플랫폼 정보 자동 감지
  
- **로깅 시스템** (`core/logger.py`)
  - 구조화된 로깅 (loguru)
  - 파일/콘솔 동시 출력
  - 자동 로테이션 및 압축
  - 컨텍스트 정보 자동 추가
  
- **데이터베이스** (`storage/`)
  - SQLAlchemy ORM
  - SQLite (개발) / PostgreSQL (운영) 지원
  - 5개 테이블 정의:
    - jobs: 작업 정보
    - job_executions: 실행 이력
    - notifications: 알림 이력
    - system_metrics: 시스템 메트릭
    - configs: 설정 저장

### 3️⃣ **스케줄러 시스템** ✅
- **APScheduler 기반** (`core/scheduler.py`)
  - Cron 표현식 완벽 지원
  - 백그라운드 실행
  - 작업 추가/제거/일시정지/재개
  - 이벤트 리스너 (실행 완료, 에러, 추가, 제거)
  - 데이터베이스에서 작업 자동 로드

### 4️⃣ **작업 실행기** ✅
- **멀티 플랫폼 스크립트 실행** (`core/executor.py`)
  - Python 스크립트 (.py)
  - Bash 스크립트 (.sh) - Linux만
  - PowerShell/Batch (.ps1, .bat) - Windows만
  - 타임아웃 처리
  - stdout/stderr 캡처
  - 실행 결과 자동 저장

### 5️⃣ **시스템 모니터링 스크립트** ✅
- **리소스 모니터링** (`scripts/monitoring/system_monitor.py`)
  - CPU 사용률
  - 메모리 사용률
  - 디스크 사용률
  - 네트워크 트래픽
  - 임계치 초과 시 경고
  - 메트릭 자동 저장

---

## 📋 **코딩해야 하는 것 (남은 작업)**

### Phase 2: 자동화 스크립트 (4주)

#### 1. 로그 분석 스크립트
```
📁 scripts/log_analysis/
├── log_analyzer.py         # 실시간 로그 파싱 및 키워드 탐지
├── pattern_detector.py     # 이상 패턴 탐지
└── report_generator.py     # 일별 요약 리포트
```

**구현 항목:**
- [ ] 로그 파일 실시간 감시 (watchdog)
- [ ] 정규표현식 패턴 매칭
- [ ] 키워드 기반 탐지 (Failed login, Error 등)
- [ ] 이상 패턴 카운팅 및 분석
- [ ] 일별/주별 요약 리포트

#### 2. 보안 점검 스크립트
```
📁 scripts/security/
├── security_checker.py     # 보안 설정 검증
├── port_scanner.py         # 포트 스캔
├── permission_checker.py   # 파일 권한 검사
└── cve_scanner.py          # CVE 취약점 스캔
```

**구현 항목:**
- [ ] 파일 권한 검사 (/etc/passwd, /etc/shadow)
- [ ] 패스워드 정책 검증
- [ ] SSH 설정 검사
- [ ] 포트 스캔 (python-nmap)
- [ ] 방화벽 규칙 검증
- [ ] CVE 데이터베이스 조회

#### 3. 계정 관리 스크립트
```
📁 scripts/account_mgmt/
├── account_checker.py      # 계정 정책 검사
├── inactive_finder.py      # 장기 미사용 계정
└── password_policy.py      # 비밀번호 정책
```

**구현 항목:**
- [ ] 장기 미사용 계정 탐지 (90일+)
- [ ] 비밀번호 만료 임박 계정 (7일 이내)
- [ ] 권한 이상 계정 탐지
- [ ] 계정 변경 이력 추적
- [ ] 정책 위반 보고서

#### 4. 백업 및 유지보수 스크립트
```
📁 scripts/maintenance/
├── backup.py              # 자동 백업
├── cleanup.py             # 디스크 정리
└── health_check.py        # 시스템 헬스체크
```

### Phase 3: 알림 시스템 (2주)

```
📁 notification/
├── __init__.py
├── email_notifier.py      # 이메일 알림
├── slack_notifier.py      # Slack 웹훅
├── discord_notifier.py    # Discord 웹훅 (선택)
└── alert_manager.py       # 알림 관리
```

**구현 항목:**
- [ ] 이메일 알림 (SMTP)
- [ ] Slack 웹훅 연동
- [ ] 알림 템플릿 시스템
- [ ] 알림 레벨별 필터링
- [ ] 중복 알림 방지

### Phase 4: 웹 대시보드 (3주)

```
📁 dashboard/
├── api/
│   ├── __init__.py
│   ├── main.py           # FastAPI 서버
│   ├── jobs.py           # 작업 관리 API
│   └── monitoring.py     # 모니터링 API
└── frontend/
    ├── index.html
    ├── app.js
    └── style.css
```

**구현 항목:**
- [ ] REST API 서버 (FastAPI)
- [ ] 작업 CRUD API
- [ ] 실행 이력 조회 API
- [ ] 실시간 로그 스트리밍 (WebSocket)
- [ ] 프론트엔드 UI
- [ ] 대시보드 차트 (Chart.js)

---

## 🛠️ **기존 모듈 활용 가능 항목**

### ✅ 이미 활용 중인 모듈
- [x] **APScheduler** - 스케줄링 엔진
- [x] **psutil** - 시스템 메트릭
- [x] **SQLAlchemy** - 데이터베이스 ORM
- [x] **pydantic** - 설정 검증
- [x] **loguru** - 로깅 시스템

### 📦 추가로 활용할 모듈

#### 로그 분석용
- **watchdog** - 파일 시스템 감시
- **re** (내장) - 정규표현식

#### 보안 스캔용
- **python-nmap** - 포트 스캔
- **paramiko** - SSH 원격 실행
- **requests** - HTTP 클라이언트 (CVE API)

#### 알림용
- **smtplib** (내장) - 이메일
- **slack-sdk** - Slack 연동

#### 웹 대시보드용
- **FastAPI** - REST API 프레임워크
- **uvicorn** - ASGI 서버
- **websockets** - 실시간 통신

---

## 🚀 **현재 사용법**

### 1. 환경 설정
```bash
cd automation-platform

# 가상환경 생성
python -m venv venv

# 의존성 설치
./venv/bin/pip install apscheduler psutil sqlalchemy pydantic pydantic-settings python-dotenv loguru
```

### 2. 설정 파일 수정
```bash
# .env 파일 편집
nano .env

# 주요 설정:
# - DATABASE_URL: 데이터베이스 경로
# - LOG_LEVEL: 로그 레벨
# - CPU_THRESHOLD, MEMORY_THRESHOLD, DISK_THRESHOLD: 임계치
```

### 3. 실행
```bash
# 메인 애플리케이션 실행
PYTHONPATH=/home/claude/automation-platform ./venv/bin/python main.py

# 또는 각 모듈 개별 테스트
PYTHONPATH=/home/claude/automation-platform ./venv/bin/python config/settings.py
PYTHONPATH=/home/claude/automation-platform ./venv/bin/python core/logger.py
PYTHONPATH=/home/claude/automation-platform ./venv/bin/python storage/database.py
PYTHONPATH=/home/claude/automation-platform ./venv/bin/python scripts/monitoring/system_monitor.py
```

### 4. 작업 등록
```python
from storage import db, Job, JobType

with db.session_scope() as session:
    job = Job(
        name="custom_job",
        description="커스텀 작업",
        job_type=JobType.CUSTOM,
        script_path="scripts/my_script.py",
        cron_expression="0 * * * *",  # 매시간
        enabled=True,
        timeout_seconds=300
    )
    session.add(job)
```

---

## 📊 **프로젝트 현황**

### 완료율
- **Phase 1 (기반 구축)**: 100% ✅
- **Phase 2 (스크립트 개발)**: 25% (모니터링만 완료)
- **Phase 3 (알림/대시보드)**: 0%
- **Phase 4 (배포/고도화)**: 0%

### 전체 진행률: **약 30%**

---

## 🎯 **다음 단계 권장사항**

### 우선순위 1: 나머지 모니터링 스크립트
1. 로그 분석 스크립트
2. 보안 점검 스크립트

### 우선순위 2: 알림 시스템
1. 이메일 알림
2. Slack 연동

### 우선순위 3: 웹 대시보드
1. REST API
2. 기본 UI

---

## 💡 **개발 팁**

### Windows에서 테스트 시
```bash
# PowerShell에서
$env:PYTHONPATH="C:\path\to\automation-platform"
python main.py
```

### Linux에서 서비스로 등록
```bash
# systemd 서비스 생성
sudo nano /etc/systemd/system/automation.service

# 서비스 활성화
sudo systemctl enable automation.service
sudo systemctl start automation.service
```

### 데이터베이스 조회
```bash
sqlite3 data/automation.db "SELECT * FROM jobs;"
sqlite3 data/automation.db "SELECT * FROM job_executions ORDER BY started_at DESC LIMIT 10;"
```

---

## 📝 **주요 파일 설명**

| 파일 | 역할 |
|------|------|
| `main.py` | 메인 진입점, 플랫폼 초기화 |
| `config/settings.py` | 전역 설정 관리 |
| `core/scheduler.py` | 작업 스케줄러 |
| `core/executor.py` | 작업 실행기 |
| `core/logger.py` | 로깅 시스템 |
| `storage/models.py` | 데이터베이스 모델 |
| `storage/database.py` | DB 연결 관리 |

---

## 🐛 **알려진 이슈**

1. ~~`datetime.utcnow()` deprecated 경고~~ → 추후 `datetime.now(timezone.utc)`로 변경 필요
2. Windows에서 Shell 스크립트 실행 불가 (의도된 제한)
3. Linux에서 PowerShell 스크립트 실행 불가 (의도된 제한)

---

**작성일**: 2025-10-25  
**버전**: 1.0.0  
**Python**: 3.10+  
**플랫폼**: Windows/Linux
