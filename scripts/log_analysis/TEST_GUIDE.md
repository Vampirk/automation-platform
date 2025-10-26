# 🧪 로그 분석 스크립트 테스트 가이드

**작성일:** 2025-10-26  
**작성자:** 1조 (남수민, 김규민, 임준호)

---

## 📦 테스트 스크립트 목록

| 파일 | 실행 시간 | 테스트 수 | 용도 |
|------|----------|----------|------|
| `quick_test.sh` | 5-10초 | 3개 | 빠른 기능 확인 |
| `test_log_analysis.sh` | 30-60초 | 10개 | 전체 통합 테스트 |

---

## 🚀 빠른 시작

### 1️⃣ 빠른 테스트 (권장)

**가장 빠르게 스크립트가 작동하는지 확인:**

```bash
cd ~/automation-platform
./scripts/log_analysis/quick_test.sh
```

**예상 결과:**
```
⚡ 로그 분석 스크립트 빠른 테스트
============================================================

📝 테스트 로그 파일 생성...
✓ 테스트 로그 생성 완료

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Test 1: 기본 패턴 탐지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
총 라인 수: 6
매치된 패턴: 6

상위 패턴:
  - failed_login: 3회 (HIGH)
  - out_of_memory: 1회 (CRITICAL)
  - service_failed: 1회 (HIGH)

✅ Test 1 PASSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Test 2: IP 주소 추적
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
탐지된 의심스러운 IP: 1개
  - 192.168.1.100: 3회 실패

✅ Test 2 PASSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Test 3: 모듈 Import
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 모든 모듈이 성공적으로 import됨
✅ Test 3 PASSED

🗑️  테스트 파일 삭제 완료

============================================================
✅ 빠른 테스트 완료!
============================================================
```

---

### 2️⃣ 전체 통합 테스트

**모든 기능을 철저하게 테스트:**

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
7. ✅ 타임스탬프 파싱 테스트
8. ✅ 심각도 분류 테스트
9. ✅ 모듈 Import 테스트
10. ✅ 에러 핸들링 테스트

**예상 결과:**
```
🧪 로그 분석 스크립트 테스트
============================================================

📁 Checking script files...

✓ log_analyzer.py found
✓ pattern_detector.py found
✓ report_generator.py found

📦 Checking dependencies...

✓ watchdog installed

🔐 Checking user permissions...

⚠ Not running as root
   Note: Some tests may work with test files, but real log analysis requires sudo

📝 Creating test log files...

✓ Test auth.log created (15 lines)
✓ Test syslog created (8 lines)
✓ Test kern.log created (2 lines)

Running tests...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test 1: Log Analyzer - File Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Command: python -c '...'

✓ Analyzed 15 lines
✓ Found 15 matches

✅ Test PASSED

... (나머지 테스트들) ...

============================================================
📊 TEST SUMMARY
============================================================
Total Tests:  10
Passed:       10
Failed:       0

✅ All tests passed!

💡 Next steps:
   1. Test with real log files:
      sudo python scripts/log_analysis/log_analyzer.py
   
   2. Generate a report:
      sudo python scripts/log_analysis/report_generator.py
   
   3. Set up scheduled monitoring:
      Add jobs to database for automated analysis
```

---

## 🔧 실제 로그 파일로 테스트

### Step 1: 실제 로그 분석 (읽기 전용)

```bash
# auth.log 분석
sudo python scripts/log_analysis/log_analyzer.py

# 또는 특정 파일 지정
sudo python -c "
from scripts.log_analysis.log_analyzer import LogAnalyzer
analyzer = LogAnalyzer()
stats = analyzer.analyze_file('/var/log/auth.log')
print(f'Total lines: {stats[\"total_lines\"]:,}')
print(f'Total matches: {stats[\"total_matches\"]:,}')
"
```

### Step 2: 패턴 탐지 테스트

```bash
sudo python scripts/log_analysis/pattern_detector.py
```

### Step 3: 리포트 생성 테스트

```bash
sudo python scripts/log_analysis/report_generator.py
```

생성된 리포트 확인:
```bash
ls -lh reports/logs/
cat reports/logs/log_analysis_report_$(date +%Y-%m-%d).txt
```

---

## 🐛 문제 해결

### ❌ Error: Required scripts not found

**원인:** 잘못된 디렉토리에서 실행

**해결:**
```bash
# 프로젝트 루트로 이동
cd ~/automation-platform

# 또는 절대 경로로 실행
cd /path/to/automation-platform
./scripts/log_analysis/quick_test.sh
```

---

### ❌ watchdog NOT installed

**원인:** watchdog 라이브러리 미설치

**해결:**
```bash
pip install watchdog

# 또는 프로젝트 가상환경에 설치
source venv/bin/activate
pip install watchdog
```

---

