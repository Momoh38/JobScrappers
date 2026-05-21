"""
main.py — Entry point for Job Scraper Bot
UPDATED: Telegram jobs are ALWAYS kept (Nigeria-friendly)
"""

import json
import os
import re
import time
from datetime import datetime

# --- FREE SOURCES (Keep all, just filter better) ---

# --- NEW SOURCES ---
from scrapers.jobsregion import scrape_jobsregion
from scrapers.jobfound import scrape_jobfound

# Nigeria-specific - BEST
from scrapers.jobberman       import scrape_jobberman
from scrapers.myjobmag        import scrape_myjobmag
from scrapers.ngcareers       import scrape_ngcareers
from scrapers.jobgurus        import scrape_jobgurus

# International / NGO / Africa - GOOD
from scrapers.ngo_jobs        import scrape_ngo_jobs
from scrapers.africa_jobs     import scrape_africa_jobs

# Global Remote - FREE (need better filtering)
from scrapers.remoteok        import scrape_remoteok
from scrapers.remotive        import scrape_remotive
from scrapers.themuse         import scrape_themuse
from scrapers.workingnomads   import scrape_workingnomads
from scrapers.braintrust      import scrape_braintrust
from scrapers.himalayas       import scrape_himalayas
from scrapers.wfh_io          import scrape_wfh_io
from scrapers.virtustant      import scrape_virtustant

# Social Media - GOOD (Nigeria-friendly, NEVER filter)
from scrapers.telegram_channels import scrape_telegram_channels

# --- REMOVED (Only these are actually paid/broken) ---
# from scrapers.weworkremotely  import scrape_weworkremotely # ❌ Requires payment
# from scrapers.jobicy          import scrape_jobicy        # ❌ Chinese jobs
# from scrapers.indeed_ng       import scrape_indeed_ng     # ❌ 403 Forbidden
# from scrapers.grabjobs        import scrape_grabjobs      # ❌ 403 Forbidden
# from scrapers.jooble          import scrape_jooble        # ❌ Paid API
# from scrapers.dailyremote     import scrape_dailyremote   # ❌ 403 Forbidden


from filter import is_halal
from sender import send_job, send_stats, send_health_alert

SEEN_JOBS_FILE = "seen_jobs.json"
HEALTH_FILE    = "scraper_health.json"
STATS_FILE     = "run_stats.json"

# After collecting jobs, before sending
for job in all_jobs:
    # If title is generic, try to extract from URL
    if job.get('title') in ["Opportunity", "Job Opportunity", "Job Vacancy", "", None]:
        url = job.get('url', '')
        if url:
            # Extract from URL path
            url_parts = url.split('/')
            for part in url_parts:
                if '-' in part and len(part) > 10:
                    # Convert URL slug to title (replace - with space, capitalize)
                    potential_title = part.replace('-', ' ').replace('_', ' ').title()
                    if len(potential_title) > 5 and len(potential_title) < 100:
                        job['title'] = potential_title
                        break

# Countries/locations to filter out (Nigerians can't apply)
FILTER_LOCATIONS = [
    # Specific countries
    'us', 'usa', 'united states', 'canada', 'uk', 'united kingdom',
    'germany', 'france', 'italy', 'spain', 'portugal', 'netherlands',
    'belgium', 'switzerland', 'austria', 'sweden', 'norway', 'denmark',
    'finland', 'ireland', 'australia', 'new zealand',
    'brazil', 'mexico', 'argentina', 'chile', 'colombia', 'peru',
    'philippines', 'malaysia', 'singapore', 'japan', 'south korea',
    'israel', 'uae', 'dubai', 'qatar', 'kuwait', 'saudi arabia',
    'latin america', 'south america', 'north america', 'europe', 'asia', 'oceania',
    
    # Location patterns
    'must be based in', 'must reside in', 'right to work',
    'us citizen', 'green card', 'security clearance',
]

# GOOD locations (Nigeria-friendly)
GOOD_LOCATIONS = [
    'remote', 'worldwide', 'global', 'anywhere', 'work from home',
    'nigeria', 'lagos', 'abuja', 'africa', 'kenya', 'ghana', 'south africa'
]

