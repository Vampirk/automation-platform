# 👤 계정 관리 스크립트 (Account Management Scripts)

사용자 계정 정책 검증, 장기 미사용 계정 탐지, 비밀번호 정책 검증을 자동화하는 스크립트 모음입니다.

**작성자:** 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)  
**작성일:** 2025-10-26  
**상태:** ✅ 정상 작동 확인 완료

---

## 📁 파일 구조

```
scripts/account_mgmt/
├── __init__.py              # 패키지 초기화
├── account_checker.py       # 계정 정책 검사 ✅
├── inactive_finder.py       # 장기 미사용 계정 탐지 ✅
├── password_policy.py       # 비밀번호 정책 검증 📋
└── README.md               # 이 파일
```

**범례:**
- ✅ 구현 완료 및 테스트 완료
- 📋 예정

---

## 🎯 주요 기능

### 1. account_checker.py ✅
**계정 정책 검사기 (Account Checker)**

시스템의 모든 사용자 계정을 조회하고 정책 위반 계정을 자동으로 탐지합니다.

#### 기능
- **전체 계정 조회**: Linux(/etc/passwd) 또는 Windows(NetUserEnum) 기반
- **계정 분류**: 시스템 계정 vs 사용자 계정
- **관리자 권한 확인**: sudo/Administrator 그룹 멤버십 검증
- **의심스러운 계정 탐지**:
  - UID 0인 비root 계정
  - sudo 권한이 있는 시스템 계정
  - 이상한 쉘을 가진 사용자 계정
  - 시스템 UID인데 사용자 홈 디렉토리를 가진 계정
  - 관리자 권한이 있는 일반 사용자 (Windows)
- **자동 알림**: 의심스러운 계정 발견 시 데이터베이스에 알림 저장
- **통계 생성**: 전체/사용자/시스템/관리자 계정 수 집계

#### Linux 탐지 패턴
1. **UID 0인 비root 계정**
   ```
   이슈: UID 0 (root privileges)
   위험도: CRITICAL
   설명: root가 아닌 계정이 UID 0을 가지고 있어 root 권한 획득
   ```

2. **이상한 쉘**
   ```
   이슈: Unusual shell
   위험도: MEDIUM
   설명: 사용자 계정인데 /bin/bash, /bin/zsh, /bin/sh가 아닌 쉘 사용
   ```

3. **시스템 UID + 사용자 홈**
   ```
   이슈: System UID with user home directory
   위험도: MEDIUM
   설명: UID < 1000인 시스템 계정이 /home/ 디렉토리 사용
   ```

4. **sudo 권한 시스템 계정**
   ```
   이슈: System account with sudo privileges
   위험도: HIGH
   설명: 시스템 계정이 sudo 권한 보유
   ```

#### Windows 탐지 패턴
1. **관리자 권한 일반 계정**
   ```
   이슈: User account with admin privileges
   위험도: HIGH
   설명: 일반 사용자 계정이 관리자 권한 보유
   ```

### 2. inactive_finder.py ✅
**장기 미사용 계정 탐지기 (Inactive Account Finder)**

일정 기간 동안 로그인하지 않은 계정을 자동으로 탐지합니다.

#### 기능
- **로그인 기록 추적**: 
  - Linux: `/var/log/wtmp`, `lastlog` 기반
  - Windows: `NetUserGetInfo` API 사용
- **장기 미사용 탐지**: 기본 90일 이상 미로그인 계정
- **한 번도 로그인 안 한 계정**: 생성 후 단 한 번도 사용되지 않은 계정
- **자동 알림**: 
  - 장기 미사용: MEDIUM 레벨
  - 한 번도 미로그인: LOW 레벨
- **상세 정보**: 계정명, 마지막 로그인 시각, 미사용 일수

#### 탐지 기준
- **장기 미사용**: 90일 (설정 가능)
- **심각도**: 
  - 180일+: CRITICAL
  - 90-180일: MEDIUM
  - 한 번도 미로그인: LOW

### 3. password_policy.py 📋
**비밀번호 정책 검증기 (Password Policy Checker)** *(개발 예정)*

#### 예정 기능
- 비밀번호 만료 임박 계정 탐지 (7일 이내)
- 비밀번호 복잡도 정책 검증
- 비밀번호 최근 변경 이력 추적
- 기본 비밀번호 사용 계정 탐지
- 비밀번호 정책 위반 통계

---

## 🚀 사용 방법

### 사전 준비

#### 의존성 설치
```bash
# Linux 전용
pip install python-pam  # 선택 사항

# Windows 전용
pip install pywin32
```

