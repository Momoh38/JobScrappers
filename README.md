```markdown
# 🔍 JobScrappers

A fully automated job alert bot that scrapes **15+ job platforms** across the web and social media, filters out non-Nigeria friendly listings, and delivers each matching job as a formatted message directly to your private **Telegram channel** every 30 minutes, every day, completely free.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Project Structure](#project-structure)
- [Job Sources](#job-sources)
- [Filter System](#filter-system)
- [Customising Your Job Preferences](#customising-your-job-preferences)
- [Installation & Setup](#installation--setup)
- [Running the Bot](#running-the-bot)
- [Resetting the Bot](#resetting-the-bot)
- [Telegram Message Format](#telegram-message-format)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

---

## How It Works

Every time the bot runs (every 30 minutes via GitHub Actions), it follows these steps:

```
1. WAKE UP      — GitHub Actions triggers the script (every 30 minutes)
2. SCRAPE       — 15+ scrapers run, collecting job listings
3. DEDUPLICATE  — Jobs already sent are skipped
4. FILTER       — Location & language filters applied
5. SEND         — Jobs formatted and delivered to Telegram
6. LOG          — Stats saved (monthly reports only)
7. SLEEP        — Script finishes until next run
```

**No server needed. No subscription. Runs on GitHub's free infrastructure.**

---

## Features

- ✅ **15+ Active Job Sources** — Nigerian job boards, global remote, NGO, Telegram groups
- ✅ **Runs Every 30 Minutes** — Never miss a job opportunity
- ✅ **Smart Filtering** — Filters out US-only, Europe-only, Asia, Israel jobs
- ✅ **Telegram Integration** — Direct messages with clickable "Apply Now" buttons
- ✅ **External Link Extraction** — Gets real job links from Telegram messages (not group links)
- ✅ **Monthly Reports Only** — No spam, just one summary report on the 1st of each month
- ✅ **Automatic Health Alerts** — Notifies you if any scraper fails
- ✅ **Fully Customizable** — Edit `config.py` to match your job preferences
- ✅ **Completely Free** — Runs on GitHub Actions free tier, all job sources are free to apply

---

## Project Structure

```
JobScarppers/
│
├── README.md
├── requirements.txt
│
├── .github/
│   └── workflows/
│       └── run.yml                   ← Runs every 30 minutes
│
└── job-bot/
    ├── main.py                       ← Entry point
    ├── config.py                     ← Your job preferences (EDIT THIS)
    ├── filter.py                     ← Filtering logic
    ├── sender.py                     ← Telegram formatter
    ├── seen_jobs.json                ← Auto-generated
    ├── scraper_health.json           ← Auto-generated
    ├── run_stats.json                ← Auto-generated
    ├── requirements.txt
    │
    └── scrapers/                     ← 15+ job source scrapers
        ├── jobberman.py              ← Nigerian job board
        ├── myjobmag.py               ← Nigerian job board
        ├── ngcareers.py              ← Nigerian job board
        ├── jobgurus.py               ← Nigerian job board
        ├── ngo_jobs.py               ← UN/ReliefWeb jobs
        ├── africa_jobs.py            ← African job boards
        ├── remoteok.py               ← Global remote jobs
        ├── remotive.py               ← Global remote jobs
        ├── themuse.py                ← Global jobs
        ├── workingnomads.py          ← Remote jobs
        ├── braintrust.py             ← Freelance/remote
        ├── himalayas.py              ← Remote jobs
        ├── wfh_io.py                 ← Remote jobs
        ├── virtustant.py             ← Global hiring
        └── telegram_channels.py      ← Nigerian Telegram groups
```

---

## Job Sources (15 Active)

### Nigeria-Specific (4 sources) — MOST RELIABLE
| Scraper | Source | Status |
|---------|--------|--------|
| Jobberman | Nigerian job board | ✅ Active |
| MyJobMag | Nigerian job board | ✅ Active |
| NGCareers | Nigerian job board | ✅ Active |
| JobGurus | Nigerian job board | ✅ Active |

### International / NGO / Africa (2 sources)
| Scraper | Source | Status |
|---------|--------|--------|
| NGO / UN Jobs | ReliefWeb API | ✅ Active |
| Africa Jobs | African job boards | ✅ Active |

### Global Remote (9 sources)
| Scraper | Source | Status |
|---------|--------|--------|
| RemoteOK | RemoteOK API | ✅ Active |
| Remotive | Remotive API | ✅ Active |
| TheMuse | The Muse API | ✅ Active |
| WorkingNomads | JSON API | ✅ Active |
| Braintrust | JSON API | ✅ Active |
| Himalayas | Free API | ✅ Active |
| WFH.io | HTML scraper | ✅ Active |
| Virtustant | HTML scraper | ✅ Active |

### Social Media (1 source — 7 channels)
| Channel | Status |
|---------|--------|
| @jbtoday | ✅ Active |
| @jobnownigeria | ✅ Active |
| @careermattersng | ✅ Active |
| @jobnetworkng | ✅ Active |
| @WorkaNigeria | ✅ Active |
| @remotejobss | ✅ Active |
| @techjobsworld | ✅ Active |

---

## Filter System (Simplified)

```
JOB FOUND
    │
    ▼
