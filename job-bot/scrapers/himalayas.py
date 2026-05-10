"""
scrapers/himalayas.py — Himalayas.app remote jobs (free open API, worldwide)
One of the best free remote job APIs available — no key, no rate limits.
"""

import requests
import hashlib


def scrape_himalayas() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    try:
        url = "https://himalayas.app/jobs/api?limit=50"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("jobs", [])

        for j in items:
            location = j.get("locationRestrictions", [])
            if isinstance(location, list):
                location = ", ".join(location) if location else "Remote (Worldwide)"

            skills = j.get("skills", [])
            tags = ", ".join([s.get("name", "") for s in skills[:5]]) if skills else ""

            salary_min = j.get("salaryMin", "")
            salary_max = j.get("salaryMax", "")
            salary = f"${salary_min:,}–${salary_max:,}" if salary_min and salary_max else ""

            job_id = hashlib.md5(str(j.get("id", j.get("slug", ""))).encode()).hexdigest()

            jobs.append({
                "id":          f"himalayas_{job_id}",
                "title":       j.get("title", ""),
                "company":     j.get("companyName", ""),
                "location":    location,
                "salary":      salary,
                "description": j.get("description", "")[:400],
                "tags":        tags,
                "experience":  j.get("seniorityLevel", ""),
                "url":         j.get("applicationLink", "") or f"https://himalayas.app/jobs/{j.get('slug','')}",
                "source":      "Himalayas",
            })

    except Exception as e:
        print(f"     ⚠️ Himalayas failed: {e}")

    return jobs
