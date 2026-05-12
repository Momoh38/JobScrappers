"""
filter.py — Simplified filtering logic
ONLY filters: location restrictions, German/Chinese language, duplicates, old jobs
"""

import re
from difflib import SequenceMatcher
from config import (
    INCLUDE_KEYWORDS, EXCLUDE_TITLES, PRIORITY_KEYWORDS,
    MIN_SALARY_NGN, MIN_SALARY_USD,
    MAX_JOB_AGE_DAYS, MIN_DESCRIPTION_LENGTH
)

# Try to import RESTRICTED_LOCATIONS from config
try:
    from config import RESTRICTED_LOCATIONS
except ImportError:
    RESTRICTED_LOCATIONS = [
        "usa only", "us only", "united states only", "must be based in us",
        "must reside in us", "north america only", "canada only",
        "uk only", "eu only", "europe only", "germany only", "netherlands only",
        "right to work in the us", "authorized to work in the united states",
        "must be located in us", "physically located in the us",
        "us citizen", "us citizenship required", "green card",
        "security clearance", "nato clearance", "australian residents only",
        "new zealand only", "romania", "romania only", "must be in romania",
        "latin america only", "latam only", "brazil", "colombia", "philippines",
        "americas", "europe", "asia", "oceania", "switzerland", "switzerland only",
        "china", "china only", "shanghai", "france only", "italy only",
        "spain only", "portugal only", "belgium only", "austria only",
        "sweden only", "norway only", "denmark only", "finland only", "ireland only",
        "south africa only", "uae only", "saudi arabia only", "qatar only",
        "kuwait only", "bahrain only", "oman only", "singapore only",
        "malaysia only", "japan only", "south korea only", "india only",
        "mexico only", "argentina only", "chile only", "peru only",
    ]

# German language indicators
GERMAN_INDICATORS = [
    "🇩🇪", "german", "deutsch", "fließend", "muttersprache", "sprache",
    "german speaking", "german language", "auf deutsch", "die stelle",
    "wir suchen", "ihre aufgaben", "ihr profil", "remote deutschland",
    "german required", "deutschkenntnisse", "muttersprachler",
]

# Chinese language indicators
CHINESE_INDICATORS = [
    "china", "shanghai", "beijing", "中文", "普通话", "汉语",
    "说明", "指引", "职位", "工作地点",
]

SUBSCRIPTION_SOURCES = ["theladders", "job-hunt.org"]

_seen_fingerprints = []


def strip_html(text: str) -> str:
    """Aggressively clean HTML tags and fix formatting"""
    if not text:
        return ""
    
    # Remove all HTML tags (anything between < and >)
    clean = re.sub(r'<[^>]+>', ' ', text)
    
    # Remove Tailwind CSS classes and other style attributes
    clean = re.sub(r'class="[^"]*"', '', clean)
    clean = re.sub(r'style="[^"]*"', '', clean)
    clean = re.sub(r'data-[^=]*="[^"]*"', '', clean)
    
    # Remove CSS style blocks
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.DOTALL)
    
    # Fix HTML entities
    entities = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&rsquo;": "'", "&lsquo;": "'",
        "&rdquo;": '"', "&ldquo;": '"', "&mdash;": "—", "&ndash;": "–",
        "&amp;#39;": "'", "&#x27;": "'", "&apos;": "'",
        "â¢": "•", "â": "–", "â": "—", "â": "'", "â": '"', "â": '"',
        "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
        "&#34;": '"', "&#38;": "&", "&#39;": "'", "&#40;": "(", "&#41;": ")",
        "&#60;": "<", "&#62;": ">", "&#91;": "[", "&#93;": "]",
    }
    for entity, replacement in entities.items():
        clean = clean.replace(entity, replacement)
    
    # Remove escaped slashes
    clean = clean.replace('\\/', '/')
    clean = clean.replace('\\', '')
    
    # Remove Tailwind-specific patterns
    clean = re.sub(r'tw-[a-zA-Z0-9-]+', '', clean)
    clean = re.sub(r'figma-[a-zA-Z0-9-]+', '', clean)
    
    # Fix comma-separated single letters (like "o, p, e, r, a, t, i, o, n, s")
    clean = re.sub(r'\b([a-z]),\s+([a-z]),\s+([a-z]),\s+([a-z])', r'\1\2\3\4', clean)
    clean = re.sub(r',\s+([a-z])', r' \1', clean)
    
    # Remove multiple spaces and clean up
    clean = re.sub(r'\s+', ' ', clean)
    clean = clean.strip()
    
    # If result is just a short fragment or empty, return a placeholder
    if not clean or len(clean) < 20:
        return "Click the 'Apply Now' button below for more details."
    
    # Try to extract meaningful text (first 100 chars)
    if len(clean) > 800:
        clean = clean[:800] + "..."
    
    return clean