#### 권한 설정
```bash
# Linux에서 lastlog, wtmp 읽기 위해 sudo 권한 필요
sudo chmod +r /var/log/wtmp
sudo chmod +r /var/log/lastlog
```

---

### 실행 방법

#### 1. 계정 정책 검사

**Linux:**
```bash
# 프로젝트 루트에서 실행
python scripts/account_mgmt/account_checker.py

# 또는 PYTHONPATH 설정
PYTHONPATH=/path/to/automation-platform python scripts/account_mgmt/account_checker.py
```

**Windows:**
```powershell
# PowerShell에서
python scripts\account_mgmt\account_checker.py

# 또는 관리자 권한으로
# (관리자 계정 정보 접근 시 권장)
```

**출력 예시:**
```
============================================================
👥 Account Policy Checker Started
============================================================

============================================================
📊 ACCOUNT CHECK REPORT
============================================================
Total Accounts: 45
User Accounts: 12
System Accounts: 33
Admin Accounts: 3
Suspicious Accounts: 2

Platform: linux

🚨 Suspicious Accounts:
------------------------------------------------------------
Account: backup_admin
  Username: backup_admin
  UID: 1001
  Group: adm
  Shell: /bin/bash
  Can Login: True
  Is Sudoer: True
  Type: user
  Issues:
    - User account with unusual admin privileges

Account: service_account
  Username: service_account
  UID: 999
  Group: sudo
  Shell: /bin/bash
  Can Login: False
  Is Sudoer: True
  Type: system
  Issues:
    - System account with sudo privileges

============================================================
✅ Account Check Completed
============================================================
```

#### 2. 장기 미사용 계정 탐지

**Linux:**
```bash
# sudo 권한으로 실행 (wtmp, lastlog 읽기 위해)
sudo python scripts/account_mgmt/inactive_finder.py

# 또는 PYTHONPATH 설정
sudo PYTHONPATH=/path/to/automation-platform python scripts/account_mgmt/inactive_finder.py
```

**Windows:**
```powershell
python scripts\account_mgmt\inactive_finder.py
```

**출력 예시:**
```
============================================================
🔍 Inactive Account Finder Started
============================================================
Threshold: 90 days

============================================================
📊 INACTIVE ACCOUNT REPORT
============================================================
Inactive Threshold: 90 days
Inactive Accounts: 3
Never Logged In: 2

Platform: linux

🚨 Inactive Accounts (90+ days):
------------------------------------------------------------
1. testuser01
   Last Login: 2024-05-15 14:30:00
   Days Inactive: 165
   Type: user
   Home: /home/testuser01
   Shell: /bin/bash

2. oldadmin
   Last Login: 2024-06-20 09:15:00
   Days Inactive: 129
   Type: user
   Home: /home/oldadmin
   Shell: /bin/bash

3. contractor
   Last Login: 2024-07-01 16:45:00
   Days Inactive: 118
   Type: user
   Home: /home/contractor
   Shell: /bin/bash

⚠️  Never Logged In:
------------------------------------------------------------
1. tempuser
   Created: 2024-08-10
   Type: user
   Home: /home/tempuser
   Shell: /bin/bash

2. testaccount
   Created: 2024-09-01
   Type: user
   Home: /home/testaccount
   Shell: /bin/bash

============================================================
✅ Inactive Account Check Completed
============================================================
```

---

## 📊 데이터베이스 알림

계정 관리 스크립트는 발견된 이슈를 자동으로 데이터베이스에 저장합니다.

### 알림 조회

```bash
# 의심스러운 계정 알림
sqlite3 data/automation.db "
SELECT title, message, level, sent_at 
FROM notifications 
WHERE channel = 'account_check' 
ORDER BY sent_at DESC;
"

# 장기 미사용 계정 알림
sqlite3 data/automation.db "
SELECT title, message, level, sent_at 
FROM notifications 
WHERE channel = 'account_inactive' 
ORDER BY sent_at DESC;
"
```

### 알림 레벨

| 레벨 | 설명 | 예시 |
|------|------|------|
| CRITICAL | 즉각 대응 필요 | UID 0 비root 계정 |
| HIGH | 빠른 대응 필요 | sudo 권한 시스템 계정 |
| MEDIUM | 주의 필요 | 장기 미사용 계정, 이상한 쉘 |
| LOW | 정보성 | 한 번도 미로그인 계정 |

---

## 🔄 스케줄링

### Cron 설정 (Linux)

