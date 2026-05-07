# 🕌 Halal Jobs Bot

A Telegram bot that scrapes multiple job boards for halal job listings in Nigeria and remote positions, filters out haram industries, and delivers each job as a message to your private Telegram channel.

---

## Sources Covered

| Source | Type |
|---|---|
| RemoteOK | Remote jobs API |
| Arbeitnow | Remote jobs API |
| The Muse | Global jobs API |
| WeWorkRemotely | Remote jobs RSS |
| Jobberman | Nigeria jobs |
| MyJobMag | Nigeria jobs |
| NGCareers | Nigeria jobs |
| Telegram Channels | Public job channels |

---

## Setup Instructions

### 1. Create the GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **+** icon → **New repository**
3. Name it `halal-jobs-bot`
4. Set it to **Private**
5. Click **Create repository**

---

### 2. Upload the Code

1. On your new repo page, click **uploading an existing file**
2. Drag and drop all the project files
3. Click **Commit changes**

Or if you use Git:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/halal-jobs-bot.git
git push -u origin main
```

---

### 3. Add Your Secrets

This keeps your bot token and channel ID private.

1. In your GitHub repo, go to **Settings**
2. Click **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these two:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Your channel ID (e.g. `-1003869498104`) |

---

### 4. Enable GitHub Actions

1. In your repo, click the **Actions** tab
2. If prompted, click **I understand my workflows, go ahead and enable them**

---

### 5. Test It Manually

1. Go to the **Actions** tab
2. Click **Halal Jobs Bot** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch it run and check your Telegram channel!

---

## Schedule

The bot runs automatically:
- **8:00 AM** Nigeria time (WAT)
- **6:00 PM** Nigeria time (WAT)

Every day, 7 days a week.

---

## Adding More Keywords to Filter

Edit `filter.py` and add words to the `HARAM_KEYWORDS` list.

---

## Adding More Telegram Channels to Monitor

Edit `scrapers/telegram_channels.py` and add channel usernames to `TELEGRAM_JOB_CHANNELS`.
