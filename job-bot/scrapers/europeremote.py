"""
scrapers/europeremote.py — Europe-based remote jobs (EMEA & Worldwide only)
ONLY includes jobs mentioning:
- Worldwide, Global, Anywhere
- EMEA (Europe, Middle East, Africa)
- Africa, Nigeria-friendly timezones
"""

import requests
import hashlib
import re

def scrape_europeremote() -> list:
    """
    Scrapes EU remote jobs but filters for Nigeria-friendly only:
    - Worldwide/Global roles
    - EMEA region roles  
    - Africa-inclusive roles
    """
    jobs = []
    
    try:
        # EU Remote Jobs API
        url = "https://euremotejobs.com/api/jobs?limit=50"
        headers = {"User-Agent": "HalalJobsBot/1.0"}
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            for job in data.get("jobs", []):
                title = job.get("title", "")
                description = job.get("description", "")
                location = job.get("location", "")
                timezone = job.get("timezone", "")
                
                # ===== NIGERIA-FRIENDLY FILTER =====
                # Only accept if mentions worldwide, global, or EMEA
                text_to_check = f"{title} {description} {location} {timezone}".lower()
                
                # Must have at least one of these indicators
                nigeria_friendly_indicators = [
                    'worldwide', 'global', 'anywhere', 'any location',
                    'emea', 'europe middle east africa', 'africa',
                    'all countries', 'international', 'all timezones',
                    'gmt', 'utc', 'wat', 'flexible timezone'
                ]
                
                is_friendly = any(indicator in text_to_check for indicator in nigeria_friendly_indicators)
                
                # Skip if no friendly indicators found
                if not is_friendly:
                    continue
                
                # Also skip if explicitly excludes Africa/Nigeria
                exclude_indicators = [
                    'us only', 'usa only', 'uk only', 'eu only', 'eu citizens only',
                    'must be in europe', 'europe only', 'schengen only',
                    'excluding africa', 'no africa', 'north america only'
                ]
                
                is_excluded = any(indicator in text_to_check for indicator in exclude_indicators)
                
                if is_excluded:
                    continue
                
                # Extract salary
                salary_min = job.get("salary_min", "")
                salary_max = job.get("salary_max", "")
                if salary_min and salary_max:
                    salary = f"€{salary_min:,}–€{salary_max:,}/year"
                else:
                    salary = "Competitive (EU rates)"
                
                # Create friendly location description
                if 'emea' in text_to_check:
                    location_desc = "EMEA Region (Nigeria-Friendly)"
                elif 'worldwide' in text_to_check or 'global' in text_to_check:
                    location_desc = "Worldwide Remote (Nigeria-Friendly)"
                else:
                    location_desc = f"{location} (Check - May include Nigeria)"
                
                job_id = hashlib.md5(str(job.get("id", "")).encode()).hexdigest()
                
                jobs.append({
                    "id": f"europeremote_{job_id}",
                    "title": title,
                    "company": job.get("company", ""),
                    "location": location_desc,
                    "salary": salary,
                    "description": f"🌍 EMEA/WORLDWIDE ROLE: {job.get('description', '')[:450]}",
                    "tags": "EMEA, Worldwide Remote, Nigeria-Friendly",
                    "url": job.get("url", ""),
                    "source": "EuropeRemote",
                    "timezone_friendliness": "High (EMEA/Worldwide)",
                    "suitable_for_nigeria": "Yes",
                    "application_tips": "✓ EMEA roles include Nigeria - apply confidently"
                })
                
    except Exception as e:
        print(f"     ⚠️ EuropeRemote failed: {e}")
    
    # Filter to ensure only quality matches
    filtered_jobs = []
    for job in jobs:
        # Double-check location field for Nigeria-friendliness
        location_text = job.get('location', '').lower()
        if any(term in location_text for term in ['worldwide', 'global', 'emea', 'nigeria-friendly']):
            filtered_jobs.append(job)
    
    print(f"     📊 Found {len(filtered_jobs)} Nigeria-friendly EU/EMEA jobs")
    return filtered_jobs[:25]  # Limit to 25 most relevant
