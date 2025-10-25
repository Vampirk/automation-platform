"""
작업 실행기 - 크로스 플랫폼 지원
Python 스크립트 및 시스템 명령 실행
Windows/Linux 모두 지원
"""
import os
import sys
import subprocess
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Any
import importlib.util
from config import settings
from core.logger import get_logger
from storage import db, Job, JobExecution, JobStatus

logger = get_logger()


class JobExecutor:
    """
    작업 실행기 클래스
    - Python 스크립트 동적 실행
    - 시스템 명령어 실행
    - 타임아웃 처리
    - 실행 결과 자동 기록
    - 크로스 플랫폼 지원
    """
    
    def __init__(self):
        self.hostname = socket.gethostname()
        self.platform = platform.system().lower()
    
    def execute_job(self, job_id: int) -> bool:
        """
        작업 실행 (데이터베이스 기반)
        
        Args:
            job_id: 작업 ID
            
        Returns:
            성공 여부
        """
        with db.session_scope() as session:
            # 작업 정보 조회
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job not found: {job_id}")
                return False
            
            logger.info(f"Executing job: {job.name} (ID: {job_id})")
            
            # 실행 이력 생성
            execution = JobExecution(
                job_id=job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.utcnow(),
                hostname=self.hostname,
                platform=self.platform
            )
            session.add(execution)
            session.commit()
            execution_id = execution.id
        
        # 실행
        success = False
        try:
            result = self._execute_script(
                script_path=job.script_path,
                timeout=job.timeout_seconds
            )
            
            # 결과 저장
            with db.session_scope() as session:
                execution = session.query(JobExecution).filter(
                    JobExecution.id == execution_id
                ).first()
                
                execution.completed_at = datetime.utcnow()
                execution.duration_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds()
                execution.stdout = result['stdout']
                execution.stderr = result['stderr']
                execution.exit_code = result['exit_code']
                
                if result['success']:
                    execution.status = JobStatus.SUCCESS
                    success = True
                    logger.info(
                        f"✅ Job completed: {job.name} "
                        f"({execution.duration_seconds:.2f}s)"
                    )
                else:
                    execution.status = JobStatus.FAILED
                    execution.error_message = result['error']
                    logger.error(f"❌ Job failed: {job.name} - {result['error']}")
                
                session.commit()
        
        except Exception as e:
            # 예외 처리
            logger.error(f"Job execution exception: {e}", exc_info=True)
            
            with db.session_scope() as session:
                execution = session.query(JobExecution).filter(
                    JobExecution.id == execution_id
                ).first()
                
                execution.completed_at = datetime.utcnow()
                execution.status = JobStatus.FAILED
                execution.error_message = str(e)
                session.commit()
        
        return success
    
    def _execute_script(
        self,
        script_path: str,
        timeout: int = 300
    ) -> dict:
        """
        스크립트 실행
        
        Args:
            script_path: 스크립트 경로
            timeout: 타임아웃 (초)
            
        Returns:
            실행 결과 딕셔너리
        """
        # 경로 정규화 (크로스 플랫폼)
        base_path = settings.get_base_path()
        full_path = base_path / script_path
        
        if not full_path.exists():
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Script not found: {full_path}',
                'error': f'Script not found: {full_path}'
            }
        
        # 파일 확장자로 실행 방법 결정
        extension = full_path.suffix.lower()
        
        if extension == '.py':
            return self._execute_python_script(full_path, timeout)
        elif extension in ['.sh', '.bash']:
            if self.platform == 'windows':
                return {
                    'success': False,
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': 'Shell scripts not supported on Windows',
                    'error': 'Shell scripts not supported on Windows'
                }
            return self._execute_shell_script(full_path, timeout)
        elif extension in ['.ps1', '.bat', '.cmd']:
            if self.platform != 'windows':
                return {
                    'success': False,
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': 'Windows scripts not supported on Linux',
                    'error': 'Windows scripts not supported on Linux'
                }
            return self._execute_windows_script(full_path, timeout)
        else:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Unsupported script type: {extension}',
                'error': f'Unsupported script type: {extension}'
            }
    
    def _execute_python_script(
        self,
        script_path: Path,
        timeout: int
    ) -> dict:
        """
        Python 스크립트 실행 (subprocess 사용)
        
        Args:
            script_path: 스크립트 절대 경로
            timeout: 타임아웃 (초)
            
        Returns:
            실행 결과
        """
        try:
            # Python 인터프리터 경로
            python_exe = sys.executable
            
            logger.debug(f"Executing Python script: {script_path}")
            logger.debug(f"Python executable: {python_exe}")
            
            # subprocess로 실행
            result = subprocess.run(
                [python_exe, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(script_path.parent)
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': None if result.returncode == 0 else result.stderr
            }
        
        except subprocess.TimeoutExpired as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Timeout after {timeout}s',
                'error': f'Timeout after {timeout}s'
            }
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'error': str(e)
            }
    
    def _execute_shell_script(
        self,
        script_path: Path,
        timeout: int
    ) -> dict:
        """
        Shell 스크립트 실행 (Linux/macOS)
        
        Args:
            script_path: 스크립트 절대 경로
            timeout: 타임아웃 (초)
            
        Returns:
            실행 결과
        """
        try:
            # 실행 권한 부여
            os.chmod(script_path, 0o755)
            
            result = subprocess.run(
                ['bash', str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(script_path.parent)
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': None if result.returncode == 0 else result.stderr
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Timeout after {timeout}s',
                'error': f'Timeout after {timeout}s'
            }
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'error': str(e)
            }
    
    def _execute_windows_script(
        self,
        script_path: Path,
        timeout: int
    ) -> dict:
        """
        Windows 스크립트 실행 (PowerShell, Batch)
        
        Args:
            script_path: 스크립트 절대 경로
            timeout: 타임아웃 (초)
            
        Returns:
            실행 결과
        """
        try:
            extension = script_path.suffix.lower()
            
            if extension == '.ps1':
                # PowerShell 실행
                cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]
            else:
                # Batch 파일 실행
                cmd = [str(script_path)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(script_path.parent),
                shell=True
            )
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': None if result.returncode == 0 else result.stderr
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Timeout after {timeout}s',
                'error': f'Timeout after {timeout}s'
            }
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'error': str(e)
            }


if __name__ == "__main__":
    # 테스트
    print("🧪 Executor Test")
    print("=" * 60)
    
    from storage import init_database
    
    # 데이터베이스 초기화
    init_database()
    
    # 테스트 스크립트 작성
    test_script_path = settings.get_base_path() / "scripts" / "test_script.py"
    test_script_path.parent.mkdir(parents=True, exist_ok=True)
    
    test_script_content = '''#!/usr/bin/env python3
import sys
import platform

print(f"Hello from test script!")
print(f"Platform: {platform.system()}")
print(f"Python: {sys.version}")
sys.exit(0)
'''
    
    with open(test_script_path, 'w') as f:
        f.write(test_script_content)
    
    print(f"Created test script: {test_script_path}")
    
    # Executor 테스트
    executor = JobExecutor()
    print(f"Hostname: {executor.hostname}")
    print(f"Platform: {executor.platform}")
    
    result = executor._execute_script(
        script_path="scripts/test_script.py",
        timeout=30
    )
    
    print("\n📋 Execution Result:")
    print(f"Success: {result['success']}")
    print(f"Exit Code: {result['exit_code']}")
    print(f"\n--- STDOUT ---")
    print(result['stdout'])
    if result['stderr']:
        print(f"\n--- STDERR ---")
        print(result['stderr'])
    
    print("\n✅ Executor test completed")
