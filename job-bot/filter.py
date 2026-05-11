"""
filter.py — All filtering logic
UPDATED: Better location filtering, German language detection, HTML cleaning
"""

import re
from difflib import SequenceMatcher
from config import (
    INCLUDE_KEYWORDS, EXCLUDE_TITLES, PRIORITY_KEYWORDS,
    MIN_SALARY_NGN, MIN_SALARY_USD,
    MAX_JOB_AGE_DAYS, MIN_DESCRIPTION_LENGTH
)

HARAM_KEYWORDS = [
    "gambling", "casino", "bet ", "betting", "betway", "bet365", "1xbet",
    "sportybet", "lottery", "lotto", "jackpot", "poker", "slots", "roulette",
    "bookmaker", "odds", "wager", "sportsbook",
    "alcohol", "alcoholic", "brewery", "brewing", "brewer", "winery", "wine",
    "beer", "lager", "spirits", "liquor", "distillery", "distilling", "vodka",
    "whiskey", "whisky", "cocktail", "bartender", "bar manager", "bar staff",
    "mixologist", "sommelier", "cellar",
    "nightclub", "night club", "strip club", "stripclub", "gentlemen's club",
    "adult entertainment", "cabaret",
    "church", "pastor", "bishop", "diocese", "cathedral", "chapel",
    "missionary", "ministry of christ", "christian mission", "seminary",
    "reverend", "deacon", "convent", "monastery", "evangelical",
    "pentecostal church",
    "adult content", "onlyfans", "escort", "prostitut", "porn", "erotic",
    "nude", "nudity", "webcam model", "sex worker", "fetish",
    "pork", "swine", "bacon", "ham producer", "pig farm", "hog farm",
    "payday loan", "loan shark", "predatory lending",
    "tobacco", "cigarette", "vape company", "e-cigarette manufacturer",
    "cannabis dispensary", "marijuana dispensary",
]

# Countries/locations that are NOT accessible from Nigeria
RESTRICTED_LOCATIONS = [
    "usa only", "us only", "united states only", "must be based in us",
    "must reside in us", "north america only", "canada only",
    "uk only", "eu only", "europe only", "germany only", "netherlands only",
    "right to work in the us", "authorized to work in the united states",
    "must be located in us", "physically located in the us",
    "us citizen", "us citizenship required", "green card",
    "security clearance", "nato clearance",
    "australian residents only", "new zealand only",
    "romania", "romania only", "must be in romania",
    "latin america only", "latam only", "brazil", "colombia", "philippines",
    "americas", "europe", "asia", "oceania",  # Continents without worldwide
    "switzerland", "switzerland only",
]

# German language indicators (block these jobs)
GERMAN_INDICATORS = [
    "🇩🇪", "german", "deutsch", "fließend", "muttersprache", "sprache",
    "german speaking", "german language", "auf deutsch", "die stelle",
    "wir suchen", "ihre aufgaben", "ihr profil", "remote deutschland",
    "german required", "deutschkenntnisse", "muttersprachler",
]

# Locations that are ACCEPTABLE (remote worldwide or Nigeria)
ACCEPTABLE_LOCATIONS = [
    "worldwide", "global", "anywhere", "remote", "nigeria", "africa",
    "uk", "united kingdom", "europe", "canada", "australia",  # Remote-friendly regions
]

SUBSCRIPTION_SOURCES = ["theladders", "job-hunt.org"]

_seen_fingerprints = []


def strip_html(text: str) -> str:
    """Clean HTML tags and fix formatting"""
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', ' ', text)
    
    # Fix common HTML entities
    entities = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&rsquo;": "'", "&lsquo;": "'",
        "&rdquo;": '"', "&ldquo;": '"', "&mdash;": "—", "&ndash;": "–",
        "&amp;#39;": "'", "&#x27;": "'", "&apos;": "'",
        "&amp;quot;": '"', "&raquo;": "»", "&laquo;": "«",
        "&bull;": "•", "&copy;": "©", "&reg;": "®",
        "â¢": "•", "â": "–", "â": "—", "â": "'", "â": '"', "â": '"',
    }
    for entity, replacement in entities.items():
        clean = clean.replace(entity, replacement)
    
    # Remove escaped slashes
    clean = clean.replace('\\/', '/')
    clean = clean.replace('\\', '')
    
    # Fix comma-separated single letters
    clean = re.sub(r'\b([a-z]),\s+([a-z]),\s+([a-z]),\s+([a-z])', r'\1\2\3\4', clean)
    clean = re.sub(r',\s+([a-z])', r' \1', clean)
    
    # Remove excessive whitespace
    clean = re.sub(r'\s+', ' ', clean)
    clean = clean.strip()
    
    # Add line breaks back after periods
    clean = re.sub(r'(\.\s+)([A-Z])', r'\1\n\2', clean)
    
    return clean


