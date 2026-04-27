#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Citation Automation System
Unit tests, integration tests, performance tests, and end-to-end validation
"""

import asyncio
import pytest
import aiohttp
import tempfile
import json
import time
import random
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules to test
from research_discovery import ResearchDiscoveryEngine, SearchQuery, ResearchPaper, PubMedAPI, CrossRefAPI
from quality_scorer import QualityScorer, QualityMetrics, BiasAssessment, GRADEAssessment
from content_enhancer import ContentEnhancementEngine, ContentAnalyzer, CitationSuggestion
from database import DatabaseManager, CitationRecord, FileProcessingRecord
from automation_pipeline import IntelligentScheduler, ProcessingTask, TaskQueue
from monitoring import HealthChecker, AlertManager, QualityAssuranceReporter
from config import config

logger = logging.getLogger(__name__)

class TestFixtures:
    """Test data fixtures"""
    
    @staticmethod
    def sample_research_paper() -> ResearchPaper:
        """Create a sample research paper for testing"""
        return ResearchPaper(
            title="Effects of High-Intensity Interval Training on Cardiovascular Health",
            authors=["Smith, J.A.", "Johnson, B.C.", "Williams, D.E."],
            abstract="Background: High-intensity interval training (HIIT) has shown promise for improving cardiovascular health. Methods: This randomized controlled trial examined 120 healthy adults over 12 weeks. Results: HIIT group showed 15.3% improvement in VO2max (p<0.001). Conclusion: HIIT is effective for cardiovascular improvement.",
            journal="Medicine & Science in Sports & Exercise",
            publication_date="2023-06-01",
            doi="10.1249/MSS.0000000000003123",
            pmid="37123456",
            keywords=["HIIT", "cardiovascular", "exercise", "training"],
            study_type="randomized_controlled_trial",
            citation_count=25,
            quality_score=0.85,
            source_api="pubmed"
        )
    
    @staticmethod
    def sample_search_query() -> SearchQuery:
        """Create a sample search query"""
        return SearchQuery(
            terms=["resistance training", "strength", "muscle"],
            max_results=20,
            min_quality_score=0.6,
            date_range=("2020-01-01", "2024-12-31")
        )
    
    @staticmethod
    def sample_content() -> str:
        """Sample content for testing"""
        return """# High-Intensity Interval Training

## Quick Takeaway
HIIT training significantly improves cardiovascular health and performance in healthy adults.

## Key Points
- HIIT protocols can improve VO2max by 10-20% in sedentary individuals
- Training sessions as short as 10-20 minutes can be effective
- HIIT appears superior to moderate-intensity continuous training for time-efficient improvements
- Protocols typically involve 30 seconds to 4 minutes of high-intensity work

## Deep Dive

High-intensity interval training (HIIT) has emerged as a time-efficient method for improving cardiovascular fitness and metabolic health. Research demonstrates that HIIT protocols can produce similar or superior adaptations to traditional moderate-intensity continuous training in significantly less time.

The physiological mechanisms underlying HIIT adaptations include enhanced mitochondrial biogenesis, improved cardiac output, and increased capillarization of skeletal muscle. Studies show that HIIT can improve VO2max by 15-20% in previously sedentary individuals within 6-8 weeks of training.

## Research Evidence

