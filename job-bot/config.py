# =============================================================================
# config.py — Your personal job preferences
# This is the ONLY file you need to edit to customise the bot
# =============================================================================


# -----------------------------------------------------------------------------
# INCLUDE KEYWORDS — Roles you WANT to receive
# A job must match at least ONE of these to reach your Telegram channel
# -----------------------------------------------------------------------------
INCLUDE_KEYWORDS = [
    # Virtual & Admin
    "virtual assistant", "executive assistant", "personal assistant",
    "administrative assistant", "admin assistant", "office assistant",
    "data entry", "data entry clerk", "data entry operator",

    # Customer Support
    "customer support", "customer service", "customer success",
    "customer care", "client support", "client success",
    "help desk", "technical support", "support agent",
    "support specialist", "live chat agent", "chat support",

    # Writing & Content
    "content writer", "copywriter", "copy editor", "proofreader",
    "technical writer", "blog writer", "article writer", "ghostwriter",
    "social media manager", "social media specialist",
    "content creator", "content strategist",

    # Tech / Development
    "software developer", "software engineer", "web developer",
    "frontend developer", "backend developer", "full stack developer",
    "fullstack developer", "mobile developer", "flutter developer",
    "react developer", "python developer", "javascript developer",
    "devops engineer", "qa engineer", "quality assurance",
    "ui/ux designer", "ux designer", "ui designer",
    "product designer", "graphic designer",

    # Data & Analytics
    "data analyst", "data scientist", "business analyst",
    "data engineer", "research analyst", "market research",

    # Finance & Accounting
    "accountant", "bookkeeper", "finance officer",
    "accounts officer", "financial analyst", "payroll officer",

    # Marketing & Sales
    "digital marketer", "digital marketing", "seo specialist",
    "email marketer", "growth marketer", "sales representative",
    "sales executive", "business development", "affiliate marketer",

    # Project & Operations
    "project manager", "project coordinator", "operations manager",
    "operations coordinator", "program manager", "scrum master",

    # HR & Recruitment
    "hr officer", "human resources", "recruiter",
    "talent acquisition", "people operations",

    # Teaching & Training
    "online tutor", "elearning", "instructional designer",
    "curriculum developer", "teacher", "trainer",

    # Transcription & Translation
    "transcriptionist", "transcription", "translator",
    "interpreter", "subtitler",

    # General Remote
    "remote", "work from home", "telecommute", "freelance", "contract",
]


# -----------------------------------------------------------------------------
# PRIORITY KEYWORDS — Roles you urgently want — tagged 🔴 in Telegram
# These still must pass all filters, but get a priority flag on the message
# -----------------------------------------------------------------------------
PRIORITY_KEYWORDS = [
    "virtual assistant",
    "customer support",
    "customer service",
    "remote customer",
    "data entry",
    "content writer",
    "social media manager",
]


# -----------------------------------------------------------------------------
# EXCLUDE TITLES — Roles to always block regardless of other filters
# -----------------------------------------------------------------------------
EXCLUDE_TITLES = [
    "cdl driver", "truck driver", "warehouse", "factory worker",
]


# -----------------------------------------------------------------------------
# MINIMUM SALARY FILTER
# Set a value to skip jobs with salaries explicitly below this threshold.
# Uses simple pattern matching — only works when salary is clearly stated.
# Examples: 300 (USD/month), 100000 (NGN/month)
# Set to 0 to disable.
# -----------------------------------------------------------------------------
MIN_SALARY_USD = 0       # e.g. 300 — skip jobs paying less than $300/month
MIN_SALARY_NGN = 0       # e.g. 100000 — skip jobs paying less than ₦100k/month


# -----------------------------------------------------------------------------
# JOB AGE FILTER
# Skip jobs older than this many days. Set to 0 to disable.
# -----------------------------------------------------------------------------
MAX_JOB_AGE_DAYS = 14


# -----------------------------------------------------------------------------
# MINIMUM DESCRIPTION LENGTH
# Set to 0 to allow all. Set to e.g. 50 to skip jobs with no description.
# -----------------------------------------------------------------------------
MIN_DESCRIPTION_LENGTH = 0


# -----------------------------------------------------------------------------
# STATS & HEALTH — Controls for reporting features
# -----------------------------------------------------------------------------
SEND_RUN_STATS = True          # Send a stats summary message after each run
HEALTH_CHECK_THRESHOLD = 3     # Alert if a scraper fails this many runs in a row
SEND_WEEKLY_REPORT = True      # Send a scraper health report every Sunday
