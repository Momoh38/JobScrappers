"""
main.py — Entry point for Halal Jobs Bot
UPDATED: Fixed import error + extracts actual job application links from Telegram
"""

import json
import os
import re
import time
from datetime import datetime

# --- Global Remote (API-based, most reliable) ---
#from scrapers.remoteok        import scrape_remoteok
#from scrapers.remotive        import scrape_remotive
#from scrapers.themuse         import scrape_themuse
#from scrapers.workingnomads   import scrape_workingnomads
#from scrapers.braintrust      import scrape_braintrust
#from scrapers.virtustant      import scrape_virtustant
#from scrapers.jobicy          import scrape_jobicy
#from scrapers.weworkremotely  import scrape_weworkremotely
#from scrapers.we_work_remotely_enhanced import scrape_wwr_enhanced
#from scrapers.wfh_io            import scrape_wfh_io
#from scrapers.himalayas       import scrape_himalayas


# --- Nigeria-specific ---
#from scrapers.jobberman       import scrape_jobberman
#from scrapers.myjobmag        import scrape_myjobmag
#from scrapers.ngcareers       import scrape_ngcareers
#from scrapers.jobgurus        import scrape_jobgurus

# --- International / NGO / Africa ---
#from scrapers.ngo_jobs        import scrape_ngo_jobs
#from scrapers.africa_jobs     import scrape_africa_jobs

# --- Social Media ---
from scrapers.telegram_channels import scrape_telegram_channels


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
#from scrapers.pangaea           import scrape_pangaea
#from scrapers.relocate_me       import scrape_relocate_me
#from scrapers.europeremote      import scrape_europeremote
#from scrapers.remoters          import scrape_remoters (Not useful)
#from scrapers.linkedin_rss    import scrape_linkedin_rss


from filter import is_halal
from sender import send_job, send_stats, send_health_alert  # Fixed import name

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


def extract_external_job_links(message_text: str) -> list:
    """
    Extract actual job application links from Telegram message.
    Filters out Telegram internal links and returns only external job URLs.
    """
    # Pattern to find all URLs
    url_pattern = r'https?://[^\s<>"\')\]]+'
    all_links = re.findall(url_pattern, message_text)
    
    # Domains to filter out (Telegram internal)
    telegram_domains = [
        't.me', 'telegram.me', 'telegram.dog', 'telegra.ph',
        't.me/', 'telegram.me/', 't.me/s/'
    ]
    
    # Job site domains (prioritize these)
    job_domains = [
        'linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'monster.com',
        'remoteok.com', 'weworkremotely.com', 'remotive.com', 'jobicy.com',
        'workingnomads.com', 'flexjobs.com', 'upwork.com', 'freelancer.com',
        'jobberman.com', 'myjobmag.com', 'ngcareers.com', 'jobgurus.com.ng',
        'careers.', 'jobs.', 'apply.', 'hire.', 'recruitment.',
        'forms.gle', 'docs.google.com/forms',
        'airtable.com', 'typeform.com',
        'bamboohr.com', 'greenhouse.io', 'lever.co', 'workable.com',
    ]
    
    external_links = []
    
    for link in all_links:
        # Clean up link
        link = link.rstrip('.,!?;:)]')
        
        # Skip Telegram internal links
        is_telegram = False
        for tg_domain in telegram_domains:
            if tg_domain in link.lower():
                is_telegram = True
                break
        
        if is_telegram:
            continue
        
        # Check if it's a job-related link
        is_job_link = False
        for job_domain in job_domains:
            if job_domain.lower() in link.lower():
                is_job_link = True
                break
        
        if is_job_link or (not external_links and len(link) > 10):
            external_links.append(link)
    
    # Remove duplicates
    seen = set()
    unique_links = []
    for link in external_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links


def enhance_telegram_job(job: dict) -> dict:
    """
    Enhance a Telegram job by extracting external links and better data
    """
    # Get message content
    message_text = job.get('description', '') or job.get('title', '')
    original_url = job.get('url', '')
    
    # Extract external job links
    external_links = extract_external_job_links(message_text)
    
    if external_links:
        # Use the first external link as the job URL
        job['url'] = external_links[0]
        job['job_links'] = external_links
        print(f"     🔗 Found external link: {external_links[0][:60]}...")
    elif original_url and 't.me' not in original_url:
        # Keep original URL if it's not a Telegram link
        pass
    else:
        # No external link found - mark for skipping
        job['_no_external_link'] = True
        print(f"     ⚠️ No external link found in message")
    
    # Try to extract better title (remove @mentions)
    title = job.get('title', '')
    if title:
        # Remove @username mentions
        title = re.sub(r'@\w+', '', title)
        # Remove common prefixes
        for prefix in ['URGENTLY', 'WE\'RE', 'HIRING', 'VACANCY', 'JOB', 'POSITION']:
            title = title.replace(prefix, '').strip(' !:')
        job['title'] = title.strip() or 'Job Opportunity'
    
    return job