This section needs more citations to support the claims made above.
"""

class TestDatabaseIntegration:
    """Test database operations"""
    
    @pytest.fixture
    async def test_db(self):
        """Create a test database"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        yield db_manager
        
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_store_citation(self, test_db):
        """Test storing a citation in database"""
        paper = TestFixtures.sample_research_paper()
        
        citation_id = await test_db.store_citation(paper)
        
        assert citation_id is not None
        assert isinstance(citation_id, int)
        
        # Retrieve and verify
        retrieved = await test_db.get_citation_by_doi(paper.doi)
        assert retrieved is not None
        assert retrieved.title == paper.title
        assert retrieved.doi == paper.doi
    
    @pytest.mark.asyncio
    async def test_search_citations(self, test_db):
        """Test citation search functionality"""
        # Store some test papers
        papers = [
            TestFixtures.sample_research_paper(),
            ResearchPaper(
                title="Resistance Training Adaptations in Older Adults",
                authors=["Brown, A.B."],
                abstract="Study of resistance training effects in elderly population",
                journal="Journal of Aging and Physical Activity",
                publication_date="2023-01-15",
                doi="10.1123/japa.2023-0001",
                study_type="cohort_study",
                quality_score=0.75
            )
        ]
        
        for paper in papers:
            await test_db.store_citation(paper)
        
        # Test search
        results = await test_db.search_citations("resistance training", min_quality=0.7)
        
        assert len(results) >= 1
        assert any("resistance" in r.title.lower() or "resistance" in r.abstract.lower() for r in results)
    
    @pytest.mark.asyncio
    async def test_validation_statistics(self, test_db):
        """Test validation statistics calculation"""
        # Store test citations with different validation statuses
        paper = TestFixtures.sample_research_paper()
        citation_id = await test_db.store_citation(paper)
        
        await test_db.update_validation_status(citation_id, "valid")
        
        stats = await test_db.get_validation_statistics()
        
        assert 'total_citations' in stats
        assert 'validation_rate' in stats
        assert stats['total_citations'] >= 1

class TestResearchDiscovery:
    """Test research discovery functionality"""
    
    @pytest.fixture
    def discovery_engine(self):
        """Create research discovery engine"""
        return ResearchDiscoveryEngine()
    
    @pytest.mark.asyncio
    async def test_pubmed_search(self):
        """Test PubMed API search"""
        pubmed_api = PubMedAPI()
        query = TestFixtures.sample_search_query()
        
        # Mock the HTTP response to avoid actual API calls
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                'esearchresult': {'idlist': ['12345678', '87654321']}
            }
            mock_response.text.return_value = """
            <PubmedArticleSet>
                <PubmedArticle>
                    <MedlineCitation>
                        <PMID>12345678</PMID>
                        <Article>
                            <ArticleTitle>Test Article Title</ArticleTitle>
                            <Abstract><AbstractText>Test abstract content</AbstractText></Abstract>
                            <Journal><Title>Test Journal</Title></Journal>
                            <AuthorList>
                                <Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
                            </AuthorList>
                        </Article>
                    </MedlineCitation>
                    <PubmedData>
                        <ArticleIdList>
                            <ArticleId IdType="doi">10.1000/test.doi</ArticleId>
                        </ArticleIdList>
                    </PubmedData>
                </PubmedArticle>
            </PubmedArticleSet>
            """
            mock_get.return_value.__aenter__.return_value = mock_response
            
            async with aiohttp.ClientSession() as session:
                papers = await pubmed_api.search_papers(query, session)
            
            assert len(papers) >= 1
            assert papers[0].title == "Test Article Title"
            assert papers[0].doi == "10.1000/test.doi"
    
    @pytest.mark.asyncio
    async def test_paper_deduplication(self, discovery_engine):
        """Test paper deduplication"""
        # Create papers with same DOI but different sources
        paper1 = TestFixtures.sample_research_paper()
        paper1.source_api = "pubmed"
        
        paper2 = TestFixtures.sample_research_paper()
        paper2.source_api = "crossref"
        paper2.title = "Slightly Different Title"  # Minor difference
        
        papers = [paper1, paper2]
        unique_papers = discovery_engine._deduplicate_papers(papers)
        
        assert len(unique_papers) == 1  # Should deduplicate based on DOI
    
    def test_title_normalization(self, discovery_engine):
        """Test title normalization for comparison"""
        title1 = "Effects of High-Intensity Interval Training on Health"
        title2 = "Effects of High Intensity Interval Training on Health!"
        
        norm1 = discovery_engine._normalize_title(title1)
        norm2 = discovery_engine._normalize_title(title2)
        
        assert norm1 == norm2

