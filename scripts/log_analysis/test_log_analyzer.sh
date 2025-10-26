#!/bin/bash
# 로그 분석 스크립트 통합 테스트
# 작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
# 작성일: 2025-10-26

echo "🧪 로그 분석 스크립트 테스트"
echo "============================================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 로그 파일 경로
TEST_LOG_DIR="/tmp/log_analysis_test_$$"
TEST_AUTH_LOG="$TEST_LOG_DIR/auth.log"
TEST_SYSLOG="$TEST_LOG_DIR/syslog"
TEST_KERN_LOG="$TEST_LOG_DIR/kern.log"

# 테스트 함수
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Test $TOTAL_TESTS: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Command: $test_command"
    echo ""
    
    # 명령 실행
    eval $test_command
    EXIT_CODE=$?
    
    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Test PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ Test FAILED (Exit code: $EXIT_CODE)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# 스크립트 존재 확인
check_scripts() {
    echo "📁 Checking script files..."
    echo ""
    
    local scripts=(
        "log_analyzer.py"
        "pattern_detector.py"
        "report_generator.py"
    )
    
    local all_found=true
    for script in "${scripts[@]}"; do
        if [ -f "scripts/log_analysis/$script" ]; then
            echo -e "${GREEN}✓${NC} $script found"
        else
            echo -e "${RED}✗${NC} $script NOT FOUND"
            all_found=false
        fi
    done
    
    echo ""
    
    if [ "$all_found" = false ]; then
        return 1
    fi
    return 0
}

# 의존성 확인
check_dependencies() {
    echo "📦 Checking dependencies..."
    echo ""
    
    # watchdog 확인
    python -c "import watchdog" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} watchdog installed"
    else
        echo -e "${YELLOW}⚠${NC} watchdog NOT installed"
        echo "   Install with: pip install watchdog"
    fi
    
    echo ""
}

# 테스트 로그 파일 생성
create_test_logs() {
    echo "📝 Creating test log files..."
    echo ""
    
    # 테스트 디렉토리 생성
    mkdir -p "$TEST_LOG_DIR"
    
    # auth.log 테스트 데이터
    cat > "$TEST_AUTH_LOG" << 'EOF'
Oct 26 01:30:00 testserver sshd[1234]: Failed password for root from 192.168.1.100 port 12345 ssh2
Oct 26 01:30:15 testserver sshd[1235]: Failed password for admin from 192.168.1.100 port 12346 ssh2
Oct 26 01:30:30 testserver sshd[1236]: Failed password for root from 192.168.1.100 port 12347 ssh2
Oct 26 01:30:45 testserver sshd[1237]: Failed password for invalid user test from 192.168.1.100 port 12348 ssh2
Oct 26 01:31:00 testserver sshd[1238]: Failed password for root from 192.168.1.100 port 12349 ssh2
Oct 26 01:31:15 testserver sshd[1239]: authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=192.168.1.100
Oct 26 01:32:00 testserver sshd[1240]: POSSIBLE BREAK-IN ATTEMPT!
Oct 26 01:32:15 testserver sudo: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/bin/bash
Oct 26 01:33:00 testserver useradd[1241]: new user: name=testuser, UID=1001, GID=1001
Oct 26 01:34:00 testserver sshd[1242]: Failed password for root from 203.0.113.42 port 22223 ssh2
Oct 26 01:34:15 testserver sshd[1243]: Failed password for root from 203.0.113.42 port 22224 ssh2
Oct 26 01:35:00 testserver sshd[1244]: Accepted password for user from 192.168.1.50 port 44444 ssh2
Oct 26 02:00:00 testserver sshd[1245]: Failed password for root from 192.168.1.100 port 12350 ssh2
Oct 26 02:00:15 testserver sshd[1246]: Failed password for root from 192.168.1.100 port 12351 ssh2
Oct 26 14:30:00 testserver sshd[1247]: Failed password for admin from 198.51.100.89 port 33333 ssh2
EOF
    
    # syslog 테스트 데이터
    cat > "$TEST_SYSLOG" << 'EOF'
Oct 26 01:30:00 testserver kernel: Out of memory: Kill process 5678 (mysqld) score 250
Oct 26 01:30:30 testserver systemd[1]: apache2.service: Failed with result 'exit-code'.
Oct 26 01:31:00 testserver kernel: segfault at 7f8e2c00 ip 00007f8e2c00 sp 00007ffed3f0 error 4
Oct 26 14:30:00 testserver disk_check: Warning: Disk usage 95%
Oct 26 14:30:15 testserver disk_check: Error: No space left on device
Oct 26 14:31:00 testserver app[9999]: ERROR: Database connection failed
Oct 26 14:31:15 testserver app[9999]: WARNING: Retrying connection
Oct 26 14:31:30 testserver app[9999]: CRITICAL: Maximum retries reached
EOF
    
    # kern.log 테스트 데이터
    cat > "$TEST_KERN_LOG" << 'EOF'
Oct 26 01:30:00 testserver kernel: [12345.678901] warning: group user does not exist
Oct 26 14:30:00 testserver kernel: [23456.789012] permission denied at /dev/sda1
EOF
    
    echo -e "${GREEN}✓${NC} Test auth.log created: $TEST_AUTH_LOG (15 lines)"
    echo -e "${GREEN}✓${NC} Test syslog created: $TEST_SYSLOG (8 lines)"
    echo -e "${GREEN}✓${NC} Test kern.log created: $TEST_KERN_LOG (2 lines)"
    echo ""
}

