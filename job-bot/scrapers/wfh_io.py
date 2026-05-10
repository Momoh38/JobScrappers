"""
scrapers/wfh_io.py — WFH.io remote jobs with SSL workaround
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings (only for specific problematic sites)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_wfh_io() -> list:
    """
    Scrapes WFH.io for worldwide remote jobs with SSL workaround
    """
    jobs = []
    
    # Custom session with SSL workaround
    session = requests.Session()
    session.verify = False  # Disable SSL verification for this site only
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
    })
    
    try:
        # Try with http instead of https
        url = "http://wfh.io/jobs"
        response = session.get(url, timeout=20, allow_redirects=True)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for job listings with broader selectors
            job_items = []
            
            # Try different selectors
            job_items = soup.find_all('div', class_=re.compile('job|post|listing')) or \
                       soup.find_all('article') or \
                       soup.find_all('li', class_=re.compile('job'))
            
            if not job_items:
                # Try finding all links that look like job posts
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if '/jobs/' in href or '/job/' in href:
                        parent = link.find_parent(['div', 'article', 'li'])
                        if parent and parent not in job_items:
                            job_items.append(parent)
            
            for item in job_items[:40]:
                # Extract title
                title_elem = item.find(['h1', 'h2', 'h3', 'h4']) or item.find(class_=re.compile('title'))
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 3:
                    continue
                
                # Extract link
                link_elem = item.find('a', href=True)
                job_url = link_elem['href'] if link_elem else ""
                if job_url and not job_url.startswith('http'):
                    job_url = f"http://wfh.io{job_url}"
                
                # Extract company
                company_elem = item.find(class_=re.compile('company')) or item.find('span', class_=re.compile('org'))
                company = company_elem.get_text(strip=True) if company_elem else "Remote Company"
                
                # Clean company name
                company = re.sub(r'at\s+', '', company, flags=re.I)
                
                # Extract description
                desc_elem = item.find(class_=re.compile('description|excerpt|summary')) or item.find('p')
                description = desc_elem.get_text(strip=True)[:500] if desc_elem else "Remote work opportunity"
                description = clean_description(description)
                
                # Create job ID
                job_id = hashlib.md5(f"{job_url}{title}".encode()).hexdigest()
                
                jobs.append({
                    "id": f"wfhio_{job_id}",
                    "title": title,
                    "company": company,
                    "location": "Worldwide Remote",
                    "salary": extract_salary(description),
                    "description": description,
                    "tags": "Work From Home, Remote, Global",
                    "url": job_url,
                    "source": "WFH.io",
                })
        
        else:
            print(f"     ⚠️ WFH.io returned status {response.status_code}")
            
    except Exception as e:
        print(f"     ⚠️ WFH.io failed: {e}")
    
    return deduplicate_jobs(jobs)


def extract_salary(text):
    """Extract salary from text"""
    patterns = [
        r'\$(\d+(?:,\d{3})*)\s*[-–]\s*\$(\d+(?:,\d{3})*)',
        r'\$(\d+(?:,\d{3})*)\/?(?:month|year|mo|yr|annum)',
        r'(\d+(?:,\d{3})*)\s*(?:USD|EUR|GBP)',
        r'(?:salary|pay|compensation)[:\s]*\$?(\d+(?:,\d{3})*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 2:
                return f"${match.group(1)}-${match.group(2)}"
            else:
                return f"${match.group(1)}+"
    return "Check listing"


def clean_description(text):
    """Clean description text"""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Apply now|Click here|Read more', '', text, flags=re.I)
    return text.strip()[:500]


def deduplicate_jobs(jobs):
    """Remove duplicates by URL"""
    seen = set()
    unique = []
    for job in jobs:
        if job['url'] not in seen:
            seen.add(job['url'])
            unique.append(job)
    return unique
