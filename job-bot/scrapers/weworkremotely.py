"""
scrapers/weworkremotely.py — WeWorkRemotely using correct RSS feed URLs
All URLs verified from weworkremotely.com/remote-job-rss-feed
"""

import requests
import xml.etree.ElementTree as ET
import hashlib
import re

WWR_FEEDS = [
    ("Programming",       "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
    ("Customer Support",  "https://weworkremotely.com/categories/remote-customer-support-jobs.rss"),
    ("Design",            "https://weworkremotely.com/categories/remote-design-jobs.rss"),
    ("Sales & Marketing", "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss"),
    ("Management",        "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss"),
    ("DevOps",            "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"),
    ("All Remote",        "https://weworkremotely.com/remote-jobs.rss"),
]


def scrape_weworkremotely() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    }

    for category, feed_url in WWR_FEEDS:
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if not channel:
                continue

            for item in channel.findall("item"):
                title_el  = item.find("title")
                link_el   = item.find("link")
                desc_el   = item.find("description")
                region_el = item.find("{https://weworkremotely.com}region")

                title  = title_el.text  if title_el  is not None else ""
                link   = link_el.text   if link_el   is not None else ""
                desc   = desc_el.text   if desc_el   is not None else ""
                region = region_el.text if region_el is not None else "Worldwide"

                # WWR title format: "Company: Role"
                company, role = "", title
                if ": " in title:
                    parts = title.split(": ", 1)
                    company, role = parts[0], parts[1]

                desc = re.sub(r"<[^>]+>", " ", desc or "")
                desc = re.sub(r"\s+", " ", desc).strip()

                if not role or len(role) < 3:
                    continue

                job_id = hashlib.md5(f"{link}{role}".encode()).hexdigest()
                jobs.append({
                    "id":          f"wwr_{job_id}",
                    "title":       role.strip(),
                    "company":     company.strip(),
                    "location":    region or "Remote (Worldwide)",
                    "salary":      "",
                    "description": desc[:400],
                    "tags":        category,
                    "url":         link,
                    "source":      "WeWorkRemotely",
                })

        except Exception as e:
            print(f"     ⚠️ WWR {category} failed: {e}")

    # Deduplicate
    seen, unique = set(), []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)
    return unique
