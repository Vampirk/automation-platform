#!/usr/bin/env python3
"""
패턴 탐지기 (Pattern Detector)
목적: 시간대별 로그 패턴 분석 및 이상 탐지
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
수정 이력:
  - 2025-10-26: 초기 버전 생성
"""

import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import json

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.logger import get_logger
from storage import db
from storage.models import Notification

logger = get_logger()


class PatternDetector:
    """
    로그 패턴 탐지기
    
    시간대별 패턴 분석 및 이상 행동 탐지
    """
    
    # 시간 형식 패턴들 (다양한 로그 형식 지원)
    TIMESTAMP_PATTERNS = [
        # Oct 26 12:34:56
        r'([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})',
        # 2025-10-26 12:34:56
        r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})',
        # 2025-10-26T12:34:56
        r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})',
    ]
    
    # 이상 탐지 임계치
    ANOMALY_THRESHOLDS = {
        'failed_login_count': 5,      # 5분 내 5회 이상
        'error_rate': 0.1,             # 전체 로그의 10% 이상이 에러
        'repeated_error': 10,          # 동일 에러 10회 이상 반복
        'suspicious_time': (0, 6),     # 새벽 0시~6시 활동
    }
    
    def __init__(self):
        """초기화"""
        self.hourly_patterns = defaultdict(lambda: defaultdict(int))
        self.event_timeline = []
        self.ip_addresses = Counter()
        self.error_messages = Counter()
        self.users = Counter()
        
    def extract_timestamp(self, line: str) -> Optional[datetime]:
        """
        로그 라인에서 타임스탬프 추출
        
        Args:
            line: 로그 라인
            
        Returns:
            datetime 객체 또는 None
        """
        for pattern in self.TIMESTAMP_PATTERNS:
            match = re.search(pattern, line)
            if match:
                try:
                    # Oct 26 12:34:56 형식
                    if len(match.groups()) == 5:
                        month_str, day, hour, minute, second = match.groups()
                        month_map = {
                            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                        }
                        return datetime(
                            year=datetime.now().year,
                            month=month_map[month_str],
                            day=int(day),
                            hour=int(hour),
                            minute=int(minute),
                            second=int(second)
                        )
                    
                    # 2025-10-26 12:34:56 형식
                    elif len(match.groups()) == 6:
                        year, month, day, hour, minute, second = match.groups()
                        return datetime(
                            year=int(year),
                            month=int(month),
                            day=int(day),
                            hour=int(hour),
                            minute=int(minute),
                            second=int(second)
                        )
                
                except (ValueError, KeyError):
                    continue
        
        return None
    
    def extract_ip_address(self, line: str) -> Optional[str]:
        """
        로그 라인에서 IP 주소 추출
        
        Args:
            line: 로그 라인
            
        Returns:
            IP 주소 문자열 또는 None
        """
        # IPv4 패턴
        ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        match = re.search(ipv4_pattern, line)
        if match:
            return match.group()
        
        return None
    
    def extract_username(self, line: str) -> Optional[str]:
        """
        로그 라인에서 사용자명 추출
        
        Args:
            line: 로그 라인
            
        Returns:
            사용자명 또는 None
        """
        # "user username", "for username" 패턴
        patterns = [
            r'user\s+(\w+)',
            r'for\s+(\w+)',
            r'USER=(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def analyze_line(self, line: str):
        """
        로그 라인 분석 및 정보 추출
        
        Args:
            line: 로그 라인
        """
        # 타임스탬프 추출
        timestamp = self.extract_timestamp(line)
        if timestamp:
            hour = timestamp.hour
            
            # 패턴 분류
            if 'failed' in line.lower() or 'failure' in line.lower():
                self.hourly_patterns[hour]['failed'] += 1
            if 'error' in line.lower():
                self.hourly_patterns[hour]['error'] += 1
                self.error_messages[line.strip()[:100]] += 1
            if 'warning' in line.lower():
                self.hourly_patterns[hour]['warning'] += 1
            if 'denied' in line.lower():
                self.hourly_patterns[hour]['denied'] += 1
            
            # 이벤트 타임라인에 추가
            self.event_timeline.append({
                'timestamp': timestamp,
                'content': line.strip()[:200]
            })
        
        # IP 주소 추출
        ip_address = self.extract_ip_address(line)
        if ip_address and 'failed' in line.lower():
            self.ip_addresses[ip_address] += 1
        
        # 사용자명 추출
        username = self.extract_username(line)
        if username:
            self.users[username] += 1
    
    def analyze_file(self, file_path: str):
        """
        로그 파일 전체 분석
        
        Args:
            file_path: 로그 파일 경로
        """
        logger.info(f"Analyzing patterns in: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    self.analyze_line(line)
        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
    
    def detect_anomalies(self) -> List[Dict]:
        """
        이상 패턴 탐지
        
        Returns:
            이상 패턴 리스트
        """
        anomalies = []
        
        # 1. 반복적인 실패 로그인 탐지
        for ip, count in self.ip_addresses.items():
            if count >= self.ANOMALY_THRESHOLDS['failed_login_count']:
                anomalies.append({
                    'type': 'repeated_failed_login',
                    'severity': 'HIGH',
                    'description': f'IP {ip}에서 {count}회 로그인 실패',
                    'details': {'ip': ip, 'count': count}
                })
        
        # 2. 시간대별 이상 활동 탐지 (새벽 시간)
        suspicious_start, suspicious_end = self.ANOMALY_THRESHOLDS['suspicious_time']
        for hour in range(suspicious_start, suspicious_end):
            total_events = sum(self.hourly_patterns[hour].values())
            if total_events > 50:  # 새벽에 50개 이상 이벤트
                anomalies.append({
                    'type': 'suspicious_time_activity',
                    'severity': 'MEDIUM',
                    'description': f'새벽 {hour}시에 {total_events}개 이벤트 발생',
                    'details': {'hour': hour, 'count': total_events}
                })
        
        # 3. 반복되는 에러 메시지 탐지
        for error_msg, count in self.error_messages.most_common(5):
            if count >= self.ANOMALY_THRESHOLDS['repeated_error']:
                anomalies.append({
                    'type': 'repeated_error',
                    'severity': 'MEDIUM',
                    'description': f'동일 에러 {count}회 반복',
                    'details': {'message': error_msg, 'count': count}
                })
        
        # 4. 특정 사용자의 과다 활동 탐지
        for username, count in self.users.most_common(3):
            if count > 100:  # 100회 이상 언급
                anomalies.append({
                    'type': 'excessive_user_activity',
                    'severity': 'LOW',
                    'description': f'사용자 {username}이(가) {count}회 언급됨',
                    'details': {'username': username, 'count': count}
                })
        
        return anomalies
    
    def get_hourly_summary(self) -> Dict:
        """
        시간대별 요약 통계
        
        Returns:
            시간대별 통계 딕셔너리
        """
        summary = {}
        
        for hour in range(24):
            patterns = self.hourly_patterns[hour]
            total = sum(patterns.values())
            
            if total > 0:
                summary[hour] = {
                    'total_events': total,
                    'failed': patterns.get('failed', 0),
                    'error': patterns.get('error', 0),
                    'warning': patterns.get('warning', 0),
                    'denied': patterns.get('denied', 0),
                }
        
        return summary
    
    def get_top_ips(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        실패한 로그인 시도가 많은 상위 IP
        
        Args:
            limit: 반환할 최대 개수
            
        Returns:
            (IP, 횟수) 튜플 리스트
        """
        return self.ip_addresses.most_common(limit)
    
    def get_top_errors(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        가장 많이 발생한 에러 메시지
        
        Args:
            limit: 반환할 최대 개수
            
        Returns:
            (에러 메시지, 횟수) 튜플 리스트
        """
        return self.error_messages.most_common(limit)
    
    def save_anomalies_to_db(self, anomalies: List[Dict]):
        """
        이상 패턴을 데이터베이스에 저장
        
        Args:
            anomalies: 이상 패턴 리스트
        """
        try:
            with db.session_scope() as session:
                for anomaly in anomalies:
                    notification = Notification(
                        title=f"Pattern Anomaly: {anomaly['type']}",
                        message=anomaly['description'],
                        level=anomaly['severity'],
                        channel='pattern_detection',
                        success=True
                    )
                    session.add(notification)
            
            logger.info(f"Saved {len(anomalies)} anomalies to database")
        
        except Exception as e:
            logger.error(f"Failed to save anomalies: {e}")


def print_analysis_report(detector: PatternDetector):
    """
    분석 리포트 출력
    
    Args:
        detector: PatternDetector 인스턴스
    """
    print("\n" + "=" * 70)
    print("🔍 Pattern Analysis Report")
    print("=" * 70)
    
    # 시간대별 요약
    print("\n⏰ Hourly Summary:")
    hourly = detector.get_hourly_summary()
    if hourly:
        for hour, stats in sorted(hourly.items()):
            print(f"   {hour:02d}:00 - Total: {stats['total_events']:>4}, "
                  f"Failed: {stats['failed']:>3}, Error: {stats['error']:>3}, "
                  f"Warning: {stats['warning']:>3}")
    else:
        print("   No data available")
    
    # 상위 IP 주소
    print("\n🌐 Top Failed Login IPs:")
    top_ips = detector.get_top_ips(5)
    if top_ips:
        for i, (ip, count) in enumerate(top_ips, 1):
            print(f"   {i}. {ip}: {count} attempts")
    else:
        print("   No failed login attempts detected")
    
    # 상위 에러 메시지
    print("\n❌ Top Error Messages:")
    top_errors = detector.get_top_errors(5)
    if top_errors:
        for i, (error, count) in enumerate(top_errors, 1):
            print(f"   {i}. [{count}x] {error[:70]}")
    else:
        print("   No errors detected")
    
    # 이상 패턴
    print("\n🚨 Detected Anomalies:")
    anomalies = detector.detect_anomalies()
    if anomalies:
        for i, anomaly in enumerate(anomalies, 1):
            print(f"   {i}. [{anomaly['severity']}] {anomaly['description']}")
    else:
        print("   ✅ No anomalies detected")
    
    print("=" * 70)


def main():
    """메인 실행 함수"""
    try:
        logger.info("=" * 60)
        logger.info("🔍 Pattern Detector Started")
        logger.info("=" * 60)
        
        # 분석할 로그 파일들
        log_files = [
            '/var/log/auth.log',
            '/var/log/syslog',
        ]
        
        # Linux 시스템인지 확인
        if not settings.is_linux():
            logger.warning("This script is designed for Linux systems")
            return 1
        
        # 패턴 탐지기 초기화
        detector = PatternDetector()
        
        # 각 로그 파일 분석
        for log_file in log_files:
            if Path(log_file).exists():
                detector.analyze_file(log_file)
            else:
                logger.warning(f"Log file not found: {log_file}")
        
        # 이상 패턴 탐지
        anomalies = detector.detect_anomalies()
        
        # 데이터베이스에 저장
        if anomalies:
            detector.save_anomalies_to_db(anomalies)
        
        # 리포트 출력
        print_analysis_report(detector)
        
        logger.info("=" * 60)
        logger.info("✅ Pattern Detection Completed")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error during pattern detection: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)