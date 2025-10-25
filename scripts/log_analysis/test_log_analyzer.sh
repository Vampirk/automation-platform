#!/bin/bash
# 로그 분석 스크립트 테스트

echo "🧪 로그 분석 스크립트 테스트"
echo "============================================================"

# 테스트 로그 파일 생성
TEST_LOG="/tmp/test_auth_$(date +%s).log"

echo "📝 테스트 로그 파일 생성: $TEST_LOG"

cat > "$TEST_LOG" << 'LOGEOF'
Oct 25 22:30:00 kali sshd[1234]: Failed password for root from 192.168.1.100 port 12345 ssh2
Oct 25 22:30:15 kali sshd[1235]: Failed password for admin from 192.168.1.100 port 12346 ssh2
Oct 25 22:30:30 kali sshd[1236]: Failed password for root from 192.168.1.100 port 12347 ssh2
Oct 25 22:30:45 kali sshd[1237]: Failed password for invalid user test from 192.168.1.100 port 12348 ssh2
Oct 25 22:31:00 kali sshd[1238]: Failed password for root from 192.168.1.100 port 12349 ssh2
Oct 25 22:31:15 kali sshd[1239]: authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=192.168.1.100
Oct 25 22:32:00 kali sshd[1240]: Invalid user hacker from 203.0.113.42 port 22222
Oct 25 22:32:15 kali sshd[1241]: Failed password for root from 203.0.113.42 port 22223 ssh2
Oct 25 22:32:30 kali sshd[1242]: Connection closed by authenticating user test 203.0.113.42 port 22224
Oct 25 22:33:00 kali sshd[1243]: Disconnected from invalid user admin 198.51.100.89 port 33333
Oct 25 22:33:15 kali sshd[1244]: Accepted password for user from 192.168.1.50 port 44444 ssh2
Oct 25 22:34:00 kali sshd[1245]: Failed password for root from 192.168.1.100 port 12350 ssh2
Oct 25 22:34:15 kali sshd[1246]: Failed password for root from 192.168.1.100 port 12351 ssh2
Oct 25 22:34:30 kali sshd[1247]: Failed password for root from 192.168.1.100 port 12352 ssh2
LOGEOF

echo "✅ 테스트 로그 파일 생성 완료 (14줄)"
echo ""
echo "📊 예상 결과:"
echo "   - 총 실패 시도: 11회"
echo "   - 의심스러운 IP: 3개 (192.168.1.100, 203.0.113.42, 198.51.100.89)"
echo "   - 경고 발생: 1개 (192.168.1.100 - 8회 실패)"
echo ""

# 스크립트 실행
echo "🚀 로그 분석 스크립트 실행..."
echo ""

python scripts/log_analysis/log_analyzer.py \
    --mode analyze \
    --log-file "$TEST_LOG"

EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ 테스트 완료!"
else
    echo "❌ 테스트 실패 (Exit code: $EXIT_CODE)"
fi

# 테스트 파일 정리
echo ""
read -p "테스트 로그 파일을 삭제하시겠습니까? (y/n): " answer
if [[ "$answer" == "y" ]]; then
    rm "$TEST_LOG"
    echo "🗑️  테스트 파일 삭제됨"
else
    echo "📁 테스트 파일 유지: $TEST_LOG"
fi
