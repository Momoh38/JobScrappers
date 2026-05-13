# 🔍 JobScrappers

> A fully automated job alert bot that scrapes **15+ platforms**, filters non-Nigeria-friendly listings, and delivers formatted jobs straight to your **Telegram channel** — every 30 minutes, completely free.

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Job Sources](#-job-sources)
- [Filter System](#-filter-system)
- [Customising Your Preferences](#-customising-your-job-preferences)
- [Installation & Setup](#-installation--setup)
- [Running the Bot](#-running-the-bot)
- [Resetting the Bot](#-resetting-the-bot)
- [Telegram Message Format](#-telegram-message-format)
- [Troubleshooting](#-troubleshooting)
- [Security Notes](#-security-notes)
- [FAQ](#-frequently-asked-questions)

---

## ⚙️ How It Works

Every 30 minutes, GitHub Actions wakes the bot and runs through this pipeline:

```
1. WAKE UP      →  GitHub Actions triggers the script
2. SCRAPE       →  15+ scrapers collect fresh job listings
3. DEDUPLICATE  →  Jobs already sent are skipped
4. FILTER       →  Location & language filters applied
5. SEND         →  Jobs formatted & delivered to Telegram
6. LOG          →  Stats saved (monthly reports only)
7. SLEEP        →  Script finishes until next run
```

> **No server needed. No subscription. Runs entirely on GitHub's free infrastructure.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 **15+ Job Sources** | Nigerian boards, global remote, NGO, and Telegram groups |
| ⏱️ **Runs Every 30 Minutes** | Never miss a fresh opportunity |
| 🧠 **Smart Filtering** | Drops US-only, Europe-only, Asia, and Israel jobs automatically |
| 📬 **Telegram Integration** | Direct messages with clickable "Apply Now" buttons |
| 🔗 **Real Link Extraction** | Pulls actual job URLs from Telegram posts — not group links |
| 📊 **Monthly Reports Only** | One clean summary on the 1st — zero daily spam |
| 🚨 **Health Alerts** | Notifies you if any scraper fails 3 runs in a row |
| 🛠️ **Fully Customisable** | Edit `config.py` to match your roles and preferences |
| 💸 **100% Free** | GitHub Actions free tier + free job sources |

---

## 📁 Project Structure

```
JobScrappers/
│
├── README.md
├── requirements.txt
│
├── .github/
│   └── workflows/
│       └── run.yml                   ← Triggers every 30 minutes
│
└── job-bot/
    ├── main.py                       ← Entry point
    ├── config.py                     ← ✏️ Your preferences (edit this)
    ├── filter.py                     ← Filtering logic
    ├── sender.py                     ← Telegram formatter & sender
    ├── seen_jobs.json                ← Auto-generated (dedup store)
    ├── scraper_health.json           ← Auto-generated (health tracker)
    ├── run_stats.json                ← Auto-generated (run stats)
    ├── requirements.txt
    │
    └── scrapers/
        ├── jobberman.py              ← 🇳🇬 Nigerian job board
        ├── myjobmag.py               ← 🇳🇬 Nigerian job board
        ├── ngcareers.py              ← 🇳🇬 Nigerian job board
        ├── jobgurus.py               ← 🇳🇬 Nigerian job board
        ├── ngo_jobs.py               ← 🌍 UN / ReliefWeb jobs
        ├── africa_jobs.py            ← 🌍 African job boards
        ├── remoteok.py               ← 🌐 Global remote jobs
        ├── remotive.py               ← 🌐 Global remote jobs
        ├── themuse.py                ← 🌐 Global jobs
        ├── workingnomads.py          ← 🌐 Remote jobs
        ├── braintrust.py             ← 🌐 Freelance / remote
        ├── himalayas.py              ← 🌐 Remote jobs
        ├── wfh_io.py                 ← 🌐 Remote jobs
        ├── virtustant.py             ← 🌐 Global hiring
        └── telegram_channels.py      ← 📢 Nigerian Telegram groups
```

---

## 🌍 Job Sources

### 🇳🇬 Nigeria-Specific — Most Reliable (4 sources)

| Scraper | Source | Status |
|---|---|---|
| Jobberman | Nigerian job board | ✅ Active |
| MyJobMag | Nigerian job board | ✅ Active |
| NGCareers | Nigerian job board | ✅ Active |
| JobGurus | Nigerian job board | ✅ Active |

### 🌍 International / NGO / Africa (2 sources)

| Scraper | Source | Status |
|---|---|---|
| NGO / UN Jobs | ReliefWeb API | ✅ Active |
| Africa Jobs | African job boards | ✅ Active |

### 🌐 Global Remote (8 sources)

| Scraper | Source | Status |
|---|---|---|
| RemoteOK | RemoteOK API | ✅ Active |
| Remotive | Remotive API | ✅ Active |
| TheMuse | The Muse API | ✅ Active |
| WorkingNomads | JSON API | ✅ Active |
| Braintrust | JSON API | ✅ Active |
| Himalayas | Free API | ✅ Active |
| WFH.io | HTML scraper | ✅ Active |
| Virtustant | HTML scraper | ✅ Active |

### 📢 Telegram Channels (7 channels)

| Channel | Status |
|---|---|
| @jbtoday | ✅ Active |
| @jobnownigeria | ✅ Active |
| @careermattersng | ✅ Active |
| @jobnetworkng | ✅ Active |
| @WorkaNigeria | ✅ Active |
| @remotejobss | ✅ Active |
| @techjobsworld | ✅ Active |

---

## 🔽 Filter System

Every scraped job passes through this pipeline before it reaches your Telegram:

```
JOB FOUND
    │
    ▼
[1] Clean HTML & formatting
    │
    ▼
[2] Too old? (>14 days) ──────────── YES ──► ❌ REJECTED
    │ NO
    ▼
[3] Salary too low? (if set) ──────── YES ──► ❌ REJECTED
    │ NO
    ▼
[4] Duplicate? (85%+ match) ────────── YES ──► ❌ REJECTED
    │ NO
    ▼
[5] German job? ─────────────────────── YES ──► ❌ REJECTED 🇩🇪
    │ NO
    ▼
[6] Chinese job? ───────────────────── YES ──► ❌ REJECTED 🇨🇳
    │ NO
    ▼
[7] Location restricted? ────────────── YES ──► ❌ REJECTED 🌍
    │    (US / Canada / Europe / Asia / Israel)
    │ NO
    ▼
[8] Excluded title? (config.py) ──────── YES ──► ❌ REJECTED
    │ NO
    ▼
[9] Matches INCLUDE_KEYWORDS? ─────── NO ───► ❌ REJECTED
    │ YES
    ▼
  Assign quality score (⭐) + priority flag (🔴)
    │
    ▼
  ✅ SENT TO TELEGRAM
```

**What gets filtered out:**
- 🇩🇪 German-language jobs
- 🇨🇳 China-based or Chinese-character listings
- 🌍 US-only, UK-only, Canada-only, Europe-only, Asia, Latin America, Philippines, Brazil, Israel
- 📅 Listings older than 14 days
- 🚫 Titles you've excluded in `config.py`

**What gets through:**
- ✅ Nigerian jobs (Lagos, Abuja, all 36 states)
- ✅ Worldwide remote roles
- ✅ Africa-based jobs
- ✅ UN / NGO listings
- ✅ Jobs with no location restrictions

---

## 🛠️ Customising Your Job Preferences

Open `config.py` and adjust to your needs:

### Roles you want to see
```python
INCLUDE_KEYWORDS = [
    "virtual assistant", "customer support", "data entry",
    "remote", "work from home", "admin", "writer",
    "developer", "engineer", "project manager",
    # Add your own keywords here
]
```

### Priority roles — tagged 🔴 in Telegram
```python
PRIORITY_KEYWORDS = [
    "virtual assistant", "customer support", "data entry",
    "remote customer service", "help desk",
]
```

### Titles to block
```python
EXCLUDE_TITLES = [
    "cdl driver", "truck driver", "warehouse",
    "convent", "monastery", "pastor",
]
```

### Minimum salary (optional — set to `0` to disable)
```python
MIN_SALARY_NGN = 80000   # Skip jobs below ₦80,000/month
MIN_SALARY_USD = 300     # Skip jobs below $300/month
```

### Maximum job age
```python
MAX_JOB_AGE_DAYS = 14   # Only show jobs from the last 14 days
```

---

## 🚀 Installation & Setup

### What You Need
- A **GitHub account** — [github.com](https://github.com) (free)
- A **Telegram account** — [telegram.org](https://telegram.org)

---

### Step 1 — Create Your Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Save the **Bot Token** you receive

### Step 2 — Create Your Telegram Channel

1. Create a new Telegram Channel (private is fine)
2. Add your bot as **Administrator** with permission to post messages
3. Forward any message from the channel to `@JsonDumpBot`
4. Copy the `"id"` field — this is your **Channel ID** (starts with `-100`)

### Step 3 — Create a GitHub Repository

1. Go to GitHub → **+** → **New repository**
2. Name it `JobScrappers` (or whatever you prefer)
3. Set to **Private**
4. Click **Create repository**

### Step 4 — Upload Project Files

Upload all files maintaining this structure:

```
Root:               README.md, requirements.txt
job-bot/:           main.py, config.py, filter.py, sender.py, requirements.txt
job-bot/scrapers/:  all .py scraper files
.github/workflows/: run.yml
```

### Step 5 — Add GitHub Secrets

Go to **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your token from BotFather |
| `TELEGRAM_CHANNEL_ID` | Your channel ID (e.g. `-1003869498104`) |

### Step 6 — Enable GitHub Actions

1. Click the **Actions** tab in your repository
2. If prompted, click **Enable workflows**
3. The bot starts running automatically every 30 minutes ✅

---

## ▶️ Running the Bot

### Manual Test Run
Go to **Actions → JobScrappers → Run workflow → Run workflow**, then check your Telegram channel.

### Automatic Schedule
The bot runs every 30 minutes, 24/7, including weekends — no input needed from you.

### Stats & Reports
- 📊 **Monthly report** on the 1st of each month (jobs sent, filtered, top sources)
- ⚠️ **Health alert** if any scraper fails 3 consecutive runs
- 🔇 No daily or weekly summaries — just monthly

---

## 🔄 Resetting the Bot

To clear all history and treat every job as new:

1. Go to **Settings → Actions → Caches** → delete all `seen-jobs-*` caches
2. Delete `run_stats.json` and `scraper_health.json` from the `job-bot/` folder
3. Run the workflow manually

---

## 📨 Telegram Message Format

Each job arrives like this:

```
🔴 PRIORITY MATCH

💼 Virtual Assistant at Acme Global
🏢 Acme Global Ltd
📍 Remote (Worldwide)
💰 $500–800/month
✨ Quality: ⭐⭐⭐⭐

📋 We are looking for a detail-oriented Virtual Assistant to support
our executive team. Responsibilities include calendar management,
email handling, research, and data entry...

Source: RemoteOK

[ 🔗 Apply Now ]
```

Jobs are automatically grouped by category:

```
💻 Tech & Development
──────────────────────────
📞 Customer Support
──────────────────────────
🗂️ Virtual & Admin
──────────────────────────
🌍 NGO & UN
──────────────────────────
🌐 General / Remote
```

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| **No jobs appearing in Telegram** | Verify bot is channel admin, check secrets, run manually and inspect logs |
| **A scraper returns 0 jobs** | The site may have changed structure — health alert fires after 3 failures |
| **German / Chinese jobs getting through** | Update exclusion rules in `filter.py` |
| **Wrong jobs being filtered** | Adjust `INCLUDE_KEYWORDS` in `config.py` |
| **Duplicate jobs appearing** | Confirm the cache is persisting (**Settings → Actions → Caches**) |
| **Import errors on run** | Ensure all files are in the correct subfolder (`job-bot/`) |
| **Rate limit (429) errors** | Built-in retry logic handles these automatically |
| **Telegram group links instead of real links** | Fixed in v2.0 — real application URLs are now extracted |

---

## 🔐 Security Notes

- **Bot token and channel ID** are stored as GitHub Secrets — never exposed in code
- **No personal data stored** — only job IDs are saved in `seen_jobs.json`
- **To revoke bot access**: open `@BotFather` → `/mybots` → **Revoke token**
- **Making the repo public** exposes `config.py` keyword preferences, but never your credentials

---

## 🆕 Recent Updates — v2.0

- ✅ Project renamed to **JobScrappers**
- ✅ Scan interval reduced to **every 30 minutes** (was 1 hour)
- ✅ Simplified filters — removed haram/alcohol/adult content filters
- ✅ Real application URL extraction from Telegram posts
- ✅ German and Chinese job filtering added
- ✅ Clean message formatting — no HTML tags or escaped slashes
- ✅ 15 active scrapers — all free sources
- ✅ Monthly reports only — no daily spam
- ✅ Smart location filtering (US, Europe, Asia, Israel excluded)
- ✅ Telegram sources always preserved — Nigerian job groups never filtered

---

## ❓ Frequently Asked Questions

<details>
<summary><strong>Is this really free?</strong></summary>

Yes. All job sources are free to apply on. GitHub Actions' free tier handles the automation. No subscriptions, no hidden costs.
</details>

<details>
<summary><strong>How many jobs will I receive per day?</strong></summary>

| Source | Estimate |
|---|---|
| Nigerian job boards | 10–30 jobs/day |
| Remote global jobs (filtered) | 20–50 jobs/day |
| Telegram groups | 5–15 jobs/day |
| **Total** | **~50–150 jobs/day** |
</details>

<details>
<summary><strong>Can I customise what jobs I receive?</strong></summary>

Absolutely. Edit `INCLUDE_KEYWORDS` in `config.py` to match your target roles.
</details>

<details>
<summary><strong>Does my laptop need to stay on?</strong></summary>

No. The bot runs entirely on GitHub's cloud servers your laptop can be completely off.
</details>

<details>
<summary><strong>How do I stop the bot?</strong></summary>

Delete the repository or disable Actions under repository settings.
</details>

---

## 📄 License

MIT — Use freely, modify as needed.

---

## 💬 Support

Open a GitHub issue if something breaks. For quick fixes:

1. Check the **Actions** tab logs for error details
2. Confirm your Telegram bot has admin rights in the channel
3. Review your `config.py` keywords

---

<div align="center">

**Happy Job Hunting! 🎯**

</div>
