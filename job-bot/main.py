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
from scrapers.indeed_ng import scrape_indeed_ng
from scrapers.grabjobs import scrape_grabjobs
from scrapers.dailyremote import scrape_dailyremote
from scrapers.workingnomads import scrape_workingnomads
from scrapers.startupjobs import scrape_startupjobs
from scrapers.dynamitejobs import scrape_dynamitejobs
from scrapers.braintrust import scrape_braintrust
from scrapers.twitter_jobs import scrape_twitter_jobs
from scrapers.virtustant import scrape_virtustant
from scrapers.oneforma import scrape_oneforma
from scrapers.jooble import scrape_jooble
from scrapers.doballi import scrape_doballi
from scrapers.remotive import scrape_remotive
from scrapers.jobgurus import scrape_jobgurus
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
    print("🚀 Halal Jobs Bot Starting...")
    seen_jobs = load_seen_jobs()
    print(f"📦 Already seen: {len(seen_jobs)} jobs\n")

    all_jobs = []

    scrapers = [
        # --- Global Remote APIs (most reliable) ---
        ("RemoteOK",        scrape_remoteok),
        ("Remotive",        scrape_remotive),
        ("Arbeitnow",       scrape_arbeitnow),
        ("TheMuse",         scrape_themuse),
        ("WeWorkRemotely",  scrape_weworkremotely),
        ("WorkingNomads",   scrape_workingnomads),
        ("Braintrust",      scrape_braintrust),
        ("DailyRemote",     scrape_dailyremote),
        ("DynamiteJobs",    scrape_dynamitejobs),
        ("StartupJobs",     scrape_startupjobs),
        ("Virtustant",      scrape_virtustant),
        ("OneForma",        scrape_oneforma),
        # --- Nigeria-specific ---
        ("Indeed Nigeria",  scrape_indeed_ng),
        ("Jobberman",       scrape_jobberman),
        ("MyJobMag",        scrape_myjobmag),
        ("NGCareers",       scrape_ngcareers),
        ("GrabJobs",        scrape_grabjobs),
        ("Jooble Nigeria",  scrape_jooble),
        ("Doballi",         scrape_doballi),
        ("JobGurus",        scrape_jobgurus),
        # --- Social Media ---
        ("Telegram",        scrape_telegram_channels),
        ("X / Twitter",     scrape_twitter_jobs),
    ]

    for name, scraper in scrapers:
        try:
            print(f"  📡 Scraping {name}...")
            jobs = scraper()
            print(f"     ✅ Found {len(jobs)} jobs")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")

    print(f"\n📋 Total jobs found across all sources: {len(all_jobs)}")

    new_count = 0
    skipped_haram = 0
    skipped_seen = 0
    skipped_filter = 0

    for job in all_jobs:
        job_id = job.get("id") or f"{job.get('title', '')}_{job.get('company', '')}"

        if job_id in seen_jobs:
            skipped_seen += 1
            continue

        if not is_halal(job):
            skipped_haram += 1
            skipped_filter += 1
            seen_jobs.add(job_id)
            continue

        try:
            send_job(job)
            seen_jobs.add(job_id)
            new_count += 1
        except Exception as e:
            print(f"     ⚠️ Failed to send: {e}")

    save_seen_jobs(seen_jobs)
    print(f"\n✅ Done!")
    print(f"   📨 Sent:          {new_count}")
    print(f"   🚫 Filtered out:  {skipped_filter} (haram/non-English/not Nigeria-friendly)")
    print(f"   👁️  Already seen:  {skipped_seen}")


if __name__ == "__main__":
    run()
