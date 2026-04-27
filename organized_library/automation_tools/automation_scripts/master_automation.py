#!/usr/bin/env python3
"""
Master Automation Script for Fitness Library Enhancement
Perfect quality-maintained batch processing with comprehensive error handling
Maintains all SOP requirements while maximizing efficiency
"""

import os
import json
import time
import logging
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import sys

# Configure logging with dual output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('master_automation.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SectionConfig:
    """Configuration for each section to be processed"""
    section: str
    start_num: int
    end_num: int
    priority: str  # 'high', 'medium', 'low'
    estimated_files: int
    description: str

@dataclass
class ProcessingStatus:
    """Track processing status for each section"""
    section: str
    status: str  # 'pending', 'processing', 'completed', 'failed', 'paused'
    processed: int
    failed: int
    skipped: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_message: Optional[str]

class MasterAutomation:
    """Master automation controller with quality preservation"""
    
    def __init__(self, api_key: str, base_dir: str, rate_limit: float = 3.0):
        self.api_key = api_key
        self.base_dir = Path(base_dir)
        self.rate_limit = rate_limit
        self.processed_notes_dir = self.base_dir / "processed_notes"
        self.processed_notes_dir.mkdir(exist_ok=True)
        
        # Processing status tracking
        self.section_status: Dict[str, ProcessingStatus] = {}
        self.total_processed = 0
        self.total_failed = 0
        self.total_skipped = 0
        
        # Quality control settings
        self.max_retries = 2
        self.min_success_rate = 85.0  # Minimum 85% success rate required
        self.quality_check_enabled = True
        
        # Load section configurations
        self.section_configs = self._load_section_configs()
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self.shutdown_requested = False
        
    def _load_section_configs(self) -> List[SectionConfig]:
        """Load predefined section configurations based on project status"""
        return [
            # HIGH PRIORITY - Incomplete sections
            SectionConfig("B", 39, 78, "high", 40, "Resistance Training (remaining)"),
            SectionConfig("F", 5, 34, "high", 30, "Performance Testing"),
            SectionConfig("G", 4, 16, "high", 13, "Special Populations"),
            
            # MEDIUM PRIORITY - New categories
            SectionConfig("J", 4, 10, "medium", 7, "Technology in Fitness"),
            SectionConfig("K", 6, 15, "medium", 10, "Elite Performance"),
            SectionConfig("M", 4, 8, "medium", 5, "Recovery Strategies"),
            SectionConfig("N", 4, 8, "medium", 5, "Long-Term Development"),
            SectionConfig("O", 4, 8, "medium", 5, "Integrated Approaches"),
            SectionConfig("P", 5, 10, "medium", 6, "Ethical Considerations"),
            
            # LOW PRIORITY - Additional categories
            SectionConfig("IX", 8, 15, "low", 8, "Health Conditions & Rehabilitation"),
            SectionConfig("X", 13, 20, "low", 8, "Additional Sports-Specific Training"),
        ]
    
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("Shutdown signal received. Finishing current operations...")
        self.shutdown_requested = True
    
    def analyze_existing_files(self) -> Dict[str, int]:
        """Analyze what files already exist to avoid reprocessing"""
        logger.info("Analyzing existing processed files...")
        
        existing_files = {}
        for config in self.section_configs:
            section = config.section
            existing_count = 0
            
            for num in range(config.start_num, config.end_num + 1):
                # Check multiple possible filename patterns
                patterns = [
                    f"rewritten_{section}{num}.*.md",
                    f"rewritten_{section}{num:02d}.*.md",
                    f"{section}{num}.*.md",
                    f"{section}{num:02d}.*.md"
                ]
                
                found = False
                for pattern in patterns:
                    if list(self.processed_notes_dir.glob(pattern)):
                        found = True
                        break
                
                if found:
                    existing_count += 1
            
            existing_files[section] = existing_count
            logger.info(f"Section {section}: {existing_count}/{config.estimated_files} files already processed")
        
        return existing_files
    
    def validate_prerequisites(self) -> bool:
        """Validate all prerequisites before starting"""
        logger.info("Validating prerequisites...")
        
        # Check API key
        if not self.api_key or len(self.api_key) < 50:
            logger.error("Invalid API key provided")
            return False
        
        # Check directories
        if not self.base_dir.exists():
            logger.error(f"Base directory {self.base_dir} does not exist")
            return False
        
        # Check if process_fitness_library.py exists
        script_path = self.base_dir / "process_fitness_library.py"
        if not script_path.exists():
            logger.error(f"Required script {script_path} not found")
            return False
        
        # Test API connectivity
        try:
            test_result = self._test_api_connection()
            if not test_result:
                logger.error("API connection test failed")
                return False
        except Exception as e:
            logger.error(f"API test error: {e}")
            return False
        
        logger.info("✅ All prerequisites validated")
        return True
    
    def _test_api_connection(self) -> bool:
        """Test API connection with a minimal call"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Minimal test call
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Test"}]
            )
            return bool(response.content)
        except Exception as e:
            logger.error(f"API test failed: {e}")
            return False
    
    def process_section_with_quality_control(self, config: SectionConfig) -> ProcessingStatus:
        """Process a section with comprehensive quality control"""
        section = config.section
        logger.info(f"🚀 Starting section {section} ({config.description})")
        
        # Initialize status tracking
        status = ProcessingStatus(
            section=section,
            status="processing",
            processed=0,
            failed=0,
            skipped=0,
            start_time=datetime.now(),
            end_time=None,
            error_message=None
        )
        self.section_status[section] = status
        
        try:
            # Build command
            cmd = [
                "python3", "process_fitness_library.py",
                "--section", section,
                "--input-dir", str(self.base_dir),
                "--output-dir", str(self.processed_notes_dir),
                "--start-num", str(config.start_num),
                "--end-num", str(config.end_num),
                "--api-key", self.api_key,
                "--rate-limit", str(self.rate_limit)
            ]
            
            # Execute with real-time monitoring
            result = self._execute_with_monitoring(cmd, section)
            
            if result and result.returncode == 0:
                # Parse results and validate quality
                report_file = self.processed_notes_dir / f"section_{section}_report.md"
                if report_file.exists():
                    stats = self._parse_report_stats(report_file)
                    status.processed = stats.get('processed', 0)
                    status.failed = stats.get('failed', 0)
                    status.skipped = stats.get('skipped', 0)
                    
                    # Quality validation
                    success_rate = self._calculate_success_rate(status)
                    if success_rate < self.min_success_rate:
                        logger.warning(f"Section {section} success rate ({success_rate:.1f}%) below threshold")
                        status.status = "completed_with_warnings"
                    else:
                        status.status = "completed"
                        logger.info(f"✅ Section {section} completed successfully (success rate: {success_rate:.1f}%)")
                else:
                    logger.warning(f"No report file found for section {section}")
                    status.status = "completed_no_report"
            else:
                status.status = "failed"
                status.error_message = f"Process exited with code {result.returncode if result else 'unknown'}"
                logger.error(f"❌ Section {section} failed: {status.error_message}")
        
        except Exception as e:
            status.status = "failed"
            status.error_message = str(e)
            logger.error(f"❌ Section {section} failed with exception: {e}")
        
        finally:
            status.end_time = datetime.now()
            self._update_global_stats(status)
        
        return status
    
    def _execute_with_monitoring(self, cmd: List[str], section: str) -> Optional[subprocess.CompletedProcess]:
        """Execute command with real-time monitoring and graceful shutdown"""
        logger.info(f"Executing: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.base_dir,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor output in real-time
            while True:
                if self.shutdown_requested:
                    logger.info(f"Gracefully terminating section {section} processing...")
                    process.terminate()
                    process.wait(timeout=30)
                    return None
                
                output = process.stdout.readline()
                if output:
                    # Log important lines
                    if any(keyword in output.lower() for keyword in ['processing:', 'error', 'failed', 'success']):
                        logger.info(f"[{section}] {output.strip()}")
                elif process.poll() is not None:
                    break
                
                time.sleep(0.1)
            
            # Wait for completion
            return_code = process.wait()
            return subprocess.CompletedProcess(cmd, return_code)
            
        except Exception as e:
            logger.error(f"Error executing command for section {section}: {e}")
            return None
    
    def _parse_report_stats(self, report_file: Path) -> Dict[str, int]:
        """Parse statistics from processing report"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            stats = {}
            import re
            
            # Extract stats using regex
            processed_match = re.search(r'\*\*Files Processed:\*\*\s*(\d+)', content)
            failed_match = re.search(r'\*\*Files Failed:\*\*\s*(\d+)', content)
            skipped_match = re.search(r'\*\*Files Skipped:\*\*\s*(\d+)', content)
            
            if processed_match:
                stats['processed'] = int(processed_match.group(1))
            if failed_match:
                stats['failed'] = int(failed_match.group(1))
            if skipped_match:
                stats['skipped'] = int(skipped_match.group(1))
            
            return stats
            
        except Exception as e:
            logger.error(f"Error parsing report {report_file}: {e}")
            return {}
    
    def _calculate_success_rate(self, status: ProcessingStatus) -> float:
        """Calculate success rate for a processing status"""
        total_attempted = status.processed + status.failed
        if total_attempted == 0:
            return 0.0
        return (status.processed / total_attempted) * 100
    
    def _update_global_stats(self, status: ProcessingStatus):
        """Update global processing statistics"""
        self.total_processed += status.processed
        self.total_failed += status.failed
        self.total_skipped += status.skipped
    
    def run_sequential_processing(self, priority_filter: Optional[str] = None) -> Dict[str, ProcessingStatus]:
        """Run sequential processing with quality control"""
        logger.info("🎯 Starting Master Automation - Sequential Processing")
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            logger.error("❌ Prerequisites validation failed. Aborting.")
            return {}
        
        # Analyze existing files
        existing_files = self.analyze_existing_files()
        
        # Filter sections by priority if specified
        sections_to_process = self.section_configs
        if priority_filter:
            sections_to_process = [c for c in self.section_configs if c.priority == priority_filter]
            logger.info(f"Processing only {priority_filter} priority sections")
        
        # Process sections sequentially
        results = {}
        total_sections = len(sections_to_process)
        
        for i, config in enumerate(sections_to_process, 1):
            if self.shutdown_requested:
                logger.info("Shutdown requested. Stopping processing.")
                break
            
            logger.info(f"📋 Processing section {i}/{total_sections}: {config.section}")
            
            # Skip if already completed (optional check)
            existing_count = existing_files.get(config.section, 0)
            if existing_count >= config.estimated_files * 0.9:  # 90% threshold
                logger.info(f"⏭️ Section {config.section} appears mostly complete ({existing_count}/{config.estimated_files})")
                continue
            
            # Process the section
            status = self.process_section_with_quality_control(config)
            results[config.section] = status
            
            # Quality gate - stop if too many failures
            if status.status == "failed":
                logger.error(f"Section {config.section} failed. Continuing with next section...")
                continue
            
            # Brief pause between sections
            if i < total_sections:
                logger.info(f"⏸️ Brief pause before next section...")
                time.sleep(5)
        
        return results
    
    def run_parallel_processing(self, max_workers: int = 2) -> Dict[str, ProcessingStatus]:
        """Run parallel processing for independent sections"""
        logger.info(f"🚀 Starting Master Automation - Parallel Processing (max_workers={max_workers})")
        
        # Validate prerequisites
        if not self.validate_prerequisites():
            logger.error("❌ Prerequisites validation failed. Aborting.")
            return {}
        
        results = {}
        
        # Group sections by priority for controlled execution
        high_priority = [c for c in self.section_configs if c.priority == "high"]
        medium_priority = [c for c in self.section_configs if c.priority == "medium"]
        low_priority = [c for c in self.section_configs if c.priority == "low"]
        
        # Process each priority group
        for priority_group, group_name in [(high_priority, "HIGH"), (medium_priority, "MEDIUM"), (low_priority, "LOW")]:
            if self.shutdown_requested:
                break
                
            if not priority_group:
                continue
                
            logger.info(f"🎯 Processing {group_name} priority sections")
            
            with ThreadPoolExecutor(max_workers=min(max_workers, len(priority_group))) as executor:
                # Submit all sections in this priority group
                future_to_config = {
                    executor.submit(self.process_section_with_quality_control, config): config
                    for config in priority_group
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_config):
                    if self.shutdown_requested:
                        logger.info("Shutdown requested. Cancelling remaining tasks...")
                        executor.shutdown(wait=False)
                        break
                        
                    config = future_to_config[future]
                    try:
                        status = future.result()
                        results[config.section] = status
                        logger.info(f"✅ Section {config.section} completed in parallel")
                    except Exception as e:
                        logger.error(f"❌ Section {config.section} failed in parallel: {e}")
                        results[config.section] = ProcessingStatus(
                            section=config.section,
                            status="failed",
                            processed=0,
                            failed=0,
                            skipped=0,
                            start_time=datetime.now(),
                            end_time=datetime.now(),
                            error_message=str(e)
                        )
            
            # Pause between priority groups
            if priority_group != low_priority:
                logger.info("⏸️ Pause between priority groups...")
                time.sleep(10)
        
        return results
    
    def generate_master_report(self, results: Dict[str, ProcessingStatus]):
        """Generate comprehensive master processing report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate overall statistics
        total_sections = len(results)
        completed_sections = len([s for s in results.values() if s.status in ["completed", "completed_with_warnings"]])
        failed_sections = len([s for s in results.values() if s.status == "failed"])
        
        overall_success_rate = (self.total_processed / (self.total_processed + self.total_failed) * 100) if (self.total_processed + self.total_failed) > 0 else 0
        
        report = f"""# Master Automation Report
