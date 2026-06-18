# 🔍 JobScrappers

A fully automated job alert bot that scrapes **15+ job platforms** across the web and delivers each job as a clean, simple message directly to your private **Telegram channel** every 30 minutes, completely free.

**For job seekers:** Join our Telegram channel to receive daily job alerts.
**For developers:** Follow this guide to build and run your own instance.

---

## 📌 Quick Links

- [For Job Seekers](#for-job-seekers-join-our-channel)
- [For Developers - Build Your Own](#for-developers-build-your-own-bot)
- [How It Works](#how-it-works)
- [Installation & Setup](#installation--setup)
- [Customizing the Bot](#customizing-the-bot)
- [Troubleshooting](#troubleshooting)
- [Legal & Documentation](#legal--documentation)

---

## For Job Seekers: Join Our Channel

**Simply join our Telegram channel to start receiving daily job alerts:**

👉 **[Click here to join JobScrappers Telegram Channel](https://t.me/+bJOD6zoeb4BiZjJk)**

No setup required. Just join and wait for jobs to appear automatically.

---

## For Developers: Build Your Own Bot

Want to run your own instance? Follow this complete guide.

### What You'll Need

| Item | Cost | Purpose |
|------|------|---------|
| GitHub Account | Free | Host the code and run the bot |
| Telegram Account | Free | Receive job alerts |
| Telegram Bot Token | Free | Bot identity |
| Telegram Channel | Free | Where jobs are posted |

**Total: $0**

### Project Structure Overview

```
JobScarppers/
│
├── .github/workflows/run.yml    ← Schedule (runs every 30 min)
├── job-bot/
│   ├── main.py                  ← Main bot logic
│   ├── config.py                ← Your preferences (edit this)
│   ├── filter.py                ← Job filtering rules
│   ├── sender.py                ← Telegram message formatting
│   └── scrapers/                ← Individual job sources
│       ├── jobberman.py         ← Nigerian job board
│       ├── myjobmag.py          ← Nigerian job board
│       ├── hireeast.py          ← East African job board
│       ├── revicemycv.py        ← Jobs in Nigeria & International
│       ├── telegram_channels.py ← Telegram job groups
│       └── ... (12+ more)
│
├── LICENSE                      ← MIT License
├── DISCLAIMER.md                ← Legal disclaimer
├── CONTRIBUTING.md              ← Contribution guidelines
├── SECURITY.md                  ← Security policy
├── CODE_OF_CONDUCT.md           ← Community guidelines
└── README.md                    ← This file
```

---

## How It Works

Every time the bot runs (every 30 minutes via GitHub Actions), it follows these steps:

```
1. WAKE UP      — GitHub Actions triggers the script (every 30 minutes)
2. SCRAPE       — 15+ scrapers run, collecting job listings
3. DEDUPLICATE  — Jobs already sent are skipped
4. FILTER       — Location & language filters applied
5. SEND         — Jobs sent to Telegram as clean messages with apply button
6. LOG          — Stats saved (monthly reports only)
7. SLEEP        — Script finishes until next run
```

**No server needed. No subscription. Runs on GitHub's free infrastructure.**

---

## Features

- ✅ **15+ Active Job Sources** — Nigerian job boards, global remote, NGO, Telegram groups
- ✅ **Runs Every 30 Minutes** — Never miss a job opportunity
- ✅ **Smart Filtering** — Filters out US-only, Europe-only, Asia, Israel jobs
- ✅ **Clean Telegram Messages** — Just job title + Apply Now button (no clutter)
- ✅ **Real Application Links** — Direct links to apply, not group links
- ✅ **Monthly Reports Only** — No spam, just one summary on the 1st of each month
- ✅ **Automatic Health Alerts** — Notifies if any scraper fails
- ✅ **Completely Free** — All job sources are free to apply, runs on GitHub free tier

---

## Job Sources (17 Active)

### Nigeria-Specific (5 sources)
| Scraper | Status |
|---------|--------|
| Jobberman | ✅ Active |
| MyJobMag | ✅ Active |
| NGCareers | ✅ Active |
| JobGurus | ✅ Active |
| ReviceMyCV | ✅ Active |

### International / NGO / Africa (3 sources)
| Scraper | Status |
|---------|--------|
| NGO / UN Jobs | ✅ Active |
| Africa Jobs | ✅ Active |
| HireEast| ✅ Active |

### Global Remote (8 sources)
| Scraper | Status |
|---------|--------|
| RemoteOK | ✅ Active |
| Remotive | ✅ Active |
| TheMuse | ✅ Active |
| Himalayas | ✅ Active |
| WFH.io | ✅ Active |
| Virtustant | ✅ Active |
| WorkingNomads | ✅ Active |
| Braintrust | ✅ Active |

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

## What Gets Filtered

The bot automatically filters out jobs that Nigerians cannot apply to:

### What Gets Through (All Free to Apply):
- ✅ Nigerian-based jobs (Lagos, Abuja, all 36 states)
- ✅ Remote jobs (worldwide)
- ✅ Africa-based jobs
- ✅ UN/NGO jobs
- ✅ All Telegram channel jobs (Nigeria-focused)

---

## Installation & Setup

### Step 1 — Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Name your bot (e.g., `MyJobBot`)
4. Choose a username ending in `bot` (e.g., `myjobbotalert_bot`)
5. **Save the Bot Token** — you'll need it later

### Step 2 — Create Your Telegram Channel
1. Open Telegram → Menu → **New Channel**
2. Name it (e.g., `My Job Alerts`)
3. Set it to **Private** (recommended)
4. Add your bot as **Administrator**:
   - Go to channel → Channel Info → Administrators → Add Admin
   - Search for your bot's username
   - Give permission: **Post Messages**

5. **Get your Channel ID:**
   - Forward any message from your channel to `@JsonDumpBot`
   - Look for `"id"` field in the response
   - It will look like `-1001234567890`
   - **Save this ID**

### Step 3 — Fork or Create Repository

**Option A: Fork the original repository (easier)**
1. Go to `https://github.com/[original-repo]/JobScarppers`
2. Click **Fork** (top right)
3. Select your GitHub account
4. Wait for fork to complete

**Option B: Create new repository**
1. Go to github.com → **+** → **New repository**
2. Name it `JobScarppers` or whichever
3. Set to **Private** (recommended)
4. Upload all project files

### Step 4 — Add Your Secrets

In your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these two secrets:

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | The token from Step 1 |
| `TELEGRAM_CHANNEL_ID` | The ID from Step 2 (e.g., `-1001234567890`) |

### Step 5 — Enable GitHub Actions

1. Click the **Actions** tab
2. If prompted, click **Enable workflows**
3. You should see a workflow named "JobScrappers"

### Step 6 — Test Your Bot

1. Go to **Actions** tab
2. Click **JobScrappers** on the left
3. Click **Run workflow** → **Run workflow**
4. Watch the live log
5. Check your Telegram channel for jobs

**Success! Your bot is now running.** It will automatically run every 30 minutes.

---

## Customizing the Bot

### Change How Often the Bot Runs

Edit `.github/workflows/run.yml`:

```yaml
on:
  schedule:
    - cron: "*/30 * * * *"   # Every 30 minutes
    # - cron: "0 * * * *"    # Every hour
    # - cron: "*/15 * * * *" # Every 15 minutes
```

### Add Your Own Keywords (Optional)

Edit `job-bot/config.py`:

```python
PRIORITY_KEYWORDS = [
    "customer support",     # Gets 🔴 tag
    "virtual assistant",    # Gets 🔴 tag
    "data entry",          # Gets 🔴 tag
]
```

### Add a New Job Source

1. Create a new file in `job-bot/scrapers/`
2. Use this template:

```python
def scrape_yoursource():
    jobs = []
    # Your scraping logic here
    job = {
        'title': "Job Title",
        'company': "Company Name",
        'location': "Remote",
        'description': "Job description",
        'url': "https://apply-link.com",
        'source': "YourSource",
    }
    jobs.append(job)
    return jobs
```

3. Import and add to `main.py`:

```python
from scrapers.yoursource import scrape_yoursource

scrapers = [
    ...
    ("YourSource", scrape_yoursource),
]
```

### Add a Telegram Channel

Edit `job-bot/scrapers/telegram_channels.py`:

```python
TELEGRAM_JOB_CHANNELS = [
    "existing_channel",
    "new_channel",  # Add your channel here
]
```

---

## Telegram Message Format

Each job appears as a clean message with just the title and an Apply Now button:

```
💼 Content Marketer Job at Right Click Technologies LTD

[🔗 Apply Now]
```

That's it! No clutter, no descriptions, no sources. Just the job title and a button to apply.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **No jobs in Telegram** | Check bot is channel admin, verify secrets, run manually and check logs |
| **Scraper shows 0 jobs** | Site may have changed — health alert after 3 failures |
| **Wrong jobs being sent** | Location filters in `filter.py` control what gets through |
| **Duplicate jobs** | Check cache is persisting (Settings → Actions → Caches) |
| **Import errors** | Ensure all files are in correct folders (`job-bot/` subfolder) |
| **Rate limiting errors** | Built-in retry handles 429 errors automatically |

---

## Legal & Documentation

This project includes the following legal and documentation files:

- [LICENSE](LICENSE) — MIT License
- [DISCLAIMER](DISCLAIMER.md) — Legal Disclaimer
- [CONTRIBUTING](CONTRIBUTING.md) — Contribution Guidelines
- [SECURITY](SECURITY.md) — Security Policy
- [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md) — Code of Conduct

## Important Legal Notice

This bot scrapes **publicly available** job listings from various websites. It does **not**:
- Bypass any paywalls or authentication
- Store or redistribute data for commercial purposes
- Harm or overload any servers (rate limiting is built in)

**If you are a website owner** and want your source removed, contact us and it will be done within **48 hours**.

---

## Frequently Asked Questions

### Is this really free?
**Yes.** All job sources are free to apply. GitHub Actions free tier handles the automation.

### How many jobs will I get?
- Nigerian job boards: 10-30 jobs/day
- Remote global jobs: 20-50 jobs/day
- Telegram groups: 5-15 jobs/day
- **Total: 50-150 jobs/day**

### What if my laptop is off?
The bot runs on GitHub's cloud servers. Your laptop can be completely off.

### How do I stop the bot?
Delete the GitHub repository or disable Actions in repository settings.

### Can I add more job sources?
Yes! Follow the "Add a New Job Source" guide above.

### Can I change what jobs are sent?
Edit `config.py` to add priority keywords. For deeper changes, modify `filter.py`.

---

## Recent Updates (v3.0)

- ✅ **Added HireEast** — East African job board
- ✅ **Added ReviceMyCV** — Nigeria & International jobs
- ✅ **Clean Telegram messages** — Just title + Apply Now button
- ✅ **Updated documentation** — Full legal and contributing guides
- ✅ **New license** — MIT License
- ✅ **Security & disclaimers** — Added DISCLAIMER.md, SECURITY.md, CODE_OF_CONDUCT.md

---

## License

[MIT License](LICENSE) — Use freely, modify as needed.

---

## Support

- **For job seekers:** Join the Telegram channel
- **For developers:** Open an issue on GitHub
- **Quick fixes:** Check Actions logs, verify secrets, test manually

---
