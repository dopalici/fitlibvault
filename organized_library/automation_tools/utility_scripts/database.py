#!/usr/bin/env python3
"""
Database Integration for Citation Automation System
Persistent storage for citations, validation results, and quality metrics
"""

import sqlite3
import asyncio
import aiosqlite
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

from research_discovery import ResearchPaper
from quality_scorer import QualityMetrics, BiasAssessment, GRADEAssessment
from config import config

logger = logging.getLogger(__name__)

@dataclass
class CitationRecord:
    """Database record for citations"""
    id: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    title: str = ""
    authors: str = ""  # JSON string
    journal: str = ""
    publication_date: str = ""
    abstract: str = ""
    keywords: str = ""  # JSON string
    study_type: Optional[str] = None
    impact_factor: Optional[float] = None
    citation_count: Optional[int] = None
    quality_score: float = 0.0
    validation_status: str = "pending"  # pending, valid, invalid, error
    validation_date: Optional[str] = None
    validation_error: Optional[str] = None
    source_api: str = ""
    created_at: str = ""
    updated_at: str = ""

@dataclass 
class FileProcessingRecord:
    """Database record for file processing status"""
    id: Optional[int] = None
    file_path: str = ""
    file_hash: str = ""
    processing_status: str = "pending"  # pending, processing, completed, error
    processing_date: Optional[str] = None
    citation_count: int = 0
    quality_score: float = 0.0
    enhancement_applied: bool = False
    error_message: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

