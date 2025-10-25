#!/usr/bin/env python3
"""
로그 분석 스크립트
실시간으로 /var/log/auth.log를 감시하여 Failed login 탐지
크로스 플랫폼 지원 (주로 Linux)
"""
import sys
import re
import time
import platform
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.logger import get_logger
from storage import db, Notification

logger = get_logger()


class FailedLoginTracker:
    """
    Failed login 추적기
    5분 내 5회 실패 시 경고
    """
    
    def __init__(self, time_window_minutes: int = 5, threshold: int = 5):
        """
        Args:
            time_window_minutes: 시간 윈도우 (분)
            threshold: 임계치 (실패 횟수)
        """
        self.time_window = timedelta(minutes=time_window_minutes)
        self.threshold = threshold
        
        # IP별 실패 시도 추적 (IP -> deque of timestamps)
        self.failed_attempts: Dict[str, deque] = defaultdict(lambda: deque())
        
        # 이미 경고한 IP (중복 알림 방지)
        self.alerted_ips: Dict[str, datetime] = {}
        
        # 알림 쿨다운 (같은 IP에 대해 30분에 1번만 알림)
        self.alert_cooldown = timedelta(minutes=30)
    
    def record_failure(self, ip: str, timestamp: datetime) -> Optional[dict]:
        """
        실패 기록 및 임계치 체크
        
        Args:
            ip: IP 주소
            timestamp: 실패 시각
            
        Returns:
            경고가 필요하면 경고 정보 딕셔너리, 아니면 None
        """
        # 오래된 기록 제거 (시간 윈도우 밖)
        cutoff_time = timestamp - self.time_window
        while self.failed_attempts[ip] and self.failed_attempts[ip][0] < cutoff_time:
            self.failed_attempts[ip].popleft()
        
        # 새 실패 기록
        self.failed_attempts[ip].append(timestamp)
        
        # 임계치 확인
        failure_count = len(self.failed_attempts[ip])
        
        if failure_count >= self.threshold:
            # 이미 최근에 알림을 보냈는지 확인
            if ip in self.alerted_ips:
                last_alert = self.alerted_ips[ip]
                if timestamp - last_alert < self.alert_cooldown:
                    return None  # 쿨다운 중
            
            # 경고 생성
            self.alerted_ips[ip] = timestamp
            
            return {
                'ip': ip,
                'failure_count': failure_count,
                'time_window': self.time_window.total_seconds() / 60,
                'first_attempt': self.failed_attempts[ip][0],
                'last_attempt': timestamp
            }
        
        return None


