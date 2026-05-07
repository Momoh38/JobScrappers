"""
scrapers/braintrust.py — Scrapes Braintrust remote jobs (global talent network)
"""

import requests
import hashlib


def scrape_braintrust() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        url = "https://app.usebraintrust.com/api/jobs/?limit=50&offset=0&ordering=-created_at"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("results", []) if isinstance(data, dict) else data

        for j in items:
            location = j.get("location", "") or "Remote (Worldwide)"
            skills = j.get("skills", [])
            tags = ", ".join([s.get("name", "") for s in skills[:5]]) if skills else ""

            pay_min = j.get("hourly_rate_min") or j.get("annual_salary_min")
            pay_max = j.get("hourly_rate_max") or j.get("annual_salary_max")
            salary = ""
            if pay_min and pay_max:
                salary = f"${pay_min}–${pay_max}"
            elif pay_min:
                salary = f"From ${pay_min}"

            job_id = hashlib.md5(str(j.get("id", "") or f"{j.get('title','')}{j.get('client','')}").encode()).hexdigest()

            title = j.get("title", "") or j.get("name", "")
            company = j.get("client", {}).get("name", "") if isinstance(j.get("client"), dict) else str(j.get("client", ""))

            if not title:
                continue

            jobs.append({
                "id": f"braintrust_{job_id}",
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "description": j.get("description", "")[:500],
                "tags": tags,
                "url": f"https://app.usebraintrust.com/jobs/{j.get('id', '')}",
                "source": "Braintrust",
            })

    except Exception as e:
        print(f"     ⚠️ Braintrust failed: {e}")

    return jobs
