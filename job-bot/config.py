# =============================================================================
# config.py — Your personal job preferences
# Edit this file to control exactly what jobs you receive
# =============================================================================

# -----------------------------------------------------------------------------
# INCLUDE — Job titles/roles you WANT to see
# A job must match at least ONE keyword from this list to be sent to you
# Add as many as you like, all lowercase
# -----------------------------------------------------------------------------

INCLUDE_KEYWORDS = [
    # Virtual & Admin
    "virtual assistant",
    "executive assistant",
    "personal assistant",
    "administrative assistant",
    "admin assistant",
    "office assistant",
    "data entry",
    "data entry clerk",
    "data entry operator",

    # Customer Support
    "customer support",
    "customer service",
    "customer success",
    "customer care",
    "client support",
    "client success",
    "help desk",
    "technical support",
    "support agent",
    "support specialist",
    "live chat agent",
    "chat support",

    # Writing & Content
    "content writer",
    "copywriter",
    "copy editor",
    "proofreader",
    "technical writer",
    "blog writer",
    "article writer",
    "ghostwriter",
    "social media manager",
    "social media specialist",
    "content creator",
    "content strategist",

    # Tech / Development
    "software developer",
    "software engineer",
    "web developer",
    "frontend developer",
    "backend developer",
    "full stack developer",
    "fullstack developer",
    "mobile developer",
    "flutter developer",
    "react developer",
    "python developer",
    "javascript developer",
    "devops engineer",
    "qa engineer",
    "quality assurance",
    "ui/ux designer",
    "ux designer",
    "ui designer",
    "product designer",
    "graphic designer",

    # Data & Analytics
    "data analyst",
    "data scientist",
    "business analyst",
    "data engineer",
    "research analyst",
    "market research",

    # Finance & Accounting
    "accountant",
    "bookkeeper",
    "finance officer",
    "accounts officer",
    "financial analyst",
    "payroll officer",

    # Marketing & Sales
    "digital marketer",
    "digital marketing",
    "seo specialist",
    "email marketer",
    "growth marketer",
    "sales representative",
    "sales executive",
    "business development",
    "affiliate marketer",

    # Project & Operations
    "project manager",
    "project coordinator",
    "operations manager",
    "operations coordinator",
    "program manager",
    "scrum master",

    # HR & Recruitment
    "hr officer",
    "human resources",
    "recruiter",
    "talent acquisition",
    "people operations",

    # Teaching & Training
    "online tutor",
    "elearning",
    "instructional designer",
    "curriculum developer",
    "teacher",
    "trainer",

    # Transcription & Translation
    "transcriptionist",
    "transcription",
    "translator",
    "interpreter",
    "subtitler",

    # General Remote
    "remote",
    "work from home",
    "telecommute",
    "freelance",
    "contract",
]


# -----------------------------------------------------------------------------
# EXCLUDE TITLES — Specific job titles you do NOT want (even if they pass the
# halal filter). Useful for filtering out very senior or irrelevant roles.
# -----------------------------------------------------------------------------

EXCLUDE_TITLES = [
    # Roles that need physical presence in specific countries
    "cdl driver",
    "truck driver",
    "warehouse",
    "factory worker",

    # Overly senior (optional — remove if you want these)
    # "chief executive",
    # "chief financial",
    # "vice president",
]


# -----------------------------------------------------------------------------
# MINIMUM DESCRIPTION LENGTH
# Jobs with very short or empty descriptions are often spam — skip them
# Set to 0 to allow all jobs regardless of description length
# -----------------------------------------------------------------------------

MIN_DESCRIPTION_LENGTH = 0  # Set to e.g. 50 to require some description
