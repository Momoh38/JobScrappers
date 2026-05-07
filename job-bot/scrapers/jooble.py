"""
scrapers/jooble.py — Scrapes Jooble Nigeria via their public API
"""

import requests
import hashlib


def scrape_jooble() -> list:
    jobs = []
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)",
    }

    searches = ["remote work", "work from home", "online job", "software", "customer service", "data entry"]

    for keyword in searches:
        try:
            url = "https://jooble.org/api/"
            payload = {
                "keywords": keyword,
                "location": "Nigeria",
                "page": "1",
            }
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get("jobs", [])

            for j in items[:10]:
                title = j.get("title", "")
                company = j.get("company", "")
                location = j.get("location", "Nigeria")
                salary = j.get("salary", "")
                snippet = j.get("snippet", "")
                link = j.get("link", "")

                if not title:
                    continue

                job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                jobs.append({
                    "id": f"jooble_{job_id}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "salary": salary,
                    "description": snippet[:400],
                    "tags": "",
                    "url": link,
                    "source": "Jooble Nigeria",
                })

        except Exception as e:
            print(f"     ⚠️ Jooble '{keyword}' failed: {e}")

    # Deduplicate
    seen = set()
    unique = []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)
    return unique
