#!/usr/bin/env python3
"""
Advanced Automation Pipeline
Orchestrates the entire citation automation process with intelligent scheduling,
batch processing, error recovery, and performance optimization
"""

import asyncio
import aiohttp
import aiofiles
import hashlib
import psutil
import time
import json
from typing import Dict, List, Optional, Tuple, Set, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import threading
import signal
import sys
import traceback

from research_discovery import ResearchDiscoveryEngine, SearchQuery, ResearchPaper
from quality_scorer import QualityScorer
from content_enhancer import ContentEnhancementEngine, ContentEnhancement
from database import DatabaseManager, db_manager
from config import config

logger = logging.getLogger(__name__)

@dataclass
class ProcessingTask:
    """Represents a processing task"""
    task_id: str
    task_type: str  # validation, enhancement, discovery, quality_scoring
    file_path: Optional[Path] = None
    priority: int = 0  # Higher number = higher priority
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

@dataclass
class ProcessingResult:
    """Results of a processing operation"""
    task_id: str
    success: bool
    duration: float
    records_processed: int
    api_calls_made: int
    memory_used: float
    error_message: Optional[str] = None
    output_data: Dict = field(default_factory=dict)

@dataclass
class SystemHealth:
    """System health metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_tasks: int
    queue_size: int
    api_rate_limits: Dict[str, float]
    error_rate: float
    throughput: float  # tasks per minute

class TaskQueue:
    """Intelligent task queue with priority and dependency management"""
    
    def __init__(self):
        self.tasks: Dict[str, ProcessingTask] = {}
        self.pending_tasks = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, ProcessingTask] = {}
        self.completed_tasks: Dict[str, ProcessingResult] = {}
        self.failed_tasks: Dict[str, ProcessingTask] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self._task_lock = asyncio.Lock()
    
    async def add_task(self, task: ProcessingTask):
        """Add task to queue"""
        async with self._task_lock:
            self.tasks[task.task_id] = task
            
            # Check if dependencies are met
            if self._dependencies_met(task):
                await self.pending_tasks.put((-task.priority, task.task_id))
            else:
                # Add to dependency graph
                for dep_id in task.dependencies:
                    if dep_id not in self.dependency_graph:
                        self.dependency_graph[dep_id] = set()
                    self.dependency_graph[dep_id].add(task.task_id)
    
    def _dependencies_met(self, task: ProcessingTask) -> bool:
        """Check if all dependencies are completed"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        return True
    
    async def get_next_task(self) -> Optional[ProcessingTask]:
        """Get next task to process"""
        try:
            _, task_id = await asyncio.wait_for(self.pending_tasks.get(), timeout=1.0)
            async with self._task_lock:
                task = self.tasks.get(task_id)
                if task:
                    self.active_tasks[task_id] = task
                    task.started_at = datetime.now()
                    return task
        except asyncio.TimeoutError:
            pass
        return None
    
    async def complete_task(self, result: ProcessingResult):
        """Mark task as completed and resolve dependencies"""
        async with self._task_lock:
            task_id = result.task_id
            
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            if result.success:
                self.completed_tasks[task_id] = result
                
                # Resolve dependencies
                if task_id in self.dependency_graph:
                    for dependent_id in self.dependency_graph[task_id]:
                        dependent_task = self.tasks.get(dependent_id)
                        if dependent_task and self._dependencies_met(dependent_task):
                            await self.pending_tasks.put((-dependent_task.priority, dependent_id))
                    
                    del self.dependency_graph[task_id]
            else:
                # Handle failure
                task = self.tasks[task_id]
                task.retry_count += 1
                task.error_message = result.error_message
                
                if task.retry_count < task.max_retries:
                    # Retry with exponential backoff
                    delay = min(60 * (2 ** task.retry_count), 300)  # Max 5 minutes
                    await asyncio.sleep(delay)
                    await self.pending_tasks.put((-task.priority, task_id))
                else:
                    self.failed_tasks[task_id] = task
    
    def get_status(self) -> Dict:
        """Get queue status"""
        return {
            'pending': self.pending_tasks.qsize(),
            'active': len(self.active_tasks),
            'completed': len(self.completed_tasks),
            'failed': len(self.failed_tasks),
            'total': len(self.tasks)
        }

