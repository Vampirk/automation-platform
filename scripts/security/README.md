# 🛡️ 보안 점검 스크립트

시스템 보안 설정을 자동으로 검증하는 스크립트 모음

## 📋 스크립트 목록

### 1. `security_checker.py` - 종합 보안 점검
시스템 전반의 보안 설정을 점검하고 보안 점수를 산출합니다.

**점검 항목:**
- ✅ 중요 파일 권한 (/etc/passwd, /etc/shadow 등)
- ✅ SSH 설정 검증 (PermitRootLogin, PasswordAuthentication 등)
- ✅ 열린 포트 확인
- ✅ 비밀번호 정책 (PASS_MAX_DAYS, PASS_MIN_DAYS)
- ✅ 방화벽 상태 (ufw, iptables)

**사용법:**
```bash
# 기본 실행 (sudo 권장)
sudo python scripts/security/security_checker.py

# 일반 사용자로 실행 (일부 점검 스킵됨)
python scripts/security/security_checker.py
```

**출력 예시:**
```
============================================================
🛡️  SECURITY CHECK REPORT
============================================================
Scan Date: 2025-10-25 23:00:00
Platform: Linux 6.12.25-amd64

📊 Summary:
  Security Score: 85/100
  Checks Passed: 12
  Checks Failed: 3
  Checks Skipped: 2
  Issues Found: 3

🚨 Issues Found:

[HIGH] - 2 issue(s)
------------------------------------------------------------
1. Incorrect permissions on /etc/shadow
   Category: File Permissions
   Description: Current: 644, Expected: 640
   Recommendation: Run: sudo chmod 640 /etc/shadow

2. Insecure SSH setting: PermitRootLogin
   Category: SSH Configuration
   Description: Current: yes, Recommended: no
   Recommendation: Set 'PermitRootLogin no' in /etc/ssh/sshd_config

[MEDIUM] - 1 issue(s)
------------------------------------------------------------
1. Firewall is inactive
   Category: Firewall
   Description: UFW firewall is not enabled
   Recommendation: Run: sudo ufw enable

============================================================
```

---

### 2. `port_scanner.py` - 포트 스캔
시스템의 열린 포트와 실행 중인 서비스를 확인합니다.

**기능:**
- ✅ 일반 포트 빠른 스캔 (20개 주요 포트)
- ✅ 범위 포트 스캔 (멀티스레드)
- ✅ 전체 포트 스캔 (1-65535)
- ✅ 위험 포트 자동 탐지
- ✅ 프로세스 정보 조회

**사용법:**
```bash
# 일반 포트 빠른 스캔 (권장)
python scripts/security/port_scanner.py --mode quick

# 1-1024 포트 스캔
python scripts/security/port_scanner.py --mode range --start-port 1 --end-port 1024

# 전체 포트 스캔 (시간 오래 걸림)
python scripts/security/port_scanner.py --mode full

# 원격 서버 스캔
python scripts/security/port_scanner.py --target 192.168.1.100 --mode quick

# 타임아웃 조정 (느린 네트워크)
python scripts/security/port_scanner.py --mode quick --timeout 2.0
```

**출력 예시:**
```
============================================================
🔌 PORT SCAN REPORT
============================================================
Target: localhost
Scan Date: 2025-10-25 23:05:00
Timeout: 1.0s

Open Ports: 5
Closed Ports: 15

📋 Open Ports:

🚨 RISKY PORTS (Security Concern):
  Port    21 - FTP
             Process: vsftpd (pid: 1234)
             ⚠️  FTP (Unencrypted)

  Port  3389 - RDP
             Process: xrdp (pid: 5678)
             ⚠️  RDP (Bruteforce target)

✅ Standard Ports:
  Port    22 - SSH
  Port    80 - HTTP
  Port   443 - HTTPS

============================================================
```

---

### 3. `permission_checker.py` - 파일 권한 검사
파일 및 디렉토리 권한을 상세하게 검사합니다.

**점검 모드:**
- `critical`: 중요 시스템 파일 권한 검사
- `world-writable`: 모두가 쓸 수 있는 위험한 파일 검색
- `suid`: SUID/SGID 파일 검색
- `ssh`: SSH 키 권한 검사
- `all`: 모든 검사 실행

**사용법:**
```bash
# 중요 파일만 검사
sudo python scripts/security/permission_checker.py --mode critical

# World-writable 파일 검색
sudo python scripts/security/permission_checker.py --mode world-writable --directory /home

# SUID 파일 검색
sudo python scripts/security/permission_checker.py --mode suid --directory /usr/bin

# SSH 키 권한 검사
python scripts/security/permission_checker.py --mode ssh

# 모든 검사 (시간 오래 걸림)
sudo python scripts/security/permission_checker.py --mode all --directory /

# 하위 디렉토리 검사 안 함
python scripts/security/permission_checker.py --mode world-writable --no-recursive
```

