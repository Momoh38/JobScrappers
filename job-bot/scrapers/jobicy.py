"""
scrapers/jobicy.py — Jobicy remote jobs API (free, no auth, worldwide open)
Updated with Nigerian-friendly filtering and expanded job fields.
"""

import requests
import hashlib
import re


def scrape_jobicy() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    try:
        # Fetch more jobs to filter for Nigerian-friendly ones
        url = "https://jobicy.com/api/v2/remote-jobs?count=100&geo=worldwide"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("jobs", [])

        # Nigerian-friendly keywords (anytime zones, companies hiring globally)
        nigeria_friendly_keywords = [
            "anywhere", "worldwide", "global", "europe", "uk", "us", 
            "africa", "emea", "remote-first", "distributed", "any timezone",
            "gmt", "utc", "flexible hours", "asynchronous"
        ]
        
        # Timezone filters - focusing on EMEA/Africa-friendly
        africa_friendly_timezones = [
            "GMT", "UTC", "WAT", "CAT", "EAT", "BST", "CET", "EET"
        ]

        for j in items:
            # Extract all available fields
            job_title = j.get("jobTitle", "")
            company_name = j.get("companyName", "")
            job_description = j.get("jobDescription", "")
            job_geo = j.get("jobGeo", "Remote")
            
            # Timezone and working hours info
            timezones = j.get("jobTimezone", [])
            if isinstance(timezones, str):
                timezones = [timezones]
            
            # Work schedule requirements
            work_schedule = j.get("jobSchedule", "Flexible")
            
            # Experience level
            experience_level = j.get("jobExperience", "Not Specified")
            
            # Benefits and perks
            benefits = j.get("jobBenefits", [])
            if isinstance(benefits, str):
                benefits = [benefits]
            
            # Required skills
            required_skills = j.get("jobTags", [])
            if isinstance(required_skills, str):
                required_skills = [required_skills]
            
            # Industry and type
            industry = j.get("jobIndustry", [])
            if isinstance(industry, str):
                industry = [industry]
            
            job_type = j.get("jobType", [])
            if isinstance(job_type, str):
                job_type = [job_type]
            
            # Salary information (annual)
            salary_min = j.get("annualSalaryMin", "")
            salary_max = j.get("annualSalaryMax", "")
            salary_currency = j.get("salaryCurrency", "USD")
            
            # Company details
            company_size = j.get("companySize", "Not Specified")
            company_industry = j.get("companyIndustry", "")
            company_founded = j.get("companyFounded", "")
            
            # Check if job is suitable for Nigerians
            is_nigeria_friendly = check_nigeria_friendliness(
                job_description, job_geo, timezones, experience_level, work_schedule
            )
            
            # Only include jobs that are truly worldwide or Nigeria-friendly
            if not is_nigeria_friendly:
                continue
            
            # Generate unique ID
            job_id = hashlib.md5(str(j.get("id", j.get("jobSlug", ""))).encode()).hexdigest()
            
            # Format salary
            salary_text = format_salary(salary_min, salary_max, salary_currency)
            
            # Extract visa sponsorship info (if mentioned)
            visa_sponsorship = "Yes" if re.search(r'visa|sponsor|relocation', job_description, re.I) else "No"
            
            # Extract English requirement
            english_level = extract_english_level(job_description)
            
            # Timezone friendliness for Nigeria (WAT = UTC+1)
            timezone_friendliness = evaluate_timezone_friendliness(timezones)
            
            # Combine all tags
            all_tags = list(set(job_type + industry + required_skills))
            tags = ", ".join(all_tags[:8])  # Show top 8 tags
            
            jobs.append({
                # Core fields
                "id": f"jobicy_{job_id}",
                "title": job_title,
                "company": company_name,
                "location": job_geo,
                "description": clean_description(job_description)[:500],
                "url": j.get("url", ""),
                "source": "Jobicy",
                
                # New expanded fields
                "salary": salary_text,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "salary_currency": salary_currency,
                
                "work_schedule": work_schedule,
                "experience_level": experience_level,
                "job_type": ", ".join(job_type),
                "industry": ", ".join(industry[:3]),
                
                "tags": tags,
                "required_skills": ", ".join(required_skills[:5]),
                "benefits": ", ".join(benefits[:3]),
                
                "timezones": ", ".join(timezones),
                "timezone_friendliness": timezone_friendliness,
                "visa_sponsorship": visa_sponsorship,
                "english_level": english_level,
                
                "company_size": company_size,
                "company_industry": company_industry,
                "company_founded": company_founded,
                
                # Nigerian-specific fields
                "suitable_for_nigeria": "Yes",
                "remote_friendly": "Worldwide",
                "application_tips": get_application_tips(experience_level, job_type),
            })

    except Exception as e:
        print(f"     ⚠️ Jobicy failed: {e}")

    return jobs


