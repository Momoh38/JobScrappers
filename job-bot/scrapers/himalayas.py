"""
scrapers/himalayas.py — Himalayas.app remote jobs with Nigeria filtering
"""

import requests
import hashlib
import re

def scrape_himalayas() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    try:
        url = "https://himalayas.app/jobs/api?limit=100"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("jobs", [])

        for j in items:
            # Check location restrictions
            location_restrictions = j.get("locationRestrictions", [])
            if location_restrictions:
                # Check if Nigeria/Africa is allowed
                restrictions_lower = [l.lower() for l in location_restrictions]
                if "united states" in str(restrictions_lower) or "us only" in str(restrictions_lower):
                    continue  # Skip US-only jobs
            
            location = ", ".join(location_restrictions) if location_restrictions else "Remote (Worldwide)"
            
            # Check if explicitly Nigeria-friendly
            description = j.get("description", "")
            title = j.get("title", "")
            is_nigeria_friendly = check_himalayas_friendly(description, title, location_restrictions)

            skills = j.get("skills", [])
            tags = ", ".join([s.get("name", "") for s in skills[:5]]) if skills else "Remote"

            salary_min = j.get("salaryMin", "")
            salary_max = j.get("salaryMax", "")
            salary_currency = j.get("salaryCurrency", "USD")
            
            if salary_min and salary_max:
                salary = f"{salary_currency} {salary_min:,}–{salary_max:,}"
            elif salary_min:
                salary = f"{salary_currency} {salary_min:,}+"
            else:
                salary = "Competitive"

            job_id = hashlib.md5(str(j.get("id", j.get("slug", ""))).encode()).hexdigest()

            jobs.append({
                "id":          f"himalayas_{job_id}",
                "title":       title,
                "company":     j.get("companyName", ""),
                "location":    location,
                "salary":      salary,
                "description": clean_description(description)[:500],
                "tags":        tags,
                "experience":  j.get("seniorityLevel", "Not Specified"),
                "url":         j.get("applicationLink", "") or f"https://himalayas.app/jobs/{j.get('slug','')}",
                "source":      "Himalayas",
                "suitable_for_nigeria": "Yes" if is_nigeria_friendly else "Check reqs",
            })

    except Exception as e:
        print(f"     ⚠️ Himalayas failed: {e}")

    return jobs

def check_himalayas_friendly(description, title, restrictions):
    """Check if job is suitable for Nigerian applicants"""
    text = (description + " " + title).lower()
    
    # Exclude if too restrictive
    exclude_terms = ["us citizen", "green card", "work authorization required", "only us"]
    for term in exclude_terms:
        if term in text:
            return False
    
    # Include if worldwide or global
    include_terms = ["worldwide", "global", "any location", "anywhere"]
    for term in include_terms:
        if term in text:
            return True
    
    # If no restrictions specified, likely worldwide
    if not restrictions or "worldwide" in str(restrictions).lower():
        return True
    
    return False

def clean_description(desc):
    """Clean HTML and extra spaces"""
    if not desc:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', desc)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()