[1] Clean HTML & formatting
    │
    ▼
[2] Too old? (>14 days) ──YES──► REJECTED
    │ NO
    ▼
[3] Salary too low? (if configured) ──YES──► REJECTED
    │ NO
    ▼
[4] Duplicate? (85%+ match) ──YES──► REJECTED
    │ NO
    ▼
[5] German job? (language/flag) ──YES──► REJECTED 🇩🇪
    │ NO
    ▼
[6] Chinese job? (characters/location) ──YES──► REJECTED 🇨🇳
    │ NO
    ▼
[7] Location restricted? (US/Canada/Europe/Asia/Israel) ──YES──► REJECTED 🌍
    │ NO
    ▼
[8] Excluded title? (config.py) ──YES──► REJECTED 🚷
    │ NO
    ▼
[9] Matches INCLUDE_KEYWORDS? ──NO──► REJECTED
    │ YES
    ▼
  Add quality score (⭐) + priority flag (🔴)
    │
    ▼
  SENT TO TELEGRAM ✅
```

### What Gets Filtered:
- 🇩🇪 German language jobs
- 🇨🇳 Chinese jobs (China location or Chinese characters)
- 🌍 US-only, Canada-only, Europe-only, UK-only
- 🌍 Asia, Latin America, Philippines, Brazil, Israel
- 📅 Jobs older than 14 days
- 🚷 Specific excluded titles

### What Gets Through (Nigeria-Friendly):
- ✅ Nigerian-based jobs (Lagos, Abuja, all 36 states)
- ✅ Remote jobs (worldwide)
- ✅ Africa-based jobs
- ✅ UN/NGO jobs
- ✅ Jobs with no location restrictions

---

## Customising Your Job Preferences

Edit `config.py` to control exactly what jobs you receive:

### Add Roles You Want:
```python
INCLUDE_KEYWORDS = [
    "virtual assistant", "customer support", "data entry",
    "remote", "work from home", "admin", "writer",
    "developer", "engineer", "project manager",
    # Add your own keywords here
]
```

### Add Priority Roles (Gets 🔴 tag):
```python
PRIORITY_KEYWORDS = [
    "virtual assistant", "customer support", "data entry",
    "remote customer service", "help desk",
]
```

### Block Specific Titles:
```python
EXCLUDE_TITLES = [
    "cdl driver", "truck driver", "warehouse",
    "convent", "monastery", "pastor",
]
```

### Set Minimum Salary (Optional):
```python
MIN_SALARY_NGN = 80000   # Skip jobs under ₦80,000/month
MIN_SALARY_USD = 300     # Skip jobs under $300/month
# Set to 0 to disable
```

### Skip Old Jobs:
```python
MAX_JOB_AGE_DAYS = 14    # Only jobs from last 14 days
# Set to 0 to disable
```

---

## Installation & Setup

### What You Need
- **GitHub account** (free) — github.com
- **Telegram account** — telegram.org

### Step 1 — Create Your Telegram Bot
1. Open Telegram, search `@BotFather`
2. Send `/newbot` and follow prompts
3. Name it (e.g., `JobScrappers`)
4. Save the **Bot Token** BotFather gives you

### Step 2 — Create Your Telegram Channel
1. Create a new Telegram Channel (private is fine)
2. Add your bot as **Administrator** (can post messages)
3. Forward any message from channel to `@JsonDumpBot`
4. Find the `"id"` field — this is your **Channel ID** (starts with `-100`)

### Step 3 — Create GitHub Repository
1. Go to github.com → **+** → **New repository**
2. Name it `JobScarppers` (or your preferred name)
3. Set to **Private**
4. Click **Create repository**

### Step 4 — Upload Project Files
Upload all files maintaining the structure:
- Root: `README.md`, `requirements.txt`
- `job-bot/`: `main.py`, `config.py`, `filter.py`, `sender.py`, `requirements.txt`
- `job-bot/scrapers/`: all scraper `.py` files
- `.github/workflows/run.yml`

### Step 5 — Add GitHub Secrets
Go to **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Your channel ID (e.g., `-1003869498104`) |

### Step 6 — Enable GitHub Actions
1. Click **Actions** tab
2. If prompted, click **Enable workflows**
3. The bot will start running automatically every 30 minutes

---

## Running the Bot

### Manual Test Run
1. **Actions** tab → **JobScrappers** → **Run workflow** → **Run workflow**
2. Watch the live log, then check your Telegram channel

### Automatic Schedule
The bot runs **every 30 minutes**, 24/7, including weekends.

### Stats & Reports
- 📊 **Monthly report** on the 1st of each month (jobs sent, filtered, top sources)
- ⚠️ **Health alert** if any scraper fails 3 times in a row
- 🔇 **No daily/weekly spam** — only monthly summaries

---

## Resetting the Bot

To clear all history and start fresh:

1. **Settings → Actions → Caches** → Delete all `seen-jobs-...` caches
2. Delete `run_stats.json` and `scraper_health.json` from `job-bot/` folder
3. Run workflow manually

The bot will treat every job as new and send everything.

---

## Telegram Message Format

```
🔴 PRIORITY MATCH          ← Only for priority roles

