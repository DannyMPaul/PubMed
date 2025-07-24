#!/usr/bin/env python3
"""
Example usage of the GPL (Get Pharma Literature) tool as a Python module.

This demonstrates how to use the core functionality programmatically
without the CLI interface.
"""

from gpl.core import PubMedSearcher, PubMedAPIError
import logging

# Setup logging to see debug information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Example of using GPL programmatically."""
    
    # Initialize the searcher
    searcher = PubMedSearcher()
    
    # Search query
    query = "cancer therapy"
    
    try:
        print(f"Searching for: '{query}'...")
        
        # Step 1: Search for paper IDs
        pmids = searcher.search_papers(query, max_results=10)  # Smaller limit for example
        print(f"Found {len(pmids)} paper IDs")
        
        if not pmids:
            print("No papers found.")
            return
        
        # Step 2: Fetch detailed information
        print("Fetching paper details...")
        papers_data = searcher.fetch_paper_details(pmids)
        print(f"Retrieved details for {len(papers_data)} papers")
        
        # Step 3: Filter for company-affiliated papers
        print("Filtering for pharmaceutical/biotech company papers...")
        company_papers = searcher.filter_company_papers(papers_data)
        
        # Display results
        print(f"\nFound {len(company_papers)} papers with company affiliations:\n")
        
        for i, paper in enumerate(company_papers, 1):
            print(f"Paper {i}:")
            print(f"  PubMed ID: {paper.pubmed_id}")
            print(f"  Title: {paper.title}")
            print(f"  Date: {paper.publication_date}")
            print(f"  Company Authors: {', '.join(paper.non_academic_authors)}")
            print(f"  Affiliations: {', '.join(paper.company_affiliations)}")
            print(f"  Email: {paper.corresponding_email}")
            print("-" * 80)
        
        if not company_papers:
            print("No papers found with pharmaceutical/biotech company affiliations.")
    
    except PubMedAPIError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()