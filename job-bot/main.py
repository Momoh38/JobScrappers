"""
main.py — Entry point for Halal Jobs Bot
UPDATED: Extracts actual job application links from Telegram messages
"""

import json
import os
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

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
from sender import send_job, send_stats, send_alert

SEEN_JOBS_FILE = "seen_jobs.json"
HEALTH_FILE    = "scraper_health.json"
STATS_FILE     = "run_stats.json"

# Rate limiting for Telegram
SENT_COUNT = 0
MINUTE_START = time.time()
MAX_PER_MINUTE = 20


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
            send_alert(name, 3)
    return health


def extract_external_job_links(message_text: str) -> List[str]:
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
        'fiverr.com', 'peopleperhour.com', 'toptal.com', 'arc.dev',
        'jobberman.com', 'myjobmag.com', 'ngcareers.com', 'jobgurus.com.ng',
        'careers.', 'jobs.', 'apply.', 'hire.', 'recruitment.',
        'forms.gle', 'docs.google.com/forms',  # Google Forms applications
        'airtable.com', 'typeform.com',  # Common job application platforms
        'bamboohr.com', 'greenhouse.io', 'lever.co', 'workable.com',
        'jobs.', '/careers', '/apply', '/job', '/position', '/vacancy'
    ]
    
    external_links = []
    
    for link in all_links:
        # Clean up link (remove trailing punctuation)
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
        
        # Also accept any non-Telegram link as fallback
        if is_job_link or len(external_links) == 0:
            external_links.append(link)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in external_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links


