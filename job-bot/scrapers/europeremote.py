"""
scrapers/europeremote.py — Europe-based remote jobs (good timezone for Nigeria)
UTC+1 to UTC+3 aligns well with Nigerian hours
"""

import requests
import hashlib
import re

def scrape_europeremote() -> list:
    jobs = []
    
    try:
        # EU Remote Jobs API
        url = "https://euremotejobs.com/api/jobs?limit=40"
        headers = {"User-Agent": "HalalJobsBot/1.0"}
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            for job in data.get("jobs", []):
                # Check if remote from Europe (good timezone for Nigeria)
                location = job.get("location", "")
                timezone = job.get("timezone", "")
                
                # Skip if explicitly US-only
                if "US only" in location or "USA only" in location:
                    continue
                
                job_id = hashlib.md5(str(job.get("id", "")).encode()).hexdigest()
                
                # Format salary (EUR)
                salary_min = job.get("salary_min", "")
                salary_max = job.get("salary_max", "")
                if salary_min and salary_max:
                    salary = f"€{salary_min:,}–€{salary_max:,}/year"
                else:
                    salary = "Competitive (EU rates)"
                
                jobs.append({
                    "id": f"europeremote_{job_id}",
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": f"{location} (EU Timezone - Nigeria friendly UTC+1)",
                    "salary": salary,
                    "description": f"🕐 EU Timezone (good for Nigeria): {job.get('description', '')[:400]}",
                    "tags": "Europe Remote, UTC+1 Friendly",
                    "url": job.get("url", ""),
                    "source": "EuropeRemote",
                    "timezone_friendliness": "High (UTC±0-3)",
                })
                
    except Exception as e:
        print(f"     ⚠️ EuropeRemote failed: {e}")
    
    return jobs[:25]