Generated: {timestamp}

## Executive Summary
- **Total Sections Processed:** {total_sections}
- **Sections Completed:** {completed_sections}
- **Sections Failed:** {failed_sections}
- **Overall Success Rate:** {overall_success_rate:.1f}%

## Global Statistics
- **Files Processed:** {self.total_processed}
- **Files Failed:** {self.total_failed}
- **Files Skipped:** {self.total_skipped}
- **Total Files Handled:** {self.total_processed + self.total_failed + self.total_skipped}

## Section Details
"""
        
        for section, status in sorted(results.items()):
            duration = "N/A"
            if status.start_time and status.end_time:
                duration = str(status.end_time - status.start_time).split('.')[0]
            
            success_rate = self._calculate_success_rate(status)
            status_emoji = {
                "completed": "✅",
                "completed_with_warnings": "⚠️",
                "failed": "❌",
                "processing": "🔄"
            }.get(status.status, "❓")
            
            report += f"""
### {status_emoji} Section {section}
- **Status:** {status.status}
- **Duration:** {duration}
- **Files Processed:** {status.processed}
- **Files Failed:** {status.failed}
- **Files Skipped:** {status.skipped}
- **Success Rate:** {success_rate:.1f}%
"""
            if status.error_message:
                report += f"- **Error:** {status.error_message}\n"
        
        # Quality assessment
        report += f"""
