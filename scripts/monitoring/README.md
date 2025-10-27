# 🖥️ 시스템 모니터링 스크립트 (System Monitoring Scripts)

시스템 리소스(CPU, 메모리, 디스크, 네트워크)를 모니터링하고 임계치 초과 시 알림을 생성하는 스크립트입니다.

**작성자:** 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)  
**작성일:** 2025-10-25  
**최종 수정:** 2025-10-27 (알림 시스템 통합)  
**상태:** ✅ 완료

---

## 📁 파일 구조

```
scripts/monitoring/
├── __init__.py              # 패키지 초기화
├── system_monitor.py        # 시스템 모니터링 메인 스크립트
└── README.md               # 이 파일
```

---

## 🎯 주요 기능

### system_monitor.py ✅

**시스템 리소스 모니터링 및 알림 생성**

**모니터링 항목:**
- ✅ CPU 사용률 (퍼센트, 코어 수)
- ✅ 메모리 사용률 (퍼센트, 사용량/전체)
- ✅ 디스크 사용률 (퍼센트, 사용량/전체)
- ✅ 네트워크 트래픽 (송신/수신 MB)

**임계치 체크:**
- CPU 임계치: 80% (기본값, `.env`에서 설정 가능)
- 메모리 임계치: 85% (기본값)
- 디스크 임계치: 90% (기본값)

**알림 레벨:**
- **WARNING**: 임계치 초과 (80-95%)
- **CRITICAL**: 심각한 수준 (95%+)

**데이터 저장:**
- `system_metrics` 테이블: 모든 메트릭 저장
- `notifications` 테이블: 임계치 초과 시 알림 저장

**출력 예시:**
```
============================================================
📊 SYSTEM MONITORING REPORT
============================================================
Timestamp: 2025-10-27 14:20:00
Hostname: server01
Platform: linux

📈 Current Metrics:
   CPU:      45.2% (8 cores)
   Memory:   68.5% (5.50GB / 8.00GB)
   Disk:     72.3% (145.00GB / 200.00GB)
   Network: ↑ 1024.50MB / ↓ 2048.30MB

⚙️  Thresholds:
   CPU:    80%
   Memory: 85%
   Disk:   90%

✅ All metrics within normal range
============================================================
```

**알림 예시 (임계치 초과 시):**
```
============================================================
🚨 Alerts: 2 issue(s) detected
   ⚠️  [WARNING] CPU usage is 85.5% (threshold: 80%)
   🔴 [CRITICAL] Memory usage is 96.2% (7.70GB / 8.00GB, threshold: 85%)
============================================================
```

---

## 🚀 사용 방법

### 사전 준비

#### 1. 의존성 설치
```bash
pip install psutil
```

#### 2. 환경 설정

`.env` 파일에서 임계치 설정:

```env
# 모니터링 임계치
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
```

### 실행 방법

#### 1. 수동 실행 (1회)

```bash
# 프로젝트 루트에서
python scripts/monitoring/system_monitor.py

# 또는 PYTHONPATH 지정
PYTHONPATH=/path/to/automation-platform python scripts/monitoring/system_monitor.py
```

#### 2. 스케줄러로 자동 실행

메인 애플리케이션의 스케줄러에서 자동 실행:

```bash
# main.py 실행 (스케줄러 포함)
python main.py
```

스케줄 설정 (데이터베이스에 작업 등록):

```python
from storage import db, Job, JobType

with db.session_scope() as session:
    job = Job(
        name="system_monitoring",
        description="System resource monitoring",
        job_type=JobType.MONITORING,
        script_path="scripts/monitoring/system_monitor.py",
        cron_expression="*/5 * * * *",  # 5분마다
        enabled=True,
        timeout_seconds=60
    )
    session.add(job)
```

#### 3. Cron으로 실행 (Linux)

```bash
# crontab 편집
crontab -e

# 5분마다 실행 추가
*/5 * * * * cd /path/to/automation-platform && python scripts/monitoring/system_monitor.py >> logs/monitoring.log 2>&1
```

#### 4. Task Scheduler로 실행 (Windows)

1. "작업 스케줄러" 열기
2. "기본 작업 만들기" 클릭
3. 트리거: 5분마다
4. 작업: Python 실행
   - 프로그램: `python.exe`
   - 인수: `scripts\monitoring\system_monitor.py`
   - 시작 위치: `C:\path\to\automation-platform`

---

## 📊 출력 및 저장

### 1. 콘솔 출력

실행 시 리포트가 콘솔에 출력됩니다:
- 현재 메트릭 값
- 임계치 설정
- 경고 및 알림 (있는 경우)

### 2. 데이터베이스 저장

**system_metrics 테이블:**
```sql
SELECT 
    timestamp, 
    hostname, 
    cpu_percent, 
    memory_percent, 
    disk_percent 
FROM system_metrics 
ORDER BY timestamp DESC 
LIMIT 10;
```

**notifications 테이블 (알림):**
```sql
SELECT 
    title, 
    level, 
    message, 
    sent_at 
FROM notifications 
WHERE channel = 'system_monitoring' 
ORDER BY sent_at DESC 
LIMIT 10;
```

### 3. 로그 파일

`logs/automation.log`에 상세 로그 기록:
```
2025-10-27 14:20:00 | INFO | System Monitoring Started
2025-10-27 14:20:01 | DEBUG | Metrics collected: CPU=45.2%, Memory=68.5%, Disk=72.3%
2025-10-27 14:20:01 | DEBUG | Metrics saved to database
2025-10-27 14:20:01 | INFO | System Monitoring Completed
```

---

## 🔗 다른 시스템과 통합

