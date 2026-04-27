#!/usr/bin/env python3
"""
Sophisticated Citation Quality Scoring System
ML-powered quality assessment with GRADE system and bias detection
"""

import asyncio
import aiohttp
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
import json
import re
import logging
from datetime import datetime
import pickle
from pathlib import Path
import hashlib

from research_discovery import ResearchPaper
from config import config

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for a research paper"""
    grade_score: float = 0.0  # GRADE assessment (0-1)
    impact_factor_score: float = 0.0
    study_design_score: float = 0.0
    bias_risk_score: float = 0.0  # Lower is better (0-1)
    methodological_quality: float = 0.0
    sample_size_adequacy: float = 0.0
    statistical_rigor: float = 0.0
    replication_status: float = 0.0
    author_credibility: float = 0.0
    journal_reputation: float = 0.0
    citation_velocity: float = 0.0  # Citations per year since publication
    peer_review_quality: float = 0.0
    data_availability: float = 0.0
    conflict_of_interest_risk: float = 0.0  # Lower is better
    overall_quality: float = 0.0

@dataclass
class BiasAssessment:
    """Risk of bias assessment"""
    selection_bias: str = "unclear"  # high, low, unclear
    performance_bias: str = "unclear"
    detection_bias: str = "unclear"
    attrition_bias: str = "unclear"
    reporting_bias: str = "unclear"
    funding_bias: str = "unclear"
    overall_risk: str = "unclear"
    risk_score: float = 0.5  # 0 = low risk, 1 = high risk

@dataclass
class GRADEAssessment:
    """GRADE (Grading of Recommendations Assessment) evaluation"""
    study_design_quality: int = 0  # Starting points based on study design
    risk_of_bias: int = 0  # -1 or -2 points for serious/very serious bias
    inconsistency: int = 0  # -1 or -2 points for heterogeneity
    indirectness: int = 0  # -1 or -2 points for population/intervention differences  
    imprecision: int = 0  # -1 or -2 points for wide CIs or small sample
    publication_bias: int = 0  # -1 point for suspected bias
    large_effect: int = 0  # +1 or +2 points for large effect sizes
    dose_response: int = 0  # +1 point for dose-response gradient
    confounding: int = 0  # +1 point if confounding would reduce effect
    final_grade: str = "very_low"  # very_low, low, moderate, high
    confidence_score: float = 0.0  # 0-1 confidence in the evidence

class JournalDatabase:
    """Database of journal impact factors and reputation scores"""
    
    def __init__(self):
        self.impact_factors = {}
        self.journal_rankings = {}
        self.predatory_journals = set()
        self._load_journal_data()
    
    def _load_journal_data(self):
        """Load journal database from various sources"""
        # High-impact journals in exercise science and medicine
        high_impact_journals = {
            "Nature": 64.8,
            "Science": 56.9,
            "New England Journal of Medicine": 176.1,
            "The Lancet": 168.9,
            "Cell": 64.5,
            "Medicine & Science in Sports & Exercise": 4.1,
            "Journal of Applied Physiology": 3.3,
            "Sports Medicine": 9.8,
            "International Journal of Sports Physiology and Performance": 3.0,
            "Journal of Strength and Conditioning Research": 3.0,
            "British Journal of Sports Medicine": 18.5,
            "Exercise and Sport Sciences Reviews": 5.2,
            "European Journal of Applied Physiology": 2.8,
            "Journal of Sports Sciences": 3.2,
            "Applied Physiology Nutrition and Metabolism": 2.4,
            "Scandinavian Journal of Medicine & Science in Sports": 4.4,
            "American Journal of Clinical Nutrition": 7.5,
            "Journal of Nutrition": 4.8,
            "Nutrients": 5.7,
            "Clinical Journal of Sport Medicine": 2.3,
            "Journal of Athletic Training": 2.3
        }
        
        self.impact_factors.update(high_impact_journals)
        
        # Predatory journals (sample list - would be expanded)
        predatory_list = {
            "International Journal of Advanced Research",
            "Global Journal of Research",
            "American Journal of Advanced Research"
        }
        
        self.predatory_journals.update(predatory_list)
    
    def get_impact_factor(self, journal_name: str) -> Optional[float]:
        """Get impact factor for a journal"""
        # Normalize journal name
        normalized = self._normalize_journal_name(journal_name)
        return self.impact_factors.get(normalized)
    
    def is_predatory(self, journal_name: str) -> bool:
        """Check if journal is on predatory list"""
        normalized = self._normalize_journal_name(journal_name)
        return normalized in self.predatory_journals
    
    def get_journal_tier(self, journal_name: str) -> str:
        """Get journal quality tier"""
        impact_factor = self.get_impact_factor(journal_name)
        if impact_factor is None:
            return "unknown"
        
        if impact_factor >= 10:
            return "tier_1"
        elif impact_factor >= 5:
            return "tier_2"  
        elif impact_factor >= 2:
            return "tier_3"
        else:
            return "tier_4"
    
    def _normalize_journal_name(self, journal_name: str) -> str:
        """Normalize journal name for matching"""
        # Remove common prefixes/suffixes, normalize case
        normalized = journal_name.lower().strip()
        normalized = re.sub(r'^the\s+', '', normalized)
        normalized = re.sub(r'\s+journal\s*$', '', normalized)
        return normalized.title()

class AuthorCredibilityScorer:
    """Score author credibility based on publication history and affiliations"""
    
    def __init__(self):
        self.author_cache = {}
        self.institution_rankings = self._load_institution_rankings()
    
    def _load_institution_rankings(self) -> Dict[str, float]:
        """Load university/institution rankings"""
        # Top institutions in exercise science/medicine (sample)
        return {
            "Harvard University": 1.0,
            "Stanford University": 1.0,
            "MIT": 1.0,
            "University of Cambridge": 0.95,
            "University of Oxford": 0.95,
            "Mayo Clinic": 0.9,
            "Johns Hopkins": 0.9,
            "University of Copenhagen": 0.85,
            "Australian Catholic University": 0.8,  # High in exercise science
            "University of Birmingham": 0.75,
            "McMaster University": 0.75
        }
    
    async def score_authors(self, paper: ResearchPaper) -> float:
        """Score author credibility for a paper"""
        if not paper.authors:
            return 0.3  # Default low score
        
        author_scores = []
        for author in paper.authors[:5]:  # Limit to first 5 authors
            score = await self._score_individual_author(author, paper)
            author_scores.append(score)
        
        # Weight first author more heavily
        if len(author_scores) == 1:
            return author_scores[0]
        elif len(author_scores) >= 2:
            return (author_scores[0] * 0.4 + author_scores[-1] * 0.3 + 
                   sum(author_scores[1:-1]) * 0.3 / max(1, len(author_scores) - 2))
        
        return sum(author_scores) / len(author_scores)
    
    async def _score_individual_author(self, author: str, paper: ResearchPaper) -> float:
        """Score individual author credibility"""
        # Check cache first
        if author in self.author_cache:
            return self.author_cache[author]
        
        score = 0.5  # Default score
        
        # Extract institution from paper if available
        # (This would typically require additional API calls or data)
        
        # For now, use a simple heuristic based on common patterns
        if self._is_likely_established_researcher(author):
            score += 0.2
        
        # Cache the result
        self.author_cache[author] = score
        return score
    
    def _is_likely_established_researcher(self, author: str) -> bool:
        """Simple heuristic to identify established researchers"""
        # Look for middle initials, multiple names, etc.
        name_parts = author.split()
        return len(name_parts) >= 3 or any(len(part) == 1 for part in name_parts[1:-1])

class BiasDetector:
    """Detect various types of bias in research papers"""
    
    def __init__(self):
        # Bias detection patterns
        self.funding_bias_patterns = [
            r'funded by.*pharmaceutical',
            r'sponsored by.*industry',
            r'conflict of interest',
            r'financial interest',
            r'stock options',
            r'consultant.*company'
        ]
        
        self.selection_bias_patterns = [
            r'convenience sample',
            r'volunteer sample',
            r'self-selected',
            r'non-random',
            r'purposive sampling'
        ]
        
        self.reporting_bias_patterns = [
            r'post-hoc analysis',
            r'exploratory analysis',
            r'data mining',
            r'p-hacking',
            r'selective reporting'
        ]
    
    def assess_bias_risk(self, paper: ResearchPaper) -> BiasAssessment:
        """Comprehensive bias risk assessment"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        assessment = BiasAssessment()
        
        # Selection bias
        assessment.selection_bias = self._assess_selection_bias(text)
        
        # Performance bias (blinding)
        assessment.performance_bias = self._assess_performance_bias(text)
        
        # Detection bias (outcome assessment)
        assessment.detection_bias = self._assess_detection_bias(text)
        
        # Attrition bias (dropout)
        assessment.attrition_bias = self._assess_attrition_bias(text)
        
        # Reporting bias
        assessment.reporting_bias = self._assess_reporting_bias(text)
        
        # Funding bias
        assessment.funding_bias = self._assess_funding_bias(text, paper)
        
        # Overall risk assessment
        assessment.overall_risk = self._calculate_overall_risk(assessment)
        assessment.risk_score = self._calculate_risk_score(assessment)
        
        return assessment
    
    def _assess_selection_bias(self, text: str) -> str:
        """Assess selection bias risk"""
        if 'randomized' in text and 'controlled' in text:
            return "low"
        elif any(re.search(pattern, text) for pattern in self.selection_bias_patterns):
            return "high"
        else:
            return "unclear"
    
    def _assess_performance_bias(self, text: str) -> str:
        """Assess performance bias (blinding)"""
        blinding_indicators = ['blind', 'masked', 'placebo']
        if any(indicator in text for indicator in blinding_indicators):
            if 'double' in text:
                return "low"
            elif 'single' in text:
                return "moderate" 
            else:
                return "unclear"
        return "high"
    
    def _assess_detection_bias(self, text: str) -> str:
        """Assess detection bias"""
        objective_measures = ['dxa', 'mri', 'ct scan', 'laboratory', 'biochemical']
        if any(measure in text for measure in objective_measures):
            return "low"
        elif 'self-report' in text or 'questionnaire' in text:
            return "high"
        else:
            return "unclear"
    
    def _assess_attrition_bias(self, text: str) -> str:
        """Assess attrition bias"""
        if 'dropout' in text or 'withdrawal' in text:
            if 'intention to treat' in text or 'itt' in text:
                return "low"
            else:
                return "high"
        return "unclear"
    
    def _assess_reporting_bias(self, text: str) -> str:
        """Assess selective reporting bias"""
        if any(re.search(pattern, text) for pattern in self.reporting_bias_patterns):
            return "high"
        elif 'protocol' in text or 'registered' in text:
            return "low"
        else:
            return "unclear"
    
    def _assess_funding_bias(self, text: str, paper: ResearchPaper) -> str:
        """Assess funding-related bias"""
        if any(re.search(pattern, text) for pattern in self.funding_bias_patterns):
            return "high"
        elif 'no conflict' in text or 'no funding' in text:
            return "low"
        else:
            return "unclear"
    
    def _calculate_overall_risk(self, assessment: BiasAssessment) -> str:
        """Calculate overall bias risk"""
        risks = [
            assessment.selection_bias,
            assessment.performance_bias, 
            assessment.detection_bias,
            assessment.attrition_bias,
            assessment.reporting_bias,
            assessment.funding_bias
        ]
        
        high_risk_count = risks.count("high")
        low_risk_count = risks.count("low")
        
        if high_risk_count >= 3:
            return "high"
        elif high_risk_count >= 1 and low_risk_count < 3:
            return "moderate"
        elif low_risk_count >= 4:
            return "low"
        else:
            return "unclear"
    
    def _calculate_risk_score(self, assessment: BiasAssessment) -> float:
        """Calculate numerical risk score (0 = low risk, 1 = high risk)"""
        risk_values = {
            "low": 0.0,
            "moderate": 0.3,
            "unclear": 0.5,
            "high": 1.0
        }
        
        risks = [
            assessment.selection_bias,
            assessment.performance_bias,
            assessment.detection_bias, 
            assessment.attrition_bias,
            assessment.reporting_bias,
            assessment.funding_bias
        ]
        
        risk_scores = [risk_values.get(risk, 0.5) for risk in risks]
        return sum(risk_scores) / len(risk_scores)

