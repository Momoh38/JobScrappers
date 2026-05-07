import json
import os
from scrapers.remoteok import scrape_remoteok
from scrapers.arbeitnow import scrape_arbeitnow
from scrapers.themuse import scrape_themuse
from scrapers.weworkremotely import scrape_weworkremotely
from scrapers.jobberman import scrape_jobberman
from scrapers.myjobmag import scrape_myjobmag
from scrapers.ngcareers import scrape_ngcareers
from scrapers.telegram_channels import scrape_telegram_channels
from filter import is_halal
from sender import send_job

SEEN_JOBS_FILE = "seen_jobs.json"

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w") as f:
        json.dump(list(seen), f)

def run():
    print("🚀 Job Bot Starting...")
    seen_jobs = load_seen_jobs()
    print(f"📦 Already seen jobs: {len(seen_jobs)}")
    all_jobs = []

    scrapers = [
        ("RemoteOK",         scrape_remoteok),
        ("Arbeitnow",        scrape_arbeitnow),
        ("TheMuse",          scrape_themuse),
        ("WeWorkRemotely",   scrape_weworkremotely),
        ("Jobberman",        scrape_jobberman),
        ("MyJobMag",         scrape_myjobmag),
        ("NGCareers",        scrape_ngcareers),
        ("TelegramChannels", scrape_telegram_channels),
    ]

    for name, scraper in scrapers:
        try:
            print(f"  📡 Scraping {name}...")
            jobs = scraper()
            print(f"     ✅ Found {len(jobs)} jobs")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")

    print(f"\n📋 Total jobs found: {len(all_jobs)}")

    new_count = 0
    skipped_haram = 0
    skipped_seen = 0

    for job in all_jobs:
        job_id = job.get("id") or f"{job.get('title','')}_{job.get('company','')}"

        if job_id in seen_jobs:
            skipped_seen += 1
            continue

        if not is_halal(job):
            skipped_haram += 1
            seen_jobs.add(job_id)
            continue

        try:
            send_job(job)
            seen_jobs.add(job_id)
            new_count += 1
        except Exception as e:
            print(f"     ⚠️ Failed to send job: {e}")

    save_seen_jobs(seen_jobs)
    print(f"\n✅ Done! Sent: {new_count} | Skipped (haram): {skipped_haram} | Already seen: {skipped_seen}")

if __name__ == "__main__":
    run()
