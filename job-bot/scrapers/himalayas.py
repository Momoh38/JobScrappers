"""
scrapers/himalayas.py — Himalayas.app remote jobs (Nigeria + Worldwide only)
Filters out: US-only, EU-only, location-restricted roles
Keeps: Worldwide, Global, Anywhere, Remote-friendly
"""

import requests
import hashlib
import re


def scrape_himalayas() -> list:
    """
    Scrapes Himalayas for remote jobs, filtered for Nigeria + Worldwide only
    """
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    try:
        url = "https://himalayas.app/jobs/api?limit=100"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("jobs", [])

        print(f"     📊 Checking {len(items)} raw jobs from Himalayas")

        for j in items:
            # Extract location restrictions
            location_restrictions = j.get("locationRestrictions", [])
            location_string = ", ".join(location_restrictions) if location_restrictions else ""
            
            title = j.get("title", "")
            description = j.get("description", "")
            
            # ===== NIGERIA + WORLDWIDE ONLY FILTER =====
            text_to_check = f"{title} {description} {location_string}".lower()
            
            # Check for restricted locations (EXCLUDE)
            restricted_indicators = [
                'us only', 'usa only', 'united states only', 'america only',
                'uk only', 'united kingdom only', 'britain only',
                'eu only', 'europe only', 'schengen only',
                'canada only', 'australia only', 'new zealand only',
                'must be in', 'citizen only', 'work authorization required',
                'green card', 'visa sponsorship not available',
                'excluding africa', 'no african countries'
            ]
            
            is_restricted = any(indicator in text_to_check for indicator in restricted_indicators)
            
            if is_restricted:
                continue
            
            # Check for Nigeria-friendly indicators (INCLUDE)
            friendly_indicators = [
                'worldwide', 'global', 'anywhere', 'any location',
                'all countries', 'international', 'remote',
                'no location restrictions', 'open to all', 'all nationalities',
                'work from anywhere', 'location independent'
            ]
            
            # Also check if location_restrictions is empty (means worldwide)
            is_empty_restrictions = not location_restrictions or len(location_restrictions) == 0
            
            is_friendly = is_empty_restrictions or any(indicator in text_to_check for indicator in friendly_indicators)
            
            # If not friendly AND has restrictions, skip
            if not is_friendly and not is_empty_restrictions:
                continue
            
            # ===== EXTRACT JOB DETAILS =====
            # Location display
            if is_empty_restrictions:
                location = "Worldwide Remote (No Restrictions)"
            elif 'worldwide' in text_to_check or 'global' in text_to_check:
                location = "Worldwide Remote (Nigeria-Friendly)"
            else:
                location = "Remote - Check location requirements"
            
            # Skills/tags
            skills = j.get("skills", [])
            tags_list = [s.get("name", "") for s in skills[:5]] if skills else []
            tags = ", ".join(tags_list) if tags_list else "Remote, Worldwide"
            
            # Add Nigeria-friendly tag
            tags += ", Nigeria-Friendly"
            
            # Salary
            salary_min = j.get("salaryMin", "")
            salary_max = j.get("salaryMax", "")
            salary_currency = j.get("salaryCurrency", "USD")
            salary = format_himalayas_salary(salary_min, salary_max, salary_currency)
            
            # Experience level
            experience = j.get("seniorityLevel", "Not Specified")
            
            # Clean description
            description_clean = clean_himalayas_description(description)[:500]
            
            # Check if explicitly Nigeria-friendly
            if 'worldwide' in text_to_check or 'global' in text_to_check:
                description_clean = f"🌍 WORLDWIDE ROLE: {description_clean}"
            elif is_empty_restrictions:
                description_clean = f"🌍 OPEN TO ALL COUNTRIES: {description_clean}"
            
            # Generate ID
            job_id = hashlib.md5(str(j.get("id", j.get("slug", ""))).encode()).hexdigest()
            
            jobs.append({
                "id":          f"himalayas_{job_id}",
                "title":       title,
                "company":     j.get("companyName", ""),
                "location":    location,
                "salary":      salary,
                "description": description_clean,
                "tags":        tags,
                "experience":  experience,
                "url":         j.get("applicationLink", "") or f"https://himalayas.app/jobs/{j.get('slug','')}",
                "source":      "Himalayas",
                "suitable_for_nigeria": "Yes",
                "filter_pass": "Worldwide/Nigeria-Friendly",
            })

    except Exception as e:
        print(f"     ⚠️ Himalayas failed: {e}")

    # Final quality filter
    filtered_jobs = []
    for job in jobs:
        # Double-check location description
        loc = job.get('location', '').lower()
        desc = job.get('description', '').lower()
        
        # Ensure it's truly Nigeria-friendly
        if any(term in loc for term in ['worldwide', 'no restrictions', 'nigeria-friendly']):
            filtered_jobs.append(job)
        elif any(term in desc for term in ['worldwide', 'global', 'any location', 'all countries']):
            filtered_jobs.append(job)
        else:
            print(f"     🚫 Filtered out (restricted): {job.get('title', '')[:50]}...")
    
    print(f"     ✅ Found {len(filtered_jobs)} Nigeria-friendly jobs from Himalayas")
    return filtered_jobs


def format_himalayas_salary(min_salary, max_salary, currency):
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
            if min_sal >= 1000000:
                return f"{currency} {min_sal/1000000:.1f}M+/year"
            elif min_sal >= 100000:
                return f"{currency} {min_sal/1000:.0f}K+/year"
            else:
                return f"{currency} {int(min_sal)}+/year"
    except:
        pass
    
    return "Competitive"


def clean_himalayas_description(desc):
    """Clean HTML from description"""
    if not desc:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', desc)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()
