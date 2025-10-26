#!/usr/bin/env python3
"""
파일 권한 검사 스크립트
시스템 전체 또는 특정 디렉토리의 파일 권한 검사
"""
import sys
import os
import stat
import pwd
import grp
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.logger import get_logger

logger = get_logger()


class PermissionIssue:
    """권한 이슈"""
    
    def __init__(self, path: str, issue_type: str, current: str, 
                 expected: str, severity: str):
        self.path = path
        self.issue_type = issue_type
        self.current = current
        self.expected = expected
        self.severity = severity
    
    def __repr__(self):
        return (
            f"[{self.severity}] {self.path}\n"
            f"  Issue: {self.issue_type}\n"
            f"  Current: {self.current}\n"
            f"  Expected: {self.expected}"
        )


class PermissionChecker:
    """권한 검사기"""
    
    # 중요 시스템 파일 및 기대되는 권한
    CRITICAL_FILES = {
        '/etc/passwd': {'mode': '0644', 'owner': 'root', 'group': 'root'},
        '/etc/shadow': {'mode': '0640', 'owner': 'root', 'group': 'shadow'},
        '/etc/group': {'mode': '0644', 'owner': 'root', 'group': 'root'},
        '/etc/gshadow': {'mode': '0640', 'owner': 'root', 'group': 'shadow'},
        '/etc/ssh/sshd_config': {'mode': '0600', 'owner': 'root', 'group': 'root'},
        '/etc/sudoers': {'mode': '0440', 'owner': 'root', 'group': 'root'},
        '/root': {'mode': '0700', 'owner': 'root', 'group': 'root'},
        '/root/.ssh': {'mode': '0700', 'owner': 'root', 'group': 'root'},
    }
    
    # 위험한 권한 (world-writable 등)
    DANGEROUS_PERMISSIONS = [
        0o002,  # world-writable
        0o020,  # group-writable (특정 상황에서)
    ]
    
    # 스킵할 디렉토리
    SKIP_DIRECTORIES = ['lost+found', 'proc', 'sys', 'dev']
    
    def __init__(self):
        self.issues: List[PermissionIssue] = []
        self.files_checked = 0
        self.files_ok = 0
        self.files_skipped = 0
    
    def get_file_permissions(self, path: Path) -> Dict:
        """
        파일의 권한 정보 조회
        
        Args:
            path: 파일 경로
            
        Returns:
            권한 정보 딕셔너리
        """
        try:
            stat_info = path.stat()
            
            # 권한 (8진수)
            mode = stat.filemode(stat_info.st_mode)
            mode_octal = oct(stat_info.st_mode)[-4:]
            
            # 소유자
            try:
                owner = pwd.getpwuid(stat_info.st_uid).pw_name
            except KeyError:
                owner = str(stat_info.st_uid)
            
            # 그룹
            try:
                group = grp.getgrgid(stat_info.st_gid).gr_name
            except KeyError:
                group = str(stat_info.st_gid)
            
            return {
                'mode': mode,
                'mode_octal': mode_octal,
                'owner': owner,
                'group': group,
                'uid': stat_info.st_uid,
                'gid': stat_info.st_gid,
                'size': stat_info.st_size,
                'mtime': datetime.fromtimestamp(stat_info.st_mtime)
            }
        
        except PermissionError:
            logger.debug(f"Permission denied: {path}")
            return None
        except Exception as e:
            logger.debug(f"Error getting permissions for {path}: {e}")
            return None
    
    def check_file(self, path: Path, expected: Dict) -> bool:
        """
        단일 파일 권한 검사
        
        Args:
            path: 파일 경로
            expected: 기대되는 권한
            
        Returns:
            문제없으면 True
        """
        self.files_checked += 1
        
        try:
            # exists() 체크도 권한 에러를 발생시킬 수 있음
            if not path.exists():
                logger.debug(f"File not found: {path}")
                self.files_skipped += 1
                return True  # 파일이 없으면 넘어감
            
            perms = self.get_file_permissions(path)
            if not perms:
                logger.debug(f"Cannot access: {path}")
                self.files_skipped += 1
                return True  # 권한 문제로 접근 불가하면 넘어감
            
            has_issue = False
            
            # 권한 체크
            if 'mode' in expected:
                expected_mode = expected['mode']
                if perms['mode_octal'] != expected_mode:
                    self.issues.append(PermissionIssue(
                        path=str(path),
                        issue_type="Incorrect Permissions",
                        current=perms['mode_octal'],
                        expected=expected_mode,
                        severity="HIGH"
                    ))
                    has_issue = True
            
            # 소유자 체크
            if 'owner' in expected:
                if perms['owner'] != expected['owner']:
                    self.issues.append(PermissionIssue(
                        path=str(path),
                        issue_type="Incorrect Owner",
                        current=perms['owner'],
                        expected=expected['owner'],
                        severity="HIGH"
                    ))
                    has_issue = True
            
            # 그룹 체크
            if 'group' in expected:
                if perms['group'] != expected['group']:
                    self.issues.append(PermissionIssue(
                        path=str(path),
                        issue_type="Incorrect Group",
                        current=perms['group'],
                        expected=expected['group'],
                        severity="MEDIUM"
                    ))
                    has_issue = True
            
            if not has_issue:
                self.files_ok += 1
                logger.debug(f"✓ {path}: OK")
            
            return not has_issue
        
        except PermissionError:
            logger.debug(f"Permission denied: {path}")
            self.files_skipped += 1
            return True
        except Exception as e:
            logger.debug(f"Error checking {path}: {e}")
            self.files_skipped += 1
            return True
    
    def check_critical_files(self):
        """중요 시스템 파일 검사"""
        logger.info("=" * 60)
        logger.info("🔒 Checking critical system files...")
        logger.info("=" * 60)
        
        for file_path, expected in self.CRITICAL_FILES.items():
            path = Path(file_path)
            self.check_file(path, expected)
    
    def check_world_writable(self, directory: Path, recursive: bool = True):
        """
        world-writable 파일 검색
        
        Args:
            directory: 검색할 디렉토리
            recursive: 하위 디렉토리도 검색
        """
        logger.info("=" * 60)
        logger.info(f"🌍 Checking for world-writable files in {directory}...")
        logger.info("=" * 60)
        
        try:
            if recursive:
                files = directory.rglob('*')
            else:
                files = directory.glob('*')
            
            for path in files:
                try:
                    if not path.exists():
                        continue
                    
                    stat_info = path.stat()
                    mode = stat_info.st_mode
                    
                    # world-writable 체크 (others에 write 권한)
                    if mode & stat.S_IWOTH:
                        perms = self.get_file_permissions(path)
                        if perms:
                            self.issues.append(PermissionIssue(
                                path=str(path),
                                issue_type="World-Writable File",
                                current=perms['mode_octal'],
                                expected="Remove write permission for others",
                                severity="CRITICAL"
                            ))
                            
                            logger.warning(f"🚨 World-writable: {path} ({perms['mode_octal']})")
                
                except PermissionError:
                    continue
                except Exception as e:
                    logger.debug(f"Error checking {path}: {e}")
        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    def check_suid_sgid_files(self, directory: Path):
        """
        SUID/SGID 파일 검색
        
        Args:
            directory: 검색할 디렉토리
        """
        logger.info("=" * 60)
        logger.info(f"🔑 Checking for SUID/SGID files in {directory}...")
        logger.info("=" * 60)
        
        suid_files = []
        sgid_files = []
        
        try:
            for path in directory.rglob('*'):
                try:
                    if not path.exists() or not path.is_file():
                        continue
                    
                    stat_info = path.stat()
                    mode = stat_info.st_mode
                    
                    # SUID 체크
                    if mode & stat.S_ISUID:
                        perms = self.get_file_permissions(path)
                        if perms:
                            suid_files.append((str(path), perms))
                            logger.info(f"SUID: {path} ({perms['mode_octal']})")
                    
                    # SGID 체크
                    if mode & stat.S_ISGID:
                        perms = self.get_file_permissions(path)
                        if perms:
                            sgid_files.append((str(path), perms))
                            logger.info(f"SGID: {path} ({perms['mode_octal']})")
                
                except PermissionError:
                    continue
                except Exception as e:
                    logger.debug(f"Error checking {path}: {e}")
        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
        
        logger.info(f"Found {len(suid_files)} SUID files")
        logger.info(f"Found {len(sgid_files)} SGID files")
    
    def check_ssh_keys(self):
        """SSH 키 파일 권한 검사"""
        logger.info("=" * 60)
        logger.info("🔑 Checking SSH key permissions...")
        logger.info("=" * 60)
        
        # /home 디렉토리의 모든 사용자 확인
        home_dir = Path('/home')
        
        if not home_dir.exists():
            logger.warning("⚠️  /home directory not found")
            return
        
        try:
            for user_dir in home_dir.iterdir():
                # 스킵할 디렉토리 체크
                if user_dir.name in self.SKIP_DIRECTORIES:
                    logger.debug(f"Skipping {user_dir}")
                    continue
                
                try:
                    if not user_dir.is_dir():
                        continue
                    
                    ssh_dir = user_dir / '.ssh'
                    if not ssh_dir.exists():
                        continue
                    
                    # .ssh 디렉토리 권한 (700)
                    ssh_perms = self.get_file_permissions(ssh_dir)
                    if ssh_perms and ssh_perms['mode_octal'] != '0700':
                        self.issues.append(PermissionIssue(
                            path=str(ssh_dir),
                            issue_type="Incorrect SSH Directory Permissions",
                            current=ssh_perms['mode_octal'],
                            expected='0700',
                            severity="HIGH"
                        ))
                    
                    # private key 파일들 (600)
                    for key_file in ssh_dir.glob('id_*'):
                        if key_file.suffix == '.pub':
                            continue  # 공개키는 제외
                        
                        key_perms = self.get_file_permissions(key_file)
                        if key_perms:
                            if key_perms['mode_octal'] not in ['0600', '0400']:
                                self.issues.append(PermissionIssue(
                                    path=str(key_file),
                                    issue_type="Insecure Private Key Permissions",
                                    current=key_perms['mode_octal'],
                                    expected='0600',
                                    severity="CRITICAL"
                                ))
                                logger.warning(f"🚨 Insecure SSH key: {key_file}")
                
                except PermissionError:
                    logger.debug(f"Permission denied: {user_dir}")
                    continue
                except Exception as e:
                    logger.debug(f"Error checking {user_dir}: {e}")
                    continue
        
        except PermissionError:
            logger.warning("⚠️  Permission denied accessing /home")
        except Exception as e:
            logger.error(f"Error checking SSH keys: {e}")
    
    def print_report(self):
        """검사 결과 보고서 출력"""
        print("\n" + "=" * 60)
        print("🔐 PERMISSION CHECK REPORT")
        print("=" * 60)
        print(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        print(f"Files Checked: {self.files_checked}")
        print(f"Files OK: {self.files_ok}")
        print(f"Files Skipped: {self.files_skipped}")
        print(f"Issues Found: {len(self.issues)}")
        print("")
        
        if self.issues:
            # 심각도별로 그룹화
            issues_by_severity = {}
            for issue in self.issues:
                if issue.severity not in issues_by_severity:
                    issues_by_severity[issue.severity] = []
                issues_by_severity[issue.severity].append(issue)
            
            severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
            
            print("🚨 Issues Found:")
            print("")
            
            for severity in severity_order:
                if severity in issues_by_severity:
                    issues = issues_by_severity[severity]
                    print(f"[{severity}] - {len(issues)} issue(s)")
                    print("-" * 60)
                    
                    for issue in issues:
                        print(f"  Path: {issue.path}")
                        print(f"  Issue: {issue.issue_type}")
                        print(f"  Current: {issue.current}")
                        print(f"  Expected: {issue.expected}")
                        print("")
        else:
            print("✅ No permission issues found!")
        
        print("=" * 60)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='파일 권한 검사 스크립트')
    parser.add_argument(
        '--mode',
        choices=['critical', 'world-writable', 'suid', 'ssh', 'all'],
        default='critical',
        help='검사 모드'
    )
    parser.add_argument(
        '--directory',
        default='/home',
        help='검사할 디렉토리 (world-writable, suid 모드에서만)'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='하위 디렉토리 검사 안 함'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("🔐 Permission Checker Started")
        logger.info(f"Mode: {args.mode}")
        logger.info("=" * 60)
        
        checker = PermissionChecker()
        
        if args.mode in ['critical', 'all']:
            checker.check_critical_files()
        
        if args.mode in ['world-writable', 'all']:
            directory = Path(args.directory)
            recursive = not args.no_recursive
            checker.check_world_writable(directory, recursive)
        
        if args.mode in ['suid', 'all']:
            directory = Path(args.directory)
            checker.check_suid_sgid_files(directory)
        
        if args.mode in ['ssh', 'all']:
            checker.check_ssh_keys()
        
        # 보고서 출력
        checker.print_report()
        
        logger.info("=" * 60)
        logger.info("✅ Permission Check Completed")
        logger.info("=" * 60)
        
        # 심각한 이슈가 있으면 종료 코드 1
        critical_issues = [i for i in checker.issues if i.severity == 'CRITICAL']
        return 1 if critical_issues else 0
    
    except Exception as e:
        logger.error(f"❌ Error during permission check: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)