class LogAnalyzer:
    """로그 분석기"""
    
    # 로그 패턴 정의
    PATTERNS = {
        'failed_password': re.compile(
            r'Failed password for (?:invalid user )?(\w+) from ([\d.]+) port \d+'
        ),
        'authentication_failure': re.compile(
            r'authentication failure.*rhost=([\d.]+)'
        ),
        'invalid_user': re.compile(
            r'Invalid user (\w+) from ([\d.]+)'
        ),
        'connection_closed': re.compile(
            r'Connection closed by authenticating user (\w+) ([\d.]+) port \d+'
        ),
        'disconnected': re.compile(
            r'Disconnected from invalid user (\w+) ([\d.]+) port \d+'
        ),
    }
    
    def __init__(self, log_file: str = '/var/log/auth.log'):
        """
        Args:
            log_file: 로그 파일 경로
        """
        self.log_file = Path(log_file)
        self.tracker = FailedLoginTracker()
        
        # 통계
        self.stats = {
            'total_lines_processed': 0,
            'failed_logins_detected': 0,
            'alerts_generated': 0,
            'suspicious_ips': set()
        }
    
    def parse_log_line(self, line: str) -> Optional[dict]:
        """
        로그 라인 파싱
        
        Args:
            line: 로그 라인
            
        Returns:
            파싱된 정보 또는 None
        """
        self.stats['total_lines_processed'] += 1
        
        # 각 패턴 시도
        for pattern_name, pattern in self.PATTERNS.items():
            match = pattern.search(line)
            if match:
                self.stats['failed_logins_detected'] += 1
                
                # IP 추출
                groups = match.groups()
                if len(groups) >= 2:
                    username = groups[0]
                    ip = groups[1]
                elif len(groups) == 1:
                    username = 'unknown'
                    ip = groups[0]
                else:
                    continue
                
                return {
                    'pattern': pattern_name,
                    'username': username,
                    'ip': ip,
                    'line': line.strip(),
                    'timestamp': datetime.now()
                }
        
        return None
    
    def process_failure(self, failure_info: dict):
        """
        실패 정보 처리
        
        Args:
            failure_info: 파싱된 실패 정보
        """
        ip = failure_info['ip']
        username = failure_info['username']
        timestamp = failure_info['timestamp']
        
        logger.warning(
            f"Failed login detected: user={username}, ip={ip}, "
            f"pattern={failure_info['pattern']}"
        )
        
        # IP를 의심스러운 목록에 추가
        self.stats['suspicious_ips'].add(ip)
        
        # 임계치 체크
        alert = self.tracker.record_failure(ip, timestamp)
        
        if alert:
            self.generate_alert(alert, failure_info)
    
    def generate_alert(self, alert: dict, failure_info: dict):
        """
        경고 생성 및 저장
        
        Args:
            alert: 경고 정보
            failure_info: 실패 정보
        """
        self.stats['alerts_generated'] += 1
        
        ip = alert['ip']
        count = alert['failure_count']
        window = alert['time_window']
        
        message = (
            f"🚨 SECURITY ALERT: Suspicious activity detected!\n"
            f"IP: {ip}\n"
            f"Failed login attempts: {count} times in {window} minutes\n"
            f"Username attempted: {failure_info['username']}\n"
            f"First attempt: {alert['first_attempt']}\n"
            f"Last attempt: {alert['last_attempt']}\n"
            f"Pattern: {failure_info['pattern']}"
        )
        
        logger.critical(message)
        
        # 데이터베이스에 알림 저장
        try:
            with db.session_scope() as session:
                notification = Notification(
                    title=f"Suspicious Login Activity from {ip}",
                    message=message,
                    level="CRITICAL",
                    channel="log_analysis",
                    success=True
                )
                session.add(notification)
            
            logger.info(f"✅ Alert saved to database for IP {ip}")
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
    
    def analyze_file(self, max_lines: Optional[int] = None):
        """
        로그 파일 분석 (전체 파일 읽기)
        
        Args:
            max_lines: 최대 읽을 라인 수 (None이면 전체)
        """
        if not self.log_file.exists():
            logger.error(f"Log file not found: {self.log_file}")
            return
        
        logger.info(f"Analyzing log file: {self.log_file}")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if max_lines and i >= max_lines:
                        break
                    
                    failure_info = self.parse_log_line(line)
                    if failure_info:
                        self.process_failure(failure_info)
            
            logger.info("✅ Log file analysis completed")
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
    
    def tail_follow(self, check_interval: float = 1.0):
        """
        tail -f 스타일로 로그 파일 실시간 감시
        
        Args:
            check_interval: 체크 간격 (초)
        """
        if not self.log_file.exists():
            logger.error(f"Log file not found: {self.log_file}")
            return
        
        logger.info(f"Starting real-time monitoring: {self.log_file}")
        logger.info("Press Ctrl+C to stop")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # 파일 끝으로 이동
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    
                    if line:
                        failure_info = self.parse_log_line(line)
                        if failure_info:
                            self.process_failure(failure_info)
                    else:
                        # 새로운 데이터가 없으면 대기
                        time.sleep(check_interval)
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error during monitoring: {e}", exc_info=True)
    
    def print_stats(self):
        """통계 출력"""
        print("\n" + "=" * 60)
        print("📊 Log Analysis Statistics")
        print("=" * 60)
        print(f"Total lines processed: {self.stats['total_lines_processed']:,}")
        print(f"Failed logins detected: {self.stats['failed_logins_detected']}")
        print(f"Alerts generated: {self.stats['alerts_generated']}")
        print(f"Suspicious IPs: {len(self.stats['suspicious_ips'])}")
        
        if self.stats['suspicious_ips']:
            print("\n🚨 Suspicious IP addresses:")
            for ip in sorted(self.stats['suspicious_ips']):
                count = len(self.tracker.failed_attempts.get(ip, []))
                print(f"   - {ip}: {count} failed attempts")
        
        print("=" * 60)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='로그 분석 스크립트')
    parser.add_argument(
        '--log-file',
        default='/var/log/auth.log',
        help='로그 파일 경로 (기본: /var/log/auth.log)'
    )
    parser.add_argument(
        '--mode',
        choices=['analyze', 'monitor'],
        default='analyze',
        help='실행 모드: analyze (전체 분석) 또는 monitor (실시간 감시)'
    )
    parser.add_argument(
        '--max-lines',
        type=int,
        default=None,
        help='분석할 최대 라인 수 (analyze 모드에서만)'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("🔍 Log Analysis Script Started")
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        logger.info(f"Log file: {args.log_file}")
        logger.info(f"Mode: {args.mode}")
        logger.info("=" * 60)
        
        analyzer = LogAnalyzer(log_file=args.log_file)
        
        if args.mode == 'analyze':
            # 전체 파일 분석
            analyzer.analyze_file(max_lines=args.max_lines)
        else:
            # 실시간 감시
            analyzer.tail_follow()
        
        # 통계 출력
        analyzer.print_stats()
        
        logger.info("=" * 60)
        logger.info("✅ Log Analysis Completed")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error during log analysis: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