def is_german_job(text: str) -> bool:
    """Check if job posting is in German or requires German language"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    for indicator in GERMAN_INDICATORS:
        if indicator.lower() in text_lower:
            return True
    
    return False


def is_chinese_job(text: str) -> bool:
    """Check if job posting is in Chinese"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    for indicator in CHINESE_INDICATORS:
        if indicator.lower() in text_lower:
            return True
    
    # Check for Chinese characters (Unicode range)
    if re.search(r'[\u4e00-\u9fff]', text):
        return True
    
    return False


def is_location_restricted(location: str, description: str) -> bool:
    """Check if job location restricts Nigerians from applying"""
    combined = f"{location.lower()} {description.lower()}"
    
    # Check if job is explicitly remote worldwide
    remote_indicators = ['remote', 'worldwide', 'global', 'anywhere', 'work from home']
    is_remote = any(indicator in combined for indicator in remote_indicators)
    
    if is_remote:
        for restricted in RESTRICTED_LOCATIONS:
            if restricted in combined:
                return True
        return False
    
    for restricted in RESTRICTED_LOCATIONS:
        if restricted in combined:
            return True
    
    return False


def clean_location(location: str) -> str:
    """Clean and standardize location field"""
    if not location:
        return "Remote / Worldwide"
    
    location = strip_html(location)
    location = re.sub(r'^Remote\s*[-–]\s*', '', location)
    
    if not location or len(location) < 2:
        return "Remote / Worldwide"
    
    return location


def is_nigeria_friendly(job: dict) -> bool:
    """
    Check if job is accessible from Nigeria.
    Filters out: German jobs, Chinese jobs, location-restricted jobs
    """
    title = job.get("title", "")
    location = job.get("location", "")
    description = job.get("description", "")
    combined = f"{title} {location} {description}"
    
    # Clean first
    combined = strip_html(combined)
    
    # Check for German language
    if is_german_job(combined) or is_german_job(title):
        print(f"     🇩🇪 Filtered (German job): {title[:50]}")
        return False
    
    # Check for Chinese language/location
    if is_chinese_job(combined) or is_chinese_job(location):
        print(f"     🇨🇳 Filtered (Chinese job): {title[:50]}")
        return False
    
    # Check location restrictions
    if is_location_restricted(location, description):
        print(f"     🌍 Filtered (location restricted): {title[:50]}")
        return False
    
    # If job explicitly mentions Nigeria - good
    if "nigeria" in combined or "lagos" in combined or "abuja" in combined:
        return True
    
    # If job is remote - good
    if "remote" in combined:
        return True
    
    return True


def is_fuzzy_duplicate(job: dict) -> bool:
    """Check if similar job was seen"""
    fingerprint = f"{job.get('title','').lower().strip()} {job.get('company','').lower().strip()}"
    for seen in _seen_fingerprints:
        ratio = SequenceMatcher(None, fingerprint, seen).ratio()
        if ratio >= 0.85:
            print(f"     🔁 Duplicate ({ratio:.0%}): {job.get('title','?')[:40]}")
            return True
    _seen_fingerprints.append(fingerprint)
    return False


def is_too_old(job: dict) -> bool:
    """Skip old jobs"""
    if MAX_JOB_AGE_DAYS == 0:
        return False
    from datetime import datetime
    date_str = job.get("date_posted", "")
    if not date_str:
        return False
    try:
        formats = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y"]
        parsed = None
        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str[:19], fmt)
                break
            except Exception:
                continue
        if not parsed:
            return False
        now = datetime.now()
        age_days = (now - parsed).days
        if age_days > MAX_JOB_AGE_DAYS:
            return True
    except Exception:
        pass
    return False