def check_nigeria_friendliness(description, location, timezones, experience, schedule):
    """Check if job is suitable for Nigerian applicants"""
    
    # Check location keywords
    location_lower = location.lower()
    description_lower = description.lower()
    
    # Reject clearly non-Nigeria-friendly jobs
    forbidden_keywords = [
        "us only", "usa only", "uk only", "europe only", "local only",
        "must be in", "must reside in", "citizen only", "work authorization required"
    ]
    
    for keyword in forbidden_keywords:
        if keyword in description_lower or keyword in location_lower:
            return False
    
    # Accept worldwide or explicitly inclusive jobs
    inclusive_keywords = [
        "worldwide", "anywhere", "global", "remote", "any location",
        "all countries", "international", "open to all", "all timezones"
    ]
    
    for keyword in inclusive_keywords:
        if keyword in location_lower or keyword in description_lower:
            return True
    
    # Check for junior/entry-level friendliness (good for Nigerian market)
    junior_friendly = any(term in description_lower for term in [
        "junior", "entry level", "graduate", "training provided", "learning opportunity"
    ])
    
    # Check for flexible schedule
    flexible = any(term in description_lower or term in schedule.lower() for term in [
        "flexible", "async", "asynchronous", "any timezone"
    ])
    
    return junior_friendly or flexible


def evaluate_timezone_friendliness(timezones):
    """Evaluate how friendly the timezone requirements are for Nigeria (UTC+1)"""
    if not timezones:
        return "Flexible/Any Timezone"
    
    friendly_zones = ["GMT", "UTC", "WAT", "CAT", "EAT", "BST", "CET", "EET", "Any", "Flexible"]
    
    for tz in timezones:
        if any(friendly in tz for friendly in friendly_zones):
            return "Nigeria-Friendly (EMEA/Africa hours)"
    
    return "Specific Timezone - Check Requirements"


def extract_english_level(description):
    """Extract English proficiency requirements"""
    desc_lower = description.lower()
    
    if "fluent" in desc_lower or "native" in desc_lower:
        return "Fluent/Native"
    elif "professional" in desc_lower or "business" in desc_lower:
        return "Professional Working"
    elif "intermediate" in desc_lower:
        return "Intermediate"
    else:
        return "Working Knowledge (likely sufficient)"


def format_salary(min_salary, max_salary, currency):
    """Format salary nicely"""
    if min_salary and max_salary:
        # Convert to thousands/millions for readability
        if max_salary >= 1000000:
            return f"{currency} {min_salary/1000000:.1f}M–{max_salary/1000000:.1f}M/year"
        elif max_salary >= 100000:
            return f"{currency} {min_salary/1000:.0f}K–{max_salary/1000:.0f}K/year"
        else:
            return f"{currency} {min_salary}–{max_salary}/year"
    elif min_salary:
        return f"{currency} {min_salary}/year+"
    else:
        return "Competitive/Not Specified"


def clean_description(description):
    """Clean HTML tags and extra whitespace from description"""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', ' ', description)
    # Remove extra whitespace
    clean = re.sub(r'\s+', ' ', clean)
    # Remove common tracking text
    clean = re.sub(r'Apply now|Click here|Read more', '', clean, flags=re.I)
    return clean.strip()


def get_application_tips(experience, job_type):
    """Provide Nigeria-specific application tips"""
    tips = []
    
    if "junior" in experience.lower() or "entry" in experience.lower():
        tips.append("✓ Junior role - good for recent graduates")
    else:
        tips.append("✓ Highlight relevant experience in your CV")
    
    if any(term in str(job_type).lower() for term in ["contract", "freelance"]):
        tips.append("✓ Contract/Freelance - can be good for remote work")
    
    tips.append("✓ Apply early as remote roles fill quickly")
    
    return " | ".join(tips[:3])
