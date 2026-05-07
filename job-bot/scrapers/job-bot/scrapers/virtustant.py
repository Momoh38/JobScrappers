"""
scrapers/virtustant.py — Scrapes Virtustant (hires globally including Africa/Nigeria)
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_virtustant() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        url = "https://jobs.virtustant.com/"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        cards = (
            soup.select("div.job-card") or
            soup.select("article") or
            soup.select("li.job") or
            soup.select("div[class*='job']")
        )

        for card in cards:
            try:
                title_el = card.find(["h2", "h3", "h4", "a"])
                title = title_el.get_text(strip=True) if title_el else ""

                company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
                company = company_el.get_text(strip=True) if company_el else "Virtustant"

                salary_el = card.find(class_=lambda c: c and "salary" in str(c).lower())
                salary = salary_el.get_text(strip=True) if salary_el else ""

                link_el = card.find("a", href=True)
                link = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = f"https://jobs.virtustant.com{link}"

                if not title or len(title) < 3:
                    continue

                job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                jobs.append({
                    "id": f"virtustant_{job_id}",
                    "title": title,
                    "company": company,
                    "location": "Remote (Worldwide)",
                    "salary": salary,
                    "description": "",
                    "tags": "Remote, Global",
                    "url": link,
                    "source": "Virtustant",
                })
            except Exception:
                continue

    except Exception as e:
        print(f"     ⚠️ Virtustant failed: {e}")

    return jobs
