from bs4 import BeautifulSoup

# ── Analyse Clutch HTML ──────────────────────────────────────────────────────
print("=" * 60)
print("CLUTCH.CO ANALYSIS")
print("=" * 60)
with open("debug_clutch.html", encoding="utf-8") as f:
    clutch_html = f.read()

soup = BeautifulSoup(clutch_html, "html.parser")

# Find company card containers
candidates = [
    "li[data-category]",
    "li.provider",
    "article.provider",
    "div.provider-row",
    "li.provider-row",
    "[class*='provider']",
    "[class*='company']",
    "li[class]",
]
for sel in candidates:
    items = soup.select(sel)
    if items:
        print(f"\nCARD SELECTOR: '{sel}' => {len(items)} found")
        el = items[0]
        print(f"  Tag: {el.name}, Classes: {el.get('class', [])}")
        # Children summary
        for child in list(el.children)[:5]:
            if hasattr(child, "name") and child.name:
                print(f"    Child: <{child.name} class={child.get('class', [])}> text={child.get_text(strip=True)[:80]}")
        break

# Look for h3 or h2 company names
print("\n--- h3 links ---")
for el in soup.select("h3 a")[:3]:
    print(f"  <h3 a href={el.get('href','')}> text={el.get_text(strip=True)[:60]}")

print("\n--- h2 links ---")
for el in soup.select("h2 a")[:3]:
    print(f"  <h2 a href={el.get('href','')}> text={el.get_text(strip=True)[:60]}")

# Location
print("\n--- Location elements ---")
for sel in ["[class*='location']", "[class*='locality']", "[itemprop='addressLocality']"]:
    els = soup.select(sel)
    if els:
        print(f"  Selector '{sel}' => {len(els)} found. First: {els[0].get_text(strip=True)[:80]}")

# Website links (external)
print("\n--- Website links ---")
for sel in ["a[data-link_id='website']", "a[title='Visit Website']", "a.website-link", "[class*='website']"]:
    els = soup.select(sel)
    if els:
        print(f"  Selector '{sel}' => {len(els)} found. First href: {els[0].get('href','')[:100]}")

# Pagination
print("\n--- Pagination ---")
for sel in ["a[rel='next']", ".pagination a", "li.next a", "a.next", "[class*='pagination']"]:
    els = soup.select(sel)
    if els:
        print(f"  Selector '{sel}' => {len(els)} found. Href: {els[0].get('href','')[:100]}")

# ── Analyse GoodFirms HTML ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("GOODFIRMS.CO ANALYSIS")
print("=" * 60)
with open("debug_goodfirms.html", encoding="utf-8") as f:
    gf_html = f.read()

soup2 = BeautifulSoup(gf_html, "html.parser")

candidates2 = [
    ".company-listing-block",
    ".company-listing",
    ".cl-detail-block",
    "[class*='company-list']",
    "[class*='listing']",
    "li[class]",
    "div[class*='company']",
]
for sel in candidates2:
    items = soup2.select(sel)
    if items:
        print(f"\nCARD SELECTOR: '{sel}' => {len(items)} found")
        el = items[0]
        print(f"  Tag: {el.name}, Classes: {el.get('class', [])}")
        for child in list(el.children)[:5]:
            if hasattr(child, "name") and child.name:
                print(f"    Child: <{child.name} class={child.get('class', [])}> text={child.get_text(strip=True)[:80]}")
        break

print("\n--- GoodFirms h3 links ---")
for el in soup2.select("h3 a")[:3]:
    print(f"  href={el.get('href','')} text={el.get_text(strip=True)[:60]}")

print("\n--- GoodFirms location ---")
for sel in ["[class*='location']", "[class*='country']", "[class*='city']"]:
    els = soup2.select(sel)
    if els:
        print(f"  '{sel}' => {els[0].get_text(strip=True)[:80]}")

print("\n--- GoodFirms website links ---")
for sel in ["a.visit-website", "a[title='Visit Website']", "a[class*='website']", "a[href^='http']:not([href*='goodfirms'])"]:
    els = soup2.select(sel)
    if els:
        print(f"  '{sel}' => {els[0].get('href','')[:100]}")

print("\nDONE")
