"""
corint_fara_fragment.py
-----------------------
Parcurge toate cărțile de pe edituracorint.ro, verifică dacă pagina
fiecărei cărți conține butonul/linkul "Răsfoiește" (fragment de citit).
Dacă NU îl găsește, salvează titlul cărții în fișierul output.

Utilizare:
    pip install requests beautifulsoup4
    python corint_fara_fragment.py

Fișier rezultat: carti_fara_rasfoieste.txt
"""

import time
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Configurare ──────────────────────────────────────────────────────────────

BASE_URL      = "https://edituracorint.ro"
CATALOG_URL   = "https://edituracorint.ro/carti.html"   # lista tuturor cărților
OUTPUT_FILE   = "carti_fara_rasfoieste.txt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}

DELAY_BETWEEN_REQUESTS = 1.0   # secunde între cereri (politicos cu serverul)
MAX_PAGES_CATALOG      = 999   # limită de siguranță pentru paginare

# ── Funcții ajutătoare ───────────────────────────────────────────────────────

def get_soup(url: str, session: requests.Session) -> BeautifulSoup | None:
    """Descarcă pagina și returnează un obiect BeautifulSoup."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"  [EROARE] {url} → {e}", file=sys.stderr)
        return None


def get_all_book_urls(session: requests.Session) -> list[str]:
    """
    Colectează URL-urile tuturor cărților parcurgând paginile din catalog.
    Site-ul folosește paginare tip ?p=2, ?p=3 etc.
    """
    book_urls: list[str] = []
    visited: set[str] = set()

    page = 1
    while page <= MAX_PAGES_CATALOG:
        url = CATALOG_URL if page == 1 else f"{CATALOG_URL}?p={page}"
        print(f"[Catalog] pagina {page}: {url}")

        soup = get_soup(url, session)
        if soup is None:
            break

        # Fiecare carte din grilă e un <a> în interiorul unui bloc .product-item
        # URL-urile arată ca: https://edituracorint.ro/titlu-carte.html
        product_links = soup.select("li.product-item a.product-item-link")

        if not product_links:
            # Încearcă selector alternativ
            product_links = soup.select("h2.product-name a, strong.product-name a")

        if not product_links:
            print(f"  → Nu s-au găsit cărți pe pagina {page}. Oprire.")
            break

        new_found = 0
        for a in product_links:
            href = a.get("href", "").strip()
            if href and href not in visited and href.startswith(BASE_URL):
                visited.add(href)
                book_urls.append(href)
                new_found += 1

        print(f"  → {new_found} cărți noi găsite (total: {len(book_urls)})")

        # Verifică dacă există pagina următoare
        next_page = soup.select_one('a[title="Pagina Spre finalizarea comenzii"]')
        if not next_page:
            # Selector alternativ pentru butonul "Următoarea"
            next_page = soup.select_one('li.pages-item-next a')

        if not next_page:
            print("  → Ultima pagină de catalog.")
            break

        page += 1
        time.sleep(DELAY_BETWEEN_REQUESTS)

    return book_urls


def has_rasfoieste(soup: BeautifulSoup) -> bool:
    """
    Verifică dacă pagina unei cărți conține butonul/linkul 'Răsfoiește'.
    Caută:
      1. Orice tag <a> al cărui text conține 'răsfoiește' (case-insensitive, diacritice)
      2. Orice tag cu atribut href ce conține 'rasfoieste' sau 'fragment' sau 'preview'
      3. Orice element cu clasa sau id sugestiv
    """
    text_lower = soup.get_text(separator=" ").lower()

    # Variantele posibile ale textului (cu/fără diacritice)
    keywords_text = ["răsfoiește", "rasfoieste", "răsfoia", "rasfoieste"]
    for kw in keywords_text:
        if kw in text_lower:
            return True

    # Verifică link-uri cu href relevant
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if any(kw in href for kw in ["rasfoieste", "fragment", "preview", "citeste"]):
            return True

    return False


def get_book_title(soup: BeautifulSoup, fallback_url: str) -> str:
    """Extrage titlul cărții din pagina ei."""
    # Încearcă h1 principal
    h1 = soup.select_one("h1.page-title span, h1.product-name span, h1")
    if h1:
        return h1.get_text(strip=True)

    # Fallback: titlul paginii HTML
    title_tag = soup.find("title")
    if title_tag:
        raw = title_tag.get_text(strip=True)
        # Elimină sufixul " | Autor" dacă există
        return raw.split("|")[0].strip()

    # Ultimul fallback: URL-ul
    return fallback_url.split("/")[-1].replace(".html", "").replace("-", " ").title()


# ── Script principal ─────────────────────────────────────────────────────────

def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    print("=" * 60)
    print("Corint Fragment Checker")
    print(f"Catalog: {CATALOG_URL}")
    print(f"Output:  {OUTPUT_FILE}")
    print("=" * 60)

    # Pasul 1: colectează toate URL-urile de cărți
    print("\n[1/2] Colectare URL-uri cărți din catalog...")
    book_urls = get_all_book_urls(session)
    print(f"\nTotal cărți găsite: {len(book_urls)}\n")

    if not book_urls:
        print("Nu s-au găsit cărți. Verifică URL-ul catalogului sau structura site-ului.")
        return

    # Pasul 2: verifică fiecare carte pentru butonul Răsfoiește
    print("[2/2] Verificare butoane 'Răsfoiește'...")
    fara_fragment: list[tuple[str, str]] = []   # (titlu, url)

    for i, url in enumerate(book_urls, 1):
        print(f"  [{i:>4}/{len(book_urls)}] {url.split('/')[-1][:60]}", end="", flush=True)
        time.sleep(DELAY_BETWEEN_REQUESTS)

        soup = get_soup(url, session)
        if soup is None:
            print(" → EROARE (skip)")
            continue

        titlu = get_book_title(soup, url)

        if has_rasfoieste(soup):
            print(f" → ✓ are Răsfoiește")
        else:
            print(f" → ✗ LIPSĂ  ({titlu[:50]})")
            fara_fragment.append((titlu, url))

    # Pasul 3: scrie rezultatele
    output_path = Path(OUTPUT_FILE)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("Cărți fără buton 'Răsfoiește' pe edituracorint.ro\n")
        f.write(f"Generat: {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Total verificate: {len(book_urls)} | Fără fragment: {len(fara_fragment)}\n")
        f.write("=" * 70 + "\n\n")
        for titlu, url in fara_fragment:
            f.write(f"{titlu}\n    {url}\n\n")

    print("\n" + "=" * 60)
    print(f"Gata! {len(fara_fragment)} cărți fără 'Răsfoiește' din {len(book_urls)} verificate.")
    print(f"Rezultate salvate în: {output_path.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()