"""
scrapers/weworkremotely.py — WeWorkRemotely with Nigeria-friendly filtering
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
    ("Copywriting",       "https://weworkremotely.com/categories/remote-writing-jobs.rss"),
    ("HR & Recruiting",   "https://weworkremotely.com/categories/remote-hr-jobs.rss"),
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

                # Check Nigeria-friendliness
                if not is_nigeria_friendly_wwr(desc, region, role):
                    continue

                if not role or len(role) < 3:
                    continue

                job_id = hashlib.md5(f"{link}{role}".encode()).hexdigest()
                jobs.append({
                    "id":          f"wwr_{job_id}",
                    "title":       role.strip(),
                    "company":     company.strip(),
                    "location":    region or "Remote (Worldwide)",
                    "salary":      extract_salary_wwr(desc),
                    "description": desc[:500],
                    "tags":        f"{category}, Remote, Worldwide",
                    "url":         link,
                    "source":      "WeWorkRemotely",
                    "suitable_for_nigeria": "Yes" if "worldwide" in region.lower() or not region else "Check hours",
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

def is_nigeria_friendly_wwr(description, region, title):
    """Filter for Nigeria-friendly remote jobs"""
    text = (description + " " + title).lower()
    region_lower = region.lower()
    
    # Exclude clearly non-friendly
    exclude = ["us only", "usa only", "uk only", "europe only", "must be us citizen"]
    for word in exclude:
        if word in text or word in region_lower:
            return False
    
    # Include worldwide or any remote
    include = ["worldwide", "global", "anywhere", "remote", "any location", "all countries"]
    for word in include:
        if word in text or word in region_lower:
            return True
    
    # Default to include remote jobs
    return "remote" in text

def extract_salary_wwr(description):
    """Try to extract salary from description"""
    patterns = [
        r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*-\s*\$(\d+(?:,\d{3})*(?:\.\d+)?)',
        r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*to\s*\$(\d+(?:,\d{3})*(?:\.\d+)?)',
        r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*\+\s*',
        r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*USD',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            if len(match.groups()) >= 2:
                return f"${match.group(1)}-${match.group(2)} USD"
            elif match.group(1):
                return f"${match.group(1)}+ USD"
    return "Check listing"
