"""
scrapers/workingnomads.py — Scrapes WorkingNomads remote jobs
"""

import requests
import hashlib


def scrape_workingnomads() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)",
        "Accept": "application/json",
    }

    categories = ["back-end", "front-end", "devops", "design", "marketing",
                  "customer-support", "writing", "finance", "management", "sales"]

    for cat in categories:
        try:
            url = f"https://www.workingnomads.com/api/exposed_jobs/?category={cat}"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, list):
                data = data.get("results", [])

            for j in data[:10]:  # Top 10 per category
                location = j.get("location", "Remote")
                tags = ", ".join(j.get("tags", []))

                job_id = hashlib.md5(f"{j.get('title','')}{j.get('company_name','')}".encode()).hexdigest()

                jobs.append({
                    "id": f"workingnomads_{job_id}",
                    "title": j.get("title", ""),
                    "company": j.get("company_name", ""),
                    "location": location or "Remote (Worldwide)",
                    "salary": "",
                    "description": j.get("description", "")[:500],
                    "tags": tags,
                    "url": j.get("url", ""),
                    "source": "WorkingNomads",
                })

        except Exception as e:
            print(f"     ⚠️ WorkingNomads {cat} failed: {e}")

    # Deduplicate
    seen = set()
    unique = []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)
    return unique
