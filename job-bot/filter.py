"""
filter.py — All filtering logic:
  - Halal check
  - English-only check
  - Nigeria-friendly check
  - Job preference check (include/exclude)
  - Priority tagging
  - Salary filter
  - Age filter
  - HTML cleaning
  - Fuzzy duplicate detection
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

FOREIGN_LANGUAGE_KEYWORDS = [
    "deutsch", "german speaking", "german language", "auf deutsch",
    "françisch", "french speaking required", "en français",
    "español", "spanish speaking required", "en español",
    "português", "portuguese speaking", "em português",
    "mandarin speaking", "cantonese speaking", "japanese speaking",
    "arabic speaking required", "russian speaking", "dutch speaking",
    "italian speaking", "korean speaking", "hindi speaking required",
    "fluent in german", "fluent in french", "fluent in spanish",
    "fluent in portuguese", "fluent in dutch", "fluent in italian",
    "native german", "native french", "native spanish", "native dutch",
    "native japanese", "native korean", "native mandarin",
    "muttersprachler", "langue maternelle",
]

NON_NIGERIA_FRIENDLY = [
    "us only", "usa only", "united states only", "must be based in us",
    "must reside in us", "north america only", "canada only",
    "uk only", "eu only", "europe only",
    "right to work in the us", "authorized to work in the united states",
    "must be located in us", "physically located in the us",
    "us citizen", "us citizenship required",
    "security clearance", "nato clearance",
    "australian residents only", "new zealand only",
]

SUBSCRIPTION_SOURCES = ["theladders", "job-hunt.org"]

# In-memory fuzzy duplicate store (resets each run — that's fine)
_seen_fingerprints = []


def strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    entities = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&rsquo;": "'", "&lsquo;": "'",
        "&rdquo;": '"', "&ldquo;": '"', "&mdash;": "—", "&ndash;": "–",
    }
    for entity, replacement in entities.items():
        clean = clean.replace(entity, replacement)
    return re.sub(r"\s+", " ", clean).strip()


def is_fuzzy_duplicate(job: dict) -> bool:
    """
    Checks if a very similar job (same title + company) was already
    seen THIS run from a different source. Uses fuzzy string matching.
    """
    fingerprint = f"{job.get('title','').lower().strip()} {job.get('company','').lower().strip()}"
    for seen in _seen_fingerprints:
        ratio = SequenceMatcher(None, fingerprint, seen).ratio()
        if ratio >= 0.85:
            print(f"     🔁 Fuzzy duplicate ({ratio:.0%} match): {job.get('title','?')}")
            return True
    _seen_fingerprints.append(fingerprint)
    return False


def is_too_old(job: dict) -> bool:
    """Skip jobs older than MAX_JOB_AGE_DAYS if a date is available."""
    if MAX_JOB_AGE_DAYS == 0:
        return False
    from datetime import datetime, timezone
    date_str = job.get("date_posted", "")
    if not date_str:
        return False  # No date = don't discard, give benefit of doubt
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
    """Skip jobs whose salary is explicitly below your minimum thresholds."""
    if MIN_SALARY_NGN == 0 and MIN_SALARY_USD == 0:
        return False
    salary_text = job.get("salary", "").lower()
    if not salary_text:
        return False  # Unknown salary — don't reject

    # Try extract a number from salary text
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
    """
    Scores a job 1–5 based on how complete its listing is.
    Shown as stars ⭐ in the Telegram message.
    """
    score = 1
    if job.get("company"):
        score += 0.5
    if job.get("salary"):
        score += 1
    if len(job.get("description", "")) > 100:
        score += 1
    if job.get("url") and "http" in job.get("url", ""):
        score += 0.5
    if job.get("tags"):
        score += 0.5
    if job.get("experience"):
        score += 0.5
    return min(5, int(score))


def is_priority(job: dict) -> bool:
    """Returns True if the job matches any PRIORITY_KEYWORDS."""
    text = f"{job.get('title','')} {job.get('description','')}".lower()
    return any(kw.lower() in text for kw in PRIORITY_KEYWORDS)


def is_english(text: str) -> bool:
    text_lower = text.lower()
    return not any(kw in text_lower for kw in FOREIGN_LANGUAGE_KEYWORDS)


def is_nigeria_friendly(job: dict) -> bool:
    combined = " ".join([
        job.get("location", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()

    if "nigeria" in combined:
        return True
    for keyword in NON_NIGERIA_FRIENDLY:
        if keyword in combined:
            print(f"     🌍 Filtered (not Nigeria-friendly): {job.get('title','?')}")
            return False
    if any(r in combined for r in ["remote", "worldwide", "anywhere", "global", "international"]):
        return True
    return True


def is_halal(job: dict) -> bool:
    """Master filter — returns True only if job passes ALL checks."""

    # 1. Clean HTML first
    job["description"] = strip_html(job.get("description", ""))

    # 2. Subscription source
    source = job.get("source", "").lower()
    if any(sub in source for sub in SUBSCRIPTION_SOURCES):
        return False

    # 3. Minimum description
    if MIN_DESCRIPTION_LENGTH > 0:
        if len(job.get("description", "")) < MIN_DESCRIPTION_LENGTH:
            return False

    # 4. Too old
    if is_too_old(job):
        return False

    # 5. Salary too low
    if is_salary_too_low(job):
        return False

    # 6. Fuzzy duplicate (same job from multiple sources)
    if is_fuzzy_duplicate(job):
        return False

    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()

    # 7. Haram keywords
    for keyword in HARAM_KEYWORDS:
        if keyword.lower() in text:
            print(f"     🚫 Filtered (haram): '{keyword}' in: {job.get('title','?')}")
            return False

    # 8. English only
    if not is_english(text):
        print(f"     🔤 Filtered (non-English): {job.get('title','?')}")
        return False

    # 9. Nigeria-friendly
    if not is_nigeria_friendly(job):
        return False

    # 10. Excluded titles
    title_lower = job.get("title", "").lower()
    for keyword in EXCLUDE_TITLES:
        if keyword.lower() in title_lower:
            print(f"     🚷 Filtered (excluded): {job.get('title','?')}")
            return False

    # 11. Must match at least one wanted role
    combined = f"{title_lower} {job.get('description','').lower()} {job.get('tags','').lower()}"
    if not any(kw.lower() in combined for kw in INCLUDE_KEYWORDS):
        print(f"     📋 Filtered (no matching role): {job.get('title','?')}")
        return False

    # 12. Tag quality score and priority onto the job for sender to use
    job["_quality"] = get_quality_score(job)
    job["_priority"] = is_priority(job)

    return True

def is_halal(job):
    """
    Main filtering function - returns True if job should be sent
    """
    
    # Get job text content to check
    title = job.get('title', '')
    description = job.get('description', '')
    company = job.get('company', '')
    tags = job.get('tags', '')
    
    # Combine all text for language detection
    all_text = f"{title} {description} {company} {tags}".lower()
    
    # ========== NEW: ENGLISH LANGUAGE FILTER ==========
    if not is_english_job(all_text):
        print(f"     🚫 Filtered (non-English): {title[:50]}...")
        return False
    # ==================================================
    
    # Your existing filters below...
    # (haram filter, location filter, etc.)
    
    return True


def is_english_job(text):
    """
    Detect if job posting is primarily in English
    Returns True for English, False for foreign languages
    """
    if not text:
        return True  # Empty text assume English
    
    # Common English words that appear in most job postings
    english_indicators = [
        'the', 'and', 'for', 'you', 'will', 'work', 'job', 'role',
        'position', 'team', 'company', 'remote', 'experience', 'skills',
        'required', 'responsibilities', 'qualifications', 'benefits',
        'salary', 'full-time', 'part-time', 'contract', 'freelance'
    ]
    
    # Common foreign language indicators (block these)
    foreign_indicators = {
        'german': ['german', 'deutsch', 'fließend', 'muttersprache', 'sprache', 'deutsche'],
        'french': ['french', 'français', 'parlez', 'bilingue', 'francophone', 'langue'],
        'spanish': ['spanish', 'español', 'idioma', 'bilingüe', 'castellano'],
        'portuguese': ['portuguese', 'português', 'idioma', 'brasil'],
        'dutch': ['dutch', 'nederlands', 'vloeiend', 'taal'],
        'italian': ['italian', 'italiano', 'lingua', 'madrelingua'],
        'chinese': ['chinese', 'mandarin', '普通话', '中文', '汉语'],
        'japanese': ['japanese', '日本語', 'nihongo', 'japonaise'],
        'korean': ['korean', '한국어', 'hangul'],
        'russian': ['russian', 'русский', 'russkiy'],
        'arabic': ['arabic', 'العربية', 'arabe', 'arabisch'],
        'hindi': ['hindi', 'हिन्दी'],
        'swedish': ['swedish', 'svenska', 'skandinavisk'],
        'polish': ['polish', 'polski', 'język'],
        'turkish': ['turkish', 'türkçe', 'dili'],
    }
    
    text_lower = text.lower()
    
    # Count English words present
    english_count = sum(1 for word in english_indicators if word in text_lower)
    
    # Check for foreign language indicators (if found, likely non-English)
    for language, indicators in foreign_indicators.items():
        for indicator in indicators:
            if indicator in text_lower:
                # Check if the job REQUIRES this foreign language
                if any(phrase in text_lower for phrase in [
                    f'{indicator} required', f'{indicator} speaking', 
                    f'fluent in {indicator}', f'{indicator} language',
                    'native ' + indicator
                ]):
                    return False
    
    # If very few English words, likely non-English
    if english_count < 3 and len(text.split()) > 20:
        return False
    
    return True


def contains_foreign_language_requirement(text):
    """
    Specifically check for requirements to speak foreign languages
    More aggressive filtering for jobs requiring non-English
    """
    text_lower = text.lower()
    
    # Patterns that indicate foreign language requirement
    foreign_patterns = [
        r'(?:fluent|proficient|native|business)\s+(?:in|level)\s+(?:german|french|spanish|mandarin|japanese|dutch|italian)',
        r'(?:german|french|spanish|dutch|italian|mandarin|japanese)\s+(?:required|mandatory|essential|must)',
        r'(?:speak|write|communicate)\s+(?:fluent|flowing)\s+(?:german|french|spanish)',
        r'language\s+requirement\s*:\s*(?:german|french|spanish)',
        r'bring\s+your\s+(?:german|french|spanish)',
        r'deutschkenntnisse',  # German
        r'français\s+obligatoire',  # French
        r'español\s+(?:requerido|necesario)',  # Spanish
    ]
    
    for pattern in foreign_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False
