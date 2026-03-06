"""
scrapers/clutch_scraper.py  (v2 — selectors verified from live HTML)

Card:     div.provider-row
Name:     data-title attribute on card (fastest) or h3 text
Location: .location element inside card
Website:  decoded from data-link attribute (u= query param)
Pagination: a[rel='next'] or next page link
"""

import time
import re
import urllib.parse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import SCRAPER_SETTINGS

BASE_URL = "https://clutch.co/it-services"


class SafeChrome(uc.Chrome):
    def __del__(self):
        # undetected_chromedriver can call quit() again during GC and throw
        # WinError 6 on Windows; suppress destructor-time cleanup errors.
        try:
            self.quit()
        except Exception:
            pass


def _build_driver():
    options = uc.ChromeOptions()
    if SCRAPER_SETTINGS.get("headless", False):
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


def _extract_real_url(redirect_url: str) -> str:
    """Extract the actual company website URL from Clutch's r.clutch.co/redirect?...&u=URL"""
    try:
        parsed = urllib.parse.urlparse(redirect_url)
        params = urllib.parse.parse_qs(parsed.query)
        u = params.get("u", [""])[0]
        if u and u.startswith("http"):
            # If it's still a PPC click URL, try extracting again
            inner = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
            final = inner.get("u", [u])[0]
            return final
        return u or redirect_url
    except Exception:
        return redirect_url


def _parse_companies_on_page(driver) -> list:
    """Extract all company cards visible on the current page."""
    companies = []
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.provider-row")
            )
        )
    except TimeoutException:
        source = (driver.page_source or "").lower()
        if "cdn-cgi/challenge-platform" in source or "cloudflare" in source:
            print("[Clutch] Blocked by Cloudflare challenge (try headless=False).")
        else:
            print("[Clutch] Timed out waiting for company cards (page blocked or no results).")
        return companies

    cards = driver.find_elements(By.CSS_SELECTOR, "div.provider-row")
    print(f"[Clutch] Found {len(cards)} cards on this page")

    for card in cards:
        try:
            # Name — fastest: read from data-title attribute
            name = card.get_attribute("data-title") or ""
            if not name:
                try:
                    h3 = card.find_element(By.CSS_SELECTOR, "h3")
                    name = h3.text.strip()
                except NoSuchElementException:
                    pass

            # Location — .location class element
            country_text, city_text = "", ""
            try:
                loc_el = card.find_element(By.CSS_SELECTOR, ".location")
                loc_raw = loc_el.text.strip()
                parts = [p.strip() for p in loc_raw.split(",")]
                city_text = parts[0] if parts else ""
                country_text = parts[-1] if len(parts) > 1 else loc_raw
            except NoSuchElementException:
                pass

            # Website — extract from data-link attribute (contains redirect with u= param)
            website = ""
            data_link = card.get_attribute("data-link") or ""
            if data_link:
                website = _extract_real_url(data_link)

            # Fallback: look for explicit website link
            if not website or "clutch.co" in website:
                try:
                    site_els = card.find_elements(By.CSS_SELECTOR, "[class*='website'] a, a[class*='website']")
                    for se in site_els:
                        href = se.get_attribute("href") or ""
                        if href and "r.clutch.co" in href:
                            website = _extract_real_url(href)
                            break
                        elif href and "clutch.co" not in href:
                            website = href
                            break
                except Exception:
                    pass

            if name:
                companies.append({
                    "company_name": name,
                    "country": country_text,
                    "city": city_text,
                    "website_url": website,
                })
        except Exception:
            continue

    return companies


def scrape_clutch(country: str, max_pages: int = None) -> list:
    """Scrape Clutch.co IT-services listings for a given country."""
    max_pages = max_pages or SCRAPER_SETTINGS.get("max_pages_per_country", 10)
    all_companies = []

    print(f"[Clutch] Scraping country: '{country}' (up to {max_pages} pages)")
    driver = _build_driver()

    try:
        for page_num in range(1, max_pages + 1):
            # Clutch URL format: country[]=India (spaces must stay as-is, Clutch handles encoding)
            url = (
                f"{BASE_URL}"
                f"?country%5B%5D={urllib.parse.quote(country)}"
                f"&sort_by=sponsored"
                f"&page={page_num}"
            )
            print(f"[Clutch] Loading page {page_num}: {url}")
            driver.get(url)
            time.sleep(SCRAPER_SETTINGS["page_load_wait"])

            companies = _parse_companies_on_page(driver)
            if not companies:
                print(f"[Clutch] No companies on page {page_num} — stopping.")
                break

            all_companies.extend(companies)
            print(f"[Clutch] Page {page_num}: {len(companies)} companies (total: {len(all_companies)})")

            # Check for next page
            try:
                next_el = driver.find_element(
                    By.CSS_SELECTOR, "a[rel='next'], li.next a, .pagination-next a"
                )
                if not next_el.is_enabled() or not next_el.get_attribute("href"):
                    break
            except NoSuchElementException:
                print(f"[Clutch] No next page — done with '{country}'.")
                break

            time.sleep(SCRAPER_SETTINGS["between_requests"])

    except Exception as e:
        print(f"[Clutch] Error: {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    print(f"[Clutch] Done '{country}': {len(all_companies)} total companies.")
    return all_companies
