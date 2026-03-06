import time
import urllib.parse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import SCRAPER_SETTINGS

BASE_URL = "https://www.goodfirms.co/companies/web-development-agency"


class SafeChrome(uc.Chrome):
    def __del__(self):
        # undetected_chromedriver can call quit() again during GC and throw
        # WinError 6 on Windows; suppress destructor-time cleanup errors.
        try:
            self.quit()
        except Exception:
            pass


def _build_driver(headless_override=None):
    options = uc.ChromeOptions()
    headless = (
        SCRAPER_SETTINGS.get("headless", False)
        if headless_override is None
        else headless_override
    )
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = SafeChrome(
        options=options,
        version_main=SCRAPER_SETTINGS["chrome_version"],
    )
    return driver


def _is_cloudflare_challenge(driver) -> bool:
    source = (driver.page_source or "").lower()
    title = (driver.title or "").lower()
    return (
        "cdn-cgi/challenge-platform" in source
        or "cf-chl-" in source
        or "cloudflare" in source
        or "just a moment" in title
    )


def _wait_for_cards_after_challenge(driver, timeout_seconds: int = 45) -> bool:
    """Wait for challenge to clear and listing cards to appear."""
    end_time = time.time() + timeout_seconds
    while time.time() < end_time:
        cards = driver.find_elements(By.CSS_SELECTOR, "div.firm-wrapper-item")
        if cards:
            return True
        if not _is_cloudflare_challenge(driver):
            return False
        time.sleep(2)
    return False


def _parse_companies_on_page(driver) -> list:
    """Extract all company cards on the current GoodFirms page."""
    companies = []
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.firm-wrapper-item"))
        )
    except TimeoutException:
        source = (driver.page_source or "").lower()
        if "cdn-cgi/challenge-platform" in source or "cloudflare" in source:
            print("[GoodFirms] Blocked by Cloudflare challenge (try headless=False).")
        else:
            print("[GoodFirms] Timed out - page blocked or no results.")
        return companies

    cards = driver.find_elements(By.CSS_SELECTOR, "div.firm-wrapper-item")
    print(f"[GoodFirms] Found {len(cards)} cards on this page")

    for card in cards:
        try:
            name, website = "", ""

            try:
                name_el = card.find_element(By.CSS_SELECTOR, "h3.firm-name a")
                name = name_el.text.strip()
            except NoSuchElementException:
                pass

            # Prefer explicit website links; fallback to firm-name href.
            try:
                site_links = card.find_elements(By.CSS_SELECTOR, "a.visit-website[href]")
                for link in site_links:
                    href = (link.get_attribute("href") or "").strip()
                    if not href:
                        continue
                    if "goodfirms.co/company/" in href:
                        continue
                    website = href
                    break
            except Exception:
                pass

            if not website:
                try:
                    fallback = card.find_element(By.CSS_SELECTOR, "h3.firm-name a")
                    website = (fallback.get_attribute("href") or "").strip()
                except NoSuchElementException:
                    website = ""

            if "?" in website:
                website = website.split("?")[0]

            city_text, country_text = "", ""
            try:
                loc_els = card.find_elements(
                    By.CSS_SELECTOR,
                    ".location-text, .city-name, [class*='location'] span, [class*='country']",
                )
                if loc_els:
                    loc_raw = loc_els[0].text.strip()
                    parts = [p.strip() for p in loc_raw.split(",")]
                    city_text = parts[0] if parts else ""
                    country_text = parts[-1] if len(parts) > 1 else loc_raw
            except NoSuchElementException:
                pass

            if name:
                companies.append(
                    {
                        "company_name": name,
                        "country": country_text,
                        "city": city_text,
                        "website_url": website,
                    }
                )
        except Exception:
            continue

    return companies


def scrape_goodfirms(country: str, max_pages: int = None) -> list:
    """Scrape GoodFirms web-dev-agency listings for a given country."""
    max_pages = max_pages or SCRAPER_SETTINGS.get("max_pages_per_country", 10)
    all_companies = []

    print(f"[GoodFirms] Scraping country: '{country}' (up to {max_pages} pages)")
    driver = _build_driver()

    try:
        for page_num in range(1, max_pages + 1):
            url = (
                f"{BASE_URL}"
                f"?country={urllib.parse.quote(country)}"
                f"&page={page_num}"
            )
            print(f"[GoodFirms] Loading page {page_num}: {url}")
            driver.get(url)
            time.sleep(SCRAPER_SETTINGS["page_load_wait"])

            # If headless gets challenged, retry in headed mode so listings can load.
            if _is_cloudflare_challenge(driver):
                print("[GoodFirms] Cloudflare challenge detected.")
                challenge_wait = SCRAPER_SETTINGS.get("challenge_wait_seconds", 45)

                if SCRAPER_SETTINGS.get("headless", False):
                    print("[GoodFirms] Retrying this page in visible browser mode...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    driver = _build_driver(headless_override=False)
                    driver.get(url)

                if _wait_for_cards_after_challenge(driver, timeout_seconds=challenge_wait):
                    print("[GoodFirms] Challenge cleared, continuing scrape.")
                else:
                    print("[GoodFirms] Challenge not cleared in time - stopping this country.")
                    break

            companies = _parse_companies_on_page(driver)
            if not companies:
                print(f"[GoodFirms] No companies on page {page_num} - stopping.")
                break

            all_companies.extend(companies)
            print(
                f"[GoodFirms] Page {page_num}: {len(companies)} companies "
                f"(total: {len(all_companies)})"
            )

            if page_num < max_pages:
                time.sleep(SCRAPER_SETTINGS["between_requests"])

    except Exception as e:
        print(f"[GoodFirms] Error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"[GoodFirms] Done '{country}': {len(all_companies)} total companies.")
    return all_companies