```bash
# crontab 편집
crontab -e

# 매일 자정에 계정 정책 검사
0 0 * * * /usr/bin/python3 /path/to/automation-platform/scripts/account_mgmt/account_checker.py

# 매주 월요일 오전 9시에 장기 미사용 계정 검사
0 9 * * 1 sudo /usr/bin/python3 /path/to/automation-platform/scripts/account_mgmt/inactive_finder.py
```

### Task Scheduler (Windows)

```powershell
# 매일 자정 실행
schtasks /create /tn "Account Policy Check" /tr "python C:\path\to\automation-platform\scripts\account_mgmt\account_checker.py" /sc daily /st 00:00

# 매주 월요일 오전 9시 실행
schtasks /create /tn "Inactive Account Check" /tr "python C:\path\to\automation-platform\scripts\account_mgmt\inactive_finder.py" /sc weekly /d MON /st 09:00
```

### 데이터베이스 기반 스케줄링

```python
from storage import db, Job, JobType

# 계정 정책 검사 작업 등록
with db.session_scope() as session:
    job = Job(
        name="account_policy_check",
        description="계정 정책 검사",
        job_type=JobType.ACCOUNT,
        script_path="scripts/account_mgmt/account_checker.py",
        cron_expression="0 0 * * *",  # 매일 자정
        enabled=True,
        timeout_seconds=600
    )
    session.add(job)

# 장기 미사용 계정 검사 작업 등록
with db.session_scope() as session:
    job = Job(
        name="inactive_account_check",
        description="장기 미사용 계정 검사",
        job_type=JobType.ACCOUNT,
        script_path="scripts/account_mgmt/inactive_finder.py",
        cron_expression="0 9 * * 1",  # 매주 월요일 오전 9시
        enabled=True,
        timeout_seconds=600
    )
    session.add(job)
```

---

## 🔧 설정 커스터마이징

### inactive_finder.py - 임계치 변경

```python
# scripts/account_mgmt/inactive_finder.py 파일 수정
class InactiveFinder:
    INACTIVE_DAYS = 90  # 기본값: 90일
    # 다른 값으로 변경 가능 (예: 60일, 120일)
```

### account_checker.py - 중요 파일 추가

Linux에서 추가 검사 파일 설정:
```python
# account_checker.py에서 CRITICAL_FILES 딕셔너리 확장
CRITICAL_FILES = {
    '/etc/passwd': {'mode': '0644', 'owner': 'root', 'group': 'root'},
    '/etc/shadow': {'mode': '0640', 'owner': 'root', 'group': 'shadow'},
    # 추가 파일...
}
```

---

## 🧪 테스트

### 수동 테스트

```bash
# account_checker 테스트
python scripts/account_mgmt/account_checker.py

# inactive_finder 테스트 (sudo 필요)
sudo python scripts/account_mgmt/inactive_finder.py

# Windows에서
python scripts\account_mgmt\account_checker.py
python scripts\account_mgmt\inactive_finder.py
```

### 통합 테스트 스크립트

```bash
#!/bin/bash
# test_account_mgmt.sh

echo "🔍 Testing Account Management Scripts..."
echo ""

echo "1️⃣  Testing account_checker.py..."
python scripts/account_mgmt/account_checker.py
if [ $? -eq 0 ]; then
    echo "✅ account_checker.py: PASS"
else
    echo "❌ account_checker.py: FAIL"
fi
echo ""

echo "2️⃣  Testing inactive_finder.py..."
sudo python scripts/account_mgmt/inactive_finder.py
if [ $? -eq 0 ]; then
    echo "✅ inactive_finder.py: PASS"
else
    echo "❌ inactive_finder.py: FAIL"
fi
echo ""

echo "✅ All tests completed!"
```

---

## 📋 보안 권장사항

### 발견된 이슈 대응 가이드

#### 1. UID 0 비root 계정
```bash
# 계정 삭제
sudo userdel -r [username]

# 또는 UID 변경
sudo usermod -u [new_uid] [username]
```

#### 2. sudo 권한 시스템 계정
```bash
# sudo 그룹에서 제거
sudo deluser [username] sudo

# sudoers 파일 확인
sudo visudo
```

#### 3. 장기 미사용 계정
```bash
# 계정 잠금
sudo usermod -L [username]

# 계정 삭제
sudo userdel -r [username]

# 계정 만료일 설정
sudo usermod -e YYYY-MM-DD [username]
```

#### 4. 한 번도 미로그인 계정
```bash
# 계정이 불필요하면 삭제
sudo userdel -r [username]

# 또는 일정 기간 후 재검토
```

---