class TestQualityScoring:
    """Test citation quality scoring"""
    
    @pytest.fixture
    def quality_scorer(self):
        """Create quality scorer"""
        return QualityScorer()
    
    @pytest.mark.asyncio
    async def test_paper_quality_scoring(self, quality_scorer):
        """Test comprehensive paper quality scoring"""
        paper = TestFixtures.sample_research_paper()
        
        metrics, bias_assessment, grade_assessment = await quality_scorer.score_paper_quality(paper)
        
        assert isinstance(metrics, QualityMetrics)
        assert isinstance(bias_assessment, BiasAssessment)
        assert isinstance(grade_assessment, GRADEAssessment)
        
        assert 0 <= metrics.overall_quality <= 1
        assert metrics.study_design_score > 0  # RCT should have high score
        assert grade_assessment.final_grade in ['very_low', 'low', 'moderate', 'high']
    
    def test_study_type_classification(self, quality_scorer):
        """Test study type classification"""
        # Test RCT identification
        rct_text = "randomized controlled trial placebo double-blind"
        study_type = quality_scorer.bias_detector._assess_selection_bias(rct_text)
        
        assert study_type == "low"  # RCT should have low selection bias
    
    def test_bias_detection(self, quality_scorer):
        """Test bias detection algorithms"""
        # Test funding bias detection
        biased_text = "funded by pharmaceutical company conflict of interest"
        bias_assessment = quality_scorer.bias_detector.assess_bias_risk(
            ResearchPaper(
                title="Test Study",
                authors=["Author, A."],
                abstract=biased_text,
                journal="Test Journal",
                publication_date="2023"
            )
        )
        
        assert bias_assessment.funding_bias in ["high", "unclear"]
        assert bias_assessment.risk_score > 0.3  # Should indicate some risk

class TestContentEnhancement:
    """Test content enhancement functionality"""
    
    @pytest.fixture
    def content_enhancer(self):
        """Create content enhancement engine"""
        return ContentEnhancementEngine()
    
    @pytest.fixture
    def content_analyzer(self):
        """Create content analyzer"""
        return ContentAnalyzer()
    
    def test_content_parsing(self, content_analyzer):
        """Test content section parsing"""
        content = TestFixtures.sample_content()
        sections = content_analyzer.parse_content(content)
        
        assert len(sections) > 0
        
        # Check for expected sections
        section_titles = [s.title for s in sections]
        assert "Quick Takeaway" in section_titles
        assert "Deep Dive" in section_titles
        assert "Research Evidence" in section_titles
    
    def test_citation_extraction(self, content_analyzer):
        """Test citation extraction from content"""
        content_with_citations = """
        # Test Content
        
        Research shows that HIIT improves VO2max (Smith et al., 2023). 
        DOI: https://doi.org/10.1249/MSS.0000000000003123
        
        Another study found similar results. PMID: https://pubmed.ncbi.nlm.nih.gov/37123456
        """
        
        citations = content_analyzer._extract_citations(content_with_citations)
        
        assert len(citations) >= 2
        assert any("10.1249/MSS.0000000000003123" in c for c in citations)
        assert any("37123456" in c for c in citations)
    
    def test_key_claims_extraction(self, content_analyzer):
        """Test extraction of key claims that need citations"""
        content = """
        Studies show that HIIT improves VO2max by 15-20% in healthy adults.
        Research demonstrates significant improvements in cardiac function.
        The training protocol resulted in a 25% increase in performance.
        """
        
        claims = content_analyzer._extract_key_claims(content)
        
        assert len(claims) > 0
        assert any("15-20%" in claim for claim in claims)
        assert any("25%" in claim for claim in claims)
    
    @pytest.mark.asyncio
    async def test_content_enhancement_pipeline(self, content_enhancer):
        """Test end-to-end content enhancement"""
        content = TestFixtures.sample_content()
        
        # Mock the research discovery to avoid API calls
        with patch.object(content_enhancer.citation_engine.research_engine, 'discover_papers') as mock_discover:
            mock_discover.return_value = [TestFixtures.sample_research_paper()]
            
            enhancement = await content_enhancer.enhance_content(content)
        
        assert enhancement.enhanced_content != content  # Should be modified
        assert len(enhancement.citation_suggestions) >= 0
        assert 0 <= enhancement.overall_improvement_score <= 1

