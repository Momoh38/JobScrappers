"""
scrapers/relocate_me.py — Jobs with visa sponsorship & relocation
Great for Nigerians seeking international roles with visa support
"""

import requests
import hashlib
import re
from datetime import datetime, timedelta

def scrape_relocate_me() -> list:
    jobs = []
    
    try:
        # Relocate.me API (no key required for public data)
        url = "https://relocate.me/api/job/list?limit=50"
        headers = {"User-Agent": "HalalJobsBot/1.0"}
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("jobs", [])
            
            for job in items:
                # Check if visa sponsorship is offered
                visa_sponsored = job.get("visa_sponsored", False)
                relocation = job.get("relocation_paid", False)
                
                if not visa_sponsored and not relocation:
                    continue  # Skip if no visa/relocation help
                
                # Nigeria-friendly timezone check
                location = job.get("location", "")
                timezone = job.get("timezone", "")
                
                job_id = hashlib.md5(str(job.get("id", "")).encode()).hexdigest()
                
                # Format salary
                salary_min = job.get("salary_min", "")
                salary_max = job.get("salary_max", "")
                salary_currency = job.get("salary_currency", "USD")
                
                if salary_min and salary_max:
                    salary = f"{salary_currency} {salary_min:,}–{salary_max:,}/year"
                else:
                    salary = "Competitive + Visa Sponsorship"
                
                # Special tag for visa sponsorship
                tags = "Visa Sponsorship, Relocation Available"
                if job.get("remote"):
                    tags += ", Remote"
                
                jobs.append({
                    "id": f"relocate_{job_id}",
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "location": location,
                    "salary": salary,
                    "description": f"🏢 VISA SPONSORSHIP OFFERED: {job.get('description', '')[:400]}",
                    "tags": tags,
                    "date_posted": job.get("published_at", ""),
                    "url": job.get("url", f"https://relocate.me/jobs/{job.get('slug', '')}"),
                    "source": "Relocate.me",
                    "suitable_for_nigeria": "Yes - Visa Sponsorship",
                })
                
    except Exception as e:
        print(f"     ⚠️ Relocate.me failed: {e}")
    
    return jobs