class DatabaseManager:
    """Database manager for citation automation system"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.database.db_path
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Citations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doi TEXT UNIQUE,
                    pmid TEXT UNIQUE,
                    title TEXT NOT NULL,
                    authors TEXT,
                    journal TEXT,
                    publication_date TEXT,
                    abstract TEXT,
                    keywords TEXT,
                    study_type TEXT,
                    impact_factor REAL,
                    citation_count INTEGER,
                    quality_score REAL DEFAULT 0.0,
                    validation_status TEXT DEFAULT 'pending',
                    validation_date TEXT,
                    validation_error TEXT,
                    source_api TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Quality metrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS quality_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_id INTEGER,
                    grade_score REAL DEFAULT 0.0,
                    impact_factor_score REAL DEFAULT 0.0,
                    study_design_score REAL DEFAULT 0.0,
                    bias_risk_score REAL DEFAULT 0.0,
                    methodological_quality REAL DEFAULT 0.0,
                    sample_size_adequacy REAL DEFAULT 0.0,
                    statistical_rigor REAL DEFAULT 0.0,
                    author_credibility REAL DEFAULT 0.0,
                    journal_reputation REAL DEFAULT 0.0,
                    citation_velocity REAL DEFAULT 0.0,
                    overall_quality REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (citation_id) REFERENCES citations (id)
                )
            """)
            
            # Bias assessments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bias_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_id INTEGER,
                    selection_bias TEXT DEFAULT 'unclear',
                    performance_bias TEXT DEFAULT 'unclear',
                    detection_bias TEXT DEFAULT 'unclear',
                    attrition_bias TEXT DEFAULT 'unclear',
                    reporting_bias TEXT DEFAULT 'unclear',
                    funding_bias TEXT DEFAULT 'unclear',
                    overall_risk TEXT DEFAULT 'unclear',
                    risk_score REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (citation_id) REFERENCES citations (id)
                )
            """)
            
            # File processing table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS file_processing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT,
                    processing_status TEXT DEFAULT 'pending',
                    processing_date TEXT,
                    citation_count INTEGER DEFAULT 0,
                    quality_score REAL DEFAULT 0.0,
                    enhancement_applied BOOLEAN DEFAULT FALSE,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Citation usage tracking
            await db.execute("""
                CREATE TABLE IF NOT EXISTS citation_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    citation_id INTEGER,
                    file_id INTEGER,
                    usage_context TEXT,
                    usage_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (citation_id) REFERENCES citations (id),
                    FOREIGN KEY (file_id) REFERENCES file_processing (id)
                )
            """)
            
            # Performance metrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT,
                    duration_seconds REAL,
                    records_processed INTEGER,
                    success_count INTEGER,
                    error_count INTEGER,
                    api_calls_made INTEGER,
                    memory_usage_mb REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_citations_doi ON citations(doi)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_citations_pmid ON citations(pmid)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_citations_quality ON citations(quality_score)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_citations_validation ON citations(validation_status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_file_processing_status ON file_processing(processing_status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_file_processing_hash ON file_processing(file_hash)")
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def store_citation(self, paper: ResearchPaper, quality_metrics: Optional[QualityMetrics] = None,
                           bias_assessment: Optional[BiasAssessment] = None) -> int:
        """Store a citation and return its ID"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Check if citation already exists
            existing_id = await self._get_existing_citation_id(db, paper)
            if existing_id:
                await self._update_citation(db, existing_id, paper, quality_metrics, bias_assessment)
                return existing_id
            
            # Insert new citation
            citation_data = (
                paper.doi, paper.pmid, paper.title, json.dumps(paper.authors),
                paper.journal, paper.publication_date, paper.abstract,
                json.dumps(paper.keywords), paper.study_type, paper.impact_factor,
                paper.citation_count, paper.quality_score, 'pending', None, None,
                paper.source_api, datetime.now().isoformat()
            )
            
            cursor = await db.execute("""
                INSERT INTO citations (
                    doi, pmid, title, authors, journal, publication_date, abstract,
                    keywords, study_type, impact_factor, citation_count, quality_score,
                    validation_status, validation_date, validation_error, source_api, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, citation_data)
            
            citation_id = cursor.lastrowid
            
            # Store quality metrics if provided
            if quality_metrics:
                await self._store_quality_metrics(db, citation_id, quality_metrics)
            
            # Store bias assessment if provided
            if bias_assessment:
                await self._store_bias_assessment(db, citation_id, bias_assessment)
            
            await db.commit()
            logger.debug(f"Stored citation: {paper.title[:50]}...")
            return citation_id
    
    async def _get_existing_citation_id(self, db: aiosqlite.Connection, paper: ResearchPaper) -> Optional[int]:
        """Check if citation already exists"""
        if paper.doi:
            cursor = await db.execute("SELECT id FROM citations WHERE doi = ?", (paper.doi,))
            result = await cursor.fetchone()
            if result:
                return result[0]
        
        if paper.pmid:
            cursor = await db.execute("SELECT id FROM citations WHERE pmid = ?", (paper.pmid,))
            result = await cursor.fetchone()
            if result:
                return result[0]
        
        # Check by title similarity (simplified)
        cursor = await db.execute("SELECT id, title FROM citations WHERE title LIKE ?", (f"%{paper.title[:30]}%",))
        results = await cursor.fetchall()
        
        for result in results:
            if self._titles_similar(paper.title, result[1]):
                return result[0]
        
        return None
    
    def _titles_similar(self, title1: str, title2: str, threshold: float = 0.8) -> bool:
        """Check if two titles are similar"""
        import difflib
        ratio = difflib.SequenceMatcher(None, title1.lower(), title2.lower()).ratio()
        return ratio >= threshold
    
    async def _update_citation(self, db: aiosqlite.Connection, citation_id: int, paper: ResearchPaper,
                             quality_metrics: Optional[QualityMetrics] = None,
                             bias_assessment: Optional[BiasAssessment] = None):
        """Update existing citation"""
        await db.execute("""
            UPDATE citations SET
                title = ?, authors = ?, journal = ?, publication_date = ?,
                abstract = ?, keywords = ?, study_type = ?, impact_factor = ?,
                citation_count = ?, quality_score = ?, source_api = ?, updated_at = ?
            WHERE id = ?
        """, (
            paper.title, json.dumps(paper.authors), paper.journal, paper.publication_date,
            paper.abstract, json.dumps(paper.keywords), paper.study_type, paper.impact_factor,
            paper.citation_count, paper.quality_score, paper.source_api,
            datetime.now().isoformat(), citation_id
        ))
        
        if quality_metrics:
            await self._update_quality_metrics(db, citation_id, quality_metrics)
        
        if bias_assessment:
            await self._update_bias_assessment(db, citation_id, bias_assessment)
    
    async def _store_quality_metrics(self, db: aiosqlite.Connection, citation_id: int, metrics: QualityMetrics):
        """Store quality metrics"""
        await db.execute("""
            INSERT INTO quality_metrics (
                citation_id, grade_score, impact_factor_score, study_design_score,
                bias_risk_score, methodological_quality, sample_size_adequacy,
                statistical_rigor, author_credibility, journal_reputation,
                citation_velocity, overall_quality
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            citation_id, metrics.grade_score, metrics.impact_factor_score,
            metrics.study_design_score, metrics.bias_risk_score,
            metrics.methodological_quality, metrics.sample_size_adequacy,
            metrics.statistical_rigor, metrics.author_credibility,
            metrics.journal_reputation, metrics.citation_velocity,
            metrics.overall_quality
        ))
    
    async def _store_bias_assessment(self, db: aiosqlite.Connection, citation_id: int, assessment: BiasAssessment):
        """Store bias assessment"""
        await db.execute("""
            INSERT INTO bias_assessments (
                citation_id, selection_bias, performance_bias, detection_bias,
                attrition_bias, reporting_bias, funding_bias, overall_risk, risk_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            citation_id, assessment.selection_bias, assessment.performance_bias,
            assessment.detection_bias, assessment.attrition_bias,
            assessment.reporting_bias, assessment.funding_bias,
            assessment.overall_risk, assessment.risk_score
        ))
    
    async def _update_quality_metrics(self, db: aiosqlite.Connection, citation_id: int, metrics: QualityMetrics):
        """Update quality metrics"""
        await db.execute("""
            UPDATE quality_metrics SET
                grade_score = ?, impact_factor_score = ?, study_design_score = ?,
                bias_risk_score = ?, methodological_quality = ?, sample_size_adequacy = ?,
                statistical_rigor = ?, author_credibility = ?, journal_reputation = ?,
                citation_velocity = ?, overall_quality = ?
            WHERE citation_id = ?
        """, (
            metrics.grade_score, metrics.impact_factor_score, metrics.study_design_score,
            metrics.bias_risk_score, metrics.methodological_quality,
            metrics.sample_size_adequacy, metrics.statistical_rigor,
            metrics.author_credibility, metrics.journal_reputation,
            metrics.citation_velocity, metrics.overall_quality, citation_id
        ))
    
    async def _update_bias_assessment(self, db: aiosqlite.Connection, citation_id: int, assessment: BiasAssessment):
        """Update bias assessment"""
        await db.execute("""
            UPDATE bias_assessments SET
                selection_bias = ?, performance_bias = ?, detection_bias = ?,
                attrition_bias = ?, reporting_bias = ?, funding_bias = ?,
                overall_risk = ?, risk_score = ?
            WHERE citation_id = ?
        """, (
            assessment.selection_bias, assessment.performance_bias,
            assessment.detection_bias, assessment.attrition_bias,
            assessment.reporting_bias, assessment.funding_bias,
            assessment.overall_risk, assessment.risk_score, citation_id
        ))
    
    async def get_citation_by_doi(self, doi: str) -> Optional[ResearchPaper]:
        """Retrieve citation by DOI"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT doi, pmid, title, authors, journal, publication_date,
                       abstract, keywords, study_type, impact_factor,
                       citation_count, quality_score, source_api
                FROM citations WHERE doi = ?
            """, (doi,))
            
            result = await cursor.fetchone()
            if result:
                return self._row_to_research_paper(result)
            
            return None
    
    async def get_citation_by_pmid(self, pmid: str) -> Optional[ResearchPaper]:
        """Retrieve citation by PMID"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT doi, pmid, title, authors, journal, publication_date,
                       abstract, keywords, study_type, impact_factor,
                       citation_count, quality_score, source_api
                FROM citations WHERE pmid = ?
            """, (pmid,))
            
            result = await cursor.fetchone()
            if result:
                return self._row_to_research_paper(result)
            
            return None
    
    def _row_to_research_paper(self, row) -> ResearchPaper:
        """Convert database row to ResearchPaper object"""
        return ResearchPaper(
            doi=row[0],
            pmid=row[1],
            title=row[2],
            authors=json.loads(row[3]) if row[3] else [],
            journal=row[4],
            publication_date=row[5],
            abstract=row[6],
            keywords=json.loads(row[7]) if row[7] else [],
            study_type=row[8],
            impact_factor=row[9],
            citation_count=row[10],
            quality_score=row[11],
            source_api=row[12]
        )
    
    async def search_citations(self, query: str, min_quality: float = 0.0,
                             study_types: Optional[List[str]] = None,
                             limit: int = 100) -> List[ResearchPaper]:
        """Search citations in database"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            sql = """
                SELECT doi, pmid, title, authors, journal, publication_date,
                       abstract, keywords, study_type, impact_factor,
                       citation_count, quality_score, source_api
                FROM citations
                WHERE (title LIKE ? OR abstract LIKE ?) AND quality_score >= ?
            """
            params = [f"%{query}%", f"%{query}%", min_quality]
            
            if study_types:
                placeholders = ','.join(['?' for _ in study_types])
                sql += f" AND study_type IN ({placeholders})"
                params.extend(study_types)
            
            sql += " ORDER BY quality_score DESC, citation_count DESC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(sql, params)
            results = await cursor.fetchall()
            
            return [self._row_to_research_paper(row) for row in results]
    
    async def update_validation_status(self, citation_id: int, status: str, error: Optional[str] = None):
        """Update citation validation status"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE citations SET
                    validation_status = ?,
                    validation_date = ?,
                    validation_error = ?,
                    updated_at = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), error, datetime.now().isoformat(), citation_id))
            
            await db.commit()
    
    async def get_validation_statistics(self) -> Dict:
        """Get validation statistics"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT validation_status, COUNT(*) 
                FROM citations 
                GROUP BY validation_status
            """)
            
            status_counts = dict(await cursor.fetchall())
            
            cursor = await db.execute("SELECT COUNT(*) FROM citations")
            total_citations = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT AVG(quality_score) FROM citations WHERE quality_score > 0")
            avg_quality = (await cursor.fetchone())[0] or 0
            
            return {
                'total_citations': total_citations,
                'status_counts': status_counts,
                'average_quality_score': avg_quality,
                'validation_rate': status_counts.get('valid', 0) / max(total_citations, 1) * 100
            }
    
    async def store_file_processing_record(self, file_path: str, file_hash: str, 
                                         status: str = "pending") -> int:
        """Store file processing record"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Check if file already exists
            cursor = await db.execute("""
                SELECT id FROM file_processing WHERE file_path = ?
            """, (file_path,))
            
            result = await cursor.fetchone()
            if result:
                # Update existing record
                await db.execute("""
                    UPDATE file_processing SET
                        file_hash = ?, processing_status = ?, updated_at = ?
                    WHERE id = ?
                """, (file_hash, status, datetime.now().isoformat(), result[0]))
                await db.commit()
                return result[0]
            else:
                # Insert new record
                cursor = await db.execute("""
                    INSERT INTO file_processing (file_path, file_hash, processing_status)
                    VALUES (?, ?, ?)
                """, (file_path, file_hash, status))
                await db.commit()
                return cursor.lastrowid
    
    async def update_file_processing_status(self, file_id: int, status: str,
                                          citation_count: Optional[int] = None,
                                          quality_score: Optional[float] = None,
                                          error_message: Optional[str] = None):
        """Update file processing status"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            updates = ["processing_status = ?", "updated_at = ?"]
            params = [status, datetime.now().isoformat()]
            
            if status in ["completed", "error"]:
                updates.append("processing_date = ?")
                params.append(datetime.now().isoformat())
            
            if citation_count is not None:
                updates.append("citation_count = ?")
                params.append(citation_count)
            
            if quality_score is not None:
                updates.append("quality_score = ?")
                params.append(quality_score)
            
            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)
            
            params.append(file_id)
            
            sql = f"UPDATE file_processing SET {', '.join(updates)} WHERE id = ?"
            
            await db.execute(sql, params)
            await db.commit()
    
    async def get_processing_statistics(self) -> Dict:
        """Get file processing statistics"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT processing_status, COUNT(*) 
                FROM file_processing 
                GROUP BY processing_status
            """)
            
            status_counts = dict(await cursor.fetchall())
            
            cursor = await db.execute("SELECT COUNT(*) FROM file_processing")
            total_files = (await cursor.fetchone())[0]
            
            cursor = await db.execute("""
                SELECT AVG(quality_score) 
                FROM file_processing 
                WHERE quality_score > 0
            """)
            avg_quality = (await cursor.fetchone())[0] or 0
            
            cursor = await db.execute("""
                SELECT SUM(citation_count) 
                FROM file_processing
            """)
            total_citations_in_files = (await cursor.fetchone())[0] or 0
            
            return {
                'total_files': total_files,
                'status_counts': status_counts,
                'completion_rate': status_counts.get('completed', 0) / max(total_files, 1) * 100,
                'average_quality_score': avg_quality,
                'total_citations_in_files': total_citations_in_files
            }
    
    async def record_performance_metrics(self, operation_type: str, duration: float,
                                       records_processed: int, success_count: int,
                                       error_count: int, api_calls: int = 0,
                                       memory_usage: float = 0.0):
        """Record performance metrics"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                INSERT INTO performance_metrics (
                    operation_type, duration_seconds, records_processed,
                    success_count, error_count, api_calls_made, memory_usage_mb
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (operation_type, duration, records_processed, success_count,
                  error_count, api_calls, memory_usage))
            
            await db.commit()
    
    async def get_performance_metrics(self, operation_type: Optional[str] = None,
                                    hours_back: int = 24) -> Dict:
        """Get performance metrics"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            since_date = (datetime.now() - timedelta(hours=hours_back)).isoformat()
            
            where_clause = "WHERE timestamp >= ?"
            params = [since_date]
            
            if operation_type:
                where_clause += " AND operation_type = ?"
                params.append(operation_type)
            
            cursor = await db.execute(f"""
                SELECT 
                    operation_type,
                    COUNT(*) as operation_count,
                    AVG(duration_seconds) as avg_duration,
                    SUM(records_processed) as total_records,
                    SUM(success_count) as total_successes,
                    SUM(error_count) as total_errors,
                    SUM(api_calls_made) as total_api_calls,
                    AVG(memory_usage_mb) as avg_memory_usage
                FROM performance_metrics
                {where_clause}
                GROUP BY operation_type
                ORDER BY operation_count DESC
            """, params)
            
            results = await cursor.fetchall()
            
            metrics = []
            for row in results:
                metrics.append({
                    'operation_type': row[0],
                    'operation_count': row[1],
                    'avg_duration_seconds': row[2],
                    'total_records_processed': row[3],
                    'total_successes': row[4],
                    'total_errors': row[5],
                    'success_rate': (row[4] / max(row[3], 1)) * 100,
                    'total_api_calls': row[6],
                    'avg_memory_usage_mb': row[7]
                })
            
            return {
                'time_period_hours': hours_back,
                'metrics_by_operation': metrics
            }
    
    async def cleanup_old_records(self, days_to_keep: int = 90):
        """Clean up old records to manage database size"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            
            # Clean up old performance metrics
            cursor = await db.execute("""
                DELETE FROM performance_metrics WHERE timestamp < ?
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            
            await db.commit()
            logger.info(f"Cleaned up {deleted_count} old performance records")
    
    async def backup_database(self, backup_path: str):
        """Create database backup"""
        async with aiosqlite.connect(str(self.db_path)) as source:
            async with aiosqlite.connect(backup_path) as backup:
                await source.backup(backup)
        
        logger.info(f"Database backed up to {backup_path}")
    
    async def get_database_stats(self) -> Dict:
        """Get overall database statistics"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            stats = {}
            
            # Table sizes
            tables = ['citations', 'quality_metrics', 'bias_assessments', 
                     'file_processing', 'citation_usage', 'performance_metrics']
            
            for table in tables:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = (await cursor.fetchone())[0]
                stats[f"{table}_count"] = count
            
            # Database file size
            stats['database_size_mb'] = self.db_path.stat().st_size / 1024 / 1024
            
            # Recent activity
            cursor = await db.execute("""
                SELECT COUNT(*) FROM citations 
                WHERE created_at > datetime('now', '-7 days')
            """)
            stats['citations_added_last_7_days'] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("""
                SELECT COUNT(*) FROM file_processing 
                WHERE created_at > datetime('now', '-7 days')
            """)
            stats['files_processed_last_7_days'] = (await cursor.fetchone())[0]
            
            return stats

# Global database instance
db_manager = DatabaseManager()