"""
scrapers/wfh_io.py — WFH.io (Work From Home) remote jobs
Curated remote jobs from companies that hire globally
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_wfh_io() -> list:
    """
    Scrapes WFH.io for worldwide remote jobs
    Great for: Entry to senior level remote positions
    """
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        # WFH.io job listings
        url = "https://wfh.io/jobs"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job listings - common selectors for WFH.io
            job_cards = soup.find_all('article', class_=re.compile('job|listing')) or \
                       soup.find_all('div', class_=re.compile('job')) or \
                       soup.find_all('li', class_=re.compile('job'))
            
            if not job_cards:
                # Try alternative parsing
                job_cards = soup.find_all('a', href=True, class_=re.compile('job'))
            
            for card in job_cards[:40]:  # Limit to 40 jobs
                # Extract title
                title_elem = card.find('h2') or card.find('h3') or card.find(class_=re.compile('title'))
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title:
                    continue
                
                # Extract company
                company_elem = card.find(class_=re.compile('company')) or card.find('span', class_=re.compile('company'))
                company = company_elem.get_text(strip=True) if company_elem else "Remote Company"
                
                # Extract link
                link_elem = card.find('a', href=True)
                job_url = link_elem['href'] if link_elem else ""
                if job_url and not job_url.startswith('http'):
                    job_url = f"https://wfh.io{job_url}"
                
                # Extract location (usually remote)
                location_elem = card.find(class_=re.compile('location'))
                location = location_elem.get_text(strip=True) if location_elem else "Worldwide Remote"
                
                # Extract salary
                salary_elem = card.find(class_=re.compile('salary')) or card.find(class_=re.compile('pay'))
                salary = salary_elem.get_text(strip=True) if salary_elem else extract_salary_from_text(card.get_text())
                
                # Extract description
                desc_elem = card.find(class_=re.compile('description')) or card.find('p')
                description = desc_elem.get_text(strip=True)[:500] if desc_elem else "Remote work opportunity"
                
                # Extract tags/category
                tags_elem = card.find(class_=re.compile('tags')) or card.find(class_=re.compile('category'))
                tags = tags_elem.get_text(strip=True) if tags_elem else "Remote, Flexible"
                
                # Extract date posted
                date_elem = card.find('time') or card.find(class_=re.compile('date'))
                date_posted = date_elem.get('datetime', '') if date_elem else ""
                
                # Check Nigeria-friendliness
                if not is_wfh_nigeria_friendly(title, description, location):
                    continue
                
                # Create unique ID
                job_id = hashlib.md5(f"{job_url}{title}{company}".encode()).hexdigest()
                
                jobs.append({
                    "id": f"wfhio_{job_id}",
                    "title": title,
                    "company": company,
                    "location": location if "remote" in location.lower() else f"{location} (Remote-Friendly)",
                    "salary": salary if salary else "Competitive",
                    "description": clean_wfh_description(description),
                    "tags": f"{tags}, Work From Home, Global",
                    "date_posted": date_posted,
                    "url": job_url,
                    "source": "WFH.io",
                    "suitable_for_nigeria": "Yes (Worldwide Remote)",
                    "apply_tips": "WFH.io jobs are remote-first - apply directly through company link"
                })
                
        else:
            # Try fallback RSS feed if available
            return scrape_wfh_io_rss_fallback()
            
    except Exception as e:
        print(f"     ⚠️ WFH.io failed: {e}")
        # Try fallback
        return scrape_wfh_io_rss_fallback()
    
    # Deduplicate by URL
    seen_urls = set()
    unique_jobs = []
    for job in jobs:
        if job["url"] not in seen_urls:
            seen_urls.add(job["url"])
            unique_jobs.append(job)
    
    return unique_jobs


def scrape_wfh_io_rss_fallback() -> list:
    """Fallback RSS feed if main page fails"""
    jobs = []
    try:
        # Some job sites have RSS feeds
        rss_url = "https://wfh.io/jobs.rss"
        headers = {"User-Agent": "HalalJobsBot/1.0"}
        
        response = requests.get(rss_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            for item in root.findall(".//item")[:30]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                description = item.findtext("description", "")
                
                if not title or not link:
                    continue
                
                # Extract company from title (format: "Job Title at Company")
                company = "Remote Company"
                if " at " in title:
                    parts = title.split(" at ", 1)
                    title, company = parts[0], parts[1]
                
                job_id = hashlib.md5(link.encode()).hexdigest()
                
                jobs.append({
                    "id": f"wfhio_rss_{job_id}",
                    "title": title,
                    "company": company,
                    "location": "Worldwide Remote",
                    "salary": "Check listing",
                    "description": clean_wfh_description(description[:400]),
                    "tags": "Remote, Worldwide, WFH",
                    "url": link,
                    "source": "WFH.io (RSS)",
                    "suitable_for_nigeria": "Yes",
                })
                
    except Exception as e:
        print(f"     ⚠️ WFH.io RSS fallback failed: {e}")
    
    return jobs


def is_wfh_nigeria_friendly(title, description, location):
    """Filter for Nigeria-friendly jobs"""
    text = (title + " " + description + " " + location).lower()
    
    # Must be remote-friendly
    if "remote" not in text and "work from home" not in text and "wfh" not in text:
        return False
    
    # Exclude clearly non-friendly
    exclude_terms = [
        "us only", "usa only", "uk only", "canada only", "australia only",
        "must be us citizen", "green card", "work authorization required",
        "cannot sponsor", "no sponsorship"
    ]
    
    for term in exclude_terms:
        if term in text:
            return False
    
    # Include worldwide/global roles
    include_terms = ["worldwide", "global", "anywhere", "any location", "all countries"]
    for term in include_terms:
        if term in text:
            return True
    
    # Default to include if remote
    return "remote" in text


def extract_salary_from_text(text):
    """Extract salary information from text"""
    patterns = [
        r'\$(\d+(?:,\d{3})*)\s*-\s*\$(\d+(?:,\d{3})*)',
        r'\$(\d+(?:,\d{3})*)\/?(?:month|year|mo|yr)',
        r'(\d+(?:,\d{3})*)\s*USD',
        r'(\d+(?:,\d{3})*)\s*EUR',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 2:
                return f"${match.group(1)}-${match.group(2)}"
            else:
                return f"${match.group(1)}+"
    return ""


def clean_wfh_description(text):
    """Clean HTML and normalize whitespace"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text[:500]
