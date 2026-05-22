"""
sender.py — Formats and sends job listings to Telegram.
UPDATED: Just title with inline button
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


def clean_title(title: str) -> str:
    """Simple title cleaning - just remove URLs"""
    if not title:
        return "Job Opportunity"
    
    # Remove URLs
    title = re.sub(r'https?://[^\s]+', '', title)
    
    # Remove "Job Scrapper" prefix
    title = re.sub(r'^Job\s+Scrapper[,:]?\s*', '', title, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()
    
    # If title is too short or generic, use a simple default
    if len(title) < 3 or title.lower() in ['opportunity', 'job', 'vacancy']:
        return "New Job Opening"
    
    # Limit length
    if len(title) > 100:
        title = title[:97] + "..."
    
    return title if title else "Job Opportunity"


def send_job(job: dict) -> bool:
    """Send job to Telegram - just title with inline button"""
    url_link = job.get("url", "")
    
    if not url_link or not url_link.startswith("http"):
        print(f"     ⚠️ No valid URL for job")
        return False
    
    if 't.me' in url_link or 'telegram.me' in url_link:
        print(f"     ⚠️ Skipping Telegram link")
        return False
    
    # Clean the title
    title = clean_title(job.get("title", "Job Opportunity"))
    
    # Just the title - button will appear below automatically
    payload = {
        "chat_id": CHANNEL_ID,
        "text": f"💼 {title}",
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
        print(f"     ✅ Sent: {title[:50]}...")
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
