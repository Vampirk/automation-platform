# 👥 계정 관리 스크립트 (Account Management Scripts)

사용자 계정 정책 검증, 장기 미사용 계정 탐지, 비밀번호 정책 검사를 자동화하는 스크립트 모음입니다.

**작성자:** 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)  
**작성일:** 2025-10-26  
**상태:** ✅ 완료

---

## 📁 파일 구조

```
scripts/account_mgmt/
├── __init__.py              # 패키지 초기화
├── account_checker.py       # 계정 정책 검사
├── inactive_finder.py       # 장기 미사용 계정 탐지
├── password_policy.py       # 비밀번호 정책 검사
└── README.md               # 이 파일
```

---

## 🎯 주요 기능

### 1. account_checker.py ✅
**계정 정책 검사 및 의심스러운 계정 탐지**

**기능:**
- 모든 사용자 계정 조회 (시스템/사용자 계정 구분)
- UID 0 계정 탐지 (root 제외)
- sudo/admin 그룹 멤버 확인
- 쉘 접근 가능 계정 확인
- 의심스러운 계정 자동 탐지
- 통계 및 리포트 생성
- 데이터베이스에 알림 저장

**탐지 항목 (Linux):**
- UID 0인 비root 계정
- 이상한 쉘을 가진 사용자 계정
- 시스템 UID(< 1000)인데 /home/ 디렉토리를 가진 계정
- sudo 권한을 가진 시스템 계정

**탐지 항목 (Windows):**
- Administrators 그룹에 속한 일반 사용자 계정
- 비활성화되지 않은 오래된 계정

**출력 예시:**
```
============================================================
👥 Account Policy Check Report
============================================================
Platform: LINUX
Total Accounts: 45
  User Accounts: 5
  System Accounts: 38
  Admin/Sudo Accounts: 3

🚨 Suspicious Accounts: 1

  ⚠️  testuser
      - System UID with user home directory
      UID: 999, Shell: /bin/bash
============================================================
```

### 2. inactive_finder.py ✅
**장기 미사용 계정 탐지**

**기능:**
- 최근 로그인 시간 조회 (lastlog)
- 90일 이상 미로그인 계정 탐지
- 한 번도 로그인하지 않은 계정 탐지
- 로그인 이력 분석
- 자동 비활성화 추천
- 통계 및 리포트 생성
- 데이터베이스에 알림 저장

**탐지 기준:**
- 미사용 기준: 90일 이상 로그인 없음
- 시스템 계정 제외 (UID < 1000)
- 로그인 불가 계정 제외 (nologin, false 쉘)

**출력 예시:**
```
============================================================
🔍 Inactive Account Report
============================================================
Platform: LINUX
Inactive Threshold: 90 days

Inactive Accounts: 2
Never Logged In: 3

⚠️  Long-term Inactive Accounts (90+ days):

  👤 olduser
     Days Inactive: 145
     Last Login: 2025-06-03 14:23:45
     Home: /home/olduser

💤 Never Logged In Accounts:
  - testuser1
  - testuser2
  - demo

💡 Recommendation:
   Consider disabling or removing long-term inactive accounts
   Review and remove unused accounts created but never used
============================================================
```

### 3. password_policy.py ✅
**비밀번호 정책 검사**

**기능:**
- 비밀번호 만료 임박 계정 탐지 (7일 이내)
- 만료된 비밀번호 계정 확인
- 비밀번호 정책 검증 (/etc/login.defs)
- shadow 파일 분석
- 비밀번호 변경 알림
- 통계 및 리포트 생성
- 데이터베이스에 알림 저장

**검사 항목:**
- PASS_MAX_DAYS: 비밀번호 최대 사용 일수
- PASS_MIN_DAYS: 비밀번호 최소 사용 일수
- PASS_MIN_LEN: 비밀번호 최소 길이
- PASS_WARN_AGE: 만료 경고 일수

**출력 예시:**
```
============================================================
🔐 Password Policy Report
============================================================
Platform: LINUX

📋 Current Policy:
   Max Days: 90
   Min Days: 1
   Min Length: 8
   Warning Days: 7

Expiry Warning Threshold: 7 days
Expiring Soon: 2
Already Expired: 1

🚨 CRITICAL - Expired Passwords:

  ⛔ expireduser
     Expired: 15 days ago
     Expiry Date: 2025-10-11

⚠️  Passwords Expiring Soon:

  👤 user1
     Days Until Expiry: 3
     Expiry Date: 2025-10-29

  👤 user2
     Days Until Expiry: 5
     Expiry Date: 2025-10-31

💡 Recommendation:
   Force password change for expired accounts immediately
   Notify users to change passwords before expiry
============================================================
```

---

## 🚀 사용 방법

### 사전 준비

#### 1. 권한 설정
```bash
# Linux: root 권한 필요 (shadow 파일 접근)
sudo chmod +r /etc/shadow

# Windows: 관리자 권한 PowerShell 필요
```

