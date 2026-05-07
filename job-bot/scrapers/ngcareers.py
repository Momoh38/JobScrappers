"""
scrapers/ngcareers.py — Scrapes NGCareers Nigeria
"""

import requests
import hashlib
from bs4 import BeautifulSoup

def scrape_ngcareers() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    for page in range(1, 4):
        try:
            url = f"https://ngcareers.com/jobs?page={page}"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            listings = (
                soup.select("div.job_listing") or
                soup.select("ul.job_listings li") or
                soup.select("article.job_listing") or
                soup.find_all("li", class_=lambda c: c and "job" in str(c).lower())
            )

            for item in listings:
                try:
                    title_el = item.find(["h2", "h3"])
                    title = title_el.get_text(strip=True) if title_el else ""

                    company_el = item.find(class_=lambda c: c and "company" in str(c).lower())
                    company = company_el.get_text(strip=True) if company_el else ""

                    location_el = item.find(class_=lambda c: c and "location" in str(c).lower())
                    location = location_el.get_text(strip=True) if location_el else "Nigeria"

                    link_el = item.find("a", href=True)
                    link = link_el["href"] if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://ngcareers.com{link}"

                    if not title or len(title) < 3:
                        continue

                    job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                    jobs.append({
                        "id": f"ngcareers_{job_id}",
                        "title": title,
                        "company": company,
                        "location": location,
                        "salary": "",
                        "description": "",
                        "tags": "",
                        "url": link,
                        "source": "NGCareers",
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"     ⚠️ NGCareers page {page} failed: {e}")

    return jobs
