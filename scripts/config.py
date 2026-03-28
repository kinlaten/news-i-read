# Configuration for News Automation

# Model Settings
GEMINI_MODEL = "gemini-2.5-flash-lite"

# News Search Settings
EXA_NUM_RESULTS = 8
EXA_SNIPPET_LENGTH = 500

# Notification Settings
DISCORD_MAX_CHARS = 1900

# News Categories
# Each category will be fetched, summarized, and sent to its own webhook
# save_to_file: If True, this category will be included in the daily .md file
NEWS_CATEGORIES = [
    {
        "name": "Tech News",
        "query": "breaking tech news today",
        "webhook_env": "DISCORD_WEBHOOK_TECH",
        "save_to_file": True,
    },
    {
        "name": "Australia Visa & Law",
        "query": "latest changes in australia laws for visa international students and jobs",
        "webhook_env": "DISCORD_WEBHOOK_AU_LAW",
        "save_to_file": False,
    },
]
