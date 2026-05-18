"""
jobsregion.py - Scrapes job listings from Jobsregion.com
Source: https://jobsregion.com
"""

import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def scrape_jobsregion():
    """Scrape job listings from Jobsregion.com"""
    jobs = []
    
    url = "https://jobsregion.com/jobs/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"     ⚠️ Jobsregion returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find job listings - looking for job cards/containers
        job_elements = soup.find_all('div', class_=re.compile(r'job|listing|card|post', re.I))
        
        # Alternative: look for article or li elements with job class
        if not job_elements:
            job_elements = soup.find_all('article', class_=re.compile(r'job', re.I))
        
        if not job_elements:
            job_elements = soup.find_all('li', class_=re.compile(r'job', re.I))
        
        for job_elem in job_elements[:30]:  # Limit to 30 jobs per run
            try:
                # Extract title
                title_elem = job_elem.find(['h2', 'h3', 'h4'], class_=re.compile(r'title|heading|name', re.I))
                if not title_elem:
                    title_elem = job_elem.find('a', class_=re.compile(r'title', re.I))
                
                title = title_elem.get_text(strip=True) if title_elem else "Job Opportunity"
                
                # Extract URL
                link_elem = job_elem.find('a', href=True)
                if not link_elem:
                    link_elem = title_elem if title_elem and title_elem.get('href') else None
                
                job_url = link_elem.get('href') if link_elem else None
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://jobsregion.com{job_url}"
                
                # Extract company
                company_elem = job_elem.find(class_=re.compile(r'company|employer|org', re.I))
                company = company_elem.get_text(strip=True) if company_elem else "Not specified"
                
                # Extract location
                location_elem = job_elem.find(class_=re.compile(r'location|place|address', re.I))
                location = location_elem.get_text(strip=True) if location_elem else "Nigeria/Remote"
                
                # Extract description (if available)
                desc_elem = job_elem.find(class_=re.compile(r'description|desc|summary|excerpt', re.I))
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Extract date posted
                date_elem = job_elem.find(class_=re.compile(r'date|posted|time', re.I))
                date_posted = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()
                
                if job_url:
                    job = {
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description[:800] if description else "",
                        'salary': "",
                        'url': job_url,
                        'source': 'Jobsregion',
                        'date_posted': date_posted,
                        'tags': '',
                    }
                    jobs.append(job)
                    
            except Exception as e:
                continue
        
        # If no jobs found with selectors, try a different approach - look for all links with job patterns
        if not jobs:
            all_links = soup.find_all('a', href=True)
            for link in all_links[:30]:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for job-like patterns in URL or text
                if ('/job/' in href or '/jobs/' in href or '/vacancy' in href) and len(text) > 5:
                    if not href.startswith('http'):
                        href = f"https://jobsregion.com{href}"
                    
                    job = {
                        'title': text[:100],
                        'company': "Not specified",
                        'location': "Nigeria/Remote",
                        'description': "",
                        'salary': "",
                        'url': href,
                        'source': 'Jobsregion',
                        'date_posted': datetime.now().isoformat(),
                        'tags': '',
                    }
                    jobs.append(job)
        
        print(f"     📥 Jobsregion: {len(jobs)} jobs found")
        return jobs
        
    except Exception as e:
        print(f"     ❌ Jobsregion error: {e}")
        return []


if __name__ == "__main__":
    jobs = scrape_jobsregion()
    for job in jobs[:3]:
        print(f"\n📋 {job['title']}")
        print(f"   🔗 {job['url']}")
