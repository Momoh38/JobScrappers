"""
revicemycv.py - Scrapes job listings from ReviceMyCV Jobs
"""

import re
import requests
from bs4 import BeautifulSoup

def scrape_revicemycv():
    """Scrape job listings from ReviceMyCV Jobs"""
    jobs = []
    url = "https://jobs.revicemycv.com"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"     ⚠️ ReviceMyCV returned {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find job listing elements based on the content you provided
        # Looking for elements that contain job titles like "Heritage Petroleum Company Limited is Recruiting..."
        job_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'job|post|listing|opportunity', re.I))
        
        # If specific class fails, try finding all links that look like job posts
        if not job_elements:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                # Look for job-related patterns in the link text or URL
                if ('recruiting' in text.lower() or 'hiring' in text.lower() or 'programme' in text.lower() or 'internship' in text.lower()) and len(text) > 15:
                    if href.startswith('/'):
                        full_url = f"https://jobs.revicemycv.com{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    job = {
                        'title': text[:150],
                        'company': "Not specified",
                        'location': "Nigeria/International",
                        'description': "",
                        'salary': "",
                        'url': full_url,
                        'source': 'ReviceMyCV',
                        'date_posted': "",
                        'tags': '',
                    }
                    jobs.append(job)
            
            # Remove duplicates by URL
            seen = set()
            unique_jobs = []
            for job in jobs:
                if job['url'] not in seen:
                    seen.add(job['url'])
                    unique_jobs.append(job)
            jobs = unique_jobs
            
        else:
            # Parse job cards if found
            for elem in job_elements[:30]:
                try:
                    link_elem = elem.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    job_url = link_elem.get('href')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://jobs.revicemycv.com{job_url}"
                    
                    title = link_elem.get_text(strip=True) or "Job Opportunity"
                    
                    # Try to extract company and location from text
                    text = elem.get_text()
                    company = "Not specified"
                    location = "Nigeria/International"
                    
                    # Look for common patterns
                    company_match = re.search(r'(?:at|@)\s+([A-Z][a-zA-Z\s]+)(?:\n|$)', text)
                    if company_match:
                        company = company_match.group(1).strip()[:100]
                    
                    location_match = re.search(r'Location:\s*([^\n]+)', text, re.I)
                    if location_match:
                        location = location_match.group(1).strip()[:100]
                    
                    if job_url:
                        job = {
                            'title': title[:150],
                            'company': company,
                            'location': location,
                            'description': "",
                            'salary': "",
                            'url': job_url,
                            'source': 'ReviceMyCV',
                            'date_posted': "",
                            'tags': '',
                        }
                        jobs.append(job)
                except Exception:
                    continue
        
        print(f"     📥 ReviceMyCV: {len(jobs)} jobs")
        return jobs[:50]  # Limit to 50 jobs per run
        
    except Exception as e:
        print(f"     ❌ ReviceMyCV error: {e}")
        return []