### 1. 웹 대시보드 연동

프론트엔드 대시보드에서 자동으로 표시:

- **실시간 메트릭**: `/monitoring/metrics/current` API
- **메트릭 이력**: `/monitoring/metrics` API
- **알림 목록**: `/monitoring/notifications` API

브라우저에서 확인: http://localhost:8080

### 2. API 조회

```bash
# 현재 시스템 메트릭
curl http://localhost:8000/monitoring/metrics/current

# 최근 메트릭 (10개)
curl http://localhost:8000/monitoring/metrics?limit=10

# 모니터링 알림 (최근 10개)
curl "http://localhost:8000/monitoring/notifications?channel=system_monitoring&limit=10"
```

### 3. 다른 스크립트와 동일 구조

모든 스크립트가 동일한 알림 시스템 사용:

```python
# 보안 스크립트
notification = Notification(
    channel="security_check",
    level="WARNING",
    # ...
)

# 로그 분석 스크립트
notification = Notification(
    channel="log_analysis",
    level="ERROR",
    # ...
)

# 시스템 모니터링 (이 스크립트)
notification = Notification(
    channel="system_monitoring",
    level="CRITICAL",
    # ...
)
```

---

## ⚙️ 설정 가능한 옵션

### 환경 변수 (.env)

```env
# CPU 임계치 (%)
CPU_THRESHOLD=80

# 메모리 임계치 (%)
MEMORY_THRESHOLD=85

# 디스크 임계치 (%)
DISK_THRESHOLD=90

# 로그 레벨
LOG_LEVEL=INFO

# 데이터베이스
DATABASE_URL=sqlite:///./data/automation.db
```

### 코드 수정

임계치별 동작 변경:

```python
# system_monitor.py에서
def check_thresholds(self, metrics: Dict) -> List[Dict]:
    # CPU 체크
    if metrics['cpu_percent'] > self.thresholds['cpu']:
        # WARNING: 80-95%
        # CRITICAL: 95%+
        level = 'CRITICAL' if metrics['cpu_percent'] > 95 else 'WARNING'
        # ...
```

---

## 🧪 테스트

### 수동 테스트

```bash
# 1. 정상 실행 확인
python scripts/monitoring/system_monitor.py

# 2. 데이터베이스 확인
sqlite3 data/automation.db "SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 1;"

# 3. 알림 확인 (임계치 초과 시)
sqlite3 data/automation.db "SELECT * FROM notifications WHERE channel='system_monitoring' ORDER BY sent_at DESC LIMIT 1;"
```

### 임계치 테스트

임계치를 낮춰서 알림 발생 테스트:

```bash
# .env 파일에서 임계치를 10%로 낮춤
CPU_THRESHOLD=10
MEMORY_THRESHOLD=10
DISK_THRESHOLD=10

# 실행하면 알림 발생
python scripts/monitoring/system_monitor.py
```

### 스트레스 테스트 (선택)

CPU/메모리 부하를 인위적으로 생성:

```bash
# CPU 부하 (Linux)
stress --cpu 8 --timeout 60s

# 메모리 부하 (Linux)
stress --vm 1 --vm-bytes 6G --timeout 60s

# 그 동안 모니터링 실행
python scripts/monitoring/system_monitor.py
```

---

## 📈 성능 및 리소스 사용

- **실행 시간**: 약 1-2초
- **메모리 사용**: 약 20-30MB
- **CPU 사용**: 거의 없음 (1% 미만)
- **디스크 I/O**: 최소 (메트릭 1개 저장)

**권장 실행 주기:**
- 일반 모니터링: 5분마다
- 중요 서버: 1분마다
- 개발 환경: 10분마다

---

## 🔍 트러블슈팅

### 1. psutil 설치 오류

**문제:**
```
ModuleNotFoundError: No module named 'psutil'
```

**해결:**
```bash
pip install psutil
```

### 2. 권한 오류 (Linux)

**문제:**
```
Permission denied: '/proc/...'
```

**해결:**
일부 시스템 정보는 root 권한 필요:
```bash
sudo python scripts/monitoring/system_monitor.py
```

### 3. 데이터베이스 오류

**문제:**
```
OperationalError: unable to open database file
```

**해결:**
```bash
# 데이터베이스 초기화
python -c "from storage import init_database; init_database()"

# 권한 확인
chmod 664 data/automation.db
```

### 4. 메트릭 수집 실패

**문제:**
특정 메트릭을 가져올 수 없음

**해결:**
- CPU: `psutil.cpu_percent(interval=1)` - interval 필수
- 디스크: Windows에서는 `C:/` 사용
- 네트워크: 가상 인터페이스는 제외됨

---

## 🚀 향후 개선 사항

- [ ] 프로세스별 리소스 사용률 추적
- [ ] GPU 사용률 모니터링 (NVIDIA)
- [ ] 온도 센서 모니터링
- [ ] 네트워크 인터페이스별 통계
- [ ] 커스텀 임계치 (사용자별)
- [ ] 이메일/Slack 알림 통합
- [ ] 트렌드 분석 (주간/월간)
- [ ] 예측 분석 (머신러닝)

---

## 📚 참고 자료

- [psutil 문서](https://psutil.readthedocs.io/)
- [시스템 모니터링 베스트 프랙티스](https://www.brendangregg.com/systems-performance-2nd-edition-book.html)

---

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

---

**💡 Tip:** 
- 프론트엔드 대시보드에서 실시간으로 메트릭을 확인할 수 있습니다
- 알림은 자동으로 데이터베이스에 저장되며 대시보드에서 확인 가능합니다
- 임계치는 `.env` 파일에서 쉽게 조정할 수 있습니다
