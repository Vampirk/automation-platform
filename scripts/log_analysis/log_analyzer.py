#!/usr/bin/env python3
"""
로그 분석기 (Log Analyzer)
목적: 실시간 로그 파일 감시 및 특정 패턴 탐지
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
수정 이력:
  - 2025-10-26: 초기 버전 생성
  - 2025-10-26: 개선 버전 (메모리 누수 방지, 압축 파일 지원, Graceful Shutdown)
  - 2025-10-26: Windows Event Log 지원 추가 (pywin32)
"""

import sys
import re
import time
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Iterator
from collections import Counter, defaultdict, deque

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

# 압축 파일 지원
try:
    from smart_open import open as smart_open
    HAS_SMART_OPEN = True
except ImportError:
    smart_open = None
    HAS_SMART_OPEN = False

# Windows Event Log 지원 (최고 성능)
try:
    import win32evtlog
    import win32evtlogutil
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from config import settings
from core.logger import get_logger
from storage import db
from storage.models import Notification

logger = get_logger()


class LogPatterns:
    """로그 패턴 정의"""
    
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
        'timeout': r'timed? out',
        'error': r'ERROR',
        'warning': r'WARNING',
        'critical': r'CRITICAL',
        # Windows 전용
        'windows_logon_failure': r'(An account failed to log on|Logon failure|audit failure)',
        'windows_service_error': r'(service .* (terminated|failed|crashed)|stopped unexpectedly)',
        'windows_system_error': r'(system error|fatal error|blue screen)',
    }
    
    SEVERITY_MAP = {
        'kernel_panic': 'CRITICAL',
        'out_of_memory': 'CRITICAL',
        'critical': 'CRITICAL',
        'windows_system_error': 'CRITICAL',
        'ssh_break_in': 'HIGH',
        'failed_login': 'HIGH',
        'service_failed': 'HIGH',
        'segfault': 'HIGH',
        'windows_logon_failure': 'HIGH',
        'windows_service_error': 'HIGH',
        'permission_denied': 'MEDIUM',
        'authentication_failure': 'MEDIUM',
        'disk_full': 'MEDIUM',
        'error': 'MEDIUM',
        'connection_refused': 'LOW',
        'timeout': 'LOW',
        'warning': 'LOW',
        'sudo_command': 'LOW',
        'user_added': 'LOW',
        'user_deleted': 'LOW',
    }


class WindowsEventLogReader:
    """
    Windows Event Log 리더 (pywin32 사용 - 최고 성능)
    """
    
    def __init__(self, log_type: str = 'System'):
        """
        초기화
        
        Args:
            log_type: 로그 타입 (System, Application, Security)
        """
        self.log_type = log_type
        self.handle = None
        
    def open(self) -> bool:
        """
        Event Log 열기
        
        Returns:
            성공 여부
        """
        if not HAS_WIN32:
            logger.error("pywin32 not installed. Install: pip install pywin32")
            return False
        
        try:
            self.handle = win32evtlog.OpenEventLog(None, self.log_type)
            return True
        except Exception as e:
            logger.error(f"Failed to open Windows Event Log ({self.log_type}): {e}")
            return False
    
    def read_events(self, max_events: int = 1000) -> Iterator[str]:
        """
        이벤트 읽기
        
        Args:
            max_events: 읽을 최대 이벤트 수
            
        Yields:
            이벤트 문자열
        """
        if not self.handle:
            if not self.open():
                return
        
        try:
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(self.handle, flags, 0)
            
            count = 0
            while events and count < max_events:
                for event in events:
                    if count >= max_events:
                        break
                    
                    # 이벤트 타입 매핑
                    event_type_map = {
                        win32con.EVENTLOG_ERROR_TYPE: 'ERROR',
                        win32con.EVENTLOG_WARNING_TYPE: 'WARNING',
                        win32con.EVENTLOG_INFORMATION_TYPE: 'INFO',
                        win32con.EVENTLOG_AUDIT_SUCCESS: 'AUDIT_SUCCESS',
                        win32con.EVENTLOG_AUDIT_FAILURE: 'AUDIT_FAILURE',
                    }
                    
                    event_type = event_type_map.get(event.EventType, 'UNKNOWN')
                    
                    # 이벤트 메시지 추출
                    try:
                        message = win32evtlogutil.SafeFormatMessage(event, self.log_type)
                    except:
                        message = str(event.StringInserts) if event.StringInserts else ''
                    
                    # 로그 라인 형식으로 변환
                    timestamp = event.TimeGenerated.Format()
                    source = event.SourceName
                    event_id = event.EventID & 0xFFFF  # 하위 16비트만
                    
                    log_line = f"{timestamp} {event_type} {source} EventID:{event_id} {message}"
                    
                    yield log_line
                    count += 1
                
                # 다음 배치 읽기
                events = win32evtlog.ReadEventLog(self.handle, flags, 0)
        
        except Exception as e:
            logger.error(f"Error reading Windows Event Log: {e}")
    
    def close(self):
        """Event Log 닫기"""
        if self.handle:
            win32evtlog.CloseEventLog(self.handle)
            self.handle = None