# Sources that are ALWAYS Nigeria-friendly (never filter by location)
ALWAYS_KEEP_SOURCES = [
    "Telegram",  # Telegram channels are Nigerian job groups
    "Jobberman",  # Nigerian job board
    "MyJobMag",   # Nigerian job board
    "NGCareers",  # Nigerian job board
    "JobGurus",   # Nigerian job board
    "Africa Jobs", # African jobs
    "NGO / UN Jobs", # UN jobs often in Africa
]


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


def is_location_nigeria_friendly(location: str, title: str = "", description: str = "", source: str = "") -> bool:
    """
    Check if job location is accessible from Nigeria.
    ALWAYS returns True for sources in ALWAYS_KEEP_SOURCES (like Telegram).
    """
    # SOURCES THAT ARE ALWAYS NIGERIA-FRIENDLY (never filter)
    if source in ALWAYS_KEEP_SOURCES:
        return True
    
    if not location:
        return True  # No location specified, assume remote
    
    location_lower = location.lower()
    combined = f"{location_lower} {title.lower()} {description.lower()}"
    
    # First check if it's explicitly good (remote/nigeria/africa)
    for good in GOOD_LOCATIONS:
        if good in combined:
            # But also check for contradictions (e.g., "remote - US only")
            for bad in FILTER_LOCATIONS:
                if bad in combined:
                    return False
            return True
    
    # Then check if it contains any bad locations
    for bad in FILTER_LOCATIONS:
        if bad in combined:
            print(f"     📍 Location filtered: '{bad}' in '{location}' (source: {source})")
            return False
    
    # If location is a single country name not in good list, likely restricted
    single_country = re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$', location_lower)
    if single_country and location_lower not in GOOD_LOCATIONS:
        print(f"     📍 Location filtered: single country '{location}' (not remote, source: {source})")
        return False
    
    return True


def clean_remotive_job(job: dict) -> dict:
    """Special handling for Remotive - remove messy descriptions"""
    description = job.get('description', '')
    if description:
        # Try to extract first meaningful paragraph
        lines = description.split('\n')
        clean_desc = []
        for line in lines[:5]:  # First few lines only
            line = line.strip()
            # Skip HTML/CSS garbage
            if line and not line.startswith('<') and len(line) > 10:
                # Remove excessive spaces
                line = re.sub(r'\s+', ' ', line)
                if line not in clean_desc:
                    clean_desc.append(line[:300])
        
        if clean_desc:
            job['description'] = '\n'.join(clean_desc[:2])  # Keep only first 2 lines
        else:
            job['description'] = "🔗 Click 'Apply Now' for full job details."
    
    return job


