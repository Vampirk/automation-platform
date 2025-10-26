# 🚀 보안 운영 자동화 플랫폼 (Automation Platform)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Vampirk/automation-platform)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/Test%20Coverage-67%25-yellow.svg)](SCRIPT_TEST_STATUS.md)

> **캡스톤 디자인 프로젝트 - 자동 스크립트 실행 및 구현**  
> 정보보안학과 4학년 2학기 | 지도교수: 이병엽

반복적인 보안 운영 및 시스템 관리 작업을 자동화하여 휴먼 에러를 최소화하고,  
보안 담당자가 위협 분석 및 대응 등 고부가가치 업무에 집중할 수 있는 환경을 구축합니다.

---

## 👥 팀 구성

| 학번 | 학년 | 성명 | 역할 |
|------|------|------|------|
| 2184039 | 4 | 남수민 | 팀장 |
| 2084002 | 4 | 김규민 | 팀원 |
| 2184 | 4 | 임준호 | 팀원 |

---

## 📋 목차

- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [프로젝트 구조](#-프로젝트-구조)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [테스트](#-테스트)
- [구현 현황](#-구현-현황)
- [개발 로드맵](#-개발-로드맵)

---

## 🎯 프로젝트 개요

### 목표

1. **업무 효율성 증대**: 매일 수행하는 서버 점검, 로그 분석, 백업 확인 등 단순 반복 작업 자동화
2. **보안 강화 및 일관성 확보**: 정기적인 취약점 스캔, 보안 설정 값 검증 등을 스크립트로 표준화
3. **장애 예방 및 신속한 대응**: 시스템 임계치 감시 및 자동 알림/초기 대응
4. **휴먼 에러 감소**: 명령어 오타, 절차 누락 등의 실수 원천 차단

### 자동화 대상

#### 1. 보안 점검 ✅
- 서버 주요 보안 설정(패스워드 정책, 접근 권한 등) 정기 검사
- 신규 CVE 발표 시 관련 패키지 설치 여부 자동 스캔
- 포트 스캔 및 방화벽 규칙 검증
- 파일 권한 검사 (SUID/SGID, world-writable)

#### 2. 로그 분석 ✅
- 특정 키워드('Failed login', 'Error', 'Permission denied') 실시간 탐지
- 이상 패턴 탐지 (반복 로그인 실패, 새벽 시간대 의심 활동)
- 일별/주별 요약 리포트 자동 생성

#### 3. 시스템 운영 ✅
- CPU, 메모리, 디스크 사용량 모니터링
- 임계치 초과 시 자동 경고
- 네트워크 트래픽 모니터링

#### 4. 계정 관리 ✅
- 장기 미사용 계정 탐지 (90일+)
- 비밀번호 만료 임박 계정 탐지 (7일 이내)
- 권한 이상 계정 탐지 (UID 0 비root 계정, sudo 권한 이상)
- 계정 정책 위반 보고

---

## ✨ 주요 기능

### 🏗️ 크로스 플랫폼 지원
- **Windows/Linux** 모두 지원
- 플랫폼 자동 감지 및 설정
- 플랫폼별 스크립트 실행 (.py, .sh, .ps1, .bat)

### ⚙️ 핵심 인프라
- **설정 관리**: 환경 변수 기반 설정, Pydantic 검증
- **로깅 시스템**: 구조화된 로깅(loguru), 자동 로테이션
- **데이터베이스**: SQLAlchemy ORM, SQLite/PostgreSQL 지원

### 📅 스케줄러 시스템
- **APScheduler 기반** Cron 표현식 지원
- 작업 추가/제거/일시정지/재개
- 데이터베이스에서 작업 자동 로드
- 실행 이력 자동 저장

### 🔐 보안 점검 스크립트 (100% 테스트 완료)
- **종합 보안 점검**: 파일 권한, SSH 설정, 포트, 방화벽 검사
- **포트 스캔**: 멀티스레드 스캔, 위험 포트 탐지
- **파일 권한 검사**: world-writable, SUID/SGID, SSH 키 권한
- **보안 점수 산출**: 0-100점 자동 채점
- **자동화 테스트**: `test_security.sh` (6개 테스트)

### 📊 시스템 모니터링
- CPU/메모리/디스크 사용률 실시간 모니터링
- 네트워크 트래픽 추적
- 임계치 초과 시 자동 알림
- 메트릭 데이터베이스 저장

### 📝 로그 분석 (100% 테스트 완료)
- **실시간 로그 감시**: watchdog 기반 파일 변경 감지
- **17가지 패턴 탐지**: 로그인 실패, 권한 거부, 메모리 부족 등
- **이상 패턴 탐지**: 반복 로그인 실패, 새벽 시간대 활동
- **리포트 생성**: 일별/주별 요약 리포트 (텍스트/JSON)
- **자동화 테스트**: `quick_test.sh`, `test_log_analysis.sh` (13개 테스트)

### 👤 계정 관리
- **계정 정책 검사**: UID 0 계정, sudo 권한 이상 탐지
- **장기 미사용 계정**: 90일 이상 미로그인 계정 탐지
- **비밀번호 정책**: 만료 임박 계정 자동 탐지 (예정)
- **자동 알림**: 정책 위반 시 데이터베이스 알림 저장

---

## 📁 프로젝트 구조

```
automation-platform/
├── main.py                      # 메인 진입점 (스케줄러 실행)
│
├── config/                      # 설정 관리
│   ├── __init__.py
│   └── settings.py             # 전역 설정 (Pydantic)
│
├── core/                        # 핵심 엔진
│   ├── __init__.py
│   ├── logger.py               # 로깅 시스템 ✅
│   ├── scheduler.py            # 작업 스케줄러 ✅
│   └── executor.py             # 작업 실행기 ✅
│
├── storage/                     # 데이터 저장
│   ├── __init__.py
│   ├── database.py             # DB 연결 관리 ✅
│   └── models.py               # 데이터 모델 (ORM) ✅
│
├── scripts/                     # 자동화 스크립트
│   ├── monitoring/             # 시스템 모니터링 ✅
│   │   ├── __init__.py
│   │   ├── system_monitor.py  # CPU/메모리/디스크 모니터링
│   │   └── README.md
│   │
│   ├── security/               # 보안 점검 ✅ (100% 테스트)
│   │   ├── __init__.py
│   │   ├── security_checker.py    # 종합 보안 점검
│   │   ├── port_scanner.py        # 포트 스캔
│   │   ├── permission_checker.py  # 파일 권한 검사
│   │   ├── test_security.sh       # 🧪 자동화 테스트 (6개)
│   │   └── README.md
│   │
│   ├── log_analysis/           # 로그 분석 ✅ (100% 테스트)
│   │   ├── __init__.py
│   │   ├── log_analyzer.py        # 실시간 로그 감시
│   │   ├── pattern_detector.py    # 이상 패턴 탐지
│   │   ├── report_generator.py    # 리포트 생성
│   │   ├── quick_test.sh          # 🧪 빠른 테스트 (3개)
│   │   ├── test_log_analysis.sh   # 🧪 전체 테스트 (10개)
│   │   ├── TEST_GUIDE.md
│   │   └── README.md
│   │
│   ├── account_mgmt/           # 계정 관리 ✅
│   │   ├── __init__.py
│   │   ├── account_checker.py     # 계정 정책 검사
│   │   ├── inactive_finder.py     # 장기 미사용 계정
│   │   ├── password_policy.py     # 비밀번호 정책 (예정)
│   │   └── README.md              # 사용 가이드
│   │
│   └── maintenance/            # 유지보수 📋
│       ├── backup.py              # 자동 백업 (예정)
│       ├── cleanup.py             # 디스크 정리 (예정)
│       └── health_check.py        # 헬스체크 (예정)
│
├── notification/                # 알림 시스템 📋
│   ├── __init__.py
│   ├── email_notifier.py       # 이메일 알림 (예정)
│   ├── slack_notifier.py       # Slack 웹훅 (예정)
│   └── alert_manager.py        # 알림 관리 (예정)
│
├── dashboard/                   # 웹 대시보드 📋
│   ├── api/                    # FastAPI 서버 (예정)
│   └── frontend/               # React/Vue UI (예정)
│
├── logs/                        # 로그 파일
├── data/                        # 데이터베이스 파일
├── reports/                     # 생성된 리포트
│
├── .env                         # 환경 변수
├── .env.example                # 환경 변수 템플릿
├── requirements.txt            # Python 의존성
├── Pipfile                      # Pipenv 설정
├── PROJECT_SUMMARY.md          # 프로젝트 요약
├── SCRIPT_TEST_STATUS.md       # 테스트 현황 📊
└── README.md                    # 이 파일
```

**범례:**
- ✅ 구현 완료 및 테스트 완료
- 🔄 진행 중
- 📋 예정
- 🧪 자동화 테스트 스크립트

---

## 🔧 설치 방법

### 1. 시스템 요구사항

- **Python**: 3.10 이상
- **운영체제**: Windows 10/11, Ubuntu 20.04+, RHEL/CentOS 7+
- **권한**: 일부 기능은 관리자 권한 필요 (sudo/Administrator)

### 2. 저장소 클론

```bash
git clone https://github.com/Vampirk/automation-platform.git
cd automation-platform
```

### 3. 가상환경 생성

#### Linux/macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### 4. 의존성 설치

```bash
pip install -r requirements.txt
```

**주요 패키지:**
- `apscheduler` - 작업 스케줄러
- `psutil` - 시스템 메트릭
- `sqlalchemy` - 데이터베이스 ORM
- `pydantic` - 설정 검증
- `loguru` - 로깅
- `watchdog` - 파일 시스템 감시
- `python-nmap` - 포트 스캔 (선택)
- `pywin32` - Windows API (Windows만)

### 5. 환경 설정

```bash
cp .env.example .env
nano .env  # 또는 원하는 에디터로 편집
```

**주요 설정 항목:**

```env
# 프로젝트 설정
PROJECT_NAME=automation-platform
PLATFORM=auto  # auto, windows, linux

# 데이터베이스
DATABASE_URL=sqlite:///./data/automation.db

# 로깅
LOG_LEVEL=INFO
LOG_FILE=logs/automation.log

# 모니터링 임계치
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90

# API 서버 (예정)
API_HOST=0.0.0.0
API_PORT=8000
```

### 6. 데이터베이스 초기화

```bash
python -c "from storage import init_database; init_database()"
```

---

## 🚀 사용 방법

### 메인 애플리케이션 실행

```bash
# 스케줄러 시작 (등록된 모든 작업 자동 실행)
python main.py
```

### 개별 스크립트 실행

#### 1️⃣ 시스템 모니터링
```bash
python scripts/monitoring/system_monitor.py
```

**출력 예시:**
```
============================================================
📊 SYSTEM MONITOR REPORT
============================================================
Timestamp: 2025-10-26 14:20:00

CPU Usage: 45.2%
Memory Usage: 68.5% (5.5GB / 8.0GB)
Disk Usage: 72.3% (145GB / 200GB)
Network Sent: 1.2 MB/s
Network Recv: 0.8 MB/s

✅ All metrics within thresholds
============================================================
```

---

#### 2️⃣ 보안 점검

##### 종합 보안 점검
```bash
# sudo 권장
sudo python scripts/security/security_checker.py
```

##### 포트 스캔
```bash
# 빠른 스캔 (20개 주요 포트)
python scripts/security/port_scanner.py --mode quick

# 범위 스캔 (1-1024)
python scripts/security/port_scanner.py --mode range --start-port 1 --end-port 1024

# 전체 스캔 (시간 오래 걸림)
python scripts/security/port_scanner.py --mode full
```

##### 파일 권한 검사
```bash
# 중요 파일만
sudo python scripts/security/permission_checker.py --mode critical

# World-writable 파일 검색
sudo python scripts/security/permission_checker.py --mode world-writable --directory /home

# SSH 키 권한 검사
python scripts/security/permission_checker.py --mode ssh

# 전체 검사
sudo python scripts/security/permission_checker.py --mode all
```

---

#### 3️⃣ 로그 분석

##### 실시간 로그 감시
```bash
# 60초 동안 로그 감시
sudo python scripts/log_analysis/log_analyzer.py
```

##### 패턴 탐지 및 분석
```bash
sudo python scripts/log_analysis/pattern_detector.py
```

##### 리포트 생성
```bash
sudo python scripts/log_analysis/report_generator.py
```

생성된 리포트는 `reports/logs/` 디렉토리에 저장됩니다.

---

#### 4️⃣ 계정 관리

##### 계정 정책 검사
```bash
python scripts/account_mgmt/account_checker.py
```

##### 장기 미사용 계정 탐지
```bash
# Linux (sudo 필요)
sudo python scripts/account_mgmt/inactive_finder.py

# Windows
python scripts/account_mgmt/inactive_finder.py
```

자세한 사용법은 [`scripts/account_mgmt/README.md`](scripts/account_mgmt/README.md)를 참고하세요.

---

## 🧪 테스트

### 테스트 커버리지: **67%** (6/9 스크립트)

| 카테고리 | 스크립트 수 | 테스트 스크립트 | 커버리지 |
|---------|------------|----------------|---------|
| 🛡️ 보안 점검 | 3개 | ✅ `test_security.sh` | **100%** |
| 📋 로그 분석 | 3개 | ✅ `quick_test.sh`, `test_log_analysis.sh` | **100%** |
| 🖥️ 시스템 모니터링 | 1개 | ⚠️ 수동 테스트 | 0% |
| 👤 계정 관리 | 2개 | ⚠️ 수동 테스트 | 0% |

> 상세한 테스트 현황은 [SCRIPT_TEST_STATUS.md](SCRIPT_TEST_STATUS.md)를 참고하세요.

---

### 자동화 테스트 실행

#### 🛡️ 보안 스크립트 테스트
```bash
cd ~/automation-platform
./scripts/security/test_security.sh
```

**테스트 항목:**
1. ✅ security_checker.py 기본 실행
2. ✅ port_scanner.py - Quick scan
3. ✅ port_scanner.py - Range scan (1-100)
4. ✅ permission_checker.py - Critical files
5. ✅ permission_checker.py - SSH keys
6. ✅ 모듈 import 테스트

**총 6개 테스트**

---

#### 📋 로그 분석 빠른 테스트 (5-10초)
```bash
cd ~/automation-platform
./scripts/log_analysis/quick_test.sh
```

**테스트 항목:**
1. ✅ 기본 패턴 탐지
2. ✅ IP 주소 추적
3. ✅ 모듈 Import

**총 3개 테스트**

---

#### 📋 로그 분석 전체 테스트 (30-60초)
```bash
cd ~/automation-platform
./scripts/log_analysis/test_log_analysis.sh
```

**테스트 항목:**
1. ✅ Log Analyzer - 파일 분석
2. ✅ Pattern Detector - 시간대별 분석
3. ✅ Pattern Detector - 이상 패턴 탐지
4. ✅ Pattern Detector - IP 추적
5. ✅ Report Generator - 요약 생성
6. ✅ Report Generator - 텍스트 리포트
7. ✅ 타임스탬프 파싱
8. ✅ 심각도 분류
9. ✅ 모듈 Import
10. ✅ 에러 핸들링

**총 10개 테스트**

---

### 수동 테스트

#### 🖥️ 시스템 모니터링
```bash
# 기본 실행
python scripts/monitoring/system_monitor.py

# 확인 사항
# - CPU/메모리/디스크/네트워크 메트릭 출력
# - 임계치 초과 경고
# - 데이터베이스 저장 확인
```

---

#### 👤 계정 관리
```bash
# 계정 정책 검사
python scripts/account_mgmt/account_checker.py

# 장기 미사용 계정 탐지 (sudo 필요)
sudo python scripts/account_mgmt/inactive_finder.py

# 확인 사항
# - 의심스러운 계정 탐지
# - 장기 미사용 계정 목록
# - 데이터베이스 알림 저장
```

---

### 단위 테스트
```bash
# 설정 테스트
python config/settings.py

# 로거 테스트
python core/logger.py

# 데이터베이스 테스트
python storage/database.py

# 스케줄러 테스트
python core/scheduler.py
```

---

## 📊 구현 현황

### Phase 1: 기반 구축 ✅ (100%)

- [x] 크로스 플랫폼 설정 관리
- [x] 로깅 시스템
- [x] 데이터베이스 ORM
- [x] 작업 스케줄러
- [x] 작업 실행기

### Phase 2: 자동화 스크립트 🔄 (75%)

#### 시스템 모니터링 ✅
- [x] CPU/메모리/디스크 사용률
- [x] 네트워크 트래픽
- [x] 임계치 기반 알림
- [ ] 자동화 테스트 스크립트

#### 보안 점검 ✅ (100% 테스트)
- [x] 종합 보안 점검
- [x] 포트 스캔 (멀티스레드)
- [x] 파일 권한 검사
- [x] SSH 설정 검사
- [x] 보안 점수 산출
- [x] 자동화 테스트 스크립트 ✅

#### 로그 분석 ✅ (100% 테스트)
- [x] 실시간 로그 감시
- [x] 17가지 패턴 탐지
- [x] 이상 패턴 탐지
- [x] 시간대별 분석
- [x] IP 추적
- [x] 리포트 생성
- [x] 자동화 테스트 스크립트 ✅

#### 계정 관리 ✅
- [x] 계정 정책 검사
- [x] UID 0 계정 탐지
- [x] sudo 권한 이상 탐지
- [x] 장기 미사용 계정 탐지
- [ ] 비밀번호 만료 임박 탐지
- [ ] 비밀번호 정책 검증
- [ ] 자동화 테스트 스크립트

#### 백업 및 유지보수 📋
- [ ] 자동 백업
- [ ] 디스크 정리
- [ ] 시스템 헬스체크

### Phase 3: 알림 시스템 📋 (0%)

- [ ] 이메일 알림 (SMTP)
- [ ] Slack 웹훅
- [ ] Discord 웹훅
- [ ] 알림 템플릿
- [ ] 중복 알림 방지

### Phase 4: 웹 대시보드 📋 (0%)

- [ ] FastAPI REST API
- [ ] 작업 관리 API (CRUD)
- [ ] 실행 이력 조회
- [ ] 실시간 로그 스트리밍
- [ ] 프론트엔드 UI
- [ ] 대시보드 차트

---

## 🗺️ 개발 로드맵

### 2025년 9월 (분석 및 설계)
- [x] 자동화 대상 선정
- [x] 시스템 아키텍처 설계
- [x] 기술 스택 결정
- [x] 프로젝트 구조 설계

### 2025년 10월 (환경 구축 및 개발)
- [x] Git 저장소 구축
- [x] 기반 인프라 개발
- [x] 시스템 모니터링 스크립트
- [x] 보안 점검 스크립트 + 테스트 ✅
- [x] 로그 분석 스크립트 + 테스트 ✅
- [x] 계정 관리 스크립트 (90%)

### 2025년 11월 (테스트 및 시범 적용)
- [ ] 나머지 스크립트 테스트 자동화
- [ ] 통합 테스트
- [ ] 알림 시스템 개발
- [ ] 웹 대시보드 개발
- [ ] 시범 운영

### 2025년 12월 (확대 적용 및 고도화)
- [ ] 운영 서버 배포
- [ ] 모니터링 및 안정화
- [ ] 성과 측정
- [ ] 최종 보고서 작성

---

## 📚 문서

- [프로젝트 요약](PROJECT_SUMMARY.md)
- [**테스트 현황** 📊](SCRIPT_TEST_STATUS.md)
- [시스템 모니터링 가이드](scripts/monitoring/README.md)
- [보안 점검 가이드](scripts/security/README.md)
- [로그 분석 가이드](scripts/log_analysis/README.md)
- [로그 분석 테스트 가이드](scripts/log_analysis/TEST_GUIDE.md)
- [계정 관리 가이드](scripts/account_mgmt/README.md)

---

## 🔍 데이터베이스 조회

### 작업 목록
```bash
sqlite3 data/automation.db "SELECT id, name, enabled, cron_expression FROM jobs;"
```

### 실행 이력 (최근 10개)
```bash
sqlite3 data/automation.db "
SELECT job_id, status, started_at, finished_at 
FROM job_executions 
ORDER BY started_at DESC 
LIMIT 10;
"
```

### 알림 조회 (보안 관련)
```bash
sqlite3 data/automation.db "
SELECT title, level, sent_at 
FROM notifications 
WHERE channel LIKE '%security%' 
ORDER BY sent_at DESC 
LIMIT 10;
"
```

### 알림 조회 (계정 관련)
```bash
sqlite3 data/automation.db "
SELECT title, level, sent_at 
FROM notifications 
WHERE channel LIKE '%account%' 
ORDER BY sent_at DESC 
LIMIT 10;
"
```

### 시스템 메트릭 (최근 10개)
```bash
sqlite3 data/automation.db "
SELECT timestamp, cpu_percent, memory_percent, disk_percent 
FROM system_metrics 
ORDER BY timestamp DESC 
LIMIT 10;
"
```

---

## 🐛 알려진 이슈

1. **Windows에서 일부 로그 파일 접근 불가**
   - 해결: 관리자 권한으로 실행

2. **Linux에서 pywin32 설치 오류**
   - 해결: Windows 전용 모듈이므로 무시

3. **python-nmap 설치 오류**
   - 해결: nmap이 먼저 설치되어 있어야 함
   ```bash
   # Ubuntu/Debian
   sudo apt-get install nmap
   
   # Windows
   # https://nmap.org/download.html에서 설치
   ```

4. **테스트 스크립트 실행 권한 오류**
   - 해결: 실행 권한 부여
   ```bash
   chmod +x scripts/security/test_security.sh
   chmod +x scripts/log_analysis/*.sh
   ```

---

## 🤝 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

---

## 📞 문의

**팀 1조** - 정보보안학과

- **팀장**: 남수민 (2184039)
- **팀원**: 김규민 (2084002)
- **팀원**: 임준호 (2184)

**지도교수**: 이병엽

**프로젝트 링크**: [https://github.com/Vampirk/automation-platform](https://github.com/Vampirk/automation-platform)

---

## 🙏 감사의 말

이 프로젝트는 정보보안학과 캡스톤 디자인 과제로 진행되었습니다.  
지도해주신 이병엽 교수님께 감사드립니다.

---

## 📈 프로젝트 통계

- **총 스크립트**: 9개
- **테스트 완료**: 6개 (67%)
- **자동화 테스트**: 19개
- **코드 라인 수**: ~3,500줄
- **문서 페이지**: 8개

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!**
