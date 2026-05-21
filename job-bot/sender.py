"""
sender.py — Formats and sends job listings to Telegram.
UPDATED: Preserve original titles, only clean not replace
"""

import os
import requests
import time
import re
from datetime import datetime

# Rate limiting
_last_message_time = 0
MIN_MESSAGE_INTERVAL = 1.5
MAX_RETRIES = 3

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Nigerian states for location detection
NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe",
    "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara",
    "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau",
    "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "FCT", "Abuja",
]


def send_with_retry(url, payload, retry_count=0):
    """Send with retry for rate limiting"""
    global _last_message_time
    
    current_time = time.time()
    time_since_last = current_time - _last_message_time
    
    if time_since_last < MIN_MESSAGE_INTERVAL:
        time.sleep(MIN_MESSAGE_INTERVAL - time_since_last)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 429:
            error_data = response.json()
            retry_after = error_data.get('parameters', {}).get('retry_after', 5)
            print(f"     ⏳ Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after + 1)
            if retry_count < MAX_RETRIES:
                return send_with_retry(url, payload, retry_count + 1)
            return False
        
        if response.status_code == 200:
            _last_message_time = time.time()
            return True
        
        if response.status_code == 400 and "can't parse entities" in response.text:
            payload['parse_mode'] = None
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                _last_message_time = time.time()
                return True
        
        return False
        
    except Exception as e:
        print(f"     ⚠️ Send error: {e}")
        if retry_count < MAX_RETRIES:
            time.sleep(5)
            return send_with_retry(url, payload, retry_count + 1)
        return False


def clean_location(location: str) -> str:
    """Clean and standardize location"""
    if not location or location == "Not specified":
        return "Remote"
    
    location = str(location)
    
    # Remove URLs
    location = re.sub(r'https?://[^\s]+', '', location)
    
    # Check for Nigerian states
    for state in NIGERIAN_STATES:
        if state.lower() in location.lower():
            return state
    
    # Clean up common patterns
    location = re.sub(r'^(Officer at|at|in|located in|based in)\s*', '', location, flags=re.IGNORECASE)
    location = re.sub(r'NG,\s*', '', location, flags=re.I)
    location = re.sub(r',\s*NG$', '', location, flags=re.I)
    location = location.replace("NG", "").strip()
    
    if "remote" in location.lower():
        return "Remote"
    if "lagos" in location.lower():
        return "Lagos"
    if "abuja" in location.lower():
        return "Abuja"
    
    if len(location) > 30:
        location = location[:30]
    
    return location if location and len(location) > 2 else "Remote"


def clean_title(title: str) -> str:
    """
    Clean job title - remove URLs and garbage but KEEP the actual title.
    Do NOT replace with generic text.
    """
    if not title:
        print(f"     ⚠️ Empty title received in clean_title")
        return "Job Opportunity"
    
    original_title = title
    print(f"     📝 Original title: {title[:80]}...")  # Debug print
    
    # Remove any URLs completely
    title = re.sub(r'https?://[^\s]+', '', title)
    
    # Remove "Job Scrapper" prefix if present
    title = re.sub(r'^Job\s+Scrapper[,:]?\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'^Job\s+Scraper[,:]?\s*', '', title, flags=re.IGNORECASE)
    
    # Remove common prefixes (but keep the rest of the title)
    title = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|NOW HIRING)[:\s]+', '', title, flags=re.IGNORECASE)
    
    # Remove @mentions
    title = re.sub(r'@\w+', '', title)
    
    # Remove trailing words that got cut off (like single letters at the end)
    title = re.sub(r'\s+[a-z]$', '', title)
    
    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()
    
    # If after cleaning we have nothing, use original cleaned
    if not title or len(title) < 3:
        # Extract first 100 characters of original without URL and without common garbage
        original_clean = re.sub(r'https?://[^\s]+', '', original_title)
        original_clean = re.sub(r'^Job\s+Scrapper[,:]?\s*', '', original_clean, flags=re.IGNORECASE)
        original_clean = re.sub(r'^(Opportunity|Vacancy|Job|Position)[:\s]*', '', original_clean, flags=re.IGNORECASE)
        title = original_clean.strip()
        
        if not title or len(title) < 3:
            print(f"     ⚠️ Could not extract title from: {original_title[:80]}")
            return "Job Vacancy"
    
    # Capitalize first letter properly
    if title and len(title) > 0:
        title = title[0].upper() + title[1:] if len(title) > 1 else title
    
    # Limit length
    if len(title) > 120:
        title = title[:117] + "..."
    
    print(f"     ✅ Cleaned title: {title[:80]}...")
    return title

def clean_company(company: str) -> str:
    """Clean company name"""
    if not company or company == "Not specified":
        return ""
    
    company = str(company)
    
    # Remove URLs
    company = re.sub(r'https?://[^\s]+', '', company)
    
    # Remove @mentions
    company = re.sub(r'@\w+', '', company)
    
    # Remove common prefixes
    company = re.sub(r'^(Company:?\s*|via\s*|at\s*)', '', company, flags=re.IGNORECASE)
    
    # Remove broken text (words that are too short or single letters)
    words = company.split()
    clean_words = []
    for w in words:
        if len(w) > 2 or w.upper() in ['LTD', 'INC', 'LLC', 'PLC', 'NG']:
            clean_words.append(w)
        elif len(w) == 2 and w.isalpha() and w.upper() in ['NG', 'UK', 'US']:
            clean_words.append(w)
    
    company = ' '.join(clean_words)
    company = company.strip()
    
    if len(company) > 50:
        company = company[:47] + "..."
    
    return company if company and len(company) > 1 else ""


def is_job_posting(title: str, description: str) -> bool:
    """Filter out non-job postings"""
    combined = f"{title.lower()} {description.lower()}"
    
    non_job_keywords = [
        'youtube.com', 'youtu.be', 'watch now', 'subscribe', 'video',
        'this video', 'click here', 'read more', 'article', 'blog post',
        'tips', 'how to', 'guide', 'age discrimination', 'career advice',
    ]
    
    for keyword in non_job_keywords:
        if keyword in combined:
            return False
    
    job_keywords = [
        'hiring', 'vacancy', 'recruitment', 'job', 'position', 'career',
        'opportunity', 'role', 'staff', 'officer', 'manager', 'assistant',
        'developer', 'engineer', 'analyst', 'specialist', 'coordinator',
        'intern', 'trainee', 'consultant', 'advisor', 'supervisor',
    ]
    
    return any(keyword in combined for keyword in job_keywords)


def format_job(job: dict) -> str:
    """Format job with clean fields - preserve original title"""
    title = clean_title(job.get("title", ""))
    company = clean_company(job.get("company", ""))
    location = clean_location(job.get("location", ""))
    salary = job.get("salary", "")
    quality = job.get("_quality", 3)
    priority = job.get("_priority", False)

    stars = "⭐" * quality
    priority_tag = "🔴 PRIORITY MATCH\n" if priority else ""

    lines = []
    
    if priority_tag:
        lines.append(priority_tag.strip())
        lines.append("")
    
    lines.append(f"💼 {title}")
    
    if company:
        lines.append(f"🏢 {company}")
    
    if location:
        lines.append(f"📍 {location}")
    
    if salary:
        lines.append(f"💰 {salary}")
    
    lines.append(f"✨ Quality: {stars}")

    return "\n".join(lines)


def send_job(job: dict) -> bool:
    """Send job to Telegram"""
    url_link = job.get("url", "")
    
    if not url_link or not url_link.startswith("http"):
        print(f"     ⚠️ No valid URL for job: {job.get('title', '?')[:50]}")
        return False
    
    if 't.me' in url_link or 'telegram.me' in url_link:
        print(f"     ⚠️ Skipping Telegram link")
        return False
    
    title = job.get("title", "")
    description = job.get("description", "")
    if not is_job_posting(title, description):
        print(f"     🚫 Filtered (not a job): {title[:40]}")
        return False
    
    message = format_job(job)
    
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "🔗 Apply Now", "url": url_link}
            ]]
        }
    }
    
    success = send_with_retry(f"{BASE_URL}/sendMessage", payload)
    
    if success:
        priority_flag = " 🔴" if job.get("_priority") else ""
        clean_title_short = clean_title(title)[:50]
        print(f"     ✅ Sent{priority_flag}: {clean_title_short}...")
        return True
    else:
        print(f"     ❌ Failed: {title[:50]}")
        return False


