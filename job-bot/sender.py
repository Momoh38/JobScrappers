"""
sender.py — Formats and sends job listings to Telegram.
UPDATED: Removed source line, cleaner output
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
    "Abia", "Adamawa", "Akwa Ibam", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe",
    "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara",
    "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau",
    "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "FCT", "Abuja",
]

# Categories (simplified)
CATEGORIES = {
    "💻 Tech & Development": [
        "developer", "engineer", "devops", "qa", "software", "web", "mobile",
        "frontend", "backend", "fullstack", "data scientist", "data analyst",
    ],
    "📞 Customer Support": [
        "customer support", "customer service", "help desk", "technical support",
        "call center", "client support",
    ],
    "🗂️ Virtual & Admin": [
        "virtual assistant", "administrative", "admin", "data entry",
        "executive assistant", "personal assistant", "office assistant",
    ],
    "💰 Finance & Accounting": [
        "accountant", "bookkeeper", "finance", "payroll", "accounts",
        "financial analyst",
    ],
    "📣 Marketing & Sales": [
        "marketing", "seo", "sales", "growth", "social media", "business development",
    ],
    "🏗️ Project & Operations": [
        "project manager", "operations", "program manager", "coordinator",
    ],
    "🌍 NGO & UN": [
        "un ", "ngo", "undp", "unicef", "who", "united nations", "non-profit",
    ],
    "📝 Writing & Content": [
        "writer", "copywriter", "editor", "content", "proofreader",
    ],
    "🎓 Teaching & Training": [
        "tutor", "teacher", "trainer", "instructor", "lecturer",
    ],
}

_sent_category_headers = set()


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
        
        # Try without parse_mode if error
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


def get_category(job: dict) -> str:
    """Determine job category from title"""
    title = job.get("title", "").lower()
    for category, keywords in CATEGORIES.items():
        if any(kw in title for kw in keywords):
            return category
    return "🌐 General / Remote"


def clean_location(location: str) -> str:
    """Clean and standardize location, extract Nigerian states"""
    if not location or location == "Not specified":
        return "Remote"
    
    location = str(location)
    
    # Check for Nigerian states
    for state in NIGERIAN_STATES:
        if state.lower() in location.lower():
            return state
    
    # Check for common location patterns
    if "lagos" in location.lower():
        return "Lagos"
    if "abuja" in location.lower():
        return "Abuja"
    if "remote" in location.lower():
        return "Remote"
    if "worldwide" in location.lower() or "global" in location.lower():
        return "Remote (Worldwide)"
    
    # Clean up common issues
    location = re.sub(r'NG,\s*', '', location, flags=re.I)
    location = re.sub(r',\s*NG$', '', location, flags=re.I)
    location = location.replace("NG", "").strip()
    
    # Limit length
    if len(location) > 30:
        location = location[:30]
    
    return location if location else "Remote"


def clean_title(title: str) -> str:
    """Clean and standardize job title"""
    if not title or title == "Opportunity":
        return "Job Opportunity"
    
    # Remove common prefixes
    title = re.sub(r'^(URGENTLY|WE\'RE|HIRING|VACANCY|JOB|POSITION|NOW HIRING)[:\s]+', '', title, flags=re.IGNORECASE)
    
    # Remove @mentions
    title = re.sub(r'@\w+', '', title)
    
    # Remove trailing garbage
    title = re.sub(r'\s*\([^)]*\)\s*$', '', title)
    
    # Clean up extra spaces
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()
    
    # Limit length
    if len(title) > 100:
        title = title[:97] + "..."
    
    return title if title else "Job Opportunity"


def clean_company(company: str) -> str:
    """Clean company name"""
    if not company or company == "Not specified":
        return "Not specified"
    
    # Remove @mentions
    company = re.sub(r'@\w+', '', company)
    
    # Remove common prefixes
    company = re.sub(r'^(Company:?\s*|via\s*)', '', company, flags=re.IGNORECASE)
    
    # Clean up
    company = company.strip()
    
    if len(company) > 50:
        company = company[:47] + "..."
    
    return company if company else "Not specified"


def is_job_posting(title: str, description: str) -> bool:
    """Filter out non-job postings (YouTube videos, articles, etc.)"""
    combined = f"{title.lower()} {description.lower()}"
    
    # Keywords that indicate NOT a job posting
    non_job_keywords = [
        'youtube.com', 'youtu.be', 'watch now', 'subscribe', 'video',
        'this video', 'click here', 'read more', 'article', 'blog post',
        'tips', 'how to', 'guide', 'age discrimination', 'career advice',
    ]
    
    for keyword in non_job_keywords:
        if keyword in combined:
            return False
    
    # Must have job-related keywords
    job_keywords = [
        'hiring', 'vacancy', 'recruitment', 'job', 'position', 'career',
        'opportunity', 'role', 'staff', 'officer', 'manager', 'assistant',
        'developer', 'engineer', 'analyst', 'specialist', 'coordinator',
    ]
    
    return any(keyword in combined for keyword in job_keywords)


def format_job(job: dict) -> str:
    """Format job with NO description and NO source line"""
    title = clean_title(job.get("title", "Job Opportunity"))
    company = clean_company(job.get("company", "Not specified"))
    location = clean_location(job.get("location", ""))
    salary = job.get("salary", "")
    quality = job.get("_quality", 3)
    priority = job.get("_priority", False)

    stars = "⭐" * quality
    priority_tag = "🔴 PRIORITY MATCH\n" if priority else ""

    lines = [priority_tag]
    
    if priority_tag:
        lines.append("")
    
    lines.append(f"💼 {title}")
    
    if company and company != "Not specified":
        lines.append(f"🏢 {company}")
    
    if location:
        lines.append(f"📍 {location}")
    
    if salary:
        lines.append(f"💰 {salary}")
    
    lines.append(f"✨ Quality: {stars}")
    
    # NO description, NO source line - just clean job info

    return "\n".join(lines)


def send_job(job: dict) -> bool:
    """Send job to Telegram - clean message with just Apply Now button"""
    url_link = job.get("url", "")
    
    if not url_link or not url_link.startswith("http"):
        print(f"     ⚠️ No valid URL for job: {job.get('title', '?')[:50]}")
        return False
    
    # Skip Telegram internal links
    if 't.me' in url_link or 'telegram.me' in url_link:
        print(f"     ⚠️ Skipping Telegram link")
        return False
    
    # Filter out non-job postings
    title = job.get("title", "")
    description = job.get("description", "")
    if not is_job_posting(title, description):
        print(f"     🚫 Filtered (not a job): {title[:40]}")
        return False
    
    message = format_job(job)
    category = get_category(job)
    
    # Send category header once per run
    if category not in _sent_category_headers:
        _send_text(f"\n{category}\n{'─' * 30}")
        _sent_category_headers.add(category)
        time.sleep(0.5)
    
    # Build payload with apply button
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
        print(f"     ✅ Sent{priority_flag}: {title[:50]}...")
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
