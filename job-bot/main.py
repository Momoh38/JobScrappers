"""
main.py — Entry point for Job Scraper Bot
UPDATED: All job sources enabled, monthly stats only
"""

import json
import os
import re
import time
from datetime import datetime

# --- Global Remote (API-based, most reliable) ---
from scrapers.remoteok        import scrape_remoteok
from scrapers.remotive        import scrape_remotive
from scrapers.themuse         import scrape_themuse
from scrapers.workingnomads   import scrape_workingnomads
from scrapers.braintrust      import scrape_braintrust
from scrapers.virtustant      import scrape_virtustant
# from scrapers.jobicy          import scrape_jobicy  # REMOVED - poor filtering
from scrapers.weworkremotely  import scrape_weworkremotely
from scrapers.we_work_remotely_enhanced import scrape_wwr_enhanced
from scrapers.wfh_io            import scrape_wfh_io
from scrapers.himalayas       import scrape_himalayas


# --- Nigeria-specific ---
from scrapers.jobberman       import scrape_jobberman
from scrapers.myjobmag        import scrape_myjobmag
from scrapers.ngcareers       import scrape_ngcareers
from scrapers.jobgurus        import scrape_jobgurus

# --- International / NGO / Africa ---
from scrapers.ngo_jobs        import scrape_ngo_jobs
from scrapers.africa_jobs     import scrape_africa_jobs

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
# from scrapers.doballi        import scrape_doballi
# from scrapers.pangaea        import scrape_pangaea
# from scrapers.relocate_me    import scrape_relocate_me
# from scrapers.remoters       import scrape_remoters
# from scrapers.linkedin_rss   import scrape_linkedin_rss


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


def extract_external_job_links(text: str) -> list:
    """Extract actual job application links from text"""
    url_pattern = r'https?://[^\s<>"\')\]]+'
    all_links = re.findall(url_pattern, text)
    
    telegram_domains = ['t.me', 'telegram.me', 'telegram.dog', 'telegra.ph']
    
    external_links = []
    
    for link in all_links:
        link = link.rstrip('.,!?;:)]')
        is_telegram = any(tg_domain in link.lower() for tg_domain in telegram_domains)
        
        if not is_telegram and link.startswith('http'):
            external_links.append(link)
    
    # Remove duplicates
    seen = set()
    unique_links = []
    for link in external_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links


def remove_links_from_text(text: str) -> str:
    """Remove all URLs from text"""
    if not text:
        return text
    text = re.sub(r'https?://[^\s<>"\')\]]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_job_description(text: str, job_links: list) -> str:
    """Extract job description by removing links"""
    if not text:
        return "Click the 'Apply Now' button below for more details about this position."
    
    description = text
    
    for link in job_links:
        description = description.replace(link, '')
    
    description = re.sub(r'https?://[^\s<>"\')\]]+', '', description)
    description = re.sub(r'@\w+', '', description)
    description = re.sub(r'\n\s*\n', '\n\n', description)
    description = re.sub(r' +', ' ', description)
    description = description.strip()
    
    prefixes_to_remove = [
        'Job posting:', 'Description:', 'Job description:',
        'Apply here:', 'Link:', 'URL:', 'Click here:'
    ]
    for prefix in prefixes_to_remove:
        if description.lower().startswith(prefix.lower()):
            description = description[len(prefix):].strip()
    
    if not description or len(description) < 10:
        description = "🔗 Click the 'Apply Now' button below to view full job details and submit your application."
    
    return description


def extract_title_from_message(text: str) -> str:
    """Extract clean title without links"""
    if not text:
        return "Job Opportunity"
    
    text_without_links = remove_links_from_text(text)
    lines = text_without_links.split('\n')
    
    for line in lines[:5]:
        line = line.strip()
        if line and not line.startswith('@'):
            cleaned = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|JOB|POSITION|NOW HIRING|🚨|🔥|💼)[:\s]+', '', line, flags=re.IGNORECASE)
            cleaned = re.sub(r'@\w+', '', cleaned)
            cleaned = cleaned.strip()
            
            if cleaned and not cleaned.startswith('http') and len(cleaned) > 5 and len(cleaned) < 200:
                if re.search(r'[a-zA-Z]', cleaned):
                    return cleaned
    
    for line in lines[:3]:
        line = line.strip()
        line_without_links = remove_links_from_text(line)
        if line_without_links and len(line_without_links) > 3 and re.search(r'[a-zA-Z]', line_without_links):
            return line_without_links[:100]
    
    return "New Job Opportunity"