class GRADEAssessor:
    """GRADE system implementation for evidence quality assessment"""
    
    def __init__(self):
        self.study_design_points = {
            'meta_analysis': 4,
            'systematic_review': 4,
            'randomized_controlled_trial': 4,
            'cohort_study': 2,
            'case_control': 2,
            'cross_sectional': 1,
            'case_study': 1,
            'review': 1
        }
    
    def assess_grade(self, paper: ResearchPaper, bias_assessment: BiasAssessment,
                    quality_metrics: QualityMetrics) -> GRADEAssessment:
        """Perform GRADE assessment"""
        grade = GRADEAssessment()
        
        # Starting points based on study design
        grade.study_design_quality = self.study_design_points.get(paper.study_type, 1)
        
        # Risk of bias downgrading
        if bias_assessment.overall_risk == "high":
            grade.risk_of_bias = -2
        elif bias_assessment.overall_risk == "moderate":
            grade.risk_of_bias = -1
        
        # Inconsistency (would require multiple studies)
        grade.inconsistency = 0  # Cannot assess from single paper
        
        # Indirectness assessment
        grade.indirectness = self._assess_indirectness(paper)
        
        # Imprecision assessment
        grade.imprecision = self._assess_imprecision(paper)
        
        # Publication bias (cannot assess from single paper)
        grade.publication_bias = 0
        
        # Large effect upgrading
        grade.large_effect = self._assess_effect_size(paper)
        
        # Dose-response upgrading  
        grade.dose_response = self._assess_dose_response(paper)
        
        # Confounding upgrading
        grade.confounding = self._assess_confounding(paper)
        
        # Calculate final grade
        total_points = (grade.study_design_quality + grade.risk_of_bias + 
                       grade.inconsistency + grade.indirectness + grade.imprecision +
                       grade.publication_bias + grade.large_effect + 
                       grade.dose_response + grade.confounding)
        
        if total_points >= 4:
            grade.final_grade = "high"
            grade.confidence_score = 0.85
        elif total_points >= 3:
            grade.final_grade = "moderate"
            grade.confidence_score = 0.65
        elif total_points >= 2:
            grade.final_grade = "low"
            grade.confidence_score = 0.35
        else:
            grade.final_grade = "very_low"
            grade.confidence_score = 0.15
        
        return grade
    
    def _assess_indirectness(self, paper: ResearchPaper) -> int:
        """Assess indirectness of evidence"""
        # Simple heuristic - would need more sophisticated analysis
        text = f"{paper.title} {paper.abstract}".lower()
        
        # Look for specific populations or interventions
        if any(term in text for term in ['elderly', 'children', 'disease', 'patient']):
            return -1  # May be indirect for general population
        
        return 0
    
    def _assess_imprecision(self, paper: ResearchPaper) -> int:
        """Assess precision of results"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        # Look for confidence intervals, sample size mentions
        if 'confidence interval' in text or 'ci' in text:
            if 'wide' in text:
                return -1
            return 0
        
        # Look for sample size indicators
        sample_size_match = re.search(r'n\s*=\s*(\d+)', text)
        if sample_size_match:
            n = int(sample_size_match.group(1))
            if n < 50:
                return -2
            elif n < 100:
                return -1
        
        return -1  # Default to imprecise if unclear
    
    def _assess_effect_size(self, paper: ResearchPaper) -> int:
        """Assess magnitude of effect"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        # Look for effect size indicators
        large_effects = ['large effect', 'substantial', 'dramatic', 'marked increase']
        if any(effect in text for effect in large_effects):
            return 1
        
        # Look for statistical significance with large differences
        if re.search(r'(\d+)%.*increase|improve', text):
            percentages = re.findall(r'(\d+)%', text)
            if percentages and max(int(p) for p in percentages) > 25:
                return 1
        
        return 0
    
    def _assess_dose_response(self, paper: ResearchPaper) -> int:
        """Assess dose-response relationship"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        dose_indicators = ['dose', 'duration', 'frequency', 'intensity', 'volume']
        response_indicators = ['response', 'relationship', 'correlation', 'gradient']
        
        if (any(dose in text for dose in dose_indicators) and 
            any(response in text for response in response_indicators)):
            return 1
        
        return 0
    
    def _assess_confounding(self, paper: ResearchPaper) -> int:
        """Assess if confounding would reduce observed effect"""
        # This is complex and would require domain expertise
        # For now, return 0 (no upgrading)
        return 0

class QualityScorer:
    """Main quality scoring system coordinator"""
    
    def __init__(self):
        self.journal_db = JournalDatabase()
        self.author_scorer = AuthorCredibilityScorer()
        self.bias_detector = BiasDetector()
        self.grade_assessor = GRADEAssessor()
        self.ml_model = None  # Would load trained ML model
        
    async def score_paper_quality(self, paper: ResearchPaper) -> Tuple[QualityMetrics, BiasAssessment, GRADEAssessment]:
        """Comprehensive quality scoring for a research paper"""
        logger.info(f"Scoring quality for: {paper.title[:50]}...")
        
        # Initialize metrics
        metrics = QualityMetrics()
        
        # Bias assessment
        bias_assessment = self.bias_detector.assess_bias_risk(paper)
        metrics.bias_risk_score = bias_assessment.risk_score
        
        # Impact factor scoring
        metrics.impact_factor_score = self._score_impact_factor(paper)
        
        # Study design scoring
        metrics.study_design_score = self._score_study_design(paper)
        
        # Author credibility
        metrics.author_credibility = await self.author_scorer.score_authors(paper)
        
        # Journal reputation
        metrics.journal_reputation = self._score_journal_reputation(paper)
        
        # Citation velocity
        metrics.citation_velocity = self._calculate_citation_velocity(paper)
        
        # Methodological quality
        metrics.methodological_quality = self._assess_methodological_quality(paper)
        
        # Sample size adequacy
        metrics.sample_size_adequacy = self._assess_sample_size(paper)
        
        # Statistical rigor
        metrics.statistical_rigor = self._assess_statistical_rigor(paper)
        
        # Data availability
        metrics.data_availability = self._assess_data_availability(paper)
        
        # Conflict of interest
        metrics.conflict_of_interest_risk = self._assess_conflict_of_interest(paper)
        
        # GRADE assessment
        grade_assessment = self.grade_assessor.assess_grade(paper, bias_assessment, metrics)
        metrics.grade_score = grade_assessment.confidence_score
        
        # Calculate overall quality score
        metrics.overall_quality = self._calculate_overall_quality(metrics)
        
        return metrics, bias_assessment, grade_assessment
    
    def _score_impact_factor(self, paper: ResearchPaper) -> float:
        """Score based on journal impact factor"""
        impact_factor = self.journal_db.get_impact_factor(paper.journal)
        if impact_factor is None:
            return 0.5  # Default for unknown journals
        
        # Normalize to 0-1 scale (log scale for impact factors)
        import math
        normalized = min(math.log(impact_factor + 1) / math.log(100), 1.0)
        
        # Penalty for predatory journals
        if self.journal_db.is_predatory(paper.journal):
            normalized *= 0.1
        
        return normalized
    
    def _score_study_design(self, paper: ResearchPaper) -> float:
        """Score based on study design hierarchy"""
        design_scores = {
            'meta_analysis': 1.0,
            'systematic_review': 0.9,
            'randomized_controlled_trial': 0.85,
            'cohort_study': 0.7,
            'case_control': 0.6,
            'cross_sectional': 0.5,
            'case_study': 0.2,
            'review': 0.4
        }
        
        return design_scores.get(paper.study_type, 0.5)
    
    def _score_journal_reputation(self, paper: ResearchPaper) -> float:
        """Score journal reputation"""
        tier_scores = {
            'tier_1': 1.0,
            'tier_2': 0.8,
            'tier_3': 0.6,
            'tier_4': 0.4,
            'unknown': 0.5
        }
        
        tier = self.journal_db.get_journal_tier(paper.journal)
        return tier_scores.get(tier, 0.5)
    
    def _calculate_citation_velocity(self, paper: ResearchPaper) -> float:
        """Calculate citations per year since publication"""
        if not paper.citation_count or not paper.publication_date:
            return 0.0
        
        try:
            pub_year = int(paper.publication_date[:4])
            current_year = datetime.now().year
            years_since_pub = max(current_year - pub_year, 1)
            
            velocity = paper.citation_count / years_since_pub
            # Normalize to 0-1 scale (log scale)
            import math
            return min(math.log(velocity + 1) / math.log(50), 1.0)
            
        except (ValueError, TypeError):
            return 0.0
    
    def _assess_methodological_quality(self, paper: ResearchPaper) -> float:
        """Assess methodological quality from abstract"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        quality_indicators = [
            'randomized', 'controlled', 'blinded', 'placebo',
            'power analysis', 'sample size calculation',
            'intention to treat', 'per protocol',
            'confidence interval', 'effect size',
            'statistical significance', 'p-value'
        ]
        
        matched_indicators = sum(1 for indicator in quality_indicators if indicator in text)
        return min(matched_indicators / len(quality_indicators), 1.0)
    
    def _assess_sample_size(self, paper: ResearchPaper) -> float:
        """Assess adequacy of sample size"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        # Look for sample size mentions
        sample_patterns = [r'n\s*=\s*(\d+)', r'(\d+)\s*participants', r'(\d+)\s*subjects']
        
        for pattern in sample_patterns:
            match = re.search(pattern, text)
            if match:
                n = int(match.group(1))
                
                # Score based on sample size adequacy
                if n >= 100:
                    return 1.0
                elif n >= 50:
                    return 0.8
                elif n >= 30:
                    return 0.6
                elif n >= 15:
                    return 0.4
                else:
                    return 0.2
        
        return 0.3  # Default if no sample size found
    
    def _assess_statistical_rigor(self, paper: ResearchPaper) -> float:
        """Assess statistical analysis rigor"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        statistical_indicators = [
            'anova', 'regression', 'correlation', 'chi-square',
            'mann-whitney', 'kruskal-wallis', 'wilcoxon',
            'bonferroni', 'benjamini', 'false discovery',
            'confidence interval', 'effect size',
            'cohen\'s d', 'eta squared', 'odds ratio'
        ]
        
        matched_indicators = sum(1 for indicator in statistical_indicators if indicator in text)
        return min(matched_indicators / 5, 1.0)  # Normalize to 0-1
    
    def _assess_data_availability(self, paper: ResearchPaper) -> float:
        """Assess data availability and transparency"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        data_indicators = [
            'data available', 'supplementary data', 'raw data',
            'github', 'figshare', 'dryad', 'osf',
            'open access', 'reproducible'
        ]
        
        if any(indicator in text for indicator in data_indicators):
            return 1.0
        else:
            return 0.3  # Default low score
    
    def _assess_conflict_of_interest(self, paper: ResearchPaper) -> float:
        """Assess conflict of interest risk"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        coi_indicators = [
            'conflict of interest', 'financial interest',
            'funded by.*pharmaceutical', 'sponsored by.*industry',
            'consultant.*company', 'stock options',
            'patent', 'royalties'
        ]
        
        high_risk_indicators = sum(1 for indicator in coi_indicators if re.search(indicator, text))
        
        if 'no conflict' in text or 'no competing interest' in text:
            return 0.1  # Low risk
        elif high_risk_indicators > 0:
            return min(high_risk_indicators * 0.3, 1.0)  # High risk
        else:
            return 0.5  # Unknown/unclear
    
    def _calculate_overall_quality(self, metrics: QualityMetrics) -> float:
        """Calculate weighted overall quality score"""
        # Weighted combination of all metrics
        weights = {
            'grade_score': 0.25,
            'study_design_score': 0.20,
            'bias_risk_score': -0.15,  # Negative weight (lower bias = higher quality)
            'impact_factor_score': 0.10,
            'methodological_quality': 0.15,
            'author_credibility': 0.08,
            'journal_reputation': 0.07,
            'statistical_rigor': 0.10
        }
        
        overall = 0.0
        for metric, weight in weights.items():
            value = getattr(metrics, metric, 0.0)
            overall += weight * value
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, overall))

