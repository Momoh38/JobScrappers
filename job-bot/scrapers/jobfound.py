"""
jobfound.py - Scrapes job-related content from Jobfound.org
UPDATED: Searches for job postings across the site
"""

import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape_jobfound():
    """Scrape job-related content from Jobfound.org"""
    jobs = []
    seen_urls = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    base_url = "https://jobfound.org"
    
    # Try different possible URLs
    urls_to_try = [
        base_url,
        f"{base_url}/jobs",
        f"{base_url}/job",
        f"{base_url}/vacancies",
        f"{base_url}/careers",
        f"{base_url}/opportunities",
        f"{base_url}/work-from-home",
        f"{base_url}/home-jobs",
    ]
    
    all_job_urls = []
    
    for url in urls_to_try:
        try:
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            if response.status_code == 200:
                print(f"     📍 Found page: {url}")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for job-related links
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    # Keywords that indicate job content
                    job_keywords = ['job', 'vacancy', 'hiring', 'career', 'employment', 'opportunity', 'position', 'work', 'remote']
                    
                    if any(keyword in href.lower() for keyword in job_keywords) or any(keyword in text.lower() for keyword in job_keywords):
                        if href.startswith('/'):
                            full_url = urljoin(base_url, href)
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            continue
                        
                        # Filter out non-job pages
                        if full_url not in seen_urls and full_url != base_url:
                            seen_urls.add(full_url)
                            # Only add if it looks like a job page
                            if any(keyword in full_url.lower() for keyword in ['job', 'vacancy', 'career']):
                                all_job_urls.append(full_url)
                
                # Also look for job listings in the page content
                text_content = soup.get_text()
                job_sections = re.finditer(r'(?i)(job|vacancy|hiring|career|opportunity).{0,200}', text_content)
                for match in job_sections[:10]:
                    context = match.group(0)
                    # Try to extract potential job titles from context
                    title_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', context)
                    if title_match and len(title_match.group(0)) > 10:
                        potential_job = {
                            'title': title_match.group(0),
                            'company': 'Not specified',
                            'location': 'Remote/Nigeria',
                            'description': context[:300],
                            'salary': '',
                            'url': url,
                            'source': 'Jobfound',
                            'date_posted': datetime.now().isoformat(),
                            'tags': '',
                        }
                        jobs.append(potential_job)
                        
        except Exception as e:
            continue
    
    # If we found job URLs, scrape them
    for job_url in all_job_urls[:30]:
        try:
            response = requests.get(job_url, headers=headers, timeout=30)
            if response.status_code != 200:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to extract title
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Job Opportunity"
            
            # Try to extract description
            desc_elem = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content', re.I))
            description = ""
            if desc_elem:
                for unwanted in desc_elem.find_all(['script', 'style']):
                    unwanted.decompose()
                description = desc_elem.get_text(strip=True)
                description = re.sub(r'\s+', ' ', description)
                description = description[:500]
            
            job = {
                'title': title[:150],
                'company': 'Not specified',
                'location': 'Remote/Nigeria',
                'description': description if description else "Click Apply Now button for details",
                'salary': '',
                'url': job_url,
                'source': 'Jobfound',
                'date_posted': datetime.now().isoformat(),
                'tags': '',
            }
            jobs.append(job)
            
        except Exception as e:
            continue
    
    print(f"     📥 Jobfound: {len(jobs)} job listings found")
    return jobs


if __name__ == "__main__":
    jobs = scrape_jobfound()
    print(f"\n✅ Total: {len(jobs)} jobs")
    for job in jobs[:3]:
        print(f"\n📋 {job['title']}")
        print(f"   🔗 {job['url']}")
