#!/usr/bin/env python3
"""
로그 분석기 (Log Analyzer)
목적: 실시간 로그 파일 감시 및 특정 패턴 탐지
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
수정 이력:
  - 2025-10-26: 초기 버전 생성
"""

import sys
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter, defaultdict
import json

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("⚠️  watchdog 라이브러리가 필요합니다")
    print("설치: pip install watchdog")
    sys.exit(1)

from config import settings
from core.logger import get_logger
from storage import db
from storage.models import Notification

logger = get_logger()


class LogPatterns:
    """로그 패턴 정의"""
    
    # 탐지할 패턴들 (정규표현식)
    PATTERNS = {
        'failed_login': r'Failed password for .* from .* port',
        'ssh_break_in': r'POSSIBLE BREAK-IN ATTEMPT',
        'permission_denied': r'Permission denied',
        'out_of_memory': r'Out of memory',
        'disk_full': r'No space left on device',
        'service_failed': r'(systemd|service).*failed',
        'kernel_panic': r'Kernel panic',
        'segfault': r'segmentation fault',
        'authentication_failure': r'authentication failure',
        'sudo_command': r'sudo:.*COMMAND=',
        'user_added': r'new user:',
        'user_deleted': r'delete user',
        'connection_refused': r'Connection refused',
        'timeout': r'timed? ?out',
        'error': r'ERROR|Error|error',
        'warning': r'WARNING|Warning|warning',
        'critical': r'CRITICAL|Critical|critical',
    }
    
    # 위험도 분류
    SEVERITY_MAP = {
        'failed_login': 'HIGH',
        'ssh_break_in': 'CRITICAL',
        'permission_denied': 'MEDIUM',
        'out_of_memory': 'CRITICAL',
        'disk_full': 'CRITICAL',
        'service_failed': 'HIGH',
        'kernel_panic': 'CRITICAL',
        'segfault': 'HIGH',
        'authentication_failure': 'HIGH',
        'sudo_command': 'LOW',
        'user_added': 'MEDIUM',
        'user_deleted': 'MEDIUM',
        'connection_refused': 'MEDIUM',
        'timeout': 'MEDIUM',
        'error': 'MEDIUM',
        'warning': 'LOW',
        'critical': 'HIGH',
    }