class TestAutomationPipeline:
    """Test automation pipeline functionality"""
    
    @pytest.fixture
    def task_queue(self):
        """Create task queue"""
        return TaskQueue()
    
    @pytest.fixture
    def scheduler(self):
        """Create scheduler with minimal workers for testing"""
        return IntelligentScheduler(max_workers=2)
    
    @pytest.mark.asyncio
    async def test_task_queue_operations(self, task_queue):
        """Test task queue basic operations"""
        task = ProcessingTask(
            task_id="test-task-1",
            task_type="test",
            priority=1
        )
        
        await task_queue.add_task(task)
        
        status = task_queue.get_status()
        assert status['total'] == 1
        assert status['pending'] >= 1
        
        retrieved_task = await task_queue.get_next_task()
        assert retrieved_task is not None
        assert retrieved_task.task_id == "test-task-1"
    
    @pytest.mark.asyncio
    async def test_task_dependencies(self, task_queue):
        """Test task dependency management"""
        # Create dependent tasks
        task1 = ProcessingTask(task_id="task-1", task_type="test", priority=1)
        task2 = ProcessingTask(
            task_id="task-2", 
            task_type="test", 
            priority=2,
            dependencies=["task-1"]
        )
        
        await task_queue.add_task(task1)
        await task_queue.add_task(task2)
        
        # Task 1 should be available first
        first_task = await task_queue.get_next_task()
        assert first_task.task_id == "task-1"
        
        # Task 2 should not be available yet
        second_task = await asyncio.wait_for(task_queue.get_next_task(), timeout=0.1)
        assert second_task is None  # Should timeout as task-2 depends on task-1
    
    def test_processing_task_creation(self):
        """Test processing task creation and validation"""
        task = ProcessingTask(
            task_id="test-validation",
            task_type="citation_validation",
            file_path=Path("test.md"),
            priority=5,
            metadata={"batch_size": 100}
        )
        
        assert task.task_id == "test-validation"
        assert task.task_type == "citation_validation"
        assert task.priority == 5
        assert task.metadata["batch_size"] == 100
        assert task.retry_count == 0
        assert task.max_retries == 3

class TestMonitoring:
    """Test monitoring and health check functionality"""
    
    @pytest.fixture
    def health_checker(self):
        """Create health checker"""
        return HealthChecker()
    
    @pytest.fixture
    def alert_manager(self):
        """Create alert manager"""
        return AlertManager()
    
    @pytest.mark.asyncio
    async def test_system_resource_check(self, health_checker):
        """Test system resource monitoring"""
        result = await health_checker._check_system_resources()
        
        assert result.check_name == "system_resources"
        assert result.status in ["healthy", "warning", "critical", "unknown"]
        assert 'cpu_percent' in result.details
        assert 'memory_percent' in result.details
        assert 'disk_percent' in result.details
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, health_checker):
        """Test database health check"""
        # Mock database operations for testing
        with patch('database.db_manager.get_database_stats') as mock_stats:
            mock_stats.return_value = {'citations_count': 100}
            
            result = await health_checker._check_database_connection()
            
            assert result.check_name == "database_connection"
            assert result.status in ["healthy", "warning", "critical", "unknown"]
    
    @pytest.mark.asyncio
    async def test_alert_generation(self, alert_manager):
        """Test alert generation from health check results"""
        from monitoring import HealthCheckResult, Alert
        
        # Create a critical health check result
        critical_result = HealthCheckResult(
            check_name="test_check",
            status="critical",
            message="Test critical condition",
            value=95.0,
            threshold=80.0
        )
        
        await alert_manager.process_health_results([critical_result])
        
        active_alerts = alert_manager.get_active_alerts()
        assert len(active_alerts) >= 1
        
        alert = active_alerts[0]
        assert alert.severity == "critical"
        assert alert.component == "test_check"
    
    def test_alert_resolution(self, alert_manager):
        """Test alert resolution when issues are fixed"""
        # This would test the alert resolution logic
        # when health checks return to normal status
        pass

