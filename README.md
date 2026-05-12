# 🔍 Job Scraper Bot

A fully automated job alert bot that scrapes **multiple job platforms** across the web and social media, filters out non-Nigeria friendly listings, enforces remote eligibility, and delivers each matching job as a formatted message directly to your private **Telegram channel** every 30 minutes, every day, completely free.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [File-by-File Breakdown](#file-by-file-breakdown)
- [Job Sources](#job-sources)
- [Filter System](#filter-system)
- [Customising Your Job Preferences](#customising-your-job-preferences)
- [Installation & Setup](#installation--setup)
- [Running the Bot](#running-the-bot)
- [Resetting the Bot (Fresh Start)](#resetting-the-bot-fresh-start)
- [Adding New Sources](#adding-new-sources)
- [Telegram Message Format](#telegram-message-format)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)

---

## How It Works

Every time the bot runs (every 30 minutes via GitHub Actions), it follows these steps:

```
1. WAKE UP      — GitHub Actions triggers the script on schedule (every 30 minutes)
2. SCRAPE       — All active scrapers run in sequence, collecting job listings
3. DEDUPLICATE  — Jobs already sent before are skipped (seen_jobs.json)
4. FILTER       — Each job passes through simplified filters (location, language, duplicates)
5. SEND         — Passing jobs are formatted and delivered to Telegram one by one
6. LOG          — Stats are saved and a summary is sent to your channel
7. SLEEP        — Script finishes, GitHub goes back to sleep until next 30 minutes
```

**No server needed. No subscription. No maintenance.** Runs entirely on GitHub's free infrastructure.

---

## Project Structure

```
job-scraper-bot/
│
├── README.md
├── requirements.txt                  ← Python dependencies (root level)
│
├── .github/
│   └── workflows/
│       └── run.yml                   ← GitHub Actions schedule (every 30 minutes)
│
└── job-bot/
    ├── main.py                       ← Entry point — runs everything
    ├── config.py                     ← Your personal job preferences
    ├── filter.py                     ← All filtering logic (simplified)
    ├── sender.py                     ← Formats and sends jobs to Telegram
    ├── seen_jobs.json                ← Auto-generated duplicate tracker
    ├── scraper_health.json           ← Auto-generated scraper health log
    ├── run_stats.json                ← Auto-generated run history
    ├── requirements.txt              ← Python dependencies (bot level)
    │
    └── scrapers/
        │
        ├── — ACTIVE SCRAPERS (17 sources) —
        │
        │   # Global Remote Platforms
        ├── remoteok.py               ← RemoteOK (free public API)
        ├── remotive.py               ← Remotive (free public API)
        ├── themuse.py                ← The Muse (free public API)
        ├── weworkremotely.py         ← WeWorkRemotely (RSS feeds)
        ├── we_work_remotely_enhanced.py ← Enhanced WWR with salary
        ├── workingnomads.py          ← WorkingNomads (JSON API)
        ├── braintrust.py             ← Braintrust (JSON API)
        ├── virtustant.py             ← Virtustant (global hiring)
        ├── wfh_io.py                 ← WFH.io (remote jobs)
        ├── himalayas.py              ← Himalayas (remote job board)
        │
        │   # Nigeria-Specific Platforms
        ├── jobberman.py              ← Jobberman Nigeria (HTML scraper)
        ├── myjobmag.py               ← MyJobMag Nigeria (HTML scraper)
        ├── ngcareers.py              ← NGCareers (HTML scraper)
        ├── jobgurus.py               ← JobGurus Nigeria (HTML scraper)
        │
        │   # International / NGO / Africa
        ├── ngo_jobs.py               ← ReliefWeb API + UN Jobs + Devex
        ├── africa_jobs.py            ← Fuzu, Shortlist.io, AfricaWork
        │
        │   # Social Media
        ├── telegram_channels.py      ← Nigerian job Telegram channels
        │
        └── — SUSPENDED / REMOVED —
            ├── jobicy.py             ← REMOVED (Chinese jobs, poor filtering)
            ├── indeed_ng.py          ← 403 Forbidden
            ├── grabjobs.py           ← 403 Forbidden
            ├── jooble.py             ← 403 - needs paid API key
            ├── dailyremote.py        ← 403 Forbidden
            ├── twitter_jobs.py       ← Nitter fully dead
            ├── arbeitnow.py          ← Germany-focused
            └── others...             ← See main.py for full list
```

---

## File-by-File Breakdown

### `main.py` — The Engine

The entry point and coordinator. When run, it:

- Loads `seen_jobs.json` to track already-sent jobs
- Runs all 17 active scrapers in sequence
- Passes each job through `filter.py`
- Extracts real application links from Telegram messages (not group links)
- Sends passing jobs to Telegram via `sender.py`
- Tracks scraper health — alerts after 3 consecutive failures
- Saves updated data (seen jobs, health stats, run history)
- Sends run summary to your Telegram channel

**Key Features:**
- Removes links from job titles (clean formatting)
- Extracts external job links from Telegram messages
- Never skips jobs with valid links (even short descriptions)
- Shows scraper health summary at the end of each run

---

### `config.py` — Your Control Panel

**This is the only file you need to edit for customisation.**

```python
# Roles you WANT to see (job must match at least one)
INCLUDE_KEYWORDS = [
    "virtual assistant", "customer support", "data entry",
    "remote", "work from home", "admin", "writer", ...
]

# Jobs matching these get 🔴 PRIORITY tag
PRIORITY_KEYWORDS = [
    "virtual assistant", "customer support", "data entry", ...
]

# Block specific titles
EXCLUDE_TITLES = ["cdl driver", "truck driver", "warehouse", ...]

# Minimum salary filters (set to 0 to disable)
MIN_SALARY_NGN = 0       # ₦
MIN_SALARY_USD = 0       # $

# Skip jobs older than this many days (0 = disabled)
MAX_JOB_AGE_DAYS = 14

# Minimum description length (0 = all jobs allowed)
MIN_DESCRIPTION_LENGTH = 0
```

---

### `filter.py` — Simplified Filtering

**Now simplified to focus only on what matters:**

| Filter | What it does |
|--------|---------------|
| 🇩🇪 German Jobs | Blocks jobs with German language or flag |
| 🇨🇳 Chinese Jobs | Blocks jobs with Chinese characters or location |
| 🌍 Location Restricted | Blocks US-only, Europe-only, Brazil, Colombia, Philippines, etc. |
| 📅 Age Filter | Skips jobs older than `MAX_JOB_AGE_DAYS` |
| 💰 Salary Filter | Blocks jobs below minimum (if configured) |
| 🔁 Duplicate Detection | Prevents same job appearing twice (85%+ match) |
| 🚷 Excluded Titles | Blocks specific unwanted titles |
| 📋 Role Match | Job must match `INCLUDE_KEYWORDS` |

**REMOVED FILTERS (for more job opportunities):**
- ❌ Haram keywords (alcohol, gambling, adult content)
- ❌ Non-English filter (was blocking good English jobs)
- ❌ Subscription sources

---

### `sender.py` — Telegram Delivery

Handles all Telegram messaging with:

- **Rate limiting** — 1.5 seconds between messages, handles 429 errors
- **Category grouping** — Jobs grouped under emoji headers (Tech, Support, Admin, etc.)
- **Inline Apply button** — Direct link to job application
- **Clean formatting** — No HTML tags, no escaped slashes, no random characters
- **Priority tagging** — 🔴 flag for your most-wanted roles

**Message Format:**
```
💼 Virtual Assistant at Company Name
🏢 Company Name
📍 Remote
✨ Quality: ⭐⭐⭐⭐

📋 Job description text goes here...

_Source: RemoteOK_

[🔗 Apply Now]  ← Clickable button
```

---

### `seen_jobs.json` — Duplicate Prevention

Auto-created on first run. Stores unique IDs of every job ever sent. Jobs already in this file are skipped instantly. Delete the GitHub Actions cache to reset and start fresh.

---

### `scraper_health.json` — Health Tracking

Tracks consecutive failures per scraper. Sends alert after 3 failures so you know when a source needs fixing.

---

### `run_stats.json` — Run History

Stores last 500 runs with stats (jobs sent, filtered, seen, source breakdown).

---

### `.github/workflows/run.yml` — The Scheduler

```yaml
on:
  schedule:
    - cron: "*/30 * * * *"   # Every 30 minutes
  workflow_dispatch:          # Manual trigger
```

Triggers every 30 minutes, 24/7. Can also be triggered manually from Actions tab.

---

## Job Sources (17 Active)

### Global Remote (11 sources)
| Scraper | Source | Stability |
|---------|--------|-----------|
| RemoteOK | RemoteOK API | ⭐⭐⭐⭐⭐ |
| Remotive | Remotive API | ⭐⭐⭐⭐⭐ |
| TheMuse | The Muse API | ⭐⭐⭐⭐ |
| WeWorkRemotely | RSS feeds | ⭐⭐⭐⭐ |
| WeWorkRemotely+ | Enhanced with salary | ⭐⭐⭐⭐ |
| WorkingNomads | JSON API | ⭐⭐⭐⭐ |
| Braintrust | JSON API | ⭐⭐⭐⭐ |
| Virtustant | HTML scraper | ⭐⭐⭐ |
| WFH.io | HTML scraper | ⭐⭐⭐ |
| Himalayas | Free API | ⭐⭐⭐⭐ |

### Nigeria-Specific (4 sources)
| Scraper | Source | Stability |
|---------|--------|-----------|
| Jobberman | HTML scraper | ⭐⭐⭐ |
| MyJobMag | HTML scraper | ⭐⭐⭐ |
| NGCareers | HTML scraper | ⭐⭐⭐ |
| JobGurus | HTML scraper | ⭐⭐⭐ |

### International / NGO / Africa (2 sources)
| Scraper | Source | Stability |
|---------|--------|-----------|
| NGO / UN Jobs | ReliefWeb API | ⭐⭐⭐⭐ |
| Africa Jobs | HTML scraper | ⭐⭐⭐ |

### Social Media (1 source)
| Scraper | Source | Notes |
|---------|--------|-------|
| Telegram | t.me preview | Enhanced with link extraction |

**Telegram channels monitored:**
- `@jbtoday` — Jobstoday Nigeria
- `@jobnownigeria` — Jobnow Nigeria
- `@careermattersng` — Careermatters NG
- `@jobnetworkng` — Latest Jobs in Nigeria
- `@JobsinNigeriadaily` — Jobs in Nigeria Daily
- `@jobsnigeria001rekrutconsulting` — Job Vacancies Nigeria
- `@WorkaNigeria` — Worka Nigeria
- `@remotejobss` — Remote Jobs (Worldwide)

---

## Filter System (Simplified)

```
JOB FOUND
    │
    ▼
[1] Clean HTML & formatting
    │
    ▼
[2] Too old? ──YES──► REJECTED
    │ NO
    ▼
[3] Salary too low? ──YES──► REJECTED
    │ NO
    ▼
[4] Duplicate? ──YES──► REJECTED
    │ NO
    ▼
[5] German job? ──YES──► REJECTED 🇩🇪
    │ NO
    ▼
[6] Chinese job? ──YES──► REJECTED 🇨🇳
    │ NO
    ▼
[7] Location restricted? ──YES──► REJECTED 🌍
    │ NO
    ▼
[8] Excluded title? ──YES──► REJECTED 🚷
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

**What gets filtered:**
- 🇩🇪 German language jobs
- 🇨🇳 Chinese jobs (China location or Chinese characters)
- 🌍 US-only, Europe-only, Brazil, Colombia, Philippines, etc.
- 📅 Jobs older than 14 days
- 🚷 Specific excluded titles

**What gets through:**
- ✅ All remote jobs
- ✅ Nigeria-based jobs
- ✅ Worldwide remote opportunities
- ✅ Jobs with no location restrictions

---

## Customising Your Job Preferences

Open `config.py` and edit:

### Add a role you want:
```python
INCLUDE_KEYWORDS = [
    ...
    "grant writer",
    "research assistant",
]
```

### Add a priority role (gets 🔴 tag):
```python
PRIORITY_KEYWORDS = [
    ...
    "remote customer service",
]
```

### Block a role:
```python
EXCLUDE_TITLES = [
    ...
    "vice president",
]
```

### Set minimum salary:
```python
MIN_SALARY_USD = 300     # Skip jobs under $300/month
MIN_SALARY_NGN = 80000   # Skip jobs under ₦80,000/month
```

### Skip old listings:
```python
MAX_JOB_AGE_DAYS = 7     # Only last 7 days
```

---

## Installation & Setup

### What You Need
- **GitHub account** (free) — github.com
- **Telegram account** — telegram.org

### Step 1 — Create Your Telegram Bot
1. Open Telegram, search `@BotFather`
2. Send `/newbot` and follow prompts
3. Name it (e.g., `Job Scraper Nigeria`)
4. Save the **Bot Token** BotFather gives you

### Step 2 — Create Your Telegram Channel
1. Create a new Telegram Channel (private is fine)
2. Add your bot as **Administrator** (can post messages)
3. Forward any message from channel to `@JsonDumpBot`
4. Find the `"id"` field — this is your **Channel ID** (starts with `-100`)

### Step 3 — Fork or Create Repository
1. Go to github.com → **+** → **New repository**
2. Name it `job-scraper-bot`, set to **Private**
3. Upload all files maintaining the structure:
   - Root: `README.md`, `requirements.txt`
   - `job-bot/`: `main.py`, `config.py`, `filter.py`, `sender.py`, `requirements.txt`
   - `job-bot/scrapers/`: all scraper `.py` files
   - `.github/workflows/run.yml`

### Step 4 — Add Secrets
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Your channel ID (e.g., `-1003869498104`) |

### Step 5 — Enable GitHub Actions
1. Click **Actions** tab
2. If prompted, click **Enable workflows**

---

## Running the Bot

### Manual Test Run
1. **Actions** tab → **Job Scraper Bot** → **Run workflow** → **Run workflow**
2. Watch the live log, then check your Telegram channel

### Automatic Schedule
The bot runs **every 30 minutes**, 24/7, including weekends.

### Stats & Reports
- 📊 Run summary after each run (jobs sent, filtered, seen)
- ⚠️ Health alert if any scraper fails 3 times in a row
- 📈 Source breakdown showing which platforms found jobs

---

## Resetting the Bot (Fresh Start)

To clear all history and start fresh:

1. **Settings → Actions → Caches** → Delete all `seen-jobs-...` caches
2. Delete `run_stats.json` and `scraper_health.json` from `job-bot/` folder
3. Run workflow manually

The bot will treat every job as new and send everything.

---

## Adding New Sources

### To add a new job board:

1. Create `scrapers/newsource.py`:
```python
def scrape_newsource():
    jobs = []
    # Your scraping logic here
    jobs.append({
        "title": "Job Title",
        "company": "Company Name",
        "location": "Remote",
        "description": "Job description",
        "url": "https://apply.com",
        "source": "NewSource",
    })
    return jobs
```

2. Import in `main.py`:
```python
from scrapers.newsource import scrape_newsource
```

3. Add to scrapers list:
```python
scrapers = [
    ...
    ("NewSource", scrape_newsource),
]
```

### To add a Telegram channel:
Add username to `TELEGRAM_JOB_CHANNELS` in `scrapers/telegram_channels.py`

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
🌍 General / Remote
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **No jobs in Telegram** | Check bot is channel admin, verify secrets, run manually and check logs |
| **Scraper shows 0 jobs** | Site may have changed structure — health alert will notify after 3 failures |
| **German/Chinese jobs getting through** | Update `GERMAN_INDICATORS` or `CHINESE_INDICATORS` in `filter.py` |
| **Wrong jobs being filtered** | Adjust `INCLUDE_KEYWORDS` in `config.py` |
| **Duplicate jobs** | Check `seen_jobs.json` cache is persisting (Settings → Actions → Caches) |
| **HTML in descriptions** | `strip_html()` handles this — shouldn't appear in current version |
| **Rate limiting errors** | Built-in retry with exponential backoff handles 429 errors |

---

## Security Notes

- 🔐 Bot token and channel ID stored as **GitHub Secrets** — never visible in code
- 📁 No personal data stored — only job IDs in `seen_jobs.json`
- 🔄 To revoke bot access: `@BotFather` → `/mybots` → **Revoke token**
- 👁️ Making repo public exposes `config.py` preferences but not credentials

---

## Recent Updates

### v2.0 (Current)
- ✅ **Renamed to Job Scraper Bot**
- ✅ **30-minute scan interval** (was 1 hour)
- ✅ **Simplified filters** — removed haram, alcohol, adult content filters
- ✅ **Telegram link extraction** — sends real application links, not group links
- ✅ **German & Chinese job filtering** — blocks non-English opportunities
- ✅ **Clean formatting** — no HTML tags, no escaped slashes
- ✅ **17 active scrapers** — removed Jobicy (Chinese jobs)

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
