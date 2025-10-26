#!/bin/bash
# 로그 분석 스크립트 빠른 테스트
# 작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)

echo "⚡ 로그 분석 스크립트 빠른 테스트"
echo "============================================================"
echo ""

# 색상
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 테스트 로그 파일 생성
TEST_LOG="/tmp/quick_test_$$.log"

echo "📝 테스트 로그 파일 생성..."
cat > "$TEST_LOG" << 'EOF'
Oct 26 12:00:00 server sshd[1]: Failed password for root from 192.168.1.100 port 22 ssh2
Oct 26 12:00:15 server sshd[2]: Failed password for root from 192.168.1.100 port 22 ssh2
Oct 26 12:00:30 server sshd[3]: Failed password for root from 192.168.1.100 port 22 ssh2
Oct 26 12:00:45 server kernel: Out of memory: Kill process 1234
Oct 26 12:01:00 server systemd: service failed
Oct 26 12:01:15 server app: ERROR: Connection timeout
EOF

echo -e "${GREEN}✓${NC} 테스트 로그 생성 완료 ($TEST_LOG)"
echo ""

# Test 1: 기본 패턴 탐지
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Test 1: 기본 패턴 탐지"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > /tmp/quick_test_1.py << PYEOF
import sys
sys.path.insert(0, '.')
from scripts.log_analysis.log_analyzer import LogAnalyzer

analyzer = LogAnalyzer()
stats = analyzer.analyze_file('$TEST_LOG')

print(f'총 라인 수: {stats["total_lines"]}')
print(f'매치된 패턴: {stats["total_matches"]}')

if stats['top_issues']:
    print('\\n상위 패턴:')
    for name, info in stats['top_issues'][:3]:
        print(f'  - {name}: {info["count"]}회 ({info["severity"]})')
PYEOF

python /tmp/quick_test_1.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Test 1 PASSED${NC}"
else
    echo -e "\n${RED}❌ Test 1 FAILED${NC}"
fi
echo ""

# Test 2: IP 추적
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Test 2: IP 주소 추적"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > /tmp/quick_test_2.py << PYEOF
import sys
sys.path.insert(0, '.')
from scripts.log_analysis.pattern_detector import PatternDetector

detector = PatternDetector()
detector.analyze_file('$TEST_LOG')
top_ips = detector.get_top_ips(5)

print(f'탐지된 의심스러운 IP: {len(top_ips)}개')
for ip, count in top_ips:
    print(f'  - {ip}: {count}회 실패')
PYEOF

python /tmp/quick_test_2.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Test 2 PASSED${NC}"
else
    echo -e "\n${RED}❌ Test 2 FAILED${NC}"
fi
echo ""

# Test 3: 모듈 import
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Test 3: 모듈 Import"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > /tmp/quick_test_3.py << PYEOF
import sys
sys.path.insert(0, '.')
from scripts.log_analysis import LogAnalyzer, PatternDetector, ReportGenerator
print('✓ 모든 모듈이 성공적으로 import됨')
PYEOF

python /tmp/quick_test_3.py 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test 3 PASSED${NC}"
else
    echo -e "${RED}❌ Test 3 FAILED${NC}"
fi
echo ""

# 정리
rm -f "$TEST_LOG"
rm -f /tmp/quick_test_*.py
echo "🗑️  테스트 파일 삭제 완료"
echo ""

echo "============================================================"
echo -e "${GREEN}✅ 빠른 테스트 완료!${NC}"
echo "============================================================"
echo ""
echo "💡 다음 단계:"
echo "   - 전체 테스트: ./scripts/log_analysis/test_log_analysis.sh"
echo "   - 실제 로그 분석: sudo python scripts/log_analysis/log_analyzer.py"
echo ""