class LogAnalyzer:
    """
    로그 파일 분석기
    
    로그 파일을 읽고 패턴을 탐지하여 통계 생성
    """
    
    def __init__(self):
        """초기화"""
        self.patterns = {
            name: re.compile(pattern, re.IGNORECASE) 
            for name, pattern in LogPatterns.PATTERNS.items()
        }
        self.matches = defaultdict(list)
        self.line_count = 0
        
    def analyze_line(self, line: str, line_number: int, file_path: str) -> Optional[Dict]:
        """
        한 줄의 로그를 분석
        
        Args:
            line: 로그 라인
            line_number: 라인 번호
            file_path: 파일 경로
            
        Returns:
            매치된 패턴 정보 (없으면 None)
        """
        self.line_count += 1
        
        for pattern_name, pattern_regex in self.patterns.items():
            if pattern_regex.search(line):
                match_info = {
                    'pattern': pattern_name,
                    'severity': LogPatterns.SEVERITY_MAP.get(pattern_name, 'LOW'),
                    'line_number': line_number,
                    'file_path': file_path,
                    'content': line.strip(),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.matches[pattern_name].append(match_info)
                return match_info
        
        return None
    
    def analyze_file(self, file_path: str) -> Dict:
        """
        로그 파일 전체 분석
        
        Args:
            file_path: 로그 파일 경로
            
        Returns:
            분석 결과
        """
        logger.info(f"Analyzing log file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_number, line in enumerate(f, 1):
                    match = self.analyze_line(line, line_number, file_path)
                    if match:
                        logger.debug(
                            f"Pattern detected: {match['pattern']} "
                            f"at line {line_number}"
                        )
        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
        
        return self.get_statistics()
    
    def get_statistics(self) -> Dict:
        """
        분석 통계 생성
        
        Returns:
            통계 딕셔너리
        """
        stats = {
            'total_lines': self.line_count,
            'total_matches': sum(len(matches) for matches in self.matches.values()),
            'patterns': {},
            'severity_summary': Counter(),
            'top_issues': []
        }
        
        # 패턴별 통계
        for pattern_name, matches in self.matches.items():
            if matches:
                severity = LogPatterns.SEVERITY_MAP.get(pattern_name, 'LOW')
                stats['patterns'][pattern_name] = {
                    'count': len(matches),
                    'severity': severity
                }
                stats['severity_summary'][severity] += len(matches)
        
        # 상위 이슈 (발생 횟수 기준)
        sorted_patterns = sorted(
            stats['patterns'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        stats['top_issues'] = sorted_patterns[:10]
        
        return stats
    
    def get_recent_matches(self, limit: int = 10) -> List[Dict]:
        """
        최근 매치된 항목들
        
        Args:
            limit: 반환할 최대 개수
            
        Returns:
            최근 매치 리스트
        """
        all_matches = []
        for pattern_name, matches in self.matches.items():
            all_matches.extend(matches)
        
        # 타임스탬프 기준 정렬
        all_matches.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_matches[:limit]


class LogFileHandler(FileSystemEventHandler):
    """
    로그 파일 감시 핸들러
    
    watchdog를 사용하여 실시간으로 로그 파일 변경 감지
    """
    
    def __init__(self, analyzer: LogAnalyzer, target_files: List[str]):
        """
        초기화
        
        Args:
            analyzer: LogAnalyzer 인스턴스
            target_files: 감시할 파일 이름 리스트
        """
        super().__init__()
        self.analyzer = analyzer
        self.target_files = set(target_files)
        self.file_positions = {}
        
    def on_modified(self, event):
        """
        파일 수정 이벤트 처리
        
        Args:
            event: 파일 시스템 이벤트
        """
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = Path(file_path).name
        
        # 감시 대상 파일인지 확인
        if file_name not in self.target_files:
            return
        
        logger.info(f"Log file modified: {file_path}")
        
        try:
            # 마지막 읽은 위치부터 읽기
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 이전 위치로 이동
                last_pos = self.file_positions.get(file_path, 0)
                f.seek(last_pos)
                
                # 새로운 라인들 읽기
                new_lines = f.readlines()
                
                # 현재 위치 저장
                self.file_positions[file_path] = f.tell()
                
                # 새 라인 분석
                for line in new_lines:
                    match = self.analyzer.analyze_line(
                        line, 
                        0,  # 실시간 감시에서는 라인 번호 추적 안함
                        file_path
                    )
                    if match:
                        self._handle_match(match)
        
        except Exception as e:
            logger.error(f"Error reading modified file {file_path}: {e}")
    
    def _handle_match(self, match: Dict):
        """
        매치된 패턴 처리
        
        Args:
            match: 매치 정보
        """
        severity = match['severity']
        pattern = match['pattern']
        content = match['content']
        
        # 심각도에 따라 로깅
        if severity == 'CRITICAL':
            logger.critical(f"🚨 CRITICAL: {pattern} - {content[:100]}")
            self._send_notification(match)
        elif severity == 'HIGH':
            logger.error(f"⚠️  HIGH: {pattern} - {content[:100]}")
            self._send_notification(match)
        elif severity == 'MEDIUM':
            logger.warning(f"⚡ MEDIUM: {pattern} - {content[:100]}")
        else:
            logger.info(f"ℹ️  LOW: {pattern} - {content[:100]}")
    
    def _send_notification(self, match: Dict):
        """
        알림 전송 (데이터베이스에 저장)
        
        Args:
            match: 매치 정보
        """
        try:
            with db.session_scope() as session:
                notification = Notification(
                    title=f"Log Alert: {match['pattern']}",
                    message=match['content'][:500],
                    level=match['severity'],
                    channel='log_analysis',
                    success=True
                )
                session.add(notification)
            
            logger.info(f"Notification saved: {match['pattern']}")
        
        except Exception as e:
            logger.error(f"Failed to save notification: {e}")


def watch_logs(directories: List[str], target_files: List[str], duration: int = None):
    """
    로그 파일 실시간 감시
    
    Args:
        directories: 감시할 디렉토리 리스트
        target_files: 감시할 파일 이름 리스트
        duration: 감시 시간 (초, None이면 무한)
    """
    analyzer = LogAnalyzer()
    event_handler = LogFileHandler(analyzer, target_files)
    observer = Observer()
    
    # 각 디렉토리에 옵저버 등록
    for directory in directories:
        if Path(directory).exists():
            observer.schedule(event_handler, directory, recursive=False)
            logger.info(f"Watching directory: {directory}")
        else:
            logger.warning(f"Directory not found: {directory}")
    
    # 감시 시작
    observer.start()
    logger.info("Log monitoring started (Press Ctrl+C to stop)")
    
    try:
        if duration:
            time.sleep(duration)
            logger.info(f"Monitoring completed after {duration}s")
        else:
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Stopping log monitoring...")
    
    finally:
        observer.stop()
        observer.join()
        
        # 통계 출력
        stats = analyzer.get_statistics()
        print_statistics(stats)


def print_statistics(stats: Dict):
    """
    통계 출력
    
    Args:
        stats: 통계 딕셔너리
    """
    print("\n" + "=" * 60)
    print("📊 Log Analysis Statistics")
    print("=" * 60)
    print(f"Total Lines: {stats['total_lines']:,}")
    print(f"Total Matches: {stats['total_matches']:,}")
    
    if stats['severity_summary']:
        print("\n🚨 Severity Summary:")
        for severity, count in stats['severity_summary'].most_common():
            print(f"   {severity}: {count}")
    
    if stats['top_issues']:
        print("\n🔝 Top Issues:")
        for i, (pattern, info) in enumerate(stats['top_issues'][:5], 1):
            print(f"   {i}. {pattern}: {info['count']} ({info['severity']})")
    
    print("=" * 60)


def main():
    """메인 실행 함수"""
    try:
        logger.info("=" * 60)
        logger.info("📋 Log Analyzer Started")
        logger.info("=" * 60)
        
        # 감시할 로그 디렉토리들
        log_directories = [
            '/var/log',
        ]
        
        # 감시할 파일들
        target_files = [
            'syslog',
            'auth.log',
            'kern.log',
            'messages',
        ]
        
        # Linux 시스템인지 확인
        if not settings.is_linux():
            logger.warning("This script is designed for Linux systems")
            logger.info("On Windows, check Event Viewer logs instead")
            return 1
        
        # 로그 감시 시작 (테스트: 60초)
        watch_logs(log_directories, target_files, duration=60)
        
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