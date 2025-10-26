#!/usr/bin/env python3
"""
보안 점검 스크립트
파일 권한, SSH 설정, 시스템 보안 정책 검증
"""
import sys
import os
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.logger import get_logger
from storage import db, Notification

logger = get_logger()


class SecurityIssue:
    """보안 이슈 정의"""
    
    SEVERITY_CRITICAL = "CRITICAL"
    SEVERITY_HIGH = "HIGH"
    SEVERITY_MEDIUM = "MEDIUM"
    SEVERITY_LOW = "LOW"
    SEVERITY_INFO = "INFO"
    
    def __init__(self, category: str, severity: str, title: str, 
                 description: str, recommendation: str):
        self.category = category
        self.severity = severity
        self.title = title
        self.description = description
        self.recommendation = recommendation
        self.detected_at = datetime.now()
    
    def __repr__(self):
        return (
            f"[{self.severity}] {self.category}: {self.title}\n"
            f"  Description: {self.description}\n"
            f"  Recommendation: {self.recommendation}"
        )


class SecurityChecker:
    """보안 점검기"""
    
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.checks_passed = 0
        self.checks_failed = 0
        self.checks_skipped = 0
        
        # 점검 대상 파일 목록
        self.sensitive_files = [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/group',
            '/etc/gshadow',
            '/etc/ssh/sshd_config',
            '/etc/sudoers'
        ]
    
    def add_issue(self, category: str, severity: str, title: str, 
                  description: str, recommendation: str):
        """보안 이슈 추가"""
        issue = SecurityIssue(category, severity, title, description, recommendation)
        self.issues.append(issue)
        self.checks_failed += 1
        
        log_level = {
            SecurityIssue.SEVERITY_CRITICAL: logger.critical,
            SecurityIssue.SEVERITY_HIGH: logger.error,
            SecurityIssue.SEVERITY_MEDIUM: logger.warning,
            SecurityIssue.SEVERITY_LOW: logger.info,
            SecurityIssue.SEVERITY_INFO: logger.info,
        }
        
        log_func = log_level.get(severity, logger.info)
        log_func(f"[{severity}] {category}: {title}")
    
    def check_passed(self, message: str):
        """점검 통과"""
        self.checks_passed += 1
        logger.info(f"✅ {message}")
    
    def check_skipped(self, message: str):
        """점검 스킵"""
        self.checks_skipped += 1
        logger.debug(f"⊘ {message}")
    
    def check_file_permissions(self):
        """중요 파일의 권한 검사"""
        logger.info("=" * 60)
        logger.info("🔒 Checking file permissions...")
        logger.info("=" * 60)
        
        for file_path in self.sensitive_files:
            path = Path(file_path)
            
            if not path.exists():
                self.check_skipped(f"File not found: {file_path}")
                continue
            
            try:
                stat_info = path.stat()
                mode = stat_info.st_mode
                
                # 파일 권한 (8진수)
                perms = oct(mode)[-3:]
                
                # 기대되는 권한
                expected_perms = {
                    '/etc/passwd': '644',
                    '/etc/group': '644',
                    '/etc/shadow': '640',
                    '/etc/gshadow': '640',
                    '/etc/ssh/sshd_config': '600',
                    '/etc/sudoers': '440'
                }
                
                expected = expected_perms.get(file_path, '644')
                
                if perms != expected:
                    self.add_issue(
                        category="File Permissions",
                        severity=SecurityIssue.SEVERITY_HIGH,
                        title=f"Incorrect permissions on {file_path}",
                        description=f"Current: {perms}, Expected: {expected}",
                        recommendation=f"Run: sudo chmod {expected} {file_path}"
                    )
                else:
                    self.check_passed(f"Correct permissions on {file_path}: {perms}")
                
                # 소유자 검사 (root여야 함)
                if stat_info.st_uid != 0:
                    self.add_issue(
                        category="File Ownership",
                        severity=SecurityIssue.SEVERITY_HIGH,
                        title=f"Incorrect owner on {file_path}",
                        description=f"Current UID: {stat_info.st_uid}, Expected: 0 (root)",
                        recommendation=f"Run: sudo chown root:root {file_path}"
                    )
                else:
                    self.check_passed(f"Correct owner on {file_path}: root")
            
            except Exception as e:
                logger.error(f"Error checking {file_path}: {e}")
                self.check_skipped(f"Cannot check {file_path}")
    
    def check_ssh_config(self):
        """SSH 설정 검사"""
        logger.info("=" * 60)
        logger.info("🔐 Checking SSH configuration...")
        logger.info("=" * 60)
        
        ssh_config = Path('/etc/ssh/sshd_config')
        
        if not ssh_config.exists():
            self.check_skipped("SSH config not found")
            return
        
        try:
            with open(ssh_config, 'r') as f:
                config_lines = f.readlines()
            
            # 보안 설정 체크리스트
            checks = {
                'PermitRootLogin': 'no',
                'PasswordAuthentication': 'no',
                'PermitEmptyPasswords': 'no',
                'X11Forwarding': 'no',
                'MaxAuthTries': '3',
                'Protocol': '2'
            }
            
            config_dict = {}
            for line in config_lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0]
                        value = parts[1]
                        config_dict[key] = value
            
            for setting, expected_value in checks.items():
                current_value = config_dict.get(setting)
                
                if current_value is None:
                    # 설정이 없으면 기본값 사용 (주의 필요)
                    if setting in ['PermitRootLogin', 'PasswordAuthentication']:
                        self.add_issue(
                            category="SSH Configuration",
                            severity=SecurityIssue.SEVERITY_MEDIUM,
                            title=f"SSH setting not explicitly set: {setting}",
                            description=f"Recommended: {setting} {expected_value}",
                            recommendation=f"Add '{setting} {expected_value}' to {ssh_config}"
                        )
                    else:
                        self.check_skipped(f"SSH setting not set: {setting}")
                
                elif current_value.lower() != expected_value.lower():
                    severity = SecurityIssue.SEVERITY_HIGH
                    if setting in ['X11Forwarding', 'MaxAuthTries', 'Protocol']:
                        severity = SecurityIssue.SEVERITY_MEDIUM
                    
                    self.add_issue(
                        category="SSH Configuration",
                        severity=severity,
                        title=f"Insecure SSH setting: {setting}",
                        description=f"Current: {current_value}, Recommended: {expected_value}",
                        recommendation=f"Set '{setting} {expected_value}' in {ssh_config}"
                    )
                else:
                    self.check_passed(f"SSH setting OK: {setting} = {current_value}")
        
        except Exception as e:
            logger.error(f"Error checking SSH config: {e}")
            self.check_skipped("Cannot read SSH config")
    
    def check_open_ports(self):
        """열린 포트 확인"""
        logger.info("=" * 60)
        logger.info("🔌 Checking open ports...")
        logger.info("=" * 60)
        
        try:
            # ss 명령어 사용 (Linux)
            result = subprocess.run(
                ['ss', '-tuln'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.check_skipped("Cannot check open ports (ss command failed)")
                return
            
            lines = result.stdout.strip().split('\n')[1:]  # 헤더 제외
            
            listening_ports = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 5 and 'LISTEN' in line:
                    local_addr = parts[4]
                    if ':' in local_addr:
                        port = local_addr.split(':')[-1]
                        listening_ports.append(port)
            
            # 일반적으로 안전한 포트
            common_safe_ports = ['22', '80', '443', '53']
            
            # 위험한 포트 (예시)
            risky_ports = ['23', '21', '3389', '5900']  # telnet, ftp, rdp, vnc
            
            logger.info(f"Found {len(set(listening_ports))} listening ports")
            
            for port in set(listening_ports):
                if port in risky_ports:
                    self.add_issue(
                        category="Network Security",
                        severity=SecurityIssue.SEVERITY_HIGH,
                        title=f"Risky port open: {port}",
                        description=f"Port {port} is listening and may be insecure",
                        recommendation=f"Close port {port} if not needed"
                    )
                elif port not in common_safe_ports:
                    logger.info(f"ℹ️  Port {port} is listening (review if needed)")
                else:
                    self.check_passed(f"Common port listening: {port}")
        
        except FileNotFoundError:
            self.check_skipped("ss command not available")
        except Exception as e:
            logger.error(f"Error checking ports: {e}")
            self.check_skipped("Cannot check open ports")
    
    def check_password_policy(self):
        """비밀번호 정책 검사"""
        logger.info("=" * 60)
        logger.info("🔑 Checking password policy...")
        logger.info("=" * 60)
        
        # /etc/login.defs 검사
        login_defs = Path('/etc/login.defs')
        
        if not login_defs.exists():
            self.check_skipped("login.defs not found")
            return
        
        try:
            with open(login_defs, 'r') as f:
                lines = f.readlines()
            
            config = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        config[parts[0]] = parts[1]
            
            # 비밀번호 정책 체크
            pass_max_days = int(config.get('PASS_MAX_DAYS', 99999))
            pass_min_days = int(config.get('PASS_MIN_DAYS', 0))
            pass_warn_age = int(config.get('PASS_WARN_AGE', 7))
            
            if pass_max_days > 90:
                self.add_issue(
                    category="Password Policy",
                    severity=SecurityIssue.SEVERITY_MEDIUM,
                    title="Password expiry too long",
                    description=f"PASS_MAX_DAYS is {pass_max_days} (recommended: 90)",
                    recommendation="Set PASS_MAX_DAYS 90 in /etc/login.defs"
                )
            else:
                self.check_passed(f"Password max age OK: {pass_max_days} days")
            
            if pass_min_days < 1:
                self.add_issue(
                    category="Password Policy",
                    severity=SecurityIssue.SEVERITY_LOW,
                    title="No minimum password age",
                    description=f"PASS_MIN_DAYS is {pass_min_days} (recommended: 1+)",
                    recommendation="Set PASS_MIN_DAYS 1 in /etc/login.defs"
                )
            else:
                self.check_passed(f"Password min age OK: {pass_min_days} days")
            
            if pass_warn_age < 7:
                logger.info(f"ℹ️  Password warning age: {pass_warn_age} days (recommended: 7+)")
            else:
                self.check_passed(f"Password warning age OK: {pass_warn_age} days")
        
        except Exception as e:
            logger.error(f"Error checking password policy: {e}")
            self.check_skipped("Cannot check password policy")
    
    def check_firewall_status(self):
        """방화벽 상태 확인"""
        logger.info("=" * 60)
        logger.info("🔥 Checking firewall status...")
        logger.info("=" * 60)
        
        try:
            # ufw 상태 확인
            result = subprocess.run(
                ['ufw', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                if 'inactive' in result.stdout.lower():
                    self.add_issue(
                        category="Firewall",
                        severity=SecurityIssue.SEVERITY_HIGH,
                        title="Firewall is inactive",
                        description="UFW firewall is not enabled",
                        recommendation="Run: sudo ufw enable"
                    )
                else:
                    self.check_passed("Firewall (ufw) is active")
                    logger.info(f"Firewall status:\n{result.stdout}")
            else:
                self.check_skipped("UFW not available")
        
        except FileNotFoundError:
            # iptables 확인
            try:
                result = subprocess.run(
                    ['iptables', '-L', '-n'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    rule_count = len(result.stdout.strip().split('\n'))
                    if rule_count < 10:  # 매우 간단한 휴리스틱
                        logger.warning("⚠️  Firewall rules seem minimal")
                    else:
                        self.check_passed(f"Firewall (iptables) has {rule_count} lines")
                else:
                    self.check_skipped("Cannot check iptables")
            
            except FileNotFoundError:
                self.check_skipped("No firewall found (ufw/iptables)")
        
        except Exception as e:
            logger.error(f"Error checking firewall: {e}")
            self.check_skipped("Cannot check firewall")
    
    def calculate_security_score(self) -> int:
        """보안 점수 계산 (0-100)"""
        total_checks = self.checks_passed + self.checks_failed
        
        if total_checks == 0:
            return 0
        
        # 기본 점수
        base_score = (self.checks_passed / total_checks) * 100
        
        # 심각도별 감점
        severity_penalties = {
            SecurityIssue.SEVERITY_CRITICAL: 20,
            SecurityIssue.SEVERITY_HIGH: 10,
            SecurityIssue.SEVERITY_MEDIUM: 5,
            SecurityIssue.SEVERITY_LOW: 2,
            SecurityIssue.SEVERITY_INFO: 0
        }
        
        penalty = 0
        for issue in self.issues:
            penalty += severity_penalties.get(issue.severity, 0)
        
        final_score = max(0, int(base_score - penalty))
        return final_score
    
    def generate_report(self) -> str:
        """보안 점검 보고서 생성"""
        score = self.calculate_security_score()
        
        report_lines = [
            "=" * 60,
            "🛡️  SECURITY CHECK REPORT",
            "=" * 60,
            f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Platform: {platform.system()} {platform.release()}",
            "",
            "📊 Summary:",
            f"  Security Score: {score}/100",
            f"  Checks Passed: {self.checks_passed}",
            f"  Checks Failed: {self.checks_failed}",
            f"  Checks Skipped: {self.checks_skipped}",
            f"  Issues Found: {len(self.issues)}",
            "",
        ]
        
        if self.issues:
            # 심각도별로 그룹화
            issues_by_severity = {}
            for issue in self.issues:
                if issue.severity not in issues_by_severity:
                    issues_by_severity[issue.severity] = []
                issues_by_severity[issue.severity].append(issue)
            
            # CRITICAL부터 순서대로
            severity_order = [
                SecurityIssue.SEVERITY_CRITICAL,
                SecurityIssue.SEVERITY_HIGH,
                SecurityIssue.SEVERITY_MEDIUM,
                SecurityIssue.SEVERITY_LOW,
                SecurityIssue.SEVERITY_INFO
            ]
            
            report_lines.append("🚨 Issues Found:")
            report_lines.append("")
            
            for severity in severity_order:
                if severity in issues_by_severity:
                    issues = issues_by_severity[severity]
                    report_lines.append(f"[{severity}] - {len(issues)} issue(s)")
                    report_lines.append("-" * 60)
                    
                    for i, issue in enumerate(issues, 1):
                        report_lines.append(f"{i}. {issue.title}")
                        report_lines.append(f"   Category: {issue.category}")
                        report_lines.append(f"   Description: {issue.description}")
                        report_lines.append(f"   Recommendation: {issue.recommendation}")
                        report_lines.append("")
        else:
            report_lines.append("✅ No security issues found!")
        
        report_lines.append("=" * 60)
        
        return '\n'.join(report_lines)
    
    def save_to_database(self, report: str, score: int):
        """결과를 데이터베이스에 저장"""
        try:
            severity_level = "INFO"
            if score < 50:
                severity_level = "CRITICAL"
            elif score < 70:
                severity_level = "WARNING"
            
            with db.session_scope() as session:
                notification = Notification(
                    title=f"Security Check Complete - Score: {score}/100",
                    message=report,
                    level=severity_level,
                    channel="security_check",
                    success=True
                )
                session.add(notification)
            
            logger.info("✅ Security check results saved to database")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    def run_all_checks(self):
        """모든 보안 점검 실행"""
        logger.info("=" * 60)
        logger.info("🛡️  Security Checker Started")
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        logger.info("=" * 60)
        
        # 권한 체크
        if os.geteuid() != 0:
            logger.warning("⚠️  Not running as root - some checks may be skipped")
        
        # 각 점검 실행
        self.check_file_permissions()
        self.check_ssh_config()
        self.check_open_ports()
        self.check_password_policy()
        self.check_firewall_status()
        
        # 보고서 생성
        report = self.generate_report()
        print("\n" + report)
        
        # 보안 점수
        score = self.calculate_security_score()
        
        # 데이터베이스 저장
        self.save_to_database(report, score)
        
        logger.info("=" * 60)
        logger.info("✅ Security Check Completed")
        logger.info("=" * 60)
        
        # 심각한 이슈가 있으면 종료 코드 1
        critical_issues = [i for i in self.issues 
                          if i.severity == SecurityIssue.SEVERITY_CRITICAL]
        return 1 if critical_issues else 0


def main():
    """메인 실행 함수"""
    try:
        checker = SecurityChecker()
        exit_code = checker.run_all_checks()
        return exit_code
    
    except Exception as e:
        logger.error(f"❌ Error during security check: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
