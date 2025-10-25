# 🤖 Automation Platform

보안 운영 및 시스템 관리 작업 자동화 플랫폼

## 📋 개요

반복적인 보안 운영 및 시스템 관리 작업을 자동화하여 휴먼 에러를 최소화하고,
보안 담당자가 고부가가치 업무에 집중할 수 있도록 지원하는 플랫폼입니다.

### 주요 기능

- ✅ **크로스 플랫폼 지원**: Windows/Linux 모두에서 동작
- ⏰ **Cron 스타일 스케줄링**: 유연한 작업 스케줄 설정
- 🔄 **자동 재시도**: 실패 시 자동 재시도 메커니즘
- 📊 **실행 이력 관리**: 모든 작업 실행 결과 저장
- 📝 **구조화된 로깅**: 상세한 로그 기록 및 분석
- 🖥️ **시스템 모니터링**: CPU/메모리/디스크 사용률 체크
- 🚨 **임계치 알림**: 설정된 임계치 초과 시 자동 알림

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# Python 3.10+ 필요
python --version

# pipenv 설치 (없는 경우)
pip install pipenv

# 의존성 설치
cd automation-platform
pipenv install

# 개발 의존성 포함 설치
pipenv install --dev
```

### 2. 환경 변수 설정

`.env` 파일을 수정하여 필요한 설정을 변경하세요:

```bash
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

### 3. 실행

```bash
# pipenv 가상환경에서 실행
pipenv run python main.py

# 또는 가상환경 활성화 후 실행
pipenv shell
python main.py
```

## 📁 프로젝트 구조

```
automation-platform/
├── main.py                 # 메인 진입점
├── config/                 # 설정 관리
│   ├── __init__.py
│   └── settings.py        # 전역 설정
├── core/                   # 핵심 엔진
│   ├── __init__.py
│   ├── logger.py          # 로깅 시스템
│   ├── scheduler.py       # 작업 스케줄러
│   └── executor.py        # 작업 실행기
├── storage/                # 데이터 저장
│   ├── __init__.py
│   ├── database.py        # DB 연결 관리
│   └── models.py          # 데이터 모델
├── scripts/                # 자동화 스크립트
│   ├── monitoring/        # 시스템 모니터링
│   │   └── system_monitor.py
│   ├── security/          # 보안 점검
│   ├── log_analysis/      # 로그 분석
│   └── account_mgmt/      # 계정 관리
├── notification/           # 알림 시스템
├── logs/                   # 로그 파일
├── data/                   # 데이터베이스 파일
├── .env                    # 환경 변수
└── Pipfile                 # 의존성 정의
```

## 🔧 사용 방법

### 작업 등록

데이터베이스에 직접 작업을 등록할 수 있습니다:

```python
from storage import db, Job, JobType

with db.session_scope() as session:
    job = Job(
        name="my_custom_job",
        description="커스텀 작업 설명",
        job_type=JobType.CUSTOM,
        script_path="scripts/my_script.py",
        cron_expression="0 * * * *",  # 매시간
        enabled=True,
        timeout_seconds=300,
        priority=5
    )
    session.add(job)
```

### Cron 표현식 예시

```
*/5 * * * *     # 5분마다
0 * * * *       # 매시간 정각
0 0 * * *       # 매일 자정
0 0 * * 0       # 매주 일요일 자정
0 9-17 * * 1-5  # 월~금 오전 9시~오후 5시
```

### 스크립트 작성 가이드

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger

logger = get_logger()

def main():
    logger.info("스크립트 시작")
    
    # 작업 수행
    # ...
    
    logger.info("스크립트 완료")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
```

## 🛠️ 개발

### 테스트 실행

```bash
# 설정 테스트
pipenv run python config/settings.py

# 로거 테스트
pipenv run python core/logger.py

# 데이터베이스 테스트
pipenv run python storage/database.py

# 스케줄러 테스트
pipenv run python core/scheduler.py

# 실행기 테스트
pipenv run python core/executor.py

# 시스템 모니터 테스트
pipenv run python scripts/monitoring/system_monitor.py
```

### 코드 품질

```bash
# 코드 포맷팅
pipenv run black .

# 린팅
pipenv run flake8 .

# 타입 체크
pipenv run mypy .
```

## 📊 모니터링

### 로그 확인

```bash
# 실시간 로그 보기
tail -f logs/automation.log

# 에러 로그만 보기
grep "ERROR" logs/automation.log

# 특정 작업 로그 검색
grep "job_id=123" logs/automation.log
```

### 데이터베이스 조회

```bash
# SQLite 데이터베이스 열기
sqlite3 data/automation.db

# 작업 목록 조회
SELECT * FROM jobs;

# 실행 이력 조회
SELECT * FROM job_executions ORDER BY started_at DESC LIMIT 10;

# 시스템 메트릭 조회
SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10;
```

## 🎯 로드맵

### Phase 1: 핵심 기능 (완료) ✅
- [x] 크로스 플랫폼 지원
- [x] 작업 스케줄러
- [x] 작업 실행기
- [x] 로깅 시스템
- [x] 데이터베이스 관리
- [x] 시스템 모니터링 스크립트

### Phase 2: 자동화 스크립트 (진행 중)
- [ ] 로그 분석 스크립트
- [ ] 보안 점검 스크립트
- [ ] 계정 관리 스크립트
- [ ] CVE 스캔 스크립트

### Phase 3: 알림 및 대시보드
- [ ] 이메일 알림
- [ ] Slack 알림
- [ ] 웹 대시보드
- [ ] REST API

### Phase 4: 고도화
- [ ] 분산 실행 지원
- [ ] 플러그인 시스템
- [ ] AI 기반 이상 탐지

## 🐛 트러블슈팅

### Windows에서 실행 시 주의사항

1. PowerShell 실행 정책 설정:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

2. 긴 경로 지원 활성화:
```
레지스트리 편집기 > HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem
LongPathsEnabled = 1
```

### Linux에서 실행 시 주의사항

1. 스크립트 실행 권한:
```bash
chmod +x scripts/**/*.py
```

2. Python 경로 확인:
```bash
which python3
```

## 📝 라이선스

이 프로젝트는 교육 목적의 캡스톤 디자인 프로젝트입니다.

## 👥 팀원

- 남수민 (2184039) - 팀장
- 김규민 (2084002)
- 임준호 (2184XXX)

## 📧 문의

프로젝트 관련 문의사항은 이슈로 등록해주세요.
