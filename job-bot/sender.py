def test_send():
    """Sends a test message to confirm Telegram connection works."""
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
