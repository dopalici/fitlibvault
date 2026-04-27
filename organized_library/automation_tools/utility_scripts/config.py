#!/usr/bin/env python3
"""
Configuration Management for Citation Automation System
Centralized configuration for APIs, processing parameters, and system settings
"""

import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import json
import yaml

@dataclass
class APIConfig:
    """API configuration settings"""
    pubmed_api_key: Optional[str] = None
    pubmed_email: Optional[str] = None
    crossref_api_key: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    google_scholar_api_key: Optional[str] = None
    rate_limit_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    batch_size: int = 10

@dataclass
class ProcessingConfig:
    """Processing configuration settings"""
    max_workers: int = 10
    chunk_size: int = 100
    min_citation_quality_score: float = 0.7
    auto_validate_citations: bool = True
    enable_duplicate_detection: bool = True
    enable_abstract_extraction: bool = True
    enable_ml_quality_scoring: bool = True

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    db_type: str = "sqlite"  # sqlite, postgresql, mysql
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "citation_automation"
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_path: str = "citation_automation.db"

@dataclass
class QualityConfig:
    """Quality assessment configuration"""
    enable_impact_factor_scoring: bool = True
    enable_study_design_classification: bool = True
    enable_bias_detection: bool = True
    enable_grade_assessment: bool = True
    min_impact_factor: float = 1.0
    preferred_study_types: List[str] = field(default_factory=lambda: [
        "randomized_controlled_trial",
        "systematic_review", 
        "meta_analysis",
        "cohort_study"
    ])

@dataclass
class SystemConfig:
    """System-wide configuration"""
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_performance_monitoring: bool = True
    enable_health_checks: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = 24

class ConfigManager:
    """Centralized configuration manager"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.yaml")
        self.api = APIConfig()
        self.processing = ProcessingConfig()
        self.database = DatabaseConfig()
        self.quality = QualityConfig()
        self.system = SystemConfig()
        
        self._load_config()
        self._load_environment_variables()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Update configurations
                if 'api' in config_data:
                    self._update_dataclass(self.api, config_data['api'])
                if 'processing' in config_data:
                    self._update_dataclass(self.processing, config_data['processing'])
                if 'database' in config_data:
                    self._update_dataclass(self.database, config_data['database'])
                if 'quality' in config_data:
                    self._update_dataclass(self.quality, config_data['quality'])
                if 'system' in config_data:
                    self._update_dataclass(self.system, config_data['system'])
                    
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")
    
    def _load_environment_variables(self):
        """Load sensitive data from environment variables"""
        # API keys from environment
        self.api.pubmed_api_key = os.getenv('PUBMED_API_KEY', self.api.pubmed_api_key)
        self.api.pubmed_email = os.getenv('PUBMED_EMAIL', self.api.pubmed_email)
        self.api.crossref_api_key = os.getenv('CROSSREF_API_KEY', self.api.crossref_api_key)
        self.api.semantic_scholar_api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY', self.api.semantic_scholar_api_key)
        self.api.google_scholar_api_key = os.getenv('GOOGLE_SCHOLAR_API_KEY', self.api.google_scholar_api_key)
        
        # Database credentials
        self.database.db_user = os.getenv('DB_USER', self.database.db_user)
        self.database.db_password = os.getenv('DB_PASSWORD', self.database.db_password)
        self.database.db_host = os.getenv('DB_HOST', self.database.db_host)
        self.database.db_name = os.getenv('DB_NAME', self.database.db_name)
    
    def _update_dataclass(self, target, source):
        """Update dataclass fields from dictionary"""
        for key, value in source.items():
            if hasattr(target, key):
                setattr(target, key, value)
    
    def save_config(self):
        """Save current configuration to file"""
        config_data = {
            'api': {
                'rate_limit_delay': self.api.rate_limit_delay,
                'max_retries': self.api.max_retries,
                'timeout': self.api.timeout,
                'batch_size': self.api.batch_size
            },
            'processing': {
                'max_workers': self.processing.max_workers,
                'chunk_size': self.processing.chunk_size,
                'min_citation_quality_score': self.processing.min_citation_quality_score,
                'auto_validate_citations': self.processing.auto_validate_citations,
                'enable_duplicate_detection': self.processing.enable_duplicate_detection,
                'enable_abstract_extraction': self.processing.enable_abstract_extraction,
                'enable_ml_quality_scoring': self.processing.enable_ml_quality_scoring
            },
            'database': {
                'db_type': self.database.db_type,
                'db_host': self.database.db_host,
                'db_port': self.database.db_port,
                'db_name': self.database.db_name,
                'db_path': self.database.db_path
            },
            'quality': {
                'enable_impact_factor_scoring': self.quality.enable_impact_factor_scoring,
                'enable_study_design_classification': self.quality.enable_study_design_classification,
                'enable_bias_detection': self.quality.enable_bias_detection,
                'enable_grade_assessment': self.quality.enable_grade_assessment,
                'min_impact_factor': self.quality.min_impact_factor,
                'preferred_study_types': self.quality.preferred_study_types
            },
            'system': {
                'log_level': self.system.log_level,
                'enable_performance_monitoring': self.system.enable_performance_monitoring,
                'enable_health_checks': self.system.enable_health_checks,
                'backup_enabled': self.system.backup_enabled,
                'backup_interval_hours': self.system.backup_interval_hours
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # API validation
        if not self.api.pubmed_email:
            issues.append("PubMed API requires email address")
        
        # Database validation
        if self.database.db_type == "postgresql" and not self.database.db_user:
            issues.append("PostgreSQL requires username")
        
        # Processing validation
        if self.processing.max_workers < 1:
            issues.append("max_workers must be >= 1")
        
        if self.processing.min_citation_quality_score < 0 or self.processing.min_citation_quality_score > 1:
            issues.append("min_citation_quality_score must be between 0 and 1")
        
        return issues

# Global configuration instance
config = ConfigManager()