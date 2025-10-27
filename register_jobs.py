#!/usr/bin/env python3
"""
작업 등록 스크립트
모든 자동화 스크립트를 스케줄러에 등록
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from storage import db, Job, JobType
from core.logger import get_logger

logger = get_logger()


def register_jobs():
    """모든 자동화 작업을 데이터베이스에 등록"""
    
    jobs_to_register = [
        # 1. 시스템 모니터링 (5분마다)
        {
            'name': 'system_monitoring',
            'description': '시스템 리소스(CPU/메모리/디스크/네트워크) 모니터링',
            'job_type': JobType.MONITORING,
            'script_path': 'scripts/monitoring/system_monitor.py',
            'cron_expression': '*/5 * * * *',  # 5분마다
            'enabled': True,
            'timeout_seconds': 60,
            'priority': 5
        },
        
        # 2. 보안 점검 (매일 새벽 2시)
        {
            'name': 'security_check',
            'description': '종합 보안 점검 (포트 스캔, 권한 검사, SSH 설정)',
            'job_type': JobType.SECURITY,
            'script_path': 'scripts/security/security_checker.py',
            'cron_expression': '0 2 * * *',  # 매일 02:00
            'enabled': True,
            'timeout_seconds': 600,
            'priority': 8
        },
        
        # 3. 로그 분석 (1시간마다)
        {
            'name': 'log_analysis',
            'description': '로그 파일 분석 및 이상 패턴 탐지',
            'job_type': JobType.LOG_ANALYSIS,
            'script_path': 'scripts/log_analysis/pattern_detector.py',
            'cron_expression': '0 * * * *',  # 매시간
            'enabled': True,
            'timeout_seconds': 300,
            'priority': 6
        },
        
        # 4. 로그 리포트 생성 (매일 새벽 3시)
        {
            'name': 'log_report',
            'description': '일별 로그 분석 리포트 생성',
            'job_type': JobType.LOG_ANALYSIS,
            'script_path': 'scripts/log_analysis/report_generator.py',
            'cron_expression': '0 3 * * *',  # 매일 03:00
            'enabled': True,
            'timeout_seconds': 300,
            'priority': 4
        },
        
        # 5. 계정 정책 검사 (매일 새벽 1시)
        {
            'name': 'account_policy_check',
            'description': '계정 정책 검사 및 의심스러운 계정 탐지',
            'job_type': JobType.ACCOUNT,
            'script_path': 'scripts/account_mgmt/account_checker.py',
            'cron_expression': '0 1 * * *',  # 매일 01:00
            'enabled': True,
            'timeout_seconds': 180,
            'priority': 7
        },
        
        # 6. 미사용 계정 탐지 (매주 일요일 새벽 4시)
        {
            'name': 'inactive_account_check',
            'description': '장기 미사용 계정 탐지 (90일+)',
            'job_type': JobType.ACCOUNT,
            'script_path': 'scripts/account_mgmt/inactive_finder.py',
            'cron_expression': '0 4 * * 0',  # 매주 일요일 04:00
            'enabled': True,
            'timeout_seconds': 180,
            'priority': 5
        },
        
        # 7. 포트 스캔 (매일 새벽 2시 30분)
        {
            'name': 'port_scan',
            'description': '빠른 포트 스캔 (주요 포트만)',
            'job_type': JobType.SECURITY,
            'script_path': 'scripts/security/port_scanner.py',
            'cron_expression': '30 2 * * *',  # 매일 02:30
            'enabled': False,  # 기본 비활성화 (필요 시 활성화)
            'timeout_seconds': 300,
            'priority': 6
        },
        
        # 8. 권한 검사 (매일 새벽 2시 45분)
        {
            'name': 'permission_check',
            'description': '중요 파일 및 SSH 키 권한 검사',
            'job_type': JobType.SECURITY,
            'script_path': 'scripts/security/permission_checker.py',
            'cron_expression': '45 2 * * *',  # 매일 02:45
            'enabled': True,
            'timeout_seconds': 180,
            'priority': 7
        }
    ]
    
    print("=" * 60)
    print("📋 작업 등록 시작")
    print("=" * 60)
    
    with db.session_scope() as session:
        registered_count = 0
        updated_count = 0
        
        for job_data in jobs_to_register:
            # 기존 작업 확인
            existing_job = session.query(Job).filter(
                Job.name == job_data['name']
            ).first()
            
            if existing_job:
                # 기존 작업 업데이트
                for key, value in job_data.items():
                    setattr(existing_job, key, value)
                
                print(f"   🔄 업데이트: {job_data['name']}")
                updated_count += 1
            else:
                # 새 작업 생성
                job = Job(**job_data)
                session.add(job)
                print(f"   ✅ 등록: {job_data['name']}")
                registered_count += 1
        
        session.commit()
    
    print()
    print("=" * 60)
    print("📊 등록 결과")
    print("=" * 60)
    print(f"   신규 등록: {registered_count}개")
    print(f"   업데이트: {updated_count}개")
    print(f"   총 작업: {registered_count + updated_count}개")
    print()
    
    # 등록된 작업 목록 출력
    print("=" * 60)
    print("📋 등록된 작업 목록")
    print("=" * 60)
    
    with db.session_scope() as session:
        jobs = session.query(Job).order_by(Job.priority.desc()).all()
        
        for job in jobs:
            status = "✅ 활성" if job.enabled else "⏸️  비활성"
            print(f"   {status} [{job.priority}] {job.name}")
            print(f"      유형: {job.job_type.value}")
            print(f"      스케줄: {job.cron_expression}")
            print(f"      스크립트: {job.script_path}")
            print()
    
    print("=" * 60)
    print("✅ 작업 등록 완료")
    print("=" * 60)
    print()
    print("💡 다음 단계:")
    print("   1. 스케줄러 시작: python main.py")
    print("   2. 대시보드 확인: http://localhost:8080")
    print("   3. API 확인: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    try:
        register_jobs()
        sys.exit(0)
    except Exception as e:
        logger.error(f"작업 등록 실패: {e}", exc_info=True)
        print(f"\n❌ 오류: {e}")
        sys.exit(1)
