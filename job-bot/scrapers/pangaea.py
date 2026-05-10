"""
scrapers/pangaea.py — Pangaea (https://pangaea.co) global remote jobs
Focuses on connecting global talent with remote-first companies
Good for Nigerians seeking international remote work
"""

import requests
import hashlib
import re
from datetime import datetime, timedelta

def scrape_pangaea() -> list:
    """
    Scrapes Pangaea for global remote jobs
    Pangaea specializes in helping global talent find remote work
    """
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    try:
        # Pangaea API endpoint (public)
        api_url = "https://api.pangaea.co/jobs"
        params = {
            "limit": 50,
            "remote": "true",
            "global": "true",
            "order": "newest"
        }
        
        response = requests.get(api_url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            jobs_data = data.get("jobs", data.get("data", []))
            
            for job in jobs_data:
                # Check if job is globally available
                location_restrictions = job.get("location_restrictions", job.get("restrictions", []))
                
                # Skip if location restricted to specific countries excluding Nigeria
                if location_restrictions and not is_nigeria_allowed(location_restrictions):
                    continue
                
                # Check timezone compatibility
                timezone_req = job.get("timezone", job.get("working_hours", ""))
                timezone_score = check_timezone_compatibility(timezone_req)
                
                # Extract visa/relocation info
                visa_support = job.get("visa_sponsorship", False) or job.get("relocation", False)
                
                # Format salary
                salary_min = job.get("salary_min", job.get("min_salary", ""))
                salary_max = job.get("salary_max", job.get("max_salary", ""))
                salary_currency = job.get("currency", "USD")
                salary = format_pangaea_salary(salary_min, salary_max, salary_currency)
                
                # Extract skills
                skills = job.get("skills", job.get("tags", []))
                if isinstance(skills, str):
                    skills = [skills]
                tags = ", ".join(skills[:5]) if skills else "Remote, Global"
                
                if visa_support:
                    tags += ", Visa Sponsorship"
                
                # Get description
                description = job.get("description", job.get("overview", ""))
                
                # Nigeria-friendliness score
                friendly_score = calculate_nigeria_friendly_score(job)
                
                job_id = hashlib.md5(str(job.get("id", job.get("slug", ""))).encode()).hexdigest()
                
                jobs.append({
                    "id": f"pangaea_{job_id}",
                    "title": job.get("title", ""),
                    "company": job.get("company_name", job.get("company", "")),
                    "location": job.get("location", "Worldwide Remote"),
                    "salary": salary,
                    "description": clean_pangaea_description(description)[:500],
                    "tags": tags,
                    "experience": job.get("experience_level", "Not Specified"),
                    "timezone_requirement": timezone_req,
                    "timezone_score": timezone_score,
                    "visa_sponsorship": "Yes" if visa_support else "Check listing",
                    "url": job.get("application_url", job.get("url", f"https://pangaea.co/jobs/{job.get('slug', '')}")),
                    "source": "Pangaea",
                    "nigeria_friendly_score": friendly_score,
                    "suitable_for_nigeria": "Yes" if friendly_score >= 3 else "Possible",
                })
                
        else:
            # Try alternative endpoint
            return scrape_pangaea_fallback()
            
    except requests.exceptions.JSONDecodeError:
        # Try HTML scraping fallback
        return scrape_pangaea_html_fallback()
    except Exception as e:
        print(f"     ⚠️ Pangaea failed: {e}")
        return scrape_pangaea_fallback()
    
    return jobs


def scrape_pangaea_fallback() -> list:
    """Fallback to alternative API or HTML scraping"""
    jobs = []
    headers = {"User-Agent": "HalalJobsBot/1.0"}
    
    try:
        # Alternative feed (if available)
        feed_url = "https://pangaea.co/jobs/feed"
        response = requests.get(feed_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Try JSON if it's JSON
            try:
                data = response.json()
                if isinstance(data, list):
                    for job in data[:30]:
                        job_id = hashlib.md5(str(job.get("id", "")).encode()).hexdigest()
                        jobs.append({
                            "id": f"pangaea_fb_{job_id}",
                            "title": job.get("title", ""),
                            "company": job.get("company", ""),
                            "location": "Worldwide Remote",
                            "salary": "Competitive",
                            "description": job.get("description", "")[:400],
                            "tags": "Remote, Global",
                            "url": job.get("url", ""),
                            "source": "Pangaea",
                        })
            except:
                # Not JSON, try RSS
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                for item in root.findall(".//item")[:30]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    desc = item.findtext("description", "")
                    
                    job_id = hashlib.md5(link.encode()).hexdigest()
                    jobs.append({
                        "id": f"pangaea_rss_{job_id}",
                        "title": title,
                        "company": "Global Company",
                        "location": "Worldwide Remote",
                        "salary": "Check listing",
                        "description": clean_pangaea_description(desc)[:400],
                        "tags": "Remote, Global",
                        "url": link,
                        "source": "Pangaea",
                    })
                    
    except Exception as e:
        print(f"     ⚠️ Pangaea fallback failed: {e}")
    
    return jobs


def scrape_pangaea_html_fallback() -> list:
    """HTML scraping fallback if API fails"""
    jobs = []
    try:
        from bs4 import BeautifulSoup
        
        url = "https://pangaea.co/jobs"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find job listings (update selectors based on actual HTML)
            job_cards = soup.find_all('div', class_=re.compile('job|card|listing'))[:30]
            
            for card in job_cards:
                title_elem = card.find('h2') or card.find('h3')
                link_elem = card.find('a', href=True)
                company_elem = card.find(class_=re.compile('company'))
                
                if not title_elem or not link_elem:
                    continue
                
                job_id = hashlib.md5(link_elem['href'].encode()).hexdigest()
                jobs.append({
                    "id": f"pangaea_html_{job_id}",
                    "title": title_elem.get_text(strip=True),
                    "company": company_elem.get_text(strip=True) if company_elem else "Pangaea",
                    "location": "Worldwide Remote",
                    "salary": "Check listing",
                    "description": "Remote position - check website for details",
                    "tags": "Remote, Global",
                    "url": link_elem['href'],
                    "source": "Pangaea",
                })
                
    except Exception as e:
        print(f"     ⚠️ Pangaea HTML fallback failed: {e}")
    
    return jobs


def is_nigeria_allowed(restrictions):
    """Check if Nigeria is allowed in location restrictions"""
    if not restrictions:
        return True
    
    restrictions_lower = [str(r).lower() for r in restrictions]
    
    # Nigeria explicitly excluded?
    if "nigeria" in str(restrictions_lower):
        return False
    
    # Only specific countries allowed (and Nigeria not listed)
    allowed_countries = []
    for r in restrictions_lower:
        if "only" in r or "must be" in r:
            allowed_countries.append(r)
    
    if allowed_countries:
        # Check if includes Africa/Nigeria/worldwide
        if not any(term in str(allowed_countries) for term in ["worldwide", "global", "africa", "nigeria"]):
            return False
    
    return True


def check_timezone_compatibility(timezone_req):
    """Check if timezone requirement works for Nigeria (UTC+1)"""
    if not timezone_req:
        return "Flexible"
    
    tz_lower = str(timezone_req).lower()
    
    # Good for Nigeria
    good_zones = ["gmt", "utc", "wat", "cat", "eat", "bst", "cet", "eet", "any", "flexible"]
    for zone in good_zones:
        if zone in tz_lower:
            return "Compatible"
    
    # Might be challenging
    challenging_zones = ["pst", "est", "cst", "mst", "akst", "hst"]
    for zone in challenging_zones:
        if zone in tz_lower:
            return "Challenging (US hours)"
    
    return "Check requirements"


def format_pangaea_salary(min_salary, max_salary, currency):
    """Format salary nicely"""
    if not min_salary and not max_salary:
        return "Competitive"
    
    try:
        min_sal = float(min_salary) if min_salary else None
        max_sal = float(max_salary) if max_salary else None
        
        if min_sal and max_sal:
            if max_sal >= 1000000:
                return f"{currency} {min_sal/1000000:.1f}M–{max_sal/1000000:.1f}M/year"
            elif max_sal >= 100000:
                return f"{currency} {min_sal/1000:.0f}K–{max_sal/1000:.0f}K/year"
            else:
                return f"{currency} {int(min_sal)}–{int(max_sal)}/year"
        elif min_sal:
            return f"{currency} {int(min_sal):,}+/year"
    except:
        pass
    
    return "Competitive"


def calculate_nigeria_friendly_score(job):
    """Calculate a score (1-5) for how Nigeria-friendly the job is"""
    score = 3  # Start neutral
    
    # Check for worldwide/global
    location = str(job.get("location", "")).lower()
    if "worldwide" in location or "global" in location:
        score += 1
    
    # Check timezone
    tz = str(job.get("timezone", "")).lower()
    if any(zone in tz for zone in ["gmt", "utc", "flexible"]):
        score += 1
    elif any(zone in tz for zone in ["pst", "est"]):
        score -= 1
    
    # Check visa sponsorship
    if job.get("visa_sponsorship") or job.get("relocation"):
        score += 1
    
    # Check remote friendliness
    if job.get("remote", True):
        score += 1
    
    # Check if explicitly excludes Africa
    restrictions = str(job.get("location_restrictions", "")).lower()
    if "africa" in restrictions and "nigeria" in restrictions:
        score -= 2
    elif "africa" in restrictions:
        score -= 1
    
    return max(1, min(5, score))


def clean_pangaea_description(text):
    """Clean HTML and normalize description"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