def extract_job_details_from_message(message_text: str, original_title: str = '') -> dict:
    """
    Extract job details (title, company, location, etc.) from message content
    """
    details = {
        'title': original_title,
        'company': '',
        'location': 'Remote',
        'job_type': 'Full-time',
        'salary': '',
        'description': message_text[:500]
    }
    
    if not details['title'] or len(details['title']) < 5:
        # Try to extract title from first line or after common prefixes
        lines = message_text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                # Remove common prefixes
                cleaned = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|JOB|POSITION)[:\s]+', '', line, flags=re.IGNORECASE)
                cleaned = re.sub(r'@\w+', '', cleaned)  # Remove @mentions
                if cleaned and len(cleaned) > 3:
                    details['title'] = cleaned[:80]
                    break
    
    # Extract company (look for common patterns)
    company_patterns = [
        r'(?:at|@|company:?\s+)([A-Z][a-zA-Z0-9\s&]+?)(?:\s+[Ii]n|\s+[Ll]ocated|\||$)',
        r'(?:hiring|recruiting|looking for)[:\s]+(?:a[n]?\s+)?(?:[A-Z][a-z]+\s+)?([A-Z][a-zA-Z0-9\s&]+?)(?:\s+is|\s+are|\s+for|\s+to|\|)',
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) < 50 and len(company) > 2:
                details['company'] = company
                break
    
    # Extract location
    location_patterns = [
        r'(?:location|based|in|@)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?)',
        r'(?:remote|onsite|hybrid|in-office)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            loc = match.group(0) if len(match.groups()) == 0 else match.group(1)
            if 'remote' in loc.lower():
                details['location'] = 'Remote'
            elif 'hybrid' in loc.lower():
                details['location'] = 'Hybrid'
            elif 'onsite' in loc.lower() or 'in-office' in loc.lower():
                details['location'] = 'On-site'
            elif len(loc) < 30:
                details['location'] = loc.strip()
            break
    
    # Extract job type
    if 'remote' in message_text.lower():
        details['job_type'] = 'Remote'
    elif 'hybrid' in message_text.lower():
        details['job_type'] = 'Hybrid'
    elif 'contract' in message_text.lower():
        details['job_type'] = 'Contract'
    elif 'part' in message_text.lower() and 'time' in message_text.lower():
        details['job_type'] = 'Part-time'
    
    # Extract salary
    salary_patterns = [
        r'([N₦$€£][0-9,]+(?:\s*-\s*[N₦$€£]?[0-9,]+)?(?:\s*(?:per|/)\s*(?:month|year|annum|hour))?)',
        r'(?:salary|pay|compensation)[:\s]+([N₦$€£][0-9,]+[^\n]*)',
    ]
    
    for pattern in salary_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            details['salary'] = match.group(1 if match.groups() else 0).strip()[:50]
            break
    
    return details


def safe_format_message(job: dict) -> Tuple[str, str]:
    """Format job message safely without HTML/Markdown errors"""
    import html
    
    # Get job details
    title = job.get('title', 'Job Opportunity')[:100]
    company = job.get('company', 'Not specified')[:50]
    location = job.get('location', 'Not specified')[:50]
    job_type = job.get('job_type', 'Full-time')[:30]
    description = job.get('description', 'No description provided')[:500]
    salary = job.get('salary', '')[:100]
    
    # Get the actual job application link (external, not Telegram)
    job_links = job.get('job_links', [])
    if job_links:
        job_url = job_links[0]
    else:
        job_url = job.get('url', job.get('link', '#'))
    
    source = job.get('source', 'Telegram Jobs')
    
    # Clean description (remove excessive newlines and special chars)
    description = ' '.join(description.split())
    description = description[:400] + '...' if len(description) > 400 else description
    
    # Escape HTML special characters to prevent parse errors
    title = html.escape(title)
    company = html.escape(company)
    location = html.escape(location)
    job_type = html.escape(job_type)
    description = html.escape(description)
    salary = html.escape(salary)
    source = html.escape(source)
    job_url = html.escape(job_url)
    
    # Build message with HTML
    message_parts = [
        f"💼 <b>{title}</b>",
        "",
        f"🏢 <b>Company:</b> {company}",
        f"📍 <b>Location:</b> {location}",
        f"🔧 <b>Type:</b> {job_type}",
    ]
    
    if salary and salary != 'Not specified':
        message_parts.append(f"💰 <b>Salary:</b> {salary}")
    
    message_parts.extend([
        "",
        f"📝 <b>Description:</b>",
        f"{description}",
        "",
        f"🔗 <b>Apply Here:</b> <a href='{job_url}'>Click to Apply</a>",
        "",
        f"<code>Source: {source}</code>"
    ])
    
    message = '\n'.join(message_parts)
    
    return message, 'HTML'


def send_with_retry_and_throttle(bot_token: str, chat_id: str, message: str, parse_mode: str = 'HTML') -> bool:
    """Send Telegram message with rate limiting and retry logic"""
    global SENT_COUNT, MINUTE_START
    
    import requests
    
    current_time = time.time()
    
    # Reset counter every minute
    if current_time - MINUTE_START >= 60:
        SENT_COUNT = 0
        MINUTE_START = current_time
    
    # Check if we're at the limit
    if SENT_COUNT >= MAX_PER_MINUTE:
        wait_time = 60 - (current_time - MINUTE_START)
        if wait_time > 0:
            print(f"     ⏳ Rate limit reached. Waiting {wait_time:.1f}s...")
            time.sleep(wait_time + 1)
            SENT_COUNT = 0
            MINUTE_START = time.time()
    
    # Send with retry logic
    max_retries = 5
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False,  # Allow preview so users see the link domain
                'disable_notification': False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                SENT_COUNT += 1
                return True
            elif response.status_code == 429:
                error_data = response.json()
                retry_after = error_data.get('parameters', {}).get('retry_after', base_delay * (2 ** attempt))
                print(f"     ⚠️ Rate limited. Retry after {retry_after}s")
                time.sleep(retry_after)
            elif response.status_code == 400:
                error_data = response.json()
                if "can't parse entities" in str(error_data):
                    print(f"     ⚠️ Parse error, sending as plain text...")
                    payload['parse_mode'] = None
                    response = requests.post(url, json=payload, timeout=30)
                    if response.status_code == 200:
                        SENT_COUNT += 1
                        return True
                else:
                    print(f"     ⚠️ Telegram error: {error_data}")
                    return False
            else:
                print(f"     ⚠️ HTTP {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"     ⚠️ Timeout (attempt {attempt + 1})")
            time.sleep(base_delay * (2 ** attempt))
        except Exception as e:
            print(f"     ⚠️ Error: {e}")
            time.sleep(base_delay * (2 ** attempt))
    
    return False


def enhanced_send_job(job: dict):
    """Enhanced send with proper external links"""
    try:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHANNEL_ID')
        
        if bot_token and chat_id:
            message, parse_mode = safe_format_message(job)
            success = send_with_retry_and_throttle(bot_token, chat_id, message, parse_mode)
            
            # Log the link being sent for debugging
            if success and job.get('job_links'):
                print(f"     🔗 Link: {job['job_links'][0][:80]}...")
            
            return success
        else:
            return send_job(job)
    except Exception as e:
        print(f"     ⚠️ Failed to send job: {e}")
        return False


def enhanced_scrape_telegram_channels():
    """
    Enhanced wrapper that extracts actual external job links from messages
    """
    try:
        print("     🎯 Scraping Telegram channels for job posts...")
        jobs = scrape_telegram_channels()
        
        if not jobs:
            print("     ⚠️ No jobs found from Telegram scraper")
            return []
        
        print(f"     📥 Processing {len(jobs)} raw messages from Telegram")
        
        enhanced_jobs = []
        external_links_found = 0
        
        for job in jobs:
            # Get message content
            message_text = job.get('description', '')
            if not message_text:
                message_text = job.get('title', '')
            
            original_title = job.get('title', '')
            
            # Extract ACTUAL external job links from the message
            external_links = extract_external_job_links(message_text)
            
            if external_links:
                external_links_found += 1
                job['job_links'] = external_links
                job['url'] = external_links[0]  # Set primary URL to the external link
                print(f"     🔗 Found external link: {external_links[0][:60]}...")
            else:
                # No external links found - log for debugging
                print(f"     ⚠️ No external links in message from {job.get('source_group', 'unknown')}")
                # Skip jobs without external links
                continue
            
            # Extract additional job details from message
            job_details = extract_job_details_from_message(message_text, original_title)
            job.update(job_details)
            
            # Add source info
            job['source'] = f"Telegram: {job.get('source_group', 'Jobs Group')}"
            
            # Generate unique job ID based on the external link
            job['id'] = f"tg_{hash(job['url'])}"
            
            enhanced_jobs.append(job)
        
        print(f"     ✅ Extracted {len(enhanced_jobs)} jobs with external links (from {external_links_found} messages)")
        
        # Show sample of extracted links
        if enhanced_jobs:
            sample = enhanced_jobs[0]
            print(f"     📋 Sample: {sample.get('title', 'No title')[:50]} -> {sample.get('url', 'No URL')[:60]}")
        
        return enhanced_jobs
        
    except Exception as e:
        print(f"     ❌ Telegram scraper error: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_enhanced_scrapers():
    """Return list of scrapers with enhanced Telegram support"""
    scrapers = [
        
        #Working Update (kept as comments for reference)
        
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
        
        # Social Media - Enhanced version that extracts external links
        ("Telegram",       enhanced_scrape_telegram_channels),
        
        # SUSPENDED (kept for reference)
        #("Pangaea",            scrape_pangaea),
        #("RelocateMe",         scrape_relocate_me),
        #("Remoters",           scrape_remoters),
        #("LinkedIn RSS",   scrape_linkedin_rss),
        #("EuropeRemote",       scrape_europeremote),
        #("Doballi",        scrape_doballi),
    ]
    return scrapers


def run():
    print(f"🚀 Halal Jobs Bot — {datetime.now().strftime('%d %b %Y %H:%M')} WAT")
    print(f"📍 Extracting REAL job application links from Telegram messages\n")

    seen_jobs = set(load_json(SEEN_JOBS_FILE, []))
    health    = load_json(HEALTH_FILE, {})
    history   = load_json(STATS_FILE, [])

    print(f"📦 Already seen: {len(seen_jobs)} jobs\n")

    scrapers = get_enhanced_scrapers()

    all_jobs      = []
    source_counts = {}

    for name, scraper in scrapers:
        try:
            print(f"  📡 Scraping {name}...")
            jobs  = scraper()
            count = len(jobs)
            print(f"     ✅ Found {count} jobs with external links")
            
            all_jobs.extend(jobs)
            source_counts[name] = count
            health = update_health(health, name, success=True)
            
            # Add small delay between scrapers
            time.sleep(0.5)
            
        except Exception as e:
            print(f"     ❌ {name} FAILED: {e}")
            health = update_health(health, name, success=False)
            source_counts[name] = 0

    print(f"\n📋 Total jobs with valid external links: {len(all_jobs)}")

    new_count      = 0
    skipped_seen   = 0
    skipped_filter = 0
    failed_send    = 0
    no_links_count = 0

    for idx, job in enumerate(all_jobs):
        # Skip jobs without external links
        if not job.get('job_links') and not job.get('url'):
            no_links_count += 1
            continue
        
        # Create unique job ID based on the external link
        job_url = job.get('url', job.get('job_links', [''])[0])
        job_id = f"{job.get('title', '')}_{job_url}"
        job_id = re.sub(r'[^a-zA-Z0-9_]', '_', job_id)[:200]

        if job_id in seen_jobs:
            skipped_seen += 1
            continue

        # Apply halal filter
        if not is_halal(job):
            skipped_filter += 1
            continue

        try:
            success = enhanced_send_job(job)
            
            if success:
                seen_jobs.add(job_id)
                new_count += 1
            else:
                failed_send += 1
            
            # Add small delay between sends
            time.sleep(0.3)
            
        except Exception as e:
            failed_send += 1
            print(f"     ⚠️ Exception: {e}")

    # Save data
    save_json(SEEN_JOBS_FILE, list(seen_jobs))
    save_json(HEALTH_FILE, health)

    stats = {
        "timestamp":     datetime.now().isoformat(),
        "sent":          new_count,
        "filtered":      skipped_filter,
        "seen":          skipped_seen,
        "failed":        failed_send,
        "no_links":      no_links_count,
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
    print(f"   🔗 No links:     {no_links_count}")
    
    if new_count == 0 and all_jobs:
        print(f"\n⚠️ No jobs were sent but {len(all_jobs)} jobs were found.")
        print("   Check that the messages contain actual external job links.")


if __name__ == "__main__":
    run()
