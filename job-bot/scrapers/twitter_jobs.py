"""
scrapers/twitter_jobs.py — Scrapes public X/Twitter job accounts via Nitter
(Nitter is a privacy-friendly Twitter frontend that doesn't require login)
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup

# Public job-focused X accounts to monitor via Nitter
TWITTER_JOB_ACCOUNTS = [
    "BenoHr80463",
    "JobFound5",
    "jobsregion",
    "TrybeCityJobs",
    "Halosznn_",
    # Additional Nigeria/remote job accounts
    "NgJobAlert",
    "RemoteJobsNG",
    "JobsInNigeria",
    "AfricaJobs",
    "RemoteJobsAfrica",
]

# Nitter instances to try (public mirrors)
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.net",
]

JOB_KEYWORDS = [
    "hiring", "vacancy", "job", "role", "position", "opening",
    "apply", "opportunity", "recruit", "needed", "wanted",
    "salary", "remote", "full-time", "part-time", "freelance",
    "engineer", "developer", "manager", "analyst", "designer",
]


def scrape_twitter_jobs() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for account in TWITTER_JOB_ACCOUNTS:
        fetched = False
        for nitter in NITTER_INSTANCES:
            try:
                url = f"{nitter}/{account}"
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                tweets = soup.select("div.tweet-content") or soup.select("div.timeline-item .tweet-content")

                if not tweets:
                    continue

                for tweet in tweets[:15]:
                    text = tweet.get_text(separator="\n", strip=True)

                    if not _looks_like_job(text):
                        continue

                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    title = lines[0][:100] if lines else "Job Opening"
                    description = " ".join(lines[1:3]) if len(lines) > 1 else ""

                    link_el = tweet.find("a", href=True)
                    link = link_el["href"] if link_el else f"https://x.com/{account}"
                    if link.startswith("/"):
                        link = f"https://x.com{link}"

                    job_id = hashlib.md5(f"{account}{text[:80]}".encode()).hexdigest()

                    jobs.append({
                        "id": f"twitter_{job_id}",
                        "title": title,
                        "company": f"@{account}",
                        "location": "Nigeria / Remote",
                        "salary": _extract_salary(text),
                        "description": description[:300],
                        "tags": "X (Twitter)",
                        "url": link,
                        "source": f"X @{account}",
                    })

                fetched = True
                break  # Success, don't try other instances

            except Exception as e:
                print(f"     ⚠️ Twitter @{account} via {nitter} failed: {e}")
                continue

        if not fetched:
            print(f"     ⚠️ All Nitter instances failed for @{account}")

    return jobs


def _looks_like_job(text: str) -> bool:
    text_lower = text.lower()
    return sum(1 for kw in JOB_KEYWORDS if kw in text_lower) >= 2


def _extract_salary(text: str) -> str:
    patterns = [
        r"[₦\$N]\s?[\d,]+[k]?",
        r"\d+[k]?\s?[-–]\s?\d+[k]?\s?(naira|usd|\$|₦)",
        r"salary[:\s]+[^\n]{3,40}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)[:60]
    return ""