# 테스트 로그 파일 정리
cleanup_test_logs() {
    if [ -d "$TEST_LOG_DIR" ]; then
        rm -rf "$TEST_LOG_DIR"
        echo -e "${GREEN}✓${NC} Test log files cleaned up"
    fi
}

# 권한 체크
check_permissions() {
    echo "🔐 Checking user permissions..."
    echo ""
    
    if [ "$EUID" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Running as root (all tests available)"
    else
        echo -e "${YELLOW}⚠${NC} Not running as root"
        echo "   Note: Some tests may work with test files, but real log analysis requires sudo"
    fi
    
    echo ""
}

# 메인 테스트 실행
main() {
    echo "Starting log analysis scripts test suite..."
    echo ""
    
    # 스크립트 파일 존재 확인
    if ! check_scripts; then
        echo -e "${RED}Error: Required scripts not found${NC}"
        echo "Please ensure you are in the automation-platform directory"
        exit 1
    fi
    
    # 의존성 확인
    check_dependencies
    
    # 권한 확인
    check_permissions
    
    # 테스트 로그 파일 생성
    create_test_logs
    
    echo "Running tests..."
    echo ""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 1: log_analyzer.py - 파일 분석 모드
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_1.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.log_analyzer import LogAnalyzer
analyzer = LogAnalyzer()
stats = analyzer.analyze_file("$TEST_AUTH_LOG")
print(f"✓ Analyzed {stats['total_lines']} lines")
print(f"✓ Found {stats['total_matches']} matches")
exit(0 if stats['total_matches'] > 0 else 1)
PYEOF
    
    run_test "Log Analyzer - File Analysis" \
        "python /tmp/test_script_1.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 2: pattern_detector.py - 시간대별 분석
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_2.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.pattern_detector import PatternDetector
detector = PatternDetector()
detector.analyze_file("$TEST_AUTH_LOG")
hourly = detector.get_hourly_summary()
print(f"✓ Analyzed {len(hourly)} hours of activity")
exit(0 if len(hourly) > 0 else 1)
PYEOF
    
    run_test "Pattern Detector - Hourly Analysis" \
        "python /tmp/test_script_2.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 3: pattern_detector.py - 이상 패턴 탐지
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_3.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.pattern_detector import PatternDetector
detector = PatternDetector()
detector.analyze_file("$TEST_AUTH_LOG")
anomalies = detector.detect_anomalies()
print(f"✓ Detected {len(anomalies)} anomalies")
for a in anomalies:
    print(f"  - [{a['severity']}] {a['description']}")
exit(0)
PYEOF
    
    run_test "Pattern Detector - Anomaly Detection" \
        "python /tmp/test_script_3.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 4: pattern_detector.py - IP 추적
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_4.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.pattern_detector import PatternDetector
detector = PatternDetector()
detector.analyze_file("$TEST_AUTH_LOG")
top_ips = detector.get_top_ips(5)
print(f"✓ Tracked {len(top_ips)} suspicious IPs")
for ip, count in top_ips:
    print(f"  - {ip}: {count} attempts")
exit(0 if len(top_ips) > 0 else 1)
PYEOF
    
    run_test "Pattern Detector - IP Tracking" \
        "python /tmp/test_script_4.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 5: report_generator.py - 리포트 생성
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_5.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.report_generator import ReportGenerator
generator = ReportGenerator()
generator.analyze_logs(["$TEST_AUTH_LOG", "$TEST_SYSLOG"])
summary = generator.generate_summary()
print(f"✓ Total lines analyzed: {summary['total_lines_analyzed']}")
print(f"✓ Total matches: {summary['total_matches']}")
print(f"✓ Anomalies detected: {len(summary['anomalies'])}")
exit(0)
PYEOF
    
    run_test "Report Generator - Summary Generation" \
        "python /tmp/test_script_5.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 6: report_generator.py - 텍스트 리포트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_6.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.report_generator import ReportGenerator
generator = ReportGenerator()
generator.analyze_logs(["$TEST_SYSLOG"])
summary = generator.generate_summary()
report = generator.generate_text_report(summary)
print(f"✓ Report generated ({len(report)} characters)")
print("\\n--- Sample Report Output ---")
print(report[:500])
print("...")
exit(0)
PYEOF
    
    run_test "Report Generator - Text Report Format" \
        "python /tmp/test_script_6.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 7: 다양한 로그 형식 파싱
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_7.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.pattern_detector import PatternDetector
detector = PatternDetector()
# Oct 26 01:30:00 형식 테스트
line1 = "Oct 26 01:30:00 server test"
ts1 = detector.extract_timestamp(line1)
print(f"✓ Parsed timestamp: {ts1}")
exit(0 if ts1 is not None else 1)
PYEOF
    
    run_test "Pattern Detector - Timestamp Parsing" \
        "python /tmp/test_script_7.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 8: 심각도 분류 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_8.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.log_analyzer import LogPatterns
patterns = LogPatterns()
# CRITICAL 패턴
critical = [p for p, s in patterns.SEVERITY_MAP.items() if s == "CRITICAL"]
high = [p for p, s in patterns.SEVERITY_MAP.items() if s == "HIGH"]
print(f"✓ CRITICAL patterns: {len(critical)}")
print(f"✓ HIGH patterns: {len(high)}")
exit(0 if len(critical) > 0 and len(high) > 0 else 1)
PYEOF
    
    run_test "Log Analyzer - Severity Classification" \
        "python /tmp/test_script_8.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 9: 모듈 import 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_9.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis import LogAnalyzer, PatternDetector, ReportGenerator
print("✓ LogAnalyzer imported successfully")
print("✓ PatternDetector imported successfully")
print("✓ ReportGenerator imported successfully")
PYEOF
    
    run_test "Module Import Test" \
        "python /tmp/test_script_9.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 10: 에러 핸들링 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cat > /tmp/test_script_10.py << PYEOF
import sys
sys.path.insert(0, ".")
from scripts.log_analysis.log_analyzer import LogAnalyzer
analyzer = LogAnalyzer()
# 존재하지 않는 파일
stats = analyzer.analyze_file("/nonexistent/file.log")
print("✓ Handled non-existent file gracefully")
exit(0)
PYEOF
    
    run_test "Log Analyzer - Error Handling" \
        "python /tmp/test_script_10.py"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 테스트 로그 파일 정리
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo ""
    cleanup_test_logs
    
    # 임시 Python 스크립트 파일 정리
    rm -f /tmp/test_script_*.py
    echo -e "${GREEN}✓${NC} Test Python scripts cleaned up"
    echo ""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 테스트 결과 요약
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo "============================================================"
    echo "📊 TEST SUMMARY"
    echo "============================================================"
    echo "Total Tests:  $TOTAL_TESTS"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
        echo "💡 Next steps:"
        echo "   1. Test with real log files:"
        echo "      sudo python scripts/log_analysis/log_analyzer.py"
        echo ""
        echo "   2. Generate a report:"
        echo "      sudo python scripts/log_analysis/report_generator.py"
        echo ""
        echo "   3. Set up scheduled monitoring:"
        echo "      Add jobs to database for automated analysis"
        echo ""
        exit 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo ""
        echo "Please check the output above for details."
        echo ""
        echo "Common issues:"
        echo "  - Missing dependencies: pip install watchdog"
        echo "  - Wrong directory: Run from automation-platform root"
        echo "  - Python path: Ensure project root is in PYTHONPATH"
        echo ""
        exit 1
    fi
}

# 스크립트 실행
main
