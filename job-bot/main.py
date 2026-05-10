"""
main.py — Entry point for Halal Jobs Bot
"""

import json
import os
from datetime import datetime

# --- Global Remote (API-based, most reliable) ---
#from scrapers.remoteok        import scrape_remoteok
#from scrapers.remotive        import scrape_remotive
#from scrapers.themuse         import scrape_themuse
#from scrapers.weworkremotely  import scrape_weworkremotely
#from scrapers.workingnomads   import scrape_workingnomads
#from scrapers.braintrust      import scrape_braintrust
#from scrapers.virtustant      import scrape_virtustant
#from scrapers.linkedin_rss    import scrape_linkedin_rss
from scrapers.jobicy          import scrape_jobicy       # replaces DailyRemote (403) TESTING
#from scrapers.himalayas       import scrape_himalayas    # new free API

# --- Nigeria-specific ---
#from scrapers.jobberman       import scrape_jobberman
#from scrapers.myjobmag        import scrape_myjobmag
#from scrapers.ngcareers       import scrape_ngcareers
#from scrapers.jobgurus        import scrape_jobgurus

# --- International / NGO / Africa ---
#from scrapers.ngo_jobs        import scrape_ngo_jobs
#from scrapers.africa_jobs     import scrape_africa_jobs

# --- Social Media ---
#from scrapers.telegram_channels import scrape_telegram_channels




# --- Suspended (kept for reference, do not import) ---
# from scrapers.indeed_ng     import scrape_indeed_ng    (403 Forbidden)
# from scrapers.grabjobs      import scrape_grabjobs     (403 Forbidden)
# from scrapers.jooble        import scrape_jooble       (403 - needs paid API key)
# from scrapers.dailyremote   import scrape_dailyremote  (403 Forbidden)
# from scrapers.twitter_jobs  import scrape_twitter_jobs (Nitter fully dead)
# from scrapers.oneforma      import scrape_oneforma     (data annotation only)
# from scrapers.startupjobs   import scrape_startupjobs  (low Nigeria relevance)
# from scrapers.dynamitejobs  import scrape_dynamitejobs (abroad-focused)
# from scrapers.freelance     import scrape_freelance    (optional freelance)
# from scrapers.arbeitnow     import scrape_arbeitnow    (Germany-focused)
#from scrapers.doballi         import scrape_doballi

from filter import is_halal
from sender import send_job, send_stats, send_health_alert

SEEN_JOBS_FILE = "seen_jobs.json"
HEALTH_FILE    = "scraper_health.json"
STATS_FILE     = "run_stats.json"


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return default
    return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def update_health(health: dict, name: str, success: bool) -> dict:
    if name not in health:
        health[name] = {"failures": 0, "last_success": None}
    if success:
        health[name]["failures"] = 0
        health[name]["last_success"] = datetime.now().isoformat()
    else:
        health[name]["failures"] += 1
        if health[name]["failures"] == 3:
            send_health_alert(name, 3)
    return health


def maybe_send_weekly_report(health: dict, run_stats_history: list):
    if datetime.now().weekday() != 6:
        return
    last  = load_json("last_weekly_report.json", {}).get("date", "")
    today = datetime.now().strftime("%Y-%m-%d")
    if last == today:
        return

    from sender import _send_text
    working = [n for n, h in health.items() if h.get("failures", 0) == 0]
    broken  = [n for n, h in health.items() if h.get("failures", 0) >= 3]

    lines = [
        "📅 *Weekly Bot Report*\n",
        f"✅ Working scrapers: *{len(working)}*",
        f"❌ Broken scrapers: *{len(broken)}*",
    ]
    if broken:
        lines.append("Needs fixing: " + ", ".join(broken))
    if run_stats_history:
        total_sent = sum(r.get("sent", 0) for r in run_stats_history[-168:])
        lines.append(f"\n📨 Jobs sent this week: *{total_sent}*")

    _send_text("\n".join(lines))
    save_json("last_weekly_report.json", {"date": today})


def run():
    print(f"🚀 Halal Jobs Bot — {datetime.now().strftime('%d %b %Y %H:%M')} WAT")

    seen_jobs = set(load_json(SEEN_JOBS_FILE, []))
    health    = load_json(HEALTH_FILE, {})
    history   = load_json(STATS_FILE, [])

    print(f"📦 Already seen: {len(seen_jobs)} jobs\n")

    scrapers = [
        # Global Remote
        #("RemoteOK",       scrape_remoteok),
        #("Remotive",       scrape_remotive),
        #("TheMuse",        scrape_themuse),
        #("WeWorkRemotely", scrape_weworkremotely),
        #("WorkingNomads",  scrape_workingnomads),
        #("Braintrust",     scrape_braintrust),
        #("Virtustant",     scrape_virtustant),
        #("LinkedIn RSS",   scrape_linkedin_rss),
        ("Jobicy",         scrape_jobicy),
        #("Himalayas",      scrape_himalayas),
        # Nigeria-specific
        #("Jobberman",      scrape_jobberman),
        #("MyJobMag",       scrape_myjobmag),
        #("NGCareers",      scrape_ngcareers),
        #("JobGurus",       scrape_jobgurus),
        
        
        # International / NGO / Africa
        #("NGO / UN Jobs",  scrape_ngo_jobs),
        #("Africa Jobs",    scrape_africa_jobs),
        # Social Media
        #("Telegram",       scrape_telegram_channels),
        #("Doballi",        scrape_doballi),
        
    ]

    all_jobs      = []
    source_counts = {}

    for name, scraper in scrapers:
        try:
            print(f"  📡 Scraping {name}...")
            jobs  = scraper()
            count = len(jobs)
            print(f"     ✅ Found {count} jobs")
            all_jobs.extend(jobs)
            source_counts[name] = count
            health = update_health(health, name, success=True)
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")
            health = update_health(health, name, success=False)
            source_counts[name] = 0

    print(f"\n📋 Total collected: {len(all_jobs)}")

    new_count      = 0
    skipped_seen   = 0
    skipped_filter = 0

    for job in all_jobs:
        job_id = job.get("id") or f"{job.get('title','')}_{job.get('company','')}"

        if job_id in seen_jobs:
            skipped_seen += 1
            continue

        if not is_halal(job):
            skipped_filter += 1
            seen_jobs.add(job_id)
            continue

        try:
            send_job(job)
            seen_jobs.add(job_id)
            new_count += 1
        except Exception as e:
            print(f"     ⚠️ Failed to send: {e}")

    save_json(SEEN_JOBS_FILE, list(seen_jobs))
    save_json(HEALTH_FILE, health)

    stats = {
        "timestamp":     datetime.now().isoformat(),
        "sent":          new_count,
        "filtered":      skipped_filter,
        "seen":          skipped_seen,
        "sources":       len(scrapers),
        "source_counts": source_counts,
    }
    history.append(stats)
    save_json(STATS_FILE, history[-500:])

    current_hour = datetime.now().hour
    if new_count > 0 or current_hour in [7, 13, 19]:
        send_stats(stats)

    maybe_send_weekly_report(health, history)

    print(f"\n✅ Done!")
    print(f"   📨 Sent:         {new_count}")
    print(f"   🚫 Filtered:     {skipped_filter}")
    print(f"   👁️  Already seen: {skipped_seen}")


if __name__ == "__main__":
    run()