async def main():
    """Test the quality scoring system"""
    from research_discovery import ResearchPaper
    
    # Test paper
    paper = ResearchPaper(
        title="Effects of High-Intensity Interval Training on Cardiovascular Health: A Randomized Controlled Trial",
        authors=["Smith, J.A.", "Johnson, B.C.", "Williams, D.E."],
        abstract="Background: High-intensity interval training (HIIT) has shown promise for improving cardiovascular health. This randomized controlled trial examined the effects of 12 weeks of HIIT on VO2max and cardiac function in 120 healthy adults. Methods: Participants were randomly assigned to HIIT (n=60) or control (n=60) groups. HIIT consisted of 4x4-minute intervals at 85-95% HRmax. Results: HIIT group showed significant improvements in VO2max (15.3%, p<0.001) and left ventricular function compared to controls. Conclusion: HIIT is effective for improving cardiovascular health markers.",
        journal="Medicine & Science in Sports & Exercise",
        publication_date="2023-06-01",
        doi="10.1249/MSS.0000000000003123",
        citation_count=25,
        study_type="randomized_controlled_trial"
    )
    
    scorer = QualityScorer()
    metrics, bias, grade = await scorer.score_paper_quality(paper)
    
    print(f"Quality Assessment for: {paper.title}")
    print(f"Overall Quality: {metrics.overall_quality:.3f}")
    print(f"GRADE: {grade.final_grade} (confidence: {grade.confidence_score:.3f})")
    print(f"Bias Risk: {bias.overall_risk} (score: {bias.risk_score:.3f})")
    print(f"Study Design: {metrics.study_design_score:.3f}")
    print(f"Impact Factor: {metrics.impact_factor_score:.3f}")
    print(f"Methodological Quality: {metrics.methodological_quality:.3f}")

if __name__ == "__main__":
    asyncio.run(main())