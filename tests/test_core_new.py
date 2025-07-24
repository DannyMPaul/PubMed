"""
Basic tests for the GPL core module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from gpl.core import PubMedSearcher, PubMedAPIError, PubMedPaper


class TestPubMedSearcher:
    """Test cases for PubMedSearcher class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.searcher = PubMedSearcher()
    
    def test_init(self):
        """Test searcher initialization."""
        assert self.searcher.rate_limit == 0.34
        assert self.searcher.session is not None
        assert 'GPL-PubMed-Tool' in self.searcher.session.headers['User-Agent']
    
    @patch('gpl.core.PubMedSearcher.fetch_paper_details')
    @patch('time.sleep')
    @patch('requests.Session.get')
    def test_search_papers_success(self, mock_get, mock_sleep, mock_fetch):
        """Test successful paper search."""
        # Mock search response
        mock_response = Mock()
        mock_response.json.return_value = {
            'esearchresult': {
                'idlist': ['12345', '67890']
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Mock fetch response
        mock_fetch.return_value = [
            {
                'pmid': '12345',
                'title': 'Test Paper',
                'authors': [{'name': 'John Doe', 'affiliation': 'Pfizer Inc.'}],
                'pub_date': {'year': '2023', 'month': 'Jan', 'day': '15'},
                'emails': ['test@pfizer.com']
            }
        ]
        
        result = self.searcher.search_papers("cancer therapy")
        
        assert len(result) == 1
        assert isinstance(result[0], PubMedPaper)
        assert result[0].pubmed_id == '12345'
        assert result[0].title == 'Test Paper'
        mock_get.assert_called_once()
    
    @patch('gpl.core.PubMedSearcher.fetch_paper_details')
    @patch('time.sleep')
    @patch('requests.Session.get')
    def test_search_papers_no_results(self, mock_get, mock_sleep, mock_fetch):
        """Test search with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'esearchresult': {
                'idlist': []
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.searcher.search_papers("nonexistent query")
        
        assert result == []
        mock_fetch.assert_not_called()
    
    @patch('time.sleep')
    @patch('requests.Session.get')
    def test_search_papers_api_error(self, mock_get, mock_sleep):
        """Test API error handling."""
        mock_get.side_effect = Exception("API Error")
        
        with pytest.raises(PubMedAPIError):
            self.searcher.search_papers("test query")
    
    def test_format_publication_date_full(self):
        """Test full date formatting."""
        pub_date = {'year': '2023', 'month': 'January', 'day': '15'}
        result = self.searcher._format_publication_date(pub_date)
        assert result == 'Jan 15 2023'
    
    def test_format_publication_date_numeric_month(self):
        """Test numeric month formatting."""
        pub_date = {'year': '2023', 'month': '1', 'day': '15'}
        result = self.searcher._format_publication_date(pub_date)
        assert result == 'Jan 15 2023'
    
    def test_format_publication_date_year_only(self):
        """Test year-only formatting."""
        pub_date = {'year': '2023'}
        result = self.searcher._format_publication_date(pub_date)
        assert result == '2023'
    
    def test_format_publication_date_empty(self):
        """Test empty date formatting."""
        result = self.searcher._format_publication_date({})
        assert result == 'Date not available'
    
    def test_extract_corresponding_email_found(self):
        """Test email extraction when email is found."""
        paper = {'emails': ['test@example.com', 'other@example.com']}
        result = self.searcher._extract_corresponding_email(paper)
        assert result == 'test@example.com'
    
    def test_extract_corresponding_email_not_found(self):
        """Test email extraction when no email is found."""
        paper = {'emails': []}
        result = self.searcher._extract_corresponding_email(paper)
        assert result == 'Email Unable to Retrieve'


class TestPubMedPaper:
    """Test cases for PubMedPaper dataclass."""
    
    def test_pubmed_paper_creation(self):
        """Test PubMedPaper object creation."""
        paper = PubMedPaper(
            pubmed_id='12345',
            title='Test Paper',
            publication_date='Jan 15 2023',
            non_academic_authors=['John Doe'],
            company_affiliations=['Pfizer Inc.'],
            corresponding_email='test@pfizer.com'
        )
        
        assert paper.pubmed_id == '12345'
        assert paper.title == 'Test Paper'
        assert paper.publication_date == 'Jan 15 2023'
        assert paper.non_academic_authors == ['John Doe']
        assert paper.company_affiliations == ['Pfizer Inc.']
        assert paper.corresponding_email == 'test@pfizer.com'
