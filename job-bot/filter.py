"""
filter.py — Halal job filter
Excludes any job that contains haram-related keywords in title, company, or description.
"""

HARAM_KEYWORDS = [
    # Gambling
    "gambling", "casino", "bet ", "betting", "betway", "bet365", "1xbet",
    "sportybet", "lottery", "lotto", "jackpot", "poker", "slots", "roulette",
    "bookmaker", "odds", "wager", "sportsbook",

    # Alcohol
    "alcohol", "alcoholic", "brewery", "brewing", "brewer", "winery", "wine",
    "beer", "lager", "spirits", "liquor", "distillery", "distilling", "vodka",
    "whiskey", "whisky", "gin ", "rum ", "champagne", "cocktail", "bartender",
    "bar manager", "bar staff", "mixologist", "sommelier", "cellar",

    # Nightlife
    "nightclub", "night club", "strip club", "stripclub", "gentlemen's club",
    "adult entertainment", "cabaret",

    # Church / Religious (non-Islamic institutions hiring for religious roles)
    "church", "pastor", "bishop", "diocese", "cathedral", "chapel",
    "missionary", "ministry of christ", "christian mission", "seminary",
    "reverend", "deacon", "convent", "monastery", "pope", "vatican",
    "evangelical", "pentecostal church",

    # Adult / Haram content
    "adult content", "onlyfans", "escort", "prostitut", "porn", "erotic",
    "nude", "nudity", "webcam model", "sex worker", "fetish",

    # Pork / Haram food
    "pork", "swine", "bacon", "ham producer", "pig farm", "hog farm",

    # Riba / Haram finance
    "payday loan", "loan shark", "predatory lending",

    # Tobacco
    "tobacco", "cigarette", "vape company", "e-cigarette manufacturer",

    # Drugs
    "cannabis dispensary", "marijuana dispensary", "drug dealer",
]

def is_halal(job: dict) -> bool:
    """Returns True if the job passes the halal filter."""
    text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("description", ""),
        job.get("tags", ""),
    ]).lower()

    for keyword in HARAM_KEYWORDS:
        if keyword.lower() in text:
            print(f"     🚫 Filtered (haram): '{keyword}' found in: {job.get('title','?')} @ {job.get('company','?')}")
            return False

    return True
