"""
scrapers/jobicy.py — Jobicy remote jobs API (free, no auth, worldwide open)
Fixed API parameters and enhanced for Nigerian-friendly jobs.
"""

import requests
import hashlib
import re


def scrape_jobicy() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    try:
        # Jobicy API v2 correct format — no 'geo' parameter, use 'industries' or just get all
        # Max 'count' appears to be 50 (API limitation)
        url = "https://jobicy.com/api/v2/remote-jobs?count=50"
        response = requests.get(url, headers=headers, timeout=15)
        
        # Check if request was successful
        if response.status_code != 200:
            print(f"     ⚠️ Jobicy API returned status {response.status_code}")
            return jobs
            
        response.raise_for_status()
        data = response.json()
        
        # The API might return jobs directly or in a 'jobs' key
        items = data.get("jobs", [])
        if not items and isinstance(data, list):
            items = data
        elif not items and isinstance(data, dict):
            # Try alternative data structures
            items = data.get("remote-jobs", []) or data.get("data", [])
        
        print(f"     📊 Retrieved {len(items)} raw jobs from Jobicy")

        for j in items:
            # Extract all available fields with safe fallbacks
            job_title = j.get("jobTitle", j.get("title", ""))
            company_name = j.get("companyName", j.get("company", ""))
            job_description = j.get("jobDescription", j.get("description", ""))
            
            # Location handling
            job_geo = j.get("jobGeo", j.get("location", "Remote"))
            
            # Timezone info (may be in different fields)
            timezones = j.get("jobTimezone", j.get("timezones", []))
            if isinstance(timezones, str):
                timezones = [timezones]
            
            # Work schedule
            work_schedule = j.get("jobSchedule", j.get("schedule", "Flexible"))
            
            # Experience level
            experience_level = j.get("jobExperience", j.get("experience", "Not Specified"))
            
            # Skills and tags
            required_skills = j.get("jobTags", j.get("tags", []))
            if isinstance(required_skills, str):
                required_skills = [required_skills]
            
            # Industry and job type
            industry = j.get("jobIndustry", j.get("industry", []))
            if isinstance(industry, str):
                industry = [industry]
            
            job_type = j.get("jobType", j.get("type", []))
            if isinstance(job_type, str):
                job_type = [job_type]
            
            # Salary information
            salary_min = j.get("annualSalaryMin", j.get("salary_min", ""))
            salary_max = j.get("annualSalaryMax", j.get("salary_max", ""))
            salary_currency = j.get("salaryCurrency", j.get("currency", "USD"))
            
            # Check if job is suitable for Nigerians
            is_nigeria_friendly = check_nigeria_friendliness(
                job_description, job_geo, timezones, experience_level, work_schedule
            )
            
            # Skip non-friendly jobs
            if not is_nigeria_friendly:
                continue
            
            # Generate unique ID
            job_id_value = j.get("id", j.get("jobSlug", j.get("slug", "")))
            job_id = hashlib.md5(str(job_id_value).encode()).hexdigest()
            
            # Format salary
            salary_text = format_salary(salary_min, salary_max, salary_currency)
            
            # Extract visa sponsorship and English requirements
            visa_sponsorship = "Yes" if re.search(r'visa|sponsor|relocation', job_description, re.I) else "No"
            english_level = extract_english_level(job_description)
            timezone_friendliness = evaluate_timezone_friendliness(timezones)
            
            # Combine all tags
            all_tags = list(set(job_type + industry + required_skills))
            tags = ", ".join(all_tags[:8]) if all_tags else "Remote, Worldwide"
            
            jobs.append({
                "id": f"jobicy_{job_id}",
                "title": job_title,
                "company": company_name,
                "location": job_geo,
                "description": clean_description(job_description)[:500],
                "url": j.get("url", j.get("applyUrl", "")),
                "source": "Jobicy",
                
                "salary": salary_text,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": salary_currency,
                
                "work_schedule": work_schedule,
                "experience_level": experience_level,
                "job_type": ", ".join(job_type) if job_type else "Remote",
                "industry": ", ".join(industry[:3]) if industry else "Technology",
                
                "tags": tags,
                "required_skills": ", ".join(required_skills[:5]) if required_skills else "Various",
                "benefits": ", ".join(j.get("jobBenefits", j.get("benefits", []))[:3]),
                
                "timezones": ", ".join(timezones) if timezones else "Any",
                "timezone_friendliness": timezone_friendliness,
                "visa_sponsorship": visa_sponsorship,
                "english_level": english_level,
                
                "company_size": j.get("companySize", "Not Specified"),
                "company_industry": j.get("companyIndustry", ""),
                "company_founded": j.get("companyFounded", ""),
                
                "suitable_for_nigeria": "Yes",
                "remote_friendly": "Worldwide",
                "application_tips": get_application_tips(experience_level, job_type),
            })
        
        print(f"     ✅ Found {len(jobs)} Nigerian-friendly jobs")
        
        # If still no jobs, try fallback endpoint
        if not jobs:
            print("     🔄 Trying fallback Jobicy endpoint...")
            return scrape_jobicy_fallback()

    except Exception as e:
        print(f"     ⚠️ Jobicy failed: {e}")
        # Try fallback on any error
        return scrape_jobicy_fallback()

    return jobs


def scrape_jobicy_fallback() -> list:
    """Fallback method using different API endpoint or parameters"""
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}
    
    try:
        # Try alternative endpoint format (some versions use this)
        url = "https://jobicy.com/api/v2/remote-jobs?count=30&industry=software-development,marketing,sales,customer-support"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("jobs", [])
            
            for j in items[:20]:  # Limit to 20 jobs
                if is_basic_nigeria_friendly(j):
                    job_id = hashlib.md5(str(j.get("id", "")).encode()).hexdigest()
                    jobs.append({
                        "id": f"jobicy_{job_id}",
                        "title": j.get("jobTitle", j.get("title", "Remote Role")),
                        "company": j.get("companyName", j.get("company", "Various")),
                        "location": "Worldwide Remote",
                        "description": clean_description(j.get("jobDescription", j.get("description", "")))[:300],
                        "url": j.get("url", j.get("applyUrl", "#")),
                        "source": "Jobicy",
                        "salary": "Check listing",
                        "tags": "Remote, Worldwide",
                        "suitable_for_nigeria": "Yes",
                    })
            
            print(f"     ✅ Fallback found {len(jobs)} jobs")
            
    except Exception as e:
        print(f"     ⚠️ Fallback also failed: {e}")
    
    return jobs


def is_basic_nigeria_friendly(job_dict):
    """Basic check for Nigeria-friendliness"""
    title = job_dict.get("jobTitle", job_dict.get("title", "")).lower()
    desc = job_dict.get("jobDescription", job_dict.get("description", "")).lower()
    
    exclude_terms = ["us only", "usa only", "uk only", "eu citizen", "work authorization required"]
    include_terms = ["remote", "worldwide", "anywhere", "global", "any location"]
    
    # Check exclusion
    for term in exclude_terms:
        if term in desc or term in title:
            return False
    
    # Check inclusion
    for term in include_terms:
        if term in desc or term in title:
            return True
    
    # Default to true for remote jobs
    return "remote" in title or "remote" in desc


# Keep the helper functions from previous version (check_nigeria_friendliness, 
# evaluate_timezone_friendliness, extract_english_level, format_salary, 
# clean_description, get_application_tips)
# ... (include all the helper functions from the previous response)
