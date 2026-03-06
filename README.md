# 🕷️ Web Scraper — Clutch.co & GoodFirms.co

Scrapes IT company listings from **Clutch.co** and **GoodFirms.co** by country,
visits each company's website to extract **phone numbers** and **email addresses**,
stores everything in **MySQL**, and exports a **CSV** file.

---

## 📋 Requirements

- Python 3.10+
- Google Chrome (for Selenium)
- WAMP (MySQL running on localhost)

---

## ⚙️ Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure database
Edit `config.py` if your MySQL password is different from the default (empty).

### 3. Initialise the database
```bash
python database.py
```
This creates the `scrapper_db` database and `companies` table in MySQL.

---

## 🚀 Usage

### Scrape a single country (Clutch):
```bash
python main.py --source clutch --country "India"
```

### Scrape a single country (GoodFirms):
```bash
python main.py --source goodfirms --country "United States"
```

### Scrape all countries from both sites:
```bash
python main.py --all
```

### Limit pages per country (faster testing):
```bash
python main.py --source clutch --country "India" --max-pages 2
```

---

## 📤 Export CSV

Results are auto-exported after each run. To manually export:
```bash
python export_csv.py
```
Output: `output/companies.csv`

---

## 🗄️ Database Schema

| Column | Description |
|--------|-------------|
| id | Auto-increment primary key |
| source | `clutch` or `goodfirms` |
| company_name | Name of the company |
| country | Country from listing |
| city | City from listing |
| website_url | Company website URL |
| phone | Extracted phone number |
| email | Extracted email address |
| scraped_at | Timestamp when scraped |

---

## 📁 Project Structure

```
scrapping_py/
├── config.py              # DB config, countries list, settings
├── database.py            # MySQL helpers
├── contact_extractor.py   # Phone/email extraction from websites
├── main.py                # CLI entry point
├── export_csv.py          # CSV export
├── requirements.txt       # Python dependencies
├── scrapers/
│   ├── clutch_scraper.py
│   └── goodfirms_scraper.py
└── output/
    └── companies.csv      # Generated after running
```
