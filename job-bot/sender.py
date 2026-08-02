"""
sender.py — Formats and sends job listings to Telegram.
UPDATED: Monthly reports only + cumulative total jobs
"""

import os
import requests
import time
import re
import json
from datetime import datetime

# Rate limiting
_last_message_time = 0
MIN_MESSAGE_INTERVAL = 1.5
MAX_RETRIES = 3

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# File to track cumulative stats
CUMULATIVE_STATS_FILE = "cumulative_stats.json"


def load_cumulative_stats():
    """Load cumulative stats from file"""
    if os.path.exists(CUMULATIVE_STATS_FILE):
        try:
            with open(CUMULATIVE_STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"total_jobs_found": 0, "total_jobs_sent": 0, "total_months": 0, "first_run": datetime.now().isoformat()}


def save_cumulative_stats(stats):
    """Save cumulative stats to file"""
    try:
        with open(CUMULATIVE_STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except:
        pass


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
    """Send job to Telegram"""
    url_link = job.get("url", "")
    
    if not url_link or not url_link.startswith("http"):
        print(f"     ⚠️ No valid URL for job")
        return False
    
    if 't.me' in url_link or 'telegram.me' in url_link:
        print(f"     ⚠️ Skipping Telegram link")
        return False
    
    # Clean the title
    title = clean_title(job.get("title", "Job Opportunity"))
    
    # Build the message
    message = f"💼 {title}"
    
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
        print(f"     ✅ Sent: {title[:50]}...")
        return True
    else:
        print(f"     ❌ Failed: {title[:50]}")
        return False


def send_stats(stats: dict):
    """
    ONLY send monthly report (on the 1st of each month)
    Includes cumulative totals from launch
    """
    today = datetime.now()
    
    # Only send on the 1st day of each month
    if today.day == 1:
        send_monthly_report(stats)
    else:
        print(f"     📊 Stats recorded (next report on {today.replace(day=1).strftime('%B 1st')})")


def send_monthly_report(stats: dict):
    """Send monthly summary report with cumulative totals"""
    now = datetime.now()
    last_month = now.strftime("%B %Y")
    
    # Load cumulative stats
    cumulative = load_cumulative_stats()
    
    # Update cumulative stats with this month's data
    cumulative["total_jobs_found"] += stats.get('sent', 0) + stats.get('filtered', 0)
    cumulative["total_jobs_sent"] += stats.get('sent', 0)
    cumulative["total_months"] += 1
    cumulative["last_update"] = datetime.now().isoformat()
    
    # Save updated cumulative stats
    save_cumulative_stats(cumulative)
    
    # Format first run date
    first_run = datetime.fromisoformat(cumulative["first_run"]).strftime("%B %Y")
    
    # Build the report
    lines = [
        f"📊 *Monthly Job Report - {last_month}*",
        f"🕐 Generated: {now.strftime('%d %b %Y, %I:%M %p')}\n",
        f"📨 Jobs sent this month: *{stats.get('sent', 0)}*",
        f"🚫 Filtered out this month: *{stats.get('filtered', 0)}*",
        f"👁️ Already seen this month: *{stats.get('seen', 0)}*",
        f"📡 Active sources: *{stats.get('sources', 0)}*\n",
        f"─" * 30,
        f"\n📈 *Lifetime Stats (Since {first_run})*",
        f"🔍 Total jobs found: *{cumulative['total_jobs_found']:,}*",
        f"📨 Total jobs sent: *{cumulative['total_jobs_sent']:,}*",
        f"📅 Months active: *{cumulative['total_months']}*",
    ]
    
    # Add top sources for this month
    breakdowns = stats.get("source_counts", {})
    if breakdowns:
        top = sorted(breakdowns.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("\n*Top sources this month:*")
        for src, count in top:
            if count > 0:
                lines.append(f"  • {src}: {count} jobs")
    
    # Add top sources overall (if available)
    if "source_counts" in cumulative:
        top_overall = sorted(cumulative.get("source_counts", {}).items(), key=lambda x: x[1], reverse=True)[:3]
        if top_overall:
            lines.append("\n*Top sources overall:*")
            for src, count in top_overall:
                if count > 0:
                    lines.append(f"  • {src}: {count} jobs")
    
    lines.append(f"\n_Next report: {now.replace(day=1, month=now.month+1).strftime('%B 1st, %Y') if now.month < 12 else 'January 1st, ' + str(now.year+1)}_")
    
    _send_text("\n".join(lines))
    print(f"     📊 Monthly report sent for {last_month}")
    print(f"     📈 Total jobs found since launch: {cumulative['total_jobs_found']:,}")


def send_health_alert(scraper_name: str, consecutive_failures: int):
    """Send health alert to main channel"""
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
