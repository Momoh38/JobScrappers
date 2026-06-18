# Contributing to JobScrappers

Thank you for your interest in contributing to JobScrappers! This document provides guidelines for contributing to the project.

## How to Contribute

### 1. Reporting Issues

Before reporting an issue, please check:
- The existing issues list to avoid duplicates
- The troubleshooting section in the README

When reporting an issue, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Any relevant error messages or logs
- Your environment (OS, Python version, etc.)

### 2. Suggesting New Sources

We welcome suggestions for new job sources! Please ensure:
- The source is publicly accessible (no login required)
- The jobs are free to apply (no payment required)
- The source is Nigeria-friendly (remote or Nigeria-based)
- The source posts real jobs (not GPT/survey/task sites)

**To suggest a source:**
1. Open a new issue
2. Title: "New Source Suggestion: [Source Name]"
3. Include the URL and any relevant information

### 3. Submitting Code Changes

1. **Fork the repository**
2. **Create a new branch** for your changes
3. **Make your changes** following the project style
4. **Test your changes** before submitting
5. **Submit a Pull Request** with a clear description

### 4. Code Style Guidelines

- Follow PEP 8 style guidelines
- Use meaningful variable names
- Add comments for complex logic
- Include docstrings for functions
- Keep functions focused and concise

### 5. Adding a New Scraper

When adding a new scraper:

1. Create a new file in `job-bot/scrapers/`
2. Name it according to the source (e.g., `newsource.py`)
3. Follow the existing scraper pattern:

```python
def scrape_newsource():
    """Scrape job listings from NewSource"""
    jobs = []
    # Your scraping logic here
    return jobs
```

Add the scraper to main.py

Add the source to the README

### 6. Pull Request Process
Ensure your code passes all checks

Update the README if adding a new source

Add yourself to the contributors list (optional)

Submit the pull request with a clear description

Be responsive to review feedback

Code of Conduct
Please be respectful and constructive in all interactions. We aim to build a positive, inclusive community.

License
By contributing, you agree that your contributions will be licensed under the project's MIT License.
