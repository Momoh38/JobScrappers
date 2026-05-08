# =============================================================================
# config.py — Your personal job preferences
# Edit this file to control exactly what jobs you receive
# =============================================================================

# -----------------------------------------------------------------------------
# INCLUDE — Job titles/roles you WANT to see
# A job must match at least ONE keyword from this list to be sent to you
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
# PRIORITY KEYWORDS — Jobs matching these get a 🔴 PRIORITY tag in Telegram
# Use for roles you are actively hunting RIGHT NOW
# -----------------------------------------------------------------------------

PRIORITY_KEYWORDS = [
    "virtual assistant",
    "customer support",
    "remote customer service",
    "data entry",
    "content writer",
    "social media manager",
]

# -----------------------------------------------------------------------------
# EXCLUDE TITLES — Block specific titles even if they pass the halal filter
# -----------------------------------------------------------------------------

EXCLUDE_TITLES = [
    "cdl driver", "truck driver", "warehouse", "factory worker",
]

# -----------------------------------------------------------------------------
# MINIMUM SALARY FILTER
# Jobs that explicitly show a salary BELOW these thresholds are skipped
# Set to 0 to disable. Amounts are monthly.
# -----------------------------------------------------------------------------

MIN_SALARY_NGN = 0       # e.g. 80000 to skip jobs below ₦80,000/month
MIN_SALARY_USD = 0       # e.g. 300 to skip jobs below $300/month

# -----------------------------------------------------------------------------
# JOB AGE FILTER
# Skip jobs older than this many days (0 = disabled)
# -----------------------------------------------------------------------------

MAX_JOB_AGE_DAYS = 14

# -----------------------------------------------------------------------------
# MINIMUM DESCRIPTION LENGTH
# Set to 0 to allow all jobs regardless of description length
# -----------------------------------------------------------------------------

MIN_DESCRIPTION_LENGTH = 0
