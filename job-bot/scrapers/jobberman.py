"""
scrapers/jobberman.py — Scrapes Jobberman Nigeria job listings
"""

import requests
import hashlib
from bs4 import BeautifulSoup

BASE_URL = "https://www.jobberman.com/jobs"

def scrape_jobberman() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    for page in range(1, 4):  # Pages 1–3
        try:
            url = f"{BASE_URL}?page={page}"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            listings = soup.select("article.p-4") or soup.select("div.job-card") or soup.select("[data-testid='job-card']")

            if not listings:
                # Try generic approach
                listings = soup.find_all("article") or soup.find_all("div", class_=lambda c: c and "job" in c.lower())

            for item in listings:
                try:
                    title_el = item.find(["h2", "h3", "a"], class_=lambda c: c and ("title" in str(c).lower() or "job" in str(c).lower()))
                    title = title_el.get_text(strip=True) if title_el else ""

                    company_el = item.find(class_=lambda c: c and "company" in str(c).lower())
                    company = company_el.get_text(strip=True) if company_el else ""

                    location_el = item.find(class_=lambda c: c and "location" in str(c).lower())
                    location = location_el.get_text(strip=True) if location_el else "Nigeria"

                    link_el = item.find("a", href=True)
                    link = link_el["href"] if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://www.jobberman.com{link}"

                    if not title:
                        continue

                    job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                    jobs.append({
                        "id": f"jobberman_{job_id}",
                        "title": title,
                        "company": company,
                        "location": location or "Nigeria",
                        "salary": "",
                        "description": "",
                        "tags": "",
                        "url": link,
                        "source": "Jobberman",
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"     ⚠️ Jobberman page {page} failed: {e}")

    return jobs