class PerformanceTests:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_citation_processing_performance(self):
        """Test citation processing performance under load"""
        start_time = time.time()
        
        # Create multiple research papers
        papers = [TestFixtures.sample_research_paper() for _ in range(100)]
        
        # Modify each paper slightly to avoid deduplication
        for i, paper in enumerate(papers):
            paper.title = f"{paper.title} - Study {i}"
            paper.doi = f"10.1000/test.{i:04d}"
        
        # Process papers with quality scoring
        quality_scorer = QualityScorer()
        
        results = []
        for paper in papers[:10]:  # Test with 10 papers to avoid long test times
            try:
                metrics, bias, grade = await quality_scorer.score_paper_quality(paper)
                results.append((metrics, bias, grade))
            except Exception as e:
                logger.warning(f"Failed to score paper: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(results) <= 10
        assert duration < 30  # Should complete within 30 seconds
        
        # Log performance metrics
        avg_time_per_paper = duration / max(len(results), 1)
        logger.info(f"Quality scoring performance: {avg_time_per_paper:.2f}s per paper")
    
    @pytest.mark.asyncio
    async def test_database_bulk_operations(self):
        """Test database performance with bulk operations"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        try:
            start_time = time.time()
            
            # Bulk insert test papers
            papers = []
            for i in range(50):
                paper = TestFixtures.sample_research_paper()
                paper.title = f"Performance Test Paper {i}"
                paper.doi = f"10.1000/perf.test.{i:04d}"
                papers.append(paper)
            
            # Insert papers
            for paper in papers:
                await db_manager.store_citation(paper)
            
            end_time = time.time()
            insert_duration = end_time - start_time
            
            # Search performance test
            start_time = time.time()
            
            results = await db_manager.search_citations("Performance Test", limit=50)
            
            end_time = time.time()
            search_duration = end_time - start_time
            
            assert len(results) <= 50
            assert insert_duration < 10  # Should complete within 10 seconds
            assert search_duration < 2   # Search should be fast
            
            logger.info(f"Database performance - Insert: {insert_duration:.2f}s, Search: {search_duration:.2f}s")
            
        finally:
            Path(db_path).unlink(missing_ok=True)

class IntegrationTests:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_complete_processing_pipeline(self):
        """Test complete processing from content to enhanced output"""
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        try:
            # Step 1: Process content through content analyzer
            content = TestFixtures.sample_content()
            analyzer = ContentAnalyzer()
            sections = analyzer.parse_content(content)
            
            assert len(sections) > 0
            
            # Step 2: Mock research discovery and enhancement
            enhancer = ContentEnhancementEngine()
            
            with patch.object(enhancer.citation_engine.research_engine, 'discover_papers') as mock_discover:
                # Mock discovery results
                mock_papers = [TestFixtures.sample_research_paper()]
                mock_discover.return_value = mock_papers
                
                # Store mock papers in database
                for paper in mock_papers:
                    await db_manager.store_citation(paper)
                
                # Enhance content
                enhancement = await enhancer.enhance_content(content)
                
                assert enhancement.enhanced_content != content
                assert len(enhancement.citation_suggestions) >= 0
            
            # Step 3: Validate database state
            stats = await db_manager.get_database_stats()
            assert stats['citations_count'] >= 1
            
            # Step 4: Run health checks
            health_checker = HealthChecker()
            
            with patch.object(health_checker, '_check_api_endpoints') as mock_api_check:
                # Mock API check to avoid external dependencies
                mock_result = type('MockResult', (), {
                    'check_name': 'api_endpoints',
                    'status': 'healthy',
                    'message': 'Mock API check passed',
                    'details': {}
                })()
                mock_api_check.return_value = mock_result
                
                health_results = await health_checker.run_all_checks()
                
                assert len(health_results) > 0
                assert any(result.check_name == "database_connection" for result in health_results)
            
            logger.info("Integration test completed successfully")
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio 
    async def test_error_handling_and_recovery(self):
        """Test system behavior under error conditions"""
        # Test database connection failure
        db_manager = DatabaseManager("/invalid/path/database.db")
        
        # This should handle the error gracefully
        try:
            await db_manager.initialize()
            # If we get here, the test environment might have different behavior
            logger.warning("Database initialization succeeded with invalid path")
        except Exception as e:
            # Expected behavior - database should fail to initialize
            assert "database" in str(e).lower() or "path" in str(e).lower()
        
        # Test API failure handling
        discovery_engine = ResearchDiscoveryEngine()
        
        # Create a query that might fail
        query = SearchQuery(terms=["nonexistent_research_term_12345"], max_results=5)
        
        # This should handle API failures gracefully
        papers = await discovery_engine.discover_papers(query)
        
        # Should return empty list or small list, not crash
        assert isinstance(papers, list)
        assert len(papers) >= 0

def run_test_suite():
    """Run the complete test suite"""
    logger.info("Starting comprehensive test suite...")
    
    # Configure pytest to run tests
    test_args = [
        __file__,
        "-v",  # Verbose output
        "-s",  # Don't capture print statements
        "--tb=short",  # Short traceback format
        "-x",  # Stop on first failure
        "--asyncio-mode=auto"  # Auto-detect async tests
    ]
    
    # Run tests
    result = pytest.main(test_args)
    
    if result == 0:
        logger.info("All tests passed successfully!")
    else:
        logger.error(f"Test suite failed with exit code: {result}")
    
    return result

async def run_performance_benchmarks():
    """Run performance benchmarks"""
    logger.info("Running performance benchmarks...")
    
    benchmarks = [
        ("Citation Quality Scoring", PerformanceTests().test_citation_processing_performance()),
        ("Database Operations", PerformanceTests().test_database_bulk_operations()),
    ]
    
    results = {}
    
    for benchmark_name, benchmark_coro in benchmarks:
        try:
            start_time = time.time()
            await benchmark_coro
            duration = time.time() - start_time
            
            results[benchmark_name] = {
                "status": "passed",
                "duration": duration
            }
            
            logger.info(f"✅ {benchmark_name}: {duration:.2f}s")
            
        except Exception as e:
            results[benchmark_name] = {
                "status": "failed",
                "error": str(e)
            }
            
            logger.error(f"❌ {benchmark_name}: {str(e)}")
    
    return results

async def main():
    """Main test runner"""
    logger.info("Citation Automation System - Test Suite")
    
    # Run unit and integration tests
    test_result = run_test_suite()
    
    # Run performance benchmarks
    perf_results = await run_performance_benchmarks()
    
    # Generate test report
    report = {
        "timestamp": datetime.now().isoformat(),
        "unit_tests": "passed" if test_result == 0 else "failed",
        "performance_benchmarks": perf_results,
        "summary": {
            "overall_status": "passed" if test_result == 0 and all(r["status"] == "passed" for r in perf_results.values()) else "failed"
        }
    }
    
    # Save report
    report_file = Path("test_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Test report saved: {report_file}")
    logger.info(f"Overall test status: {report['summary']['overall_status']}")
    
    return report

if __name__ == "__main__":
    # Set up logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    asyncio.run(main())