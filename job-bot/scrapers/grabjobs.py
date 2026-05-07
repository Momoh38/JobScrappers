"""
scrapers/grabjobs.py — Scrapes GrabJobs Nigeria
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_grabjobs() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    for page in range(1, 4):
        try:
            url = f"https://grabjobs.co/nigeria/jobs?page={page}"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            cards = (
                soup.select("div.job-card") or
                soup.select("article.job") or
                soup.select("div[class*='job-item']") or
                soup.select("li[class*='job']")
            )

            for card in cards:
                try:
                    title_el = card.find(["h2", "h3", "h4"])
                    title = title_el.get_text(strip=True) if title_el else ""

                    company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
                    company = company_el.get_text(strip=True) if company_el else ""

                    location_el = card.find(class_=lambda c: c and "location" in str(c).lower())
                    location = location_el.get_text(strip=True) if location_el else "Nigeria"

                    link_el = card.find("a", href=True)
                    link = link_el["href"] if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://grabjobs.co{link}"

                    if not title or len(title) < 3:
                        continue

                    job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                    jobs.append({
                        "id": f"grabjobs_{job_id}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": "",
                        "description": "",
                        "tags": "",
                        "url": link,
                        "source": "GrabJobs Nigeria",
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"     ⚠️ GrabJobs page {page} failed: {e}")

    return jobs
