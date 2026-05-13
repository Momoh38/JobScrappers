# =============================================================================
# config.py — Your personal job preferences
# =============================================================================

# -----------------------------------------------------------------------------
# INCLUDE — Job titles/roles you WANT to see
# A job must match at least ONE keyword from this list to be sent to you
# -----------------------------------------------------------------------------

INCLUDE_KEYWORDS = [
    # Customer Support & Service (Group 1)
    "Customer Service", "Virtual Assistance", "Customer Support", "Email Support",
    "Customer Experience", "Call Center Management", "Phone Support",
    "Customer Experience Management Software", "Leadership Training", "Jira",
    "Customer Satisfaction", "Multitasking", "Answered Ticket", "Interpersonal Skills",
    "Ticketing System", "Online Chat Support", "KPI Metric Development",
    "Customer Service Training", "Retail & Consumer Goods", "English",
    "US English Dialect", "Product Knowledge", "Email Communication",
    "Email Management Software", "CRM System", "Helpdesk Platform",
    "Administrative Support", "CRM Software", "Data Entry", "Troubleshooting",
    "Communication Skills", "Quality Assurance", "Analytics", "Software Debugging",
    "Tools", "Zendesk", "Slack", "Chargebee", "Google Suite", "Zoom", "Sendgrid",
    "Amplitude", "Zoom Video Conferencing", "Communications", "Sales",
    "Order Tracking", "Scheduling", "Calendar Management", "Microsoft Excel",
    "Microsoft Office", "Google Workspace", "Canva", "Monday.com", "Intercom",
    "prop firm", "Forex Trading", "Communication Etiquette", "File Management",
    "Social Media Management",
    
    # Virtual Assistance & Admin (Group 2)
    "Virtual Assistant", "Administrative Support", "Calendar Management",
    "Scheduling", "File Management", "Travel Arrangements", "Meeting Coordination",
    "Document Preparation", "Time Management", "Task Prioritization",
    "Project Coordination", "Client Communication", "Project Management Tools",
    "Trello", "Asana", "Expense Reporting", "Invoice Processing",
    "Social Media Management", "Content Scheduling", "Newsletter Management",
    "Mailchimp", "Research", "Lead Generation", "Data Management",
    "Spreadsheet Management", "Google Sheets", "Appointment Setting",
    "Reminder Follow-ups", "Confidentiality", "Attention to Detail",
    "Problem Solving", "Organization", "Remote Support", "Executive Assistance",
    "Personal Assistant",
    
    # Nigerian States (Group 3)
    "Abia", "Adamawa", "Akwa Ibam", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe",
    "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara",
    "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau",
    "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "FCT", "Abuja",
    
    # Tech & Development
    "developer", "engineer", "devops", "qa", "quality assurance",
    "frontend", "backend", "fullstack", "full stack", "mobile", "flutter",
    "react", "python", "javascript", "software", "web dev", "ui/ux",
    "data scientist", "data analyst",
    
    # Writing & Content
    "writer", "copywriter", "editor", "proofreader", "content",
    "ghostwriter", "blogger", "journalist", "transcri",
    
    # Finance & Accounting
    "accountant", "bookkeeper", "finance", "payroll", "accounts",
    
    # Marketing & Sales
    "marketing", "seo", "sales", "growth", "affiliate",
    "email market", "business development",
    
    # Project & Operations
    "project manager", "operations", "program manager", "scrum",
    "coordinator",
    
    # HR & Recruitment
    "hr", "human resources", "recruiter", "talent", "people ops",
    
    # Teaching & Training
    "tutor", "teacher", "trainer", "elearning", "curriculum",
    
    # General Remote
    "remote", "work from home", "telecommute", "freelance", "contract",
    
    # Generic terms to catch more jobs
    "support", "assistant", "admin", "coordinator", 
    "specialist", "representative", "analyst", "associate",
    "officer", "executive", "manager", "supervisor",
]

# -----------------------------------------------------------------------------
# PRIORITY KEYWORDS — Jobs matching these get a 🔴 PRIORITY tag in Telegram
# Use for roles you are actively hunting RIGHT NOW
# -----------------------------------------------------------------------------

PRIORITY_KEYWORDS = [
    # Customer Support Priority
    "customer support", "customer service", "customer success",
    "remote customer service", "help desk", "technical support",
    
    # Virtual Assistant Priority
    "virtual assistant", "executive assistant", "personal assistant",
    "administrative assistant", "remote assistant",
    
    # Data Entry Priority
    "data entry", "data entry clerk", "data entry operator",
    
    # Content Priority
    "content writer", "copywriter", "social media manager",
    
    # Tech Priority
    "remote developer", "remote engineer", "devops",
]

# -----------------------------------------------------------------------------
# EXCLUDE TITLES — Block specific titles even if they pass the halal filter
# -----------------------------------------------------------------------------

EXCLUDE_TITLES = [
    "cdl driver", "truck driver", "warehouse", "factory worker",
    "convent", "monastery", "pastor", "priest", "minister",
    "alcohol", "bartender", "mixologist", "gambling", "casino",
]

# -----------------------------------------------------------------------------
# NIGERIAN STATES — Used for location detection (kept for reference)
# -----------------------------------------------------------------------------

NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibam", "Anambra", "Bauchi", "Bayelsa", "Benue",
    "Borno", "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe",
    "Imo", "Jigawa", "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara",
    "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun", "Oyo", "Plateau",
    "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara", "FCT", "Abuja",
]

# -----------------------------------------------------------------------------
# RESTRICTED LOCATIONS — Jobs that require residence in these countries/regions
# Jobs with these locations will be filtered out
# -----------------------------------------------------------------------------

RESTRICTED_LOCATIONS = [
    # North America
    "canada only", "usa only", "us only", "united states only",
    "north america only", "must be based in us", "must reside in us",
    "right to work in the us", "authorized to work in the united states",
    "us citizen", "us citizenship required", "green card", "security clearance",
    
    # United Kingdom & Europe
    "uk only", "united kingdom only", "eu only", "europe only",
    "germany only", "france only", "italy only", "spain only", "portugal only",
    "netherlands only", "belgium only", "switzerland only", "austria only",
    "sweden only", "norway only", "denmark only", "finland only", "ireland only",
    
    # Australia & Oceania
    "australia only", "oceania only", "new zealand only",
    
    # Africa (excluding Nigeria)
    "south africa only", "africa only",
    
    # Middle East
    "uae only", "saudi arabia only", "qatar only", "kuwait only",
    "bahrain only", "oman only", "dubai only",
    
    # Asia
    "asia only", "singapore only", "malaysia only", "japan only",
    "south korea only", "china only", "india only",
    
    # South America
    "brazil only", "south america only", "mexico only", "argentina only",
    "chile only", "colombia only", "peru only",
    
    # Other
    "antarctica only",
]

LINKEDIN_RSS_URLS = [
    "https://www.linkedin.com/jobs/rss/view/all?keywords=remote&location=Nigeria",
    "https://www.linkedin.com/jobs/rss/view/all?keywords=virtual+assistant&location=Worldwide",
]

# -----------------------------------------------------------------------------
# MINIMUM SALARY FILTER
# Jobs that explicitly show a salary BELOW these thresholds are skipped
# Set to 0 to disable.
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
