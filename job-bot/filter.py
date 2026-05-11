"""
filter.py — All filtering logic:
  - Halal check
  - Nigeria-friendly check (improved)
  - Job preference check (include/exclude)
  - Priority tagging
  - Salary filter
  - Age filter
  - HTML cleaning
  - Fuzzy duplicate detection
  - REMOVED: Non-English filter (was causing issues)
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

# Countries/locations to filter out (jobs that require being in these locations)
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
    "latin america only", "latam only",
]

SUBSCRIPTION_SOURCES = ["theladders", "job-hunt.org"]

# In-memory fuzzy duplicate store
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
    
    # Remove escaped slashes (like \/ becomes /)
    clean = clean.replace('\\/', '/')
    clean = clean.replace('\\', '')
    
    # Fix comma-separated single letters (like "o, p, e, r, a, t, i, o, n, s")
    clean = re.sub(r'\b([a-z]),\s+([a-z]),\s+([a-z]),\s+([a-z])', r'\1\2\3\4', clean)
    clean = re.sub(r',\s+([a-z])', r' \1', clean)
    
    # Remove extra whitespace and fix line breaks
    clean = re.sub(r'\s+', ' ', clean)
    clean = clean.strip()
    
    # Add line breaks back for readability (after periods)
    clean = re.sub(r'(\.\s+)([A-Z])', r'\1\n\2', clean)
    
    return clean


def clean_location(location: str) -> str:
    """Clean and standardize location field"""
    if not location:
        return "Remote / Worldwide"
    
    # Remove HTML and clean
    location = strip_html(location)
    
    # Remove "Remote - " prefix if exists
    location = re.sub(r'^Remote\s*[-–]\s*', '', location)
    
    # If location is empty after cleaning, return Remote
    if not location or len(location) < 2:
        return "Remote / Worldwide"
    
    return location


def is_nigeria_friendly(job: dict) -> bool:
    """
    Check if job is accessible from Nigeria.
    Returns True if:
    - Job explicitly mentions Nigeria/Africa
    - Job is fully remote worldwide
    - Job doesn't have restricted location requirements
    """
    combined = " ".join([
        job.get("location", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()
    
    # Clean the combined text first
    combined = strip_html(combined)
    
    # If job explicitly mentions Nigeria or Africa - definitely good
    if "nigeria" in combined or "africa" in combined or "lagos" in combined or "abuja" in combined:
        return True
    
    # If job is fully remote with no location restrictions
    if "remote" in combined and "worldwide" in combined:
        return True
    if "remote" in combined and "anywhere" in combined:
        return True
    if "remote" in combined and "global" in combined:
        return True
    
    # Check for restricted locations (USA, UK, EU, etc.)
    for keyword in RESTRICTED_LOCATIONS:
        if keyword in combined:
            print(f"     🌍 Filtered (location restricted): {job.get('title','?')[:50]} - {keyword}")
            return False
    
    # If location contains specific countries only (Germany, Netherlands, etc.)
    specific_countries = ['germany', 'netherlands', 'ireland', 'uk ', ' united kingdom', 'usa', 'canada', 'australia']
    location_text = job.get("location", "").lower()
    for country in specific_countries:
        if country in location_text and 'remote' not in location_text:
            print(f"     🌍 Filtered (country-specific, not remote): {job.get('title','?')[:50]} - {country}")
            return False
    
    # Default: allow if remote or unclear
    return True


def is_fuzzy_duplicate(job: dict) -> bool:
    """Check if a similar job was already seen"""
    fingerprint = f"{job.get('title','').lower().strip()} {job.get('company','').lower().strip()}"
    for seen in _seen_fingerprints:
        ratio = SequenceMatcher(None, fingerprint, seen).ratio()
        if ratio >= 0.85:
            print(f"     🔁 Fuzzy duplicate ({ratio:.0%} match): {job.get('title','?')}")
            return True
    _seen_fingerprints.append(fingerprint)
    return False


def is_too_old(job: dict) -> bool:
    """Skip jobs older than MAX_JOB_AGE_DAYS"""
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
            print(f"     📅 Filtered (too old, {age_days}d): {job.get('title','?')}")
            return True
    except Exception:
        pass
    return False


def is_salary_too_low(job: dict) -> bool:
    """Skip jobs with explicitly low salary"""
    if MIN_SALARY_NGN == 0 and MIN_SALARY_USD == 0:
        return False
    salary_text = job.get("salary", "").lower()
    if not salary_text:
        return False
    
    # Clean salary text
    salary_text = strip_html(salary_text)
    
    numbers = re.findall(r"[\d,]+", salary_text.replace(",", ""))
    if not numbers:
        return False
    amount = int(numbers[0])
    
    if "₦" in salary_text or "ngn" in salary_text or "naira" in salary_text:
        if MIN_SALARY_NGN > 0 and amount < MIN_SALARY_NGN:
            print(f"     💰 Filtered (salary too low ₦{amount:,}): {job.get('title','?')}")
            return True
    elif "$" in salary_text or "usd" in salary_text:
        if MIN_SALARY_USD > 0 and amount < MIN_SALARY_USD:
            print(f"     💰 Filtered (salary too low ${amount:,}): {job.get('title','?')}")
            return True
    return False


def get_quality_score(job: dict) -> int:
    """Score job 1-5 based on completeness"""
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
    """Check if job matches priority keywords"""
    text = f"{job.get('title','')} {job.get('description','')}".lower()
    text = strip_html(text)
    return any(kw.lower() in text for kw in PRIORITY_KEYWORDS)


def clean_job_data(job: dict) -> dict:
    """Clean all text fields in the job"""
    # Clean title
    if job.get('title'):
        job['title'] = strip_html(job['title'])
        # Remove weird patterns
        job['title'] = re.sub(r'\\/', '/', job['title'])
        job['title'] = job['title'].strip()
    
    # Clean description
    if job.get('description'):
        job['description'] = strip_html(job['description'])
        # Remove too short descriptions (like just "<p> </p>")
        if len(job['description']) < 20:
            job['description'] = "Click the 'Apply Now' button below for more details."
    
    # Clean company
    if job.get('company'):
        job['company'] = strip_html(job['company'])
        job['company'] = re.sub(r'\\/', '/', job['company'])
        if not job['company'] or len(job['company']) < 2:
            job['company'] = "Not specified"
    
    # Clean location
    if job.get('location'):
        job['location'] = clean_location(job['location'])
    
    return job


def is_halal(job: dict) -> bool:
    """Master filter — returns True only if job passes ALL checks."""
    
    # First clean all HTML and formatting
    job = clean_job_data(job)
    
    # 1. Minimum description length check
    if MIN_DESCRIPTION_LENGTH > 0:
        if len(job.get("description", "")) < MIN_DESCRIPTION_LENGTH:
            return False
    
    # 2. Too old check
    if is_too_old(job):
        return False
    
    # 3. Salary too low
    if is_salary_too_low(job):
        return False
    
    # 4. Fuzzy duplicate check
    if is_fuzzy_duplicate(job):
        return False
    
    # 5. Get text for keyword checks
    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()
    
    # 6. Haram keywords check
    for keyword in HARAM_KEYWORDS:
        if keyword.lower() in text:
            print(f"     🚫 Filtered (haram): '{keyword}' in: {job.get('title','?')[:50]}")
            return False
    
    # 7. Excluded titles check
    title_lower = job.get("title", "").lower()
    for keyword in EXCLUDE_TITLES:
        if keyword.lower() in title_lower:
            print(f"     🚷 Filtered (excluded): {job.get('title','?')[:50]}")
            return False
    
    # 8. Nigeria-friendly check (includes location filtering)
    if not is_nigeria_friendly(job):
        return False
    
    # 9. Must match at least one wanted role
    combined = f"{title_lower} {job.get('description','').lower()} {job.get('tags','').lower()}"
    if not any(kw.lower() in combined for kw in INCLUDE_KEYWORDS):
        print(f"     📋 Filtered (no matching role): {job.get('title','?')[:50]}")
        return False
    
    # 10. Add quality and priority scores
    job["_quality"] = get_quality_score(job)
    job["_priority"] = is_priority(job)
    
    return True
