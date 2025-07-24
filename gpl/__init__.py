"""
GPL - Get Pharma Literature

A CLI tool to search PubMed for pharmaceutical/biotech company research papers.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .core import PubMedSearcher, PubMedPaper, PubMedAPIError

__all__ = ["PubMedSearcher", "PubMedPaper", "PubMedAPIError"]