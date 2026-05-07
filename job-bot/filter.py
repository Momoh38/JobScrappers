"""
filter.py — Halal job filter + English filter + Nigeria-friendly filter
"""

import re

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
    "deutsch", "german speaking", "german language", "auf deutsch",
    "französisch", "french speaking required", "en français",
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
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def is_english(text: str) -> bool:
    text_lower = text.lower()
    for keyword in FOREIGN_LANGUAGE_KEYWORDS:
        if keyword in text_lower:
            return False
    return True


def is_nigeria_friendly(job: dict) -> bool:
    location = job.get("location", "").lower()
    description = job.get("description", "").lower()
    tags = job.get("tags", "").lower()
    combined = f"{location} {description} {tags}"

    if "nigeria" in combined:
        return True

    for keyword in NON_NIGERIA_FRIENDLY:
        if keyword in combined:
            print(f"     🌍 Filtered (not Nigeria-friendly): '{keyword}' in {job.get('title','?')}")
            return False

    remote_indicators = ["remote", "worldwide", "anywhere", "global", "international"]
    if any(r in combined for r in remote_indicators):
        return True

    return True


def is_halal(job: dict) -> bool:
    job["description"] = strip_html(job.get("description", ""))

    source = job.get("source", "").lower()
    for sub in SUBSCRIPTION_SOURCES:
        if sub in source:
            return False

    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()

    for keyword in HARAM_KEYWORDS:
        if keyword.lower() in text:
            print(f"     🚫 Filtered (haram): '{keyword}' in: {job.get('title','?')}")
            return False

    if not is_english(text):
        print(f"     🔤 Filtered (non-English): {job.get('title','?')}")
        return False

    if not is_nigeria_friendly(job):
        return False

    return True
