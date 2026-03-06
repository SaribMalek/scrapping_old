"""
contact_extractor.py
Extract phone and email from a company website with homepage + contact-page fallbacks.
"""

import re
import time
from html import unescape
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import SCRAPER_SETTINGS, HEADERS

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
PHONE_PATTERN = re.compile(
    r"(?:\+|00)?\d[\d\s().\-]{6,}\d"
)

JUNK_EMAIL_DOMAINS = {
    "example.com",
    "domain.com",
    "email.com",
    "test.com",
    "sentry.io",
    "wixpress.com",
    "amazonaws.com",
}

SKIP_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".css",
    ".js",
    ".pdf",
    ".zip",
)

CONTACT_HINTS = (
    "contact",
    "contact-us",
    "about",
    "about-us",
    "reach",
    "support",
    "connect",
    "get-in-touch",
)


def _unique(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _normalize_phone(value: str) -> str:
    value = (value or "").strip()
    value = value.replace("tel:", "").replace("callto:", "")
    value = re.sub(r"\s+", " ", value)
    value = value.lstrip(")")
    return value.strip(" ,;|")


def _is_valid_phone(number: str) -> bool:
    number = _normalize_phone(number)
    if re.fullmatch(r"(19|20)\d{2}\s*-\s*(19|20)\d{2}", number):
        return False
    digits = re.sub(r"\D", "", number)
    if not (7 <= len(digits) <= 15):
        return False
    if len(set(digits)) <= 1:
        return False
    # Avoid long plain numeric IDs unless prefixed as international format.
    if number.isdigit() and len(digits) > 10:
        return False
    return True


def _is_valid_email(email: str) -> bool:
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1]
    if domain in JUNK_EMAIL_DOMAINS:
        return False
    if email.endswith((".png", ".jpg", ".gif", ".svg", ".js")):
        return False
    return True


def _pick_best_phone(candidates: list[str]) -> str:
    best, best_score = "", -10**9
    for raw in _unique([_normalize_phone(c) for c in candidates if c]):
        if not _is_valid_phone(raw):
            continue
        digits = re.sub(r"\D", "", raw)
        score = 0
        if raw.startswith("+") or raw.startswith("00"):
            score += 5
        if any(ch in raw for ch in (" ", "-", "(", ")", ".")):
            score += 3
        if raw.isdigit() and len(digits) > 9:
            score -= 4
        if 9 <= len(digits) <= 12:
            score += 2
        if score > best_score:
            best, best_score = raw, score
    return best


def _pick_best_email(candidates: list[str]) -> str:
    for email in _unique([c.strip() for c in candidates if c]):
        if _is_valid_email(email):
            return email
    return ""


def _decode_cfemail(encoded: str) -> str:
    try:
        r = int(encoded[:2], 16)
        out = ""
        for i in range(2, len(encoded), 2):
            out += chr(int(encoded[i : i + 2], 16) ^ r)
        return out
    except Exception:
        return ""


def _fetch_html(url: str) -> str | None:
    if not url or not url.startswith("http"):
        return None
    if any(url.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
        return None

    retries = SCRAPER_SETTINGS.get("max_retries", 2)
    timeout = SCRAPER_SETTINGS.get("request_timeout", 15)
    for _ in range(max(1, retries)):
        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=timeout,
                allow_redirects=True,
            )
            if resp.ok and "text/html" in resp.headers.get("Content-Type", ""):
                return resp.text
        except Exception:
            pass
    return None


def _extract_contact_links(html: str, base_url: str, limit: int = 6) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    parsed_base = urlparse(base_url)
    links: list[str] = []

    for a in soup.find_all("a", href=True):
        href = unescape((a.get("href") or "").strip())
        if not href:
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc and parsed_base.netloc and parsed.netloc != parsed_base.netloc:
            continue

        hint_target = (href + " " + a.get_text(" ", strip=True)).lower()
        if any(h in hint_target for h in CONTACT_HINTS):
            links.append(full)

    return _unique(links)[:limit]


def _extract_from_html(html: str, base_url: str = "") -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    phones: list[str] = []
    emails: list[str] = []

    for tag in soup.find_all(attrs={"data-cfemail": True}):
        decoded = _decode_cfemail((tag.get("data-cfemail") or "").strip())
        if _is_valid_email(decoded):
            emails.append(decoded)

    for a in soup.find_all("a", href=True):
        href = unescape((a.get("href") or "").strip())
        lower = href.lower()

        if lower.startswith("tel:") or lower.startswith("callto:"):
            phones.append(_normalize_phone(href))

        if lower.startswith("mailto:"):
            mail = href.split(":", 1)[1].split("?")[0].strip()
            if EMAIL_PATTERN.match(mail):
                emails.append(mail)

        if "wa.me/" in lower:
            phone = href.split("wa.me/")[-1].split("?")[0]
            phones.append(_normalize_phone(phone))
        elif "api.whatsapp.com/send" in lower:
            phone = parse_qs(urlparse(href).query).get("phone", [""])[0]
            phones.append(_normalize_phone(phone))

        for m in EMAIL_PATTERN.findall(href):
            emails.append(m)

    body_text = soup.get_text(separator=" ", strip=True)

    for match in EMAIL_PATTERN.findall(body_text):
        emails.append(match)

    for match in PHONE_PATTERN.findall(body_text):
        phones.append(_normalize_phone(match))

    phone = _pick_best_phone(phones)
    email = _pick_best_email(emails)
    return phone, email


def _try_contact_pages(base_url: str, homepage_html: str = "") -> tuple[str, str]:
    fixed_suffixes = ["/contact", "/contact-us", "/about", "/about-us", "/reach-us"]
    urls = [base_url.rstrip("/") + s for s in fixed_suffixes]

    if homepage_html:
        urls.extend(_extract_contact_links(homepage_html, base_url))

    for trial_url in _unique(urls):
        html = _fetch_html(trial_url)
        if not html:
            continue
        phone, email = _extract_from_html(html, trial_url)
        if phone or email:
            return phone, email

    return "", ""


def _resolve_goodfirms_profile(url: str) -> str:
    if "goodfirms.co/company/" not in (url or ""):
        return url

    html = _fetch_html(url)
    if not html:
        return url

    soup = BeautifulSoup(html, "html.parser")
    selectors = ["a.visit-website[href]", "a.web-url[href]", "a.list-blue-link[href]"]
    for selector in selectors:
        for a in soup.select(selector):
            href = (a.get("href") or "").strip()
            if href and "goodfirms.co/company/" not in href and href.startswith("http"):
                return href
    return url


def extract_contacts(url: str) -> tuple[str, str]:
    """Given a company URL, return (phone, email)."""
    if not url:
        return "", ""

    target_url = _resolve_goodfirms_profile(url)
    html = _fetch_html(target_url)
    if not html:
        return "", ""

    phone, email = _extract_from_html(html, target_url)

    if not phone or not email:
        p2, e2 = _try_contact_pages(target_url, homepage_html=html)
        if not phone:
            phone = p2
        if not email:
            email = e2

    time.sleep(SCRAPER_SETTINGS.get("between_requests", 1))
    return phone, email
