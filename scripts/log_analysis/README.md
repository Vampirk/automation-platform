# 📋 로그 분석 스크립트 (Log Analysis Scripts)

로그 파일을 실시간으로 감시하고 이상 패턴을 탐지하여 일별/주별 리포트를 생성하는 자동화 스크립트입니다.

**작성자:** 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)  
**작성일:** 2025-10-26

---

## 📁 파일 구조

```
scripts/log_analysis/
├── __init__.py              # 패키지 초기화
├── log_analyzer.py          # 실시간 로그 감시 및 패턴 탐지
├── pattern_detector.py      # 시간대별 분석 및 이상 탐지
├── report_generator.py      # 일별/주별 요약 리포트 생성
└── README.md               # 이 파일
```

---

## 🎯 주요 기능

### 1. log_analyzer.py
**실시간 로그 파일 감시**

- watchdog 라이브러리를 사용한 실시간 파일 변경 감지
- 17가지 로그 패턴 탐지 (실패 로그인, 권한 거부, 메모리 부족 등)
- 심각도별 분류 (CRITICAL, HIGH, MEDIUM, LOW)
- 데이터베이스에 알림 자동 저장
- 통계 생성 및 출력

**탐지 패턴:**
- Failed login (로그인 실패)
- SSH break-in attempt (SSH 침입 시도)
- Permission denied (권한 거부)
- Out of memory (메모리 부족)
- Disk full (디스크 가득 참)
- Service failed (서비스 실패)
- Kernel panic (커널 패닉)
- Segmentation fault (세그먼트 오류)
- 기타 에러/경고/치명적 메시지

### 2. pattern_detector.py
**시간대별 패턴 분석 및 이상 탐지**

- 타임스탬프 자동 추출 (다양한 로그 형식 지원)
- 시간대별(24시간) 활동 패턴 분석
- IP 주소 추출 및 실패 로그인 추적
- 사용자명 추출 및 통계
- 이상 패턴 자동 탐지
- 데이터베이스에 이상 패턴 저장

**이상 패턴 탐지:**
- 반복적인 로그인 실패 (5분 내 5회 이상)
- 새벽 시간대(0-6시) 의심스러운 활동
- 동일 에러 메시지 반복 (10회 이상)
- 특정 사용자의 과다 활동

### 3. report_generator.py
**종합 분석 리포트 생성**

- 일별/주별 로그 분석 요약
- 텍스트 및 JSON 형식 리포트
- 시각적으로 보기 쉬운 통계 표시
- 권장 사항 자동 생성
- 파일로 자동 저장

**리포트 내용:**
- 전체 요약 (분석 라인 수, 매치 수)
- 심각도별 통계
- 상위 탐지 패턴 (Top 10)
- 시간대별 활동
- 실패한 로그인 시도 (Top 10 IP)
- 빈번한 에러 메시지
- 이상 패턴 목록
- 권장 사항

---

## 🚀 사용 방법

### 사전 준비

#### 1. 의존성 설치
```bash
pip install watchdog
```

#### 2. 권한 설정
```bash
# 로그 파일 읽기 권한이 필요합니다 (sudo 권장)
sudo chmod +r /var/log/auth.log
sudo chmod +r /var/log/syslog
```

### 실행 방법

#### 1. 실시간 로그 감시 (60초)
```bash
# 프로젝트 루트에서 실행
PYTHONPATH=/path/to/automation-platform python scripts/log_analysis/log_analyzer.py

# 또는 sudo로 실행 (전체 로그 접근)
sudo PYTHONPATH=/path/to/automation-platform python scripts/log_analysis/log_analyzer.py
```

**출력 예시:**
```
📊 Log Analysis Statistics
============================================================
Total Lines: 12,345
Total Matches: 234

🚨 Severity Summary:
   CRITICAL: 12
   HIGH: 45
   MEDIUM: 89
   LOW: 88

🔝 Top Issues:
   1. failed_login: 45 (HIGH)
   2. error: 89 (MEDIUM)
   3. permission_denied: 23 (MEDIUM)
============================================================
```

#### 2. 패턴 탐지 및 이상 분석
```bash
PYTHONPATH=/path/to/automation-platform python scripts/log_analysis/pattern_detector.py
```

**출력 예시:**
```
🔍 Pattern Analysis Report
======================================================================
⏰ Hourly Summary:
   14:00 - Total:  345, Failed:  12, Error:  23, Warning:  45
   15:00 - Total:  289, Failed:   8, Error:  15, Warning:  32

🌐 Top Failed Login IPs:
   1. 192.168.1.100: 15 attempts
   2. 10.0.0.50: 8 attempts

🚨 Detected Anomalies:
   1. [HIGH] IP 192.168.1.100에서 15회 로그인 실패
   2. [MEDIUM] 동일 에러 12회 반복
======================================================================
```

#### 3. 종합 리포트 생성
```bash
PYTHONPATH=/path/to/automation-platform python scripts/log_analysis/report_generator.py
```