## Quality Assessment
- **Minimum Success Rate Target:** {self.min_success_rate}%
- **Actual Overall Success Rate:** {overall_success_rate:.1f}%
- **Quality Standard:** {"✅ MET" if overall_success_rate >= self.min_success_rate else "❌ NOT MET"}

## Next Steps
"""
        
        if failed_sections > 0:
            report += "- Review and retry failed sections\n"
        if overall_success_rate < self.min_success_rate:
            report += "- Investigate quality issues and improve processing\n"
        if completed_sections == total_sections and overall_success_rate >= self.min_success_rate:
            report += "- ✅ All sections completed successfully!\n"
        
        # Save report
        report_file = self.processed_notes_dir / "master_automation_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📊 Master report saved to {report_file}")
        
        # Also save machine-readable JSON
        json_data = {
            "timestamp": timestamp,
            "global_stats": {
                "total_processed": self.total_processed,
                "total_failed": self.total_failed,
                "total_skipped": self.total_skipped,
                "overall_success_rate": overall_success_rate
            },
            "sections": {k: asdict(v) for k, v in results.items()}
        }
        
        json_file = self.processed_notes_dir / "master_automation_results.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        return report_file

def main():
    """Main function with comprehensive CLI"""
    parser = argparse.ArgumentParser(description="Master Automation for Fitness Library Processing")
    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument("--base-dir", default=".", help="Base directory containing fitness library files")
    parser.add_argument("--mode", choices=["sequential", "parallel"], default="sequential", 
                       help="Processing mode")
    parser.add_argument("--priority", choices=["high", "medium", "low"], 
                       help="Process only specific priority sections")
    parser.add_argument("--max-workers", type=int, default=2, 
                       help="Maximum parallel workers (for parallel mode)")
    parser.add_argument("--rate-limit", type=float, default=3.0, 
                       help="Delay between API calls (seconds)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Analyze and report without processing")
    
    args = parser.parse_args()
    
    # Initialize automation system
    automation = MasterAutomation(
        api_key=args.api_key,
        base_dir=args.base_dir,
        rate_limit=args.rate_limit
    )
    
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - Analysis only")
        existing = automation.analyze_existing_files()
        for section, count in existing.items():
            config = next((c for c in automation.section_configs if c.section == section), None)
            if config:
                logger.info(f"Section {section}: {count}/{config.estimated_files} files ({count/config.estimated_files*100:.1f}%)")
        return
    
    # Run processing
    start_time = datetime.now()
    logger.info(f"🚀 Master Automation Started at {start_time}")
    
    try:
        if args.mode == "parallel":
            results = automation.run_parallel_processing(args.max_workers)
        else:
            results = automation.run_sequential_processing(args.priority)
        
        # Generate final report
        report_file = automation.generate_master_report(results)
        
        end_time = datetime.now()
        total_duration = end_time - start_time
        
        logger.info(f"""
🏁 Master Automation Completed!
⏱️ Total Duration: {total_duration}
📊 Report: {report_file}
✅ Processed: {automation.total_processed}
❌ Failed: {automation.total_failed}
⏭️ Skipped: {automation.total_skipped}
        """)
        
    except KeyboardInterrupt:
        logger.info("🛑 Processing interrupted by user")
    except Exception as e:
        logger.error(f"💥 Master automation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()