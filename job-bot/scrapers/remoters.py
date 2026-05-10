"""
scrapers/remoters.py — Remoters.net with SSL workaround
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_remoters() -> list:
    """
    Scrapes Remoters.net with SSL workaround
    """
    jobs = []
    session = requests.Session()
    session.verify = False
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    
    try:
        # Try HTTP first
        url = "http://remoters.net/jobs/"
        response = session.get(url, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job listings
            job_cards = soup.find_all('div', class_=re.compile('job|post|listing')) or \
                       soup.find_all('article') or \
                       soup.find_all('li', class_=re.compile('job'))
            
            for card in job_cards[:30]:
                # Extract title
                title_elem = card.find(['h1', 'h2', 'h3']) or card.find(class_=re.compile('title'))
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title:
                    continue
                
                # Extract link
                link_elem = card.find('a', href=True)
                job_url = link_elem['href'] if link_elem else ""
                if job_url and not job_url.startswith('http'):
                    job_url = f"http://remoters.net{job_url}"
                
                # Extract company
                company_elem = card.find(class_=re.compile('company'))
                company = company_elem.get_text(strip=True) if company_elem else "Remote Company"
                
                # Extract location
                location_elem = card.find(class_=re.compile('location'))
                location = location_elem.get_text(strip=True) if location_elem else "Worldwide Remote"
                
                # Extract description
                desc_elem = card.find(class_=re.compile('description')) or card.find('p')
                description = desc_elem.get_text(strip=True)[:400] if desc_elem else "Remote position"
                description = clean_remoters_description(description)
                
                job_id = hashlib.md5(f"{job_url}{title}".encode()).hexdigest()
                
                jobs.append({
                    "id": f"remoters_{job_id}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": "Check listing",
                    "description": description,
                    "tags": "Remote, Worldwide",
                    "url": job_url,
                    "source": "Remoters",
                })
                
    except Exception as e:
        print(f"     ⚠️ Remoters failed: {e}")
    
    return deduplicate_remoters(jobs)


def clean_remoters_description(text):
    """Clean description"""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def deduplicate_remoters(jobs):
    """Remove duplicates"""
    seen = set()
    unique = []
    for job in jobs:
        if job['url'] not in seen:
            seen.add(job['url'])
            unique.append(job)
    return unique
