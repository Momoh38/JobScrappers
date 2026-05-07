"""
scrapers/indeed_ng.py — Scrapes Indeed Nigeria
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_indeed_ng() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    queries = ["remote", "work from home", "online"]

    for query in queries:
        for start in [0, 10, 20]:
            try:
                url = f"https://ng.indeed.com/jobs?q={query}&l=Nigeria&start={start}&lang=en"
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.select("div.job_seen_beacon") or soup.select("div.tapItem") or soup.select("div[data-testid='slider_item']")

                for card in cards:
                    try:
                        title_el = card.select_one("h2.jobTitle span, h2 a span")
                        title = title_el.get_text(strip=True) if title_el else ""

                        company_el = card.select_one("span.companyName, [data-testid='company-name']")
                        company = company_el.get_text(strip=True) if company_el else ""

                        location_el = card.select_one("div.companyLocation, [data-testid='text-location']")
                        location = location_el.get_text(strip=True) if location_el else "Nigeria"

                        salary_el = card.select_one("div.salary-snippet, [data-testid='attribute_snippet_testid']")
                        salary = salary_el.get_text(strip=True) if salary_el else ""

                        link_el = card.select_one("h2 a[href]")
                        link = ""
                        if link_el:
                            href = link_el.get("href", "")
                            link = f"https://ng.indeed.com{href}" if href.startswith("/") else href

                        if not title:
                            continue

                        job_id = hashlib.md5(f"{title}{company}".encode()).hexdigest()

                        jobs.append({
                            "id": f"indeed_ng_{job_id}",
                            "title": title,
                            "company": company,
                            "location": location or "Nigeria",
                            "salary": salary,
                            "description": "",
                            "tags": "",
                            "url": link,
                            "source": "Indeed Nigeria",
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"     ⚠️ Indeed NG failed (query={query}, start={start}): {e}")

    # Deduplicate
    seen = set()
    unique = []
    for j in jobs:
        if j["id"] not in seen:
            seen.add(j["id"])
            unique.append(j)
    return unique
