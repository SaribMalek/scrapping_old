"""
export_csv.py – Export all rows from the companies table to a CSV file.
Run:  python export_csv.py
"""

import csv
import os
from datetime import datetime
from database import get_all_companies
from config import CSV_OUTPUT_PATH


def export_to_csv(output_path: str = None):
    """Fetch all DB records and write them to a CSV file."""
    path = output_path or CSV_OUTPUT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    rows = get_all_companies()
    if not rows:
        print("[CSV] No data found in database.")
        return

    fieldnames = [
        "id", "source", "company_name", "country", "city",
        "website_url", "phone", "email", "scraped_at"
    ]

    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Convert scraped_at datetime to string if needed
            if hasattr(row.get("scraped_at"), "strftime"):
                row["scraped_at"] = row["scraped_at"].strftime("%Y-%m-%d %H:%M:%S")
            # Only write known columns
            filtered = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(filtered)

    print(f"[CSV] Exported {len(rows)} records to: {os.path.abspath(path)}")


if __name__ == "__main__":
    export_to_csv()