class LogAnalyzer:
    """
    로그 파일 분석기
    
    개선 사항:
    - 메모리 누수 방지 (deque로 크기 제한)
    - 압축 파일 지원 (.gz, .bz2, .xz)
    - 권한 체크 강화
    - IP 추적 메모리 제한
    - Windows Event Log 지원 (pywin32)
    """
    
    MAX_MATCHES_PER_PATTERN = 1000
    MAX_IP_TRACKING = 500
    
    def __init__(self):
        """초기화"""
        self.patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in LogPatterns.PATTERNS.items()
        }
        
        self.matches = defaultdict(lambda: deque(maxlen=self.MAX_MATCHES_PER_PATTERN))
        
        self.total_lines = 0
        self.total_matches = 0
        
        self.pattern_counts = Counter()
        self.severity_counts = Counter()
        
        self.failed_ips = Counter()
    
    def check_file_permission(self, filepath: str) -> bool:
        """파일 읽기 권한 체크"""
        try:
            path = Path(filepath)
            if not path.exists():
                logger.warning(f"File does not exist: {filepath}")
                return False
            
            with open(filepath, 'r') as f:
                f.read(1)
            return True
            
        except PermissionError:
            logger.error(f"Permission denied: {filepath}")
            logger.info("💡 Run with: sudo python script.py")
            return False
        except Exception as e:
            logger.error(f"Cannot read file {filepath}: {e}")
            return False
    
    def open_file(self, filepath: str) -> Optional[Iterator[str]]:
        """압축 파일 자동 감지 및 열기"""
        path = Path(filepath)
        
        try:
            if HAS_SMART_OPEN:
                return smart_open(filepath, 'r', encoding='utf-8', errors='ignore')
            
            elif path.suffix == '.gz':
                import gzip
                return gzip.open(filepath, 'rt', encoding='utf-8', errors='ignore')
            
            elif path.suffix == '.bz2':
                import bz2
                return bz2.open(filepath, 'rt', encoding='utf-8', errors='ignore')
            
            elif path.suffix == '.xz':
                import lzma
                return lzma.open(filepath, 'rt', encoding='utf-8', errors='ignore')
            
            else:
                return open(filepath, 'r', encoding='utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Failed to open {filepath}: {e}")
            return None
    
    def analyze_line(self, line: str) -> List[Dict]:
        """한 줄 분석 및 패턴 매칭"""
        results = []
        
        for pattern_name, pattern in self.patterns.items():
            match = pattern.search(line)
            if match:
                severity = LogPatterns.SEVERITY_MAP.get(pattern_name, 'LOW')
                
                result = {
                    'pattern': pattern_name,
                    'severity': severity,
                    'line': line.strip(),
                    'timestamp': datetime.now(timezone.utc),
                    'matched_text': match.group(0)
                }
                
                if pattern_name == 'failed_login':
                    ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        ip = ip_match.group(1)
                        self.failed_ips[ip] += 1
                        result['ip'] = ip
                        
                        if len(self.failed_ips) > self.MAX_IP_TRACKING:
                            min_ip = self.failed_ips.most_common()[-1][0]
                            del self.failed_ips[min_ip]
                
                self.matches[pattern_name].append(result)
                
                self.pattern_counts[pattern_name] += 1
                self.severity_counts[severity] += 1
                self.total_matches += 1
                
                results.append(result)
                
                if severity in ['CRITICAL', 'HIGH']:
                    self.save_to_database(result)
        
        return results
    
    def analyze_file(self, filepath: str) -> Dict:
        """파일 분석 (압축 파일 지원)"""
        if not self.check_file_permission(filepath):
            return self.get_statistics()
        
        logger.info(f"Analyzing file: {filepath}")
        
        file_handle = self.open_file(filepath)
        if file_handle is None:
            return self.get_statistics()
        
        try:
            with file_handle as f:
                for line in f:
                    self.total_lines += 1
                    self.analyze_line(line)
                    
                    if self.total_lines % 1000000 == 0:
                        logger.info(f"Processed {self.total_lines:,} lines...")
        
        except Exception as e:
            logger.error(f"Error analyzing file: {e}", exc_info=True)
        
        logger.info(f"Completed: {self.total_lines:,} lines, {self.total_matches:,} matches")
        return self.get_statistics()
    
    def analyze_windows_eventlog(self, log_type: str = 'System', max_events: int = 1000) -> Dict:
        """
        Windows Event Log 분석
        
        Args:
            log_type: 로그 타입 (System, Application, Security)
            max_events: 읽을 최대 이벤트 수
            
        Returns:
            분석 통계
        """
        if not settings.is_windows():
            logger.warning("Windows Event Log is only available on Windows")
            return self.get_statistics()
        
        if not HAS_WIN32:
            logger.error("pywin32 not installed. Install: pip install pywin32")
            return self.get_statistics()
        
        logger.info(f"Analyzing Windows Event Log: {log_type}")
        
        reader = WindowsEventLogReader(log_type)
        
        try:
            for line in reader.read_events(max_events):
                self.total_lines += 1
                self.analyze_line(line)
                
                if self.total_lines % 10000 == 0:
                    logger.info(f"Processed {self.total_lines:,} events...")
        
        except Exception as e:
            logger.error(f"Error analyzing Windows Event Log: {e}", exc_info=True)
        
        finally:
            reader.close()
        
        logger.info(f"Completed: {self.total_lines:,} events, {self.total_matches:,} matches")
        return self.get_statistics()
    
    def save_to_database(self, result: Dict):
        """알림을 데이터베이스에 저장"""
        try:
            with db.session_scope() as session:
                notification = Notification(
                    title=f"Log Alert: {result['pattern']}",
                    message=result['line'][:500],
                    level=result['severity'],
                    channel='log_analysis',
                    sent_at=result['timestamp']
                )
                session.add(notification)
        except Exception as e:
            logger.error(f"Failed to save notification: {e}")
    
    def get_statistics(self) -> Dict:
        """통계 반환"""
        stats = {
            'total_lines': self.total_lines,
            'total_matches': self.total_matches,
            'severity_summary': self.severity_counts,
            'patterns': {},
            'failed_ips': dict(self.failed_ips.most_common(10)),
            'memory_usage': {
                'matches_stored': sum(len(m) for m in self.matches.values()),
                'ips_tracked': len(self.failed_ips)
            }
        }
        
        for pattern_name, count in self.pattern_counts.items():
            stats['patterns'][pattern_name] = {
                'count': count,
                'severity': LogPatterns.SEVERITY_MAP.get(pattern_name, 'LOW'),
                'recent_matches': len(self.matches[pattern_name])
            }
        
        sorted_patterns = sorted(
            stats['patterns'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        stats['top_issues'] = sorted_patterns[:10]
        
        return stats
    
    def get_recent_matches(self, limit: int = 10) -> List[Dict]:
        """최근 매치된 항목들"""
        all_matches = []
        for pattern_name, matches in self.matches.items():
            all_matches.extend(matches)
        
        all_matches.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_matches[:limit]


class LogFileHandler(FileSystemEventHandler):
    """로그 파일 감시 핸들러"""
    
    def __init__(self, analyzer: LogAnalyzer, target_files: List[str]):
        """초기화"""
        super().__init__()
        self.analyzer = analyzer
        self.target_files = set(target_files)
        self.file_positions = {}
        
        self.compressed_extensions = {'.gz', '.bz2', '.xz'}
    
    def _is_target_file(self, filename: str) -> bool:
        """감시 대상 파일인지 확인"""
        path = Path(filename)
        
        if path.name in self.target_files:
            return True
        
        stem = path.stem
        if path.suffix in self.compressed_extensions:
            base_name = Path(stem).stem
            if base_name in self.target_files:
                return True
        
        return False
    
    def on_modified(self, event):
        """파일 수정 이벤트 처리"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        if not self._is_target_file(Path(file_path).name):
            return
        
        logger.info(f"Log file modified: {file_path}")
        
        try:
            if Path(file_path).suffix in self.compressed_extensions:
                self.analyzer.analyze_file(file_path)
            else:
                self._analyze_incremental(file_path)
        
        except Exception as e:
            logger.error(f"Error handling file modification: {e}")
    
    def _analyze_incremental(self, file_path: str):
        """증분 분석"""
        file_handle = self.analyzer.open_file(file_path)
        if file_handle is None:
            return
        
        try:
            with file_handle as f:
                last_pos = self.file_positions.get(file_path, 0)
                f.seek(last_pos)
                
                new_lines = f.readlines()
                
                for line in new_lines:
                    self.analyzer.analyze_line(line)
                
                self.file_positions[file_path] = f.tell()
                
                if new_lines:
                    logger.debug(f"Analyzed {len(new_lines)} new lines from {file_path}")
        
        except Exception as e:
            logger.error(f"Incremental analysis failed: {e}")


shutdown_requested = False

def signal_handler(signum, frame):
    """시그널 핸들러"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


def watch_logs(directories: List[str], target_files: List[str], 
               duration: int = None, max_runtime: int = 3600):
    """개선된 로그 파일 실시간 감시"""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    analyzer = LogAnalyzer()
    event_handler = LogFileHandler(analyzer, target_files)
    observer = Observer()
    
    for directory in directories:
        if Path(directory).exists():
            observer.schedule(event_handler, directory, recursive=False)
            logger.info(f"Watching directory: {directory}")
        else:
            logger.warning(f"Directory not found: {directory}")
    
    observer.start()
    logger.info("Log monitoring started (Press Ctrl+C to stop)")
    logger.info(f"Max runtime: {max_runtime}s, Duration: {duration or 'unlimited'}")
    
    start_time = time.time()
    
    try:
        while not shutdown_requested:
            time.sleep(1)
            
            elapsed = time.time() - start_time
            
            if duration and elapsed >= duration:
                logger.info(f"Duration {duration}s reached, stopping...")
                break
            
            if elapsed >= max_runtime:
                logger.warning(f"Max runtime {max_runtime}s reached, stopping...")
                break
            
            if int(elapsed) % 300 == 0 and elapsed > 0:
                stats = analyzer.get_statistics()
                logger.info(f"Stats: {stats['total_matches']} matches, "
                           f"Memory: {stats['memory_usage']}")
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received...")
    
    finally:
        observer.stop()
        observer.join()
        
        stats = analyzer.get_statistics()
        print_statistics(stats)
        
        return stats


def print_statistics(stats: Dict):
    """통계 출력"""
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
    
    if stats.get('failed_ips'):
        print("\n🌐 Top Failed Login IPs:")
        for ip, count in list(stats['failed_ips'].items())[:5]:
            print(f"   {ip}: {count} attempts")
    
    if 'memory_usage' in stats:
        print("\n💾 Memory Usage:")
        print(f"   Matches stored: {stats['memory_usage']['matches_stored']:,}")
        print(f"   IPs tracked: {stats['memory_usage']['ips_tracked']}")
    
    print("=" * 60)


def main():
    """메인 실행 함수"""
    try:
        logger.info("=" * 60)
        logger.info("📋 Log Analyzer Started")
        logger.info("=" * 60)
        
        if settings.is_linux():
            # Linux: 파일 기반 로그 감시
            log_directories = ['/var/log']
            
            target_files = [
                'syslog',
                'auth.log',
                'kern.log',
                'messages',
            ]
            
            watch_logs(
                log_directories, 
                target_files, 
                duration=60,
                max_runtime=3600
            )
        
        elif settings.is_windows():
            # Windows: Event Log 분석
            logger.info("Windows platform detected - analyzing Event Logs")
            
            if not HAS_WIN32:
                logger.error("pywin32 not installed")
                logger.info("Install: pip install pywin32")
                return 1
            
            analyzer = LogAnalyzer()
            
            # System, Application, Security 순서로 분석
            for log_type in ['System', 'Application', 'Security']:
                logger.info(f"Analyzing {log_type} log...")
                analyzer.analyze_windows_eventlog(log_type, max_events=1000)
            
            # 통계 출력
            stats = analyzer.get_statistics()
            print_statistics(stats)
        
        else:
            logger.error("Unsupported platform")
            return 1
        
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