def is_german_job(text: str) -> bool:
    """Check if job posting is in German or requires German language"""
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for German indicators
    for indicator in GERMAN_INDICATORS:
        if indicator.lower() in text_lower:
            return True
    
    # Check for German flag emoji
    if '🇩🇪' in text:
        return True
    
    return False


def is_location_restricted(location: str, description: str) -> bool:
    """Check if job location restricts Nigerians from applying"""
    combined = f"{location.lower()} {description.lower()}"
    
    # First check if job is explicitly remote worldwide
    remote_indicators = ['remote', 'worldwide', 'global', 'anywhere', 'work from home']
    is_remote = any(indicator in combined for indicator in remote_indicators)
    
    if is_remote:
        # Check if remote is restricted to specific regions
        for restricted in RESTRICTED_LOCATIONS:
            if restricted in combined:
                return True
        return False  # Remote without restrictions is fine
    
    # Check for specific country restrictions
    for restricted in RESTRICTED_LOCATIONS:
        if restricted in combined:
            return True
    
    # Check if location contains only specific countries (no remote option)
    countries = ['germany', 'netherlands', 'brazil', 'colombia', 'philippines', 'switzerland', 'us', 'usa']
    for country in countries:
        if country in location.lower() and 'remote' not in location.lower():
            return True
    
    return False


def clean_location(location: str) -> str:
    """Clean and standardize location field"""
    if not location:
        return "Remote / Worldwide"
    
    # Remove HTML
    location = strip_html(location)
    
    # Remove prefix
    location = re.sub(r'^Remote\s*[-–]\s*', '', location)
    
    # If location is US/Canada only, mark as restricted
    if location.lower() in ['us', 'usa', 'canada', 'uk']:
        return location
    
    if not location or len(location) < 2:
        return "Remote / Worldwide"
    
    return location


def is_nigeria_friendly(job: dict) -> bool:
    """
    Check if job is accessible from Nigeria.
    Returns False if:
    - Job requires being in specific countries (US, Brazil, Germany, etc.)
    - Job is written in German
    - Location is restricted to Americas/Europe/Asia (without worldwide)
    """
    title = job.get("title", "")
    location = job.get("location", "")
    description = job.get("description", "")
    combined = f"{title} {location} {description}"
    
    # Clean first
    combined = strip_html(combined)
    location_clean = clean_location(location)
    
    # Check for German language
    if is_german_job(combined) or is_german_job(title):
        print(f"     🇩🇪 Filtered (German language job): {title[:50]}")
        return False
    
    # Check for German flag in title
    if '🇩🇪' in title:
        print(f"     🇩🇪 Filtered (German job): {title[:50]}")
        return False
    
    # Check location restrictions
    if is_location_restricted(location, description):
        print(f"     🌍 Filtered (location restricted): {title[:50]} - {location_clean}")
        return False
    
    # If job explicitly mentions Nigeria - definitely good
    if "nigeria" in combined or "lagos" in combined or "abuja" in combined:
        return True
    
    # If job is remote and doesn't have specific location requirements
    if "remote" in combined and not is_location_restricted(location, description):
        return True
    
    # Default: allow if unclear
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
    """Clean all job text fields"""
    if job.get('title'):
        job['title'] = strip_html(job['title'])
        # Remove German flag from title
        job['title'] = job['title'].replace('🇩🇪', '').strip()
        job['title'] = re.sub(r'\\/', '/', job['title'])
        job['title'] = job['title'].strip()
    
    if job.get('description'):
        job['description'] = strip_html(job['description'])
        # Remove truncated HTML
        if '<p' in job['description'] or '<div' in job['description']:
            job['description'] = re.sub(r'<[^>]+>', ' ', job['description'])
        if len(job['description']) < 20:
            job['description'] = "Click 'Apply Now' below for details."
    
    if job.get('company'):
        job['company'] = strip_html(job['company'])
        job['company'] = re.sub(r'\\/', '/', job['company'])
        if not job['company'] or len(job['company']) < 2:
            job['company'] = "Not specified"
    
    if job.get('location'):
        job['location'] = clean_location(job['location'])
    
    return job


def is_halal(job: dict) -> bool:
    """Master filter"""
    
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
    
    # Get text for checks
    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()
    
    # Haram check
    for keyword in HARAM_KEYWORDS:
        if keyword.lower() in text:
            print(f"     🚫 Filtered (haram - {keyword}): {job.get('title','?')[:50]}")
            return False
    
    # Excluded titles
    title_lower = job.get("title", "").lower()
    for keyword in EXCLUDE_TITLES:
        if keyword.lower() in title_lower:
            print(f"     🚷 Filtered (excluded): {job.get('title','?')[:50]}")
            return False
    
    # Nigeria-friendly check (includes location & German filtering)
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
