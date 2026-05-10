"""
scrapers/jobicy.py — Jobicy remote jobs (free open API, no auth needed)
Fixed: removed invalid 'geo=worldwide' parameter, use correct industry names
"""

import requests
import hashlib


def scrape_jobicy() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    # Query by relevant industries using correct Jobicy industry names
    industries = [
        "supporting",       # customer support
        "dev",              # development
        "marketing",        # marketing
        "design-multimedia",# design
        "copywriting",      # writing/content
        "data-science",     # data
        "admin-support",    # admin/virtual assistant
        "accounting-finance",# finance
        "hr",               # HR
        "technical-support",# tech support
    ]

    seen_ids = set()

    for industry in industries:
        try:
            url = f"https://jobicy.com/api/v2/remote-jobs?count=20&industry={industry}"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get("jobs", [])

            for j in items:
                job_id = str(j.get("id", ""))
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                salary = ""
                sal_min = j.get("annualSalaryMin", "")
                sal_max = j.get("annualSalaryMax", "")
                currency = j.get("salaryCurrency", "USD")
                if sal_min and sal_max:
                    salary = f"{currency} {int(sal_min):,}–{int(sal_max):,}/yr"

                jobs.append({
                    "id":          f"jobicy_{job_id}",
                    "title":       j.get("jobTitle", ""),
                    "company":     j.get("companyName", ""),
                    "location":    j.get("jobGeo", "Remote (Worldwide)"),
                    "salary":      salary,
                    "description": j.get("jobExcerpt", "")[:400],
                    "tags":        f"{j.get('jobType','')}",
                    "experience":  j.get("jobLevel", ""),
                    "date_posted": j.get("pubDate", "")[:10],
                    "url":         j.get("url", ""),
                    "source":      "Jobicy",
                })

        except Exception as e:
            print(f"     ⚠️ Jobicy {industry} failed: {e}")

    return jobs