## 🐛 문제 해결

### ❌ Permission denied: /var/log/wtmp

**원인:** wtmp 파일 읽기 권한 없음

**해결:**
```bash
# sudo로 실행
sudo python scripts/account_mgmt/inactive_finder.py

# 또는 읽기 권한 부여
sudo chmod +r /var/log/wtmp
sudo chmod +r /var/log/lastlog
```

---

### ❌ ModuleNotFoundError: No module named 'win32net'

**원인:** Windows에서 pywin32 미설치

**해결:**
```bash
pip install pywin32
```

---

### ❌ lastlog command not found

**원인:** lastlog 명령어 미설치

**해결:**
```bash
# Ubuntu/Debian
sudo apt-get install util-linux

# RHEL/CentOS
sudo yum install util-linux
```

---

## 📈 통계 및 리포트

### 주간 리포트 생성

```python
#!/usr/bin/env python3
"""주간 계정 관리 리포트 생성"""

from scripts.account_mgmt.account_checker import AccountChecker
from scripts.account_mgmt.inactive_finder import InactiveFinder
from datetime import datetime

def generate_weekly_report():
    print("=" * 60)
    print("주간 계정 관리 리포트")
    print(f"생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # 계정 정책 검사
    print("1. 계정 정책 검사")
    print("-" * 60)
    checker = AccountChecker()
    account_stats = checker.check_all()
    print(f"전체 계정: {account_stats['total_accounts']}")
    print(f"사용자 계정: {account_stats['user_accounts']}")
    print(f"시스템 계정: {account_stats['system_accounts']}")
    print(f"관리자 계정: {account_stats['admin_accounts']}")
    print(f"의심스러운 계정: {account_stats['suspicious_accounts']}")
    print()
    
    # 장기 미사용 계정
    print("2. 장기 미사용 계정")
    print("-" * 60)
    finder = InactiveFinder()
    inactive_stats = finder.check_all()
    print(f"장기 미사용 계정: {inactive_stats['inactive_accounts']}")
    print(f"한 번도 미로그인: {inactive_stats['never_logged_in']}")
    print()
    
    print("=" * 60)
    print("리포트 생성 완료")
    print("=" * 60)

if __name__ == "__main__":
    generate_weekly_report()
```

실행:
```bash
sudo python weekly_account_report.py > reports/account_report_$(date +%Y-%m-%d).txt
```

---

## 📚 참고 자료

### Linux 계정 관리
- [User and Group Management](https://www.linux.com/training-tutorials/understanding-users-and-groups-linux/)
- [Linux PAM](https://linux.die.net/man/5/pam)
- [lastlog Command](https://man7.org/linux/man-pages/man8/lastlog.8.html)

### Windows 계정 관리
- [NetUserEnum](https://docs.microsoft.com/en-us/windows/win32/api/lmaccess/nf-lmaccess-netuserenum)
- [NetUserGetInfo](https://docs.microsoft.com/en-us/windows/win32/api/lmaccess/nf-lmaccess-netusergetinfo)

---

## ✅ 체크리스트

계정 관리 스크립트 사용 전 확인:

- [ ] Python 3.10+ 설치
- [ ] 필요한 라이브러리 설치 (pywin32 for Windows)
- [ ] 적절한 권한 (sudo for Linux)
- [ ] 프로젝트 루트에서 실행
- [ ] 데이터베이스 초기화 완료
- [ ] 로그 디렉토리 권한 확인

---

## 🔮 향후 개발 계획

### password_policy.py (예정)
- [ ] 비밀번호 만료 임박 탐지 (7일 이내)
- [ ] 비밀번호 복잡도 검증
- [ ] 기본 비밀번호 사용 탐지
- [ ] 비밀번호 변경 이력 추적
- [ ] 정책 준수율 통계

### 고급 기능
- [ ] 계정 변경 이력 추적 (audit log)
- [ ] 그룹 멤버십 변경 모니터링
- [ ] 특정 사용자 활동 패턴 분석
- [ ] 이상 계정 활동 탐지 (AI/ML)
- [ ] Active Directory 연동 (Windows)

---

## 📞 문의

계정 관리 스크립트 관련 문의:

**팀 1조** - 정보보안학과
- **팀장**: 남수민 (2184039)
- **팀원**: 김규민 (2084002)
- **팀원**: 임준호 (2184)

**프로젝트**: [https://github.com/Vampirk/automation-platform](https://github.com/Vampirk/automation-platform)

---

**⭐ 정상 작동 확인 완료! 계정 보안 관리를 자동화하세요!**