def run():
    print(f"🚀 Job Scraper Bot — {datetime.now().strftime('%d %b %Y %H:%M')} WAT")
    print(f"✅ Using FREE job sources with smart location filtering\n")
    print(f"📌 Telegram & Nigerian sources are ALWAYS kept (no location filtering)\n")
    
    # ALL FREE SCRAPERS
    scrapers = [

        # NEW SOURCES - Nigerian/African job boards
        ("Jobsregion",          scrape_jobsregion),
        ("Jobfound",            scrape_jobfound),
        
        # Nigeria-specific (MOST RELIABLE - NEVER FILTER)
        ("Jobberman",           scrape_jobberman),
        ("MyJobMag",            scrape_myjobmag),
        ("NGCareers",           scrape_ngcareers),
        ("JobGurus",            scrape_jobgurus),
        
        # International / NGO / Africa (NEVER FILTER)
        ("NGO / UN Jobs",       scrape_ngo_jobs),
        ("Africa Jobs",         scrape_africa_jobs),
        
        # Global Remote (FILTER these by location)
        ("RemoteOK",            scrape_remoteok),
        ("Remotive",            scrape_remotive),
        ("TheMuse",             scrape_themuse),
        ("WorkingNomads",       scrape_workingnomads),
        ("Braintrust",          scrape_braintrust),
        ("Himalayas",           scrape_himalayas),
        ("WFH.io",              scrape_wfh_io),
        ("Virtustant",          scrape_virtustant),
        
        # Social Media (NEVER FILTER - Nigerian job groups)
        ("Telegram",            scrape_telegram_channels),
    ]
    
    print(f"📍 Scanning {len(scrapers)} job sources (all free)\n")

    seen_jobs = set(load_json(SEEN_JOBS_FILE, []))
    health    = load_json(HEALTH_FILE, {})
    history   = load_json(STATS_FILE, [])

    print(f"📦 Already seen: {len(seen_jobs)} jobs\n")

    all_jobs      = []
    source_counts = {}
    location_filtered = 0

    for name, scraper in scrapers:
        try:
            print(f"  📡 Scraping {name}...")
            jobs = scraper()
            original_count = len(jobs)
            
            # Apply location filtering (but NEVER filter Telegram/Nigerian sources)
            filtered_jobs = []
            for job in jobs:
                location = job.get('location', '')
                title = job.get('title', '')
                description = job.get('description', '')
                
                if is_location_nigeria_friendly(location, title, description, name):
                    filtered_jobs.append(job)
                else:
                    location_filtered += 1
                    if location:
                        print(f"     📍 Filtered: {job.get('title', '?')[:40]}... ({location})")
            
            # Special handling for Remotive (clean descriptions)
            if name == "Remotive":
                filtered_jobs = [clean_remotive_job(job) for job in filtered_jobs]
            
            count = len(filtered_jobs)
            keep_note = " (ALL KEPT)" if name in ALWAYS_KEEP_SOURCES else ""
            print(f"     ✅ Found {original_count} raw, {count} Nigeria-friendly jobs{keep_note}")
            all_jobs.extend(filtered_jobs)
            source_counts[name] = count
            health = update_health(health, name, success=True)
            time.sleep(1)
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")
            health = update_health(health, name, success=False)
            source_counts[name] = 0

    print(f"\n📋 Total Nigeria-friendly jobs: {len(all_jobs)}")
    print(f"   📍 Location-filtered: {location_filtered} jobs removed")

    new_count      = 0
    skipped_seen   = 0
    skipped_filter = 0
    failed_send    = 0

    for job in all_jobs:
        job_url = job.get('url', '')
        if job_url:
            job_id = re.sub(r'[^a-zA-Z0-9_]', '_', job_url)[:200]
        else:
            job_id = f"{job.get('title','')}_{job.get('company','')}"
            job_id = re.sub(r'[^a-zA-Z0-9_]', '_', job_id)[:200]

        if job_id in seen_jobs:
            skipped_seen += 1
            continue

        if not is_halal(job):
            skipped_filter += 1
            continue

        try:
            success = send_job(job)
            if success:
                seen_jobs.add(job_id)
                new_count += 1
            else:
                failed_send += 1
            time.sleep(0.5)
        except Exception as e:
            failed_send += 1
            print(f"     ⚠️ Failed to send: {e}")

    save_json(SEEN_JOBS_FILE, list(seen_jobs))
    save_json(HEALTH_FILE, health)

    stats = {
        "timestamp":     datetime.now().isoformat(),
        "sent":          new_count,
        "filtered":      skipped_filter,
        "seen":          skipped_seen,
        "failed":        failed_send,
        "location_filtered": location_filtered,
        "sources":       len(scrapers),
        "source_counts": source_counts,
    }
    history.append(stats)
    save_json(STATS_FILE, history[-500:])

    send_stats(stats)

    print(f"\n✅ Done!")
    print(f"   📨 Sent:         {new_count}")
    print(f"   🚫 Filtered:     {skipped_filter}")
    print(f"   👁️  Already seen: {skipped_seen}")
    print(f"   📍 Location removed: {location_filtered}")
    print(f"   ❌ Failed:       {failed_send}")
    print(f"\n💡 All {len(scrapers)} sources are FREE - no payment required!")
    print(f"   📌 Telegram & Nigerian sources: ALL jobs kept (Nigeria-friendly)")
    
    print(f"\n📊 Scraper Health:")
    working = []
    failed = []
    for name, h in health.items():
        if h.get('failures', 0) >= 2:
            failed.append(name)
        else:
            working.append(name)
    
    print(f"   ✅ Working: {len(working)} sources")
    if failed:
        print(f"   ❌ Failed: {', '.join(failed)}")


if __name__ == "__main__":
    run()