def enhanced_scrape_telegram():
    """Wrapper for telegram scraper with link extraction"""
    try:
        print(f"  📡 Scraping Telegram...")
        jobs = scrape_telegram_channels()
        
        if not jobs:
            print(f"     ⚠️ No jobs found")
            return []
        
        print(f"     📥 Found {len(jobs)} raw messages")
        
        enhanced_jobs = []
        for job in jobs:
            enhanced = enhance_telegram_job(job)
            enhanced_jobs.append(enhanced)
        
        # Count jobs with external links
        with_links = sum(1 for j in enhanced_jobs if not j.get('_no_external_link'))
        print(f"     ✅ {with_links}/{len(enhanced_jobs)} have external job links")
        
        return enhanced_jobs
        
    except Exception as e:
        print(f"     ❌ Telegram FAILED: {e}")
        return []


def run():
    print(f"🚀 Halal Jobs Bot — {datetime.now().strftime('%d %b %Y %H:%M')} WAT")
    print(f"📍 Extracting REAL job application links from Telegram\n")

    seen_jobs = set(load_json(SEEN_JOBS_FILE, []))
    health    = load_json(HEALTH_FILE, {})
    history   = load_json(STATS_FILE, [])

    print(f"📦 Already seen: {len(seen_jobs)} jobs\n")

    scrapers = [
         
        #Working Update (kept for reference)
        
        #("WeWorkRemotely", scrape_weworkremotely),
        #("Himalayas",      scrape_himalayas),
        
        # Global Remote
        #("RemoteOK",       scrape_remoteok),
        #("Remotive",       scrape_remotive),
        #("TheMuse",        scrape_themuse),
        #("WeWorkRemotely+",    scrape_wwr_enhanced),
        #("WFH.io",             scrape_wfh_io),
        
        #("WorkingNomads",  scrape_workingnomads),
        #("Braintrust",     scrape_braintrust),
        #("Virtustant",     scrape_virtustant),
        #("Jobicy",         scrape_jobicy),
        
        # Nigeria-specific
        #("Jobberman",      scrape_jobberman),
        #("MyJobMag",       scrape_myjobmag),
        #("NGCareers",      scrape_ngcareers),
        #("JobGurus",       scrape_jobgurus),
        
        # International / NGO / Africa
        #("NGO / UN Jobs",  scrape_ngo_jobs),
        #("Africa Jobs",    scrape_africa_jobs),
        
        # Social Media - Using enhanced wrapper
        ("Telegram",       enhanced_scrape_telegram),
        
        #SUSPENDED (kept for reference)
        #("Pangaea",            scrape_pangaea),
        #("RelocateMe",         scrape_relocate_me),
        #("Remoters",           scrape_remoters),
        #("LinkedIn RSS",   scrape_linkedin_rss),
        #("EuropeRemote",       scrape_europeremote),
        #("Doballi",        scrape_doballi),
    ]

    all_jobs      = []
    source_counts = {}

    for name, scraper in scrapers:
        try:
            jobs = scraper()
            count = len(jobs)
            print(f"     ✅ Found {count} jobs")
            all_jobs.extend(jobs)
            source_counts[name] = count
            health = update_health(health, name, success=True)
            time.sleep(0.5)  # Small delay between scrapers
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")
            health = update_health(health, name, success=False)
            source_counts[name] = 0

    # Filter out jobs without external links
    valid_jobs = [j for j in all_jobs if not j.get('_no_external_link')]
    skipped_no_links = len(all_jobs) - len(valid_jobs)
    
    print(f"\n📋 Total collected: {len(all_jobs)}")
    print(f"   🔗 With external links: {len(valid_jobs)}")
    print(f"   🚫 Skipped (no links): {skipped_no_links}")

    new_count      = 0
    skipped_seen   = 0
    skipped_filter = 0
    failed_send    = 0

    for job in valid_jobs:
        # Create unique job ID based on URL or title
        job_url = job.get('url', '')
        if job_url:
            job_id = f"{job_url}"
        else:
            job_id = f"{job.get('title','')}_{job.get('company','')}"
        job_id = re.sub(r'[^a-zA-Z0-9_]', '_', job_id)[:200]

        if job_id in seen_jobs:
            skipped_seen += 1
            continue

        if not is_halal(job):
            skipped_filter += 1
            # Don't add filtered jobs to seen to allow re-scanning
            continue

        try:
            send_job(job)
            seen_jobs.add(job_id)
            new_count += 1
            time.sleep(0.5)  # Delay between sends to avoid rate limits
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
        "no_links":      skipped_no_links,
        "sources":       len(scrapers),
        "source_counts": source_counts,
    }
    history.append(stats)
    save_json(STATS_FILE, history[-500:])

    current_hour = datetime.now().hour
    if new_count > 0 or current_hour in [7, 13, 19]:
        send_stats(stats)

    print(f"\n✅ Done!")
    print(f"   📨 Sent:         {new_count}")
    print(f"   🚫 Filtered:     {skipped_filter}")
    print(f"   👁️  Already seen: {skipped_seen}")
    print(f"   ❌ Failed:       {failed_send}")
    print(f"   🔗 No links:     {skipped_no_links}")


if __name__ == "__main__":
    run()
