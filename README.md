# 🔍 JobScrappers

> A fully automated job alert bot that scrapes **15+ job platforms** and delivers clean job listings directly to your private **Telegram channel** every 30 minutes — completely free.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Project Structure](#project-structure)
- [Job Sources](#job-sources)
- [What Gets Filtered](#what-gets-filtered)
- [Installation & Setup](#installation--setup)
- [Running the Bot](#running-the-bot)
- [Resetting the Bot](#resetting-the-bot)
- [Telegram Message Format](#telegram-message-format)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [FAQ](#frequently-asked-questions)

---

## How It Works

Every 30 minutes, GitHub Actions wakes the bot and runs the full pipeline:

```
1. WAKE UP      — GitHub Actions triggers the script
2. SCRAPE       — 15+ scrapers collect job listings
3. DEDUPLICATE  — Jobs already sent are skipped
4. FILTER       — Location & language filters applied
5. SEND         — Jobs sent to Telegram with an Apply button
6. LOG          — Stats saved (monthly reports only)
7. SLEEP        — Script finishes until next run
```

**No server needed. No subscription. Runs entirely on GitHub's free infrastructure.**

---

## Features

| | Feature |
|---|---|
| ✅ | **15+ Active Job Sources** — Nigerian boards, global remote, NGO, Telegram groups |
| ✅ | **Runs Every 30 Minutes** — Never miss an opportunity |
| ✅ | **Smart Filtering** — Filters out US-only, Europe-only, Asia, and Israel jobs |
| ✅ | **Clean Telegram Messages** — Just the job title and an Apply Now button |
| ✅ | **Real Application Links** — Direct apply links, not group redirects |
| ✅ | **Monthly Reports Only** — One summary on the 1st of each month, no spam |
| ✅ | **Automatic Health Alerts** — Notified if any scraper fails |
| ✅ | **Completely Free** — All sources are free to apply; runs on GitHub's free tier |

---

## Project Structure

```
JobScrappers/
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
    ├── config.py                     ← Your preferences
    ├── filter.py                     ← Filtering logic
    ├── sender.py                     ← Telegram formatter
    ├── seen_jobs.json                ← Auto-generated
    ├── scraper_health.json           ← Auto-generated
    ├── run_stats.json                ← Auto-generated
    ├── requirements.txt
    │
    └── scrapers/
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

## Job Sources

### 🇳🇬 Nigeria-Specific

| Scraper | Source |
|---------|--------|
| Jobberman | Nigerian job board |
| MyJobMag | Nigerian job board |
| NGCareers | Nigerian job board |
| JobGurus | Nigerian job board |

### 🌍 International / NGO / Africa

| Scraper | Source |
|---------|--------|
| NGO / UN Jobs | ReliefWeb API |
| Africa Jobs | African job boards |

### 🌐 Global Remote

| Scraper | Source |
|---------|--------|
| RemoteOK | RemoteOK API |
| Remotive | Remotive API |
| TheMuse | The Muse API |
| WorkingNomads | JSON API |
| Braintrust | JSON API |
| Himalayas | Free API |
| WFH.io | HTML scraper |
| Virtustant | HTML scraper |

### 💬 Telegram Channels

| Channel |
|---------|
| @jbtoday |
| @jobnownigeria |
| @careermattersng |
| @jobnetworkng |
| @WorkaNigeria |
| @remotejobss |
| @techjobsworld |

---

## What Gets Filtered

The bot automatically filters out jobs that Nigerians cannot apply to:

| Filter | Examples |
|--------|----------|
| 🇩🇪 German Jobs | Jobs in German or requiring German |
| 🇨🇳 Chinese Jobs | Jobs in Chinese or located in China |
| 🌍 Location-Restricted | US-only, Canada-only, UK-only, Europe-only |
| 🌏 Region-Restricted | Asia-only, Latin America, Philippines, Brazil |
| 🇮🇱 Country-Restricted | Israel jobs |
| 📅 Old Listings | Jobs older than 14 days (configurable) |

**What gets through:**

- ✅ Nigerian-based jobs (Lagos, Abuja, all 36 states)
- ✅ Remote jobs (worldwide / open)
- ✅ Africa-based jobs
- ✅ UN / NGO jobs
- ✅ All Telegram channel jobs (Nigeria-focused, never filtered)

---

## Installation & Setup

### Prerequisites

- A free **GitHub account** — [github.com](https://github.com)
- A **Telegram account** — [telegram.org](https://telegram.org)

---

### Step 1 — Create Your Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Give it a name (e.g., `JobScrappers`)
4. Save the **Bot Token** BotFather provides

### Step 2 — Create Your Telegram Channel

1. Create a new Telegram Channel (private is fine)
2. Add your bot as an **Administrator** with permission to post messages
3. Forward any message from the channel to `@JsonDumpBot`
4. Find the `"id"` field — this is your **Channel ID** (starts with `-100`)

### Step 3 — Create a GitHub Repository

1. Go to [github.com](https://github.com) → **+** → **New repository**
2. Name it `JobScrappers`
3. Set visibility to **Private**
4. Click **Create repository**

### Step 4 — Upload Project Files

Upload all files maintaining the folder structure:

- Root: `README.md`, `requirements.txt`
- `job-bot/`: `main.py`, `config.py`, `filter.py`, `sender.py`, `requirements.txt`
- `job-bot/scrapers/`: all scraper `.py` files
- `.github/workflows/run.yml`

### Step 5 — Add GitHub Secrets

Navigate to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Your channel ID (e.g., `-1003869498104`) |

### Step 6 — Enable GitHub Actions

1. Click the **Actions** tab in your repository
2. If prompted, click **Enable workflows**
3. The bot will begin running automatically every 30 minutes

---

## Running the Bot

### Manual Test Run

1. Go to **Actions** → **JobScrappers** → **Run workflow** → **Run workflow**
2. Watch the live log, then check your Telegram channel

### Automatic Schedule

Once enabled, the bot runs **every 30 minutes, 24/7**, including weekends. Your laptop can be completely off — it runs on GitHub's cloud.

### Reports & Alerts

- 📊 **Monthly report** on the 1st of each month (jobs sent, filtered, top sources)
- ⚠️ **Health alert** if any scraper fails 3 times in a row
- 🔇 No daily or weekly spam

---

## Resetting the Bot

To clear all history and start fresh:

1. Go to **Settings → Actions → Caches** and delete all `seen-jobs-...` caches
2. Delete `run_stats.json` and `scraper_health.json` from the `job-bot/` folder
3. Run the workflow manually

The bot will treat every job as new and send everything again.

---

## Telegram Message Format

Each job appears as a single clean message:

```
💼 Content Marketer Job at Right Click Technologies LTD

[🔗 Apply Now]
```

No descriptions. No clutter. Just the title and a direct apply button.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No jobs in Telegram | Confirm the bot is a channel admin, verify secrets are set, run manually and check logs |
| Scraper shows 0 jobs | The site may have changed its structure — a health alert fires after 3 failures |
| Wrong jobs appearing | Adjust location filters in `filter.py` |
| Duplicate jobs | Confirm the cache is persisting under **Settings → Actions → Caches** |
| Import errors | Ensure all files are in the correct subfolders (especially `job-bot/`) |
| Rate limiting errors | Built-in retry logic handles 429 errors automatically |

---

## Security Notes

- 🔐 Bot token and channel ID are stored as **GitHub Secrets** — never exposed in code
- 📁 No personal data is stored — only job IDs in `seen_jobs.json`
- 🔄 To revoke bot access: open `@BotFather` → `/mybots` → **Revoke token**
- 👁️ Making the repo public exposes your configuration but not your credentials

---

## Frequently Asked Questions

**Is this really free?**
Yes. All job sources are free to apply to. GitHub Actions' free tier handles the automation with no subscriptions or hidden costs.

**How many jobs will I get?**
Roughly 50–150 jobs per day across all sources (Nigerian boards: 10–30/day, remote global: 20–50/day filtered, Telegram groups: 5–15/day).

**What if my laptop is off?**
The bot runs on GitHub's cloud servers. Your device being off has no effect.

**How do I stop the bot?**
Delete the GitHub repository or disable Actions in your repository settings.

**Why are some jobs not showing?**
Jobs restricted to the US, Europe, Asia, Israel, or requiring German/Chinese are filtered out since they are not accessible to Nigerian applicants.

---

## License

MIT — Use freely, modify as needed.
