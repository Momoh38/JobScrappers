"""
scrapers/freelance.py — Freelance job platforms open to Nigerians, free to apply.
Covers: PeoplePerHour, Guru.com, Freelancer job listings (no paid membership needed to apply).
NOTE: Upwork excluded (requires paid connects to apply).
"""

import requests
import hashlib
from bs4 import BeautifulSoup


def scrape_freelance() -> list:
    jobs = []
    jobs.extend(_scrape_peopleperhour())
    jobs.extend(_scrape_guru())
    jobs.extend(_scrape_freelancer_projects())
    return jobs


def _scrape_peopleperhour() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    categories = ["writing-translation", "admin-support", "tech-programming",
                  "design", "digital-marketing", "data-entry"]

    for cat in categories:
        try:
            url = f"https://www.peopleperhour.com/freelance-{cat}-jobs"
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("li.feed-item") or soup.select("div.job-card") or soup.select("article")

            for card in cards[:10]:
                title_el = card.find(["h2", "h3", "a"])
                title    = title_el.get_text(strip=True) if title_el else ""
                desc_el  = card.find("p")
                desc     = desc_el.get_text(strip=True) if desc_el else ""
                link_el  = card.find("a", href=True)
                link     = link_el["href"] if link_el else ""
                if link and not link.startswith("http"):
                    link = f"https://www.peopleperhour.com{link}"
                budget_el = card.find(class_=lambda c: c and "budget" in str(c).lower())
                salary    = budget_el.get_text(strip=True) if budget_el else ""

                if not title or len(title) < 3:
                    continue
                job_id = hashlib.md5(f"pph{title}{desc[:30]}".encode()).hexdigest()
                jobs.append({
                    "id":          f"pph_{job_id}",
                    "title":       title,
                    "company":     "PeoplePerHour Client",
                    "location":    "Remote (Worldwide)",
                    "salary":      salary,
                    "description": desc[:300],
                    "tags":        f"Freelance, {cat.replace('-', ' ').title()}",
                    "url":         link,
                    "source":      "PeoplePerHour",
                })
        except Exception as e:
            print(f"     ⚠️ PeoplePerHour {cat} failed: {e}")
    return jobs


def _scrape_guru() -> list:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        url = "https://www.guru.com/d/jobs/"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("div.jobRecord") or soup.select("li.job") or soup.select("div[class*='job']")

        for card in cards[:20]:
            title_el  = card.find(["h2", "h3", "a"])
            title     = title_el.get_text(strip=True) if title_el else ""
            desc_el   = card.find(class_=lambda c: c and "desc" in str(c).lower())
            desc      = desc_el.get_text(strip=True) if desc_el else ""
            link_el   = card.find("a", href=True)
            link      = link_el["href"] if link_el else ""
            if link and not link.startswith("http"):
                link = f"https://www.guru.com{link}"
            if not title or len(title) < 3:
                continue
            job_id = hashlib.md5(f"guru{title}".encode()).hexdigest()
            jobs.append({
                "id":          f"guru_{job_id}",
                "title":       title,
                "company":     "Guru Client",
                "location":    "Remote (Worldwide)",
                "salary":      "",
                "description": desc[:300],
                "tags":        "Freelance",
                "url":         link,
                "source":      "Guru.com",
            })
    except Exception as e:
        print(f"     ⚠️ Guru.com failed: {e}")
    return jobs


def _scrape_freelancer_projects() -> list:
    """Freelancer.com public project listings — free to bid."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (HalalJobsBot/1.0)",
        "Accept": "application/json",
    }
    try:
        url = (
            "https://www.freelancer.com/api/projects/0.1/projects/active/"
            "?job_details=true&limit=20&offset=0"
        )
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
        data    = response.json()
        projects = data.get("result", {}).get("projects", [])

        for p in projects:
            title  = p.get("title", "")
            desc   = p.get("preview_description", "") or p.get("description", "")
            pid    = p.get("id", "")
            budget = p.get("budget", {})
            salary = ""
            if budget:
                mn = budget.get("minimum", "")
                mx = budget.get("maximum", "")
                if mn and mx:
                    salary = f"${mn}–${mx}"

            if not title:
                continue
            jobs.append({
                "id":          f"freelancer_{pid}",
                "title":       title,
                "company":     "Freelancer Client",
                "location":    "Remote (Worldwide)",
                "salary":      salary,
                "description": str(desc)[:300],
                "tags":        "Freelance, Project",
                "url":         f"https://www.freelancer.com/projects/{pid}",
                "source":      "Freelancer.com",
            })
    except Exception as e:
        print(f"     ⚠️ Freelancer.com failed: {e}")
    return jobs
