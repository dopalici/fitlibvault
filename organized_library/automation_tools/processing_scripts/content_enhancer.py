#!/usr/bin/env python3
"""
Intelligent Content Enhancement Engine
Context-aware citation suggestions, content optimization, and automated fact-checking
"""

import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
from datetime import datetime
import hashlib
import difflib

from research_discovery import ResearchDiscoveryEngine, SearchQuery, ResearchPaper
from quality_scorer import QualityScorer, QualityMetrics
from config import config

logger = logging.getLogger(__name__)

@dataclass
class ContentSection:
    """Represents a section of content"""
    title: str
    content: str
    section_type: str  # introduction, methods, results, discussion, etc.
    citations: List[str] = field(default_factory=list)
    key_claims: List[str] = field(default_factory=list)
    citation_density: float = 0.0
    needs_citations: bool = False

@dataclass
class CitationSuggestion:
    """Citation suggestion for content"""
    paper: ResearchPaper
    relevance_score: float
    suggested_location: str
    context_snippet: str
    justification: str
    citation_type: str  # supporting, contrasting, methodology, background

@dataclass
class ContentEnhancement:
    """Content enhancement recommendations"""
    original_content: str
    enhanced_content: str
    citation_suggestions: List[CitationSuggestion]
    fact_check_results: List[Dict]
    quality_improvements: List[str]
    structure_improvements: List[str]
    readability_score: float
    citation_density_score: float
    overall_improvement_score: float

