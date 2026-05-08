"""
scrapers/africa_jobs.py — Africa-focused job platforms that actively connect
African talent (including Nigeria) with international employers.
Sources: Fuzu, Shortlist.io, Jobbatical, AfricaRecruit, EthicsPoint
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_africa_jobs() -> list:
    jobs = []
    jobs.extend(_scrape_fuzu())
    jobs.extend(_scrape_shortlist())
    jobs.extend(_scrape_africawork())
    return jobs


def _scrape_fuzu() -> list:
    """Fuzu — East & West Africa job platform, actively includes Nigeria."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        url = "https://www.fuzu.com/nigeria/jobs"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        soup  = BeautifulSoup(response.text, "html.parser")
        cards = (
            soup.select("div.job-card") or
            soup.select("article") or
            soup.select("div[class*='job']")
        )
        for card in cards[:20]:
            title_el   = card.find(["h2", "h3", "h4"])
            title      = title_el.get_text(strip=True) if title_el else ""
            company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
            company    = company_el.get_text(strip=True) if company_el else ""
            loc_el     = card.find(class_=lambda c: c and "location" in str(c).lower())
            location   = loc_el.get_text(strip=True) if loc_el else "Nigeria"
            link_el    = card.find("a", href=True)
            link       = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = f"https://www.fuzu.com{link}"
            if not title or len(title) < 3:
                continue
            job_id = hashlib.md5(f"fuzu{title}{company}".encode()).hexdigest()
            jobs.append({
                "id":          f"fuzu_{job_id}",
                "title":       title,
                "company":     company,
                "location":    location,
                "salary":      "",
                "description": "",
                "tags":        "Africa, Nigeria, Fuzu",
                "url":         link,
                "source":      "Fuzu",
            })
    except Exception as e:
        print(f"     ⚠️ Fuzu failed: {e}")
    return jobs


def _scrape_shortlist() -> list:
    """Shortlist.io — matches African professionals with international companies."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        url = "https://shortlist.io/jobs"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        soup  = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("div.job-card") or soup.select("article") or soup.select("li.job")
        for card in cards[:20]:
            title_el   = card.find(["h2", "h3", "a"])
            title      = title_el.get_text(strip=True) if title_el else ""
            company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
            company    = company_el.get_text(strip=True) if company_el else ""
            link_el    = card.find("a", href=True)
            link       = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = f"https://shortlist.io{link}"
            if not title or len(title) < 3:
                continue
            job_id = hashlib.md5(f"shortlist{title}{company}".encode()).hexdigest()
            jobs.append({
                "id":          f"shortlist_{job_id}",
                "title":       title,
                "company":     company,
                "location":    "Africa / Remote",
                "salary":      "",
                "description": "",
                "tags":        "Africa, International, Shortlist",
                "url":         link,
                "source":      "Shortlist.io",
            })
    except Exception as e:
        print(f"     ⚠️ Shortlist.io failed: {e}")
    return jobs


def _scrape_africawork() -> list:
    """AfricaWork — pan-African recruitment platform."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        url = "https://www.africa-work.com/job-offers/nigeria"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        soup  = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("article.offer") or soup.select("div[class*='offer']") or soup.select("li.job")
        for card in cards[:20]:
            title_el   = card.find(["h2", "h3", "a"])
            title      = title_el.get_text(strip=True) if title_el else ""
            company_el = card.find(class_=lambda c: c and "company" in str(c).lower())
            company    = company_el.get_text(strip=True) if company_el else ""
            link_el    = card.find("a", href=True)
            link       = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = f"https://www.africa-work.com{link}"
            if not title or len(title) < 3:
                continue
            job_id = hashlib.md5(f"africawork{title}{company}".encode()).hexdigest()
            jobs.append({
                "id":          f"africawork_{job_id}",
                "title":       title,
                "company":     company,
                "location":    "Nigeria / Africa",
                "salary":      "",
                "description": "",
                "tags":        "Africa, Nigeria, Pan-African",
                "url":         link,
                "source":      "AfricaWork",
            })
    except Exception as e:
        print(f"     ⚠️ AfricaWork failed: {e}")
    return jobs
