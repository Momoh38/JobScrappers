"""
telegram_channels.py — Scrapes job posts from public Telegram channels
UPDATED: Better link extraction - removes trailing text like "(Follow)", "Apply", etc.
"""

import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# List of Telegram channels to scrape
TELEGRAM_JOB_CHANNELS = [
    "jbtoday",
    "jobnownigeria",
    "careermattersng",
    "jobnetworkng",
    "JobsinNigeriadaily",
    "jobsnigeria001rekrutconsulting",
    "WorkaNigeria",
    "remotejobss",
    "techjobsworld",
]

# Common job application domains (prioritize these)
JOB_DOMAINS = [
    'linkedin.com/jobs',
    'linkedin.com/company',
    'indeed.com',
    'glassdoor.com',
    'jobberman.com',
    'myjobmag.com',
    'ngcareers.com',
    'jobgurus.com.ng',
    'remoteok.com',
    'remotive.com',
    'weworkremotely.com',
    'workingnomads.com',
    'braintrust.com',
    'themuse.com',
    'himalayas.com',
    'wfh.io',
    'virtustant.com',
    'forms.gle',
    'docs.google.com/forms',
    'airtable.com',
    'typeform.com',
    'greenhouse.io',
    'lever.co',
    'workable.com',
    'bamboohr.com',
    'apply.workable.com',
    'careers.',
    'jobs.',
    'apply.',
    'hire.',
    'ellamanager.com',  # Added from example
]


def clean_url(url: str) -> str:
    """
    Clean URL by removing trailing garbage like (Follow), (Apply), ---, etc.
    """
    if not url:
        return url
    
    # Remove trailing parentheses and their content like "(Follow)", "(Apply Now)"
    url = re.sub(r'\s*\([^)]*\)\s*$', '', url)
    
    # Remove trailing dashes/hyphens
    url = re.sub(r'\s*[-–—]+.*$', '', url)
    
    # Remove trailing words like "Follow", "Apply", "Click", "Here"
    url = re.sub(r'\s+(?:Follow|Apply|Click|Here|Link|Job|Position)\s*$', '', url, flags=re.IGNORECASE)
    
    # Remove any non-URL characters at the end
    url = re.sub(r'[^a-zA-Z0-9/:._-]+$', '', url)
    
    return url.strip()


