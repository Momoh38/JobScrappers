"""
jobfound.py - Scrapes job listings from Jobfound.org
Source: https://jobfound.org
"""

import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def scrape_jobfound():
    """Scrape job listings from Jobfound.org"""
    jobs = []
    
    url = "https://jobfound.org/jobs/"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"     ⚠️ Jobfound returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find job listings
        job_elements = soup.find_all('div', class_=re.compile(r'job|listing|card|item', re.I))
        
        if not job_elements:
            job_elements = soup.find_all('article', class_=re.compile(r'job', re.I))
        
        if not job_elements:
            job_elements = soup.find_all('tr', class_=re.compile(r'job', re.I))
        
        for job_elem in job_elements[:30]:
            try:
                # Extract title
                title_elem = job_elem.find(['h2', 'h3', 'h4', 'strong', 'a'], class_=re.compile(r'title|heading|name|role', re.I))
                if not title_elem:
                    title_elem = job_elem.find('a')
                
                title = title_elem.get_text(strip=True) if title_elem else "Job Opportunity"
                
                # Extract URL
                link_elem = job_elem.find('a', href=True)
                if not link_elem:
                    link_elem = title_elem if title_elem and title_elem.get('href') else None
                
                job_url = link_elem.get('href') if link_elem else None
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://jobfound.org{job_url}"
                
                # Extract company
                company_elem = job_elem.find(class_=re.compile(r'company|employer|firm|by', re.I))
                company = company_elem.get_text(strip=True) if company_elem else "Not specified"
                
                # Extract location
                location_elem = job_elem.find(class_=re.compile(r'location|place|city|country', re.I))
                location = location_elem.get_text(strip=True) if location_elem else "Remote"
                
                # Extract description
                desc_elem = job_elem.find(class_=re.compile(r'description|desc|summary|details', re.I))
                if not desc_elem:
                    desc_elem = job_elem.find('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Extract salary if available
                salary_elem = job_elem.find(class_=re.compile(r'salary|pay|compensation', re.I))
                salary = salary_elem.get_text(strip=True) if salary_elem else ""
                
                # Extract date
                date_elem = job_elem.find(class_=re.compile(r'date|posted|time', re.I))
                date_posted = date_elem.get_text(strip=True) if date_elem else datetime.now().isoformat()
                
                if job_url:
                    job = {
                        'title': title[:150],
                        'company': company[:100],
                        'location': location[:100],
                        'description': description[:800] if description else "",
                        'salary': salary[:100],
                        'url': job_url,
                        'source': 'Jobfound',
                        'date_posted': date_posted,
                        'tags': '',
                    }
                    jobs.append(job)
                    
            except Exception as e:
                continue
        
        # Fallback: look for all job-related links
        if not jobs:
            all_links = soup.find_all('a', href=True)
            for link in all_links[:30]:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if ('/job' in href.lower() or '/jobs' in href.lower() or '/vacancy' in href.lower() or '/position' in href.lower()) and len(text) > 5:
                    if not href.startswith('http'):
                        href = f"https://jobfound.org{href}"
                    
                    job = {
                        'title': text[:100],
                        'company': "Not specified",
                        'location': "Remote",
                        'description': "",
                        'salary': "",
                        'url': href,
                        'source': 'Jobfound',
                        'date_posted': datetime.now().isoformat(),
                        'tags': '',
                    }
                    jobs.append(job)
        
        print(f"     📥 Jobfound: {len(jobs)} jobs found")
        return jobs
        
    except Exception as e:
        print(f"     ❌ Jobfound error: {e}")
        return []


if __name__ == "__main__":
    jobs = scrape_jobfound()
    for job in jobs[:3]:
        print(f"\n📋 {job['title']}")
        print(f"   🔗 {job['url']}")
