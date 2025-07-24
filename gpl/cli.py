"""
CLI entry point for the GPL (Get Pharma Literature) tool.
"""

import csv
import sys
import logging
from typing import List, Optional

import click
from tabulate import tabulate

from .core import PubMedSearcher, PubMedAPIError, PubMedPaper


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def format_list_for_display(items: List[str], max_width: int = 40) -> str:
    """Format list items for table display with proper wrapping."""
    if not items:
        return ""
    
    if len(items) == 1:
        return items[0][:max_width] + "..." if len(items[0]) > max_width else items[0]
    
    # For multiple items, show count and truncate
    formatted = f"{items[0][:max_width//2]}..."
    if len(items) > 1:
        formatted += f" (+{len(items)-1} more)"
    
    return formatted


def display_papers_table(papers: List[PubMedPaper]) -> None:
    """Display papers in a formatted table."""
    if not papers:
        click.echo("No papers found with company affiliations")
        return
    
    headers = [
        "PubMed ID",
        "Title", 
        "Publication Date",
        "Non-academic Author(s)",
        "Company Affiliation(s)",
        "Corresponding Author Email"
    ]
    
    table_data = []
    for paper in papers:
        # Truncate long titles for table display
        title = paper.title[:50] + "..." if len(paper.title) > 50 else paper.title
        
        row = [
            paper.pubmed_id,
            title,
            paper.publication_date,
            format_list_for_display(paper.non_academic_authors, 30),
            format_list_for_display(paper.company_affiliations, 35),
            paper.corresponding_email[:30] + "..." if len(paper.corresponding_email) > 30 
            else paper.corresponding_email
        ]
        table_data.append(row)
    
    click.echo(f"\nFound {len(papers)} papers with pharmaceutical/biotech company affiliations:\n")
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid", stralign="left"))


def save_papers_csv(papers: List[PubMedPaper], filename: str) -> None:
    """Save papers to CSV file."""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                "PubMed ID",
                "Title", 
                "Publication Date",
                "Non-academic Author(s)",
                "Company Affiliation(s)",
                "Corresponding Author Email"
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for paper in papers:
                writer.writerow({
                    "PubMed ID": paper.pubmed_id,
                    "Title": paper.title,
                    "Publication Date": paper.publication_date,
                    "Non-academic Author(s)": "; ".join(paper.non_academic_authors),
                    "Company Affiliation(s)": "; ".join(paper.company_affiliations),
                    "Corresponding Author Email": paper.corresponding_email
                })
        
        click.echo(f"Results saved to {filename}")
        
    except IOError as e:
        click.echo(f"Error saving to file {filename}: {str(e)}", err=True)
        sys.exit(1)


@click.command()
@click.argument('query', required=False)
@click.option('--file', '-f', 'output_file', help='Save results to CSV file')
@click.option('--debug', '-d', is_flag=True, help='Enable debug logging')
@click.option('--no-prefilter', is_flag=True, help='Disable pre-filtering at search level (slower but more comprehensive)')
@click.option('--help', '-h', is_flag=True, help='Show this help message')
def main(query: Optional[str], output_file: Optional[str], debug: bool, no_prefilter: bool, help: bool) -> None:
    """
    GPL - Get Pharma Literature
    
    Search PubMed for research papers from pharmaceutical/biotech companies.
    
    QUERY: Search term (e.g., "cancer therapy", "diabetes treatment")
    
    Examples:
    \b
        gpl "cancer therapy"
        gpl "diabetes treatment" --file results.csv
        gpl "immunotherapy" --debug
        gpl "cancer therapy" --no-prefilter  # Disable search-level filtering
        gpl --help
    """
    if help or not query:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return
    
    # Setup logging
    setup_logging(debug)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize searcher
        searcher = PubMedSearcher()
        
        # Search for papers
        use_prefilter = not no_prefilter
        filter_msg = "with pre-filtering" if use_prefilter else "without pre-filtering"
        click.echo(f"Searching PubMed for: '{query}' ({filter_msg})...")
        
        with click.progressbar(length=100, label='Searching') as bar:
            papers = searcher.search_papers(query, max_results=200, filter_companies=use_prefilter)
            bar.update(100)
        
        if not papers:
            click.echo("No papers found for the given query.")
            return
        
        # Output results
        if output_file:
            save_papers_csv(papers, output_file)
        else:
            display_papers_table(papers)
    
    except PubMedAPIError as e:
        logger.error(f"PubMed API error: {str(e)}")
        click.echo(f"Error accessing PubMed: {str(e)}", err=True)
        sys.exit(1)
    
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        click.echo(f"An unexpected error occurred: {str(e)}", err=True)
        if debug:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()