리포트 파일이 다음 위치에 저장됩니다:
- `reports/logs/log_analysis_report_2025-10-26.txt`
- `reports/logs/log_analysis_report_2025-10-26.json`

---

## 🔧 스케줄러 등록

자동으로 정기적으로 실행하려면 데이터베이스에 작업을 등록하세요.

```python
from storage import db, Job, JobType

with db.session_scope() as session:
    # 매일 자정에 리포트 생성
    job = Job(
        name="daily_log_report",
        description="일일 로그 분석 리포트",
        job_type=JobType.LOG_ANALYSIS,
        script_path="scripts/log_analysis/report_generator.py",
        cron_expression="0 0 * * *",  # 매일 자정
        enabled=True,
        timeout_seconds=600
    )
    session.add(job)
```

---

## 📊 데이터베이스 연동

### 알림 저장
로그 분석 결과는 `notifications` 테이블에 자동으로 저장됩니다.

```sql
SELECT * FROM notifications 
WHERE channel IN ('log_analysis', 'pattern_detection')
ORDER BY sent_at DESC 
LIMIT 10;
```

### 결과 조회
```python
from storage import db
from storage.models import Notification

with db.session_scope() as session:
    # 최근 로그 알림 조회
    recent_alerts = session.query(Notification)\
        .filter(Notification.channel == 'log_analysis')\
        .order_by(Notification.sent_at.desc())\
        .limit(10)\
        .all()
    
    for alert in recent_alerts:
        print(f"[{alert.level}] {alert.title}: {alert.message}")
```

---

## ⚙️ 설정 커스터마이징

### 탐지 패턴 추가
`log_analyzer.py`의 `LogPatterns` 클래스를 수정하세요.

```python
class LogPatterns:
    PATTERNS = {
        # 기존 패턴...
        'custom_pattern': r'YOUR_REGEX_PATTERN',
    }
    
    SEVERITY_MAP = {
        # 기존 맵핑...
        'custom_pattern': 'HIGH',
    }
```

### 이상 탐지 임계치 조정
`pattern_detector.py`의 `PatternDetector` 클래스를 수정하세요.

```python
ANOMALY_THRESHOLDS = {
    'failed_login_count': 10,      # 10회로 변경
    'error_rate': 0.15,            # 15%로 변경
    'repeated_error': 20,          # 20회로 변경
    'suspicious_time': (0, 5),     # 0-5시로 변경
}
```

### 감시할 로그 파일 추가
스크립트의 `main()` 함수에서 로그 파일 목록을 수정하세요.

```python
log_files = [
    '/var/log/auth.log',
    '/var/log/syslog',
    '/var/log/apache2/error.log',    # 추가
    '/var/log/nginx/error.log',      # 추가
]
```

---

## 🐛 문제 해결

### 1. Permission denied 에러
```bash
# 해결: sudo로 실행
sudo PYTHONPATH=/path/to/automation-platform python scripts/log_analysis/log_analyzer.py
```

### 2. watchdog 모듈을 찾을 수 없음
```bash
# 해결: watchdog 설치
pip install watchdog
```

### 3. 로그 파일을 찾을 수 없음
```bash
# 로그 파일 경로 확인
ls -la /var/log/auth.log
ls -la /var/log/syslog

# Windows의 경우 Event Viewer 사용
# 이 스크립트는 Linux 전용입니다
```

### 4. 데이터베이스 연결 오류
```bash
# 데이터베이스 초기화 확인
python storage/database.py

# 또는 main.py 실행으로 자동 초기화
python main.py
```

---

## 📝 테스트

### 단위 테스트
```bash
# log_analyzer 테스트
python -c "
from scripts.log_analysis.log_analyzer import LogAnalyzer
analyzer = LogAnalyzer()
print('LogAnalyzer initialized successfully')
"

# pattern_detector 테스트
python -c "
from scripts.log_analysis.pattern_detector import PatternDetector
detector = PatternDetector()
print('PatternDetector initialized successfully')
"
```

### 통합 테스트
```bash
# 테스트 로그 파일 생성
echo "Oct 26 12:34:56 server sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 12345 ssh2" > /tmp/test.log
echo "Oct 26 12:35:00 server kernel: Out of memory: Kill process 5678" >> /tmp/test.log

# 테스트 로그 분석
PYTHONPATH=/path/to/automation-platform python scripts/log_analysis/log_analyzer.py
```

---

## 🎯 향후 계획

- [ ] 웹 대시보드 연동
- [ ] 실시간 알림 (이메일/Slack)
- [ ] 머신러닝 기반 이상 탐지
- [ ] 그래프/차트 시각화
- [ ] Windows Event Log 지원
- [ ] 원격 로그 서버 지원

---

## 📚 참고 자료

- [watchdog 문서](https://pythonhosted.org/watchdog/)
- [정규표현식 가이드](https://docs.python.org/3/library/re.html)
- [Linux 로그 파일 이해](https://www.loggly.com/ultimate-guide/linux-logging-basics/)

---

**💡 Tip:** 스케줄러에 등록하여 매일 자동으로 리포트를 생성하세요!
