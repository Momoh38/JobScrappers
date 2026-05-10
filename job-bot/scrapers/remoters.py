"""
scrapers/remoters.py — Remoters.net remote jobs (free, no API key)
Curated worldwide remote jobs with good Nigeria-friendly timezones
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup

def scrape_remoters() -> list:
    """
    Scrapes Remoters.net for worldwide remote jobs
    Good for: Remote-first companies, flexible timezones
    """
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        # Remoters job listings page
        url = "https://remoters.net/jobs/"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job listings (adjust selectors based on actual HTML)
            job_cards = soup.find_all('div', class_=re.compile('job|listing|card'))
            
            for card in job_cards[:30]:  # Limit to 30 jobs
                # Extract job details (update selectors as needed)
                title_elem = card.find('h2') or card.find('h3') or card.find(class_=re.compile('title'))
                company_elem = card.find(class_=re.compile('company'))
                link_elem = card.find('a', href=True)
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True) if company_elem else "Remote Company"
                job_url = link_elem['href']
                if not job_url.startswith('http'):
                    job_url = f"https://remoters.net{job_url}"
                
                # Extract location (usually remote/worldwide)
                location_elem = card.find(class_=re.compile('location'))
                location = location_elem.get_text(strip=True) if location_elem else "Worldwide Remote"
                
                # Extract salary if present
                salary_elem = card.find(class_=re.compile('salary'))
                salary = salary_elem.get_text(strip=True) if salary_elem else "Competitive"
                
                # Get description snippet
                desc_elem = card.find(class_=re.compile('description|excerpt'))
                description = desc_elem.get_text(strip=True)[:400] if desc_elem else "Remote position"
                
                # Extract tags/skills
                tags_elem = card.find(class_=re.compile('tags|skills'))
                tags = tags_elem.get_text(strip=True) if tags_elem else "Remote, Worldwide"
                
                # Nigeria-friendly check
                if not is_remoters_nigeria_friendly(title, description, location):
                    continue
                
                job_id = hashlib.md5(f"{job_url}{title}".encode()).hexdigest()
                
                jobs.append({
                    "id": f"remoters_{job_id}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": salary,
                    "description": clean_description(description),
                    "tags": tags,
                    "url": job_url,
                    "source": "Remoters",
                    "suitable_for_nigeria": "Yes (Worldwide Remote)",
                })
                
    except Exception as e:
        print(f"     ⚠️ Remoters failed: {e}")
    
    return jobs


def is_remoters_nigeria_friendly(title, description, location):
    """Check if job is suitable for Nigerian applicants"""
    text = (title + " " + description + " " + location).lower()
    
    # Exclude clearly non-friendly
    exclude = ["us only", "usa only", "uk only", "eu only", "must be citizen"]
    for word in exclude:
        if word in text:
            return False
    
    # Include worldwide/remote
    include = ["worldwide", "anywhere", "global", "remote", "any location"]
    for word in include:
        if word in text or "remote" in location.lower():
            return True
    
    return True  # Default to include


def clean_description(text):
    """Clean up description text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove HTML if any
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()
