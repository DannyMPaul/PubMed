"""
Core module for PubMed querying and filtering pharmaceutical/biotech papers.
"""

import re
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

import requests
from requests.exceptions import RequestException, Timeout


logger = logging.getLogger(__name__)


@dataclass
class PubMedPaper:
    """Data class representing a PubMed paper with company affiliations."""
    pubmed_id: str
    title: str
    publication_date: str
    non_academic_authors: List[str]
    company_affiliations: List[str]
    corresponding_email: str


class PubMedAPIError(Exception):
    """Custom exception for PubMed API related errors."""
    pass


class PubMedSearcher:
    """Handler for PubMed E-utilities API interactions."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    SEARCH_URL = f"{BASE_URL}/esearch.fcgi"
    FETCH_URL = f"{BASE_URL}/efetch.fcgi"
    
    def __init__(self, rate_limit: float = 0.34) -> None:
        """
        Initialize PubMed searcher.
        
        Args:
            rate_limit: Delay between requests in seconds (default: 0.34s for 3 req/sec)
        """
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GPL-PubMed-Tool/1.0 (https://github.com/yourusername/gpl)'
        })
    
    def search_papers(self, query: str, max_results: int = 200, filter_companies: bool = True) -> List[PubMedPaper]:
        """
        Search PubMed for papers matching the query with company affiliation pre-filtering.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            filter_companies: If True, adds company affiliation filters to the search
            
        Returns:
            List of PubMedPaper objects
            
        Raises:
            PubMedAPIError: If API request fails
        """
        # Enhance query with company affiliation filters if requested
        enhanced_query = self._build_company_filtered_query(query) if filter_companies else query
        
        params = {
            'db': 'pubmed',
            'term': enhanced_query,
            'retmax': str(max_results),
            'retmode': 'json',
            'sort': 'relevance',
            'tool': 'gpl',
            'email': 'your.email@example.com'  # Required by NCBI
        }
        
        logger.debug(f"Searching PubMed with URL: {self.SEARCH_URL}")
        logger.debug(f"Original query: {query}")
        logger.debug(f"Enhanced query: {enhanced_query}")
        logger.debug(f"Search parameters: {params}")
        
        try:
            response = self._make_request(self.SEARCH_URL, params)
            data = response.json()
            
            logger.debug(f"Search response: {data}")
            
            if 'esearchresult' not in data:
                raise PubMedAPIError("Invalid response format from PubMed search")
            
            pmids = data['esearchresult'].get('idlist', [])
            logger.info(f"Found {len(pmids)} papers for query: '{query}' (enhanced: {filter_companies})")
            
            if not pmids:
                return []
            
            # Fetch paper details
            paper_details = self.fetch_paper_details(pmids)
            
            # Parse details into PubMedPaper objects
            papers = []
            for paper_data in paper_details:
                pub_date = self._format_publication_date(paper_data.get('pub_date', ''))
                email = self._extract_corresponding_email(paper_data)
                
                # Extract author names and affiliations
                author_names = [author.get('name', '') for author in paper_data.get('authors', []) if author.get('name')]
                affiliations = list(set([author.get('affiliation', '') for author in paper_data.get('authors', []) if author.get('affiliation')]))
                
                paper = PubMedPaper(
                    pubmed_id=paper_data.get('pmid', ''),
                    title=paper_data.get('title', ''),
                    publication_date=pub_date,
                    non_academic_authors=author_names,
                    company_affiliations=affiliations,
                    corresponding_email=email
                )
                papers.append(paper)
            
            return papers
            
        except RequestException as e:
            raise PubMedAPIError(f"Failed to search PubMed: {str(e)}")
        except Exception as e:
            raise PubMedAPIError(f"Unexpected error during PubMed search: {str(e)}")
    
    def _build_company_filtered_query(self, query: str) -> str:
        """
        Build a PubMed query that filters for company affiliations using search field tags.
        
        Args:
            query: Original search query
            
        Returns:
            Enhanced query with company affiliation filters
        """
        # Major pharmaceutical and biotech company names for targeted searching
        major_companies = [
            "pfizer", "moderna", "johnson johnson", "merck", "novartis", "roche", 
            "bristol myers", "abbvie", "gilead", "amgen", "biogen", "regeneron",
            "eli lilly", "gsk", "glaxosmithkline", "astrazeneca", "sanofi",
            "takeda", "bayer", "boehringer ingelheim", "vertex", "celgene"
        ]
        
        # Generic company indicators
        company_terms = [
            "pharmaceutical", "pharmaceuticals", "pharma", "biotech", "biotechnology",
            "therapeutics", "biopharmaceutical", "inc[ad]", "ltd[ad]", "corp[ad]",
            "corporation[ad]", "company[ad]", "laboratories[ad]", "lab[ad]"
        ]
        
        # Build affiliation search terms using PubMed's [ad] field tag (author affiliation)
        company_affiliation_parts = []
        
        # Add major company names
        for company in major_companies:
            company_affiliation_parts.append(f'"{company}"[ad]')
        
        # Add generic company terms
        for term in company_terms:
            company_affiliation_parts.append(f'{term}[ad]')
        
        # Combine with OR operators
        company_filter = "(" + " OR ".join(company_affiliation_parts) + ")"
        
        # Exclude academic institutions
        academic_exclusions = [
            '"university"[ad]', '"college"[ad]', '"institute"[ad]', '"hospital"[ad]',
            '"medical center"[ad]', '"department"[ad]', '"school"[ad]'
        ]
        
        academic_filter = "NOT (" + " OR ".join(academic_exclusions) + ")"
        
        # Combine original query with company filter
        enhanced_query = f"({query}) AND {company_filter} {academic_filter}"
        
        return enhanced_query
    
    def fetch_paper_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch detailed information for given PubMed IDs.
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            List of paper detail dictionaries
            
        Raises:
            PubMedAPIError: If API request fails
        """
        if not pmids:
            return []
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'tool': 'gpl',
            'email': 'your.email@example.com'
        }
        
        logger.debug(f"Fetching paper details with URL: {self.FETCH_URL}")
        logger.debug(f"Fetch parameters: {params}")
        
        try:
            response = self._make_request(self.FETCH_URL, params)
            xml_content = response.text
            
            logger.debug(f"Fetch response length: {len(xml_content)} characters")
            logger.debug(f"Fetch response preview: {xml_content[:500]}...")
            
            return self._parse_xml_response(xml_content)
            
        except RequestException as e:
            raise PubMedAPIError(f"Failed to fetch paper details: {str(e)}")
    
    def _make_request(self, url: str, params: Dict[str, str]) -> requests.Response:
        """Make rate-limited request to PubMed API."""
        time.sleep(self.rate_limit)  # Rate limiting
        
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response
    
    def _parse_xml_response(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse XML response from PubMed efetch API.
        
        This is a simplified XML parser for demonstration.
        In production, consider using xml.etree.ElementTree or lxml.
        """
        papers = []
        
        # Improved regex patterns for PubMed XML structure
        pmid_pattern = r'<PMID[^>]*>(\d+)</PMID>'
        title_pattern = r'<ArticleTitle>([^<]+)</ArticleTitle>'
        
        # Updated author pattern to handle nested affiliation structure
        # Pattern that works: extract from within each individual author section
        author_pattern = r'<LastName>([^<]+)</LastName>.*?<ForeName>([^<]*)</ForeName>.*?<AffiliationInfo>.*?<Affiliation>([^<]*)</Affiliation>'
        
        date_pattern = r'<PubDate>.*?<Year>(\d{4})</Year>(?:.*?<Month>([^<]*)</Month>)?(?:.*?<Day>(\d+)</Day>)?.*?</PubDate>'
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        
        pmids = re.findall(pmid_pattern, xml_content)
        titles = re.findall(title_pattern, xml_content, re.DOTALL)
        
        # Split by PubmedArticle for individual paper processing
        articles = re.split(r'<PubmedArticle[^>]*>', xml_content)
        
        for i, article in enumerate(articles[1:], 0):  # Skip first empty split
            if i >= len(pmids):
                break
                
            paper = {
                'pmid': pmids[i] if i < len(pmids) else '',
                'title': titles[i] if i < len(titles) else '',
                'authors': [],
                'pub_date': '',
                'emails': []
            }
            
            # Extract authors and affiliations with improved approach
            # First, find all individual Author sections
            individual_authors = re.findall(r'<Author[^>]*>(.*?)</Author>', article, re.DOTALL)
            
            for author_section in individual_authors:
                # Extract name components
                last_name_match = re.search(r'<LastName>([^<]+)</LastName>', author_section)
                first_name_match = re.search(r'<ForeName>([^<]*)</ForeName>', author_section)
                
                if last_name_match and first_name_match:
                    last_name = last_name_match.group(1)
                    first_name = first_name_match.group(1)
                    
                    # Extract affiliation (may or may not exist)
                    affiliation_match = re.search(r'<AffiliationInfo>.*?<Affiliation>([^<]*)</Affiliation>', author_section, re.DOTALL)
                    affiliation = affiliation_match.group(1).strip() if affiliation_match else ''
                    
                    author_info = {
                        'name': f"{first_name} {last_name}".strip(),
                        'affiliation': affiliation
                    }
                    paper['authors'].append(author_info)
            
            # Extract publication date
            date_match = re.search(date_pattern, article, re.DOTALL)
            if date_match:
                year, month, day = date_match.groups()
                paper['pub_date'] = {
                    'year': year,
                    'month': month or '',
                    'day': day or ''
                }
            
            # Extract emails
            emails = re.findall(email_pattern, article)
            paper['emails'] = emails
            
            papers.append(paper)
        
        return papers
    
    def _format_publication_date(self, pub_date: Dict[str, str]) -> str:
        """Format publication date to 'Jan 15 2024' format."""
        if not pub_date:
            return "Date not available"
        
        year = pub_date.get('year', '')
        month = pub_date.get('month', '')
        day = pub_date.get('day', '')
        
        if not year:
            return "Date not available"
        
        # Convert month number to name if numeric
        month_names = {
            '1': 'Jan', '2': 'Feb', '3': 'Mar', '4': 'Apr', '5': 'May', '6': 'Jun',
            '7': 'Jul', '8': 'Aug', '9': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
        }
        
        if month.isdigit():
            month = month_names.get(month, month)
        elif month:
            month = month[:3].capitalize()  # Take first 3 chars and capitalize
        
        # Format date
        if month and day:
            return f"{month} {day} {year}"
        elif month:
            return f"{month} {year}"
        else:
            return year
    
    def _extract_corresponding_email(self, paper: Dict[str, Any]) -> str:
        """Extract corresponding author email if available."""
        emails = paper.get('emails', [])
        
        if emails:
            return emails[0]  # Return first email found
        
        return "Email Unable to Retrieve"