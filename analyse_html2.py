from bs4 import BeautifulSoup

# ── Deep dive: Clutch card structure ─────────────────────────────────────────
with open("debug_clutch.html", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

cards = soup.select("div.provider-row")
print(f"Clutch cards: {len(cards)}")
if cards:
    card = cards[0]
    print("\n--- FIRST CARD full structure (truncated) ---")
    print(str(card)[:2000])

    # Find company name
    print("\n--- Name candidates ---")
    for sel in ["h3", ".company_info h3", ".provider__main-info h3", "h3.company-name"]:
        els = card.select(sel)
        if els:
            print(f"  '{sel}': {els[0].get_text(strip=True)[:80]}")

    # Find location
    print("\n--- Location candidates ---")
    for sel in ["[itemprop='addressLocality']", "[class*='location']", "[class*='locality']", "span.location"]:
        els = card.select(sel)
        if els:
            print(f"  '{sel}': '{els[0].get_text(strip=True)[:80]}'")

    # Find website link
    print("\n--- Website link candidates ---")
    for sel in ["[class*='website']", "a[data-link_id]", "h3 a", "[class*='visit']"]:
        els = card.select(sel)
        if els:
            href = els[0].get("href", "")[:150]
            print(f"  '{sel}': href={href}")

# ── Deep dive: GoodFirms card structure ──────────────────────────────────────
print("\n" + "=" * 60)
print("GOODFIRMS DEEP DIVE")
print("=" * 60)
with open("debug_goodfirms.html", encoding="utf-8") as f:
    soup2 = BeautifulSoup(f, "html.parser")

# Find the parent of a known h3 a element
h3s = soup2.select("h3 a")
if h3s:
    # Walk up from h3 to find card container
    h3_el = h3s[0].parent.parent  # h3's parent
    print(f"h3 parent: <{h3_el.name} class={h3_el.get('class',[])}> ")
    grandparent = h3_el.parent
    print(f"h3 grandparent: <{grandparent.name} class={grandparent.get('class',[])}> ")
    great = grandparent.parent
    print(f"h3 great-grandparent: <{great.name} class={great.get('class',[])}> ")

    # Print first card snippet
    print("\n--- First GoodFirms card (grandparent) ---")
    print(str(grandparent)[:2000])

# Check for location inside GoodFirms cards
print("\n--- GoodFirms location/country selectors ---")
for sel in ["[class*='country']", "[class*='city']", "[class*='location']", "address", "[class*='address']"]:
    els = soup2.select(sel)
    if els:
        print(f"  '{sel}' => count={len(els)}, first='{els[0].get_text(strip=True)[:80]}'")

# Pagination
print("\n--- GoodFirms pagination ---")
for sel in ["a[rel='next']", ".pagination a", "li.next a", "[class*='pagination']", "a[class*='next']"]:
    els = soup2.select(sel)
    if els:
        print(f"  '{sel}' => {len(els)} found, href={els[0].get('href','')[:100]}")

print("\nDONE")
