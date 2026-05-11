"""
main.py — Entry point for Halal Jobs Bot
UPDATED: Removes links from title field
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
from scrapers.jobicy          import scrape_jobicy
from scrapers.weworkremotely  import scrape_weworkremotely
from scrapers.we_work_remotely_enhanced import scrape_wwr_enhanced
from scrapers.wfh_io            import scrape_wfh_io
from scrapers.himalayas       import scrape_himalayas


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
#from scrapers.remoters          import scrape_remoters (Not useful)
#from scrapers.linkedin_rss    import scrape_linkedin_rss


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
    """
    Extract actual job application links from text.
    Filters out Telegram internal links.
    """
    # Pattern to find all URLs
    url_pattern = r'https?://[^\s<>"\')\]]+'
    all_links = re.findall(url_pattern, text)
    
    # Domains to filter out (Telegram internal)
    telegram_domains = ['t.me', 'telegram.me', 'telegram.dog', 'telegra.ph']
    
    external_links = []
    
    for link in all_links:
        # Clean up link
        link = link.rstrip('.,!?;:)]')
        
        # Skip Telegram internal links
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
    
    # Remove URLs
    text = re.sub(r'https?://[^\s<>"\')\]]+', '', text)
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def extract_job_description(text: str, job_links: list) -> str:
    """
    Extract the actual job description by removing the job links from the text.
    If description is empty or too short, returns a placeholder.
    """
    if not text:
        return "Click the 'Apply Now' button below for more details about this position."
    
    description = text
    
    # Remove all job links from the description
    for link in job_links:
        description = description.replace(link, '')
    
    # Remove any URLs (in case any were missed)
    description = re.sub(r'https?://[^\s<>"\')\]]+', '', description)
    
    # Remove any leftover Telegram group mentions
    description = re.sub(r'@\w+', '', description)
    
    # Clean up excessive whitespace
    description = re.sub(r'\n\s*\n', '\n\n', description)
    description = re.sub(r' +', ' ', description)
    description = description.strip()
    
    # Remove common prefixes
    prefixes_to_remove = [
        'Job posting:', 'Description:', 'Job description:',
        'Apply here:', 'Link:', 'URL:', 'Click here:'
    ]
    for prefix in prefixes_to_remove:
        if description.lower().startswith(prefix.lower()):
            description = description[len(prefix):].strip()
    
    # If description is empty or too short, provide placeholder
    if not description or len(description) < 10:
        description = "🔗 Click the 'Apply Now' button below to view full job details and submit your application."
    
    return description


def extract_title_from_message(text: str) -> str:
    """Extract a clean title from the message - WITHOUT any links"""
    if not text:
        return "Job Opportunity"
    
    # First, remove all links from the text
    text_without_links = remove_links_from_text(text)
    
    lines = text_without_links.split('\n')
    
    # Look for the first meaningful line that's not a link or mention
    for line in lines[:5]:
        line = line.strip()
        # Skip empty lines, mentions
        if line and not line.startswith('@'):
            # Remove common prefixes
            cleaned = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|JOB|POSITION|NOW HIRING|🚨|🔥|💼)[:\s]+', '', line, flags=re.IGNORECASE)
            cleaned = re.sub(r'@\w+', '', cleaned)
            cleaned = cleaned.strip()
            
            # Make sure it's not a URL (just in case)
            if cleaned and not cleaned.startswith('http') and len(cleaned) > 5 and len(cleaned) < 200:
                # Check if it has meaningful words (not just symbols)
                if re.search(r'[a-zA-Z]', cleaned):
                    return cleaned
    
    # If no good title found, try to use the first line that contains letters
    for line in lines[:3]:
        line = line.strip()
        line_without_links = remove_links_from_text(line)
        if line_without_links and len(line_without_links) > 3 and re.search(r'[a-zA-Z]', line_without_links):
            return line_without_links[:100]
    
    return "New Job Opportunity"


def extract_company_from_message(text: str) -> str:
    """Extract company name from message"""
    if not text:
        return "Not specified"
    
    # Remove links first
    text = remove_links_from_text(text)
    
    # Look for common patterns
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
                # Clean up any remaining special characters
                company = re.sub(r'[^\w\s@&-]', '', company)
                return company
    
    return "Not specified"


def enhance_telegram_job(job: dict) -> dict:
    """
    Enhance a Telegram job by properly separating:
    - Job description (the actual details)
    - Application link (the URL to apply)
    - NEVER skips jobs with valid links
    """
    # Get the raw message content
    raw_text = job.get('description', '') or job.get('title', '')
    
    # Extract external job links (the actual application URLs)
    job_links = extract_external_job_links(raw_text)
    
    # Extract the actual job description (remove links)
    description = extract_job_description(raw_text, job_links)
    
    # Extract title and company (with links removed)
    title = extract_title_from_message(raw_text)
    company = extract_company_from_message(raw_text)
    
    # Double-check title doesn't contain any links
    title = remove_links_from_text(title)
    
    # If we have no title but have a link, create a generic title
    if (not title or title == "Job Opportunity" or len(title) < 3) and job_links:
        title = "New Job Opportunity"
    
    # Enhance the job object
    enhanced_job = {
        'title': title,
        'company': company,
        'description': description,  # This is the actual job details text
        'location': job.get('location', 'Remote'),
        'salary': job.get('salary', ''),
        'tags': job.get('tags', ''),
        'source': f"Telegram: {job.get('source_group', 'Jobs Group')}",
        'url': job_links[0] if job_links else None,  # The application link
        'job_links': job_links,
        'date_posted': job.get('date_posted', datetime.now().isoformat()),
        'message_id': job.get('message_id'),
        'source_group': job.get('source_group'),
    }
    
    # Copy any existing fields we might have missed
    for key, value in job.items():
        if key not in enhanced_job and key not in ['_no_external_link']:
            enhanced_job[key] = value
    
    # Mark if no external link found (these will be skipped)
    if not job_links:
        enhanced_job['_no_external_link'] = True
        print(f"     ⚠️ No external link found - will skip")
    else:
        print(f"     🔗 Found link: {job_links[0][:60]}...")
        print(f"     📝 Clean Title: {title[:50]}")
        desc_preview = description[:60] + "..." if len(description) > 60 else description
        print(f"     📝 Description preview: {desc_preview}")
    
    return enhanced_job


def enhanced_scrape_telegram():
    """Wrapper for telegram scraper with link extraction - NEVER SKIPS VALID JOBS"""
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
            # Only skip jobs that have NO external link at all
            if enhanced.get('_no_external_link'):
                skipped_no_link += 1
            else:
                enhanced_jobs.append(enhanced)
        
        print(f"     ✅ {len(enhanced_jobs)} jobs with valid external links")
        print(f"     ⚠️ {skipped_no_link} jobs skipped (no external link found)")
        
        # Show sample of first job
        if enhanced_jobs:
            sample = enhanced_jobs[0]
            print(f"     📋 Sample job:")
            print(f"        Title: {sample.get('title', 'N/A')[:50]}")
            print(f"        Link: {sample.get('url', 'N/A')[:60]}")
            print(f"        Description: {sample.get('description', '')[:80]}...")
        
        return enhanced_jobs
        
    except Exception as e:
        print(f"     ❌ Telegram FAILED: {e}")
        import traceback
        traceback.print_exc()
        return []


def run():
    print(f"🚀 Halal Jobs Bot — {datetime.now().strftime('%d %b %Y %H:%M')} WAT")
    print(f"📍 Extracting job descriptions and application links from Telegram\n")

    seen_jobs = set(load_json(SEEN_JOBS_FILE, []))
    health    = load_json(HEALTH_FILE, {})
    history   = load_json(STATS_FILE, [])

    print(f"📦 Already seen: {len(seen_jobs)} jobs\n")

    scrapers = [
        # Social Media - Using enhanced wrapper
        ("Telegram", enhanced_scrape_telegram),
        
        # Other scrapers are commented out as before
    ]

    all_jobs      = []
    source_counts = {}

    for name, scraper in scrapers:
        try:
            jobs = scraper()
            count = len(jobs)
            print(f"     ✅ Found {count} jobs with valid links")
            all_jobs.extend(jobs)
            source_counts[name] = count
            health = update_health(health, name, success=True)
            time.sleep(0.5)
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")
            health = update_health(health, name, success=False)
            source_counts[name] = 0

    print(f"\n📋 Total jobs with valid links: {len(all_jobs)}")

    new_count      = 0
    skipped_seen   = 0
    skipped_filter = 0
    failed_send    = 0

    for job in all_jobs:
        # Create unique job ID based on URL
        job_url = job.get('url', '')
        if not job_url:
            continue
            
        job_id = re.sub(r'[^a-zA-Z0-9_]', '_', job_url)[:200]

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

    current_hour = datetime.now().hour
    if new_count > 0 or current_hour in [7, 13, 19]:
        send_stats(stats)

    print(f"\n✅ Done!")
    print(f"   📨 Sent:         {new_count}")
    print(f"   🚫 Filtered:     {skipped_filter}")
    print(f"   👁️  Already seen: {skipped_seen}")
    print(f"   ❌ Failed:       {failed_send}")


if __name__ == "__main__":
    run()
