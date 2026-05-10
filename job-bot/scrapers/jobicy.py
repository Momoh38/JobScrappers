"""
scrapers/jobicy.py — Jobicy remote jobs API (free, no auth, worldwide open)
Good replacement for DailyRemote and GrabJobs which are now blocking scrapers.
"""

import requests
import hashlib


def scrape_jobicy() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    try:
        # Jobicy has a completely open JSON API — no key needed
        url = "https://jobicy.com/api/v2/remote-jobs?count=50&geo=worldwide"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        data = response.json()
        items = data.get("jobs", [])

        for j in items:
            location = j.get("jobGeo", "Remote (Worldwide)")
            tags_list = j.get("jobType", [])
            if isinstance(tags_list, str):
                tags_list = [tags_list]
            industry = j.get("jobIndustry", [])
            if isinstance(industry, str):
                industry = [industry]
            all_tags = tags_list + industry
            tags = ", ".join(all_tags[:5])

            job_id = hashlib.md5(str(j.get("id", j.get("jobSlug", ""))).encode()).hexdigest()

            jobs.append({
                "id":          f"jobicy_{job_id}",
                "title":       j.get("jobTitle", ""),
                "company":     j.get("companyName", ""),
                "location":    location,
                "salary":      j.get("annualSalaryMin", "") and f"${j.get('annualSalaryMin')}–${j.get('annualSalaryMax')}" or "",
                "description": j.get("jobDescription", "")[:400],
                "tags":        tags,
                "url":         j.get("url", ""),
                "source":      "Jobicy",
            })

    except Exception as e:
        print(f"     ⚠️ Jobicy failed: {e}")

    return jobs
