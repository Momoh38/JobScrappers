"""
scrapers/telegram_channels.py — Reads public Telegram job channels via t.me preview
All channels verified as active Nigerian/remote job channels.
"""

import requests
import hashlib
import re
from bs4 import BeautifulSoup

# Verified active Nigerian & remote job Telegram channels
TELEGRAM_JOB_CHANNELS = [
    # Nigerian job channels (verified active)
    "jbtoday",                        # Jobstoday - Nigerian + international remote jobs
    "jobnownigeria",                   # Jobnow Nigeria - verified daily vacancies
    "jobnetworkng",                    # Latest Jobs in Nigeria
    "JobsinNigeriadaily",              # Jobs in Nigeria Daily
    "jobsnigeria001rekrutconsulting",  # Job Vacancies Nigeria
    "illtip",                          # Job vacancies in nigeria  
    "techjobsworld",           # Lagos tech jobs
    "EllfexNaijaJobber"        # General Nigeria jobs
    "naijajobsportal",           
    
    #"WorkaNigeria",                    # Worka Nigeria - Web2 & Web3 jobs
    #"careermattersng",                  Careermatters NG - active recruitment platform (NOT ACTIVE)
    # Remote/worldwide job channels
    "remotejobss",                     # Remote Jobs (English & Worldwide)
]

JOB_KEYWORDS = [
    "hiring", "vacancy", "job", "role", "position", "opening",
    "apply", "opportunity", "recruit", "needed", "wanted",
    "salary", "remote", "full-time", "part-time", "freelance",
    "engineer", "developer", "manager", "analyst", "designer",
    "officer", "executive", "coordinator", "specialist", "intern",
]


def scrape_telegram_channels() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for channel in TELEGRAM_JOB_CHANNELS:
        try:
            url = f"https://t.me/s/{channel}"
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"     ⚠️ Telegram @{channel} returned {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            messages = soup.select("div.tgme_widget_message_text")

            if not messages:
                continue

            for msg in messages[:25]:
                text = msg.get_text(separator="\n", strip=True)

                if not text or len(text) < 30:
                    continue

                if not _looks_like_job(text):
                    continue

                lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 3]
                title = lines[0][:120] if lines else "Job Opening"
                description = " | ".join(lines[1:4]) if len(lines) > 1 else ""

                link_el = msg.find("a", href=True)
                link = link_el["href"] if link_el else f"https://t.me/s/{channel}"

                if link and "t.me" in link and channel in link:
                    link = f"https://t.me/s/{channel}"

                job_id = hashlib.md5(f"{channel}{text[:120]}".encode()).hexdigest()

                jobs.append({
                    "id": f"tg_{job_id}",
                    "title": title,
                    "company": f"via @{channel}",
                    "location": _extract_location(text),
                    "salary": _extract_salary(text),
                    "description": description[:300],
                    "tags": "Telegram",
                    "url": link,
                    "source": f"Telegram @{channel}",
                })

        except Exception as e:
            print(f"     ⚠️ Telegram @{channel} failed: {e}")

    return jobs


def _looks_like_job(text: str) -> bool:
    text_lower = text.lower()
    return sum(1 for kw in JOB_KEYWORDS if kw in text_lower) >= 2


def _extract_salary(text: str) -> str:
    patterns = [
        r"[₦\$]\s?[\d,]+[k]?(?:\s?[-–]\s?[₦\$]?\s?[\d,]+[k]?)?",
        r"\d+[k]\s?[-–]\s?\d+[k]",
        r"salary[:\s]+[^\n]{3,50}",
        r"pay[:\s]+[^\n]{3,50}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()[:60]
    return ""


def _extract_location(text: str) -> str:
    patterns = [
        r"location[:\s]+([^\n]{3,50})",
        r"based in[:\s]+([^\n]{3,50})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:50]

    cities = ["Remote", "Nigeria" "Abia", "Adamawa", "Akwa Ibom",
              "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno",
              "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti",
              "Enugu", "Gombe", "Imo", "Jigawa", "Kaduna", "Kano",
              "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa",
              "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers",
              "Sokoto", "Taraba", "Yobe", "Zamfara", "Abuja", "Fedral Capital Territory"]
    for city in cities:
        if city.lower() in text.lower():
            return city

    return "Nigeria / Remote"
