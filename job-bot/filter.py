"""
filter.py — Simplified filtering logic
FOR PUBLIC BOT: No keyword restrictions - ALL halal jobs pass
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
        "israel", "tel aviv", "jerusalem",
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
    
    clean = re.sub(r'<[^>]+>', ' ', text)
    clean = re.sub(r'class="[^"]*"', '', clean)
    clean = re.sub(r'style="[^"]*"', '', clean)
    clean = re.sub(r'data-[^=]*="[^"]*"', '', clean)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.DOTALL)
    
    entities = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&rsquo;": "'", "&lsquo;": "'",
        "&rdquo;": '"', "&ldquo;": '"', "&mdash;": "—", "&ndash;": "–",
        "&amp;#39;": "'", "&#x27;": "'", "&apos;": "'",
        "â¢": "•", "â": "–", "â": "—", "â": "'", "â": '"', "â": '"',
    }
    for entity, replacement in entities.items():
        clean = clean.replace(entity, replacement)
    
    clean = clean.replace('\\/', '/')
    clean = clean.replace('\\', '')
    clean = re.sub(r'tw-[a-zA-Z0-9-]+', '', clean)
    clean = re.sub(r'figma-[a-zA-Z0-9-]+', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    clean = clean.strip()
    
    return clean


def is_german_job(text: str) -> bool:
    """Check if job posting is in German"""
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
    if re.search(r'[\u4e00-\u9fff]', text):
        return True
    return False


def is_location_restricted(location: str, description: str, source: str = "") -> bool:
    """Check if job location restricts Nigerians from applying"""
    combined = f"{location.lower()} {description.lower()}"
    
    # Telegram and Nigerian sources are ALWAYS allowed
    always_keep_sources = ["Telegram", "Jobberman", "MyJobMag", "NGCareers", "JobGurus", "Africa Jobs", "NGO / UN Jobs"]
    if source in always_keep_sources:
        return False
    
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
    """Clean location field"""
    if not location:
        return "Remote"
    location = strip_html(location)
    location = re.sub(r'^Remote\s*[-–]\s*', '', location)
    if not location or len(location) < 2:
        return "Remote"
    return location


def is_nigeria_friendly(job: dict, source: str = "") -> bool:
    """Check if job is accessible from Nigeria"""
    title = job.get("title", "")
    location = job.get("location", "")
    description = job.get("description", "")
    combined = f"{title} {location} {description}"
    combined = strip_html(combined)
    
    # Telegram and Nigerian sources are ALWAYS kept
    always_keep_sources = ["Telegram", "Jobberman", "MyJobMag", "NGCareers", "JobGurus", "Africa Jobs", "NGO / UN Jobs"]
    if source in always_keep_sources:
        return True
    
    if is_german_job(combined) or is_german_job(title):
        print(f"     🇩🇪 Filtered (German job): {title[:50]}")
        return False
    
    if is_chinese_job(combined) or is_chinese_job(location):
        print(f"     🇨🇳 Filtered (Chinese job): {title[:50]}")
        return False
    
    if is_location_restricted(location, description, source):
        print(f"     🌍 Filtered (location restricted): {title[:50]}")
        return False
    
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


def extract_clean_title(job: dict) -> str:
    """Extract clean title"""
    title = job.get('title', '')
    if title and len(title) > 3 and len(title) < 200:
        title = strip_html(title)
        title = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|JOB|POSITION|NOW HIRING)[:\s]+', '', title, flags=re.IGNORECASE)
        title = title.strip()
        if title and len(title) > 3:
            return title[:100]
    return "Job Opportunity"


def extract_clean_company(job: dict) -> str:
    """Extract clean company name"""
    company = job.get('company', '')
    if company and company not in ["Not specified", ""]:
        company = strip_html(company)
        if len(company) > 2 and len(company) < 50:
            return company
    return "Not specified"


def extract_clean_location(job: dict) -> str:
    """Extract clean location"""
    location = job.get('location', '')
    if location and location not in ["", "Not specified"]:
        location = strip_html(location)
        if len(location) > 2 and len(location) < 100:
            return location
    return "Remote"


def clean_job_data(job: dict) -> dict:
    """Clean all job text fields"""
    job['title'] = extract_clean_title(job)
    job['company'] = extract_clean_company(job)
    job['location'] = extract_clean_location(job)
    
    if job.get('description'):
        job['description'] = strip_html(job['description'])
        if not job['description'] or len(job['description']) < 20:
            job['description'] = "Click the 'Apply Now' button below for more details."
    
    return job


def is_halal(job: dict, source: str = "") -> bool:
    """
    Master filter for PUBLIC BOT
    NO KEYWORD RESTRICTIONS - ALL halal jobs pass
    Only filters: location, language, duplicates, age, salary
    """
    
    job = clean_job_data(job)
    
    # Minimum description length
    if MIN_DESCRIPTION_LENGTH > 0:
        if len(job.get("description", "")) < MIN_DESCRIPTION_LENGTH:
            return False
    
    # Age filter
    if is_too_old(job):
        print(f"     📅 Filtered (too old): {job.get('title','?')[:50]}")
        return False
    
    # Salary filter
    if is_salary_too_low(job):
        print(f"     💰 Filtered (salary too low): {job.get('title','?')[:50]}")
        return False
    
    # Duplicate filter
    if is_fuzzy_duplicate(job):
        return False
    
    # Excluded titles
    title_lower = job.get("title", "").lower()
    for keyword in EXCLUDE_TITLES:
        if keyword.lower() in title_lower:
            print(f"     🚷 Filtered (excluded title): {job.get('title','?')[:50]}")
            return False
    
    # Nigeria-friendly check (location & language only)
    if not is_nigeria_friendly(job, source):
        return False
    
    # ==============================================
    # NO KEYWORD RESTRICTIONS FOR PUBLIC BOT
    # ALL JOBS THAT PASS ABOVE CHECKS ARE SENT
    # ==============================================
    
    # Add quality and priority scores
    job["_quality"] = get_quality_score(job)
    job["_priority"] = is_priority(job)
    
    return True
