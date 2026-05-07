"""
scrapers/remoteok.py — Scrapes RemoteOK via their public API
"""

import requests

def scrape_remoteok() -> list:
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()
    # First item is a legal notice, skip it
    jobs_raw = [item for item in data if isinstance(item, dict) and item.get("id")]

    jobs = []
    for j in jobs_raw:
        location = j.get("location", "Remote")
        # Include remote jobs or Nigeria-specific
        if location and location.lower() not in ["", "worldwide", "remote", "anywhere"]:
            if "nigeria" not in location.lower() and "remote" not in location.lower():
                continue

        jobs.append({
            "id": f"remoteok_{j.get('id')}",
            "title": j.get("position", ""),
            "company": j.get("company", ""),
            "location": location or "Remote",
            "salary": _format_salary(j.get("salary_min"), j.get("salary_max")),
            "description": j.get("description", ""),
            "tags": ", ".join(j.get("tags", [])),
            "url": j.get("url", ""),
            "source": "RemoteOK",
        })

    return jobs


def _format_salary(min_s, max_s):
    if min_s and max_s:
        return f"${int(min_s):,} – ${int(max_s):,}/yr"
    elif min_s:
        return f"From ${int(min_s):,}/yr"
    return ""
