# ─── Database Configuration ────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # WAMP default – change if yours differs
    "database": "scrapper_db",
    "charset": "utf8mb4",
}

# ─── Scraper Settings ──────────────────────────────────────────────────────────
SCRAPER_SETTINGS = {
    "chrome_version": 145,     # Match your installed Chrome version (check chrome://version)
    "page_load_wait": 6,       # seconds to wait after page load (JS rendering)
    "between_requests": 3,     # seconds between each HTTP request to a company site
    "max_retries": 3,          # retries for failed requests
    "request_timeout": 15,     # seconds before abandoning a company site fetch
    "headless": True,          # set False to watch the browser
    "max_pages_per_country": 10,  # safety cap per country (set None for unlimited)
}

# ─── Output ────────────────────────────────────────────────────────────────────
CSV_OUTPUT_PATH = "output/companies.csv"

# ─── Target Countries ──────────────────────────────────────────────────────────
# Add/remove countries as needed. These are used as filter query values on the sites.
COUNTRIES = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "Netherlands",
    "Singapore",
    "United Arab Emirates",
    "Pakistan",
    "Bangladesh",
    "Ukraine",
    "Poland",
    "Brazil",
    "Mexico",
    "Argentina",
    "South Africa",
    "Philippines",
    "Indonesia",
    "Malaysia",
    "Israel",
    "Turkey",
    "Spain",
    "Italy",
    "Sweden",
    "Norway",
    "Denmark",
    "Switzerland",
    "New Zealand",
]

# ─── User-Agent for requests ───────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}
