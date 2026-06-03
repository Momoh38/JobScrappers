"""
hireeast.py - Scrapes job listings from HireEast (East African Job Board)
"""

import re
import requests
from bs4 import BeautifulSoup

def scrape_hireeast():
    """Scrape job listings from HireEast"""
    jobs = []
    url = "https://hireeast.ng/jobs"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"     ⚠️ HireEast returned {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find job listing cards - adjust selectors based on actual site structure
        job_cards = soup.find_all('div', class_=re.compile(r'job|listing|card', re.I))
        
        for card in job_cards[:30]:
            try:
                # Extract title
                title_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'title|name', re.I))
                title = title_elem.get_text(strip=True) if title_elem else "Job Opportunity"
                
                # Extract URL
                link_elem = card.find('a', href=True)
                job_url = link_elem.get('href') if link_elem else None
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://hireeast.ng{job_url}"
                
                # Extract company
                company_elem = card.find(class_=re.compile(r'company', re.I))
                company = company_elem.get_text(strip=True) if company_elem else "Not specified"
                
                # Extract location
                location_elem = card.find(class_=re.compile(r'location', re.I))
                location = location_elem.get_text(strip=True) if location_elem else "East Africa"
                
                if job_url:
                    job = {
                        'title': title[:150],
                        'company': company[:100],
                        'location': location[:100],
                        'description': "",
                        'salary': "",
                        'url': job_url,
                        'source': 'HireEast',
                        'date_posted': "",
                        'tags': '',
                    }
                    jobs.append(job)
            except Exception:
                continue
                
        print(f"     📥 HireEast: {len(jobs)} jobs")
        return jobs
        
    except Exception as e:
        print(f"     ❌ HireEast error: {e}")
        return []