def is_salary_too_low(job: dict) -> bool:
    """Skip low salary jobs"""
    if MIN_SALARY_NGN == 0 and MIN_SALARY_USD == 0:
        return False
    salary_text = job.get("salary", "").lower()
    if not salary_text:
        return False
    
    salary_text = strip_html(salary_text)
    numbers = re.findall(r"[\d,]+", salary_text.replace(",", ""))
    if not numbers:
        return False
    amount = int(numbers[0])
    
    if "₦" in salary_text or "ngn" in salary_text or "naira" in salary_text:
        if MIN_SALARY_NGN > 0 and amount < MIN_SALARY_NGN:
            return True
    elif "$" in salary_text or "usd" in salary_text:
        if MIN_SALARY_USD > 0 and amount < MIN_SALARY_USD:
            return True
    return False


def get_quality_score(job: dict) -> int:
    """Score job 1-5"""
    score = 1
    if job.get("company") and job.get("company") != "Not specified":
        score += 0.5
    if job.get("salary"):
        score += 1
    if len(job.get("description", "")) > 100:
        score += 1
    if job.get("url") and "http" in job.get("url", ""):
        score += 0.5
    if job.get("tags") and len(job.get("tags", "")) > 5:
        score += 0.5
    if job.get("experience"):
        score += 0.5
    return min(5, int(score))


def is_priority(job: dict) -> bool:
    """Check priority match"""
    text = f"{job.get('title','')} {job.get('description','')}".lower()
    text = strip_html(text)
    return any(kw.lower() in text for kw in PRIORITY_KEYWORDS)


def clean_job_data(job: dict) -> dict:
    """Clean all job text fields aggressively"""
    if job.get('title'):
        job['title'] = strip_html(job['title'])
        job['title'] = job['title'].replace('🇩🇪', '').replace('🇨🇳', '').strip()
        # Remove "US" from title if present
        job['title'] = re.sub(r'\s*[-–]\s*US$', '', job['title'])
        job['title'] = re.sub(r'\s*[-–]\s*USA$', '', job['title'])
    
    if job.get('description'):
        job['description'] = strip_html(job['description'])
        # If description is still mostly HTML or garbage, use placeholder
        if not job['description'] or len(job['description']) < 20:
            job['description'] = "Click the 'Apply Now' button below for more details."
    
    if job.get('company'):
        job['company'] = strip_html(job['company'])
        if not job['company'] or len(job['company']) < 2:
            job['company'] = "Not specified"
    
    if job.get('location'):
        job['location'] = clean_location(job['location'])
    
    return job


def is_halal(job: dict) -> bool:
    """Master filter - SIMPLIFIED: only location, language, duplicates, age, salary"""
    
    # Clean first
    job = clean_job_data(job)
    
    # Check description length
    if MIN_DESCRIPTION_LENGTH > 0:
        if len(job.get("description", "")) < MIN_DESCRIPTION_LENGTH:
            return False
    
    # Check age
    if is_too_old(job):
        print(f"     📅 Filtered (too old): {job.get('title','?')[:50]}")
        return False
    
    # Check salary
    if is_salary_too_low(job):
        print(f"     💰 Filtered (salary too low): {job.get('title','?')[:50]}")
        return False
    
    # Check duplicates
    if is_fuzzy_duplicate(job):
        return False
    
    # Excluded titles
    title_lower = job.get("title", "").lower()
    for keyword in EXCLUDE_TITLES:
        if keyword.lower() in title_lower:
            print(f"     🚷 Filtered (excluded title): {job.get('title','?')[:50]}")
            return False
    
    # Nigeria-friendly check (location & language only)
    if not is_nigeria_friendly(job):
        return False
    
    # Must match wanted role
    combined = f"{title_lower} {job.get('description','').lower()} {job.get('tags','').lower()}"
    if not any(kw.lower() in combined for kw in INCLUDE_KEYWORDS):
        print(f"     📋 Filtered (no role match): {job.get('title','?')[:50]}")
        return False
    
    # Add quality and priority
    job["_quality"] = get_quality_score(job)
    job["_priority"] = is_priority(job)
    
    return True
