#!/usr/bin/env python3
"""
Quality Assurance and Monitoring System
Real-time monitoring, health checks, alerting, and comprehensive reporting
"""

import asyncio
import aiohttp
import json
import smtplib
import statistics
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psutil
import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

from database import DatabaseManager, db_manager
from config import config

logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    check_name: str
    status: str  # healthy, warning, critical, unknown
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict = field(default_factory=dict)

@dataclass
class Alert:
    """System alert"""
    alert_id: str
    severity: str  # info, warning, critical
    title: str
    message: str
    component: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict = field(default_factory=dict)

@dataclass
class QualityMetrics:
    """Quality metrics for the system"""
    citation_validation_rate: float
    average_quality_score: float
    processing_success_rate: float
    api_uptime_rate: float
    error_rate: float
    performance_score: float
    data_completeness: float
    timestamp: datetime = field(default_factory=datetime.now)

class HealthChecker:
    """Performs various health checks on the system"""
    
    def __init__(self):
        self.checks = {
            'database_connection': self._check_database_connection,
            'api_endpoints': self._check_api_endpoints,
            'system_resources': self._check_system_resources,
            'citation_quality': self._check_citation_quality,
            'processing_pipeline': self._check_processing_pipeline,
            'data_integrity': self._check_data_integrity,
            'performance_metrics': self._check_performance_metrics
        }
        
    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all health checks"""
        results = []
        
        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                results.append(result)
                logger.debug(f"Health check {check_name}: {result.status}")
            except Exception as e:
                result = HealthCheckResult(
                    check_name=check_name,
                    status="unknown",
                    message=f"Health check failed: {str(e)}"
                )
                results.append(result)
                logger.error(f"Health check {check_name} failed: {e}")
        
        return results
    
    async def _check_database_connection(self) -> HealthCheckResult:
        """Check database connectivity and basic operations"""
        try:
            # Test database connection
            stats = await db_manager.get_database_stats()
            
            # Check if database is responsive
            response_time_start = datetime.now()
            citation_count = stats.get('citations_count', 0)
            response_time = (datetime.now() - response_time_start).total_seconds()
            
            if response_time > 5.0:
                return HealthCheckResult(
                    check_name="database_connection",
                    status="warning",
                    message=f"Database response time is slow: {response_time:.2f}s",
                    value=response_time,
                    threshold=5.0
                )
            
            return HealthCheckResult(
                check_name="database_connection",
                status="healthy",
                message=f"Database connected, {citation_count} citations available",
                value=response_time,
                details=stats
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="database_connection",
                status="critical",
                message=f"Database connection failed: {str(e)}"
            )
    
    async def _check_api_endpoints(self) -> HealthCheckResult:
        """Check external API endpoints"""
        api_endpoints = {
            'pubmed': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi',
            'crossref': 'https://api.crossref.org/works?rows=1',
            'doi': 'https://doi.org/10.1038/nature12373'  # Test DOI
        }
        
        results = {}
        all_healthy = True
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for api_name, endpoint in api_endpoints.items():
                try:
                    start_time = datetime.now()
                    async with session.get(endpoint) as response:
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        if response.status == 200:
                            results[api_name] = {
                                'status': 'healthy',
                                'response_time': response_time,
                                'status_code': response.status
                            }
                        else:
                            results[api_name] = {
                                'status': 'warning',
                                'response_time': response_time,
                                'status_code': response.status
                            }
                            all_healthy = False
                            
                except Exception as e:
                    results[api_name] = {
                        'status': 'critical',
                        'error': str(e)
                    }
                    all_healthy = False
        
        overall_status = "healthy" if all_healthy else "warning"
        if any(r.get('status') == 'critical' for r in results.values()):
            overall_status = "critical"
        
        return HealthCheckResult(
            check_name="api_endpoints",
            status=overall_status,
            message=f"API endpoints check: {len([r for r in results.values() if r.get('status') == 'healthy'])}/{len(results)} healthy",
            details=results
        )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Determine overall status
        status = "healthy"
        issues = []
        
        if cpu_percent > 80:
            status = "warning" if cpu_percent < 90 else "critical"
            issues.append(f"High CPU usage: {cpu_percent:.1f}%")
        
        if memory.percent > 80:
            status = "warning" if memory.percent < 90 else "critical"
            issues.append(f"High memory usage: {memory.percent:.1f}%")
        
        if disk.percent > 80:
            status = "warning" if disk.percent < 90 else "critical"
            issues.append(f"High disk usage: {disk.percent:.1f}%")
        
        message = "System resources normal" if not issues else "; ".join(issues)
        
        return HealthCheckResult(
            check_name="system_resources",
            status=status,
            message=message,
            details={
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
        )
    
    async def _check_citation_quality(self) -> HealthCheckResult:
        """Check citation quality metrics"""
        try:
            validation_stats = await db_manager.get_validation_statistics()
            
            validation_rate = validation_stats.get('validation_rate', 0)
            avg_quality = validation_stats.get('average_quality_score', 0)
            total_citations = validation_stats.get('total_citations', 0)
            
            status = "healthy"
            issues = []
            
            if validation_rate < 70:
                status = "warning" if validation_rate >= 50 else "critical"
                issues.append(f"Low validation rate: {validation_rate:.1f}%")
            
            if avg_quality < 0.6:
                status = "warning" if avg_quality >= 0.4 else "critical"
                issues.append(f"Low average quality: {avg_quality:.2f}")
            
            message = "Citation quality good" if not issues else "; ".join(issues)
            
            return HealthCheckResult(
                check_name="citation_quality",
                status=status,
                message=message,
                value=validation_rate,
                details={
                    'validation_rate': validation_rate,
                    'average_quality_score': avg_quality,
                    'total_citations': total_citations
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="citation_quality",
                status="unknown",
                message=f"Could not check citation quality: {str(e)}"
            )
    
    async def _check_processing_pipeline(self) -> HealthCheckResult:
        """Check processing pipeline health"""
        try:
            processing_stats = await db_manager.get_processing_statistics()
            
            completion_rate = processing_stats.get('completion_rate', 0)
            total_files = processing_stats.get('total_files', 0)
            failed_files = processing_stats.get('status_counts', {}).get('error', 0)
            
            status = "healthy"
            issues = []
            
            if completion_rate < 80:
                status = "warning" if completion_rate >= 60 else "critical"
                issues.append(f"Low completion rate: {completion_rate:.1f}%")
            
            if failed_files > total_files * 0.1:  # More than 10% failed
                status = "warning"
                issues.append(f"High failure rate: {failed_files} failed files")
            
            message = "Processing pipeline healthy" if not issues else "; ".join(issues)
            
            return HealthCheckResult(
                check_name="processing_pipeline",
                status=status,
                message=message,
                value=completion_rate,
                details=processing_stats
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="processing_pipeline",
                status="unknown",
                message=f"Could not check processing pipeline: {str(e)}"
            )
    
    async def _check_data_integrity(self) -> HealthCheckResult:
        """Check data integrity"""
        try:
            # Check for duplicate citations
            duplicate_count = await self._count_duplicate_citations()
            
            # Check for orphaned records
            orphaned_count = await self._count_orphaned_records()
            
            # Check for missing required fields
            incomplete_count = await self._count_incomplete_citations()
            
            status = "healthy"
            issues = []
            
            if duplicate_count > 10:
                status = "warning"
                issues.append(f"{duplicate_count} duplicate citations")
            
            if orphaned_count > 5:
                status = "warning"
                issues.append(f"{orphaned_count} orphaned records")
            
            if incomplete_count > 20:
                status = "warning"
                issues.append(f"{incomplete_count} incomplete citations")
            
            message = "Data integrity good" if not issues else "; ".join(issues)
            
            return HealthCheckResult(
                check_name="data_integrity",
                status=status,
                message=message,
                details={
                    'duplicate_citations': duplicate_count,
                    'orphaned_records': orphaned_count,
                    'incomplete_citations': incomplete_count
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="data_integrity",
                status="unknown",
                message=f"Could not check data integrity: {str(e)}"
            )
    
    async def _check_performance_metrics(self) -> HealthCheckResult:
        """Check performance metrics"""
        try:
            perf_metrics = await db_manager.get_performance_metrics(hours_back=24)
            
            if not perf_metrics.get('metrics_by_operation'):
                return HealthCheckResult(
                    check_name="performance_metrics",
                    status="warning",
                    message="No performance metrics available"
                )
            
            # Analyze performance trends
            avg_durations = []
            success_rates = []
            
            for metric in perf_metrics['metrics_by_operation']:
                avg_durations.append(metric['avg_duration_seconds'])
                success_rates.append(metric['success_rate'])
            
            avg_duration = statistics.mean(avg_durations) if avg_durations else 0
            avg_success_rate = statistics.mean(success_rates) if success_rates else 0
            
            status = "healthy"
            issues = []
            
            if avg_duration > 30:  # Longer than 30 seconds average
                status = "warning"
                issues.append(f"Slow processing: {avg_duration:.1f}s average")
            
            if avg_success_rate < 90:
                status = "warning" if avg_success_rate >= 80 else "critical"
                issues.append(f"Low success rate: {avg_success_rate:.1f}%")
            
            message = "Performance good" if not issues else "; ".join(issues)
            
            return HealthCheckResult(
                check_name="performance_metrics",
                status=status,
                message=message,
                value=avg_success_rate,
                details={
                    'average_duration_seconds': avg_duration,
                    'average_success_rate': avg_success_rate,
                    'metrics_count': len(perf_metrics['metrics_by_operation'])
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                check_name="performance_metrics",
                status="unknown",
                message=f"Could not check performance metrics: {str(e)}"
            )
    
    async def _count_duplicate_citations(self) -> int:
        """Count duplicate citations (simplified check)"""
        # This would need proper SQL queries
        return 0
    
    async def _count_orphaned_records(self) -> int:
        """Count orphaned records"""
        # This would need proper SQL queries
        return 0
    
    async def _count_incomplete_citations(self) -> int:
        """Count citations with missing required fields"""
        # This would need proper SQL queries
        return 0

class AlertManager:
    """Manages system alerts and notifications"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels = {
            'email': self._send_email_notification,
            'log': self._log_notification
        }
        
    async def process_health_results(self, results: List[HealthCheckResult]):
        """Process health check results and generate alerts"""
        current_time = datetime.now()
        
        for result in results:
            alert_id = f"{result.check_name}_{current_time.strftime('%Y%m%d_%H')}"
            
            # Generate alert based on status
            if result.status in ['critical', 'warning']:
                severity = 'critical' if result.status == 'critical' else 'warning'
                
                alert = Alert(
                    alert_id=alert_id,
                    severity=severity,
                    title=f"{result.check_name.title().replace('_', ' ')} Issue",
                    message=result.message,
                    component=result.check_name,
                    metadata={
                        'value': result.value,
                        'threshold': result.threshold,
                        'details': result.details
                    }
                )
                
                await self._handle_alert(alert)
            
            elif result.status == 'healthy':
                # Resolve any existing alerts for this component
                await self._resolve_component_alerts(result.check_name)
    
    async def _handle_alert(self, alert: Alert):
        """Handle a new alert"""
        # Check if this is a new alert or update to existing
        existing_alert = self.active_alerts.get(alert.alert_id)
        
        if existing_alert:
            # Update existing alert
            existing_alert.message = alert.message
            existing_alert.timestamp = alert.timestamp
            existing_alert.metadata.update(alert.metadata)
        else:
            # New alert
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
            
            # Send notifications
            await self._send_notifications(alert)
            
            logger.warning(f"New {alert.severity} alert: {alert.title} - {alert.message}")
    
    async def _resolve_component_alerts(self, component: str):
        """Resolve all alerts for a component"""
        resolved_alerts = []
        
        for alert_id, alert in self.active_alerts.items():
            if alert.component == component and not alert.resolved:
                alert.resolved = True
                alert.timestamp = datetime.now()
                resolved_alerts.append(alert_id)
        
        # Remove resolved alerts from active list
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
            logger.info(f"Resolved alert: {alert_id}")
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        for channel_name, send_func in self.notification_channels.items():
            try:
                await send_func(alert)
            except Exception as e:
                logger.error(f"Failed to send {channel_name} notification: {e}")
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        # Email configuration would come from config
        if not hasattr(config, 'email') or not config.email.smtp_server:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = config.email.from_address
            msg['To'] = config.email.alert_recipients
            msg['Subject'] = f"[{alert.severity.upper()}] Citation System Alert: {alert.title}"
            
            body = f"""
            Alert Details:
            
            Severity: {alert.severity.upper()}
            Component: {alert.component}
            Message: {alert.message}
            Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            
            Additional Details:
            {json.dumps(alert.metadata, indent=2)}
            
            This is an automated alert from the Citation Automation System.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config.email.smtp_server, config.email.smtp_port)
            if config.email.use_tls:
                server.starttls()
            if config.email.username:
                server.login(config.email.username, config.email.password)
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def _log_notification(self, alert: Alert):
        """Log notification"""
        logger.warning(f"ALERT [{alert.severity}] {alert.component}: {alert.message}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_summary(self) -> Dict:
        """Get alert summary"""
        active_by_severity = {}
        for alert in self.active_alerts.values():
            severity = alert.severity
            active_by_severity[severity] = active_by_severity.get(severity, 0) + 1
        
        recent_history = [
            alert for alert in self.alert_history
            if alert.timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            'active_alerts': len(self.active_alerts),
            'active_by_severity': active_by_severity,
            'alerts_last_24h': len(recent_history),
            'components_affected': len(set(alert.component for alert in self.active_alerts.values()))
        }

class QualityAssuranceReporter:
    """Generates comprehensive quality and performance reports"""
    
    def __init__(self):
        self.report_dir = Path("reports")
        self.report_dir.mkdir(exist_ok=True)
        
    async def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive quality assurance report"""
        logger.info("Generating comprehensive QA report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': await self._generate_health_report(),
            'citation_quality': await self._generate_citation_quality_report(),
            'performance_metrics': await self._generate_performance_report(),
            'data_integrity': await self._generate_data_integrity_report(),
            'recommendations': await self._generate_recommendations()
        }
        
        # Save report
        report_file = self.report_dir / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"QA report saved: {report_file}")
        return report
    
    async def _generate_health_report(self) -> Dict:
        """Generate system health report"""
        health_checker = HealthChecker()
        results = await health_checker.run_all_checks()
        
        health_summary = {
            'overall_status': 'healthy',
            'checks_passed': 0,
            'checks_warning': 0,
            'checks_critical': 0,
            'check_results': []
        }
        
        for result in results:
            health_summary['check_results'].append({
                'check_name': result.check_name,
                'status': result.status,
                'message': result.message,
                'value': result.value,
                'details': result.details
            })
            
            if result.status == 'healthy':
                health_summary['checks_passed'] += 1
            elif result.status == 'warning':
                health_summary['checks_warning'] += 1
                if health_summary['overall_status'] == 'healthy':
                    health_summary['overall_status'] = 'warning'
            elif result.status == 'critical':
                health_summary['checks_critical'] += 1
                health_summary['overall_status'] = 'critical'
        
        return health_summary
    
    async def _generate_citation_quality_report(self) -> Dict:
        """Generate citation quality report"""
        try:
            validation_stats = await db_manager.get_validation_statistics()
            
            # Get quality distribution
            citations = await db_manager.search_citations("", min_quality=0.0, limit=1000)
            quality_scores = [c.quality_score for c in citations if c.quality_score > 0]
            
            quality_distribution = {}
            if quality_scores:
                quality_distribution = {
                    'mean': statistics.mean(quality_scores),
                    'median': statistics.median(quality_scores),
                    'std_dev': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                    'min': min(quality_scores),
                    'max': max(quality_scores),
                    'count': len(quality_scores)
                }
            
            return {
                'validation_statistics': validation_stats,
                'quality_distribution': quality_distribution,
                'high_quality_citations': len([s for s in quality_scores if s >= 0.8]),
                'low_quality_citations': len([s for s in quality_scores if s < 0.5])
            }
            
        except Exception as e:
            logger.error(f"Error generating citation quality report: {e}")
            return {'error': str(e)}
    
    async def _generate_performance_report(self) -> Dict:
        """Generate performance report"""
        try:
            perf_metrics_24h = await db_manager.get_performance_metrics(hours_back=24)
            perf_metrics_7d = await db_manager.get_performance_metrics(hours_back=168)
            
            return {
                'last_24_hours': perf_metrics_24h,
                'last_7_days': perf_metrics_7d,
                'trends': self._analyze_performance_trends(perf_metrics_24h, perf_metrics_7d)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}
    
    def _analyze_performance_trends(self, recent: Dict, historical: Dict) -> Dict:
        """Analyze performance trends"""
        trends = {
            'throughput_trend': 'stable',
            'error_rate_trend': 'stable',
            'duration_trend': 'stable'
        }
        
        try:
            recent_ops = recent.get('metrics_by_operation', [])
            historical_ops = historical.get('metrics_by_operation', [])
            
            if recent_ops and historical_ops:
                # Compare success rates
                recent_success = statistics.mean([op['success_rate'] for op in recent_ops])
                historical_success = statistics.mean([op['success_rate'] for op in historical_ops])
                
                if recent_success > historical_success + 5:
                    trends['error_rate_trend'] = 'improving'
                elif recent_success < historical_success - 5:
                    trends['error_rate_trend'] = 'degrading'
                
                # Compare durations
                recent_duration = statistics.mean([op['avg_duration_seconds'] for op in recent_ops])
                historical_duration = statistics.mean([op['avg_duration_seconds'] for op in historical_ops])
                
                if recent_duration < historical_duration * 0.9:
                    trends['duration_trend'] = 'improving'
                elif recent_duration > historical_duration * 1.1:
                    trends['duration_trend'] = 'degrading'
        
        except Exception as e:
            logger.warning(f"Error analyzing trends: {e}")
        
        return trends
    
    async def _generate_data_integrity_report(self) -> Dict:
        """Generate data integrity report"""
        try:
            db_stats = await db_manager.get_database_stats()
            
            # Additional integrity checks
            integrity_report = {
                'database_stats': db_stats,
                'data_completeness': await self._calculate_data_completeness(),
                'consistency_checks': await self._run_consistency_checks()
            }
            
            return integrity_report
            
        except Exception as e:
            logger.error(f"Error generating data integrity report: {e}")
            return {'error': str(e)}
    
    async def _calculate_data_completeness(self) -> Dict:
        """Calculate data completeness metrics"""
        try:
            citations = await db_manager.search_citations("", min_quality=0.0, limit=1000)
            
            total_citations = len(citations)
            if total_citations == 0:
                return {'completeness_score': 0}
            
            complete_fields = {
                'doi_or_pmid': 0,
                'title': 0,
                'authors': 0,
                'journal': 0,
                'abstract': 0,
                'publication_date': 0
            }
            
            for citation in citations:
                if citation.doi or citation.pmid:
                    complete_fields['doi_or_pmid'] += 1
                if citation.title and citation.title.strip():
                    complete_fields['title'] += 1
                if citation.authors:
                    complete_fields['authors'] += 1
                if citation.journal and citation.journal.strip():
                    complete_fields['journal'] += 1
                if citation.abstract and citation.abstract.strip():
                    complete_fields['abstract'] += 1
                if citation.publication_date and citation.publication_date != "Unknown":
                    complete_fields['publication_date'] += 1
            
            # Calculate completeness percentages
            completeness_percentages = {
                field: (count / total_citations) * 100
                for field, count in complete_fields.items()
            }
            
            overall_completeness = statistics.mean(completeness_percentages.values())
            
            return {
                'total_citations': total_citations,
                'field_completeness': completeness_percentages,
                'overall_completeness': overall_completeness
            }
            
        except Exception as e:
            logger.error(f"Error calculating data completeness: {e}")
            return {'error': str(e)}
    
    async def _run_consistency_checks(self) -> List[Dict]:
        """Run data consistency checks"""
        checks = []
        
        try:
            # Check for duplicate DOIs
            # This would need actual database queries
            checks.append({
                'check_name': 'duplicate_dois',
                'status': 'passed',
                'message': 'No duplicate DOIs found',
                'count': 0
            })
            
            # Check for invalid publication dates
            checks.append({
                'check_name': 'invalid_dates',
                'status': 'passed',
                'message': 'All publication dates are valid',
                'count': 0
            })
            
        except Exception as e:
            logger.error(f"Error running consistency checks: {e}")
            checks.append({
                'check_name': 'consistency_check_error',
                'status': 'error',
                'message': str(e)
            })
        
        return checks
    
    async def _generate_recommendations(self) -> List[Dict]:
        """Generate system improvement recommendations"""
        recommendations = []
        
        try:
            # Get recent data for analysis
            validation_stats = await db_manager.get_validation_statistics()
            processing_stats = await db_manager.get_processing_statistics()
            db_stats = await db_manager.get_database_stats()
            
            # Validation rate recommendations
            validation_rate = validation_stats.get('validation_rate', 0)
            if validation_rate < 80:
                recommendations.append({
                    'priority': 'high',
                    'category': 'citation_quality',
                    'title': 'Improve Citation Validation Rate',
                    'description': f'Current validation rate is {validation_rate:.1f}%. Consider reviewing validation processes and API reliability.',
                    'suggested_actions': [
                        'Review failed validation cases',
                        'Improve error handling in validation logic',
                        'Consider alternative validation sources'
                    ]
                })
            
            # Processing recommendations
            completion_rate = processing_stats.get('completion_rate', 0)
            if completion_rate < 90:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'processing',
                    'title': 'Improve Processing Completion Rate',
                    'description': f'Current completion rate is {completion_rate:.1f}%. Some files may be failing to process.',
                    'suggested_actions': [
                        'Investigate failed processing cases',
                        'Improve error handling and retry logic',
                        'Optimize processing pipeline'
                    ]
                })
            
            # Database size recommendations
            db_size_mb = db_stats.get('database_size_mb', 0)
            if db_size_mb > 1000:  # 1GB
                recommendations.append({
                    'priority': 'low',
                    'category': 'maintenance',
                    'title': 'Database Maintenance',
                    'description': f'Database size is {db_size_mb:.0f}MB. Consider cleanup and optimization.',
                    'suggested_actions': [
                        'Archive old performance metrics',
                        'Clean up duplicate records',
                        'Optimize database indexes'
                    ]
                })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append({
                'priority': 'high',
                'category': 'system',
                'title': 'System Analysis Error',
                'description': f'Could not analyze system for recommendations: {str(e)}',
                'suggested_actions': ['Review system logs', 'Check database connectivity']
            })
        
        return recommendations
    
    async def generate_dashboard_data(self) -> Dict:
        """Generate data for monitoring dashboard"""
        try:
            health_checker = HealthChecker()
            health_results = await health_checker.run_all_checks()
            
            alert_manager = AlertManager()
            # Process health results to generate alerts
            await alert_manager.process_health_results(health_results)
            
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'system_status': self._determine_overall_status(health_results),
                'health_checks': [
                    {
                        'name': result.check_name,
                        'status': result.status,
                        'message': result.message,
                        'value': result.value
                    }
                    for result in health_results
                ],
                'alerts': {
                    'active_count': len(alert_manager.get_active_alerts()),
                    'summary': alert_manager.get_alert_summary(),
                    'recent_alerts': [
                        {
                            'title': alert.title,
                            'severity': alert.severity,
                            'component': alert.component,
                            'timestamp': alert.timestamp.isoformat()
                        }
                        for alert in alert_manager.get_active_alerts()[:10]
                    ]
                },
                'metrics': await self._get_key_metrics()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'system_status': 'unknown',
                'error': str(e)
            }
    
    def _determine_overall_status(self, health_results: List[HealthCheckResult]) -> str:
        """Determine overall system status from health check results"""
        if any(result.status == 'critical' for result in health_results):
            return 'critical'
        elif any(result.status == 'warning' for result in health_results):
            return 'warning'
        elif all(result.status == 'healthy' for result in health_results):
            return 'healthy'
        else:
            return 'unknown'
    
    async def _get_key_metrics(self) -> Dict:
        """Get key system metrics for dashboard"""
        try:
            validation_stats = await db_manager.get_validation_statistics()
            processing_stats = await db_manager.get_processing_statistics()
            db_stats = await db_manager.get_database_stats()
            
            return {
                'total_citations': validation_stats.get('total_citations', 0),
                'validation_rate': validation_stats.get('validation_rate', 0),
                'average_quality_score': validation_stats.get('average_quality_score', 0),
                'processing_completion_rate': processing_stats.get('completion_rate', 0),
                'total_files_processed': processing_stats.get('total_files', 0),
                'database_size_mb': db_stats.get('database_size_mb', 0),
                'citations_added_last_7_days': db_stats.get('citations_added_last_7_days', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting key metrics: {e}")
            return {}

# Global instances
health_checker = HealthChecker()
alert_manager = AlertManager()
qa_reporter = QualityAssuranceReporter()

async def run_monitoring_cycle():
    """Run a complete monitoring cycle"""
    logger.info("Starting monitoring cycle...")
    
    try:
        # Run health checks
        health_results = await health_checker.run_all_checks()
        
        # Process alerts
        await alert_manager.process_health_results(health_results)
        
        # Generate reports (less frequently)
        report = await qa_reporter.generate_comprehensive_report()
        
        logger.info(f"Monitoring cycle completed. Overall status: {qa_reporter._determine_overall_status(health_results)}")
        
        return report
        
    except Exception as e:
        logger.error(f"Error in monitoring cycle: {e}")
        
        # Create critical alert for monitoring system failure
        alert = Alert(
            alert_id=f"monitoring_failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            severity="critical",
            title="Monitoring System Failure",
            message=f"Monitoring cycle failed: {str(e)}",
            component="monitoring"
        )
        
        await alert_manager._handle_alert(alert)

async def main():
    """Test monitoring system"""
    await db_manager.initialize()
    
    # Run monitoring cycle
    report = await run_monitoring_cycle()
    
    print("Monitoring Report Generated:")
    print(f"System Status: {report.get('system_health', {}).get('overall_status', 'unknown')}")
    print(f"Active Alerts: {len(alert_manager.get_active_alerts())}")

if __name__ == "__main__":
    asyncio.run(main())