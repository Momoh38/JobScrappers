"""
scrapers/ngo_jobs.py — UN, NGO, and international organisation job boards.
These are halal, high-paying, and actively hire Nigerians remotely.
Sources: UN Jobs, ReliefWeb, Devex (free listings), UNHCR, UNICEF
"""

import requests
import hashlib
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re


def scrape_ngo_jobs() -> list:
    jobs = []
    jobs.extend(_scrape_reliefweb())
    jobs.extend(_scrape_unjobs())
    jobs.extend(_scrape_devex())
    return jobs


def _scrape_reliefweb() -> list:
    """ReliefWeb has a free public API — very reliable."""
    jobs = []
    try:
        url = "https://api.reliefweb.int/v1/jobs"
        payload = {
            "filter": {
                "operator": "AND",
                "conditions": [
                    {"field": "status", "value": "published"},
                ]
            },
            "fields": {
                "include": ["title", "body", "url", "date", "source", "country", "career_categories"]
            },
            "sort": ["date:desc"],
            "limit": 30,
        }
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        data  = response.json()
        items = data.get("data", [])

        for item in items:
            fields   = item.get("fields", {})
            title    = fields.get("title", "")
            desc     = fields.get("body", "")
            job_url  = fields.get("url", "")
            date_str = fields.get("date", {}).get("created", "")
            sources  = fields.get("source", [{}])
            org      = sources[0].get("name", "NGO") if sources else "NGO"
            countries = fields.get("country", [{}])
            location = countries[0].get("name", "Remote") if countries else "Remote"

            desc = re.sub(r"<[^>]+>", " ", desc or "")
            desc = re.sub(r"\s+", " ", desc).strip()

            if not title:
                continue

            job_id = hashlib.md5(f"reliefweb{item.get('id',title)}".encode()).hexdigest()
            jobs.append({
                "id":          f"reliefweb_{job_id}",
                "title":       title,
                "company":     org,
                "location":    location,
                "salary":      "",
                "description": desc[:400],
                "tags":        "NGO, International, ReliefWeb",
                "date_posted": date_str[:10] if date_str else "",
                "url":         job_url,
                "source":      "ReliefWeb",
            })
    except Exception as e:
        print(f"     ⚠️ ReliefWeb failed: {e}")
    return jobs


def _scrape_unjobs() -> list:
    """UN Jobs public listings."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        url = "https://unjobs.org/duty_stations/nigeria"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        soup  = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("div.j") or soup.select("li.job") or soup.select("div[class*='job']")

        for card in cards[:20]:
            title_el = card.find(["h2", "h3", "a"])
            title    = title_el.get_text(strip=True) if title_el else ""
            org_el   = card.find(class_=lambda c: c and "org" in str(c).lower())
            org      = org_el.get_text(strip=True) if org_el else "UN Agency"
            link_el  = card.find("a", href=True)
            link     = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = f"https://unjobs.org{link}"
            if not title or len(title) < 3:
                continue
            job_id = hashlib.md5(f"unjobs{title}{org}".encode()).hexdigest()
            jobs.append({
                "id":          f"unjobs_{job_id}",
                "title":       title,
                "company":     org,
                "location":    "Nigeria / Remote",
                "salary":      "",
                "description": "",
                "tags":        "UN, NGO, Nigeria",
                "url":         link,
                "source":      "UN Jobs",
            })
    except Exception as e:
        print(f"     ⚠️ UN Jobs failed: {e}")
    return jobs


def _scrape_devex() -> list:
    """Devex — international development sector jobs (free listings only)."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        url = "https://www.devex.com/jobs/search?type=job&location=Nigeria"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        soup  = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("article.job-listing") or soup.select("div[class*='job']")

        for card in cards[:15]:
            title_el = card.find(["h2", "h3"])
            title    = title_el.get_text(strip=True) if title_el else ""
            org_el   = card.find(class_=lambda c: c and "org" in str(c).lower())
            org      = org_el.get_text(strip=True) if org_el else ""
            link_el  = card.find("a", href=True)
            link     = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = f"https://www.devex.com{link}"
            if not title or len(title) < 3:
                continue
            job_id = hashlib.md5(f"devex{title}{org}".encode()).hexdigest()
            jobs.append({
                "id":          f"devex_{job_id}",
                "title":       title,
                "company":     org,
                "location":    "Nigeria / Remote",
                "salary":      "",
                "description": "",
                "tags":        "NGO, Development, International",
                "url":         link,
                "source":      "Devex",
            })
    except Exception as e:
        print(f"     ⚠️ Devex failed: {e}")
    return jobs