class ResourceMonitor:
    """Monitor system resources and API usage"""
    
    def __init__(self):
        self.api_call_history: Dict[str, List[float]] = {}
        self.error_history: List[Tuple[datetime, str]] = []
        self.performance_history: List[Tuple[datetime, float]] = []
        self._monitoring = False
        
    def start_monitoring(self):
        """Start resource monitoring"""
        self._monitoring = True
        asyncio.create_task(self._monitor_loop())
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                await self._collect_metrics()
                await asyncio.sleep(10)  # Collect metrics every 10 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    async def _collect_metrics(self):
        """Collect system metrics"""
        # Clean up old history (keep last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        # Clean API call history
        for api_name in list(self.api_call_history.keys()):
            self.api_call_history[api_name] = [
                timestamp for timestamp in self.api_call_history[api_name]
                if datetime.fromtimestamp(timestamp) > cutoff_time
            ]
        
        # Clean error history
        self.error_history = [
            (timestamp, error) for timestamp, error in self.error_history
            if timestamp > cutoff_time
        ]
        
        # Clean performance history
        self.performance_history = [
            (timestamp, value) for timestamp, value in self.performance_history
            if timestamp > cutoff_time
        ]
    
    def record_api_call(self, api_name: str):
        """Record an API call"""
        if api_name not in self.api_call_history:
            self.api_call_history[api_name] = []
        
        self.api_call_history[api_name].append(time.time())
    
    def record_error(self, error_message: str):
        """Record an error"""
        self.error_history.append((datetime.now(), error_message))
    
    def record_performance(self, tasks_per_minute: float):
        """Record performance metric"""
        self.performance_history.append((datetime.now(), tasks_per_minute))
    
    def get_api_rate(self, api_name: str, window_minutes: int = 60) -> float:
        """Get API call rate for the given window"""
        if api_name not in self.api_call_history:
            return 0.0
        
        cutoff_time = time.time() - (window_minutes * 60)
        recent_calls = [
            timestamp for timestamp in self.api_call_history[api_name]
            if timestamp > cutoff_time
        ]
        
        return len(recent_calls) / window_minutes
    
    def get_error_rate(self, window_minutes: int = 60) -> float:
        """Get error rate for the given window"""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_errors = [
            error for timestamp, error in self.error_history
            if timestamp > cutoff_time
        ]
        
        return len(recent_errors) / window_minutes
    
    def get_system_health(self, queue_size: int, active_tasks: int) -> SystemHealth:
        """Get current system health"""
        # System resources
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # API rate limits
        api_rates = {}
        for api_name in ['pubmed', 'crossref', 'semantic_scholar']:
            api_rates[api_name] = self.get_api_rate(api_name)
        
        # Performance metrics
        recent_performance = [
            value for timestamp, value in self.performance_history
            if timestamp > datetime.now() - timedelta(minutes=10)
        ]
        
        throughput = sum(recent_performance) / max(len(recent_performance), 1)
        
        return SystemHealth(
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_tasks=active_tasks,
            queue_size=queue_size,
            api_rate_limits=api_rates,
            error_rate=self.get_error_rate(10),  # Last 10 minutes
            throughput=throughput
        )
    
    def should_throttle(self) -> bool:
        """Check if processing should be throttled"""
        health = self.get_system_health(0, 0)  # Dummy values for resource check
        
        # Throttle if system resources are high
        if health.cpu_usage > 80 or health.memory_usage > 80:
            return True
        
        # Throttle if error rate is high
        if health.error_rate > 10:  # More than 10 errors per minute
            return True
        
        # Check API rate limits
        api_limits = {
            'pubmed': 10,  # requests per minute
            'crossref': 50,
            'semantic_scholar': 100
        }
        
        for api_name, limit in api_limits.items():
            if self.get_api_rate(api_name) > limit * 0.8:  # 80% of limit
                return True
        
        return False

