"""
database.py – MySQL schema creation and CRUD helpers
"""

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
from config import DB_CONFIG


# ─── Schema ────────────────────────────────────────────────────────────────────

CREATE_DB_SQL = "CREATE DATABASE IF NOT EXISTS `scrapper_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `companies` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `source`       VARCHAR(50)  NOT NULL COMMENT 'clutch or goodfirms',
    `company_name` VARCHAR(255) NOT NULL,
    `country`      VARCHAR(100) DEFAULT NULL,
    `city`         VARCHAR(100) DEFAULT NULL,
    `website_url`  TEXT         DEFAULT NULL,
    `phone`        VARCHAR(150) DEFAULT NULL,
    `email`        VARCHAR(255) DEFAULT NULL,
    `scraped_at`   DATETIME     DEFAULT NULL,
    UNIQUE KEY `uniq_source_name` (`source`, `company_name`(180))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


# ─── Connection ────────────────────────────────────────────────────────────────

def get_connection(with_db: bool = True):
    """Return a fresh MySQL connection.  Pass with_db=False to skip selecting a database (used during init)."""
    cfg = DB_CONFIG.copy()
    if not with_db:
        cfg.pop("database", None)
    return mysql.connector.connect(**cfg)


# ─── Init ──────────────────────────────────────────────────────────────────────

def init_db():
    """Create the database and table if they do not already exist."""
    conn = get_connection(with_db=False)
    cursor = conn.cursor()
    cursor.execute(CREATE_DB_SQL)
    cursor.execute(f"USE `{DB_CONFIG['database']}`;")
    cursor.execute(CREATE_TABLE_SQL)
    conn.commit()
    cursor.close()
    conn.close()
    print("[DB] Database and table ready.")


# ─── Write ─────────────────────────────────────────────────────────────────────

def save_company(
    source: str,
    company_name: str,
    country: str = None,
    city: str = None,
    website_url: str = None,
    phone: str = None,
    email: str = None,
):
    """
    Insert a new company or update phone/email if the record already exists.
    Silently ignores duplicate entries that have no new contact info.
    """
    def clean(value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    sql = """
        INSERT INTO companies (source, company_name, country, city, website_url, phone, email, scraped_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            country     = COALESCE(NULLIF(VALUES(country), ''), country),
            city        = COALESCE(NULLIF(VALUES(city), ''), city),
            website_url = COALESCE(NULLIF(VALUES(website_url), ''), website_url),
            phone       = COALESCE(NULLIF(VALUES(phone), ''), phone),
            email       = COALESCE(NULLIF(VALUES(email), ''), email),
            scraped_at  = VALUES(scraped_at)
    """
    values = (
        clean(source),
        clean(company_name),
        clean(country),
        clean(city),
        clean(website_url),
        clean(phone),
        clean(email),
        datetime.now(),
    )
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"[DB ERROR] {err} | company={company_name}")


# ─── Read ──────────────────────────────────────────────────────────────────────

def get_all_companies():
    """Fetch every row from the companies table and return as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM companies ORDER BY id ASC;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ─── Run directly to initialise DB ────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("[DB] Setup complete. Table 'companies' is ready.")
