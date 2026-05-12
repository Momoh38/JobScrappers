"""
sender.py — Formats and sends job listings to Telegram.
Updated: Monthly stats only (no after-run summaries)
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

# Categories
CATEGORIES = {
    "💻 Tech & Development": [
        "developer", "engineer", "devops", "qa", "quality assurance",
        "frontend", "backend", "fullstack", "full stack", "mobile", "flutter",
        "react", "python", "javascript", "software", "web dev", "ui/ux", "data scientist",
        "data analyst", "software engineer",
    ],
    "📞 Customer Support": [
        "customer support", "customer service", "customer success",
        "customer care", "client support", "help desk", "live chat",
        "chat support", "technical support", "virtual assistance",
        "call center", "phone support", "email support",
    ],
    "🖊️ Writing & Content": [
        "writer", "copywriter", "editor", "proofreader", "content",
        "ghostwriter", "blogger", "journalist", "content writer",
    ],
    "🗂️ Virtual & Admin": [
        "virtual assistant", "administrative", "admin", "data entry",
        "executive assistant", "personal assistant", "office assistant",
        "administrative assistant", "virtual assistance",
    ],
    "💰 Finance & Accounting": [
        "accountant", "bookkeeper", "finance", "payroll", "accounts",
        "financial analyst",
    ],
    "📣 Marketing & Sales": [
        "marketing", "seo", "sales", "growth", "affiliate",
        "social media", "email market", "business development",
        "digital marketing",
    ],
    "🏗️ Project & Operations": [
        "project manager", "operations", "program manager", "scrum",
        "coordinator", "project coordinator",
    ],
    "🌍 NGO & UN": [
        "un ", "ngo", "undp", "unicef", "who", "world bank", "united nations",
        "non-profit", "nonprofit", "field assistant", "relief",
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
    title = job.get("title", "").lower()
    tags = job.get("tags", "").lower()
    combined = f"{title} {tags}"
    for category, keywords in CATEGORIES.items():
        if any(kw in combined for kw in keywords):
            return category
    return "🌐 General / Remote"


def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    if not text:
        return ""
    text = str(text)
    text = text.replace('_', '\\_')
    text = text.replace('*', '\\*')
    text = text.replace('`', '\\`')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    text = text.replace('(', '\\(')
    text = text.replace(')', '\\)')
    return text


def clean_text(text: str, max_length: int = 800) -> str:
    """Clean and truncate text"""
    if not text:
        return ""
    
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('\\/', '/')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    if len(text) > max_length:
        text = text[:max_length].strip() + "..."
    
    return text


def format_job(job: dict) -> str:
    """Format job with clean text"""
    title = clean_text(job.get("title", "Job Opportunity"), 100)
    company = clean_text(job.get("company", "Not specified"), 50)
    location = clean_text(job.get("location", "Remote"), 50)
    salary = clean_text(job.get("salary", ""), 80)
    description = clean_text(job.get("description", ""), 600)
    source = clean_text(job.get("source", ""), 50)
    quality = job.get("_quality", 3)
    priority = job.get("_priority", False)

    stars = "⭐" * quality
    priority_tag = "🔴 *PRIORITY MATCH*\n" if priority else ""

    lines = [priority_tag]
    
    if title:
        lines.append(f"💼 *{escape_markdown(title)}*")
    if company and company != "Not specified":
        lines.append(f"🏢 {escape_markdown(company)}")
    if location and location != "Remote / Worldwide":
        lines.append(f"📍 {escape_markdown(location)}")
    if salary:
        lines.append(f"💰 {escape_markdown(salary)}")
    
    lines.append(f"✨ Quality: {stars}")
    
    if description and description != "Click the 'Apply Now' button below for more details about this position.":
        lines.append(f"\n📋 {escape_markdown(description)}")
    elif description:
        lines.append(f"\n📋 {description}")
    
    if source:
        lines.append(f"\n_Source: {escape_markdown(source)}_")

    return "\n".join(l for l in lines if l)


def send_job(job: dict) -> bool:
    """Send job to Telegram"""
    url_link = job.get("url", "")
    
    if not url_link or not url_link.startswith("http"):
        print(f"     ⚠️ No valid URL for job: {job.get('title', '?')[:50]}")
        return False
    
    if 't.me' in url_link or 'telegram.me' in url_link:
        print(f"     ⚠️ Skipping Telegram link")
        return False
    
    message = format_job(job)
    category = get_category(job)
    
    if category not in _sent_category_headers:
        _send_text(f"\n{category}\n{'─' * 23}")
        _sent_category_headers.add(category)
        time.sleep(0.5)
    
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
        print(f"     ✅ Sent{priority_flag}: {job.get('title', '?')[:50]}...")
        return True
    else:
        print(f"     ❌ Failed: {job.get('title', '?')[:50]}")
        return False


def send_stats(stats: dict):
    """
    Send run summary - DISABLED by default.
    Only sends if it's the first day of the month (monthly report).
    """
    today = datetime.now()
    
    # Only send on the 1st day of each month
    if today.day == 1:
        send_monthly_report(stats)
    else:
        # Silent - no message sent
        print(f"     📊 Stats recorded (no message sent - next monthly report on {today.replace(day=1).strftime('%B 1st')})")
        pass


def send_monthly_report(stats: dict):
    """Send monthly summary report (first day of each month)"""
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
    
    # Add top sources
    breakdowns = stats.get("source_counts", {})
    if breakdowns:
        top = sorted(breakdowns.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("*Top sources this month:*")
        for src, count in top:
            if count > 0:
                lines.append(f"  • {escape_markdown(src)}: {count} jobs")
    
    # Calculate next month
    if now.month == 12:
        next_month = f"January 1st, {now.year + 1}"
    else:
        next_month = f"{now.replace(day=1, month=now.month + 1).strftime('%B 1st, %Y')}"
    
    lines.append(f"\n_Next report: {next_month}_")
    
    _send_text("\n".join(lines))
    print(f"     📊 Monthly report sent for {last_month}")


def send_health_alert(scraper_name: str, consecutive_failures: int):
    """Send health alert when a scraper fails repeatedly"""
    msg = (
        f"⚠️ *Health Alert*\n"
        f"`{scraper_name}` has failed "
        f"*{consecutive_failures}* runs in a row.\n"
        f"It may need fixing."
    )
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
