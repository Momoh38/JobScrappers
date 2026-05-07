"""
scrapers/startupjobs.py — Scrapes startup.jobs (remote friendly)
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_startupjobs() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for page in range(1, 3):
        try:
            url = f"https://startup.jobs/?remote=true&page={page}"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            cards = (
                soup.select("div.job") or
                soup.select("article") or
                soup.select("li[class*='job']")
            )

            for card in cards:
                try:
                    title_el = card.find(["h2", "h3", "a"])
                    title = title_el.get_text(strip=True) if title_el else ""

                    company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
                    company = company_el.get_text(strip=True) if company_el else ""

                    link_el = card.find("a", href=True)
                    link = link_el["href"] if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://startup.jobs{link}"

                    if not title or len(title) < 3:
                        continue

                    job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                    jobs.append({
                        "id": f"startupjobs_{job_id}",
                        "title": title,
                        "company": company,
                        "location": "Remote (Worldwide)",
                        "salary": "",
                        "description": "",
                        "tags": "Startup",
                        "url": link,
                        "source": "StartupJobs",
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"     ⚠️ StartupJobs page {page} failed: {e}")

    return jobs
