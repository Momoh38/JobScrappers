"""
scrapers/themuse.py — Scrapes The Muse public jobs API
"""

import requests

def scrape_themuse() -> list:
    jobs = []
    page = 1

    while page <= 3:
        url = f"https://www.themuse.com/api/public/jobs?page={page}&descending=true"
        headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("results", [])
        if not items:
            break

        for j in items:
            locations = j.get("locations", [])
            location_names = [loc.get("name", "") for loc in locations]
            location_str = ", ".join(location_names) if location_names else "Remote"

            # Include if Flexible/Remote or Nigeria
            is_remote = any("flex" in l.lower() or "remote" in l.lower() for l in location_names)
            is_nigeria = any("nigeria" in l.lower() for l in location_names)

            if not is_remote and not is_nigeria and location_names:
                continue

            levels = j.get("levels", [])
            experience = ", ".join([lv.get("name", "") for lv in levels])

            jobs.append({
                "id": f"themuse_{j.get('id','')}",
                "title": j.get("name", ""),
                "company": j.get("company", {}).get("name", ""),
                "location": location_str,
                "salary": "",
                "description": j.get("contents", "")[:500],
                "tags": ", ".join([cat.get("name","") for cat in j.get("categories", [])]),
                "experience": experience,
                "url": j.get("refs", {}).get("landing_page", ""),
                "source": "The Muse",
            })

        page += 1

    return jobs
