import os
import requests
import time

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def format_job(job: dict) -> str:
    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    location = job.get("location", "Remote / Nigeria")
    salary = job.get("salary", "")
    description = job.get("description", "")
    url = job.get("url", "")
    source = job.get("source", "")
    tags = job.get("tags", "")
    experience = job.get("experience", "")

    if description and len(description) > 300:
        description = description[:300].strip() + "..."

    lines = [
        f"💼 *{escape(title)}*",
        f"🏢 {escape(company)}",
        f"📍 {escape(location)}",
    ]

    if salary:
        lines.append(f"💰 {escape(salary)}")
    if experience:
        lines.append(f"📊 {escape(experience)}")
    if tags:
        lines.append(f"🏷️ {escape(tags)}")
    if description:
        lines.append(f"\n📋 _{escape(description)}_")
    if url:
        lines.append(f"\n🔗 [Apply Here]({url})")
    if source:
        lines.append(f"\n_Source: {escape(source)}_")

    return "\n".join(lines)


def escape(text: str) -> str:
    if not text:
        return ""
    for ch in ["*", "_", "`"]:
        text = text.replace(ch, f"\\{ch}")
    return str(text)


def send_job(job: dict):
    message = format_job(job)
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }
    response = requests.post(TELEGRAM_API, json=payload, timeout=10)
    if response.status_code != 200:
        print(f"     ⚠️ Telegram error: {response.text}")
    else:
        print(f"     ✅ Sent: {job.get('title','?')} @ {job.get('company','?')}")
    time.sleep(1)


def test_send():
    payload = {
        "chat_id": CHANNEL_ID,
        "text": "✅ Halal Jobs Bot is connected and running! Jobs will appear below.",
        "parse_mode": "Markdown",
    }
    response = requests.post(TELEGRAM_API, json=payload, timeout=10)
    if response.status_code != 200:
        print(f"     ❌ Telegram test FAILED: {response.text}")
    else:
        print(f"     ✅ Telegram test message sent successfully!")
