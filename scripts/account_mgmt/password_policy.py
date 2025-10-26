#!/usr/bin/env python3
"""
비밀번호 정책 검사기 (Password Policy Checker)
목적: 비밀번호 만료 임박 계정 탐지 및 정책 검증
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
수정 이력:
  - 2025-10-26: 초기 버전 생성
"""

import sys
import spwd
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

# 프로젝트 루트
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Windows 지원
try:
    import win32net
    import win32netcon
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from config import settings
from core.logger import get_logger
from storage import db
from storage.models import Notification

logger = get_logger()


class PasswordPolicyChecker:
    """
    비밀번호 정책 검사기
    
    기능:
    - 비밀번호 만료 임박 계정 탐지 (7일 이내)
    - 비밀번호 정책 검증 (/etc/login.defs)
    - 만료된 비밀번호 계정 확인
    - 비밀번호 변경 알림
    """
    
    EXPIRY_WARNING_DAYS = 7  # 만료 경고 기준 일수
    
    def __init__(self):
        """초기화"""
        self.expiring_soon = []
        self.expired = []
        self.policy = {}
    
    def get_password_policy_linux(self) -> Dict:
        """
        Linux: 비밀번호 정책 조회 (/etc/login.defs)
        
        Returns:
            정책 딕셔너리
        """
        policy = {
            'pass_max_days': None,
            'pass_min_days': None,
            'pass_min_len': None,
            'pass_warn_age': None,
        }
        
        try:
            login_defs = Path('/etc/login.defs')
            if login_defs.exists():
                with open(login_defs, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('#') or not line:
                            continue
                        
                        parts = line.split()
                        if len(parts) >= 2:
                            key = parts[0].lower()
                            value = parts[1]
                            
                            if key == 'pass_max_days':
                                policy['pass_max_days'] = int(value)
                            elif key == 'pass_min_days':
                                policy['pass_min_days'] = int(value)
                            elif key == 'pass_min_len':
                                policy['pass_min_len'] = int(value)
                            elif key == 'pass_warn_age':
                                policy['pass_warn_age'] = int(value)
        
        except Exception as e:
            logger.error(f"Failed to read password policy: {e}")
        
        return policy
    
    def get_password_status_linux(self, username: str) -> Dict:
        """
        Linux: 비밀번호 상태 조회 (passwd -S)
        
        Args:
            username: 사용자명
            
        Returns:
            비밀번호 상태
        """
        status = {
            'username': username,
            'locked': False,
            'password_set': True,
            'last_change': None,
            'min_days': None,
            'max_days': None,
            'warn_days': None,
            'inactive_days': None,
        }
        
        try:
            result = subprocess.run(
                ['passwd', '-S', username],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 출력 파싱: username P 10/26/2025 0 99999 7 -1
            parts = result.stdout.strip().split()
            if len(parts) >= 7:
                # P = password set, L = locked, NP = no password
                status['locked'] = (parts[1] == 'L')
                status['password_set'] = (parts[1] == 'P')
                
                # 날짜 파싱 (MM/DD/YYYY)
                if parts[2] != '0':
                    try:
                        status['last_change'] = datetime.strptime(parts[2], '%m/%d/%Y')
                    except:
                        pass
                
                status['min_days'] = int(parts[3])
                status['max_days'] = int(parts[4])
                status['warn_days'] = int(parts[5])
                status['inactive_days'] = int(parts[6])
        
        except Exception as e:
            logger.debug(f"Failed to get password status for {username}: {e}")
        
        return status
    
    def get_shadow_info_linux(self, username: str) -> Optional[Dict]:
        """
        Linux: /etc/shadow 정보 조회
        
        Args:
            username: 사용자명
            
        Returns:
            shadow 정보 또는 None
        """
        try:
            shadow = spwd.getspnam(username)
            
            # 마지막 변경일 (1970-01-01 이후 일수)
            last_change_days = shadow.sp_lstchg
            if last_change_days > 0:
                last_change = datetime(1970, 1, 1) + timedelta(days=last_change_days)
            else:
                last_change = None
            
            # 최대 일수
            max_days = shadow.sp_max if shadow.sp_max != 99999 else None
            
            # 만료일 계산
            expiry_date = None
            if last_change and max_days:
                expiry_date = last_change + timedelta(days=max_days)
            
            return {
                'last_change': last_change,
                'min_days': shadow.sp_min,
                'max_days': max_days,
                'warn_days': shadow.sp_warn,
                'inactive_days': shadow.sp_inact,
                'expiry_date': expiry_date,
            }
        
        except KeyError:
            return None
        except PermissionError:
            logger.warning("Need root privileges to read /etc/shadow")
            return None
        except Exception as e:
            logger.debug(f"Failed to read shadow for {username}: {e}")
            return None
    
    def get_password_expiry_windows(self, username: str) -> Optional[Dict]:
        """
        Windows: 비밀번호 만료 정보 조회
        
        Args:
            username: 사용자명
            
        Returns:
            만료 정보 또는 None
        """
        if not HAS_WIN32:
            return None
        
        try:
            user_info = win32net.NetUserGetInfo(None, username, 1)
            
            # password_age: 비밀번호 경과 시간 (초)
            password_age = user_info.get('password_age', 0)
            
            # 최대 비밀번호 나이 조회 (도메인 정책)
            # 기본값: 42일
            max_password_age = 42 * 24 * 3600  # 초 단위
            
            if password_age > 0:
                last_change = datetime.now(timezone.utc) - timedelta(seconds=password_age)
                expiry_date = last_change + timedelta(seconds=max_password_age)
                
                return {
                    'last_change': last_change,
                    'password_age_days': password_age / (24 * 3600),
                    'expiry_date': expiry_date,
                    'expires': not bool(user_info['flags'] & win32netcon.UF_DONT_EXPIRE_PASSWD),
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"Failed to get password expiry for {username}: {e}")
            return None
    
    def check_expiring_passwords_linux(self) -> List[Dict]:
        """
        Linux: 만료 임박 비밀번호 탐지
        
        Returns:
            만료 임박 계정 리스트
        """
        import pwd
        
        expiring = []
        expired = []
        threshold_date = datetime.now() + timedelta(days=self.EXPIRY_WARNING_DAYS)
        
        try:
            for user in pwd.getpwall():
                username = user.pw_name
                uid = user.pw_uid
                
                # 시스템 계정 제외
                if uid < 1000:
                    continue
                
                # 로그인 불가 계정 제외
                if user.pw_shell.endswith(('nologin', 'false')):
                    continue
                
                # shadow 정보 조회
                shadow_info = self.get_shadow_info_linux(username)
                if not shadow_info or not shadow_info['expiry_date']:
                    continue
                
                expiry_date = shadow_info['expiry_date']
                days_until_expiry = (expiry_date - datetime.now()).days
                
                account_info = {
                    'username': username,
                    'uid': uid,
                    'last_change': shadow_info['last_change'],
                    'expiry_date': expiry_date,
                    'days_until_expiry': days_until_expiry,
                }
                
                if days_until_expiry < 0:
                    # 이미 만료됨
                    expired.append(account_info)
                elif days_until_expiry <= self.EXPIRY_WARNING_DAYS:
                    # 만료 임박
                    expiring.append(account_info)
        
        except Exception as e:
            logger.error(f"Failed to check expiring passwords: {e}")
        
        self.expired = expired
        return expiring
    
    def check_expiring_passwords_windows(self) -> List[Dict]:
        """
        Windows: 만료 임박 비밀번호 탐지
        
        Returns:
            만료 임박 계정 리스트
        """
        if not HAS_WIN32:
            return []
        
        expiring = []
        expired = []
        threshold_date = datetime.now(timezone.utc) + timedelta(days=self.EXPIRY_WARNING_DAYS)
        
        try:
            resume = 0
            while True:
                users, total, resume = win32net.NetUserEnum(
                    None, 1, win32netcon.FILTER_NORMAL_ACCOUNT, resume
                )
                
                for user in users:
                    username = user['name']
                    
                    # 비밀번호 만료 안 함 플래그 확인
                    if user['flags'] & win32netcon.UF_DONT_EXPIRE_PASSWD:
                        continue
                    
                    expiry_info = self.get_password_expiry_windows(username)
                    if not expiry_info or not expiry_info['expires']:
                        continue
                    
                    expiry_date = expiry_info['expiry_date']
                    days_until_expiry = (expiry_date - datetime.now(timezone.utc)).days
                    
                    account_info = {
                        'username': username,
                        'last_change': expiry_info['last_change'],
                        'expiry_date': expiry_date,
                        'days_until_expiry': days_until_expiry,
                    }
                    
                    if days_until_expiry < 0:
                        expired.append(account_info)
                    elif days_until_expiry <= self.EXPIRY_WARNING_DAYS:
                        expiring.append(account_info)
                
                if resume == 0:
                    break
        
        except Exception as e:
            logger.error(f"Failed to check expiring passwords: {e}")
        
        self.expired = expired
        return expiring
    
    def check_password_policy(self) -> Dict:
        """
        비밀번호 정책 검사 실행
        
        Returns:
            검사 결과
        """
        logger.info("=" * 60)
        logger.info("🔐 Password Policy Checker Started")
        logger.info("=" * 60)
        
        # 플랫폼별 조회
        if settings.is_linux():
            self.policy = self.get_password_policy_linux()
            self.expiring_soon = self.check_expiring_passwords_linux()
        elif settings.is_windows():
            self.expiring_soon = self.check_expiring_passwords_windows()
        else:
            logger.error("Unsupported platform")
            return {}
        
        # 통계 생성
        stats = {
            'policy': self.policy,
            'expiring_soon': len(self.expiring_soon),
            'expired': len(self.expired),
            'expiry_warning_days': self.EXPIRY_WARNING_DAYS,
            'expiring_details': self.expiring_soon,
            'expired_details': self.expired,
            'platform': 'linux' if settings.is_linux() else 'windows',
        }
        
        # 알림 저장
        self._save_alerts()
        
        logger.info("=" * 60)
        logger.info("✅ Password Policy Check Completed")
        logger.info("=" * 60)
        
        return stats
    
    def _save_alerts(self):
        """알림 저장"""
        # 만료 임박
        for account in self.expiring_soon:
            try:
                with db.session_scope() as session:
                    notification = Notification(
                        title=f"Password Expiring Soon: {account['username']}",
                        message=f"Password expires in {account['days_until_expiry']} days",
                        level='HIGH',
                        channel='password_policy',
                        sent_at=datetime.now(timezone.utc)
                    )
                    session.add(notification)
            except Exception as e:
                logger.error(f"Failed to save alert: {e}")
        
        # 이미 만료됨
        for account in self.expired:
            try:
                with db.session_scope() as session:
                    notification = Notification(
                        title=f"Password Expired: {account['username']}",
                        message=f"Password expired {abs(account['days_until_expiry'])} days ago",
                        level='CRITICAL',
                        channel='password_policy',
                        sent_at=datetime.now(timezone.utc)
                    )
                    session.add(notification)
            except Exception as e:
                logger.error(f"Failed to save alert: {e}")
    
    def print_report(self, stats: Dict):
        """리포트 출력"""
        print("\n" + "=" * 60)
        print("🔐 Password Policy Report")
        print("=" * 60)
        print(f"Platform: {stats['platform'].upper()}")
        
        if stats['platform'] == 'linux' and stats['policy']:
            print(f"\n📋 System Password Policy:")
            policy = stats['policy']
            if policy['pass_max_days']:
                print(f"   Max Days: {policy['pass_max_days']}")
            if policy['pass_min_days']:
                print(f"   Min Days: {policy['pass_min_days']}")
            if policy['pass_min_len']:
                print(f"   Min Length: {policy['pass_min_len']}")
            if policy['pass_warn_age']:
                print(f"   Warning Days: {policy['pass_warn_age']}")
        
        print(f"\nExpiry Warning Threshold: {stats['expiry_warning_days']} days")
        print(f"Expiring Soon: {stats['expiring_soon']}")
        print(f"Already Expired: {stats['expired']}")
        
        if stats['expired'] > 0:
            print(f"\n🚨 CRITICAL - Expired Passwords:")
            for account in stats['expired_details']:
                print(f"\n  ⛔ {account['username']}")
                print(f"     Expired: {abs(account['days_until_expiry'])} days ago")
                if account['expiry_date']:
                    print(f"     Expiry Date: {account['expiry_date'].strftime('%Y-%m-%d')}")
        
        if stats['expiring_soon'] > 0:
            print(f"\n⚠️  Passwords Expiring Soon:")
            for account in stats['expiring_details']:
                print(f"\n  👤 {account['username']}")
                print(f"     Days Until Expiry: {account['days_until_expiry']}")
                if account['expiry_date']:
                    print(f"     Expiry Date: {account['expiry_date'].strftime('%Y-%m-%d')}")
        
        if stats['expiring_soon'] == 0 and stats['expired'] == 0:
            print("\n✅ No password expiry issues found")
        
        print("\n💡 Recommendation:")
        if stats['expired'] > 0:
            print("   Force password change for expired accounts immediately")
        if stats['expiring_soon'] > 0:
            print("   Notify users to change passwords before expiry")
        
        print("=" * 60)


def main():
    """메인 실행 함수"""
    try:
        checker = PasswordPolicyChecker()
        stats = checker.check_password_policy()
        checker.print_report(stats)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error during password policy check: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
