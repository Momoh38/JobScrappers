"""
sender.py — Formats and sends job listings to Telegram.
Features: quality stars, priority tag, inline Apply button, category headers,
          stats summary message, health alerts.
"""
import os
import requests
import time
import re
from datetime import datetime

# Rate limiting variables
_last_message_time = 0
MIN_MESSAGE_INTERVAL = 1.5  # 1.5 seconds between messages
MAX_RETRIES = 3

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Category grouping — maps keywords in job title to a display category
CATEGORIES = {
    "💻 Tech & Development": [
        "developer", "engineer", "devops", "qa ", "quality assurance",
        "frontend", "backend", "fullstack", "full stack", "mobile", "flutter",
        "react", "python", "javascript", "software", "web dev", "ui/ux",
    ],
    "📞 Customer Support": [
        "customer support", "customer service", "customer success",
        "customer care", "client support", "help desk", "live chat",
        "chat support", "technical support", "Customer Service", "Virtual Assistance",
    ],
    "🖊️ Writing & Content": [
        "writer", "copywriter", "editor", "proofreader", "content",
        "ghostwriter", "blogger", "journalist", "transcri",
    ],
    "🗂️ Virtual & Admin": [
        "virtual assistant", "administrative", "admin", "data entry",
        "executive assistant", "personal assistant", "office assistant",
    ],
    "📊 Data & Analytics": [
        "data analyst", "data scientist", "business analyst",
        "data engineer", "research analyst",
    ],
    "💰 Finance & Accounting": [
        "accountant", "bookkeeper", "finance", "payroll", "accounts",
    ],
    "📣 Marketing & Sales": [
        "marketing", "seo", "sales", "growth", "affiliate",
        "social media", "email market",
    ],
    "🏗️ Project & Operations": [
        "project manager", "operations", "program manager", "scrum",
        "coordinator",
    ],
    "👥 HR & Recruitment": [
        "hr ", "human resources", "recruiter", "talent", "people ops",
    ],
    "🎓 Teaching & Training": [
        "tutor", "teacher", "trainer", "elearning", "curriculum",
        "instructional",
    ],
}

# Track which category header has already been sent this run
_sent_category_headers = set()


def send_with_retry(url, payload, retry_count=0):
    """Send message with retry logic for rate limiting"""
    global _last_message_time
    
    # Enforce minimum time between messages
    current_time = time.time()
    time_since_last = current_time - _last_message_time
    
    if time_since_last < MIN_MESSAGE_INTERVAL:
        wait_time = MIN_MESSAGE_INTERVAL - time_since_last
        time.sleep(wait_time)
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        # Check for rate limit (429)
        if response.status_code == 429:
            error_data = response.json()
            retry_after = error_data.get('parameters', {}).get('retry_after', 5)
            print(f"     ⏳ Rate limited, waiting {retry_after}s...")
            time.sleep(retry_after + 1)
            
            if retry_count < MAX_RETRIES:
                return send_with_retry(url, payload, retry_count + 1)
            return False
        
        result = response.json()
        
        if response.status_code == 200 and result.get('ok'):
            _last_message_time = time.time()
            return True
        elif response.status_code == 400 and "can't parse entities" in str(result):
            # Try without parse_mode
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
    title = job.get("title", "").lower()
    tags = job.get("tags", "").lower()
    combined = f"{title} {tags}"
    for category, keywords in CATEGORIES.items():
        if any(kw in combined for kw in keywords):
            return category
    return "🌐 General / Remote"


def escape_markdown(text: str) -> str:
    """Escape Markdown special characters"""
    if not text:
        return ""
    # Escape special characters for Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for ch in special_chars:
        text = str(text).replace(ch, f"\\{ch}")
    return str(text)


def clean_description(desc: str, max_length: int = 800) -> str:
    """Clean and truncate description"""
    if not desc:
        return ""
    
    # Remove excessive whitespace and newlines
    desc = re.sub(r'\n\s*\n', '\n\n', desc)  # Keep double newlines as paragraph breaks
    desc = re.sub(r' +', ' ', desc)  # Remove extra spaces
    desc = desc.strip()
    
    # Truncate if too long
    if len(desc) > max_length:
        desc = desc[:max_length].strip() + "..."
    
    return desc