class ContentAnalyzer:
    """Analyze content structure and extract key information"""
    
    def __init__(self):
        self.section_patterns = {
            'introduction': [r'introduction', r'background', r'rationale'],
            'methods': [r'methods?', r'methodology', r'procedure', r'protocol'],
            'results': [r'results?', r'findings', r'outcomes'],
            'discussion': [r'discussion', r'implications', r'conclusion'],
            'abstract': [r'abstract', r'summary'],
            'quick_takeaway': [r'quick takeaway', r'key point'],
            'deep_dive': [r'deep dive', r'detailed analysis']
        }
    
    def parse_content(self, content: str) -> List[ContentSection]:
        """Parse content into sections"""
        sections = []
        
        # Split by headers
        header_pattern = r'^#{1,6}\s+(.+)$'
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous section
                if current_section:
                    section = ContentSection(
                        title=current_section,
                        content='\n'.join(current_content).strip(),
                        section_type=self._classify_section(current_section)
                    )
                    section.citations = self._extract_citations(section.content)
                    section.key_claims = self._extract_key_claims(section.content)
                    section.citation_density = self._calculate_citation_density(section.content)
                    section.needs_citations = self._assess_citation_needs(section)
                    sections.append(section)
                
                # Start new section
                current_section = header_match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_section:
            section = ContentSection(
                title=current_section,
                content='\n'.join(current_content).strip(),
                section_type=self._classify_section(current_section)
            )
            section.citations = self._extract_citations(section.content)
            section.key_claims = self._extract_key_claims(section.content)
            section.citation_density = self._calculate_citation_density(section.content)
            section.needs_citations = self._assess_citation_needs(section)
            sections.append(section)
        
        return sections
    
    def _classify_section(self, title: str) -> str:
        """Classify section type based on title"""
        title_lower = title.lower()
        
        for section_type, patterns in self.section_patterns.items():
            if any(re.search(pattern, title_lower) for pattern in patterns):
                return section_type
        
        return 'other'
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract existing citations from content"""
        # DOI citations
        doi_pattern = r'DOI:\s*(https://doi\.org/[^\s\)]+)'
        dois = re.findall(doi_pattern, content)
        
        # PMID citations
        pmid_pattern = r'PMID:\s*(https://pubmed\.ncbi\.nlm\.nih\.gov/\d+)'
        pmids = re.findall(pmid_pattern, content)
        
        # Author-year citations
        author_pattern = r'([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?)\s*\((\d{4})\)'
        authors = [f"{match[0]} ({match[1]})" for match in re.findall(author_pattern, content)]
        
        return dois + pmids + authors
    
    def _extract_key_claims(self, content: str) -> List[str]:
        """Extract key factual claims that need citations"""
        claims = []
        
        # Sentences with quantitative claims
        quant_patterns = [
            r'[^.!?]*\d+(?:\.\d+)?%[^.!?]*[.!?]',  # Percentage claims
            r'[^.!?]*\d+(?:\.\d+)?\s*(?:fold|times|x)[^.!?]*[.!?]',  # Fold changes
            r'[^.!?]*(?:increase|decrease|improve|reduce)[^.!?]*\d+(?:\.\d+)?[^.!?]*[.!?]',  # Change claims
            r'[^.!?]*significantly[^.!?]*[.!?]',  # Significance claims
        ]
        
        for pattern in quant_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            claims.extend([match.strip() for match in matches])
        
        # Causal/mechanism claims
        causal_patterns = [
            r'[^.!?]*(?:causes?|leads? to|results? in|due to)[^.!?]*[.!?]',
            r'[^.!?]*mechanism[^.!?]*[.!?]',
            r'[^.!?]*(?:enhances?|improves?|increases?|decreases?)[^.!?]*[.!?]'
        ]
        
        for pattern in causal_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            claims.extend([match.strip() for match in matches])
        
        return list(set(claims))  # Remove duplicates
    
    def _calculate_citation_density(self, content: str) -> float:
        """Calculate citation density (citations per 100 words)"""
        word_count = len(content.split())
        citation_count = len(self._extract_citations(content))
        
        if word_count == 0:
            return 0.0
        
        return (citation_count / word_count) * 100
    
    def _assess_citation_needs(self, section: ContentSection) -> bool:
        """Assess if section needs more citations"""
        # Sections that typically need citations
        citation_heavy_sections = ['introduction', 'discussion', 'results', 'deep_dive']
        
        if section.section_type in citation_heavy_sections:
            # Check if has claims but low citation density
            if section.key_claims and section.citation_density < 2.0:  # Less than 2 citations per 100 words
                return True
            
            # Check for specific claim types that need citations
            content_lower = section.content.lower()
            needs_citation_indicators = [
                'research shows', 'studies indicate', 'evidence suggests',
                'significantly', 'proven', 'demonstrated'
            ]
            
            if any(indicator in content_lower for indicator in needs_citation_indicators):
                return len(section.citations) == 0
        
        return False

class ContextAwareCitationEngine:
    """Generate context-aware citation suggestions"""
    
    def __init__(self):
        self.research_engine = ResearchDiscoveryEngine()
        self.quality_scorer = QualityScorer()
        self.concept_cache = {}
        
    async def suggest_citations(self, section: ContentSection, context_sections: List[ContentSection]) -> List[CitationSuggestion]:
        """Generate citation suggestions for a content section"""
        if not section.needs_citations:
            return []
        
        logger.info(f"Generating citation suggestions for: {section.title}")
        
        # Extract key concepts and search terms
        search_terms = self._extract_search_terms(section, context_sections)
        
        # Search for relevant papers
        papers = await self._search_relevant_papers(search_terms)
        
        # Score and rank papers
        scored_papers = await self._score_paper_relevance(papers, section)
        
        # Generate specific suggestions
        suggestions = []
        for paper, relevance_score in scored_papers[:10]:  # Top 10
            suggestion = await self._create_citation_suggestion(paper, section, relevance_score)
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    def _extract_search_terms(self, section: ContentSection, context_sections: List[ContentSection]) -> List[str]:
        """Extract search terms from content"""
        text = section.content
        
        # Add context from other sections
        for ctx_section in context_sections:
            if ctx_section.section_type in ['introduction', 'abstract']:
                text += " " + ctx_section.content
        
        # Extract key terms using various methods
        terms = set()
        
        # Medical/scientific terms (capitalized phrases)
        scientific_terms = re.findall(r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b', text)
        terms.update(term for term in scientific_terms if len(term.split()) <= 3)
        
        # Fitness/exercise specific terms
        fitness_terms = [
            'resistance training', 'strength training', 'hypertrophy', 'muscle growth',
            'cardiovascular', 'aerobic', 'anaerobic', 'HIIT', 'interval training',
            'nutrition', 'protein', 'carbohydrate', 'recovery', 'adaptation',
            'performance', 'endurance', 'power', 'force', 'velocity'
        ]
        
        for term in fitness_terms:
            if term.lower() in text.lower():
                terms.add(term)
        
        # Extract noun phrases (simplified)
        noun_phrases = re.findall(r'\b(?:the\s+)?[a-z]+(?:\s+[a-z]+)*(?=\s+(?:is|are|was|were|can|may|will|show|indicate|suggest))', text.lower())
        terms.update(phrase for phrase in noun_phrases if 2 <= len(phrase.split()) <= 4)
        
        return list(terms)[:10]  # Limit to top 10 terms
    
    async def _search_relevant_papers(self, search_terms: List[str]) -> List[ResearchPaper]:
        """Search for papers relevant to the search terms"""
        all_papers = []
        
        # Search with different term combinations
        term_combinations = [
            search_terms[:3],  # Top 3 terms
            search_terms[1:4],  # Terms 2-4
            [search_terms[0]] if search_terms else []  # Most important term
        ]
        
        for terms in term_combinations:
            if not terms:
                continue
                
            query = SearchQuery(
                terms=terms,
                max_results=30,
                min_quality_score=0.6,
                date_range=("2018-01-01", "2024-12-31")  # Recent papers
            )
            
            papers = await self.research_engine.discover_papers(query)
            all_papers.extend(papers)
        
        # Deduplicate
        seen_dois = set()
        seen_titles = set()
        unique_papers = []
        
        for paper in all_papers:
            # Check DOI
            if paper.doi and paper.doi in seen_dois:
                continue
            elif paper.doi:
                seen_dois.add(paper.doi)
            
            # Check title similarity
            title_key = self._normalize_title(paper.title)
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            unique_papers.append(paper)
        
        return unique_papers
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        return ' '.join(normalized.split())
    
    async def _score_paper_relevance(self, papers: List[ResearchPaper], section: ContentSection) -> List[Tuple[ResearchPaper, float]]:
        """Score papers for relevance to the section"""
        scored_papers = []
        
        for paper in papers:
            relevance = self._calculate_section_relevance(paper, section)
            if relevance > 0.3:  # Only include reasonably relevant papers
                scored_papers.append((paper, relevance))
        
        # Sort by relevance
        scored_papers.sort(key=lambda x: x[1], reverse=True)
        
        return scored_papers
    
    def _calculate_section_relevance(self, paper: ResearchPaper, section: ContentSection) -> float:
        """Calculate how relevant a paper is to a specific section"""
        paper_text = f"{paper.title} {paper.abstract}".lower()
        section_text = section.content.lower()
        
        # Term overlap
        paper_terms = set(re.findall(r'\b\w+\b', paper_text))
        section_terms = set(re.findall(r'\b\w+\b', section_text))
        
        if not section_terms:
            return 0.0
        
        overlap = len(paper_terms.intersection(section_terms))
        term_relevance = overlap / len(section_terms)
        
        # Boost for specific matches
        key_phrases = section.key_claims[:5]  # Top 5 key claims
        phrase_matches = 0
        
        for claim in key_phrases:
            claim_terms = set(re.findall(r'\b\w+\b', claim.lower()))
            if claim_terms.intersection(paper_terms):
                phrase_matches += 1
        
        phrase_relevance = phrase_matches / max(len(key_phrases), 1)
        
        # Study type relevance
        study_type_boost = 1.0
        if section.section_type == 'methods' and paper.study_type in ['randomized_controlled_trial', 'systematic_review']:
            study_type_boost = 1.2
        elif section.section_type == 'introduction' and paper.study_type in ['review', 'meta_analysis']:
            study_type_boost = 1.1
        
        # Recency boost
        recency_boost = 1.0
        if paper.publication_date:
            try:
                pub_year = int(paper.publication_date[:4])
                years_old = datetime.now().year - pub_year
                if years_old <= 2:
                    recency_boost = 1.2
                elif years_old <= 5:
                    recency_boost = 1.1
            except:
                pass
        
        # Quality boost
        quality_boost = 1.0 + (paper.quality_score * 0.3)
        
        relevance = (term_relevance * 0.4 + phrase_relevance * 0.6) * study_type_boost * recency_boost * quality_boost
        
        return min(relevance, 1.0)
    
    async def _create_citation_suggestion(self, paper: ResearchPaper, section: ContentSection, relevance_score: float) -> Optional[CitationSuggestion]:
        """Create a specific citation suggestion"""
        # Find the best location in the section to add the citation
        location, context = self._find_citation_location(paper, section)
        
        if not location:
            return None
        
        # Determine citation type
        citation_type = self._determine_citation_type(paper, section, context)
        
        # Create justification
        justification = self._create_citation_justification(paper, section, citation_type)
        
        return CitationSuggestion(
            paper=paper,
            relevance_score=relevance_score,
            suggested_location=location,
            context_snippet=context,
            justification=justification,
            citation_type=citation_type
        )
    
    def _find_citation_location(self, paper: ResearchPaper, section: ContentSection) -> Tuple[Optional[str], Optional[str]]:
        """Find the best location to insert a citation"""
        sentences = re.split(r'[.!?]+', section.content)
        paper_terms = set(re.findall(r'\b\w+\b', f"{paper.title} {paper.abstract}".lower()))
        
        best_sentence = None
        best_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            sentence_terms = set(re.findall(r'\b\w+\b', sentence.lower()))
            overlap = len(sentence_terms.intersection(paper_terms))
            
            # Boost for sentences that need citations
            needs_citation_indicators = [
                'research shows', 'studies indicate', 'evidence suggests',
                'significantly', 'demonstrated', 'proven', 'shown to'
            ]
            
            citation_boost = 1.0
            if any(indicator in sentence.lower() for indicator in needs_citation_indicators):
                citation_boost = 2.0
            
            score = overlap * citation_boost
            
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        if best_sentence and best_score > 0:
            return best_sentence[:100] + "...", best_sentence
        
        return None, None
    
    def _determine_citation_type(self, paper: ResearchPaper, section: ContentSection, context: str) -> str:
        """Determine the type of citation relationship"""
        context_lower = context.lower() if context else ""
        paper_text = f"{paper.title} {paper.abstract}".lower()
        
        # Supporting evidence
        if any(term in context_lower for term in ['shows', 'demonstrates', 'indicates', 'evidence', 'supports']):
            return 'supporting'
        
        # Methodology
        if section.section_type == 'methods' or 'method' in context_lower:
            return 'methodology'
        
        # Background/introduction
        if section.section_type == 'introduction' or any(term in context_lower for term in ['background', 'previously', 'prior']):
            return 'background'
        
        # Contrasting findings
        if any(term in context_lower for term in ['however', 'contrast', 'different', 'but']):
            return 'contrasting'
        
        return 'supporting'  # Default
    
    def _create_citation_justification(self, paper: ResearchPaper, section: ContentSection, citation_type: str) -> str:
        """Create a justification for the citation suggestion"""
        justifications = {
            'supporting': f"This {paper.study_type or 'study'} provides supporting evidence for the claims in this section.",
            'methodology': f"This paper describes relevant methodology that could strengthen the methods discussion.",
            'background': f"This {paper.study_type or 'study'} provides important background context.",
            'contrasting': f"This study presents contrasting findings that should be acknowledged."
        }
        
        base = justifications.get(citation_type, "This study is relevant to the section content.")
        
        # Add quality indicators
        if paper.quality_score > 0.8:
            base += f" High-quality study (quality score: {paper.quality_score:.2f})."
        
        if paper.citation_count and paper.citation_count > 50:
            base += f" Well-cited paper ({paper.citation_count} citations)."
        
        return base

class FactChecker:
    """Automated fact-checking against research literature"""
    
    def __init__(self):
        self.research_engine = ResearchDiscoveryEngine()
        self.fact_cache = {}
    
    async def check_facts(self, content: str) -> List[Dict]:
        """Check factual claims in content"""
        # Extract quantitative claims
        claims = self._extract_factual_claims(content)
        
        fact_check_results = []
        for claim in claims:
            result = await self._verify_claim(claim)
            if result:
                fact_check_results.append(result)
        
        return fact_check_results
    
    def _extract_factual_claims(self, content: str) -> List[str]:
        """Extract factual claims that can be verified"""
        claims = []
        
        # Quantitative claims
        quant_patterns = [
            r'[^.!?]*\d+(?:\.\d+)?%\s*(?:increase|decrease|improvement|reduction)[^.!?]*[.!?]',
            r'[^.!?]*(?:increases?|improves?|enhances?)[^.!?]*\d+(?:\.\d+)?%[^.!?]*[.!?]',
            r'[^.!?]*\d+\s*(?:fold|times)\s*(?:higher|lower|greater|increase)[^.!?]*[.!?]'
        ]
        
        for pattern in quant_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            claims.extend(matches)
        
        return [claim.strip() for claim in claims if len(claim.strip()) > 20]
    
    async def _verify_claim(self, claim: str) -> Optional[Dict]:
        """Verify a specific claim against literature"""
        # Extract key terms from claim
        terms = self._extract_claim_terms(claim)
        
        # Search for relevant papers
        query = SearchQuery(
            terms=terms,
            max_results=20,
            min_quality_score=0.7
        )
        
        papers = await self.research_engine.discover_papers(query)
        
        # Analyze evidence
        supporting_papers = []
        contradicting_papers = []
        
        for paper in papers:
            relevance = self._calculate_claim_relevance(claim, paper)
            if relevance > 0.6:
                if self._supports_claim(claim, paper):
                    supporting_papers.append(paper)
                elif self._contradicts_claim(claim, paper):
                    contradicting_papers.append(paper)
        
        # Create fact-check result
        return {
            'claim': claim,
            'supporting_evidence': len(supporting_papers),
            'contradicting_evidence': len(contradicting_papers),
            'confidence': self._calculate_fact_confidence(supporting_papers, contradicting_papers),
            'status': self._determine_fact_status(supporting_papers, contradicting_papers),
            'supporting_papers': supporting_papers[:3],  # Top 3
            'contradicting_papers': contradicting_papers[:3]
        }
    
    def _extract_claim_terms(self, claim: str) -> List[str]:
        """Extract key terms from a claim"""
        # Remove numbers and percentages for search
        clean_claim = re.sub(r'\d+(?:\.\d+)?%?', '', claim)
        
        # Extract key terms
        terms = []
        words = re.findall(r'\b\w+\b', clean_claim.lower())
        
        # Filter for meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        meaningful_words = [word for word in words if word not in stop_words and len(word) > 3]
        
        return meaningful_words[:5]  # Top 5 terms
    
    def _calculate_claim_relevance(self, claim: str, paper: ResearchPaper) -> float:
        """Calculate how relevant a paper is to a specific claim"""
        paper_text = f"{paper.title} {paper.abstract}".lower()
        claim_terms = set(re.findall(r'\b\w+\b', claim.lower()))
        paper_terms = set(re.findall(r'\b\w+\b', paper_text))
        
        overlap = len(claim_terms.intersection(paper_terms))
        return overlap / max(len(claim_terms), 1)
    
    def _supports_claim(self, claim: str, paper: ResearchPaper) -> bool:
        """Check if paper supports the claim"""
        # Simple heuristic - would need more sophisticated NLP
        paper_text = f"{paper.title} {paper.abstract}".lower()
        
        # Look for similar quantitative patterns
        claim_numbers = re.findall(r'\d+(?:\.\d+)?', claim)
        paper_numbers = re.findall(r'\d+(?:\.\d+)?', paper_text)
        
        # If claim and paper have similar numbers, assume potential support
        if claim_numbers and paper_numbers:
            claim_nums = [float(n) for n in claim_numbers]
            paper_nums = [float(n) for n in paper_numbers if float(n) < 100]  # Exclude years
            
            # Check if any numbers are similar (within 50% range)
            for c_num in claim_nums:
                for p_num in paper_nums:
                    if abs(c_num - p_num) / max(c_num, 1) < 0.5:
                        return True
        
        return False
    
    def _contradicts_claim(self, claim: str, paper: ResearchPaper) -> bool:
        """Check if paper contradicts the claim"""
        # Look for contradictory language
        paper_text = f"{paper.title} {paper.abstract}".lower()
        
        contradiction_indicators = ['no effect', 'no significant', 'did not', 'failed to', 'contradicts']
        if any(indicator in paper_text for indicator in contradiction_indicators):
            return True
        
        return False
    
    def _calculate_fact_confidence(self, supporting: List[ResearchPaper], contradicting: List[ResearchPaper]) -> float:
        """Calculate confidence in fact verification"""
        total_papers = len(supporting) + len(contradicting)
        if total_papers == 0:
            return 0.0
        
        # Weight by paper quality
        support_weight = sum(paper.quality_score or 0.5 for paper in supporting)
        contradict_weight = sum(paper.quality_score or 0.5 for paper in contradicting)
        
        total_weight = support_weight + contradict_weight
        if total_weight == 0:
            return 0.0
        
        return support_weight / total_weight
    
    def _determine_fact_status(self, supporting: List[ResearchPaper], contradicting: List[ResearchPaper]) -> str:
        """Determine the verification status of a claim"""
        support_count = len(supporting)
        contradict_count = len(contradicting)
        
        if support_count >= 3 and contradict_count == 0:
            return "likely_true"
        elif support_count >= 2 and contradict_count <= 1:
            return "probably_true"
        elif contradict_count >= 3 and support_count == 0:
            return "likely_false"
        elif contradict_count >= 2 and support_count <= 1:
            return "probably_false"
        elif support_count > 0 and contradict_count > 0:
            return "conflicting_evidence"
        else:
            return "insufficient_evidence"

class ContentEnhancementEngine:
    """Main content enhancement engine"""
    
    def __init__(self):
        self.content_analyzer = ContentAnalyzer()
        self.citation_engine = ContextAwareCitationEngine()
        self.fact_checker = FactChecker()
        self.enhancement_cache = {}
    
    async def enhance_content(self, content: str, file_path: Optional[Path] = None) -> ContentEnhancement:
        """Comprehensively enhance content"""
        logger.info(f"Enhancing content: {file_path or 'unknown'}")
        
        # Check cache
        if file_path:
            cache_key = hashlib.md5(content.encode()).hexdigest()
            if cache_key in self.enhancement_cache:
                logger.info("Returning cached enhancement")
                return self.enhancement_cache[cache_key]
        
        # Analyze content structure
        sections = self.content_analyzer.parse_content(content)
        
        # Generate citation suggestions
        all_suggestions = []
        for section in sections:
            if section.needs_citations:
                suggestions = await self.citation_engine.suggest_citations(section, sections)
                all_suggestions.extend(suggestions)
        
        # Fact-check content
        fact_check_results = await self.fact_checker.check_facts(content)
        
        # Generate enhanced content
        enhanced_content = self._apply_enhancements(content, all_suggestions)
        
        # Calculate improvement scores
        readability = self._calculate_readability_score(enhanced_content)
        citation_density = self._calculate_citation_density_score(sections)
        overall_improvement = self._calculate_overall_improvement(content, enhanced_content, all_suggestions)
        
        # Generate quality and structure improvements
        quality_improvements = self._suggest_quality_improvements(sections, fact_check_results)
        structure_improvements = self._suggest_structure_improvements(sections)
        
        enhancement = ContentEnhancement(
            original_content=content,
            enhanced_content=enhanced_content,
            citation_suggestions=all_suggestions,
            fact_check_results=fact_check_results,
            quality_improvements=quality_improvements,
            structure_improvements=structure_improvements,
            readability_score=readability,
            citation_density_score=citation_density,
            overall_improvement_score=overall_improvement
        )
        
        # Cache result
        if file_path:
            self.enhancement_cache[cache_key] = enhancement
        
        return enhancement
    
    def _apply_enhancements(self, content: str, suggestions: List[CitationSuggestion]) -> str:
        """Apply citation suggestions to content"""
        enhanced = content
        
        # Sort suggestions by relevance score
        suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Apply top suggestions
        for suggestion in suggestions[:10]:  # Limit to top 10
            # Create citation text
            paper = suggestion.paper
            if paper.doi:
                citation_text = f" [{paper.authors[0] if paper.authors else 'Unknown'} et al. ({paper.publication_date[:4] if paper.publication_date else 'Unknown'}). {paper.title}. DOI: https://doi.org/{paper.doi}]"
            elif paper.pmid:
                citation_text = f" [{paper.authors[0] if paper.authors else 'Unknown'} et al. ({paper.publication_date[:4] if paper.publication_date else 'Unknown'}). {paper.title}. PMID: https://pubmed.ncbi.nlm.nih.gov/{paper.pmid}]"
            else:
                citation_text = f" [{paper.authors[0] if paper.authors else 'Unknown'} et al. ({paper.publication_date[:4] if paper.publication_date else 'Unknown'}). {paper.title}.]"
            
            # Find insertion point
            if suggestion.context_snippet in enhanced:
                # Insert citation at end of sentence
                enhanced = enhanced.replace(
                    suggestion.context_snippet,
                    suggestion.context_snippet + citation_text
                )
        
        return enhanced
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (simplified)"""
        sentences = len(re.findall(r'[.!?]+', content))
        words = len(content.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        avg_sentence_length = words / sentences
        
        # Penalize very long sentences
        if avg_sentence_length > 25:
            return 0.3
        elif avg_sentence_length > 20:
            return 0.6
        else:
            return 0.8
    
    def _calculate_citation_density_score(self, sections: List[ContentSection]) -> float:
        """Calculate overall citation density score"""
        if not sections:
            return 0.0
        
        total_density = sum(section.citation_density for section in sections)
        avg_density = total_density / len(sections)
        
        # Optimal density is around 3-5 citations per 100 words
        if 3 <= avg_density <= 5:
            return 1.0
        elif 2 <= avg_density < 3 or 5 < avg_density <= 7:
            return 0.8
        elif 1 <= avg_density < 2 or 7 < avg_density <= 10:
            return 0.6
        else:
            return 0.3
    
    def _calculate_overall_improvement(self, original: str, enhanced: str, suggestions: List[CitationSuggestion]) -> float:
        """Calculate overall improvement score"""
        # Citation improvement
        original_citations = len(re.findall(r'DOI:|PMID:', original))
        enhanced_citations = len(re.findall(r'DOI:|PMID:', enhanced))
        citation_improvement = min((enhanced_citations - original_citations) / max(original_citations, 1), 1.0)
        
        # Quality of suggestions
        avg_suggestion_quality = sum(s.relevance_score for s in suggestions) / max(len(suggestions), 1)
        
        return (citation_improvement * 0.6 + avg_suggestion_quality * 0.4)
    
    def _suggest_quality_improvements(self, sections: List[ContentSection], fact_results: List[Dict]) -> List[str]:
        """Suggest quality improvements"""
        improvements = []
        
        # Check for sections without citations
        sections_needing_citations = [s for s in sections if s.needs_citations]
        if sections_needing_citations:
            improvements.append(f"Add citations to {len(sections_needing_citations)} sections that make unsupported claims")
        
        # Check fact verification issues
        problematic_facts = [f for f in fact_results if f['status'] in ['likely_false', 'probably_false']]
        if problematic_facts:
            improvements.append(f"Review {len(problematic_facts)} potentially inaccurate claims")
        
        # Check citation density
        low_density_sections = [s for s in sections if s.citation_density < 1.0 and len(s.key_claims) > 2]
        if low_density_sections:
            improvements.append(f"Increase citation density in {len(low_density_sections)} claim-heavy sections")
        
        return improvements
    
    def _suggest_structure_improvements(self, sections: List[ContentSection]) -> List[str]:
        """Suggest structural improvements"""
        improvements = []
        
        # Check for missing sections
        section_types = {s.section_type for s in sections}
        
        if 'introduction' not in section_types:
            improvements.append("Consider adding an introduction or background section")
        
        if 'quick_takeaway' not in section_types:
            improvements.append("Add a quick takeaway section for better accessibility")
        
        # Check section balance
        section_lengths = [len(s.content.split()) for s in sections]
        if section_lengths and max(section_lengths) / min(section_lengths) > 10:
            improvements.append("Balance section lengths for better readability")
        
        return improvements

async def main():
    """Test the content enhancement engine"""
    # Test content
    test_content = """# High-Intensity Interval Training Effects

## Quick Takeaway
HIIT training significantly improves cardiovascular health and performance.

## Deep Dive
High-intensity interval training (HIIT) has been shown to increase VO2max by 15-20% in sedentary individuals. Research demonstrates that HIIT protocols lasting 4-7 minutes can produce similar adaptations to traditional endurance training. The mechanisms involve enhanced mitochondrial biogenesis and improved cardiac output.

HIIT also significantly improves insulin sensitivity and glucose uptake. Studies indicate 40-60% improvements in insulin sensitivity following 2-6 weeks of HIIT intervention.
"""
    
    engine = ContentEnhancementEngine()
    enhancement = await engine.enhance_content(test_content)
    
    print("Content Enhancement Results:")
    print(f"Citation suggestions: {len(enhancement.citation_suggestions)}")
    print(f"Fact-check results: {len(enhancement.fact_check_results)}")
    print(f"Overall improvement: {enhancement.overall_improvement_score:.2f}")
    print("\nTop citation suggestions:")
    for i, suggestion in enumerate(enhancement.citation_suggestions[:3]):
        print(f"{i+1}. {suggestion.paper.title[:60]}...")
        print(f"   Relevance: {suggestion.relevance_score:.2f}")
        print(f"   Type: {suggestion.citation_type}")

if __name__ == "__main__":
    asyncio.run(main())