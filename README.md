# 🕌 Halal Jobs Bot
A fully automated job alert bot that scrapes **22 job platforms** across the web and social media, filters out haram industries, enforces English-only listings, checks Nigeria/remote eligibility, and delivers each matching job as a formatted message directly to your private **Telegram channel** — twice a day, every day, for free (More can be included).

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
- [GitHub Actions Schedule](#github-actions-schedule)
- [Adding New Sources](#adding-new-sources)
- [Telegram Message Format](#telegram-message-format)
- [Troubleshooting](#troubleshooting)

---

## How It Works

Every time the bot runs (twice daily via GitHub Actions), it follows these steps:

```
1. WAKE UP     — GitHub Actions triggers the script on schedule
2. SCRAPE      — 22 scrapers run in sequence, collecting job listings
3. DEDUPLICATE — Jobs already sent before are skipped (seen_jobs.json)
4. FILTER      — Each job passes through 5 filter layers
5. SEND        — Passing jobs are formatted and sent to Telegram one by one
6. SLEEP       — Script finishes, GitHub goes back to sleep
```

No server needed. No subscription. Runs entirely on GitHub's free infrastructure.

---

## Project Structure

```
halal-jobs-bot/
│
├── main.py                   ← Entry point. Runs all scrapers and coordinates everything
├── config.py                 ← Your personal preferences (roles you want, roles to block)
├── filter.py                 ← All filtering logic (halal, English, Nigeria, preferences)
├── sender.py                 ← Formats and sends jobs to Telegram
├── seen_jobs.json            ← Auto-generated. Tracks already-sent jobs to avoid repeats
├── requirements.txt          ← Python dependencies
│
├── scrapers/                 ← One file per job source
│   ├── __init__.py
│   ├── remoteok.py
│   ├── remotive.py
│   ├── arbeitnow.py
│   ├── themuse.py
│   ├── weworkremotely.py
│   ├── workingnomads.py
│   ├── braintrust.py
│   ├── dailyremote.py
│   ├── dynamitejobs.py
│   ├── startupjobs.py
│   ├── virtustant.py
│   ├── oneforma.py
│   ├── indeed_ng.py
│   ├── jobberman.py
│   ├── myjobmag.py
│   ├── ngcareers.py
│   ├── grabjobs.py
│   ├── jooble.py
│   ├── doballi.py
│   ├── jobgurus.py
│   ├── telegram_channels.py
│   └── twitter_jobs.py
│
└── .github/
    └── workflows/
        └── run.yml           ← GitHub Actions schedule (8am & 6pm WAT daily)
```

---

## File-by-File Breakdown

### `main.py` — The Engine
The entry point and coordinator of the entire bot. When run, it:
- Loads `seen_jobs.json` to know which jobs have already been sent
- Calls every scraper in sequence, collecting all job listings
- Passes each job through the filter in `filter.py`
- Sends passing jobs to Telegram via `sender.py`
- Saves the updated seen jobs list back to `seen_jobs.json`
- Prints a summary log at the end (sent / filtered / already seen)

---

### `config.py` — Your Control Panel
**This is the main file you will edit to customise the bot.**

It contains three sections:

**`INCLUDE_KEYWORDS`** — A list of job titles and role keywords. A job must match at least one of these to reach your Telegram channel. Currently includes roles across Virtual Assistant, Customer Support, Writing, Tech, Data, Finance, Marketing, HR, Teaching, and Transcription.

**`EXCLUDE_TITLES`** — A list of job titles to block even if they pass the halal filter. Use this for roles that are simply not relevant to you (e.g. truck driver, warehouse worker).

**`MIN_DESCRIPTION_LENGTH`** — Set a minimum character count for job descriptions. Jobs with descriptions shorter than this are skipped. Default is `0` (all jobs allowed). Set to `50` or `100` to filter out low-quality listings with no detail.

---

### `filter.py` — The 5-Layer Filter
Every job passes through five checks in order. If it fails any one check, it is rejected.

**Layer 1 — Subscription Source Check**
Blocks jobs from platforms that require a paid subscription to apply (e.g. The Ladders, job-hunt.org).

**Layer 2 — Haram Keyword Filter**
Scans the job title, company name, description, and tags for any haram-related terms. Categories covered: gambling, alcohol, nightlife, non-Islamic religious institutions, adult content, pork, riba/predatory lending, tobacco, and drugs.

**Layer 3 — English-Only Filter**
Rejects jobs that require fluency in a foreign language (German, French, Spanish, Portuguese, Mandarin, Japanese, Korean, Dutch, Italian, etc.). The job must be workable in English only.

**Layer 4 — Nigeria-Friendly Filter**
Blocks jobs that explicitly restrict applicants by citizenship or location (e.g. "US only", "EU only", "must have right to work in UK", "security clearance required"). Remote jobs open to worldwide applicants are always allowed through.

**Layer 5 — Job Preference Filter**
Cross-checks the job against your personal `INCLUDE_KEYWORDS` and `EXCLUDE_TITLES` from `config.py`. Blocks anything outside your chosen roles.

Also handles HTML cleaning — strips all HTML tags and entities from job descriptions before displaying them (fixes the `<p><span style=...>` display issue).

---

### `sender.py` — Telegram Delivery
Handles formatting and sending each job to your Telegram channel.

**`format_job()`** — Builds a clean, readable Telegram message with emoji labels for title, company, location, salary, experience level, tags, description snippet, apply link, and source platform.

**`escape()`** — Sanitises special characters so Telegram's Markdown parser doesn't break.

**`send_job()`** — Posts the formatted message to your channel via the Telegram Bot API. Includes a 1-second delay between messages to respect Telegram's rate limits.

Credentials (bot token and channel ID) are read from environment variables, never hardcoded.

---

### `seen_jobs.json` — Duplicate Prevention
Auto-created on first run. Stores the unique ID of every job the bot has ever sent or evaluated. On each run, any job whose ID is already in this file is skipped entirely. This prevents the same job from appearing in your channel multiple times across different runs. Managed automatically — you never need to edit this file manually. Stored in GitHub's cache across runs.

---

### `requirements.txt` — Dependencies
Lists the Python libraries the bot needs:
- `requests` — for making HTTP calls to job board APIs and websites
- `beautifulsoup4` — for parsing and scraping HTML pages
- `lxml` — HTML parser used by BeautifulSoup for faster, more reliable parsing

---

### `.github/workflows/run.yml` — The Scheduler
The GitHub Actions workflow file that automates the bot. It:
- Triggers at **8:00 AM WAT** and **6:00 PM WAT** every day
- Can also be triggered manually from the GitHub Actions tab at any time
- Sets up Python, installs dependencies, restores the seen_jobs cache, runs the bot, and saves the updated cache
- Injects the Telegram secrets securely from GitHub's secret store

---

## Job Sources

### Global Remote Platforms (API-based, most reliable)

| Scraper File | Source | Method |
|---|---|---|
| `remoteok.py` | RemoteOK | Free public JSON API |
| `remotive.py` | Remotive | Free public JSON API |
| `arbeitnow.py` | Arbeitnow | Free public JSON API |
| `themuse.py` | The Muse | Free public JSON API |
| `weworkremotely.py` | WeWorkRemotely | RSS feed (5 categories) |
| `workingnomads.py` | WorkingNomads | JSON API (10 categories) |
| `braintrust.py` | Braintrust | JSON API |
| `dailyremote.py` | DailyRemote | HTML scraper |
| `dynamitejobs.py` | DynamiteJobs | HTML scraper |
| `startupjobs.py` | StartupJobs | HTML scraper |
| `virtustant.py` | Virtustant | HTML scraper (global hiring) |
| `oneforma.py` | OneForma | HTML scraper (global tasks) |

### Nigeria-Specific Platforms

| Scraper File | Source | Method |
|---|---|---|
| `indeed_ng.py` | Indeed Nigeria | HTML scraper |
| `jobberman.py` | Jobberman | HTML scraper |
| `myjobmag.py` | MyJobMag Nigeria | HTML scraper |
| `ngcareers.py` | NGCareers | HTML scraper |
| `grabjobs.py` | GrabJobs Nigeria | HTML scraper |
| `jooble.py` | Jooble Nigeria | JSON API |
| `doballi.py` | Doballi (Africa) | HTML scraper |
| `jobgurus.py` | JobGurus Nigeria | HTML scraper |

### Social Media

| Scraper File | Source | Method |
|---|---|---|
| `telegram_channels.py` | 8 Nigerian Telegram channels | t.me public web preview |
| `twitter_jobs.py` | 10+ X/Twitter job accounts | Nitter public mirror |

**Telegram channels monitored:**
- `@jbtoday` — Jobstoday Nigeria (Nigerian + international remote)
- `@jobnownigeria` — Jobnow Nigeria (daily verified vacancies)
- `@careermattersng` — Careermatters NG (active recruitment)
- `@jobnetworkng` — Latest Jobs in Nigeria
- `@JobsinNigeriadaily` — Jobs in Nigeria Daily
- `@jobsnigeria001rekrutconsulting` — Job Vacancies Nigeria
- `@WorkaNigeria` — Worka Nigeria (Web2 & Web3 jobs)
- `@remotejobss` — Remote Jobs (English & Worldwide)

**X/Twitter accounts monitored:**
- `@BenoHr80463`, `@JobFound5`, `@jobsregion`, `@TrybeCityJobs`, `@Halosznn_`
- `@NgJobAlert`, `@RemoteJobsNG`, `@JobsInNigeria`, `@AfricaJobs`, `@RemoteJobsAfrica`

> **Note:** WhatsApp channels cannot be scraped. WhatsApp encrypts all content and has no public web preview or API. The Telegram channels above cover equivalent Nigerian job content.

---

## Filter System

Every job passes through all five layers below. Failing any one layer rejects the job.

```
JOB FOUND
    │
    ▼
[1] Subscription source? ──YES──► REJECTED
    │ NO
    ▼
[2] Contains haram keyword? ──YES──► REJECTED
    │ NO
    ▼
[3] Requires foreign language? ──YES──► REJECTED
    │ NO
    ▼
[4] Restricted to non-Nigeria region? ──YES──► REJECTED
    │ NO
    ▼
[5] Matches your INCLUDE_KEYWORDS? ──NO──► REJECTED
    │ YES
    ▼
  SENT TO TELEGRAM ✅
```

---

## Customising Your Job Preferences

Open `config.py` in your GitHub repo and edit freely:

**To add a new role you want:**
```python
INCLUDE_KEYWORDS = [
    ...
    "grant writer",
    "research assistant",
    "community manager",
]
```

**To block a role you don't want:**
```python
EXCLUDE_TITLES = [
    ...
    "chief executive",
    "vice president",
]
```

**To require a minimum description (filter out low-quality listings):**
```python
MIN_DESCRIPTION_LENGTH = 80
```

No other files need to be changed. `filter.py` reads from `config.py` automatically.

---

## Installation & Setup

### What You Need
- A **GitHub account** (free) — github.com
- A **Telegram account** — telegram.org

### Step 1 — Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Give it a name (e.g. `Halal Jobs Nigeria`) and a username ending in `bot`
4. BotFather gives you a **Bot Token** — save it

### Step 2 — Create Your Telegram Channel
1. Create a new Telegram Channel (can be private)
2. Add your bot as an **Administrator** with permission to post messages
3. Forward any message from the channel to `@JsonDumpBot`
4. Note the `"id"` field in the JSON response — this is your **Channel ID** (starts with `-100`)

### Step 3 — Create the GitHub Repository
1. Go to github.com → click **+** → **New repository**
2. Name it `halal-jobs-bot`, set to **Private**
3. Click **Create repository**

### Step 4 — Upload the Project Files
1. In your repo click **Add file** → **Upload files**
2. Upload all project files, maintaining the folder structure:
   - All `.py` files in `job-bot/`
   - All scraper files in `job-bot/scrapers/`
3. For the workflow file, click **Add file** → **Create new file** and name it:
   ```
   .github/workflows/run.yml
   ```
   Then paste the workflow content

### Step 5 — Add Your Secrets
1. In your repo go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add both:

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
2. Click **Halal Jobs Bot** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch the live log — then check your Telegram channel

### Automatic Schedule
The bot runs automatically at:
- **8:00 AM WAT** (West Africa Time, UTC+1)
- **6:00 PM WAT**

Every day, 7 days a week, including weekends.

### Clearing Seen Jobs (Reset)
If you want all jobs to be sent fresh (e.g. after a long break):
1. Go to **Settings** → **Actions** → **Caches**
2. Delete any cache named `seen-jobs-...`
3. Run the workflow manually

---

## Adding New Sources

To add a new job board:

1. Create a new file in `scrapers/` (e.g. `scrapers/mynewsource.py`)
2. Write a function that returns a list of job dictionaries in this format:
```python
{
    "id":          "unique_id_string",
    "title":       "Job Title",
    "company":     "Company Name",
    "location":    "Remote / Nigeria",
    "salary":      "₦200,000/month",   # or "" if unknown
    "description": "Job description text here",
    "tags":        "python, remote, full-time",
    "url":         "https://apply-link.com",
    "source":      "MyNewSource",
}
```
3. Import and register it in `main.py`:
```python
from scrapers.mynewsource import scrape_mynewsource
# then add to the scrapers list:
("MyNewSource", scrape_mynewsource),
```

To add a new Telegram channel, just add its username to the `TELEGRAM_JOB_CHANNELS` list in `scrapers/telegram_channels.py`.

---

## Telegram Message Format

Each job is sent as a separate message formatted like this:

```
💼 Virtual Assistant (Remote)
🏢 Acme Global Ltd
📍 Remote (Worldwide)
💰 $500–$800/month
📊 Entry Level
🏷️ admin, remote, part-time

📋 We are looking for a detail-oriented Virtual Assistant to support our
executive team. Responsibilities include calendar management, email
handling, research, and data entry...

🔗 Apply Here

Source: RemoteOK
```

---

## Troubleshooting

**Jobs are not appearing in Telegram**
- Confirm your bot is an Administrator of the channel with posting rights
- Check that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHANNEL_ID` are correctly saved in GitHub Secrets
- Run the workflow manually and expand the **Run python main.py** step to read the logs

**A scraper shows 0 jobs every run**
- The website may have changed its HTML structure (common with scrapers)
- The site may be temporarily blocking the request
- API-based scrapers (RemoteOK, Remotive, Arbeitnow, Jooble) are the most stable

**Jobs are being sent that don't match my roles**
- Open `config.py` and tighten your `INCLUDE_KEYWORDS` list
- Add unwanted role names to `EXCLUDE_TITLES`

**The same job keeps appearing**
- The seen_jobs cache may not be persisting correctly between runs
- Go to **Settings** → **Actions** → **Caches** and check that a `seen-jobs-*` cache exists after each run

**HTML tags appearing in descriptions** (e.g. `<p><span style=...>`)
- This is handled automatically by `filter.py`'s `strip_html()` function
- If it still appears from a specific source, check that the scraper is not bypassing the filter

**"Chat not found" error in Telegram**
- Your bot is not added as admin to the channel — go to channel settings and add it
- Double-check the channel ID starts with `-100`

---

## Security Notes

- Your bot token and channel ID are stored as **GitHub Secrets** — never visible in code or logs
- The repository is set to **Private** — your config and job preferences are not public
- No personal data is stored anywhere — only job IDs in `seen_jobs.json`
- To revoke bot access at any time, go to `@BotFather` → `/mybots` → **Revoke token**