**출력 예시:**
```
============================================================
🔐 PERMISSION CHECK REPORT
============================================================
Scan Date: 2025-10-25 23:10:00

Files Checked: 50
Files OK: 45
Issues Found: 5

🚨 Issues Found:

[CRITICAL] - 2 issue(s)
------------------------------------------------------------
  Path: /home/user/.ssh/id_rsa
  Issue: Insecure Private Key Permissions
  Current: 0644
  Expected: 0600

  Path: /tmp/shared_folder
  Issue: World-Writable File
  Current: 0777
  Expected: Remove write permission for others

[HIGH] - 3 issue(s)
------------------------------------------------------------
  Path: /etc/shadow
  Issue: Incorrect Permissions
  Current: 0644
  Expected: 0640

============================================================
```

---

## 🚀 통합 사용법

### **정기 보안 점검 스크립트**

전체 보안 점검을 한 번에 실행:
```bash
#!/bin/bash
# 통합 보안 점검 스크립트

echo "🛡️  Starting comprehensive security check..."
echo ""

# 1. 종합 보안 점검
echo "1️⃣  Running security checker..."
sudo python scripts/security/security_checker.py
echo ""

# 2. 포트 스캔
echo "2️⃣  Running port scanner..."
python scripts/security/port_scanner.py --mode quick
echo ""

# 3. 권한 검사
echo "3️⃣  Running permission checker..."
sudo python scripts/security/permission_checker.py --mode all --directory /home
echo ""

echo "✅ Security check completed!"
```

---

## 📊 데이터베이스 스케줄러 등록

### 자동 실행 작업 등록:
```python
from storage import db, Job, JobType

with db.session_scope() as session:
    # 매일 자정 보안 점검
    security_job = Job(
        name="daily_security_check",
        description="일일 시스템 보안 점검",
        job_type=JobType.SECURITY,
        script_path="scripts/security/security_checker.py",
        cron_expression="0 0 * * *",  # 매일 자정
        enabled=True,
        timeout_seconds=300,
        priority=9
    )
    session.add(security_job)
    
    # 주간 포트 스캔
    port_scan_job = Job(
        name="weekly_port_scan",
        description="주간 포트 스캔",
        job_type=JobType.SECURITY,
        script_path="scripts/security/port_scanner.py",
        script_args="--mode quick",
        cron_expression="0 2 * * 0",  # 매주 일요일 새벽 2시
        enabled=True,
        timeout_seconds=180,
        priority=7
    )
    session.add(port_scan_job)
```

---

## 🐛 트러블슈팅

### 1. Permission denied 에러
```bash
# 대부분의 보안 점검은 root 권한 필요
sudo python scripts/security/security_checker.py
```

### 2. 모듈 import 에러
```bash
# PYTHONPATH 설정
export PYTHONPATH=/path/to/automation-platform:$PYTHONPATH
python scripts/security/security_checker.py
```

### 3. 포트 스캔 느림
```bash
# 타임아웃 줄이기 (빠르지만 정확도 감소)
python scripts/security/port_scanner.py --mode quick --timeout 0.5

# 워커 수 늘리기 (빠르지만 시스템 부하 증가)
# port_scanner.py 코드에서 max_workers 조정
```

### 4. SSH 설정 파일 없음
```bash
# SSH 서버가 설치되어 있는지 확인
which sshd

# 설치 (Ubuntu/Debian)
sudo apt-get install openssh-server

# 설정 파일 위치 확인
ls -la /etc/ssh/sshd_config
```

---

## 📈 보안 점검 결과 조회
```bash
# 데이터베이스에서 최근 보안 점검 결과 조회
sqlite3 data/automation.db

SELECT 
    title,
    level,
    sent_at
FROM notifications 
WHERE channel = 'security_check' 
ORDER BY sent_at DESC 
LIMIT 5;

# 보안 점수 추이 확인
SELECT 
    title,
    sent_at
FROM notifications 
WHERE channel = 'security_check' 
AND title LIKE '%Score:%'
ORDER BY sent_at DESC;
```

---

## 💡 보안 강화 권장사항

### 1. SSH 보안 강화
```bash
# /etc/ssh/sshd_config 편집
sudo nano /etc/ssh/sshd_config

# 권장 설정:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
X11Forwarding no
MaxAuthTries 3

# SSH 재시작
sudo systemctl restart sshd
```

### 2. 방화벽 활성화
```bash
# UFW 설치 및 활성화
sudo apt-get install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 3. 자동 업데이트 설정
```bash
# unattended-upgrades 설치
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. 파일 권한 수정
```bash
# 중요 파일 권한 수정
sudo chmod 640 /etc/shadow
sudo chmod 640 /etc/gshadow
sudo chmod 600 /etc/ssh/sshd_config
sudo chmod 440 /etc/sudoers

# SSH 키 권한 수정
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*
chmod 644 ~/.ssh/id_*.pub
chmod 644 ~/.ssh/authorized_keys
```

---

## 🎯 다음 단계

- [ ] CVE 취약점 스캔 추가
- [ ] 알림 시스템 연동 (이메일/Slack)
- [ ] 자동 복구 기능
- [ ] 웹 대시보드에 보안 점수 표시
- [ ] Fail2ban 로그 분석 연동

---

## 📞 문제 발생 시

- GitHub Issues: https://github.com/Vampirk/automation-platform/issues
- 로그 확인: `tail -f logs/automation.log`
