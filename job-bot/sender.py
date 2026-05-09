"""
sender.py — Formats and sends job listings to Telegram.
Features: quality stars, priority tag, inline Apply button, category headers,
          stats summary message, health alerts.
"""

import os
import requests
import time

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
        "chat support", "technical support",
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


def get_category(job: dict) -> str:
    title = job.get("title", "").lower()
    tags = job.get("tags", "").lower()
    combined = f"{title} {tags}"
    for category, keywords in CATEGORIES.items():
        if any(kw in combined for kw in keywords):
            return category
    return "🌐 General / Remote"


def escape(text: str) -> str:
    if not text:
        return ""
    for ch in ["*", "_", "`", "["]:
        text = str(text).replace(ch, f"\\{ch}")
    return str(text)


def format_job(job: dict) -> str:
    title    = job.get("title", "N/A")
    company  = job.get("company", "N/A")
    location = job.get("location", "Remote / Nigeria")
    salary   = job.get("salary", "")
    desc     = job.get("description", "")
    source   = job.get("source", "")
    tags     = job.get("tags", "")
    exp      = job.get("experience", "")
    quality  = job.get("_quality", 3)
    priority = job.get("_priority", False)

    if desc and len(desc) > 350:
        desc = desc[:350].strip() + "..."

    stars = "⭐" * quality
    priority_tag = "🔴 *PRIORITY MATCH*\n" if priority else ""

    lines = [
        priority_tag,
        f"💼 *{escape(title)}*",
        f"🏢 {escape(company)}",
        f"📍 {escape(location)}",
    ]

    if salary:
        lines.append(f"💰 {escape(salary)}")
    if exp:
        lines.append(f"📊 {escape(exp)}")
    if tags:
        lines.append(f"🏷️ {escape(tags)}")

    lines.append(f"✨ Quality: {stars}")

    if desc:
        lines.append(f"\n📋 _{escape(desc)}_")

    if source:
        lines.append(f"\n_Source: {escape(source)}_")

    return "\n".join(l for l in lines if l)


def send_job(job: dict):
    """Send a single job to Telegram with an inline Apply button."""
    url_link = job.get("url", "")
    message  = format_job(job)
    category = get_category(job)

    # Send category header if this is the first job in this category this run
    if category not in _sent_category_headers:
        _send_text(f"\n{category}\n{'─' * 30}")
        _sent_category_headers.add(category)
        time.sleep(0.5)

    # Build payload — with inline Apply button if we have a URL
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    if url_link and url_link.startswith("http"):
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "🔗 Apply Now", "url": url_link}
            ]]
        }

    response = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    if response.status_code != 200:
        print(f"     ⚠️ Telegram error: {response.text}")
    else:
        priority_flag = " 🔴" if job.get("_priority") else ""
        print(f"     ✅ Sent{priority_flag}: {job.get('title','?')} @ {job.get('company','?')}")

    time.sleep(1)


def send_stats(stats: dict):
    """Send a run summary message to the channel."""
    from datetime import datetime
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    lines = [
        f"📊 *Bot Run Summary*",
        f"🕐 {now} WAT\n",
        f"📨 New jobs sent:     *{stats.get('sent', 0)}*",
        f"🚫 Filtered out:      *{stats.get('filtered', 0)}*",
        f"👁️ Already seen:      *{stats.get('seen', 0)}*",
        f"📡 Sources scraped:   *{stats.get('sources', 0)}*",
    ]

    breakdowns = stats.get("source_counts", {})
    if breakdowns:
        top = sorted(breakdowns.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("\n*Top sources this run:*")
        for src, count in top:
            lines.append(f"  • {escape(src)}: {count} jobs")

    _send_text("\n".join(lines))


def send_health_alert(scraper_name: str, consecutive_failures: int):
    """Alert if a scraper has been failing repeatedly."""
    msg = (
        f"⚠️ *Health Alert*\n"
        f"`{escape(scraper_name)}` has failed "
        f"*{consecutive_failures}* runs in a row.\n"
        f"It may need fixing."
    )
    _send_text(msg)


def _send_text(text: str):
    """Send a plain formatted text message."""
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
    time.sleep(0.5)
