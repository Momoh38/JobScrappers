"""
scrapers/weworkremotely.py — Scrapes WeWorkRemotely via RSS feed
"""

import requests
import xml.etree.ElementTree as ET
import hashlib

WWR_FEEDS = [
    ("Programming", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
    ("Design",      "https://weworkremotely.com/categories/remote-design-jobs.rss"),
    ("Marketing",   "https://weworkremotely.com/categories/remote-marketing-jobs.rss"),
    ("Finance",     "https://weworkremotely.com/categories/remote-finance-legal-jobs.rss"),
    ("All Others",  "https://weworkremotely.com/categories/remote-jobs.rss"),
]

def scrape_weworkremotely() -> list:
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)"}

    for category, feed_url in WWR_FEEDS:
        try:
            response = requests.get(feed_url, headers=headers, timeout=15)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is None:
                continue

            for item in channel.findall("item"):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                region_el = item.find("{https://weworkremotely.com}region")

                title = title_el.text if title_el is not None else ""
                link = link_el.text if link_el is not None else ""
                desc = desc_el.text if desc_el is not None else ""
                region = region_el.text if region_el is not None else "Worldwide"

                # Parse "Company: Role" format in title
                company, role = "", title
                if ": " in title:
                    parts = title.split(": ", 1)
                    company, role = parts[0], parts[1]

                # Clean HTML from description
                desc = _strip_html(desc)

                job_id = hashlib.md5(link.encode()).hexdigest()

                jobs.append({
                    "id": f"wwr_{job_id}",
                    "title": role.strip(),
                    "company": company.strip(),
                    "location": region or "Remote",
                    "salary": "",
                    "description": desc[:500],
                    "tags": category,
                    "url": link,
                    "source": "WeWorkRemotely",
                })

        except Exception as e:
            print(f"     ⚠️ WWR feed {category} failed: {e}")

    return jobs


def _strip_html(text: str) -> str:
    import re
    clean = re.sub(r"<[^>]+>", " ", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean
