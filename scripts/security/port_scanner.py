#!/usr/bin/env python3
"""
포트 스캔 스크립트
열린 포트 및 실행 중인 서비스 확인
"""
import sys
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import concurrent.futures

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.logger import get_logger

logger = get_logger()


class PortScanner:
    """포트 스캔기"""
    
    # 일반적인 포트와 서비스 매핑
    COMMON_PORTS = {
        20: "FTP Data",
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        6379: "Redis",
        8080: "HTTP Proxy",
        8443: "HTTPS Alt",
        27017: "MongoDB"
    }
    
    # 위험한 포트 (일반적으로 닫혀있어야 함)
    RISKY_PORTS = {
        21: "FTP (Unencrypted)",
        23: "Telnet (Unencrypted)",
        445: "SMB (WannaCry vector)",
        3389: "RDP (Bruteforce target)",
        5900: "VNC (Weak authentication)"
    }
    
    def __init__(self, target: str = 'localhost', timeout: float = 1.0):
        """
        Args:
            target: 스캔할 대상 (IP 또는 도메인)
            timeout: 연결 타임아웃 (초)
        """
        self.target = target
        self.timeout = timeout
        self.open_ports: List[Dict] = []
        self.closed_ports: List[int] = []
    
    def scan_port(self, port: int) -> bool:
        """
        단일 포트 스캔
        
        Args:
            port: 포트 번호
            
        Returns:
            열려있으면 True
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.target, port))
            sock.close()
            
            return result == 0
        except Exception as e:
            logger.debug(f"Error scanning port {port}: {e}")
            return False
    
    def get_service_name(self, port: int) -> str:
        """
        포트 번호로 서비스 이름 추정
        
        Args:
            port: 포트 번호
            
        Returns:
            서비스 이름
        """
        # 커스텀 매핑 확인
        if port in self.COMMON_PORTS:
            return self.COMMON_PORTS[port]
        
        # 시스템 서비스 조회
        try:
            service = socket.getservbyport(port)
            return service
        except:
            return "Unknown"
    
    def is_risky_port(self, port: int) -> bool:
        """
        위험한 포트인지 확인
        
        Args:
            port: 포트 번호
            
        Returns:
            위험하면 True
        """
        return port in self.RISKY_PORTS
    
    def scan_port_range(self, start_port: int, end_port: int, 
                       max_workers: int = 50):
        """
        포트 범위 스캔 (멀티스레드)
        
        Args:
            start_port: 시작 포트
            end_port: 끝 포트
            max_workers: 최대 워커 수
        """
        logger.info(f"Scanning ports {start_port}-{end_port} on {self.target}...")
        
        ports_to_scan = range(start_port, end_port + 1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 포트 스캔 병렬 실행
            future_to_port = {
                executor.submit(self.scan_port, port): port 
                for port in ports_to_scan
            }
            
            for future in concurrent.futures.as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    is_open = future.result()
                    
                    if is_open:
                        service = self.get_service_name(port)
                        is_risky = self.is_risky_port(port)
                        
                        port_info = {
                            'port': port,
                            'service': service,
                            'risky': is_risky
                        }
                        
                        self.open_ports.append(port_info)
                        
                        risk_indicator = "🚨" if is_risky else "✓"
                        logger.info(f"{risk_indicator} Port {port} open - {service}")
                    else:
                        self.closed_ports.append(port)
                
                except Exception as e:
                    logger.error(f"Error scanning port {port}: {e}")
    
    def scan_common_ports(self):
        """일반적인 포트만 빠르게 스캔"""
        logger.info(f"Quick scan of common ports on {self.target}...")
        
        common_port_numbers = sorted(self.COMMON_PORTS.keys())
        
        for port in common_port_numbers:
            is_open = self.scan_port(port)
            
            if is_open:
                service = self.COMMON_PORTS[port]
                is_risky = self.is_risky_port(port)
                
                port_info = {
                    'port': port,
                    'service': service,
                    'risky': is_risky
                }
                
                self.open_ports.append(port_info)
                
                risk_indicator = "🚨" if is_risky else "✓"
                logger.info(f"{risk_indicator} Port {port} open - {service}")
            else:
                self.closed_ports.append(port)
    
    def get_process_info(self, port: int) -> Optional[str]:
        """
        포트를 사용하는 프로세스 정보 조회 (Linux only)
        
        Args:
            port: 포트 번호
            
        Returns:
            프로세스 정보 문자열
        """
        try:
            # lsof 명령 사용
            result = subprocess.run(
                ['lsof', '-i', f':{port}', '-P', '-n'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')[1:]  # 헤더 제외
                if lines:
                    return lines[0]  # 첫 번째 프로세스 반환
            
            return None
        
        except FileNotFoundError:
            # lsof 없으면 ss 사용
            try:
                result = subprocess.run(
                    ['ss', '-tulnp', f'sport = :{port}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        return lines[1]
                
                return None
            
            except:
                return None
        
        except Exception as e:
            logger.debug(f"Error getting process info for port {port}: {e}")
            return None
    
    def print_report(self):
        """스캔 결과 보고서 출력"""
        print("\n" + "=" * 60)
        print("🔌 PORT SCAN REPORT")
        print("=" * 60)
        print(f"Target: {self.target}")
        print(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Timeout: {self.timeout}s")
        print("")
        print(f"Open Ports: {len(self.open_ports)}")
        print(f"Closed Ports: {len(self.closed_ports)}")
        print("")
        
        if self.open_ports:
            print("📋 Open Ports:")
            print("-" * 60)
            
            # 위험한 포트 먼저
            risky_ports = [p for p in self.open_ports if p['risky']]
            safe_ports = [p for p in self.open_ports if not p['risky']]
            
            if risky_ports:
                print("\n🚨 RISKY PORTS (Security Concern):")
                for port_info in sorted(risky_ports, key=lambda x: x['port']):
                    port = port_info['port']
                    service = port_info['service']
                    
                    print(f"  Port {port:5d} - {service}")
                    
                    # 프로세스 정보 (가능하면)
                    process_info = self.get_process_info(port)
                    if process_info:
                        print(f"             Process: {process_info}")
                    
                    # 권장사항
                    if port in self.RISKY_PORTS:
                        print(f"             ⚠️  {self.RISKY_PORTS[port]}")
            
            if safe_ports:
                print("\n✅ Standard Ports:")
                for port_info in sorted(safe_ports, key=lambda x: x['port']):
                    port = port_info['port']
                    service = port_info['service']
                    
                    print(f"  Port {port:5d} - {service}")
        else:
            print("✅ No open ports found (or all ports closed)")
        
        print("=" * 60)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='포트 스캔 스크립트')
    parser.add_argument(
        '--target',
        default='localhost',
        help='스캔 대상 IP 또는 도메인 (기본: localhost)'
    )
    parser.add_argument(
        '--mode',
        choices=['quick', 'full', 'range'],
        default='quick',
        help='스캔 모드: quick (일반 포트만), full (1-65535), range (범위 지정)'
    )
    parser.add_argument(
        '--start-port',
        type=int,
        default=1,
        help='시작 포트 (range 모드에서만)'
    )
    parser.add_argument(
        '--end-port',
        type=int,
        default=1024,
        help='끝 포트 (range 모드에서만)'
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=1.0,
        help='연결 타임아웃 (초)'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("🔌 Port Scanner Started")
        logger.info(f"Target: {args.target}")
        logger.info(f"Mode: {args.mode}")
        logger.info("=" * 60)
        
        scanner = PortScanner(target=args.target, timeout=args.timeout)
        
        if args.mode == 'quick':
            # 일반 포트만 스캔
            scanner.scan_common_ports()
        
        elif args.mode == 'full':
            # 전체 포트 스캔 (1-65535)
            logger.warning("⚠️  Full scan may take a long time!")
            scanner.scan_port_range(1, 65535, max_workers=100)
        
        elif args.mode == 'range':
            # 범위 스캔
            scanner.scan_port_range(args.start_port, args.end_port)
        
        # 보고서 출력
        scanner.print_report()
        
        logger.info("=" * 60)
        logger.info("✅ Port Scan Completed")
        logger.info("=" * 60)
        
        # 위험한 포트가 열려있으면 종료 코드 1
        risky_open = any(p['risky'] for p in scanner.open_ports)
        return 1 if risky_open else 0
    
    except Exception as e:
        logger.error(f"❌ Error during port scan: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
