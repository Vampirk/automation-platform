# 🔍 로그 분석 스크립트

실시간으로 `/var/log/auth.log`를 감시하여 Failed login 탐지 및 의심스러운 IP 추적

## 📋 주요 기능

- ✅ **실시간 로그 감시**: `tail -f` 스타일로 로그 파일 모니터링
- ✅ **Failed login 탐지**: 5가지 패턴 자동 인식
  - Failed password
  - Authentication failure
  - Invalid user
  - Connection closed
  - Disconnected
- ✅ **의심스러운 IP 추적**: 5분 내 5회 실패 시 자동 경고
- ✅ **중복 알림 방지**: 같은 IP에 대해 30분에 1회만 알림
- ✅ **데이터베이스 저장**: 모든 경고를 DB에 자동 저장

## 🚀 사용 방법

### **1. 전체 로그 파일 분석** (과거 기록 분석)
```bash
# 기본 사용
python scripts/log_analysis/log_analyzer.py --mode analyze

# 최근 1000줄만 분석
python scripts/log_analysis/log_analyzer.py --mode analyze --max-lines 1000

# 다른 로그 파일 분석
python scripts/log_analysis/log_analyzer.py --mode analyze --log-file /var/log/secure
```

### **2. 실시간 감시** (권장)
```bash
# 실시간 모니터링 시작
python scripts/log_analysis/log_analyzer.py --mode monitor

# Ctrl+C로 중지
```

### **3. 테스트 실행**
```bash
# 테스트 스크립트 실행
cd ~/automation-platform
./scripts/log_analysis/test_log_analyzer.sh
```

### **4. 백그라운드 실행**
```bash
# 백그라운드에서 실행
nohup python scripts/log_analysis/log_analyzer.py --mode monitor > /dev/null 2>&1 &

# 프로세스 확인
ps aux | grep log_analyzer

# 중지
pkill -f log_analyzer
```

## 📊 출력 예시

### 정상 실행:
```
============================================================
🔍 Log Analysis Script Started
Platform: Linux 6.12.25-amd64
Log file: /var/log/auth.log
Mode: monitor
============================================================
Starting real-time monitoring: /var/log/auth.log
Press Ctrl+C to stop

2025-10-25 22:30:15 | WARNING | Failed login detected: user=root, ip=192.168.1.100
2025-10-25 22:30:45 | WARNING | Failed login detected: user=admin, ip=192.168.1.100
```

### 경고 발생:
```
2025-10-25 22:35:00 | CRITICAL | 🚨 SECURITY ALERT: Suspicious activity detected!
IP: 192.168.1.100
Failed login attempts: 5 times in 5.0 minutes
Username attempted: root
First attempt: 2025-10-25 22:30:00
Last attempt: 2025-10-25 22:35:00
Pattern: failed_password

✅ Alert saved to database for IP 192.168.1.100
```

### 통계 출력:
```
============================================================
📊 Log Analysis Statistics
============================================================
Total lines processed: 1,234
Failed logins detected: 15
Alerts generated: 2
Suspicious IPs: 3

🚨 Suspicious IP addresses:
   - 192.168.1.100: 5 failed attempts
   - 203.0.113.42: 8 failed attempts
   - 198.51.100.89: 3 failed attempts
============================================================
```

## ⚙️ 설정

### 임계치 변경

`scripts/log_analysis/log_analyzer.py` 파일에서 수정:
```python
# 5분 내 5회 → 10분 내 3회로 변경
self.tracker = FailedLoginTracker(
    time_window_minutes=10,  # 시간 윈도우
    threshold=3              # 임계치
)
```

### 알림 쿨다운 변경
```python
# 30분 → 1시간으로 변경
self.alert_cooldown = timedelta(minutes=60)
```

## 🐛 트러블슈팅

### 1. Permission denied 에러
```bash
# 로그 파일 읽기 권한 필요
sudo chmod 644 /var/log/auth.log

# 또는 sudo로 실행
sudo python scripts/log_analysis/log_analyzer.py --mode monitor
```

### 2. 로그 파일이 없음
```bash
# Ubuntu/Debian
/var/log/auth.log

# CentOS/RHEL
/var/log/secure

# 파일 확인
ls -la /var/log/auth.log
```

### 3. 테스트 로그 생성
```bash
# 테스트용 Failed login 시뮬레이션
cat > /tmp/test_auth.log << 'TESTEOF'
Oct 25 22:30:00 kali sshd[1234]: Failed password for root from 192.168.1.100 port 12345
Oct 25 22:30:15 kali sshd[1235]: Failed password for admin from 192.168.1.100 port 12346
Oct 25 22:30:30 kali sshd[1236]: Failed password for root from 192.168.1.100 port 12347
Oct 25 22:30:45 kali sshd[1237]: Failed password for user from 192.168.1.100 port 12348
Oct 25 22:31:00 kali sshd[1238]: Failed password for root from 192.168.1.100 port 12349
TESTEOF

# 테스트 실행
python scripts/log_analysis/log_analyzer.py \
    --mode analyze \
    --log-file /tmp/test_auth.log
```

## 📝 로그 패턴

현재 지원하는 로그 패턴:

1. **Failed password**: `Failed password for user from IP port PORT`
2. **Authentication failure**: `authentication failure...rhost=IP`
3. **Invalid user**: `Invalid user USERNAME from IP`
4. **Connection closed**: `Connection closed by authenticating user USERNAME IP`
5. **Disconnected**: `Disconnected from invalid user USERNAME IP`

## 🎯 다음 단계

- [ ] 알림 시스템 연동 (이메일/Slack)
- [ ] GeoIP 조회 (IP 위치 확인)
- [ ] 자동 차단 기능 (iptables)
- [ ] 웹 대시보드에 실시간 표시

## 💡 팁

- **sudo 권한 없이 실행**: 로그 파일을 복사하여 테스트
```bash
  sudo cp /var/log/auth.log /tmp/auth.log
  sudo chmod 644 /tmp/auth.log
  python scripts/log_analysis/log_analyzer.py --log-file /tmp/auth.log
```

- **백그라운드 실행 로그 확인**:
```bash
  tail -f logs/automation.log | grep "Failed login"
```

- **실시간 통계**:
```bash
  watch -n 5 'sqlite3 data/automation.db "SELECT COUNT(*) FROM notifications WHERE channel=\"log_analysis\""'
```

## 📞 문제 발생 시

- 로그 파일 권한 문제: `sudo` 사용
- 파일 경로 문제: 절대 경로 사용
- 모듈 import 에러: `PYTHONPATH` 설정 확인
