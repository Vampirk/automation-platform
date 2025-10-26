# 🚀 Automation Platform

**크로스 플랫폼 시스템 자동화 및 모니터링 플랫폼**

Python 기반의 강력한 자동화 플랫폼으로 시스템 모니터링, 보안 점검, 로그 분석 등을 자동화합니다.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Progress](https://img.shields.io/badge/progress-37.5%25-orange.svg)](README.md)

---

## 📊 **프로젝트 진행 상황**

```
Phase 1: 핵심 인프라         ████████████████████ 100% ✅
Phase 2: 자동화 스크립트     ██████████░░░░░░░░░░  50% 🔄
Phase 3: 알림 시스템         ░░░░░░░░░░░░░░░░░░░░   0% 📋
Phase 4: 웹 대시보드         ░░░░░░░░░░░░░░░░░░░░   0% 📋

전체 진행도                  ████████░░░░░░░░░░░░  37.5%
```

---

## ✨ **주요 기능**

### ✅ **구현 완료**

#### 🔧 **핵심 인프라**
- ✅ 크로스 플랫폼 지원 (Windows/Linux)
- ✅ 작업 스케줄러 (APScheduler + Cron 표현식)
- ✅ 작업 실행기 (Python/Bash/PowerShell/Batch)
- ✅ 구조화된 로깅 시스템 (Loguru)
- ✅ 데이터베이스 관리 (SQLAlchemy ORM)
- ✅ 설정 관리 (Pydantic + 환경 변수)

#### 📈 **시스템 모니터링**
- ✅ CPU/메모리/디스크/네트워크 모니터링
- ✅ 임계치 기반 경고
- ✅ 메트릭 데이터베이스 저장
- ✅ 자동 실행 및 로깅

#### 🛡️ **보안 점검**
- ✅ 종합 보안 점검 (파일 권한, SSH 설정, 방화벽)
- ✅ 포트 스캔 (멀티스레드, 위험 포트 탐지)
- ✅ 파일 권한 검사 (World-writable, SUID/SGID)
- ✅ SSH 키 권한 검증
- ✅ 보안 점수 산출 (0-100)
- ✅ 데이터베이스 자동 저장

### 🔄 **진행 중**
- 🔄 로그 분석 스크립트
- 🔄 계정 관리 스크립트

### 📋 **예정**
- 📋 이메일/Slack 알림 시스템
- 📋 웹 대시보드 (FastAPI + React/Vue)
- 📋 CVE 취약점 스캔
- 📋 자동 백업 스크립트

---

## 🚀 **빠른 시작**

### **1. 요구 사항**
- Python 3.10 이상
- pipenv (권장) 또는 pip
- SQLite (기본) 또는 PostgreSQL

### **2. 설치**

```bash
# 저장소 클론
git clone https://github.com/Vampirk/automation-platform.git
cd automation-platform

# 가상환경 생성 및 의존성 설치
pipenv install
# 또는
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### **3. 환경 설정**

`.env` 파일 편집:
```bash
cp .env.example .env
nano .env
```

주요 설정:
```env
# 데이터베이스
DATABASE_URL=sqlite:///./data/automation.db

# 로깅
LOG_LEVEL=INFO
LOG_FILE=logs/automation.log

# 모니터링 임계치
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
```

### **4. 실행**

#### **메인 애플리케이션 (스케줄러)**
```bash
# 모든 등록된 작업 자동 실행
python main.py
```

#### **개별 스크립트 실행**
```bash
# 시스템 모니터링
python scripts/monitoring/system_monitor.py

# 보안 점검
python scripts/security/security_checker.py

# 포트 스캔 (빠른 스캔)
python scripts/security/port_scanner.py --mode quick

# 파일 권한 검사
python scripts/security/permission_checker.py --mode critical
```

---

## 📁 **프로젝트 구조**

```
automation-platform/
├── main.py                      # 메인 진입점 (스케줄러 실행)
├── config/                      # 설정 관리
│   ├── __init__.py
│   └── settings.py             # 전역 설정 (Pydantic)
├── core/                        # 핵심 엔진
│   ├── __init__.py
│   ├── logger.py               # 로깅 시스템
│   ├── scheduler.py            # 작업 스케줄러
│   └── executor.py             # 작업 실행기
├── storage/                     # 데이터 저장
│   ├── __init__.py
│   ├── database.py             # DB 연결 관리
│   └── models.py               # 데이터 모델 (ORM)
├── scripts/                     # 자동화 스크립트
│   ├── monitoring/             # 시스템 모니터링 ✅
│   │   └── system_monitor.py
│   ├── security/               # 보안 점검 ✅
│   │   ├── security_checker.py
│   │   ├── port_scanner.py
│   │   ├── permission_checker.py
│   │   └── README.md
│   ├── log_analysis/           # 로그 분석 🔄
│   ├── account_mgmt/           # 계정 관리 🔄
│   └── maintenance/            # 유지보수 📋
├── notification/                # 알림 시스템 📋
├── dashboard/                   # 웹 대시보드 📋
├── logs/                        # 로그 파일
├── data/                        # 데이터베이스 파일
├── .env                         # 환경 변수
├── Pipfile                      # 의존성 정의
└── README.md                    # 이 파일
```

**범례:**
- ✅ 구현 완료
- 🔄 진행 중
- 📋 예정

---

## 📚 **사용 가이드**

### **작업 등록 및 스케줄링**

#### **방법 1: 데이터베이스에 직접 등록**

```python
from storage import db, Job, JobType

with db.session_scope() as session:
    # 매일 자정 시스템 모니터링
    monitoring_job = Job(
        name="daily_monitoring",
        description="일일 시스템 모니터링",
        job_type=JobType.MONITORING,
        script_path="scripts/monitoring/system_monitor.py",
        cron_expression="0 0 * * *",  # 매일 자정
        enabled=True,
        timeout_seconds=300,
        priority=5
    )
    session.add(monitoring_job)
    
    # 매일 자정 보안 점검
    security_job = Job(
        name="daily_security_check",
        description="일일 보안 점검",
        job_type=JobType.SECURITY,
        script_path="scripts/security/security_checker.py",
        cron_expression="0 0 * * *",  # 매일 자정
        enabled=True,
        timeout_seconds=300,
        priority=9
    )
    session.add(security_job)
```

#### **방법 2: Python 스크립트로 등록**

```bash
python -c "
from storage import db, Job, JobType
with db.session_scope() as session:
    job = Job(
        name='hourly_monitoring',
        job_type=JobType.MONITORING,
        script_path='scripts/monitoring/system_monitor.py',
        cron_expression='0 * * * *',
        enabled=True
    )
    session.add(job)
"
```

### **Cron 표현식 예시**

```
*/5 * * * *     # 5분마다
0 * * * *       # 매시간 정각
0 0 * * *       # 매일 자정
0 0 * * 0       # 매주 일요일 자정
0 9-17 * * 1-5  # 월~금 오전 9시~오후 5시
0 0 1 * *       # 매월 1일 자정
*/15 9-17 * * * # 평일 근무 시간에 15분마다
```

---

## 🔧 **스크립트 상세 가이드**

### **1. 시스템 모니터링**

```bash
# 기본 실행
python scripts/monitoring/system_monitor.py

# 출력 예시:
# 📊 System Metrics:
#    CPU: 45.2% (8 cores)
#    Memory: 8.5GB / 16.0GB (53.1%)
#    Disk: 120.3GB / 500.0GB (24.1%)
#    Network: ↑ 1024.5MB / ↓ 2048.3MB
```

**경고 기준:**
- CPU > 80%
- 메모리 > 85%
- 디스크 > 90%

### **2. 보안 점검**

#### **종합 보안 점검**
```bash
# sudo 권장 (전체 점검)
sudo python scripts/security/security_checker.py

# 일반 사용자 (일부 점검 스킵)
python scripts/security/security_checker.py
```

**점검 항목:**
- ✅ 파일 권한 (/etc/passwd, /etc/shadow 등)
- ✅ SSH 설정 (PermitRootLogin, PasswordAuthentication)
- ✅ 열린 포트
- ✅ 비밀번호 정책 (PASS_MAX_DAYS, PASS_MIN_DAYS)
- ✅ 방화벽 상태

**보안 점수:**
- 90-100: 우수
- 70-89: 양호
- 50-69: 보통
- 0-49: 취약

#### **포트 스캔**
```bash
# 일반 포트 빠른 스캔 (20개 주요 포트)
python scripts/security/port_scanner.py --mode quick

# 범위 스캔 (1-1024)
python scripts/security/port_scanner.py --mode range --start-port 1 --end-port 1024

# 전체 스캔 (1-65535, 시간 오래 걸림)
python scripts/security/port_scanner.py --mode full

# 원격 서버 스캔
python scripts/security/port_scanner.py --target 192.168.1.100 --mode quick
```

#### **파일 권한 검사**
```bash
# 중요 시스템 파일만
python scripts/security/permission_checker.py --mode critical

# World-writable 파일 검색
sudo python scripts/security/permission_checker.py --mode world-writable --directory /home

# SUID/SGID 파일 검색
sudo python scripts/security/permission_checker.py --mode suid --directory /usr/bin

# SSH 키 권한 검사
python scripts/security/permission_checker.py --mode ssh

# 모든 검사
sudo python scripts/security/permission_checker.py --mode all
```

---

## 📊 **데이터베이스 조회**

### **작업 목록 조회**
```bash
sqlite3 data/automation.db "SELECT id, name, enabled, cron_expression FROM jobs;"
```

### **실행 이력 조회**
```bash
sqlite3 data/automation.db "SELECT * FROM job_executions ORDER BY started_at DESC LIMIT 10;"
```

### **보안 점검 결과 조회**
```bash
sqlite3 data/automation.db "
SELECT title, level, sent_at 
FROM notifications 
WHERE channel = 'security_check' 
ORDER BY sent_at DESC 
LIMIT 5;
"
```

### **시스템 메트릭 조회**
```bash
sqlite3 data/automation.db "
SELECT timestamp, cpu_percent, memory_percent, disk_percent 
FROM system_metrics 
ORDER BY timestamp DESC 
LIMIT 10;
"
```

---

## 🧪 **테스트**

### **단위 테스트**
```bash
# 설정 테스트
python config/settings.py

# 로거 테스트
python core/logger.py

# 데이터베이스 테스트
python storage/database.py

# 스케줄러 테스트
python core/scheduler.py

# 실행기 테스트
python core/executor.py
```

### **통합 테스트**
```bash
# 시스템 모니터링 테스트
python scripts/monitoring/system_monitor.py

# 보안 스크립트 통합 테스트
./scripts/security/test_security.sh

# 전체 테스트 (sudo 권장)
sudo ./scripts/security/test_security.sh
```

---

## 🗺️ **로드맵**

### **Phase 2: 자동화 스크립트 (진행 중 - 50%)**
- [x] 시스템 모니터링
- [x] 보안 점검
- [ ] 로그 분석
- [ ] 계정 관리
- [ ] 백업 자동화

### **Phase 3: 알림 시스템 (예정)**
- [ ] 이메일 알림 (SMTP)
- [ ] Slack 웹훅
- [ ] Discord 웹훅
- [ ] 알림 템플릿
- [ ] 중복 알림 방지

### **Phase 4: 웹 대시보드 (예정)**
- [ ] FastAPI REST API
- [ ] 작업 관리 API (CRUD)
- [ ] 실행 이력 조회 API
- [ ] 실시간 로그 스트리밍 (WebSocket)
- [ ] 프론트엔드 UI (React/Vue)
- [ ] 대시보드 차트 (Chart.js)

---

## 📝 **변경 이력**

### **v0.4.0 (2025-10-26)** - 현재
- ✅ 보안 점검 스크립트 추가
  - 종합 보안 점검 (파일 권한, SSH, 포트, 방화벽)
  - 포트 스캔 (멀티스레드, 위험 포트 탐지)
  - 파일 권한 검사 (world-writable, SUID/SGID, SSH 키)
  - 보안 점수 산출 시스템
- ✅ 테스트 스크립트 추가

### **v0.3.0 (2025-10-25)**
- ✅ 시스템 모니터링 스크립트 추가

### **v0.2.0 (2025-10-24)**
- ✅ 작업 스케줄러 구현
- ✅ 작업 실행기 구현

### **v0.1.0 (2025-10-23)**
- ✅ 프로젝트 초기 구조 설정

---

## 👥 **팀원**

- **남수민** (2184039) - 팀장
- **김규민** (2084002)
- **임준호** (2184XXX)

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**
