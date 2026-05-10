"""
scrapers/myjobmag.py — Scrapes MyJobMag Nigeria (fixed URL)
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_myjobmag() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    urls = [
        "https://www.myjobmag.com/jobs",
        "https://www.myjobmag.com/find-a-job",
        "https://www.myjobmag.com/latest-jobs",
        "https://www.myjobmag.com/",
    ]

    for base_url in urls:
        try:
            response = requests.get(base_url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            cards = (
                soup.select("div.job-list-item") or
                soup.select("li.job-item") or
                soup.select("article.job") or
                soup.select("div[class*='job-item']") or
                soup.select("div[class*='job_listing']") or
                soup.find_all("li", class_=lambda c: c and "job" in str(c).lower())
            )

            if not cards:
                continue

            for card in cards:
                try:
                    title_el = card.find(["h2", "h3", "a"])
                    title = title_el.get_text(strip=True) if title_el else ""
                    company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
                    company = company_el.get_text(strip=True) if company_el else ""
                    location_el = card.find(class_=lambda c: c and "location" in str(c).lower())
                    location = location_el.get_text(strip=True) if location_el else "Nigeria"
                    link_el = card.find("a", href=True)
                    link = link_el["href"] if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://www.myjobmag.com{link}"
                    if not title or len(title) < 3:
                        continue
                    job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()
                    jobs.append({
                        "id": f"myjobmag_{job_id}",
                        "title": title,
                        "company": company,
                        "location": location or "Nigeria",
                        "salary": "",
                        "description": "",
                        "tags": "",
                        "url": link,
                        "source": "MyJobMag",
                    })
                except Exception:
                    continue

            if jobs:
                break

        except Exception as e:
            print(f"     ⚠️ MyJobMag {base_url} failed: {e}")

    return jobs
