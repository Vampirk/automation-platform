#!/usr/bin/env python3
"""
작업 실행기 - 크로스 플랫폼 지원
Python 스크립트 및 시스템 명령 실행
Windows/Linux 모두 지원

수정 이력:
  - 2025-10-27: SQLAlchemy 세션 관리 문제 수정
"""
import os
import sys
import subprocess
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Any, Dict
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
        # 먼저 Job 정보를 딕셔너리로 추출 (세션 밖에서 사용 가능)
        job_info = {}
        execution_id = None
        
        with db.session_scope() as session:
            # 작업 정보 조회
            job = session.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job not found: {job_id}")
                return False
            
            # ✅ Job 정보를 딕셔너리로 복사 (세션 독립적)
            job_info = {
                'id': job.id,
                'name': job.name,
                'script_path': job.script_path,
                'timeout_seconds': job.timeout_seconds
            }
            
            logger.info(f"Executing job: {job_info['name']} (ID: {job_id})")
            
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
        
        # ✅ 실행 (세션 밖에서, job_info 딕셔너리 사용)
        success = False
        try:
            result = self._execute_script(
                script_path=job_info['script_path'],
                timeout=job_info['timeout_seconds']
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
                        f"✅ Job completed: {job_info['name']} "
                        f"({execution.duration_seconds:.2f}s)"
                    )
                else:
                    execution.status = JobStatus.FAILED
                    execution.error_message = result['error']
                    logger.error(f"❌ Job failed: {job_info['name']} - {result['error']}")
                
                session.commit()
        
        except Exception as e:
            # 예외 처리
            logger.error(f"Job execution exception: {e}", exc_info=True)
            
            with db.session_scope() as session:
                execution = session.query(JobExecution).filter(
                    JobExecution.id == execution_id
                ).first()
                
                if execution:
                    execution.completed_at = datetime.utcnow()
                    execution.status = JobStatus.FAILED
                    execution.error_message = str(e)
                    session.commit()
        
        return success
    
    def _execute_script(
        self,
        script_path: str,
        timeout: int = 300
    ) -> Dict:
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
                'error': f'Script not found: {full_path}',
                'duration': 0
            }
        
        # 파일 확장자로 실행 방법 결정
        extension = full_path.suffix.lower()
        
        if extension == '.py':
            return self._execute_python(full_path, timeout)
        elif extension == '.sh' and self.platform != 'windows':
            return self._execute_shell(full_path, timeout)
        elif extension in ['.ps1', '.bat'] and self.platform == 'windows':
            return self._execute_powershell(full_path, timeout)
        else:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Unsupported script type: {extension}',
                'error': f'Unsupported script type: {extension}',
                'duration': 0
            }
    
    def _execute_python(self, script_path: Path, timeout: int) -> Dict:
        """Python 스크립트 실행"""
        try:
            start_time = datetime.utcnow()
            
            # subprocess로 실행
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': result.stderr if result.returncode != 0 else None,
                'duration': duration
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Script timeout after {timeout}s',
                'error': f'Timeout after {timeout}s',
                'duration': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'error': str(e),
                'duration': 0
            }
    
    def _execute_shell(self, script_path: Path, timeout: int) -> Dict:
        """Shell 스크립트 실행 (Linux/Mac)"""
        try:
            start_time = datetime.utcnow()
            
            result = subprocess.run(
                ['bash', str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': result.stderr if result.returncode != 0 else None,
                'duration': duration
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Script timeout after {timeout}s',
                'error': f'Timeout after {timeout}s',
                'duration': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'error': str(e),
                'duration': 0
            }
    
    def _execute_powershell(self, script_path: Path, timeout: int) -> Dict:
        """PowerShell/Batch 스크립트 실행 (Windows)"""
        try:
            start_time = datetime.utcnow()
            
            if script_path.suffix == '.ps1':
                cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(script_path)]
            else:
                cmd = [str(script_path)]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': result.stderr if result.returncode != 0 else None,
                'duration': duration
            }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f'Script timeout after {timeout}s',
                'error': f'Timeout after {timeout}s',
                'duration': timeout
            }
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'error': str(e),
                'duration': 0
            }


# ScriptExecutor 클래스 (API와의 호환성)
class ScriptExecutor(JobExecutor):
    """
    API에서 사용하는 스크립트 실행기
    JobExecutor의 별칭
    """
    
    def execute_script(self, script_path: str, timeout: int = 300) -> Dict:
        """
        스크립트 직접 실행 (Job 없이)
        
        Args:
            script_path: 스크립트 경로
            timeout: 타임아웃
            
        Returns:
            실행 결과
        """
        return self._execute_script(script_path, timeout)


if __name__ == "__main__":
    # 테스트
    print("=" * 60)
    print("🧪 Executor Test")
    print("=" * 60)
    
    executor = JobExecutor()
    
    # 시스템 정보 출력
    print(f"\nHostname: {executor.hostname}")
    print(f"Platform: {executor.platform}")
    
    # 테스트 스크립트 실행
    test_script = "scripts/monitoring/system_monitor.py"
    print(f"\nTesting script: {test_script}")
    
    result = executor._execute_script(test_script, timeout=60)
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Exit Code: {result['exit_code']}")
    print(f"  Duration: {result.get('duration', 0):.2f}s")
    
    if result['stdout']:
        print(f"\nStdout:\n{result['stdout'][:200]}...")
    
    if result['stderr']:
        print(f"\nStderr:\n{result['stderr'][:200]}...")