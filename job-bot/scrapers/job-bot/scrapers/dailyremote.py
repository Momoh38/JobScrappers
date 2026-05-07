"""
scrapers/dailyremote.py — Scrapes DailyRemote (remote-friendly, worldwide)
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_dailyremote() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    categories = ["", "developer-jobs", "customer-support-jobs", "marketing-jobs", "design-jobs", "writing-jobs"]

    for cat in categories:
        try:
            url = f"https://dailyremote.com/{cat}" if cat else "https://dailyremote.com/remote-jobs"
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            cards = (
                soup.select("article.card") or
                soup.select("div.job-card") or
                soup.select("div[class*='job']")
            )

            for card in cards:
                try:
                    title_el = card.find(["h2", "h3", "h4", "a"])
                    title = title_el.get_text(strip=True) if title_el else ""

                    company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
                    company = company_el.get_text(strip=True) if company_el else ""

                    link_el = card.find("a", href=True)
                    link = link_el["href"] if link_el else ""
                    if link and not link.startswith("http"):
                        link = f"https://dailyremote.com{link}"

                    tags_el = card.find_all(class_=lambda c: c and "tag" in str(c).lower())
                    tags = ", ".join([t.get_text(strip=True) for t in tags_el[:5]])

                    if not title or len(title) < 3:
                        continue

                    job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                    jobs.append({
                        "id": f"dailyremote_{job_id}",
                        "title": title,
                        "company": company,
                        "location": "Remote (Worldwide)",
                        "salary": "",
                        "description": "",
                        "tags": tags,
                        "url": link,
                        "source": "DailyRemote",
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"     ⚠️ DailyRemote {cat} failed: {e}")

    # Deduplicate
    seen = set()
    unique = []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)
    return unique
