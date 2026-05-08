"""
scrapers/linkedin_rss.py — LinkedIn jobs via RSS (no login needed)
Targets specific searches relevant to Nigeria/remote English speakers.
"""

import requests
import hashlib
import xml.etree.ElementTree as ET
import re


LINKEDIN_RSS_SEARCHES = [
    "remote+customer+service",
    "remote+virtual+assistant",
    "remote+data+entry",
    "remote+content+writer",
    "remote+software+engineer",
    "nigeria+remote",
    "africa+remote+jobs",
]


def scrape_linkedin_rss() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    }

    for search in LINKEDIN_RSS_SEARCHES:
        try:
            url = (
                f"https://www.linkedin.com/jobs/search/?keywords={search}"
                f"&location=Worldwide&f_WT=2&f_TPR=r86400"
                f"&position=1&pageNum=0"
            )
            # LinkedIn RSS feed URL format
            rss_url = (
                f"https://www.linkedin.com/jobs/search.rss?"
                f"keywords={search}&location=Nigeria,Worldwide&f_WT=2"
            )

            response = requests.get(rss_url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue

            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if not channel:
                continue

            for item in channel.findall("item"):
                title_el   = item.find("title")
                link_el    = item.find("link")
                desc_el    = item.find("description")
                pubdate_el = item.find("pubDate")

                title   = title_el.text if title_el is not None else ""
                link    = link_el.text  if link_el  is not None else ""
                desc    = desc_el.text  if desc_el  is not None else ""
                pubdate = pubdate_el.text if pubdate_el is not None else ""

                # LinkedIn title format: "Job Title at Company"
                company = ""
                if " at " in title:
                    parts   = title.rsplit(" at ", 1)
                    title   = parts[0].strip()
                    company = parts[1].strip()

                desc = re.sub(r"<[^>]+>", " ", desc or "")
                desc = re.sub(r"\s+", " ", desc).strip()

                if not title:
                    continue

                job_id = hashlib.md5(f"{title}{company}{link}".encode()).hexdigest()

                jobs.append({
                    "id":          f"linkedin_{job_id}",
                    "title":       title,
                    "company":     company,
                    "location":    "Remote / Worldwide",
                    "salary":      "",
                    "description": desc[:400],
                    "tags":        "LinkedIn",
                    "date_posted": pubdate,
                    "url":         link,
                    "source":      "LinkedIn",
                })

        except Exception as e:
            print(f"     ⚠️ LinkedIn RSS ({search}) failed: {e}")

    # Deduplicate
    seen, unique = set(), []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)
    return unique
