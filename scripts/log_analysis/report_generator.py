#!/usr/bin/env python3
"""
리포트 생성기 (Report Generator)
목적: 일별/주별 로그 분석 요약 리포트 생성
작성자: 1조 (남수민 2184039, 김규민 2084002, 임준호 2184XXX)
수정 이력:
  - 2025-10-26: 초기 버전 생성
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import json

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from core.logger import get_logger
from storage import db
from storage.models import Notification

# 다른 로그 분석 모듈 import
from .log_analyzer import LogAnalyzer, LogPatterns
from .pattern_detector import PatternDetector

logger = get_logger()


class ReportGenerator:
    """
    로그 분석 리포트 생성기
    
    일별/주별 로그 분석 결과를 종합하여 리포트 생성
    """
    
    def __init__(self):
        """초기화"""
        self.log_analyzer = LogAnalyzer()
        self.pattern_detector = PatternDetector()
        self.report_data = {}
        
    def analyze_logs(self, log_files: List[str]):
        """
        로그 파일들을 분석
        
        Args:
            log_files: 분석할 로그 파일 경로 리스트
        """
        logger.info("Starting log analysis for report generation")
        
        for log_file in log_files:
            if not Path(log_file).exists():
                logger.warning(f"Log file not found: {log_file}")
                continue
            
            # LogAnalyzer로 패턴 탐지
            self.log_analyzer.analyze_file(log_file)
            
            # PatternDetector로 시간대별 분석
            self.pattern_detector.analyze_file(log_file)
        
        logger.info("Log analysis completed")
    
    def generate_summary(self) -> Dict:
        """
        전체 요약 생성
        
        Returns:
            요약 딕셔너리
        """
        # LogAnalyzer 통계
        analyzer_stats = self.log_analyzer.get_statistics()
        
        # PatternDetector 통계
        anomalies = self.pattern_detector.detect_anomalies()
        hourly_summary = self.pattern_detector.get_hourly_summary()
        top_ips = self.pattern_detector.get_top_ips(10)
        top_errors = self.pattern_detector.get_top_errors(10)
        
        summary = {
            'generated_at': datetime.now().isoformat(),
            'total_lines_analyzed': analyzer_stats['total_lines'],
            'total_matches': analyzer_stats['total_matches'],
            'severity_breakdown': dict(analyzer_stats['severity_summary']),
            'top_patterns': [
                {'name': name, 'count': info['count'], 'severity': info['severity']}
                for name, info in analyzer_stats['top_issues'][:10]
            ],
            'hourly_activity': hourly_summary,
            'anomalies': anomalies,
            'top_failed_login_ips': [
                {'ip': ip, 'attempts': count} for ip, count in top_ips
            ],
            'top_errors': [
                {'message': msg[:100], 'count': count} 
                for msg, count in top_errors
            ],
        }
        
        return summary
    
    def generate_text_report(self, summary: Dict) -> str:
        """
        텍스트 형식 리포트 생성
        
        Args:
            summary: 요약 딕셔너리
            
        Returns:
            리포트 텍스트
        """
        lines = []
        lines.append("=" * 80)
        lines.append(" " * 25 + "📊 LOG ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"\n생성 시각: {summary['generated_at']}")
        lines.append(f"분석 기간: 최근 24시간")
        
        # 전체 요약
        lines.append("\n" + "─" * 80)
        lines.append("📈 전체 요약")
        lines.append("─" * 80)
        lines.append(f"총 분석 라인 수: {summary['total_lines_analyzed']:,}개")
        lines.append(f"패턴 매치 수: {summary['total_matches']:,}개")
        
        if summary['total_lines_analyzed'] > 0:
            match_rate = (summary['total_matches'] / summary['total_lines_analyzed']) * 100
            lines.append(f"매치 비율: {match_rate:.2f}%")
        
        # 심각도별 통계
        if summary['severity_breakdown']:
            lines.append("\n🚨 심각도별 통계:")
            for severity, count in sorted(
                summary['severity_breakdown'].items(),
                key=lambda x: {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(x[0], 0),
                reverse=True
            ):
                lines.append(f"  • {severity:8s}: {count:>5,}개")
        
        # 상위 패턴
        if summary['top_patterns']:
            lines.append("\n" + "─" * 80)
            lines.append("🔝 상위 탐지 패턴 (Top 10)")
            lines.append("─" * 80)
            for i, pattern in enumerate(summary['top_patterns'], 1):
                lines.append(
                    f"{i:2d}. [{pattern['severity']:8s}] "
                    f"{pattern['name']:30s}: {pattern['count']:>5,}회"
                )
        
        # 시간대별 활동
        if summary['hourly_activity']:
            lines.append("\n" + "─" * 80)
            lines.append("⏰ 시간대별 활동 (활동이 많은 시간대)")
            lines.append("─" * 80)
            
            # 활동이 많은 상위 5개 시간대
            sorted_hours = sorted(
                summary['hourly_activity'].items(),
                key=lambda x: x[1]['total_events'],
                reverse=True
            )[:5]
            
            for hour, stats in sorted_hours:
                lines.append(
                    f"{hour:02d}:00 시간대 - "
                    f"총 {stats['total_events']:>4}개 "
                    f"(실패: {stats['failed']:>3}, "
                    f"에러: {stats['error']:>3}, "
                    f"경고: {stats['warning']:>3})"
                )
        
        # 실패한 로그인 시도 (상위 IP)
        if summary['top_failed_login_ips']:
            lines.append("\n" + "─" * 80)
            lines.append("🌐 실패한 로그인 시도 (Top 10 IP)")
            lines.append("─" * 80)
            for i, ip_info in enumerate(summary['top_failed_login_ips'], 1):
                lines.append(f"{i:2d}. {ip_info['ip']:15s}: {ip_info['attempts']:>5}회 시도")
        
        # 상위 에러 메시지
        if summary['top_errors']:
            lines.append("\n" + "─" * 80)
            lines.append("❌ 빈번한 에러 메시지 (Top 10)")
            lines.append("─" * 80)
            for i, error_info in enumerate(summary['top_errors'], 1):
                lines.append(f"{i:2d}. [{error_info['count']:>4}회] {error_info['message']}")
        
        # 이상 패턴
        if summary['anomalies']:
            lines.append("\n" + "─" * 80)
            lines.append("🚨 탐지된 이상 패턴")
            lines.append("─" * 80)
            for i, anomaly in enumerate(summary['anomalies'], 1):
                lines.append(
                    f"{i:2d}. [{anomaly['severity']:8s}] "
                    f"{anomaly['description']}"
                )
        else:
            lines.append("\n✅ 이상 패턴이 탐지되지 않았습니다.")
        
        # 권장 사항
        lines.append("\n" + "─" * 80)
        lines.append("💡 권장 사항")
        lines.append("─" * 80)
        
        recommendations = self._generate_recommendations(summary)
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        lines.append("\n" + "=" * 80)
        lines.append(" " * 28 + "END OF REPORT")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """
        권장 사항 생성
        
        Args:
            summary: 요약 딕셔너리
            
        Returns:
            권장 사항 리스트
        """
        recommendations = []
        
        # 심각도가 높은 이벤트가 많은 경우
        severity = summary.get('severity_breakdown', {})
        if severity.get('CRITICAL', 0) > 0:
            recommendations.append(
                f"CRITICAL 레벨 이벤트 {severity['CRITICAL']}개 발견. "
                "즉시 확인이 필요합니다."
            )
        
        if severity.get('HIGH', 0) > 10:
            recommendations.append(
                f"HIGH 레벨 이벤트 {severity['HIGH']}개 발견. "
                "빠른 시일 내 조치가 필요합니다."
            )
        
        # 실패한 로그인 시도가 많은 경우
        if summary['top_failed_login_ips']:
            top_ip = summary['top_failed_login_ips'][0]
            if top_ip['attempts'] >= 10:
                recommendations.append(
                    f"IP {top_ip['ip']}에서 {top_ip['attempts']}회 로그인 실패. "
                    "브루트포스 공격 가능성이 있으니 해당 IP를 차단하거나 조사하세요."
                )
        
        # 이상 패턴이 탐지된 경우
        anomalies = summary.get('anomalies', [])
        critical_anomalies = [a for a in anomalies if a['severity'] == 'CRITICAL']
        high_anomalies = [a for a in anomalies if a['severity'] == 'HIGH']
        
        if critical_anomalies:
            recommendations.append(
                f"{len(critical_anomalies)}개의 심각한 이상 패턴 탐지됨. "
                "보안 담당자에게 알리고 즉시 조사하세요."
            )
        
        if high_anomalies:
            recommendations.append(
                f"{len(high_anomalies)}개의 주의가 필요한 이상 패턴 탐지됨. "
                "로그를 확인하고 필요 시 대응하세요."
            )
        
        # 권장 사항이 없는 경우
        if not recommendations:
            recommendations.append(
                "현재 심각한 문제는 발견되지 않았습니다. "
                "정기적인 모니터링을 계속하세요."
            )
        
        return recommendations
    
    def generate_json_report(self, summary: Dict) -> str:
        """
        JSON 형식 리포트 생성
        
        Args:
            summary: 요약 딕셔너리
            
        Returns:
            JSON 문자열
        """
        return json.dumps(summary, indent=2, ensure_ascii=False)
    
    def save_report(self, report_text: str, output_file: str):
        """
        리포트를 파일로 저장
        
        Args:
            report_text: 리포트 텍스트
            output_file: 출력 파일 경로
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            logger.info(f"Report saved to: {output_path}")
            print(f"\n✅ 리포트가 저장되었습니다: {output_path}")
        
        except Exception as e:
            logger.error(f"Failed to save report: {e}")


def main():
    """메인 실행 함수"""
    try:
        logger.info("=" * 60)
        logger.info("📊 Report Generator Started")
        logger.info("=" * 60)
        
        # 분석할 로그 파일들
        log_files = [
            '/var/log/auth.log',
            '/var/log/syslog',
            '/var/log/kern.log',
        ]
        
        # Linux 시스템인지 확인
        if not settings.is_linux():
            logger.warning("This script is designed for Linux systems")
            return 1
        
        # 리포트 생성기 초기화
        generator = ReportGenerator()
        
        # 로그 분석
        generator.analyze_logs(log_files)
        
        # 요약 생성
        summary = generator.generate_summary()
        
        # 텍스트 리포트 생성
        text_report = generator.generate_text_report(summary)
        
        # 콘솔에 출력
        print(text_report)
        
        # 파일로 저장
        today = datetime.now().strftime("%Y-%m-%d")
        report_dir = settings.get_base_path() / "reports" / "logs"
        
        # 텍스트 리포트 저장
        text_file = report_dir / f"log_analysis_report_{today}.txt"
        generator.save_report(text_report, str(text_file))
        
        # JSON 리포트 저장
        json_report = generator.generate_json_report(summary)
        json_file = report_dir / f"log_analysis_report_{today}.json"
        generator.save_report(json_report, str(json_file))
        
        logger.info("=" * 60)
        logger.info("✅ Report Generation Completed")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error during report generation: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