class IntelligentScheduler:
    """Intelligent task scheduler with load balancing and optimization"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or config.processing.max_workers
        self.task_queue = TaskQueue()
        self.resource_monitor = ResourceMonitor()
        self.worker_pool: List[asyncio.Task] = []
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        
    async def start(self):
        """Start the scheduler"""
        logger.info(f"Starting intelligent scheduler with {self.max_workers} workers")
        
        self.is_running = True
        self.resource_monitor.start_monitoring()
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.worker_pool.append(worker)
        
        # Start scheduler management tasks
        asyncio.create_task(self._scheduler_loop())
        asyncio.create_task(self._health_check_loop())
    
    async def stop(self):
        """Stop the scheduler gracefully"""
        logger.info("Stopping scheduler...")
        
        self.is_running = False
        self._shutdown_event.set()
        self.resource_monitor.stop_monitoring()
        
        # Wait for workers to complete current tasks
        if self.worker_pool:
            await asyncio.gather(*self.worker_pool, return_exceptions=True)
        
        logger.info("Scheduler stopped")
    
    async def _worker_loop(self, worker_id: str):
        """Main worker loop"""
        logger.debug(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Check if we should throttle
                if self.resource_monitor.should_throttle():
                    await asyncio.sleep(10)
                    continue
                
                # Get next task
                task = await self.task_queue.get_next_task()
                if not task:
                    continue
                
                logger.info(f"Worker {worker_id} processing task {task.task_id}")
                
                # Process task
                result = await self._process_task(task, worker_id)
                
                # Record result
                await self.task_queue.complete_task(result)
                
                # Record performance
                if result.duration > 0:
                    tasks_per_minute = 60 / result.duration
                    self.resource_monitor.record_performance(tasks_per_minute)
                
                # Record metrics in database
                await db_manager.record_performance_metrics(
                    operation_type=task.task_type,
                    duration=result.duration,
                    records_processed=result.records_processed,
                    success_count=1 if result.success else 0,
                    error_count=0 if result.success else 1,
                    api_calls=result.api_calls_made,
                    memory_usage=result.memory_used
                )
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self.resource_monitor.record_error(str(e))
                await asyncio.sleep(5)
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def _process_task(self, task: ProcessingTask, worker_id: str) -> ProcessingResult:
        """Process a single task"""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
        
        result = ProcessingResult(
            task_id=task.task_id,
            success=False,
            duration=0.0,
            records_processed=0,
            api_calls_made=0,
            memory_used=0.0
        )
        
        try:
            if task.task_type == "file_enhancement":
                result = await self._process_file_enhancement(task)
            elif task.task_type == "citation_validation":
                result = await self._process_citation_validation(task)
            elif task.task_type == "research_discovery":
                result = await self._process_research_discovery(task)
            elif task.task_type == "quality_scoring":
                result = await self._process_quality_scoring(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            result.success = True
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            result.error_message = str(e)
            self.resource_monitor.record_error(str(e))
        
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
            
            result.duration = end_time - start_time
            result.memory_used = max(0, end_memory - start_memory)
        
        return result
    
    async def _process_file_enhancement(self, task: ProcessingTask) -> ProcessingResult:
        """Process file enhancement task"""
        result = ProcessingResult(task_id=task.task_id, success=False, duration=0, records_processed=0, api_calls_made=0, memory_used=0)
        
        if not task.file_path or not task.file_path.exists():
            raise ValueError(f"File not found: {task.file_path}")
        
        # Read file content
        async with aiofiles.open(task.file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        # Calculate file hash
        file_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Store file processing record
        file_id = await db_manager.store_file_processing_record(
            str(task.file_path), file_hash, "processing"
        )
        
        try:
            # Enhance content
            enhancer = ContentEnhancementEngine()
            enhancement = await enhancer.enhance_content(content, task.file_path)
            
            # Count API calls made (estimated)
            api_calls = len(enhancement.citation_suggestions) * 3  # Estimate 3 API calls per suggestion
            self.resource_monitor.record_api_call("content_enhancement")
            
            # Save enhanced content
            output_path = task.file_path.parent / f"enhanced_{task.file_path.name}"
            async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                await f.write(enhancement.enhanced_content)
            
            # Update database
            await db_manager.update_file_processing_status(
                file_id, "completed",
                citation_count=len(enhancement.citation_suggestions),
                quality_score=enhancement.overall_improvement_score
            )
            
            result.records_processed = 1
            result.api_calls_made = api_calls
            result.output_data = {
                'output_file': str(output_path),
                'improvement_score': enhancement.overall_improvement_score,
                'citations_added': len(enhancement.citation_suggestions)
            }
            
        except Exception as e:
            await db_manager.update_file_processing_status(
                file_id, "error", error_message=str(e)
            )
            raise
        
        return result
    
    async def _process_citation_validation(self, task: ProcessingTask) -> ProcessingResult:
        """Process citation validation task"""
        result = ProcessingResult(task_id=task.task_id, success=False, duration=0, records_processed=0, api_calls_made=0, memory_used=0)
        
        # Get citations to validate
        citations = await db_manager.search_citations(
            query=task.metadata.get('search_query', ''),
            min_quality=0.0,
            limit=task.metadata.get('batch_size', 100)
        )
        
        validated_count = 0
        for citation in citations:
            try:
                # Validate DOI/PMID
                if citation.doi:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(f"https://doi.org/{citation.doi}", timeout=10) as response:
                            status = "valid" if response.status == 200 else "invalid"
                elif citation.pmid:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(f"https://pubmed.ncbi.nlm.nih.gov/{citation.pmid}/", timeout=10) as response:
                            status = "valid" if response.status == 200 else "invalid"
                else:
                    status = "no_link"
                
                # Update validation status (would need citation ID)
                validated_count += 1
                self.resource_monitor.record_api_call("citation_validation")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.warning(f"Failed to validate citation {citation.title[:50]}: {e}")
        
        result.records_processed = validated_count
        result.api_calls_made = validated_count
        
        return result
    
    async def _process_research_discovery(self, task: ProcessingTask) -> ProcessingResult:
        """Process research discovery task"""
        result = ProcessingResult(task_id=task.task_id, success=False, duration=0, records_processed=0, api_calls_made=0, memory_used=0)
        
        # Create search query from metadata
        query_terms = task.metadata.get('query_terms', [])
        if not query_terms:
            raise ValueError("No query terms provided for research discovery")
        
        search_query = SearchQuery(
            terms=query_terms,
            max_results=task.metadata.get('max_results', 50),
            min_quality_score=task.metadata.get('min_quality', 0.6)
        )
        
        # Discover papers
        engine = ResearchDiscoveryEngine()
        papers = await engine.discover_papers(search_query)
        
        # Store discovered papers
        stored_count = 0
        for paper in papers:
            try:
                citation_id = await db_manager.store_citation(paper)
                stored_count += 1
            except Exception as e:
                logger.warning(f"Failed to store paper {paper.title[:50]}: {e}")
        
        # Estimate API calls (3 APIs * batch requests)
        api_calls = len(query_terms) * 3
        
        result.records_processed = stored_count
        result.api_calls_made = api_calls
        result.output_data = {
            'papers_discovered': len(papers),
            'papers_stored': stored_count
        }
        
        # Record API usage
        for api_name in ['pubmed', 'crossref', 'semantic_scholar']:
            self.resource_monitor.record_api_call(api_name)
        
        return result
    
    async def _process_quality_scoring(self, task: ProcessingTask) -> ProcessingResult:
        """Process quality scoring task"""
        result = ProcessingResult(task_id=task.task_id, success=False, duration=0, records_processed=0, api_calls_made=0, memory_used=0)
        
        # Get papers to score
        papers = await db_manager.search_citations(
            query=task.metadata.get('search_query', ''),
            min_quality=0.0,
            limit=task.metadata.get('batch_size', 50)
        )
        
        scorer = QualityScorer()
        scored_count = 0
        
        for paper in papers:
            try:
                # Score paper quality
                metrics, bias_assessment, grade_assessment = await scorer.score_paper_quality(paper)
                
                # Update paper with quality metrics (would need to store these)
                paper.quality_score = metrics.overall_quality
                
                scored_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to score paper {paper.title[:50]}: {e}")
        
        result.records_processed = scored_count
        result.api_calls_made = 0  # Quality scoring doesn't use external APIs
        
        return result
    
    async def _scheduler_loop(self):
        """Main scheduler management loop"""
        while self.is_running:
            try:
                # Adjust worker count based on system health
                health = self.resource_monitor.get_system_health(
                    self.task_queue.pending_tasks.qsize(),
                    len(self.task_queue.active_tasks)
                )
                
                await self._adjust_worker_count(health)
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
    
    async def _adjust_worker_count(self, health: SystemHealth):
        """Dynamically adjust worker count based on system health"""
        current_workers = len([w for w in self.worker_pool if not w.done()])
        optimal_workers = self.max_workers
        
        # Reduce workers if system resources are high
        if health.cpu_usage > 80 or health.memory_usage > 80:
            optimal_workers = max(1, current_workers - 1)
        
        # Increase workers if system has capacity and queue is large
        elif health.cpu_usage < 50 and health.memory_usage < 50 and health.queue_size > 10:
            optimal_workers = min(self.max_workers, current_workers + 1)
        
        # Adjust worker pool
        if optimal_workers != current_workers:
            logger.info(f"Adjusting worker count: {current_workers} -> {optimal_workers}")
            
            if optimal_workers > current_workers:
                # Add workers
                for i in range(optimal_workers - current_workers):
                    worker_id = f"worker-{len(self.worker_pool)}"
                    worker = asyncio.create_task(self._worker_loop(worker_id))
                    self.worker_pool.append(worker)
            
            elif optimal_workers < current_workers:
                # Remove workers (they will stop naturally when is_running becomes False)
                workers_to_remove = current_workers - optimal_workers
                for _ in range(workers_to_remove):
                    if self.worker_pool:
                        worker = self.worker_pool.pop()
                        if not worker.done():
                            worker.cancel()
    
    async def _health_check_loop(self):
        """Periodic health checks and maintenance"""
        while self.is_running:
            try:
                # Database maintenance
                await db_manager.cleanup_old_records(days_to_keep=30)
                
                # Performance metrics cleanup
                await self.resource_monitor._collect_metrics()
                
                # Log health status
                health = self.resource_monitor.get_system_health(
                    self.task_queue.pending_tasks.qsize(),
                    len(self.task_queue.active_tasks)
                )
                
                logger.info(f"System Health - CPU: {health.cpu_usage:.1f}%, "
                           f"Memory: {health.memory_usage:.1f}%, "
                           f"Queue: {health.queue_size}, "
                           f"Active: {health.active_tasks}, "
                           f"Throughput: {health.throughput:.1f}/min")
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    async def submit_task(self, task: ProcessingTask):
        """Submit a task to the scheduler"""
        await self.task_queue.add_task(task)
        logger.debug(f"Submitted task {task.task_id} ({task.task_type})")
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        queue_status = self.task_queue.get_status()
        
        health = self.resource_monitor.get_system_health(
            queue_status['pending'],
            queue_status['active']
        )
        
        return {
            'is_running': self.is_running,
            'worker_count': len([w for w in self.worker_pool if not w.done()]),
            'queue_status': queue_status,
            'system_health': {
                'cpu_usage': health.cpu_usage,
                'memory_usage': health.memory_usage,
                'disk_usage': health.disk_usage,
                'error_rate': health.error_rate,
                'throughput': health.throughput
            },
            'api_rates': health.api_rate_limits
        }

# Global scheduler instance
scheduler = IntelligentScheduler()

async def main():
    """Test the automation pipeline"""
    # Initialize database
    await db_manager.initialize()
    
    # Start scheduler
    await scheduler.start()
    
    # Create some test tasks
    tasks = [
        ProcessingTask(
            task_id="test-discovery-1",
            task_type="research_discovery",
            priority=1,
            metadata={
                'query_terms': ['resistance training', 'strength'],
                'max_results': 20
            }
        ),
        ProcessingTask(
            task_id="test-validation-1", 
            task_type="citation_validation",
            priority=2,
            metadata={'batch_size': 50}
        )
    ]
    
    # Submit tasks
    for task in tasks:
        await scheduler.submit_task(task)
    
    # Monitor for a while
    for i in range(12):  # 2 minutes
        status = scheduler.get_status()
        print(f"Status: {status['queue_status']}")
        await asyncio.sleep(10)
    
    # Stop scheduler
    await scheduler.stop()

if __name__ == "__main__":
    # Set up graceful shutdown
    def signal_handler(signum, frame):
        print("Received shutdown signal")
        asyncio.create_task(scheduler.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    asyncio.run(main())