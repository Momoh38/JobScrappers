"""
scrapers/pangaea.py — Alternative global remote jobs (Pangaea alternative)
Since Pangaea API has SSL issues, using alternative sources
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_pangaea() -> list:
    """
    Alternative global remote jobs scraper
    (Pangaea has SSL issues - using similar global remote sources)
    """
    jobs = []
    
    # Source 1: RemoteOK Global (already have but including for completeness)
    jobs.extend(scrape_global_remote_alternative())
    
    # Source 2: We Work Remotely Global
    jobs.extend(scrape_global_remote_rss())
    
    return deduplicate_jobs(jobs)


def scrape_global_remote_alternative() -> list:
    """Alternative global remote job source"""
    jobs = []
    session = requests.Session()
    session.verify = False
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    })
    
    try:
        # Use a reliable global remote job API
        url = "https://remotive.com/api/remote-jobs"
        response = session.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            for job in data.get('jobs', [])[:30]:
                # Filter for truly global roles
                location = job.get('candidate_required_location', 'Worldwide')
                
                # Skip US/EU only roles
                if any(term in location.lower() for term in ['us only', 'usa only', 'eu only']):
                    continue
                
                job_id = hashlib.md5(str(job.get('id', '')).encode()).hexdigest()
                
                # Extract salary
                salary = job.get('salary', '')
                if not salary:
                    salary = extract_salary_alternative(job.get('description', ''))
                
                jobs.append({
                    "id": f"pangaea_alt_{job_id}",
                    "title": job.get('title', ''),
                    "company": job.get('company_name', 'Global Company'),
                    "location": location if 'remote' in location.lower() else f"{location} (Remote)",
                    "salary": salary if salary else "Competitive",
                    "description": clean_job_description(job.get('description', ''))[:500],
                    "tags": "Remote, Global, Worldwide",
                    "url": job.get('url', ''),
                    "source": "GlobalRemote",
                    "suitable_for_nigeria": "Yes" if 'worldwide' in location.lower() else "Check",
                })
                
    except Exception as e:
        print(f"     ⚠️ Global remote alternative failed: {e}")
    
    return jobs


def scrape_global_remote_rss() -> list:
    """RSS-based global jobs"""
    jobs = []
    session = requests.Session()
    session.verify = False
    
    try:
        import xml.etree.ElementTree as ET
        
        rss_urls = [
            "https://weworkremotely.com/remote-jobs.rss",
            "https://jobs.github.com/positions.json",  # GitHub jobs (global)
        ]
        
        for url in rss_urls:
            try:
                response = session.get(url, timeout=10)
                if response.status_code == 200:
                    if 'rss' in url:
                        root = ET.fromstring(response.content)
                        for item in root.findall(".//item")[:20]:
                            title = item.findtext("title", "")
                            link = item.findtext("link", "")
                            desc = item.findtext("description", "")
                            
                            if not title:
                                continue
                            
                            # Extract company from title
                            company = "Remote Company"
                            if ": " in title:
                                parts = title.split(": ", 1)
                                company, title = parts[0], parts[1]
                            
                            job_id = hashlib.md5(link.encode()).hexdigest()
                            jobs.append({
                                "id": f"pangaea_rss_{job_id}",
                                "title": title,
                                "company": company,
                                "location": "Worldwide Remote",
                                "salary": extract_salary_alternative(desc),
                                "description": clean_job_description(desc)[:400],
                                "tags": "Remote, Global",
                                "url": link,
                                "source": "GlobalRSS",
                            })
                    elif 'github' in url:
                        # GitHub Jobs API (global)
                        for job in response.json()[:20]:
                            if 'remote' in job.get('location', '').lower() or job.get('remote'):
                                job_id = hashlib.md5(str(job.get('id', '')).encode()).hexdigest()
                                jobs.append({
                                    "id": f"pangaea_github_{job_id}",
                                    "title": job.get('title', ''),
                                    "company": job.get('company', ''),
                                    "location": "Worldwide Remote",
                                    "salary": "Check listing",
                                    "description": clean_job_description(job.get('description', ''))[:400],
                                    "tags": "Remote, Tech",
                                    "url": job.get('url', ''),
                                    "source": "GitHubJobs",
                                })
                                
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"     ⚠️ RSS fallback failed: {e}")
    
    return jobs


def extract_salary_alternative(text):
    """Extract salary from text"""
    patterns = [
        r'\$(\d+(?:,\d{3})*)\s*[-–]\s*\$(\d+(?:,\d{3})*)',
        r'\$(\d+(?:,\d{3})*)\/?(?:month|year|mo|yr)',
        r'(?:₦|N)(\d+(?:,\d{3})*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 2:
                return f"${match.group(1)}-${match.group(2)}"
            else:
                return f"${match.group(1)}+"
    return ""


def clean_job_description(text):
    """Clean HTML from description"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def deduplicate_jobs(jobs):
    """Remove duplicates"""
    seen = set()
    unique = []
    for job in jobs:
        job_key = f"{job.get('title', '')}_{job.get('company', '')}"
        if job_key not in seen:
            seen.add(job_key)
            unique.append(job)
    return unique[:50]  # Limit to 50 jobs
