"""
yeshub.py - Scrapes job listings from YesHub.ng
"""

import re
import requests
from bs4 import BeautifulSoup

def scrape_yeshub():
    """Scrape job listings from YesHub.ng"""
    jobs = []
    url = "https://yeshub.ng/jobs"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"     ⚠️ YesHub returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find job listing cards (based on the site's structure)
        job_cards = soup.find_all('div', class_=re.compile(r'job|listing|card|vacancy', re.I))
        
        # If no cards found, try finding articles or list items
        if not job_cards:
            job_cards = soup.find_all('article', class_=re.compile(r'job', re.I))
        
        if not job_cards:
            job_cards = soup.find_all('li', class_=re.compile(r'job', re.I))
        
        for card in job_cards[:30]:
            try:
                # Extract title
                title_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'title|name|heading', re.I))
                if not title_elem:
                    title_elem = card.find('a')
                
                title = title_elem.get_text(strip=True) if title_elem else "Job Opportunity"
                
                # Extract URL
                link_elem = card.find('a', href=True)
                job_url = link_elem.get('href') if link_elem else None
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://yeshub.ng{job_url}"
                
                # Extract company
                company_elem = card.find(class_=re.compile(r'company|employer', re.I))
                company = company_elem.get_text(strip=True) if company_elem else "Not specified"
                
                # Extract location
                location_elem = card.find(class_=re.compile(r'location|place|address', re.I))
                location = location_elem.get_text(strip=True) if location_elem else "Nigeria"
                
                # Extract description (if available)
                desc_elem = card.find(class_=re.compile(r'description|desc|summary', re.I))
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Extract date posted (if available)
                date_elem = card.find(class_=re.compile(r'date|posted|time', re.I))
                date_posted = date_elem.get_text(strip=True) if date_elem else ""
                
                if job_url and title:
                    job = {
                        'title': title[:150],
                        'company': company[:100],
                        'location': location[:100],
                        'description': description[:800] if description else "",
                        'salary': "",
                        'url': job_url,
                        'source': 'YesHub',
                        'date_posted': date_posted,
                        'tags': '',
                    }
                    jobs.append(job)
                    
            except Exception as e:
                # Silent continue for individual job parsing errors
                continue
        
        # Fallback: If no job cards found, try finding all links with job patterns
        if not jobs:
            all_links = soup.find_all('a', href=True)
            for link in all_links[:30]:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if ('/job/' in href or '/jobs/' in href or '/vacancy' in href) and len(text) > 5:
                    if not href.startswith('http'):
                        href = f"https://yeshub.ng{href}"
                    
                    job = {
                        'title': text[:100],
                        'company': "Not specified",
                        'location': "Nigeria",
                        'description': "",
                        'salary': "",
                        'url': href,
                        'source': 'YesHub',
                        'date_posted': "",
                        'tags': '',
                    }
                    jobs.append(job)
        
        print(f"     📥 YesHub: {len(jobs)} jobs found")
        return jobs
        
    except Exception as e:
        print(f"     ❌ YesHub error: {e}")
        return []
