"""
scrapers/oneforma.py — Scrapes OneForma (global remote tasks/jobs, open to Nigeria)
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_oneforma() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        url = "https://www.oneforma.com/jobs/"
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        cards = (
            soup.select("div.job-listing") or
            soup.select("article.job") or
            soup.select("div[class*='job']") or
            soup.select("li[class*='job']")
        )

        for card in cards:
            try:
                title_el = card.find(["h2", "h3", "h4", "a"])
                title = title_el.get_text(strip=True) if title_el else ""

                desc_el = card.find("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                link_el = card.find("a", href=True)
                link = link_el["href"] if link_el else "https://www.oneforma.com/jobs/"
                if link and not link.startswith("http"):
                    link = f"https://www.oneforma.com{link}"

                if not title or len(title) < 3:
                    continue

                job_id = hashlib.md5(f"{title}oneforma".encode()).hexdigest()

                jobs.append({
                    "id": f"oneforma_{job_id}",
                    "title": title,
                    "company": "OneForma",
                    "location": "Remote (Worldwide)",
                    "salary": "",
                    "description": description[:300],
                    "tags": "Freelance, Remote, Global",
                    "url": link,
                    "source": "OneForma",
                })
            except Exception:
                continue

    except Exception as e:
        print(f"     ⚠️ OneForma failed: {e}")

    return jobs