def format_job(job: dict) -> str:
    """Format job with proper description text, not just the link"""
    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    location = job.get("location", "Remote / Nigeria")
    salary = job.get("salary", "")
    description = job.get("description", "")
    source = job.get("source", "")
    tags = job.get("tags", "")
    exp = job.get("experience", "")
    quality = job.get("_quality", 3)
    priority = job.get("_priority", False)

    # Clean and truncate description
    description = clean_description(description, 800)

    stars = "⭐" * quality
    priority_tag = "🔴 *PRIORITY MATCH*\n" if priority else ""

    lines = [
        priority_tag,
        f"💼 *{escape_markdown(title)}*",
        f"🏢 {escape_markdown(company)}",
        f"📍 {escape_markdown(location)}",
    ]

    if salary:
        lines.append(f"💰 {escape_markdown(salary)}")
    if exp:
        lines.append(f"📊 {escape_markdown(exp)}")
    if tags:
        lines.append(f"🏷️ {escape_markdown(tags)}")

    lines.append(f"✨ Quality: {stars}")

    # Show the ACTUAL JOB DESCRIPTION, not the link
    if description:
        lines.append(f"\n📋 {escape_markdown(description)}")

    if source:
        lines.append(f"\n_Source: {escape_markdown(source)}_")

    return "\n".join(l for l in lines if l)


def send_job(job: dict):
    """Send a single job to Telegram with an inline Apply button."""
    url_link = job.get("url", "")
    
    # Don't send Telegram internal links
    if url_link and ('t.me' in url_link or 'telegram.me' in url_link):
        print(f"     ⚠️ Skipping Telegram internal link: {url_link[:50]}")
        return False
    
    message = format_job(job)
    category = get_category(job)

    # Send category header if this is the first job in this category this run
    if category not in _sent_category_headers:
        _send_text(f"\n{category}\n{'─' * 23}")
        _sent_category_headers.add(category)
        time.sleep(0.5)

    # Build payload with inline Apply button if we have a valid URL
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,  # Disable preview to keep message clean
    }

    if url_link and url_link.startswith("http") and 't.me' not in url_link:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "🔗 Apply Now", "url": url_link}
            ]]
        }

    success = send_with_retry(f"{BASE_URL}/sendMessage", payload)
    
    if success:
        priority_flag = " 🔴" if job.get("_priority") else ""
        print(f"     ✅ Sent{priority_flag}: {job.get('title','?')[:50]}...")
        return True
    else:
        print(f"     ❌ Failed to send: {job.get('title','?')}")
        return False


def send_stats(stats: dict):
    """Send a run summary message to the channel."""
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    lines = [
        f"📊 *Bot Run Summary*",
        f"🕐 {now} WAT\n",
        f"📨 New jobs sent:     *{stats.get('sent', 0)}*",
        f"🚫 Filtered out:      *{stats.get('filtered', 0)}*",
        f"👁️ Already seen:      *{stats.get('seen', 0)}*",
        f"🔗 No external links: *{stats.get('no_links', 0)}*",
        f"📡 Sources scraped:   *{stats.get('sources', 0)}*",
    ]

    breakdowns = stats.get("source_counts", {})
    if breakdowns:
        top = sorted(breakdowns.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("\n*Top sources this run:*")
        for src, count in top:
            lines.append(f"  • {escape_markdown(src)}: {count} jobs")

    _send_text("\n".join(lines))


def send_health_alert(scraper_name: str, consecutive_failures: int):
    """Alert if a scraper has been failing repeatedly."""
    msg = (
        f"⚠️ *Health Alert*\n"
        f"`{escape_markdown(scraper_name)}` has failed "
        f"*{consecutive_failures}* runs in a row.\n"
        f"It may need fixing."
    )
    _send_text(msg)


def send_alert(scraper_name: str, consecutive_failures: int):
    """Alias for send_health_alert for compatibility"""
    send_health_alert(scraper_name, consecutive_failures)


def _send_text(text: str):
    """Send a plain formatted text message."""
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
