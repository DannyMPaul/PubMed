# GPL - Get Pharma Literature

A command-line tool to search PubMed for research papers authored by pharmaceutical and biotech company researchers. This tool filters out academic papers and focuses specifically on industry-affiliated research.

## Features

- Search PubMed using natural language queries
- Filter papers to show only those with pharmaceutical/biotech company affiliations
- Display results in formatted tables or save to CSV
- Rate-limited API calls to respect PubMed usage guidelines
- Debug mode for troubleshooting
- Built with type annotations and modular architecture

## Installation

### Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gpl.git
cd gpl
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

## Usage

### Basic Commands

Search for papers and display in terminal:
```bash
gpl "cancer therapy"
```

Save results to CSV file:
```bash
gpl "diabetes treatment" --file results.csv
```

Enable debug logging:
```bash
gpl "immunotherapy" --debug
```

Show help:
```bash
gpl --help
```

### Command Options

- `QUERY`: Search term (required) - e.g., "cancer therapy", "gene editing"
- `--file`, `-f`: Save results to specified CSV file
- `--debug`, `-d`: Enable verbose debugging output
- `--help`, `-h`: Show help message and usage examples

### Output Format

The tool provides the following information for each paper:

- **PubMed ID**: Unique identifier in PubMed database
- **Title**: Full paper title
- **Publication Date**: Formatted as "Jan 15 2024"
- **Non-academic Author(s)**: Authors affiliated with companies
- **Company Affiliation(s)**: Pharmaceutical/biotech company names
- **Corresponding Author Email**: Contact email (or "Email Unable to Retrieve")

## How It Works

### Architecture

The project is structured into two main modules:

1. **Core Module (`gpl/core.py`)**:
   - `PubMedSearcher`: Main class for API interactions
   - `PubMedPaper`: Data structure for paper information
   - `PubMedAPIError`: Custom exception handling

2. **CLI Module (`gpl/cli.py`)**:
   - Command-line interface using Click
   - Table formatting with tabulate
   - CSV export functionality
   - Progress indicators and error handling

### Company Detection Logic

The tool uses keyword-based heuristics to identify company affiliations:

**Company Keywords** (case-insensitive):
- pharma, pharmaceutical, biotech, biotechnology
- inc., ltd., llc, corp., corporation
- therapeutics, biopharm, medicines, drugs
- laboratories, technologies, gmbh, plc

**Excluded Academic Keywords**:
- university, college, institute, school
- department, faculty, hospital, clinic
- medical center, foundation, society

### API Integration

- Uses PubMed E-utilities API (free, no authentication required)
- Rate limited to 3 requests/second per NCBI guidelines
- Searches up to 50 most relevant papers per query
- Handles XML parsing for detailed paper information

## Project Structure

```
gpl/
├── gpl/
│   ├── __init__.py          # Package initialization
│   ├── core.py              # Core PubMed API and filtering logic
│   └── cli.py               # Command-line interface
├── tests/                   # Test files (future)
├── pyproject.toml           # Poetry configuration and dependencies
├── README.md                # This file
└── LICENSE                  # MIT License
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Run type checking
poetry run mypy gpl/

# Run code formatting
poetry run black gpl/

# Run linting
poetry run flake8 gpl/
```

### Testing

```bash
# Run tests (when implemented)
poetry run pytest
```

## Publishing to TestPyPI

The project is structured to support publishing to TestPyPI:

1. Build the package:
```bash
poetry build
```

2. Configure TestPyPI (one-time setup):
```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi YOUR_TESTPYPI_TOKEN
```

3. Publish to TestPyPI:
```bash
poetry publish --repository testpypi
```

## Dependencies

### Production Dependencies
- `requests`: HTTP library for API calls
- `click`: Command-line interface framework
- `tabulate`: Table formatting for console output

### Development Dependencies
- `pytest`: Testing framework
- `black`: Code formatting
- `flake8`: Code linting
- `mypy`: Static type checking
- `types-requests`, `types-tabulate`: Type stubs

## Limitations and Future Improvements

### Current Limitations
- Simplified XML parsing (production version should use proper XML parser)
- Basic keyword matching for company detection
- Limited to 50 papers per search
- Email extraction may not capture all corresponding authors

### Planned Improvements
- More sophisticated affiliation parsing using NLP
- Configurable company keyword lists
- Better XML parsing with `lxml` or `xml.etree.ElementTree`
- Pagination support for larger result sets
- Caching to reduce API calls
- More comprehensive email extraction

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Uses NCBI's PubMed E-utilities API
- Built with assistance from Claude AI for initial structure and implementation
- Inspired by the need for industry-focused biomedical literature searches

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/gpl](https://github.com/yourusername/gpl)