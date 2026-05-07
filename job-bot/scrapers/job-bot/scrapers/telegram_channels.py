"""
scrapers/telegram_channels.py — Reads public Telegram job channels via t.me preview
These are public channels, no login required — we scrape the web preview.
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup

# Public Telegram job channels to monitor
TELEGRAM_JOB_CHANNELS = [
    "nigeriajobs",
    "jobsinnigeria",
    "remotejobsng",
    "naijajobsalert",
    "jobvacancyinnigeria",
    "nigeriajobalerts",
    "remote_jobs_ng",
    "africajobsalert",
]

def scrape_telegram_channels() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    for channel in TELEGRAM_JOB_CHANNELS:
        try:
            url = f"https://t.me/s/{channel}"
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.select("div.tgme_widget_message_text")

            for msg in messages[:20]:  # Last 20 messages per channel
                text = msg.get_text(separator="\n", strip=True)

                # Only process if it looks like a job post
                if not _looks_like_job(text):
                    continue

                # Try to extract title from first line
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                title = lines[0][:100] if lines else "Job Opening"
                description = "\n".join(lines[1:4]) if len(lines) > 1 else ""

                # Try to find a link inside the message
                link_el = msg.find("a", href=True)
                link = link_el["href"] if link_el else f"https://t.me/s/{channel}"

                job_id = hashlib.md5(f"{channel}{text[:100]}".encode()).hexdigest()

                jobs.append({
                    "id": f"tg_{job_id}",
                    "title": title,
                    "company": f"@{channel}",
                    "location": "Nigeria / Remote",
                    "salary": _extract_salary(text),
                    "description": description[:300],
                    "tags": "Telegram",
                    "url": link,
                    "source": f"Telegram @{channel}",
                })

        except Exception as e:
            print(f"     ⚠️ Telegram @{channel} failed: {e}")

    return jobs


JOB_KEYWORDS = [
    "hiring", "vacancy", "job", "role", "position", "opening",
    "apply", "opportunity", "recruit", "needed", "wanted",
    "salary", "remote", "full-time", "part-time", "freelance",
]

def _looks_like_job(text: str) -> bool:
    text_lower = text.lower()
    return sum(1 for kw in JOB_KEYWORDS if kw in text_lower) >= 2


def _extract_salary(text: str) -> str:
    # Look for patterns like ₦50,000 or $500 or N100k
    patterns = [
        r"[₦\$N]\s?[\d,]+[k]?",
        r"\d+[k]?\s?-\s?\d+[k]?\s?(naira|usd|\$|₦)",
        r"salary[:\s]+[^\n]+",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)[:50]
    return ""