💼 Virtual Assistant at Acme Global
🏢 Acme Global Ltd
📍 Remote (Worldwide)
💰 $500–800/month
✨ Quality: ⭐⭐⭐⭐

📋 We are looking for a detail-oriented Virtual Assistant to support
our executive team. Responsibilities include calendar management,
email handling, research, and data entry...

_Source: RemoteOK_

[🔗 Apply Now]  ← Clickable button
```

**Category Headers (jobs grouped automatically):**
```
💻 Tech & Development
──────────────────────────────
📞 Customer Support
──────────────────────────────
🗂️ Virtual & Admin
──────────────────────────────
🌍 NGO & UN
──────────────────────────────
🌐 General / Remote
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **No jobs in Telegram** | Check bot is channel admin, verify secrets, run manually and check logs |
| **Scraper shows 0 jobs** | Site may have changed — health alert after 3 failures |
| **German/Chinese jobs getting through** | Update filters in `filter.py` |
| **Wrong jobs being filtered** | Adjust `INCLUDE_KEYWORDS` in `config.py` |
| **Duplicate jobs** | Check cache is persisting (Settings → Actions → Caches) |
| **Import errors** | Ensure all files are in correct folders (`job-bot/` subfolder) |
| **Rate limiting errors** | Built-in retry handles 429 errors automatically |
| **Telegram links showing instead of real links** | Fixed in latest version — extracts real application URLs |

---

## Security Notes

- 🔐 Bot token and channel ID stored as **GitHub Secrets** — never visible in code
- 📁 No personal data stored — only job IDs in `seen_jobs.json`
- 🔄 To revoke bot access: `@BotFather` → `/mybots` → **Revoke token**
- 👁️ Making repo public exposes `config.py` preferences but not credentials

---

## Recent Updates (v2.0)

- ✅ **Name changed to JobScrappers**
- ✅ **30-minute scan interval** 
- ✅ **Simplified filters** — removed haram, alcohol, adult content filters
- ✅ **Telegram link extraction** — sends real application links, not group links
- ✅ **German & Chinese job filtering**
- ✅ **Clean formatting** — no HTML tags or escaped slashes
- ✅ **15 active scrapers** — all free sources
- ✅ **Monthly reports only** — no daily spam
- ✅ **Smart location filtering** — filters out US, Europe, Asia, Israel jobs
- ✅ **Telegram sources always kept** — Nigerian job groups never filtered

---

## Frequently Asked Questions

### Is this really free?
**Yes!** All job sources are free to apply. GitHub Actions free tier handles the automation. No subscriptions, no hidden costs.

### How many jobs will I get?
- Nigerian job boards: 10-30 jobs/day
- Remote global jobs: 20-50 jobs/day (filtered)
- Telegram groups: 5-15 jobs/day
- **Total: 50-150 jobs/day**

### Can I customize what jobs I get?
**Absolutely!** Edit `INCLUDE_KEYWORDS` in `config.py` to match your desired roles.

### What if my laptop is off?
The bot runs on GitHub's cloud servers. Your laptop can be completely off — the bot keeps running.

### How do I stop the bot?
Delete the GitHub repository or disable Actions in repository settings.

---

## License

MIT — Use freely, modify as needed.

---

## Support

Issues? Open a ticket on GitHub. For quick fixes:
- Check Actions logs for errors
- Verify your Telegram bot is admin
- Review `config.py` keywords

---

**Happy Job Hunting! 🎯**
```
