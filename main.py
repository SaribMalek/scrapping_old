"""
main.py – Orchestrates the full scraping pipeline.

Usage examples:
  python main.py --source clutch --country "India"
  python main.py --source goodfirms --country "United States" --max-pages 3
  python main.py --all                  # Scrapes ALL countries from BOTH sources
  python main.py --all --max-pages 2    # All countries, limit 2 pages each
"""

import argparse
import sys
from config import COUNTRIES, SCRAPER_SETTINGS
from database import init_db, save_company
from contact_extractor import extract_contacts
from scrapers.clutch_scraper import scrape_clutch
from scrapers.goodfirms_scraper import scrape_goodfirms
from export_csv import export_to_csv


def process_companies(source: str, companies: list):
    """For each company, extract contact info and save to DB."""
    total = len(companies)
    for idx, company in enumerate(companies, start=1):
        name = company.get("company_name", "")
        url = company.get("website_url", "")
        country = company.get("country", "")
        city = company.get("city", "")

        print(f"  [{idx}/{total}] {name} - {url}")

        phone, email = "", ""
        if url:
            try:
                phone, email = extract_contacts(url)
            except Exception as e:
                print(f"    [WARNING] Contact extraction failed: {e}")

        if phone or email:
            print(f"    [OK] Phone: {phone or 'N/A'} | Email: {email or 'N/A'}")
        else:
            print("    [NO] No contact info found")

        save_company(
            source=source,
            company_name=name,
            country=country,
            city=city,
            website_url=url,
            phone=phone,
            email=email,
        )


def run_source_country(source: str, country: str, max_pages: int):
    print(f"\n{'='*60}")
    print(f"  Source: {source.upper()} | Country: {country}")
    print(f"{'='*60}")

    if source == "clutch":
        companies = scrape_clutch(country=country, max_pages=max_pages)
    elif source == "goodfirms":
        companies = scrape_goodfirms(country=country, max_pages=max_pages)
    else:
        print(f"[ERROR] Unknown source: {source}")
        return

    if not companies:
        print(f"  No companies found for {country} on {source}.")
        return

    print(f"\n  Processing {len(companies)} companies for contact info...\n")
    process_companies(source=source, companies=companies)


def main():
    parser = argparse.ArgumentParser(
        description="Web scraper for Clutch.co and GoodFirms.co"
    )
    parser.add_argument(
        "--source",
        choices=["clutch", "goodfirms"],
        help="Which site to scrape",
    )
    parser.add_argument(
        "--country",
        type=str,
        help="Country name to filter (e.g. 'India')",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to scrape per country (default from config)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scrape ALL countries from BOTH sources",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export results to CSV after scraping",
    )
    args = parser.parse_args()

    max_pages = args.max_pages or SCRAPER_SETTINGS.get("max_pages_per_country", 10)

    # ─── Init DB ───────────────────────────────────────────────────────────────
    print("[MAIN] Initialising database...")
    init_db()

    # ─── Decide what to scrape ─────────────────────────────────────────────────
    if args.all:
        sources = ["clutch", "goodfirms"]
        for source in sources:
            for country in COUNTRIES:
                try:
                    run_source_country(source, country, max_pages)
                except Exception as e:
                    print(f"[ERROR] Failed for {source}/{country}: {e}")
                    continue
    elif args.source and args.country:
        run_source_country(args.source, args.country, max_pages)
    elif args.source and not args.country:
        # Scrape all countries for one source
        for country in COUNTRIES:
            try:
                run_source_country(args.source, country, max_pages)
            except Exception as e:
                print(f"[ERROR] Failed for {args.source}/{country}: {e}")
                continue
    else:
        parser.print_help()
        sys.exit(0)

    # ─── Auto export CSV ───────────────────────────────────────────────────────
    print("\n[MAIN] Exporting results to CSV...")
    export_to_csv()
    print("[MAIN] Done! Check 'output/companies.csv' for results.")


if __name__ == "__main__":
    main()
