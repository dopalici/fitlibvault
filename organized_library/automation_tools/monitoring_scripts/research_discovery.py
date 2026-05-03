#!/usr/bin/env python3
"""
Advanced Research Discovery System
Multi-API integration for automated literature search and citation discovery
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set, Tuple, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import re
import logging
from urllib.parse import quote
from pathlib import Path
import hashlib

from config import config

logger = logging.getLogger(__name__)

@dataclass
class ResearchPaper:
    """Research paper data structure"""
    title: str
    authors: List[str]
    abstract: str
    journal: str
    publication_date: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    study_type: Optional[str] = None
    impact_factor: Optional[float] = None
    citation_count: Optional[int] = None
    quality_score: float = 0.0
    relevance_score: float = 0.0
    source_api: str = ""
    raw_data: Dict = field(default_factory=dict)

@dataclass
class SearchQuery:
    """Search query configuration"""
    terms: List[str]
    filters: Dict = field(default_factory=dict)
    date_range: Optional[Tuple[str, str]] = None
    max_results: int = 100
    min_quality_score: float = 0.6
    preferred_study_types: List[str] = field(default_factory=list)

class PubMedAPI:
    """Advanced PubMed API integration"""
    
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.api_key = config.api.pubmed_api_key
        self.email = config.api.pubmed_email
        
    async def search_papers(self, query: SearchQuery, session: aiohttp.ClientSession) -> List[ResearchPaper]:
        """Search PubMed for papers"""
        try:
            # Build search query
            search_term = " AND ".join([f'"{term}"' for term in query.terms])
            
            # Add filters
            if query.date_range:
                start_date, end_date = query.date_range
                search_term += f" AND ({start_date}[PDAT]:{end_date}[PDAT])"
            
            # Add study type filters
            if query.filters.get('study_types'):
                study_filters = " OR ".join([f'"{st}"[pt]' for st in query.filters['study_types']])
                search_term += f" AND ({study_filters})"
            
            # Search for PMIDs
            search_params = {
                'db': 'pubmed',
                'term': search_term,
                'retmax': query.max_results,
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            if self.api_key:
                search_params['api_key'] = self.api_key
            if self.email:
                search_params['email'] = self.email
            
            async with session.get(f"{self.base_url}/esearch.fcgi", params=search_params) as response:
                if response.status != 200:
                    logger.error(f"PubMed search failed: {response.status}")
                    return []
                
                data = await response.json()
                pmids = data.get('esearchresult', {}).get('idlist', [])
                
                if not pmids:
                    return []
                
                # Fetch paper details
                return await self._fetch_paper_details(pmids, session)
                
        except Exception as e:
            logger.error(f"PubMed search error: {e}")
            return []
    
    async def _fetch_paper_details(self, pmids: List[str], session: aiohttp.ClientSession) -> List[ResearchPaper]:
        """Fetch detailed information for papers"""
        if not pmids:
            return []
        
        # Process in batches to avoid overwhelming the API
        batch_size = 100
        papers = []
        
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i:i+batch_size]
            batch_papers = await self._fetch_batch_details(batch_pmids, session)
            papers.extend(batch_papers)
            
            # Rate limiting
            await asyncio.sleep(config.api.rate_limit_delay)
        
        return papers
    
    async def _fetch_batch_details(self, pmids: List[str], session: aiohttp.ClientSession) -> List[ResearchPaper]:
        """Fetch details for a batch of PMIDs"""
        try:
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml',
                'rettype': 'abstract'
            }
            
            if self.api_key:
                fetch_params['api_key'] = self.api_key
            if self.email:
                fetch_params['email'] = self.email
            
            async with session.get(f"{self.base_url}/efetch.fcgi", params=fetch_params) as response:
                if response.status != 200:
                    return []
                
                xml_content = await response.text()
                return self._parse_pubmed_xml(xml_content)
                
        except Exception as e:
            logger.error(f"Batch fetch error: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_content: str) -> List[ResearchPaper]:
        """Parse PubMed XML response"""
        papers = []
        try:
            root = ET.fromstring(xml_content)
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    # Extract basic info
                    title_elem = article.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else "Unknown Title"
                    
                    # Authors
                    authors = []
                    for author in article.findall('.//Author'):
                        lastname = author.find('LastName')
                        forename = author.find('ForeName')
                        if lastname is not None:
                            name = lastname.text
                            if forename is not None:
                                name = f"{forename.text} {name}"
                            authors.append(name)
                    
                    # Abstract
                    abstract_elem = article.find('.//Abstract/AbstractText')
                    abstract = abstract_elem.text if abstract_elem is not None else ""
                    
                    # Journal
                    journal_elem = article.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else "Unknown Journal"
                    
                    # Publication date
                    pub_date = self._extract_publication_date(article)
                    
                    # PMID
                    pmid_elem = article.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else None
                    
                    # DOI
                    doi = None
                    for article_id in article.findall('.//ArticleId'):
                        if article_id.get('IdType') == 'doi':
                            doi = article_id.text
                            break
                    
                    # Keywords
                    keywords = []
                    for keyword in article.findall('.//Keyword'):
                        if keyword.text:
                            keywords.append(keyword.text)
                    
                    # Study type classification
                    study_type = self._classify_study_type(title, abstract)
                    
                    paper = ResearchPaper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        journal=journal,
                        publication_date=pub_date,
                        doi=doi,
                        pmid=pmid,
                        keywords=keywords,
                        study_type=study_type,
                        source_api="pubmed"
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing article: {e}")
                    continue
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
        
        return papers
    
    def _extract_publication_date(self, article) -> str:
        """Extract publication date from article XML"""
        # Try different date fields
        date_fields = ['.//PubDate', './/ArticleDate']
        
        for field in date_fields:
            date_elem = article.find(field)
            if date_elem is not None:
                year = date_elem.find('Year')
                month = date_elem.find('Month')
                day = date_elem.find('Day')
                
                if year is not None:
                    date_str = year.text
                    if month is not None:
                        date_str += f"-{month.text.zfill(2)}"
                        if day is not None:
                            date_str += f"-{day.text.zfill(2)}"
                    return date_str
        
        return "Unknown"
    
    def _classify_study_type(self, title: str, abstract: str) -> Optional[str]:
        """Classify study type based on title and abstract"""
        text = f"{title} {abstract}".lower()
        
        # Study type patterns
        patterns = {
            'meta_analysis': [r'meta[\-\s]?analysis', r'systematic review and meta[\-\s]?analysis'],
            'systematic_review': [r'systematic review', r'systematic literature review'],
            'randomized_controlled_trial': [r'randomized controlled trial', r'rct', r'random(ly|ized)', r'placebo[\-\s]controlled'],
            'cohort_study': [r'cohort study', r'prospective study', r'longitudinal'],
            'cross_sectional': [r'cross[\-\s]sectional', r'survey'],
            'case_control': [r'case[\-\s]control', r'retrospective'],
            'case_study': [r'case study', r'case report'],
            'review': [r'review', r'narrative review']
        }
        
        for study_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                if re.search(pattern, text):
                    return study_type
        
        return None

class CrossRefAPI:
    """CrossRef API integration for DOI-based searches"""
    
    def __init__(self):
        self.base_url = "https://api.crossref.org/works"
        self.api_key = config.api.crossref_api_key
        
    async def search_papers(self, query: SearchQuery, session: aiohttp.ClientSession) -> List[ResearchPaper]:
        """Search CrossRef for papers"""
        try:
            search_term = " ".join(query.terms)
            
            params = {
                'query': search_term,
                'rows': min(query.max_results, 1000),  # CrossRef limit
                'sort': 'relevance',
                'order': 'desc'
            }
            
            # Add filters
            if query.date_range:
                start_date, end_date = query.date_range
                params['filter'] = f'from-pub-date:{start_date},until-pub-date:{end_date}'
            
            headers = {'User-Agent': 'CitationAutomation/1.0 (mailto:your-email@domain.com)'}
            
            async with session.get(self.base_url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"CrossRef search failed: {response.status}")
                    return []
                
                data = await response.json()
                items = data.get('message', {}).get('items', [])
                
                return [self._parse_crossref_item(item) for item in items]
                
        except Exception as e:
            logger.error(f"CrossRef search error: {e}")
            return []
    
    def _parse_crossref_item(self, item: Dict) -> ResearchPaper:
        """Parse CrossRef item into ResearchPaper"""
        # Extract title
        title_list = item.get('title', ['Unknown Title'])
        title = title_list[0] if title_list else 'Unknown Title'
        
        # Extract authors
        authors = []
        for author in item.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if family:
                name = f"{given} {family}".strip()
                authors.append(name)
        
        # Extract journal
        journal_list = item.get('container-title', ['Unknown Journal'])
        journal = journal_list[0] if journal_list else 'Unknown Journal'
        
        # Extract publication date
        pub_date = "Unknown"
        if 'published-print' in item:
            date_parts = item['published-print'].get('date-parts', [[]])
            if date_parts and date_parts[0]:
                pub_date = '-'.join([str(d).zfill(2) for d in date_parts[0]])
        elif 'published-online' in item:
            date_parts = item['published-online'].get('date-parts', [[]])
            if date_parts and date_parts[0]:
                pub_date = '-'.join([str(d).zfill(2) for d in date_parts[0]])
        
        # Extract DOI
        doi = item.get('DOI')
        
        # Extract abstract (usually not available in CrossRef)
        abstract = item.get('abstract', '')
        
        # Citation count
        citation_count = item.get('is-referenced-by-count', 0)
        
        return ResearchPaper(
            title=title,
            authors=authors,
            abstract=abstract,
            journal=journal,
            publication_date=pub_date,
            doi=doi,
            citation_count=citation_count,
            source_api="crossref",
            raw_data=item
        )

class SemanticScholarAPI:
    """Semantic Scholar API integration"""
    
    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = config.api.semantic_scholar_api_key
        
    async def search_papers(self, query: SearchQuery, session: aiohttp.ClientSession) -> List[ResearchPaper]:
        """Search Semantic Scholar for papers"""
        try:
            search_term = " ".join(query.terms)
            
            params = {
                'query': search_term,
                'limit': min(query.max_results, 100),  # API limit
                'fields': 'paperId,title,authors,abstract,journal,year,citationCount,influentialCitationCount,url,venue,publicationDate'
            }
            
            headers = {}
            if self.api_key:
                headers['x-api-key'] = self.api_key
            
            async with session.get(f"{self.base_url}/paper/search", params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Semantic Scholar search failed: {response.status}")
                    return []
                
                data = await response.json()
                papers_data = data.get('data', [])
                
                return [self._parse_semantic_scholar_item(item) for item in papers_data]
                
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            return []
    
    def _parse_semantic_scholar_item(self, item: Dict) -> ResearchPaper:
        """Parse Semantic Scholar item into ResearchPaper"""
        title = item.get('title', 'Unknown Title')
        
        # Extract authors
        authors = []
        for author in item.get('authors', []):
            name = author.get('name', '')
            if name:
                authors.append(name)
        
        abstract = item.get('abstract', '')
        journal = item.get('venue', 'Unknown Journal')
        pub_date = str(item.get('year', 'Unknown'))
        url = item.get('url')
        citation_count = item.get('citationCount', 0)
        
        return ResearchPaper(
            title=title,
            authors=authors,
            abstract=abstract,
            journal=journal,
            publication_date=pub_date,
            url=url,
            citation_count=citation_count,
            source_api="semantic_scholar",
            raw_data=item
        )

class ResearchDiscoveryEngine:
    """Main research discovery engine coordinating multiple APIs"""
    
    def __init__(self):
        self.pubmed_api = PubMedAPI()
        self.crossref_api = CrossRefAPI()
        self.semantic_scholar_api = SemanticScholarAPI()
        self.cache_dir = Path("research_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
    async def discover_papers(self, query: SearchQuery) -> List[ResearchPaper]:
        """Discover papers using multiple APIs"""
        logger.info(f"Starting research discovery for: {' '.join(query.terms)}")
        
        # Check cache first
        cache_key = self._generate_cache_key(query)
        cached_results = self._load_from_cache(cache_key)
        if cached_results:
            logger.info("Returning cached results")
            return cached_results
        
        # Search multiple APIs concurrently
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.api.timeout)) as session:
            search_tasks = []
            
            # Add API search tasks
            search_tasks.append(self.pubmed_api.search_papers(query, session))
            search_tasks.append(self.crossref_api.search_papers(query, session))
            search_tasks.append(self.semantic_scholar_api.search_papers(query, session))
            
            # Execute searches concurrently
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            all_papers = []
            for result in results:
                if isinstance(result, list):
                    all_papers.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Search error: {result}")
            
            # Deduplicate and rank
            unique_papers = self._deduplicate_papers(all_papers)
            ranked_papers = self._rank_papers(unique_papers, query)
            
            # Filter by quality score
            filtered_papers = [
                paper for paper in ranked_papers 
                if paper.quality_score >= query.min_quality_score
            ]
            
            # Cache results
            self._save_to_cache(cache_key, filtered_papers)
            
            logger.info(f"Discovered {len(filtered_papers)} high-quality papers")
            return filtered_papers
    
    def _deduplicate_papers(self, papers: List[ResearchPaper]) -> List[ResearchPaper]:
        """Remove duplicate papers based on DOI, PMID, and title similarity"""
        seen_dois = set()
        seen_pmids = set()
        seen_titles = set()
        unique_papers = []
        
        for paper in papers:
            # Check DOI
            if paper.doi and paper.doi in seen_dois:
                continue
            elif paper.doi:
                seen_dois.add(paper.doi)
            
            # Check PMID
            if paper.pmid and paper.pmid in seen_pmids:
                continue
            elif paper.pmid:
                seen_pmids.add(paper.pmid)
            
            # Check title similarity (simple approach)
            title_key = self._normalize_title(paper.title)
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            unique_papers.append(paper)
        
        return unique_papers
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Remove special characters, convert to lowercase, remove extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _rank_papers(self, papers: List[ResearchPaper], query: SearchQuery) -> List[ResearchPaper]:
        """Rank papers by quality and relevance"""
        for paper in papers:
            # Calculate quality score
            quality_score = self._calculate_quality_score(paper, query)
            paper.quality_score = quality_score
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(paper, query)
            paper.relevance_score = relevance_score
        
        # Sort by combined score (quality * relevance)
        papers.sort(key=lambda p: p.quality_score * p.relevance_score, reverse=True)
        
        return papers
    
    def _calculate_quality_score(self, paper: ResearchPaper, query: SearchQuery) -> float:
        """Calculate paper quality score"""
        score = 0.0
        
        # Study type scoring
        if paper.study_type:
            study_type_scores = {
                'meta_analysis': 1.0,
                'systematic_review': 0.9,
                'randomized_controlled_trial': 0.85,
                'cohort_study': 0.7,
                'cross_sectional': 0.6,
                'case_control': 0.55,
                'case_study': 0.3,
                'review': 0.4
            }
            score += study_type_scores.get(paper.study_type, 0.5) * 0.4
        else:
            score += 0.2  # Default for unknown
        
        # Citation count scoring (normalized)
        if paper.citation_count:
            citation_score = min(paper.citation_count / 100, 1.0)  # Cap at 100 citations
            score += citation_score * 0.3
        
        # Recency scoring (more recent = higher score)
        if paper.publication_date and paper.publication_date != "Unknown":
            try:
                pub_year = int(paper.publication_date[:4])
                current_year = datetime.now().year
                years_ago = current_year - pub_year
                recency_score = max(0, 1 - (years_ago / 20))  # Linear decay over 20 years
                score += recency_score * 0.2
            except:
                score += 0.1  # Default for unparseable dates
        
        # Abstract quality (length and keywords)
        if paper.abstract:
            abstract_score = min(len(paper.abstract.split()) / 200, 1.0)  # Cap at 200 words
            score += abstract_score * 0.1
        
        return min(score, 1.0)
    
    def _calculate_relevance_score(self, paper: ResearchPaper, query: SearchQuery) -> float:
        """Calculate paper relevance score"""
        text = f"{paper.title} {paper.abstract}".lower()
        
        # Term matching
        term_matches = 0
        for term in query.terms:
            if term.lower() in text:
                term_matches += 1
        
        relevance_score = term_matches / len(query.terms) if query.terms else 0
        
        # Keyword matching bonus
        if paper.keywords:
            keyword_matches = sum(1 for term in query.terms if any(term.lower() in kw.lower() for kw in paper.keywords))
            relevance_score += (keyword_matches / len(query.terms)) * 0.2
        
        return min(relevance_score, 1.0)
    
    def _generate_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for query"""
        key_data = {
            'terms': sorted(query.terms),
            'filters': query.filters,
            'date_range': query.date_range,
            'max_results': query.max_results
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[ResearchPaper]]:
        """Load results from cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                # Check if cache is recent (within 24 hours)
                cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if cache_age < timedelta(hours=24):
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    papers = []
                    for paper_data in data:
                        paper = ResearchPaper(**paper_data)
                        papers.append(paper)
                    
                    return papers
            except Exception as e:
                logger.warning(f"Cache load error: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, papers: List[ResearchPaper]):
        """Save results to cache"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            paper_data = []
            for paper in papers:
                # Convert to dict, handling non-serializable fields
                paper_dict = {
                    'title': paper.title,
                    'authors': paper.authors,
                    'abstract': paper.abstract,
                    'journal': paper.journal,
                    'publication_date': paper.publication_date,
                    'doi': paper.doi,
                    'pmid': paper.pmid,
                    'url': paper.url,
                    'keywords': paper.keywords,
                    'study_type': paper.study_type,
                    'impact_factor': paper.impact_factor,
                    'citation_count': paper.citation_count,
                    'quality_score': paper.quality_score,
                    'relevance_score': paper.relevance_score,
                    'source_api': paper.source_api
                }
                paper_data.append(paper_dict)
            
            with open(cache_file, 'w') as f:
                json.dump(paper_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Cache save error: {e}")

async def main():
    """Test the research discovery system"""
    engine = ResearchDiscoveryEngine()
    
    # Test query
    query = SearchQuery(
        terms=["resistance training", "strength", "hypertrophy"],
        max_results=50,
        min_quality_score=0.7,
        date_range=("2020-01-01", "2024-12-31")
    )
    
    papers = await engine.discover_papers(query)
    
    print(f"Found {len(papers)} papers:")
    for paper in papers[:10]:  # Show top 10
        print(f"- {paper.title}")
        print(f"  Authors: {', '.join(paper.authors[:3])}")
        print(f"  Journal: {paper.journal}")
        print(f"  Quality: {paper.quality_score:.2f}, Relevance: {paper.relevance_score:.2f}")
        print(f"  DOI: {paper.doi or 'N/A'}, PMID: {paper.pmid or 'N/A'}")
        print()

if __name__ == "__main__":
    asyncio.run(main())