# fetch_gdocs.py
import os, csv, requests, pandas as pd

DOCS_LIST = os.path.join("data", "docs_list.csv")
OUT_CSV   = os.path.join("data", "google_docs_corpus.csv")
HEADERS   = {"User-Agent": "UploadDigitalBot/1.0 (+contact@uploaddigital.co)"}

def doc_export_txt(doc_id: str) -> str:
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def row_to_record(row: dict):
    # BOM-safe header handling:
    doc_id = (row.get("doc_id") or row.get("\ufeffdoc_id") or "").strip()
    title  = (row.get("title") or "Google Doc").strip()
    url    = (row.get("url") or f"https://docs.google.com/document/d/{doc_id}/edit").strip()
    tags   = (row.get("tags") or "").strip()
    if not doc_id:
        print(f"⚠️  Skipping row without doc_id: {row}")
        return None
    try:
        txt = doc_export_txt(doc_id)
    except Exception as e:
        print(f"⚠️  Could not fetch {doc_id}: {e}")
        return None

    return {
        "id": f"gdoc-{doc_id}",
        "url": url,
        "title": title,
        "section": "",
        "content": " ".join(txt.split()),
        "published_at": "",
        "updated_at": "",
        "tags": tags,
        "source": "gdoc"
    }

def main():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DOCS_LIST):
        print(f"⚠️  Missing {DOCS_LIST}. Create it first.")
        return

    out = []
    # utf-8-sig strips BOM automatically
    with open(DOCS_LIST, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec = row_to_record(row)
            if rec:
                out.append(rec)

    if not out:
        print("No Google Docs fetched. Check sharing (Anyone with link: Viewer) and docs_list.csv.")
        return

    df = pd.DataFrame(out, columns=[
        "id","url","title","section","content",
        "published_at","updated_at","tags","source"
    ])
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"Saved {len(df)} Google Doc(s) to {OUT_CSV}")

if __name__ == "__main__":
    main()