#### 2. 의존성 확인
```bash
# Linux 전용 명령어
which lastlog
which passwd

# Windows의 경우 pywin32 필요
pip install pywin32
```

### 실행 방법

#### 1. 계정 정책 검사
```bash
# Linux
sudo python scripts/account_mgmt/account_checker.py

# 또는 PYTHONPATH 설정
sudo PYTHONPATH=/path/to/automation-platform python scripts/account_mgmt/account_checker.py

# Windows (관리자 권한 PowerShell)
python scripts\account_mgmt\account_checker.py
```

**출력 정보:**
- 전체 계정 수 (사용자/시스템/관리자 계정)
- 의심스러운 계정 목록 및 이슈
- 플랫폼별 세부 정보

#### 2. 장기 미사용 계정 탐지
```bash
# Linux
sudo python scripts/account_mgmt/inactive_finder.py

# Windows
python scripts\account_mgmt\inactive_finder.py
```

**출력 정보:**
- 90일 이상 미사용 계정
- 한 번도 로그인하지 않은 계정
- 각 계정의 마지막 로그인 시간
- 미사용 일수

#### 3. 비밀번호 정책 검사
```bash
# Linux
sudo python scripts/account_mgmt/password_policy.py

# Windows
python scripts\account_mgmt\password_policy.py
```

**출력 정보:**
- 현재 비밀번호 정책
- 7일 이내 만료 예정 계정
- 이미 만료된 계정
- 각 계정의 만료일 및 남은 일수

---

## 🔧 설정 및 커스터마이징

### 미사용 계정 기준 변경

`inactive_finder.py` 파일에서 기준 일수 수정:

```python
class InactiveAccountFinder:
    INACTIVE_DAYS = 90  # 기본값: 90일
    # 예: 180일로 변경 → INACTIVE_DAYS = 180
```

### 비밀번호 만료 경고 기준 변경

`password_policy.py` 파일에서 경고 일수 수정:

```python
class PasswordPolicyChecker:
    EXPIRY_WARNING_DAYS = 7  # 기본값: 7일
    # 예: 14일로 변경 → EXPIRY_WARNING_DAYS = 14
```

### 시스템 계정 제외 UID 변경

`account_checker.py` 및 `inactive_finder.py`에서:

```python
# 시스템 계정 제외 (UID < 1000)
if uid < 1000:  # Linux 기본값
    continue

# 예: UID < 500으로 변경 (일부 시스템)
if uid < 500:
    continue
```

---

## 📅 스케줄러 등록

### 데이터베이스에 작업 등록

```python
from storage import db, Job, JobType

with db.session_scope() as session:
    # 매일 자정 계정 검사
    account_job = Job(
        name="daily_account_check",
        description="일일 계정 정책 검사",
        job_type=JobType.ACCOUNT,
        script_path="scripts/account_mgmt/account_checker.py",
        cron_expression="0 0 * * *",  # 매일 자정
        enabled=True,
        timeout_seconds=300
    )
    session.add(account_job)
    
    # 매주 월요일 장기 미사용 계정 검사
    inactive_job = Job(
        name="weekly_inactive_check",
        description="주간 미사용 계정 검사",
        job_type=JobType.ACCOUNT,
        script_path="scripts/account_mgmt/inactive_finder.py",
        cron_expression="0 1 * * 1",  # 매주 월요일 1시
        enabled=True,
        timeout_seconds=300
    )
    session.add(inactive_job)
    
    # 매주 비밀번호 정책 검사
    password_job = Job(
        name="weekly_password_check",
        description="주간 비밀번호 정책 검사",
        job_type=JobType.ACCOUNT,
        script_path="scripts/account_mgmt/password_policy.py",
        cron_expression="0 2 * * 1",  # 매주 월요일 2시
        enabled=True,
        timeout_seconds=300
    )
    session.add(password_job)
```

### Cron 표현식 예시

```bash
# 매일 자정
0 0 * * *

# 매주 월요일 오전 2시
0 2 * * 1

# 매월 1일 오전 3시
0 3 1 * *

# 매일 오전 9시, 오후 6시
0 9,18 * * *

# 평일 오전 10시
0 10 * * 1-5
```

---

## 📊 데이터베이스 조회

### 계정 관리 알림 조회

```bash
# 의심스러운 계정 알림
sqlite3 data/automation.db "
SELECT title, message, level, sent_at 
FROM notifications 
WHERE channel = 'account_check' 
ORDER BY sent_at DESC 
LIMIT 10;
"

# 장기 미사용 계정 알림
sqlite3 data/automation.db "
SELECT title, message, level, sent_at 
FROM notifications 
WHERE channel = 'account_inactive' 
ORDER BY sent_at DESC 
LIMIT 10;
"

# 비밀번호 만료 알림
sqlite3 data/automation.db "
SELECT title, message, level, sent_at 
FROM notifications 
WHERE channel = 'password_policy' 
ORDER BY sent_at DESC 
LIMIT 10;
"

# 최근 7일 간 모든 계정 관련 알림
sqlite3 data/automation.db "
SELECT title, message, level, channel, sent_at 
FROM notifications 
WHERE channel IN ('account_check', 'account_inactive', 'password_policy')
  AND sent_at >= datetime('now', '-7 days')
ORDER BY sent_at DESC;
"
```