### ❌ Permission denied: /var/log/auth.log

**원인:** 로그 파일 읽기 권한 없음

**해결:**
```bash
# sudo로 실행
sudo python scripts/log_analysis/log_analyzer.py

# 또는 읽기 권한 부여
sudo chmod 644 /var/log/auth.log
```

---

### ❌ ModuleNotFoundError: No module named 'scripts'

**원인:** PYTHONPATH 미설정

**해결:**
```bash
# 프로젝트 루트에서 실행
cd ~/automation-platform
python scripts/log_analysis/log_analyzer.py

# 또는 PYTHONPATH 설정
export PYTHONPATH=/path/to/automation-platform:$PYTHONPATH
python scripts/log_analysis/log_analyzer.py
```

---

## ✅ 체크리스트

테스트 전 확인사항:

- [ ] 프로젝트 루트 디렉토리에 있는가?
- [ ] watchdog가 설치되어 있는가? (`pip list | grep watchdog`)
- [ ] Python 3.10+ 버전인가? (`python --version`)
- [ ] 실행 권한이 있는가? (`ls -l scripts/log_analysis/*.sh`)
- [ ] (실제 로그 테스트) sudo 권한이 있는가?

---

## 📊 테스트 스크립트 상세

### quick_test.sh

**실행 시간:** 5-10초  
**목적:** 빠른 기능 확인

**테스트 내용:**
1. **기본 패턴 탐지**
   - 테스트 로그 6줄 생성
   - failed_login, out_of_memory, service_failed 등 탐지
   - 심각도별 분류 확인

2. **IP 주소 추적**
   - 192.168.1.100 IP에서 3회 실패 탐지
   - IP별 카운팅 확인

3. **모듈 Import**
   - LogAnalyzer, PatternDetector, ReportGenerator 모듈
   - 정상 import 확인

---

### test_log_analysis.sh

**실행 시간:** 30-60초  
**목적:** 전체 기능 검증

**테스트 내용:**
1. **파일 분석 (log_analyzer.py)**
   - 15줄 auth.log 테스트 파일 분석
   - 패턴 매치 확인
   - 통계 생성 확인

2. **시간대별 분석 (pattern_detector.py)**
   - 타임스탬프 추출
   - 시간대별 활동 집계
   - hourly_summary 생성

3. **이상 패턴 탐지**
   - 반복 로그인 실패 탐지 (5회 이상)
   - 새벽 시간대 활동 탐지
   - 반복 에러 탐지

4. **IP 추적**
   - 192.168.1.100: 8회 시도
   - 203.0.113.42: 2회 시도
   - 198.51.100.89: 1회 시도

5. **리포트 생성**
   - 전체 요약 생성
   - 텍스트 리포트 포맷
   - JSON 리포트 포맷

6. **타임스탬프 파싱**
   - Oct 26 01:30:00 형식
   - 2025-10-26 12:34:56 형식
   - ISO 8601 형식

7. **심각도 분류**
   - CRITICAL 패턴 확인
   - HIGH 패턴 확인
   - MEDIUM/LOW 패턴 확인

8. **모듈 Import**
   - 모든 모듈 정상 import
   - 순환 의존성 없음

9. **에러 핸들링**
   - 존재하지 않는 파일
   - 권한 없는 파일
   - Graceful degradation

10. **자동 정리**
    - 테스트 로그 파일 삭제
    - 임시 디렉토리 정리

---

## 🎯 다음 단계

테스트가 성공적으로 완료되면:

### 1. 실제 환경 테스트
```bash
# 실제 로그 파일로 분석
sudo python scripts/log_analysis/log_analyzer.py
sudo python scripts/log_analysis/pattern_detector.py
sudo python scripts/log_analysis/report_generator.py
```

### 2. 스케줄러 등록
```python
from storage import db, Job, JobType

with db.session_scope() as session:
    job = Job(
        name="daily_log_analysis",
        description="일일 로그 분석 리포트",
        job_type=JobType.LOG_ANALYSIS,
        script_path="scripts/log_analysis/report_generator.py",
        cron_expression="0 0 * * *",  # 매일 자정
        enabled=True,
        timeout_seconds=600
    )
    session.add(job)
```

### 3. 알림 시스템 연동
```bash
# Phase 3로 진행
# notification/ 디렉토리에 이메일/Slack 알림 구현
```

---

## 💡 참고

- 테스트 스크립트는 **security/test_security.sh** 패턴을 따릅니다
- 색상 코드: 🟢 GREEN (성공), 🔴 RED (실패), 🟡 YELLOW (경고)
- 각 테스트는 독립적으로 실행되며 실패해도 다음 테스트 진행
- 실제 로그 파일은 테스트하지 않으며, 항상 별도의 테스트 파일 생성

---

**🎉 즐거운 테스트 되세요!**
