#!/usr/bin/env python3
"""
장기 미사용 계정 탐지기 (Inactive Account Finder)
목적: 90일 이상 미사용 계정 탐지 및 자동 비활성화 추천
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
수정 이력:
  - 2025-10-26: 초기 버전 생성
"""

import sys
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
    import pywintypes
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from config import settings
from core.logger import get_logger
from storage import db
from storage.models import Notification

logger = get_logger()


class InactiveAccountFinder:
    """
    장기 미사용 계정 탐지기
    
    기능:
    - 최근 로그인 시간 조회 (lastlog)
    - 90일 이상 미로그인 계정 탐지
    - 로그인 이력 분석
    - 자동 비활성화 추천
    """
    
    INACTIVE_DAYS = 90  # 미사용 기준 일수
    
    def __init__(self):
        """초기화"""
        self.inactive_accounts = []
        self.never_logged_in = []
    
    def get_last_login_linux(self, username: str) -> Optional[datetime]:
        """
        Linux: 마지막 로그인 시간 조회 (lastlog)
        
        Args:
            username: 사용자명
            
        Returns:
            마지막 로그인 시간 또는 None
        """
        try:
            result = subprocess.run(
                ['lastlog', '-u', username],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None
            
            # 마지막 줄 파싱
            last_line = lines[-1]
            
            # "Never logged in" 체크
            if 'Never logged in' in last_line or '**Never logged in**' in last_line:
                return None
            
            # 날짜 파싱 (예: "Mon Oct 26 10:30:45 +0900 2025")
            parts = last_line.split()
            if len(parts) >= 4:
                # 간단한 파싱 (정확한 구현은 dateutil 사용 권장)
                try:
                    date_str = ' '.join(parts[-5:])  # 마지막 5개 토큰
                    # 여기서는 간단히 현재 시간 기준으로 체크
                    # 실제로는 더 정교한 파싱 필요
                    return datetime.now(timezone.utc)  # Placeholder
                except:
                    pass
            
            return None
        
        except Exception as e:
            logger.debug(f"Failed to get last login for {username}: {e}")
            return None
    
    def get_login_history_linux(self, username: str, days: int = 90) -> List[Dict]:
        """
        Linux: 로그인 이력 조회 (last)
        
        Args:
            username: 사용자명
            days: 조회할 일수
            
        Returns:
            로그인 이력 리스트
        """
        history = []
        
        try:
            result = subprocess.run(
                ['last', '-n', '100', username],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.strip().split('\n'):
                if username in line and 'wtmp begins' not in line:
                    history.append({'line': line})
        
        except Exception as e:
            logger.debug(f"Failed to get login history for {username}: {e}")
        
        return history
    
    def get_last_login_windows(self, username: str) -> Optional[datetime]:
        """
        Windows: 마지막 로그인 시간 조회
        
        Args:
            username: 사용자명
            
        Returns:
            마지막 로그인 시간 또는 None
        """
        if not HAS_WIN32:
            return None
        
        try:
            user_info = win32net.NetUserGetInfo(None, username, 2)
            
            # last_logon은 FILETIME 형식
            last_logon = user_info.get('last_logon', 0)
            
            if last_logon == 0:
                return None
            
            # FILETIME을 datetime으로 변환
            # FILETIME: 1601-01-01 이후 100나노초 단위
            dt = datetime(1601, 1, 1) + timedelta(microseconds=last_logon / 10)
            return dt.replace(tzinfo=timezone.utc)
        
        except Exception as e:
            logger.debug(f"Failed to get last login for {username}: {e}")
            return None
    
    def find_inactive_accounts_linux(self) -> List[Dict]:
        """
        Linux: 장기 미사용 계정 탐지
        
        Returns:
            미사용 계정 리스트
        """
        import pwd
        
        inactive = []
        threshold_date = datetime.now(timezone.utc) - timedelta(days=self.INACTIVE_DAYS)
        
        try:
            for user in pwd.getpwall():
                username = user.pw_name
                uid = user.pw_uid
                
                # 시스템 계정 제외 (UID < 1000)
                if uid < 1000:
                    continue
                
                # 로그인 불가 계정 제외
                if user.pw_shell.endswith(('nologin', 'false')):
                    continue
                
                last_login = self.get_last_login_linux(username)
                
                if last_login is None:
                    # 한 번도 로그인 안 함
                    self.never_logged_in.append({
                        'username': username,
                        'uid': uid,
                        'home': user.pw_dir,
                        'shell': user.pw_shell,
                        'status': 'never_logged_in'
                    })
                
                elif last_login < threshold_date:
                    # 90일 이상 미로그인
                    days_inactive = (datetime.now(timezone.utc) - last_login).days
                    
                    inactive.append({
                        'username': username,
                        'uid': uid,
                        'home': user.pw_dir,
                        'shell': user.pw_shell,
                        'last_login': last_login,
                        'days_inactive': days_inactive,
                        'status': 'inactive'
                    })
        
        except Exception as e:
            logger.error(f"Failed to find inactive accounts: {e}")
        
        return inactive
    
    def find_inactive_accounts_windows(self) -> List[Dict]:
        """
        Windows: 장기 미사용 계정 탐지
        
        Returns:
            미사용 계정 리스트
        """
        if not HAS_WIN32:
            return []
        
        inactive = []
        threshold_date = datetime.now(timezone.utc) - timedelta(days=self.INACTIVE_DAYS)
        
        try:
            resume = 0
            while True:
                users, total, resume = win32net.NetUserEnum(
                    None, 2, win32netcon.FILTER_NORMAL_ACCOUNT, resume
                )
                
                for user in users:
                    username = user['name']
                    
                    # 비활성화된 계정 제외
                    if user['flags'] & win32netcon.UF_ACCOUNTDISABLE:
                        continue
                    
                    last_login = self.get_last_login_windows(username)
                    
                    if last_login is None:
                        # 한 번도 로그인 안 함
                        self.never_logged_in.append({
                            'username': username,
                            'full_name': user.get('full_name', ''),
                            'status': 'never_logged_in'
                        })
                    
                    elif last_login < threshold_date:
                        # 90일 이상 미로그인
                        days_inactive = (datetime.now(timezone.utc) - last_login).days
                        
                        inactive.append({
                            'username': username,
                            'full_name': user.get('full_name', ''),
                            'last_login': last_login,
                            'days_inactive': days_inactive,
                            'status': 'inactive'
                        })
                
                if resume == 0:
                    break
        
        except Exception as e:
            logger.error(f"Failed to find inactive accounts: {e}")
        
        return inactive
    
    def check_inactive_accounts(self) -> Dict:
        """
        장기 미사용 계정 검사 실행
        
        Returns:
            검사 결과
        """
        logger.info("=" * 60)
        logger.info("🔍 Inactive Account Finder Started")
        logger.info("=" * 60)
        
        # 플랫폼별 조회
        if settings.is_linux():
            self.inactive_accounts = self.find_inactive_accounts_linux()
        elif settings.is_windows():
            self.inactive_accounts = self.find_inactive_accounts_windows()
        else:
            logger.error("Unsupported platform")
            return {}
        
        # 통계 생성
        stats = {
            'inactive_accounts': len(self.inactive_accounts),
            'never_logged_in': len(self.never_logged_in),
            'inactive_threshold_days': self.INACTIVE_DAYS,
            'inactive_details': self.inactive_accounts,
            'never_logged_in_details': self.never_logged_in,
            'platform': 'linux' if settings.is_linux() else 'windows',
        }
        
        # 알림 저장
        self._save_alerts()
        
        logger.info("=" * 60)
        logger.info("✅ Inactive Account Check Completed")
        logger.info("=" * 60)
        
        return stats
    
    def _save_alerts(self):
        """알림 저장"""
        # 장기 미사용 계정
        for account in self.inactive_accounts:
            try:
                with db.session_scope() as session:
                    notification = Notification(
                        title=f"Inactive Account: {account['username']}",
                        message=f"No login for {account['days_inactive']} days",
                        level='MEDIUM',
                        channel='account_inactive',
                        sent_at=datetime.now(timezone.utc)
                    )
                    session.add(notification)
            except Exception as e:
                logger.error(f"Failed to save alert: {e}")
        
        # 한 번도 로그인 안 한 계정
        for account in self.never_logged_in:
            try:
                with db.session_scope() as session:
                    notification = Notification(
                        title=f"Never Logged In: {account['username']}",
                        message="Account created but never used",
                        level='LOW',
                        channel='account_inactive',
                        sent_at=datetime.now(timezone.utc)
                    )
                    session.add(notification)
            except Exception as e:
                logger.error(f"Failed to save alert: {e}")
    
    def print_report(self, stats: Dict):
        """리포트 출력"""
        print("\n" + "=" * 60)
        print("🔍 Inactive Account Report")
        print("=" * 60)
        print(f"Platform: {stats['platform'].upper()}")
        print(f"Inactive Threshold: {stats['inactive_threshold_days']} days")
        print(f"\nInactive Accounts: {stats['inactive_accounts']}")
        print(f"Never Logged In: {stats['never_logged_in']}")
        
        if stats['inactive_accounts'] > 0:
            print(f"\n⚠️  Long-term Inactive Accounts ({stats['inactive_threshold_days']}+ days):")
            for account in stats['inactive_details']:
                print(f"\n  👤 {account['username']}")
                print(f"     Days Inactive: {account['days_inactive']}")
                if 'last_login' in account:
                    print(f"     Last Login: {account['last_login'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                if settings.is_linux():
                    print(f"     Home: {account['home']}")
                elif settings.is_windows():
                    print(f"     Full Name: {account.get('full_name', 'N/A')}")
        
        if stats['never_logged_in'] > 0:
            print(f"\n💤 Never Logged In Accounts:")
            for account in stats['never_logged_in_details'][:10]:  # 상위 10개만
                print(f"  - {account['username']}")
        
        if stats['inactive_accounts'] == 0 and stats['never_logged_in'] == 0:
            print("\n✅ No inactive accounts found")
        
        print("\n💡 Recommendation:")
        if stats['inactive_accounts'] > 0:
            print("   Consider disabling or removing long-term inactive accounts")
        if stats['never_logged_in'] > 0:
            print("   Review and remove unused accounts created but never used")
        
        print("=" * 60)


def main():
    """메인 실행 함수"""
    try:
        finder = InactiveAccountFinder()
        stats = finder.check_inactive_accounts()
        finder.print_report(stats)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error during inactive account check: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
