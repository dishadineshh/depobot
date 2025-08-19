# scrape_site.py (BS4-only, Windows-safe save)
import os, hashlib, time, urllib.parse as up, requests, pandas as pd
from bs4 import BeautifulSoup
import tldextract

BASE = "https://www.uploaddigital.co"
HEADERS = {"User-Agent": "UploadDigitalBot/1.0 (+contact@uploaddigital.co)"}

def canonicalize(url: str) -> str:
    return up.urljoin(BASE, url.split('#')[0])

def same_domain(url: str) -> bool:
    base = tldextract.extract(BASE); u = tldextract.extract(url)
    return (u.domain, u.suffix) == (base.domain, base.suffix)

def get_links(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception:
        return [], None
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = canonicalize(a["href"])
        if href.startswith(("mailto:", "tel:")): continue
        if same_domain(href) and href.startswith(BASE):
            links.append(href)
    return list(set(links)), r.text

def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript"]):  # keep sections/aside/header/footer now
        tag.decompose()
    return " ".join(soup.get_text(" ").split())

def try_sitemap():
    try:
        sm = requests.get(up.urljoin(BASE, "/sitemap.xml"), headers=HEADERS, timeout=15)
        if sm.ok and "<urlset" in sm.text:
            soup = BeautifulSoup(sm.text, "xml")
            return [u.loc.text.strip() for u in soup.find_all("url") if u and u.loc and u.loc.text]
    except Exception:
        pass
    return []

def crawl(max_pages=600):
    seen, to_visit, pages = set(), set([BASE]), []
    sm = try_sitemap()
    if sm: to_visit |= set([u for u in sm if same_domain(u)])
    while to_visit and len(seen) < max_pages:
        url = to_visit.pop()
        if url in seen: continue
        seen.add(url)

        links, html = get_links(url)
        if html is None: continue

        soup = BeautifulSoup(html, "html.parser")
        title = " ".join(soup.title.text.split()) if soup.title and soup.title.text else url
        text = clean_text(html)
        if not text or len(text) < 20:   # lower threshold to catch short pages
            continue

        pages.append({
            "id": hashlib.md5(url.encode("utf-8")).hexdigest()[:12],
            "url": url,
            "title": title,
            "section": "",
            "content": text[:200000],
            "published_at": "",
            "updated_at": "",
            "tags": "",
            "source": "website",
        })
        for L in links:
            if L not in seen and same_domain(L) and L.startswith(BASE):
                to_visit.add(L)
        time.sleep(0.3)
    return pages

if __name__ == "__main__":
    pages = crawl(max_pages=800)
    df = pd.DataFrame(pages, columns=[
        "id","url","title","section","content",
        "published_at","updated_at","tags","source"
    ])
    os.makedirs("data", exist_ok=True)
    final_path = os.path.join("data","uploaddigital_corpus.csv")
    tmp_path   = final_path + ".tmp"
    df.to_csv(tmp_path, index=False, encoding="utf-8")
    try:
        if os.path.exists(final_path): os.remove(final_path)
    except PermissionError:
        print("⚠️  Close the CSV (Excel) and run again."); raise
    os.replace(tmp_path, final_path)
    print(f"Saved {len(df)} pages to {final_path}")
