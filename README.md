# 🕌 Halal Jobs Bot

A fully automated job alert bot that scrapes **different job platforms** across the web and social media, filters out haram industries, enforces English-only listings, checks Nigeria/remote eligibility, and delivers each matching job as a formatted message directly to your private **Telegram channel** every hour, every day, for free.

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

Every time the bot runs (every 5-minutes via GitHub Actions), it follows these steps:

```
1. WAKE UP      — GitHub Actions triggers the script on schedule (every 5-minutes)
2. SCRAPE       — All active scrapers run in sequence, collecting job listings
3. DEDUPLICATE  — Jobs already sent before are skipped (seen_jobs.json)
4. FILTER       — Each job passes through multiple filter layers
5. SEND         — Passing jobs are formatted and delivered to Telegram one by one
6. LOG          — Stats are saved and a summary is sent to your channel
7. SLEEP        — Script finishes, GitHub goes back to sleep until next 5-minutes
```

No server needed. No subscription. Runs entirely on GitHub's free infrastructure.

---

## Project Structure

```
halal-jobs-bot/
│
├── README.md
├── requirements.txt                  ← Python dependencies (root level)
│
├── .github/
│   └── workflows/
│       └── run.yml                   ← GitHub Actions schedule (every 5-minutes)
│
└── job-bot/
    ├── main.py                       ← Entry point — runs everything
    ├── config.py                     ← Your personal job preferences
    ├── filter.py                     ← All filtering logic
    ├── sender.py                     ← Formats and sends jobs to Telegram
    ├── seen_jobs.json                ← Auto-generated duplicate tracker
    ├── scraper_health.json           ← Auto-generated scraper health log
    ├── run_stats.json                ← Auto-generated run history
    ├── requirements.txt              ← Python dependencies (bot level)
    │
    └── scrapers/
        │
        ├── — ACTIVE SCRAPERS —
        │
        ├── remoteok.py               ← RemoteOK (free public API)
        ├── remotive.py               ← Remotive (free public API)
        ├── themuse.py                ← The Muse (free public API)
        ├── weworkremotely.py         ← WeWorkRemotely (RSS feeds)
        ├── workingnomads.py          ← WorkingNomads (JSON API)
        ├── braintrust.py             ← Braintrust (JSON API, global talent)
        ├── dailyremote.py            ← DailyRemote (HTML scraper)
        ├── virtustant.py             ← Virtustant (global hiring, free)
        ├── linkedin_rss.py           ← LinkedIn (RSS feed, no login)
        ├── indeed_ng.py              ← Indeed Nigeria (HTML scraper)
        ├── jobberman.py              ← Jobberman Nigeria (HTML scraper)
        ├── myjobmag.py               ← MyJobMag Nigeria (HTML scraper)
        ├── ngcareers.py              ← NGCareers (HTML scraper)
        ├── grabjobs.py               ← GrabJobs Nigeria (HTML scraper)
        ├── jooble.py                 ← Jooble Nigeria (JSON API)
        ├── doballi.py                ← Doballi Africa (HTML scraper)
        ├── jobgurus.py               ← JobGurus Nigeria (HTML scraper)
        ├── ngo_jobs.py               ← ReliefWeb API + UN Jobs + Devex
        ├── africa_jobs.py            ← Fuzu, Shortlist.io, AfricaWork
        ├── telegram_channels.py      ← Nigerian job Telegram channels
        ├── twitter_jobs.py           ← X/Twitter job accounts (via Nitter)
        │
        └── — AVAILABLE BUT SUSPENDED —
            ├── arbeitnow.py          ← Arbeitnow (Germany-focused, disabled)
            ├── startupjobs.py        ← StartupJobs (disabled)
            ├── dynamitejobs.py       ← DynamiteJobs (abroad-focused, disabled)
            ├── oneforma.py           ← OneForma (data annotation, disabled)
            └── freelance.py          ← PeoplePerHour/Guru/Freelancer (disabled)
```

---

## File-by-File Breakdown

### `main.py` — The Engine

The entry point and coordinator of the entire bot. When run, it:

- Loads `seen_jobs.json` to know which jobs were already sent
- Runs all active scrapers in sequence, collecting listings
- Passes each job through `filter.py`
- Sends passing jobs to Telegram via `sender.py`
- Tracks scraper health — alerts you if any scraper fails 3 runs in a row
- Saves updated seen jobs, health data, and run stats
- Sends a stats summary to your Telegram channel after each run
- Sends a weekly report every Sunday

