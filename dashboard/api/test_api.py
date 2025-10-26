#!/usr/bin/env python3
"""
Dashboard API 테스트 스크립트
간단한 API 테스트 및 사용 예시
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_health():
    """헬스 체크 테스트"""
    print("=" * 60)
    print("🏥 Health Check")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def test_stats():
    """대시보드 통계 테스트"""
    print("=" * 60)
    print("📊 Dashboard Statistics")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/monitoring/stats")
    if response.status_code == 200:
        stats = response.json()
        print(f"Total Jobs: {stats['total_jobs']}")
        print(f"Enabled Jobs: {stats['enabled_jobs']}")
        print(f"Total Executions: {stats['total_executions']}")
        print(f"Success Rate: {stats['success_rate']}%")
        print(f"Total Notifications: {stats['total_notifications']}")
    else:
        print(f"Error: {response.status_code}")
    print()


def test_current_metrics():
    """현재 시스템 메트릭 테스트"""
    print("=" * 60)
    print("💻 Current System Metrics")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/monitoring/metrics/current")
    if response.status_code == 200:
        metrics = response.json()
        print(f"Hostname: {metrics['hostname']}")
        print(f"Timestamp: {metrics['timestamp']}")
        print(f"\nCPU:")
        print(f"  Percent: {metrics['cpu']['percent']}%")
        print(f"  Count: {metrics['cpu']['count']} cores")
        print(f"\nMemory:")
        print(f"  Total: {metrics['memory']['total_gb']:.2f} GB")
        print(f"  Used: {metrics['memory']['used_gb']:.2f} GB")
        print(f"  Percent: {metrics['memory']['percent']}%")
        print(f"\nDisk:")
        print(f"  Total: {metrics['disk']['total_gb']:.2f} GB")
        print(f"  Used: {metrics['disk']['used_gb']:.2f} GB")
        print(f"  Percent: {metrics['disk']['percent']}%")
    else:
        print(f"Error: {response.status_code}")
    print()


def test_list_jobs():
    """작업 목록 조회 테스트"""
    print("=" * 60)
    print("📋 Job List")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/jobs")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Jobs: {data['total']}")
        for job in data['items'][:5]:  # 상위 5개만 표시
            print(f"\nJob ID: {job['id']}")
            print(f"  Name: {job['name']}")
            print(f"  Type: {job['job_type']}")
            print(f"  Enabled: {job['enabled']}")
            print(f"  Cron: {job['cron_expression']}")
    else:
        print(f"Error: {response.status_code}")
    print()


def test_create_job():
    """작업 생성 테스트"""
    print("=" * 60)
    print("➕ Create Job")
    print("=" * 60)
    
    new_job = {
        "name": f"test_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "API 테스트 작업",
        "job_type": "monitoring",
        "script_path": "scripts/monitoring/system_monitor.py",
        "cron_expression": "0 * * * *",
        "enabled": True,
        "max_retries": 3,
        "timeout_seconds": 300,
        "priority": 5
    }
    
    response = requests.post(f"{BASE_URL}/jobs", json=new_job)
    if response.status_code == 201:
        job = response.json()
        print(f"✅ Job Created!")
        print(f"  ID: {job['id']}")
        print(f"  Name: {job['name']}")
        print(f"  Type: {job['job_type']}")
        return job['id']
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        return None
    print()


def test_execute_job(job_id):
    """작업 실행 테스트"""
    print("=" * 60)
    print(f"▶️  Execute Job {job_id}")
    print("=" * 60)
    
    response = requests.post(f"{BASE_URL}/jobs/{job_id}/execute")
    if response.status_code == 200:
        execution = response.json()
        print(f"✅ Job Executed!")
        print(f"  Execution ID: {execution['id']}")
        print(f"  Status: {execution['status']}")
        print(f"  Started: {execution['started_at']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
    print()


def test_recent_executions():
    """최근 실행 이력 테스트"""
    print("=" * 60)
    print("⏱️  Recent Executions")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/monitoring/executions/recent?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"Total Executions: {data['total']}")
        for execution in data['items']:
            print(f"\nExecution ID: {execution['id']}")
            print(f"  Job ID: {execution['job_id']}")
            print(f"  Status: {execution['status']}")
            print(f"  Duration: {execution.get('duration_seconds', 'N/A')}s")
    else:
        print(f"Error: {response.status_code}")
    print()


def test_system_health():
    """시스템 건강 상태 테스트"""
    print("=" * 60)
    print("🏥 System Health")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/monitoring/health")
    if response.status_code == 200:
        health = response.json()
        status_emoji = {"healthy": "✅", "warning": "⚠️", "critical": "🚨"}
        
        print(f"Overall Status: {status_emoji.get(health['status'], '❓')} {health['status'].upper()}")
        print(f"\nComponent Status:")
        print(f"  CPU: {status_emoji.get(health['cpu_status'], '❓')} {health['cpu_status']} ({health.get('current_cpu', 0)}%)")
        print(f"  Memory: {status_emoji.get(health['memory_status'], '❓')} {health['memory_status']} ({health.get('current_memory', 0)}%)")
        print(f"  Disk: {status_emoji.get(health['disk_status'], '❓')} {health['disk_status']} ({health.get('current_disk', 0)}%)")
        print(f"\nLast Check: {health['last_check']}")
    else:
        print(f"Error: {response.status_code}")
    print()


def main():
    """메인 함수"""
    print("\n" + "=" * 60)
    print("🧪 Automation Platform Dashboard API Test")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    print()
    
    try:
        # 1. 헬스 체크
        test_health()
        
        # 2. 대시보드 통계
        test_stats()
        
        # 3. 현재 시스템 메트릭
        test_current_metrics()
        
        # 4. 시스템 건강 상태
        test_system_health()
        
        # 5. 작업 목록 조회
        test_list_jobs()
        
        # 6. 작업 생성 (선택적)
        create_job = input("\n❓ Would you like to create a test job? (y/n): ")
        if create_job.lower() == 'y':
            job_id = test_create_job()
            
            if job_id:
                # 7. 작업 실행 (선택적)
                execute_job = input(f"\n❓ Would you like to execute job {job_id}? (y/n): ")
                if execute_job.lower() == 'y':
                    test_execute_job(job_id)
        
        # 8. 최근 실행 이력
        test_recent_executions()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print(f"   Please make sure the server is running at {BASE_URL}")
        print("   Run: python dashboard/api/main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
