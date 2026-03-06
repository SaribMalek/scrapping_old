"""
debug_page.py – Opens Clutch.co and GoodFirms in Selenium, saves raw HTML
so we can see the real CSS selectors.
Run: python debug_page.py
"""
import time, sys
import undetected_chromedriver as uc
from config import SCRAPER_SETTINGS

def save_page(url, filename):
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # NOT headless so Cloudflare/bot checks pass more easily
    driver = uc.Chrome(options=options, version_main=SCRAPER_SETTINGS["chrome_version"])
    try:
        print(f"Loading: {url}")
        driver.get(url)
        print("Waiting 10 seconds for JS to render...")
        time.sleep(10)
        # Print the current URL (may have redirected)
        print(f"Final URL: {driver.current_url}")
        html = driver.page_source
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved to {filename} ({len(html)} chars)")
    finally:
        driver.quit()

if __name__ == "__main__":
    save_page(
        "https://clutch.co/it-services?country[]=India&sort_by=sponsored&page=1",
        "debug_clutch.html"
    )
    save_page(
        "https://www.goodfirms.co/companies/web-development-agency?country=India&page=1",
        "debug_goodfirms.html"
    )
    print("Done! Check debug_clutch.html and debug_goodfirms.html")
