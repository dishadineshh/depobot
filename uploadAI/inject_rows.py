# inject_rows.py — upsert guaranteed rows into data/uploaddigital_corpus.csv
import os, pandas as pd
DATA = "data/uploaddigital_corpus.csv"
os.makedirs("data", exist_ok=True)

rows = [
    {"id": "services123", "url": "https://www.uploaddigital.co/services", "title": "Services",
     "section": "Overview", "content": "Upload Digital offers: Email marketing strategy and automation; Web development and optimization; AI content workflows; Content personalization; A/B testing and experimentation; Social media strategy and algorithm analysis.",
     "published_at": "", "updated_at": "", "tags": "services", "source": "website"},
    {"id": "industries123", "url": "https://www.uploaddigital.co/industries", "title": "Industries We Serve",
     "section": "Overview", "content": "Upload Digital works with e-commerce, hospitality, education, technology startups, professional services, and media/entertainment.",
     "published_at": "", "updated_at": "", "tags": "industries", "source": "website"},
    {"id": "emailtips123", "url": "https://www.uploaddigital.co/blog/email-marketing-tips", "title": "Email Marketing Tips",
     "section": "Guide", "content": "Tips: Clean opt-in lists; Segment audiences; Clear subject lines; A/B testing; Mobile-friendly; Personalization; Automation; Deliverability setup (SPF/DKIM/DMARC); Track CTR & conversions; Fresh, value-first content.",
     "published_at": "", "updated_at": "", "tags": "email,tips", "source": "website"}
]

if not os.path.exists(DATA):
    pd.DataFrame(rows).to_csv(DATA, index=False, encoding="utf-8")
    print(f"Created {DATA} with {len(rows)} row(s).")
else:
    df = pd.read_csv(DATA, dtype=str).fillna("")
    ids = set(df["id"])
    for r in rows:
        if r["id"] in ids:
            df.loc[df["id"] == r["id"], df.columns] = [r.get(c, "") for c in df.columns]
        else:
            df = pd.concat([df, pd.DataFrame([r])[df.columns]], ignore_index=True)
    df.to_csv(DATA, index=False, encoding="utf-8")
    print(f"Upserted {len(rows)} row(s) into {DATA}.")