def extract_external_links(text: str) -> list:
    """
    Extract actual job application links from message text.
    Filters out Telegram internal links and returns real job URLs.
    """
    if not text:
        return []
    
    # Find all URLs in the text
    url_pattern = r'https?://[^\s<>"\')\]]+'
    all_urls = re.findall(url_pattern, text)
    
    # Clean up URLs and remove trailing garbage
    cleaned_urls = []
    for url in all_urls:
        # Clean the URL
        url = clean_url(url)
        # Remove trailing punctuation
        url = url.rstrip('.,!?;:)]')
        if url and url.startswith('http'):
            cleaned_urls.append(url)
    
    # Also look for URLs that might have been split by newlines
    lines = text.split('\n')
    for line in lines:
        if 'http' in line:
            # Extract URL even if it has spaces around it
            urls_in_line = re.findall(r'https?://[^\s]+', line)
            for url in urls_in_line:
                url = clean_url(url)
                url = url.rstrip('.,!?;:)]')
                if url and url.startswith('http'):
                    cleaned_urls.append(url)
    
    # Filter out Telegram internal links
    external_links = []
    for url in cleaned_urls:
        is_telegram = False
        telegram_domains = ['t.me', 'telegram.me', 'telegram.dog', 'telegra.ph']
        for tg_domain in telegram_domains:
            if tg_domain in url.lower():
                is_telegram = True
                break
        
        if not is_telegram:
            external_links.append(url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in external_links:
        # Also validate the link looks like a real URL
        if link and link not in seen and len(link) > 10:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links


def extract_email(text: str) -> list:
    """Extract email addresses from text"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return list(set(emails))


def extract_whatsapp_link(text: str) -> list:
    """Extract WhatsApp links from text"""
    whatsapp_pattern = r'https?://(?:chat\.whatsapp\.com|wa\.me|api\.whatsapp\.com)[^\s<>"\')\]]+'
    whatsapp_links = re.findall(whatsapp_pattern, text)
    return [clean_url(link) for link in whatsapp_links]


def is_job_application_link(url: str) -> bool:
    """Check if a URL is a job application link (not just a company homepage)"""
    url_lower = url.lower()
    
    # Check if it matches known job domains
    for domain in JOB_DOMAINS:
        if domain in url_lower:
            return True
    
    # Check for job-related URL patterns
    job_patterns = [
        '/jobs/',
        '/careers/',
        '/apply/',
        '/position/',
        '/vacancy/',
        '/opportunity/',
        '/recruitment/',
        '/candidate/',
        '/job/',
        'applynow',
        'careers',
        'job-apply',  # Added for ellamanager.com style
    ]
    
    for pattern in job_patterns:
        if pattern in url_lower:
            return True
    
    return False


def get_best_application_link(external_links: list, emails: list, whatsapp_links: list) -> str:
    """
    Determine the best application link/method from available options.
    Priority: Job application URLs > Emails > WhatsApp > Other links
    """
    # First, look for job application specific URLs
    for link in external_links:
        if is_job_application_link(link):
            return link
    
    # Second, return any external link
    if external_links:
        return external_links[0]
    
    # Third, return email (user can copy)
    if emails:
        return f"mailto:{emails[0]}"
    
    # Fourth, return WhatsApp link
    if whatsapp_links:
        return whatsapp_links[0]
    
    return None


def extract_application_method(text: str) -> dict:
    """
    Extract all application methods from message text.
    Returns dict with URL, email, WhatsApp, etc.
    """
    result = {
        'url': None,
        'emails': [],
        'whatsapp': [],
        'all_links': [],
    }
    
    # Extract all external links
    external_links = extract_external_links(text)
    result['all_links'] = external_links
    
    # Extract emails
    emails = extract_email(text)
    result['emails'] = emails
    
    # Extract WhatsApp links
    whatsapp = extract_whatsapp_link(text)
    result['whatsapp'] = whatsapp
    
    # Get best application link
    result['url'] = get_best_application_link(external_links, emails, whatsapp)
    
    return result


def scrape_channel(channel_username: str, limit: int = 20) -> list:
    """
    Scrape job posts from a single Telegram channel using public web preview.
    Returns list of job dictionaries.
    """
    jobs = []
    
    # Use Telegram's public web interface
    url = f"https://t.me/s/{channel_username}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"     ⚠️ Cannot access channel: {channel_username}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all message containers
        messages = soup.find_all('div', class_='tgme_widget_message')
        
        for msg in messages[:limit]:
            try:
                # Extract message text
                text_elem = msg.find('div', class_='tgme_widget_message_text')
                if not text_elem:
                    continue
                
                message_text = text_elem.get_text()
                
                # Skip very short messages (likely not job posts)
                if len(message_text) < 30:
                    continue
                
                # Extract application method
                app_method = extract_application_method(message_text)
                
                # Get message ID and link
                message_id = msg.get('data-post')
                if message_id:
                    parts = message_id.split('/')
                    if len(parts) >= 2:
                        message_id = parts[-1]
                
                # Only add if we have an application method
                if app_method['url']:
                    job = {
                        'title': extract_job_title(message_text),
                        'description': message_text,
                        'company': extract_company(message_text),
                        'location': extract_location(message_text),
                        'url': app_method['url'],
                        'all_links': app_method['all_links'],
                        'emails': app_method['emails'],
                        'whatsapp': app_method['whatsapp'],
                        'source_group': channel_username,
                        'source': f"Telegram: @{channel_username}",
                        'message_id': message_id,
                        'date_posted': datetime.now().isoformat(),
                        'tags': extract_tags(message_text),
                    }
                    jobs.append(job)
                    
            except Exception as e:
                print(f"     ⚠️ Error parsing message: {e}")
                continue
                
    except Exception as e:
        print(f"     ❌ Error scraping {channel_username}: {e}")
    
    return jobs


def extract_job_title(text: str) -> str:
    """Extract job title from message"""
    lines = text.split('\n')
    
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 5 and len(line) < 150:
            # Remove common prefixes
            cleaned = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|JOB|POSITION|NOW HIRING|🚨|🔥|💼)[:\s]+', '', line, flags=re.IGNORECASE)
            cleaned = re.sub(r'@\w+', '', cleaned)
            
            # Remove trailing follow/apply text
            cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', cleaned)
            cleaned = re.sub(r'\s*[-–—]+.*$', '', cleaned)
            
            # Check if it looks like a job title
            if len(cleaned) > 5 and len(cleaned) < 100:
                return cleaned[:100]
    
    return "Job Opportunity"


def extract_company(text: str) -> str:
    """Extract company name from message"""
    patterns = [
        r'(?:at|@|company:?\s+)([A-Z][a-zA-Z0-9\s&]+?)(?:\s+[Ii]n|\s+[Ll]ocated|\||$|\.|\,|$)',
        r'via\s+@(\w+)',
        r'([A-Z][a-zA-Z0-9\s&]+?)\s+(?:is hiring|is recruiting|is looking for)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) < 50 and len(company) > 2:
                return company
    
    return "Not specified"


def extract_location(text: str) -> str:
    """Extract location from message"""
    location_patterns = [
        r'(?:location|located|based|in|@)[:\s]+(\w+(?:\s+\w+)?(?:\s*,\s*\w+)?)',
        r'(remote|worldwide|global|anywhere|on-site|hybrid|onsite|nigeria|lagos|abuja)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1) if match.groups() else match.group(0)
            if 'remote' in location.lower():
                return "Remote"
            elif 'worldwide' in location.lower() or 'global' in location.lower():
                return "Remote (Worldwide)"
            elif len(location) < 50:
                return location.strip()
    
    return "Remote"


def extract_tags(text: str) -> str:
    """Extract hashtags as tags"""
    hashtags = re.findall(r'#(\w+)', text)
    if hashtags:
        return ', '.join(hashtags[:5])
    return ""


def scrape_telegram_channels():
    """Main function to scrape all Telegram channels"""
    all_jobs = []
    
    print(f"     📡 Scraping {len(TELEGRAM_JOB_CHANNELS)} Telegram channels...")
    
    for channel in TELEGRAM_JOB_CHANNELS:
        print(f"        → @{channel}")
        jobs = scrape_channel(channel, limit=15)
        all_jobs.extend(jobs)
        print(f"           Found {len(jobs)} jobs with valid application links")
    
    return all_jobs


# For testing
if __name__ == "__main__":
    jobs = scrape_telegram_channels()
    print(f"\n✅ Total jobs found: {len(jobs)}")
    for job in jobs[:3]:
        print(f"\n📋 {job['title']}")
        print(f"   🔗 {job['url']}")
        print(f"   📍 {job['location']}")