---

## 🐛 문제 해결

### 1. Permission denied 에러

**문제:**
```
PermissionError: [Errno 13] Permission denied: '/etc/shadow'
```

**해결:**
```bash
# Linux: sudo로 실행
sudo python scripts/account_mgmt/account_checker.py

# Windows: 관리자 권한 PowerShell에서 실행
```

### 2. spwd 모듈을 찾을 수 없음 (Windows)

**문제:**
```
ModuleNotFoundError: No module named 'spwd'
```

**해결:**
- spwd는 Linux 전용 모듈입니다
- Windows에서는 자동으로 win32 모듈을 사용합니다
- pywin32 설치: `pip install pywin32`

### 3. lastlog 명령을 찾을 수 없음

**문제:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'lastlog'
```

**해결:**
```bash
# lastlog 설치
sudo apt-get install login  # Debian/Ubuntu
sudo yum install util-linux  # CentOS/RHEL

# 경로 확인
which lastlog
```

### 4. 데이터베이스 연결 오류

**문제:**
```
OperationalError: unable to open database file
```

**해결:**
```bash
# 데이터베이스 초기화
python storage/database.py

# 또는 main.py 실행으로 자동 초기화
python main.py
```

### 5. 계정 정보가 표시되지 않음

**문제:**
- 출력에 계정이 0개로 표시됨

**해결:**
```bash
# 권한 확인
ls -la /etc/passwd
ls -la /etc/shadow

# root 권한으로 실행
sudo python scripts/account_mgmt/account_checker.py
```

---

## 📝 테스트

### 단위 테스트
```bash
# 각 스크립트 개별 실행
sudo python scripts/account_mgmt/account_checker.py
sudo python scripts/account_mgmt/inactive_finder.py
sudo python scripts/account_mgmt/password_policy.py
```

### 통합 테스트
```bash
# 전체 계정 관리 스크립트 순차 실행
for script in account_checker.py inactive_finder.py password_policy.py; do
    echo "Running $script..."
    sudo python scripts/account_mgmt/$script
    echo "---"
done
```

### 테스트 계정 생성 (테스트용)
```bash
# 테스트 계정 생성
sudo useradd -m -s /bin/bash testuser1
sudo useradd -m -s /bin/bash testuser2

# 90일 이상 미사용으로 설정 (테스트)
sudo chage -d $(date -d "100 days ago" +%Y-%m-%d) testuser1

# 비밀번호 만료 테스트
sudo chage -M 1 testuser2  # 1일 후 만료
echo "testuser2:password" | sudo chpasswd
```

---

## 🎯 향후 계획

- [ ] 웹 대시보드에서 계정 관리 결과 시각화
- [ ] 이메일/Slack 알림 통합
- [ ] 계정 자동 비활성화 기능
- [ ] 계정 변경 이력 추적
- [ ] 정책 위반 자동 복구
- [ ] Active Directory 연동 (Windows)
- [ ] LDAP 지원
- [ ] 다단계 인증(MFA) 상태 확인

---

## 📚 참고 자료

### Linux
- [passwd 명령어](https://linux.die.net/man/1/passwd)
- [lastlog 명령어](https://linux.die.net/man/8/lastlog)
- [/etc/shadow 파일 형식](https://www.cyberciti.biz/faq/understanding-etcshadow-file/)
- [/etc/login.defs](https://man7.org/linux/man-pages/man5/login.defs.5.html)

### Windows
- [Win32 API 문서](https://docs.microsoft.com/en-us/windows/win32/)
- [pywin32 문서](https://github.com/mhammond/pywin32)
- [사용자 계정 관리](https://docs.microsoft.com/en-us/windows/security/identity-protection/)

### 보안 모범 사례
- [NIST 비밀번호 가이드라인](https://pages.nist.gov/800-63-3/)
- [CIS 벤치마크](https://www.cisecurity.org/cis-benchmarks/)

---

## ⚠️ 보안 참고사항

### 중요 권한 요구사항
1. **Linux:** `/etc/shadow` 파일 읽기 권한 (root 필요)
2. **Windows:** 관리자 권한 필요
3. **데이터베이스:** 쓰기 권한 필요

### 권장 사항
- 정기적으로 스크립트 실행 (최소 주 1회)
- 의심스러운 계정 발견 시 즉시 조치
- 장기 미사용 계정은 비활성화 또는 삭제
- 비밀번호 만료 전 사용자에게 통지
- 로그 및 알림 기록 보관

### 주의사항
- 프로덕션 환경에서는 테스트 후 사용
- 계정 삭제 전 백업 필수
- 시스템 계정 수정 시 각별히 주의
- 정책 변경은 보안 팀과 협의 후 진행

---

**💡 Tip:** 스케줄러에 등록하여 자동으로 계정 관리를 수행하세요!