def extract_company_from_message(text: str) -> str:
    """Extract company name"""
    if not text:
        return "Not specified"
    
    text = remove_links_from_text(text)
    
    patterns = [
        r'(?:at|@|company:?\s+)([A-Z][a-zA-Z0-9\s&]+?)(?:\s+[Ii]n|\s+[Ll]ocated|\||$|\.|\,)',
        r'(?:hiring|recruiting)[:\s]+(?:a[n]?\s+)?(?:[A-Z][a-z]+\s+)?([A-Z][a-zA-Z0-9\s&]+?)(?:\s+is|\s+are|\n)',
        r'via\s+@(\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) < 50 and len(company) > 2:
                company = re.sub(r'[^\w\s@&-]', '', company)
                return company
    
    return "Not specified"


def enhance_telegram_job(job: dict) -> dict:
    """Enhance Telegram job with proper links and description"""
    raw_text = job.get('description', '') or job.get('title', '')
    job_links = extract_external_job_links(raw_text)
    description = extract_job_description(raw_text, job_links)
    title = extract_title_from_message(raw_text)
    company = extract_company_from_message(raw_text)
    
    title = remove_links_from_text(title)
    
    if (not title or title == "Job Opportunity" or len(title) < 3) and job_links:
        title = "New Job Opportunity"
    
    enhanced_job = {
        'title': title,
        'company': company,
        'description': description,
        'location': job.get('location', 'Remote'),
        'salary': job.get('salary', ''),
        'tags': job.get('tags', ''),
        'source': f"Telegram: {job.get('source_group', 'Jobs Group')}",
        'url': job_links[0] if job_links else None,
        'job_links': job_links,
        'date_posted': job.get('date_posted', datetime.now().isoformat()),
        'message_id': job.get('message_id'),
        'source_group': job.get('source_group'),
    }
    
    for key, value in job.items():
        if key not in enhanced_job and key not in ['_no_external_link']:
            enhanced_job[key] = value
    
    if not job_links:
        enhanced_job['_no_external_link'] = True
        print(f"     ⚠️ No external link found - will skip")
    else:
        print(f"     🔗 Found link: {job_links[0][:60]}...")
        print(f"     📝 Clean Title: {title[:50]}")
    
    return enhanced_job


def enhanced_scrape_telegram():
    """Wrapper for telegram scraper"""
    try:
        print(f"  📡 Scraping Telegram...")
        jobs = scrape_telegram_channels()
        
        if not jobs:
            print(f"     ⚠️ No jobs found")
            return []
        
        print(f"     📥 Found {len(jobs)} raw messages")
        
        enhanced_jobs = []
        skipped_no_link = 0
        
        for job in jobs:
            enhanced = enhance_telegram_job(job)
            if enhanced.get('_no_external_link'):
                skipped_no_link += 1
            else:
                enhanced_jobs.append(enhanced)
        
        print(f"     ✅ {len(enhanced_jobs)} jobs with valid external links")
        print(f"     ⚠️ {skipped_no_link} jobs skipped (no external link found)")
        
        if enhanced_jobs:
            sample = enhanced_jobs[0]
            print(f"     📋 Sample: {sample.get('title', 'N/A')[:50]}")
        
        return enhanced_jobs
        
    except Exception as e:
        print(f"     ❌ Telegram FAILED: {e}")
        return []


def run():
    print(f"🚀 Job Scraper Bot — {datetime.now().strftime('%d %b %Y %H:%M')} WAT")
    print(f"📍 Scanning {len(scrapers)} job sources\n")

    seen_jobs = set(load_json(SEEN_JOBS_FILE, []))
    health    = load_json(HEALTH_FILE, {})
    history   = load_json(STATS_FILE, [])

    print(f"📦 Already seen: {len(seen_jobs)} jobs\n")

    # ALL SCRAPERS ENABLED (17 sources)
    scrapers = [
        # Global Remote
        ("RemoteOK",            scrape_remoteok),
        ("Remotive",            scrape_remotive),
        ("TheMuse",             scrape_themuse),
        ("WorkingNomads",       scrape_workingnomads),
        ("Braintrust",          scrape_braintrust),
        ("Virtustant",          scrape_virtustant),
        # ("Jobicy",            scrape_jobicy),  # REMOVED
        ("WeWorkRemotely",      scrape_weworkremotely),
        ("WeWorkRemotely+",     scrape_wwr_enhanced),
        ("WFH.io",              scrape_wfh_io),
        ("Himalayas",           scrape_himalayas),
        
        # Nigeria-specific
        ("Jobberman",           scrape_jobberman),
        ("MyJobMag",            scrape_myjobmag),
        ("NGCareers",           scrape_ngcareers),
        ("JobGurus",            scrape_jobgurus),
        
        # International / NGO / Africa
        ("NGO / UN Jobs",       scrape_ngo_jobs),
        ("Africa Jobs",         scrape_africa_jobs),
        
        # Social Media (Enhanced)
        ("Telegram",            enhanced_scrape_telegram),
    ]

    all_jobs      = []
    source_counts = {}

    for name, scraper in scrapers:
        try:
            print(f"  📡 Scraping {name}...")
            jobs = scraper()
            count = len(jobs)
            print(f"     ✅ Found {count} jobs")
            all_jobs.extend(jobs)
            source_counts[name] = count
            health = update_health(health, name, success=True)
            time.sleep(1)
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")
            health = update_health(health, name, success=False)
            source_counts[name] = 0

    print(f"\n📋 Total collected: {len(all_jobs)}")

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
        "sources":       len(scrapers),
        "source_counts": source_counts,
    }
    history.append(stats)
    save_json(STATS_FILE, history[-500:])

    # Send monthly stats (only on the 1st of each month)
    send_stats(stats)

    print(f"\n✅ Done!")
    print(f"   📨 Sent:         {new_count}")
    print(f"   🚫 Filtered:     {skipped_filter}")
    print(f"   👁️  Already seen: {skipped_seen}")
    print(f"   ❌ Failed:       {failed_send}")
    
    print(f"\n📊 Scraper Health Summary:")
    working = []
    failed = []
    for name, h in health.items():
        if h.get('failures', 0) >= 2:
            failed.append(name)
        else:
            working.append(name)
    
    print(f"   ✅ Working ({len(working)}): {', '.join(working[:5])}{'...' if len(working) > 5 else ''}")
    if failed:
        print(f"   ❌ Failed ({len(failed)}): {', '.join(failed)}")


if __name__ == "__main__":
    run()
