"""
scrapers/remotive.py — Scrapes Remotive API (remote jobs, worldwide open)
"""

import requests
import hashlib


def scrape_remotive() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    categories = [
        "software-dev", "customer-support", "design", "marketing",
        "writing", "data", "finance", "product", "hr", "qa",
    ]

    for cat in categories:
        try:
            url = f"https://remotive.com/api/remote-jobs?category={cat}&limit=20"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get("jobs", [])

            for j in items:
                candidate_required = j.get("candidate_required_location", "Worldwide")

                # Skip if explicitly restricted to non-Nigeria regions
                restricted = ["us only", "usa only", "north america only",
                              "uk only", "eu only", "europe only", "australia only"]
                if any(r in candidate_required.lower() for r in restricted):
                    continue

                job_id = hashlib.md5(str(j.get("id", "") or j.get("url", "")).encode()).hexdigest()

                jobs.append({
                    "id": f"remotive_{job_id}",
                    "title": j.get("title", ""),
                    "company": j.get("company_name", ""),
                    "location": candidate_required or "Remote (Worldwide)",
                    "salary": j.get("salary", ""),
                    "description": j.get("description", "")[:500],
                    "tags": ", ".join(j.get("tags", [])),
                    "url": j.get("url", ""),
                    "source": "Remotive",
                })

        except Exception as e:
            print(f"     ⚠️ Remotive {cat} failed: {e}")

    # Deduplicate
    seen = set()
    unique = []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)
    return unique
