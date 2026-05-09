"""
scrapers/arbeitnow.py — Scrapes Arbeitnow free jobs API


import requests

def scrape_arbeitnow() -> list:
    jobs = []
    page = 1

    while page <= 3:  # Max 3 pages per run
        url = f"https://www.arbeitnow.com/api/job-board-api?page={page}"
        headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("data", [])
        if not items:
            break

        for j in items:
            location = j.get("location", "")
            remote = j.get("remote", False)

            # Only include remote or Nigeria
            if not remote and "nigeria" not in location.lower():
                continue

            jobs.append({
                "id": f"arbeitnow_{j.get('slug','')}",
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "location": "Remote" if remote else location,
                "salary": "",
                "description": j.get("description", "")[:500],
                "tags": ", ".join(j.get("tags", [])),
                "url": j.get("url", ""),
                "source": "Arbeitnow",
            })

        page += 1

    return jobs
"""