Scrapers are clearly organised into sections inside the file: Nigeria-specific, global remote, and social media. Suspended scrapers are commented out with notes explaining why.

---

### `config.py` — Your Control Panel

**This is the main file you edit to customise what jobs you receive.**

It has five sections:

**`INCLUDE_KEYWORDS`** — A job must match at least one keyword here to reach your channel. Covers roles across: Virtual Assistant, Admin, Customer Support, Writing, Tech, Data, Finance, Marketing, HR, Teaching, Transcription, and General Remote.

**`PRIORITY_KEYWORDS`** — Jobs matching these get a 🔴 PRIORITY tag in Telegram. Use for roles you are actively hunting right now (e.g. "virtual assistant", "customer support").

**`EXCLUDE_TITLES`** — Blocks specific job titles even if they pass all other filters. Use for roles that are simply not relevant to you.

**`MIN_SALARY_NGN / MIN_SALARY_USD`** — Optional minimum salary filter. Jobs that explicitly advertise a salary below your threshold are skipped. Set to `0` to disable.

**`MAX_JOB_AGE_DAYS`** — Skip jobs older than this many days. Default is `14`. Set to `0` to disable.

**`MIN_DESCRIPTION_LENGTH`** — Minimum character count for job descriptions. Filters out very low-quality listings with no detail. Default is `0` (all jobs allowed).

---

### `filter.py` — The Multi-Layer Filter

Every job passes through all layers in order. Failing any one layer rejects it.

**Layer 1 — HTML Cleaning**
Before any checks, all HTML tags and entities are stripped from job descriptions. This fixes the raw `<p><span style=...>` issue that appeared in early versions.

**Layer 2 — Subscription Source Check**
Blocks jobs from platforms that require paid membership to apply (e.g. The Ladders, job-hunt.org).

**Layer 3 — Minimum Description Check**
Skips jobs whose description is too short to be useful (configurable in `config.py`).

**Layer 4 — Age Filter**
Skips jobs older than `MAX_JOB_AGE_DAYS` when a posting date is available.

**Layer 5 — Salary Filter**
Skips jobs that explicitly advertise a salary below your minimum threshold.

**Layer 6 — Fuzzy Duplicate Detection**
Within a single run, if two jobs from different sources have a title + company that are 85%+ similar, the second one is skipped. Prevents the same job appearing twice from different platforms.

**Layer 7 — Haram Keyword Filter**
Scans title, company, description, and tags for haram-related terms. Categories: gambling, alcohol, nightlife, non-Islamic religious institutions, adult content, pork, riba/predatory lending, tobacco, and drugs.

**Layer 8 — English-Only Filter**
Rejects jobs requiring fluency in a foreign language (German, French, Spanish, Portuguese, Mandarin, Japanese, Korean, Dutch, Italian, etc.).

**Layer 9 — Nigeria-Friendly Filter**
Blocks jobs that explicitly restrict by citizenship or residency (e.g. "US only", "EU only", "must have right to work in UK", "security clearance"). Remote/worldwide jobs are always allowed through.

**Layer 10 — Excluded Titles**
Blocks job titles listed in `EXCLUDE_TITLES` in `config.py`.

**Layer 11 — Job Preference Match**
The job must match at least one keyword from `INCLUDE_KEYWORDS`. If nothing matches, it is rejected.

**Quality Score & Priority Tag**
After passing all layers, each job is scored 1–5 stars based on completeness (has salary? description? direct link? tags?). Jobs matching `PRIORITY_KEYWORDS` are tagged 🔴 PRIORITY.

---

### `sender.py` — Telegram Delivery

Handles formatting and sending each job to your channel.

**`format_job()`** — Builds a clean Telegram message with emoji labels: title, company, location, salary, experience, tags, quality stars, description snippet, source.

**`get_category()`** — Determines which job category the listing belongs to (Tech, Customer Support, Writing, Admin, etc.) and groups jobs under category headers in your channel.

**`send_job()`** — Posts the formatted message with an inline **Apply Now** button via the Telegram Bot API. Includes a 1-second delay between messages to respect rate limits.

**`send_stats()`** — Sends a run summary to your channel showing jobs sent, filtered, already seen, and top sources.

