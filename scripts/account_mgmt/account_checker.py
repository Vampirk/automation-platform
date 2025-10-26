#!/usr/bin/env python3
"""
계정 정책 검사기 (Account Checker)
목적: 사용자 계정 정책 검증 및 의심스러운 계정 탐지
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
수정 이력:
  - 2025-10-26: 초기 버전 생성
"""

import sys
import pwd
import grp
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

# 프로젝트 루트
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Windows 지원
try:
    import win32net
    import win32netcon
    import win32security
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from config import settings
from core.logger import get_logger
from storage import db
from storage.models import Notification

logger = get_logger()


class AccountChecker:
    """
    계정 정책 검사기
    
    기능:
    - 모든 사용자 계정 조회
    - UID 0 계정 탐지 (root 외)
    - sudo/admin 그룹 멤버 확인
    - 쉘 접근 가능 계정 확인
    - 시스템 계정 vs 사용자 계정 구분
    """
    
    def __init__(self):
        """초기화"""
        self.accounts = []
        self.suspicious_accounts = []
        self.admin_accounts = []
        self.system_accounts = []
        self.user_accounts = []
    
    def get_all_accounts_linux(self) -> List[Dict]:
        """
        Linux: 모든 계정 조회 (/etc/passwd)
        
        Returns:
            계정 정보 리스트
        """
        accounts = []
        
        try:
            for user in pwd.getpwall():
                account = {
                    'username': user.pw_name,
                    'uid': user.pw_uid,
                    'gid': user.pw_gid,
                    'home': user.pw_dir,
                    'shell': user.pw_shell,
                    'gecos': user.pw_gecos,
                }
                
                # 그룹 정보
                try:
                    group = grp.getgrgid(user.pw_gid)
                    account['group'] = group.gr_name
                except KeyError:
                    account['group'] = str(user.pw_gid)
                
                # sudo 권한 확인
                account['is_sudoer'] = self._is_sudoer_linux(user.pw_name)
                
                # 로그인 가능 여부
                account['can_login'] = not user.pw_shell.endswith(('nologin', 'false'))
                
                # 시스템 계정 vs 사용자 계정 (UID 기준)
                if user.pw_uid < 1000:
                    account['type'] = 'system'
                else:
                    account['type'] = 'user'
                
                accounts.append(account)
        
        except Exception as e:
            logger.error(f"Failed to read accounts: {e}")
        
        return accounts
    
    def get_all_accounts_windows(self) -> List[Dict]:
        """
        Windows: 모든 계정 조회
        
        Returns:
            계정 정보 리스트
        """
        if not HAS_WIN32:
            logger.error("pywin32 not installed")
            return []
        
        accounts = []
        
        try:
            resume = 0
            while True:
                users, total, resume = win32net.NetUserEnum(
                    None, 2, win32netcon.FILTER_NORMAL_ACCOUNT, resume
                )
                
                for user in users:
                    account = {
                        'username': user['name'],
                        'full_name': user.get('full_name', ''),
                        'comment': user.get('comment', ''),
                        'flags': user['flags'],
                        'priv': user['priv'],
                    }
                    
                    # 관리자 권한 확인
                    account['is_admin'] = self._is_admin_windows(user['name'])
                    
                    # 계정 활성화 상태
                    account['disabled'] = bool(user['flags'] & win32netcon.UF_ACCOUNTDISABLE)
                    
                    # 계정 타입
                    if user['priv'] == win32netcon.USER_PRIV_ADMIN:
                        account['type'] = 'admin'
                    elif user['flags'] & win32netcon.UF_WORKSTATION_TRUST_ACCOUNT:
                        account['type'] = 'machine'
                    else:
                        account['type'] = 'user'
                    
                    accounts.append(account)
                
                if resume == 0:
                    break
        
        except Exception as e:
            logger.error(f"Failed to read Windows accounts: {e}")
        
        return accounts
    
    def _is_sudoer_linux(self, username: str) -> bool:
        """
        Linux: sudo 권한 확인
        
        Args:
            username: 사용자명
            
        Returns:
            sudo 권한 여부
        """
        try:
            # sudo, wheel, admin 그룹 멤버십 확인
            sudo_groups = ['sudo', 'wheel', 'admin']
            
            for group_name in sudo_groups:
                try:
                    group = grp.getgrnam(group_name)
                    if username in group.gr_mem:
                        return True
                except KeyError:
                    continue
            
            # 직접 확인 (sudo -l)
            result = subprocess.run(
                ['sudo', '-l', '-U', username],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return 'not allowed' not in result.stdout.lower()
        
        except Exception:
            return False
    
    def _is_admin_windows(self, username: str) -> bool:
        """
        Windows: 관리자 권한 확인
        
        Args:
            username: 사용자명
            
        Returns:
            관리자 여부
        """
        if not HAS_WIN32:
            return False
        
        try:
            # Administrators 그룹 SID
            admin_sid = win32security.ConvertStringSidToSid('S-1-5-32-544')
            
            # 사용자 그룹 조회
            user_groups = win32net.NetUserGetLocalGroups(None, username)
            
            for group in user_groups:
                if 'administrators' in group.lower():
                    return True
            
            return False
        
        except Exception:
            return False
    
    def check_accounts(self) -> Dict:
        """
        계정 검사 실행
        
        Returns:
            검사 결과
        """
        logger.info("=" * 60)
        logger.info("👥 Account Policy Checker Started")
        logger.info("=" * 60)
        
        # 플랫폼별 계정 조회
        if settings.is_linux():
            self.accounts = self.get_all_accounts_linux()
            self._check_suspicious_linux()
        elif settings.is_windows():
            self.accounts = self.get_all_accounts_windows()
            self._check_suspicious_windows()
        else:
            logger.error("Unsupported platform")
            return {}
        
        # 분류
        self._classify_accounts()
        
        # 통계 생성
        stats = self._generate_statistics()
        
        # 알림 저장
        self._save_alerts()
        
        logger.info("=" * 60)
        logger.info("✅ Account Check Completed")
        logger.info("=" * 60)
        
        return stats
    
    def _check_suspicious_linux(self):
        """Linux: 의심스러운 계정 탐지"""
        for account in self.accounts:
            issues = []
            
            # UID 0인 비root 계정
            if account['uid'] == 0 and account['username'] != 'root':
                issues.append('UID 0 (root privileges)')
            
            # 이상한 쉘 (사용자 계정인데 /bin/bash가 아님)
            if account['type'] == 'user' and account['can_login']:
                if account['shell'] not in ['/bin/bash', '/bin/zsh', '/bin/sh']:
                    issues.append(f"Unusual shell: {account['shell']}")
            
            # 홈 디렉토리가 /root가 아닌데 UID < 1000
            if account['uid'] < 1000 and account['home'].startswith('/home/'):
                issues.append('System UID with user home directory')
            
            # sudo 권한 있는 시스템 계정
            if account['type'] == 'system' and account['is_sudoer']:
                issues.append('System account with sudo privileges')
            
            if issues:
                self.suspicious_accounts.append({
                    'account': account,
                    'issues': issues
                })
    
    def _check_suspicious_windows(self):
        """Windows: 의심스러운 계정 탐지"""
        for account in self.accounts:
            issues = []
            
            # 관리자 권한인 일반 계정
            if account['type'] == 'user' and account['is_admin']:
                issues.append('User account with admin privileges')
            
            # 비활성화되지 않은 오래된 계정 (추가 로직 필요)
            
            if issues:
                self.suspicious_accounts.append({
                    'account': account,
                    'issues': issues
                })
    
    def _classify_accounts(self):
        """계정 분류"""
        for account in self.accounts:
            if settings.is_linux():
                if account.get('is_sudoer'):
                    self.admin_accounts.append(account)
                
                if account['type'] == 'system':
                    self.system_accounts.append(account)
                else:
                    self.user_accounts.append(account)
            
            elif settings.is_windows():
                if account.get('is_admin'):
                    self.admin_accounts.append(account)
                
                if account['type'] == 'user':
                    self.user_accounts.append(account)
                else:
                    self.system_accounts.append(account)
    
    def _generate_statistics(self) -> Dict:
        """통계 생성"""
        stats = {
            'total_accounts': len(self.accounts),
            'user_accounts': len(self.user_accounts),
            'system_accounts': len(self.system_accounts),
            'admin_accounts': len(self.admin_accounts),
            'suspicious_accounts': len(self.suspicious_accounts),
            'suspicious_details': self.suspicious_accounts,
            'platform': 'linux' if settings.is_linux() else 'windows',
        }
        
        return stats
    
    def _save_alerts(self):
        """의심스러운 계정 알림 저장"""
        for item in self.suspicious_accounts:
            account = item['account']
            issues = item['issues']
            
            try:
                with db.session_scope() as session:
                    notification = Notification(
                        title=f"Suspicious Account: {account.get('username')}",
                        message=f"Issues: {', '.join(issues)}",
                        level='HIGH',
                        channel='account_check',
                        sent_at=datetime.now(timezone.utc)
                    )
                    session.add(notification)
            except Exception as e:
                logger.error(f"Failed to save alert: {e}")
    
    def print_report(self, stats: Dict):
        """리포트 출력"""
        print("\n" + "=" * 60)
        print("👥 Account Policy Check Report")
        print("=" * 60)
        print(f"Platform: {stats['platform'].upper()}")
        print(f"Total Accounts: {stats['total_accounts']}")
        print(f"  User Accounts: {stats['user_accounts']}")
        print(f"  System Accounts: {stats['system_accounts']}")
        print(f"  Admin/Sudo Accounts: {stats['admin_accounts']}")
        
        if stats['suspicious_accounts'] > 0:
            print(f"\n🚨 Suspicious Accounts: {stats['suspicious_accounts']}")
            for item in stats['suspicious_details']:
                account = item['account']
                issues = item['issues']
                print(f"\n  ⚠️  {account.get('username')}")
                for issue in issues:
                    print(f"      - {issue}")
                
                if settings.is_linux():
                    print(f"      UID: {account['uid']}, Shell: {account['shell']}")
                elif settings.is_windows():
                    print(f"      Type: {account['type']}, Disabled: {account.get('disabled', False)}")
        else:
            print("\n✅ No suspicious accounts found")
        
        print("=" * 60)


def main():
    """메인 실행 함수"""
    try:
        checker = AccountChecker()
        stats = checker.check_accounts()
        checker.print_report(stats)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error during account check: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