def send_stats(stats: dict):
    """Send monthly report only"""
    today = datetime.now()
    
    if today.day == 1:
        send_monthly_report(stats)
    else:
        print(f"     📊 Stats recorded (next report on {today.replace(day=1).strftime('%B 1st')})")


def send_monthly_report(stats: dict):
    """Send monthly summary report"""
    now = datetime.now()
    last_month = now.strftime("%B %Y")
    
    lines = [
        f"📊 *Monthly Job Report - {last_month}*",
        f"🕐 Generated: {now.strftime('%d %b %Y, %I:%M %p')}\n",
        f"📨 Jobs sent this month: *{stats.get('sent', 0)}*",
        f"🚫 Filtered out: *{stats.get('filtered', 0)}*",
        f"👁️ Already seen: *{stats.get('seen', 0)}*",
        f"📡 Active sources: *{stats.get('sources', 0)}*\n",
    ]
    
    breakdowns = stats.get("source_counts", {})
    if breakdowns:
        top = sorted(breakdowns.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("*Top sources this month:*")
        for src, count in top:
            if count > 0:
                lines.append(f"  • {src}: {count} jobs")
    
    _send_text("\n".join(lines))


def send_health_alert(scraper_name: str, consecutive_failures: int):
    """Send health alert"""
    msg = f"⚠️ *Health Alert*\n`{scraper_name}` failed {consecutive_failures} times."
    _send_text(msg)


def send_alert(scraper_name: str, consecutive_failures: int):
    """Alias for compatibility"""
    send_health_alert(scraper_name, consecutive_failures)


def _send_text(text: str):
    """Send plain text"""
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
        time.sleep(0.5)
    except Exception as e:
        print(f"     ⚠️ Failed to send text: {e}")
