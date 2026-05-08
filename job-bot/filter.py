"""
filter.py — All filtering logic:
  1. Subscription source block
  2. Haram keyword filter
  3. English-only filter
  4. Nigeria-friendly filter
  5. Job preference filter (include/exclude)
  6. Salary filter
  7. Job age filter
  + HTML cleaning, priority tagging, fuzzy duplicate detection
"""

import re
from datetime import datetime, timezone
from config import (
    INCLUDE_KEYWORDS, EXCLUDE_TITLES, PRIORITY_KEYWORDS,
    MIN_DESCRIPTION_LENGTH, MIN_SALARY_USD, MIN_SALARY_NGN, MAX_JOB_AGE_DAYS,
)

HARAM_KEYWORDS = [
    # Gambling
    "gambling", "casino", "bet ", "betting", "betway", "bet365", "1xbet",
    "sportybet", "lottery", "lotto", "jackpot", "poker", "slots", "roulette",
    "bookmaker", "odds", "wager", "sportsbook",
    # Alcohol
    "alcohol", "alcoholic", "brewery", "brewing", "brewer", "winery", "wine",
    "beer", "lager", "spirits", "liquor", "distillery", "distilling", "vodka",
    "whiskey", "whisky", "cocktail", "bartender", "bar manager", "bar staff",
    "mixologist", "sommelier", "cellar",
    # Nightlife
    "nightclub", "night club", "strip club", "stripclub", "gentlemen's club",
    "adult entertainment", "cabaret",
    # Church / Religious non-Islamic
    "church", "pastor", "bishop", "diocese", "cathedral", "chapel",
    "missionary", "ministry of christ", "christian mission", "seminary",
    "reverend", "deacon", "convent", "monastery", "evangelical",
    "pentecostal church",
    # Adult content
    "adult content", "onlyfans", "escort", "prostitut", "porn", "erotic",
    "nude", "nudity", "webcam model", "sex worker", "fetish",
    # Pork
    "pork", "swine", "bacon", "ham producer", "pig farm", "hog farm",
    # Riba
    "payday loan", "loan shark", "predatory lending",
    # Tobacco
    "tobacco", "cigarette", "vape company", "e-cigarette manufacturer",
    # Drugs
    "cannabis dispensary", "marijuana dispensary",
]

