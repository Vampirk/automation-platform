#!/bin/bash
# 보안 점검 스크립트 테스트

echo "🧪 보안 점검 스크립트 테스트"
echo "============================================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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
        "security_checker.py"
        "port_scanner.py"
        "permission_checker.py"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "scripts/security/$script" ]; then
            echo -e "${GREEN}✓${NC} $script found"
        else
            echo -e "${RED}✗${NC} $script NOT FOUND"
            return 1
        fi
    done
    
    echo ""
    return 0
}

# 권한 체크
check_permissions() {
    echo "🔐 Checking user permissions..."
    echo ""
    
    if [ "$EUID" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Running as root (all tests available)"
    else
        echo -e "${YELLOW}⚠${NC} Not running as root (some checks may be skipped)"
    fi
    
    echo ""
}

# 메인 테스트 실행
main() {
    echo "Starting security scripts test suite..."
    echo ""
    
    # 파일 존재 확인
    if ! check_scripts; then
        echo -e "${RED}Error: Required scripts not found${NC}"
        echo "Please ensure you are in the automation-platform directory"
        exit 1
    fi
    
    # 권한 확인
    check_permissions
    
    echo "Running tests..."
    echo ""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 1: security_checker.py 기본 실행
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if [ "$EUID" -eq 0 ]; then
        run_test "Security Checker - Full Scan (Root)" \
            "python scripts/security/security_checker.py"
    else
        run_test "Security Checker - Non-root Scan" \
            "python scripts/security/security_checker.py"
    fi
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 2: port_scanner.py - Quick scan
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_test "Port Scanner - Quick Scan" \
        "python scripts/security/port_scanner.py --mode quick"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 3: port_scanner.py - Range scan (1-100)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_test "Port Scanner - Range Scan (1-100)" \
        "python scripts/security/port_scanner.py --mode range --start-port 1 --end-port 100"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 4: permission_checker.py - Critical files (일반 사용자도 실행)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_test "Permission Checker - Critical Files" \
        "python scripts/security/permission_checker.py --mode critical"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 5: permission_checker.py - SSH keys
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_test "Permission Checker - SSH Keys" \
        "python scripts/security/permission_checker.py --mode ssh"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 6: 모듈 import 테스트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    run_test "Module Import Test" \
        "python -c 'import sys; sys.path.insert(0, \".\"); from scripts.security import security_checker, port_scanner, permission_checker; print(\"✓ All modules imported successfully\")'"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 테스트 결과 요약
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo ""
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
        
        if [ "$EUID" -ne 0 ]; then
            echo -e "${YELLOW}💡 Tip: Run with sudo for complete testing${NC}"
            echo "   sudo ./scripts/security/test_security.sh"
        fi
        
        exit 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo ""
        echo "Please check the output above for details."
        exit 1
    fi
}

# 스크립트 실행
main
