#!/usr/bin/env python3
"""
시스템 모니터링 스크립트
CPU, 메모리, 디스크 사용률 체크
크로스 플랫폼 지원 (Windows/Linux)
"""
import sys
import platform
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import psutil
from config import settings
from core.logger import get_logger
from storage import db, SystemMetric

logger = get_logger()


def get_system_metrics():
    """
    시스템 메트릭 수집
    
    Returns:
        메트릭 딕셔너리
    """
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
    
    return {
        'cpu_percent': cpu_percent,
        'cpu_count': cpu_count,
        'memory_total_gb': round(memory_total_gb, 2),
        'memory_used_gb': round(memory_used_gb, 2),
        'memory_percent': memory_percent,
        'disk_total_gb': round(disk_total_gb, 2),
        'disk_used_gb': round(disk_used_gb, 2),
        'disk_percent': disk_percent,
        'network_sent_mb': round(network_sent_mb, 2),
        'network_recv_mb': round(network_recv_mb, 2)
    }


def check_thresholds(metrics):
    """
    임계치 체크 및 경고 생성
    
    Args:
        metrics: 메트릭 딕셔너리
        
    Returns:
        경고 목록
    """
    warnings = []
    
    if metrics['cpu_percent'] > settings.cpu_threshold:
        warnings.append(
            f"⚠️  CPU usage high: {metrics['cpu_percent']:.1f}% "
            f"(threshold: {settings.cpu_threshold}%)"
        )
    
    if metrics['memory_percent'] > settings.memory_threshold:
        warnings.append(
            f"⚠️  Memory usage high: {metrics['memory_percent']:.1f}% "
            f"(threshold: {settings.memory_threshold}%)"
        )
    
    if metrics['disk_percent'] > settings.disk_threshold:
        warnings.append(
            f"⚠️  Disk usage high: {metrics['disk_percent']:.1f}% "
            f"(threshold: {settings.disk_threshold}%)"
        )
    
    return warnings


def save_metrics(metrics):
    """
    메트릭을 데이터베이스에 저장
    
    Args:
        metrics: 메트릭 딕셔너리
    """
    import socket
    
    try:
        with db.session_scope() as session:
            metric = SystemMetric(
                timestamp=datetime.utcnow(),
                hostname=socket.gethostname(),
                **metrics
            )
            session.add(metric)
        
        logger.info("✅ Metrics saved to database")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")


def main():
    """메인 실행 함수"""
    try:
        logger.info("=" * 60)
        logger.info("🖥️  System Monitoring Script Started")
        logger.info(f"Platform: {platform.system()} {platform.release()}")
        logger.info(f"Hostname: {platform.node()}")
        logger.info("=" * 60)
        
        # 메트릭 수집
        logger.info("Collecting system metrics...")
        metrics = get_system_metrics()
        
        # 결과 출력
        print("\n📊 System Metrics:")
        print(f"   CPU: {metrics['cpu_percent']:.1f}% ({metrics['cpu_count']} cores)")
        print(f"   Memory: {metrics['memory_used_gb']:.2f}GB / "
              f"{metrics['memory_total_gb']:.2f}GB ({metrics['memory_percent']:.1f}%)")
        print(f"   Disk: {metrics['disk_used_gb']:.2f}GB / "
              f"{metrics['disk_total_gb']:.2f}GB ({metrics['disk_percent']:.1f}%)")
        print(f"   Network: ↑ {metrics['network_sent_mb']:.2f}MB / "
              f"↓ {metrics['network_recv_mb']:.2f}MB")
        
        # 임계치 체크
        warnings = check_thresholds(metrics)
        if warnings:
            print("\n🚨 Warnings:")
            for warning in warnings:
                print(f"   {warning}")
                logger.warning(warning)
        else:
            print("\n✅ All metrics within normal range")
        
        # 데이터베이스에 저장
        save_metrics(metrics)
        
        logger.info("=" * 60)
        logger.info("✅ System Monitoring Completed")
        logger.info("=" * 60)
        
        # 경고가 있으면 종료 코드 1, 없으면 0
        return 1 if warnings else 0
    
    except Exception as e:
        logger.error(f"❌ Error during monitoring: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
