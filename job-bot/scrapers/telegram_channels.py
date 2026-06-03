"""
telegram_channels.py — Scrapes job posts from public Telegram channels
UPDATED: Removed channels with link issues
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
    # "JobsinNigeriadaily",  # REMOVED - link extraction issues
    # "jobsnigeria001rekrutconsulting",  # REMOVED - link extraction issues
    "WorkaNigeria",
    "remotejobss",
    "techjobsworld",
    "dixcoverhub",
]

# Common job application domains (prioritize these)
JOB_DOMAINS = [
    'linkedin.com',
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
    'docs.google.com',
    'airtable.com',
    'typeform.com',
    'greenhouse.io',
    'lever.co',
    'workable.com',
    'bamboohr.com',
    'ellamanager.com',
]


def clean_url(url: str) -> str:
    """
    Clean URL by removing ONLY obvious garbage at the end.
    Does NOT remove actual URL path characters.
    """
    if not url:
        return url
    
    # Remove trailing parentheses with common words (Follow), (Apply)
    url = re.sub(r'\s*\(Follow\)\s*$', '', url)
    url = re.sub(r'\s*\(Apply\)\s*$', '', url)
    url = re.sub(r'\s*\(Apply Now\)\s*$', '', url)
    url = re.sub(r'\s*\(Click\)\s*$', '', url)
    url = re.sub(r'\s*\(Link\)\s*$', '', url)
    
    # Remove trailing dashes with common words
    url = re.sub(r'\s*[-–—]+\s*Follow\s*$', '', url, flags=re.IGNORECASE)
    url = re.sub(r'\s*[-–—]+\s*Apply\s*$', '', url, flags=re.IGNORECASE)
    url = re.sub(r'\s*[-–—]+\s*Click\s*$', '', url, flags=re.IGNORECASE)
    
    # Remove standalone words at the end
    url = re.sub(r'\s+Follow$', '', url, flags=re.IGNORECASE)
    url = re.sub(r'\s+Apply$', '', url, flags=re.IGNORECASE)
    url = re.sub(r'\s+Click$', '', url, flags=re.IGNORECASE)
    url = re.sub(r'\s+Here$', '', url, flags=re.IGNORECASE)
    
    # Remove trailing spaces and punctuation
    url = url.rstrip(' .,!?;:')
    
    return url


def extract_external_links(text: str) -> list:
    """
    Extract actual job application links from message text.
    Filters out Telegram internal links and returns real job URLs.
    """
    if not text:
        return []
    
    # Find all URLs in the text - match until space or newline or end of line
    url_pattern = r'https?://[^\s\n]+'
    all_urls = re.findall(url_pattern, text)
    
    external_links = []
    
    for url in all_urls:
        # Clean the URL
        url = clean_url(url)
        
        if not url:
            continue
            
        # Skip Telegram internal links
        is_telegram = False
        telegram_domains = ['t.me', 'telegram.me', 'telegram.dog', 'telegra.ph']
        for tg_domain in telegram_domains:
            if tg_domain in url.lower():
                is_telegram = True
                break
        
        if not is_telegram:
            if url.startswith('http') and len(url) > 10:
                external_links.append(url)
    
    # Remove duplicates
    seen = set()
    unique_links = []
    for link in external_links:
        if link not in seen:
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
    whatsapp_pattern = r'https?://(?:chat\.whatsapp\.com|wa\.me|api\.whatsapp\.com)[^\s\n]+'
    whatsapp_links = re.findall(whatsapp_pattern, text)
    return whatsapp_links


def is_job_application_link(url: str) -> bool:
    """Check if a URL is a job application link"""
    url_lower = url.lower()
    
    for domain in JOB_DOMAINS:
        if domain in url_lower:
            return True
    
    job_patterns = [
        '/jobs/', '/careers/', '/apply/', '/position/',
        '/vacancy/', '/opportunity/', '/recruitment/',
        '/candidate/', '/job/', 'job-apply', 'applynow',
    ]
    
    for pattern in job_patterns:
        if pattern in url_lower:
            return True
    
    return False


def get_best_application_link(external_links: list, emails: list, whatsapp_links: list) -> str:
    """Determine the best application link/method"""
    for link in external_links:
        if is_job_application_link(link):
            return link
    
    if external_links:
        return external_links[0]
    
    if emails:
        return f"mailto:{emails[0]}"
    
    if whatsapp_links:
        return whatsapp_links[0]
    
    return None


def extract_application_method(text: str) -> dict:
    """Extract all application methods from message text"""
    result = {
        'url': None,
        'emails': [],
        'whatsapp': [],
        'all_links': [],
    }
    
    external_links = extract_external_links(text)
    result['all_links'] = external_links
    result['emails'] = extract_email(text)
    result['whatsapp'] = extract_whatsapp_link(text)
    result['url'] = get_best_application_link(external_links, result['emails'], result['whatsapp'])
    
    return result


def scrape_channel(channel_username: str, limit: int = 20) -> list:
    """Scrape job posts from a single Telegram channel"""
    jobs = []
    
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
        messages = soup.find_all('div', class_='tgme_widget_message')
        
        for msg in messages[:limit]:
            try:
                text_elem = msg.find('div', class_='tgme_widget_message_text')
                if not text_elem:
                    continue
                
                message_text = text_elem.get_text()
                
                if len(message_text) < 30:
                    continue
                
                app_method = extract_application_method(message_text)
                
                message_id = msg.get('data-post')
                if message_id:
                    parts = message_id.split('/')
                    if len(parts) >= 2:
                        message_id = parts[-1]
                
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
                continue
                
    except Exception as e:
        print(f"     ❌ Error scraping {channel_username}: {e}")
    
    return jobs


def extract_job_title(text: str) -> str:
    """Extract job title from message - be more aggressive"""
    lines = text.split('\n')
    
    # First, look for common job title patterns
    patterns = [
        r'(?:We\'re|We are|We need a|Looking for a|Hiring a|Now hiring:?)\s+([A-Za-z\s/]+?)(?:\n|$|\.)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Manager|Officer|Assistant|Coordinator|Specialist|Analyst|Developer|Engineer))',
        r'(JOB TITLE:|POSITION:|ROLE:|VACANCY:?)\s*([A-Za-z\s/]+?)(?:\n|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            title = match.group(1) if len(match.groups()) > 0 else match.group(0)
            title = title.strip()
            if len(title) > 5 and len(title) < 100:
                return title
    
    # If no pattern matches, look for the first line that isn't an @mention or link
    for line in lines[:5]:
        line = line.strip()
        # Skip empty lines, mentions, and URLs
        if line and not line.startswith('@') and not line.startswith('http') and len(line) > 5 and len(line) < 150:
            # Remove common prefixes
            cleaned = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|JOB|POSITION|NOW HIRING|🚨|🔥|💼)[:\s]+', '', line, flags=re.IGNORECASE)
            cleaned = re.sub(r'@\w+', '', cleaned)
            
            # Check if it looks like a job title (contains job-related words)
            job_words = ['hiring', 'vacancy', 'position', 'officer', 'manager', 'assistant', 'developer', 'engineer', 'analyst', 'specialist']
            if any(word in cleaned.lower() for word in job_words):
                return cleaned[:100]
    
    # Last resort: check if the message itself is short and likely a title
    first_line = lines[0].strip() if lines else ""
    if first_line and len(first_line) < 100 and len(first_line) > 5:
        return first_line[:100]
    
    return "Job Opportunity"


def extract_company(text: str) -> str:
    """Extract company name from message"""
    patterns = [
        r'(?:at|@|company:?\s+)([A-Z][a-zA-Z0-9\s&]+?)(?:\s+[Ii]n|\s+[Ll]ocated|\||$|\.|\,|$)',
        r'via\s+@(\w+)',
        r'([A-Z][a-zA-Z0-9\s&]+?)\s+(?:is hiring|is recruiting)',
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
        r'(remote|worldwide|global|anywhere|nigeria|lagos|abuja)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1) if match.groups() else match.group(0)
            if 'remote' in location.lower():
                return "Remote"
            elif 'worldwide' in location.lower():
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
        print(f"           Found {len(jobs)} jobs")
    
    return all_jobs


if __name__ == "__main__":
    jobs = scrape_telegram_channels()
    print(f"\n✅ Total jobs found: {len(jobs)}")
    for job in jobs[:3]:
        print(f"\n📋 {job['title']}")
        print(f"   🔗 {job['url']}")
