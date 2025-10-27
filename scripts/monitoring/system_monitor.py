#!/usr/bin/env python3
"""
시스템 모니터링 스크립트 (System Monitor)
목적: CPU, 메모리, 디스크, 네트워크 사용률 체크 및 알림 생성
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
크로스 플랫폼 지원 (Windows/Linux)

수정 이력:
  - 2025-10-25: 초기 버전 생성
  - 2025-10-27: 최신 동기화 버전 (알림 시스템 통합, 다른 스크립트와 일관성)
"""
import sys
import platform
import socket
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import psutil
from config import settings
from core.logger import get_logger
from storage import db
from storage.models import SystemMetric, Notification

logger = get_logger()


class SystemMonitor:
    """
    시스템 모니터링 클래스
    - 시스템 리소스 사용률 체크
    - 임계치 초과 시 경고 및 알림 생성
    - 메트릭 데이터베이스 저장
    """
    
    def __init__(self):
        self.hostname = socket.gethostname()
        self.platform = platform.system().lower()
        
        # 임계치 설정
        self.thresholds = {
            'cpu': settings.cpu_threshold,
            'memory': settings.memory_threshold,
            'disk': settings.disk_threshold
        }
        
        logger.info(f"System Monitor initialized on {self.hostname} ({self.platform})")
    
    def collect_metrics(self) -> Dict:
        """
        시스템 메트릭 수집
        
        Returns:
            메트릭 딕셔너리
        """
        try:
            # CPU 메트릭
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 메모리 메트릭
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024 ** 3)
            memory_used_gb = memory.used / (1024 ** 3)
            memory_percent = memory.percent
            
            # 디스크 메트릭 (루트 파티션)
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024 ** 3)
            disk_used_gb = disk.used / (1024 ** 3)
            disk_percent = disk.percent
            
            # 네트워크 메트릭
            net_io = psutil.net_io_counters()
            network_sent_mb = net_io.bytes_sent / (1024 ** 2)
            network_recv_mb = net_io.bytes_recv / (1024 ** 2)
            
            metrics = {
                'cpu_percent': round(cpu_percent, 2),
                'cpu_count': cpu_count,
                'memory_total_gb': round(memory_total_gb, 2),
                'memory_used_gb': round(memory_used_gb, 2),
                'memory_percent': round(memory_percent, 2),
                'disk_total_gb': round(disk_total_gb, 2),
                'disk_used_gb': round(disk_used_gb, 2),
                'disk_percent': round(disk_percent, 2),
                'network_sent_mb': round(network_sent_mb, 2),
                'network_recv_mb': round(network_recv_mb, 2)
            }
            
            logger.debug(f"Metrics collected: CPU={cpu_percent}%, Memory={memory_percent}%, Disk={disk_percent}%")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}", exc_info=True)
            raise
    
    def check_thresholds(self, metrics: Dict) -> List[Dict]:
        """
        임계치 체크 및 이슈 목록 생성
        
        Args:
            metrics: 메트릭 딕셔너리
            
        Returns:
            이슈 목록 (각 이슈는 {'type', 'level', 'message'} 포함)
        """
        issues = []
        
        # CPU 체크
        if metrics['cpu_percent'] > self.thresholds['cpu']:
            level = 'CRITICAL' if metrics['cpu_percent'] > 95 else 'WARNING'
            issues.append({
                'type': 'cpu',
                'level': level,
                'message': f"CPU usage is {metrics['cpu_percent']}% (threshold: {self.thresholds['cpu']}%)",
                'value': metrics['cpu_percent']
            })
        
        # 메모리 체크
        if metrics['memory_percent'] > self.thresholds['memory']:
            level = 'CRITICAL' if metrics['memory_percent'] > 95 else 'WARNING'
            issues.append({
                'type': 'memory',
                'level': level,
                'message': f"Memory usage is {metrics['memory_percent']}% "
                          f"({metrics['memory_used_gb']:.2f}GB / {metrics['memory_total_gb']:.2f}GB, "
                          f"threshold: {self.thresholds['memory']}%)",
                'value': metrics['memory_percent']
            })
        
        # 디스크 체크
        if metrics['disk_percent'] > self.thresholds['disk']:
            level = 'CRITICAL' if metrics['disk_percent'] > 95 else 'WARNING'
            issues.append({
                'type': 'disk',
                'level': level,
                'message': f"Disk usage is {metrics['disk_percent']}% "
                          f"({metrics['disk_used_gb']:.2f}GB / {metrics['disk_total_gb']:.2f}GB, "
                          f"threshold: {self.thresholds['disk']}%)",
                'value': metrics['disk_percent']
            })
        
        return issues
    
    def save_metrics(self, metrics: Dict):
        """
        메트릭을 데이터베이스에 저장
        
        Args:
            metrics: 메트릭 딕셔너리
        """
        try:
            with db.session_scope() as session:
                metric = SystemMetric(
                    timestamp=datetime.now(timezone.utc),
                    hostname=self.hostname,
                    **metrics
                )
                session.add(metric)
            
            logger.debug("Metrics saved to database")
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def save_alerts(self, issues: List[Dict], metrics: Dict):
        """
        임계치 초과 알림을 데이터베이스에 저장
        
        Args:
            issues: 이슈 목록
            metrics: 메트릭 딕셔너리
        """
        if not issues:
            return
        
        try:
            with db.session_scope() as session:
                for issue in issues:
                    # 알림 제목 생성
                    titles = {
                        'cpu': f"High CPU Usage Alert: {issue['value']}%",
                        'memory': f"High Memory Usage Alert: {issue['value']}%",
                        'disk': f"High Disk Usage Alert: {issue['value']}%"
                    }
                    title = titles.get(issue['type'], "System Resource Alert")
                    
                    # 상세 메시지 생성
                    message = f"Host: {self.hostname}\n"
                    message += f"Platform: {self.platform}\n"
                    message += f"\n{issue['message']}\n"
                    message += f"\nCurrent System Status:\n"
                    message += f"  CPU: {metrics['cpu_percent']}% ({metrics['cpu_count']} cores)\n"
                    message += f"  Memory: {metrics['memory_percent']}% "
                    message += f"({metrics['memory_used_gb']:.2f}GB / {metrics['memory_total_gb']:.2f}GB)\n"
                    message += f"  Disk: {metrics['disk_percent']}% "
                    message += f"({metrics['disk_used_gb']:.2f}GB / {metrics['disk_total_gb']:.2f}GB)\n"
                    
                    # 알림 저장
                    notification = Notification(
                        title=title,
                        message=message,
                        level=issue['level'],
                        channel='system_monitoring',
                        sent_at=datetime.now(timezone.utc)
                    )
                    session.add(notification)
                    
                    logger.warning(f"Alert created: {title}")
            
            logger.info(f"✅ {len(issues)} alert(s) saved to database")
            
        except Exception as e:
            logger.error(f"Failed to save alerts: {e}")
    
    def print_report(self, metrics: Dict, issues: List[Dict]):
        """
        모니터링 리포트 출력
        
        Args:
            metrics: 메트릭 딕셔너리
            issues: 이슈 목록
        """
        print("\n" + "=" * 60)
        print("📊 SYSTEM MONITORING REPORT")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Hostname: {self.hostname}")
        print(f"Platform: {self.platform}")
        print()
        
        # 메트릭 출력
        print("📈 Current Metrics:")
        print(f"   CPU:     {metrics['cpu_percent']:>6.1f}% ({metrics['cpu_count']} cores)")
        print(f"   Memory:  {metrics['memory_percent']:>6.1f}% "
              f"({metrics['memory_used_gb']:.2f}GB / {metrics['memory_total_gb']:.2f}GB)")
        print(f"   Disk:    {metrics['disk_percent']:>6.1f}% "
              f"({metrics['disk_used_gb']:.2f}GB / {metrics['disk_total_gb']:.2f}GB)")
        print(f"   Network: ↑ {metrics['network_sent_mb']:.2f}MB / ↓ {metrics['network_recv_mb']:.2f}MB")
        print()
        
        # 임계치 출력
        print("⚙️  Thresholds:")
        print(f"   CPU:    {self.thresholds['cpu']}%")
        print(f"   Memory: {self.thresholds['memory']}%")
        print(f"   Disk:   {self.thresholds['disk']}%")
        print()
        
        # 이슈 출력
        if issues:
            print(f"🚨 Alerts: {len(issues)} issue(s) detected")
            for idx, issue in enumerate(issues, 1):
                icon = "⚠️ " if issue['level'] == 'WARNING' else "🔴"
                print(f"   {icon} [{issue['level']}] {issue['message']}")
        else:
            print("✅ All metrics within normal range")
        
        print("=" * 60)
    
    def run(self) -> int:
        """
        모니터링 실행
        
        Returns:
            종료 코드 (0: 정상, 1: 이슈 있음)
        """
        try:
            logger.info("=" * 60)
            logger.info("🖥️  System Monitoring Started")
            logger.info(f"Platform: {platform.system()} {platform.release()}")
            logger.info(f"Hostname: {self.hostname}")
            logger.info("=" * 60)
            
            # 1. 메트릭 수집
            logger.info("Collecting system metrics...")
            metrics = self.collect_metrics()
            
            # 2. 임계치 체크
            logger.info("Checking thresholds...")
            issues = self.check_thresholds(metrics)
            
            # 3. 데이터베이스 저장
            logger.info("Saving to database...")
            self.save_metrics(metrics)
            
            # 4. 알림 저장 (이슈가 있는 경우)
            if issues:
                self.save_alerts(issues, metrics)
            
            # 5. 리포트 출력
            self.print_report(metrics, issues)
            
            logger.info("=" * 60)
            logger.info("✅ System Monitoring Completed")
            logger.info("=" * 60)
            
            # 이슈가 있으면 종료 코드 1, 없으면 0
            return 1 if issues else 0
            
        except Exception as e:
            logger.error(f"❌ Error during monitoring: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")
            return 1


def main():
    """메인 실행 함수"""
    try:
        monitor = SystemMonitor()
        exit_code = monitor.run()
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Monitoring interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)