**`send_health_alert()`** — Sends an alert when any scraper has failed 3 consecutive runs.

**`_send_text()`** — Internal helper for sending plain formatted messages (used by stats, alerts, weekly report, and category headers).

Credentials (bot token and channel ID) are read from environment variables — never hardcoded.

---

### `seen_jobs.json` — Duplicate Prevention

Auto-created on first run. Stores the unique ID of every job ever evaluated. Jobs already in this file are skipped instantly on future runs. You never need to edit this manually. To reset it and start fresh, delete the GitHub Actions cache (see [Resetting the Bot](#resetting-the-bot-fresh-start)).

---

### `scraper_health.json` — Health Tracking

Auto-generated. Tracks how many consecutive failures each scraper has had, and the timestamp of its last success. Used by `main.py` to send health alerts when something consistently breaks.

---

### `run_stats.json` — Run History

Auto-generated. Stores the stats from the last 500 runs (timestamp, jobs sent, filtered, seen, source breakdown). Used by `main.py` to produce the weekly Sunday report.

---

### `requirements.txt` — Dependencies

```
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.1.0
```

- `requests` — HTTP calls to APIs and websites
- `beautifulsoup4` — HTML parsing and scraping
- `lxml` — faster, more reliable HTML parser for BeautifulSoup

---

### `.github/workflows/run.yml` — The Scheduler

GitHub Actions workflow file. It:

- Triggers **every hour**, 24 hours a day, 7 days a week
- Can also be triggered manually from the Actions tab at any time
- Sets up Python 3.11, installs dependencies, restores the seen_jobs cache, runs the bot, and saves the updated cache
- Injects `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` securely from GitHub Secrets

---

## Job Sources

### Active — Global Remote Platforms

| Scraper | Source | Method |
|---|---|---|
| `remoteok.py` | RemoteOK | Free public JSON API |
| `remotive.py` | Remotive | Free public JSON API |
| `themuse.py` | The Muse | Free public JSON API |
| `weworkremotely.py` | WeWorkRemotely | RSS feeds (5 categories) |
| `workingnomads.py` | WorkingNomads | JSON API (10 categories) |
| `braintrust.py` | Braintrust | JSON API (global talent network) |
| `dailyremote.py` | DailyRemote | HTML scraper |
| `virtustant.py` | Virtustant | HTML scraper (hires globally) |
| `linkedin_rss.py` | LinkedIn | RSS feed (no login needed) |

### Active — Nigeria-Specific Platforms

| Scraper | Source | Method |
|---|---|---|
| `indeed_ng.py` | Indeed Nigeria | HTML scraper |
| `jobberman.py` | Jobberman | HTML scraper |
| `myjobmag.py` | MyJobMag Nigeria | HTML scraper |
| `ngcareers.py` | NGCareers | HTML scraper |
| `grabjobs.py` | GrabJobs Nigeria | HTML scraper |
| `jooble.py` | Jooble Nigeria | JSON API |
| `doballi.py` | Doballi (Africa) | HTML scraper |
| `jobgurus.py` | JobGurus Nigeria | HTML scraper |

### Active — International / NGO / Africa

| Scraper | Source | Method |
|---|---|---|
| `ngo_jobs.py` | ReliefWeb API, UN Jobs, Devex | API + HTML |
| `africa_jobs.py` | Fuzu Nigeria, Shortlist.io, AfricaWork | HTML scraper |

### Active — Social Media

| Scraper | Source | Method |
|---|---|---|
| `telegram_channels.py` | Nigerian job Telegram channels | t.me public web preview |
| `twitter_jobs.py` | X/Twitter job accounts | Nitter public mirror |

**Telegram channels monitored:**
- `@jbtoday` — Jobstoday Nigeria
- `@jobnownigeria` — Jobnow Nigeria
- `@careermattersng` — Careermatters NG
- `@jobnetworkng` — Latest Jobs in Nigeria
- `@JobsinNigeriadaily` — Jobs in Nigeria Daily
- `@jobsnigeria001rekrutconsulting` — Job Vacancies Nigeria
- `@WorkaNigeria` — Worka Nigeria (Web2 & Web3)
- `@remotejobss` — Remote Jobs (Worldwide)

**X/Twitter accounts monitored:**
- `@BenoHr80463`, `@JobFound5`, `@jobsregion`, `@TrybeCityJobs`, `@Halosznn_`
- `@NgJobAlert`, `@RemoteJobsNG`, `@JobsInNigeria`, `@AfricaJobs`, `@RemoteJobsAfrica`

> **Note:** WhatsApp channels cannot be scraped — WhatsApp encrypts all content and has no public API or web preview. The Telegram channels above cover equivalent Nigerian job content.

### Suspended (Available to Re-enable)

| Scraper | Reason Suspended |
|---|---|
| `arbeitnow.py` | Primarily Germany-focused listings |
| `dynamitejobs.py` | Mostly abroad/non-Nigeria roles |
| `startupjobs.py` | Low Nigeria relevance |
| `oneforma.py` | Data annotation only — re-enable if interested |
| `freelance.py` | PeoplePerHour, Guru, Freelancer — re-enable if you want freelance gigs |

To re-enable any suspended scraper, simply uncomment its import and entry in `main.py`.

---

## Filter System

```
JOB FOUND
    │
    ▼
[1]  Strip HTML from description
    │
    ▼
[2]  Subscription source? ──YES──► REJECTED
    │ NO
    ▼
[3]  Description too short? ──YES──► REJECTED
    │ NO
    ▼
[4]  Job too old? ──YES──► REJECTED
    │ NO
    ▼
[5]  Salary below minimum? ──YES──► REJECTED
    │ NO
    ▼
[6]  Fuzzy duplicate from another source this run? ──YES──► REJECTED
    │ NO
    ▼
[7]  Contains haram keyword? ──YES──► REJECTED
    │ NO
    ▼
[8]  Requires foreign language? ──YES──► REJECTED
    │ NO
    ▼
[9]  Restricted to non-Nigeria region? ──YES──► REJECTED
    │ NO
    ▼
[10] Title in EXCLUDE_TITLES? ──YES──► REJECTED
    │ NO
    ▼
[11] Matches INCLUDE_KEYWORDS? ──NO──► REJECTED
    │ YES
    ▼
  Tag quality score (⭐–⭐⭐⭐⭐⭐) + priority flag (🔴)
    │
    ▼
  SENT TO TELEGRAM ✅
```

---

## Customising Your Job Preferences

Open `config.py` in your GitHub repo and edit freely:

**Add a new role you want:**
```python
INCLUDE_KEYWORDS = [
    ...
    "grant writer",
    "research assistant",
    "community manager",
]
```

**Add a priority role (gets 🔴 tag):**
```python
PRIORITY_KEYWORDS = [
    ...
    "remote customer service",
]
```

**Block a role:**
```python
EXCLUDE_TITLES = [
    ...
    "vice president",
]
```

**Set minimum salary:**
```python
MIN_SALARY_USD = 300     # Skip jobs showing less than $300/month
MIN_SALARY_NGN = 80000   # Skip jobs showing less than ₦80,000/month
```

**Skip old listings:**
```python
MAX_JOB_AGE_DAYS = 7    # Only show jobs posted in the last 7 days
```

No other files need changing. `filter.py` reads `config.py` automatically.

---

## Installation & Setup

### What You Need
- A **GitHub account** (free) — github.com
- A **Telegram account** — telegram.org

### Step 1 — Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Name it (e.g. `Halal Jobs Nigeria`) and give it a username ending in `bot`
4. BotFather gives you a **Bot Token** — save it

### Step 2 — Create Your Telegram Channel
1. Create a new Telegram Channel (private is fine)
2. Add your bot as an **Administrator** with permission to post messages
3. Forward any message from the channel to `@JsonDumpBot`
4. Find the `"id"` field in the JSON — this is your **Channel ID** (starts with `-100`)

### Step 3 — Create the GitHub Repository
1. Go to github.com → **+** → **New repository**
2. Name it `halal-jobs-bot`, set to **Private**
3. Click **Create repository**

### Step 4 — Upload the Project Files
Upload all files maintaining the folder structure:
- Root: `README.md`, `requirements.txt`
- `job-bot/`: `main.py`, `config.py`, `filter.py`, `sender.py`, `requirements.txt`
- `job-bot/scrapers/`: all scraper `.py` files
- For the workflow file, create it via **Add file → Create new file** named `.github/workflows/run.yml`

### Step 5 — Add Your Secrets
Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Your channel ID (e.g. `-1003869498104`) |

### Step 6 — Enable GitHub Actions
1. Click the **Actions** tab in your repo
2. If prompted, click **Enable workflows**

---

## Running the Bot

### Manual Test Run
1. Go to the **Actions** tab
2. Click **Halal Jobs Bot** on the left
3. Click **Run workflow** → **Run workflow**
4. Watch the live log — then check your Telegram channel

### Automatic Schedule
The bot runs **every hour**, 24/7, including weekends.

### Stats & Reports
- After each run that sends jobs, a 📊 stats summary is sent to your channel
- Every **Sunday**, a weekly report is sent showing working/broken scrapers and total jobs sent that week
- If any scraper fails 3 runs in a row, a ⚠️ health alert is sent immediately

---

## Resetting the Bot (Fresh Start)

To clear all history and have the bot send all jobs as if starting fresh:

1. In your GitHub repo go to **Settings → Actions → Caches**
2. Delete any cache named `seen-jobs-...`
3. Also delete `run_stats.json` and `scraper_health.json` from the `job-bot/` folder if they exist
4. Run the workflow manually

The bot will treat every job as new and send everything it finds.

---

## Adding New Sources

**To add a new job board:**

1. Create `scrapers/mynewsource.py` with a function returning this format:
```python
{
    "id":          "unique_id_string",
    "title":       "Job Title",
    "company":     "Company Name",
    "location":    "Remote / Nigeria",
    "salary":      "₦200,000/month",
    "description": "Job description text",
    "tags":        "remote, full-time",
    "date_posted": "2026-05-01",        # optional
    "url":         "https://apply.com",
    "source":      "MyNewSource",
}
```

2. Import and add it to the scrapers list in `main.py`:
```python
from scrapers.mynewsource import scrape_mynewsource

scrapers = [
    ...
    ("MyNewSource", scrape_mynewsource),
]
```

**To add a Telegram channel:**
Add its username to `TELEGRAM_JOB_CHANNELS` in `scrapers/telegram_channels.py`.

**To re-enable a suspended scraper:**
Uncomment its import and list entry in `main.py`.

---

## Telegram Message Format

```
🔴 PRIORITY MATCH          ← only on priority roles

💼 Virtual Assistant (Remote)
🏢 Acme Global Ltd
📍 Remote (Worldwide)
💰 $500–$800/month
📊 Entry Level
🏷️ admin, remote, part-time
✨ Quality: ⭐⭐⭐⭐

📋 We are looking for a detail-oriented Virtual Assistant to support
our executive team. Responsibilities include calendar management,
email handling, research, and data entry...

Source: Virtustant

[ 🔗 Apply Now ]           ← inline button
```

Jobs are grouped under category headers:
```
💻 Tech & Development
──────────────────────────────
📞 Customer Support
──────────────────────────────
🗂️ Virtual & Admin
```

---

## Troubleshooting

**Jobs not appearing in Telegram**
- Confirm your bot is an Administrator of the channel with posting rights
- Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` are correct in GitHub Secrets
- Run the workflow manually and expand **Run python main.py** to read the logs
- Check your channel ID starts with `-100`

**A scraper shows 0 jobs every run**
- The site may have changed its HTML structure
- The site may be temporarily blocking requests
- API-based scrapers (RemoteOK, Remotive, Jooble) are the most stable
- You will receive a ⚠️ health alert automatically after 3 consecutive failures

**Jobs arriving that don't match my roles**
- Tighten your `INCLUDE_KEYWORDS` list in `config.py`
- Add unwanted titles to `EXCLUDE_TITLES`

**The same job appearing twice**
- The fuzzy duplicate filter handles this within a single run
- For cross-run duplicates, check the seen_jobs cache is persisting (Settings → Actions → Caches)

**HTML tags in descriptions** (e.g. `<p><span style=...>`)
- Handled automatically by `filter.py`'s `strip_html()` — should not happen on current version

**Want to re-enable a suspended scraper?**
- Uncomment its import and list entry in `main.py` and commit

---

## Security Notes

- Bot token and channel ID stored as **GitHub Secrets** — never visible in code or logs
- No personal data stored anywhere — only job IDs in `seen_jobs.json`
- To revoke bot access: `@BotFather` → `/mybots` → **Revoke token**
- Making the repo public exposes your `config.py` keyword preferences but not your credentials