FOREIGN_LANGUAGE_KEYWORDS = [
    "deutsch", "german speaking", "german language",
    "french speaking required", "en français",
    "spanish speaking required", "en español",
    "portuguese speaking", "em português",
    "mandarin speaking", "cantonese speaking", "japanese speaking",
    "arabic speaking required", "russian speaking", "dutch speaking",
    "italian speaking", "korean speaking", "hindi speaking required",
    "fluent in german", "fluent in french", "fluent in spanish",
    "fluent in portuguese", "fluent in dutch", "fluent in italian",
    "native german", "native french", "native spanish", "native dutch",
    "native japanese", "native korean", "native mandarin",
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


# ---------------------------------------------------------------------------
# HTML Cleaning
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Fuzzy Duplicate Detection
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    """Lowercase, strip punctuation and extra spaces for comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def is_fuzzy_duplicate(job: dict, seen_titles: set) -> bool:
    """
    Checks if a job with a very similar title+company already exists.
    Catches the same job listed on multiple platforms with different IDs.
    """
    key = _normalise(f"{job.get('title', '')} {job.get('company', '')}")
    if key in seen_titles:
        return True
    seen_titles.add(key)
    return False


# ---------------------------------------------------------------------------
# Priority Tagging
# ---------------------------------------------------------------------------

def is_priority(job: dict) -> bool:
    """Returns True if job matches any priority keyword."""
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    return any(kw.lower() in text for kw in PRIORITY_KEYWORDS)


# ---------------------------------------------------------------------------
# Job Age Filter
# ---------------------------------------------------------------------------

def is_too_old(job: dict) -> bool:
    """Returns True if job is older than MAX_JOB_AGE_DAYS."""
    if MAX_JOB_AGE_DAYS == 0:
        return False
    date_str = job.get("date_posted", "")
    if not date_str:
        return False  # No date info — allow through
    try:
        posted = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - posted).days
        if age > MAX_JOB_AGE_DAYS:
            print(f"     📅 Filtered (too old, {age}d): {job.get('title','?')}")
            return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Salary Filter
# ---------------------------------------------------------------------------

def is_below_min_salary(job: dict) -> bool:
    """Returns True if salary is explicitly below configured minimums."""
    if MIN_SALARY_USD == 0 and MIN_SALARY_NGN == 0:
        return False

    salary_text = job.get("salary", "").lower()
    if not salary_text:
        return False  # No salary info — allow through

    # Check USD
    if MIN_SALARY_USD > 0:
        usd_match = re.search(r"\$\s?([\d,]+)", salary_text)
        if usd_match:
            amount = int(usd_match.group(1).replace(",", ""))
            if amount < MIN_SALARY_USD:
                print(f"     💸 Filtered (low salary ${amount}): {job.get('title','?')}")
                return True

    # Check NGN
    if MIN_SALARY_NGN > 0:
        ngn_match = re.search(r"[₦N]\s?([\d,]+)", salary_text)
        if ngn_match:
            amount = int(ngn_match.group(1).replace(",", ""))
            if amount < MIN_SALARY_NGN:
                print(f"     💸 Filtered (low salary ₦{amount}): {job.get('title','?')}")
                return True

    return False


# ---------------------------------------------------------------------------
# Core Filters
# ---------------------------------------------------------------------------

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
    for kw in NON_NIGERIA_FRIENDLY:
        if kw in combined:
            print(f"     🌍 Filtered (not Nigeria-friendly): {job.get('title','?')}")
            return False
    remote_indicators = ["remote", "worldwide", "anywhere", "global", "international"]
    if any(r in combined for r in remote_indicators):
        return True
    return True


def matches_include_keywords(job: dict) -> bool:
    combined = " ".join([
        job.get("title", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()
    if any(kw.lower() in combined for kw in INCLUDE_KEYWORDS):
        return True
    print(f"     📋 Filtered (no matching role): {job.get('title','?')}")
    return False


def matches_exclude_titles(job: dict) -> bool:
    title = job.get("title", "").lower()
    for kw in EXCLUDE_TITLES:
        if kw.lower() in title:
            print(f"     🚷 Filtered (excluded title): {job.get('title','?')}")
            return True
    return False


# ---------------------------------------------------------------------------
# Master Filter
# ---------------------------------------------------------------------------

def is_halal(job: dict) -> bool:
    """Returns True only if job passes ALL filters."""

    # Clean HTML first
    job["description"] = strip_html(job.get("description", ""))

    # 1. Subscription source
    source = job.get("source", "").lower()
    if any(sub in source for sub in SUBSCRIPTION_SOURCES):
        return False

    # 2. Minimum description length
    if MIN_DESCRIPTION_LENGTH > 0:
        if len(job.get("description", "")) < MIN_DESCRIPTION_LENGTH:
            return False

    # 3. Job age
    if is_too_old(job):
        return False

    # 4. Salary minimum
    if is_below_min_salary(job):
        return False

    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()

    # 5. Haram filter
    for kw in HARAM_KEYWORDS:
        if kw.lower() in text:
            print(f"     🚫 Filtered (haram '{kw}'): {job.get('title','?')}")
            return False

    # 6. English only
    if not is_english(text):
        print(f"     🔤 Filtered (non-English): {job.get('title','?')}")
        return False

    # 7. Nigeria-friendly
    if not is_nigeria_friendly(job):
        return False

    # 8. Excluded titles
    if matches_exclude_titles(job):
        return False

    # 9. Must match a wanted role
    if not matches_include_keywords(job):
        return False

    # Tag as priority if applicable
    job["priority"] = is_priority(job)

    return True
