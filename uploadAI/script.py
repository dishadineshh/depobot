# script.py — RAG server with Google CSE fallback and neat citations
import os, joblib, pandas as pd, requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from bs4 import BeautifulSoup

# ----- Init -----
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")
client = OpenAI(api_key=OPENAI_API_KEY)

GOOGLE_CSE_KEY = os.getenv("GOOGLE_CSE_KEY", "")
GOOGLE_CSE_CX  = os.getenv("GOOGLE_CSE_CX", "")

app = Flask(__name__)
CORS(app)

HEADERS = {"User-Agent": "UploadDigitalBot/1.0 (+contact@uploaddigital.co)"}
MAX_CONTEXT = 9000
TOP_K = 8

# ----- Load index -----
VEC_PATH  = "index_store/tfidf_vectorizer.joblib"
KNN_PATH  = "index_store/knn.joblib"
RECS_PATH = "index_store/records.pkl"
if not (os.path.exists(VEC_PATH) and os.path.exists(KNN_PATH) and os.path.exists(RECS_PATH)):
    raise RuntimeError("Index not found. Run: python build_index.py")

vectorizer: TfidfVectorizer = joblib.load(VEC_PATH)
knn: NearestNeighbors       = joblib.load(KNN_PATH)
records: pd.DataFrame       = pd.read_pickle(RECS_PATH).fillna("")

# ----- Force rules (IDs optional; we can also force by source/title) -----
FORCE_IDS = {
    # if you seeded specific rows by ID, put them here:
    # "services":   "services123",
    # "industries": "industries123",
    # "email":      "emailtips123",
}

def force_context(question_lower: str):
    parts = []
    # ID-based rules (only if you've created those rows)
    for key, rid in FORCE_IDS.items():
        if key in question_lower:
            row = records[records["id"] == rid]
            if not row.empty:
                parts.append(str(row.iloc[0]["content"]))

    # Topic-based force for Google Docs (Newsletters/Landing)
    if any(k in question_lower for k in ["newsletter", "gen z", "gen-z", "attention span", "jingle", "community", "landing"]):
        rows = records[(records["source"] == "gdoc") | (records["title"].str.contains("newsletter|landing", case=False, na=False))]
        if not rows.empty:
            parts.append(str(rows.iloc[0]["content"])[:2000])
    return parts

def retrieve(question: str, k: int = TOP_K):
    expanded = (
        f"{question} "
        " services service offerings what we do solutions capabilities packages pricing "
        " industries clients sectors verticals case studies portfolio work "
        " email marketing newsletter subject line deliverability open rate ctr automation segmentation a/b testing "
        " newsletter newsletters gen z gen-z attention span attention-span youth marketing "
        " vibe marketing community community-first case study tips how-to best practices jingles earworm nostalgia landing"
    )
    qvec = vectorizer.transform([expanded])
    pool = min(k * 3, len(records))
    distances, indices = knn.kneighbors(qvec, n_neighbors=pool)

    hits = []
    for dist, idx in zip(distances[0], indices[0]):
        row = records.iloc[idx]
        title = row["title"] if isinstance(row["title"], str) and row["title"].strip() else row["url"]
        url   = str(row["url"])
        text  = str(row["content"])

        base = float(1 - dist)
        t = f"{title} {url}".lower()
        boost = 0.0
        if "service" in t:      boost += 0.20
        if "services" in t:     boost += 0.30
        if "/services" in url:  boost += 0.35
        if "what we do" in t:   boost += 0.15
        if "solutions" in t:    boost += 0.10
        if "/contact" in url:   boost += 0.10
        if "/about" in url:     boost += 0.05
        if "newsletter" in t:   boost += 0.35
        if "gen z" in t or "gen-z" in t: boost += 0.30
        if "attention span" in t or "attention-span" in t: boost += 0.25
        if "tips" in t or "how to" in t or "best practices" in t: boost += 0.20
        if "jingle" in t or "jingles" in t or "earworm" in t: boost += 0.20
        if "community" in t or "community-first" in t: boost += 0.20
        if "case study" in t: boost += 0.15
        if "landing" in t: boost += 0.15

        hits.append({"url": url, "title": title, "text": text, "score": base + boost})

    hits.sort(key=lambda h: h["score"], reverse=True)
    seen, out = set(), []
    for h in hits:
        if h["url"] in seen: continue
        seen.add(h["url"]); out.append(h)
        if len(out) >= k: break
    return out

# ----- Google CSE fallback (site-limited) -----
def google_search(query: str, num: int = 5):
    if not GOOGLE_CSE_KEY or not GOOGLE_CSE_CX:
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_CSE_KEY,
        "cx":  GOOGLE_CSE_CX,
        "q":   f"site:uploaddigital.co {query}",
        "num": max(1, min(num, 10)),
        "safe":"off",
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []
    items = data.get("items", []) or []
    out = []
    for it in items:
        out.append({
            "title": it.get("title") or "",
            "url":   it.get("link") or "",
            "snippet": it.get("snippet") or ""
        })
    return out

def fetch_and_clean(url: str, max_chars: int = 2000) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception:
        return ""
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script","style","noscript"]): t.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:max_chars]

def build_context(chunks, max_chars=MAX_CONTEXT):
    parts, total = [], 0
    for h in chunks:
        piece = (h or "").strip()
        if not piece: continue
        if len(piece) > 1400: piece = piece[:1400]
        if total + len(piece) + 8 > max_chars: break
        parts.append(piece); total += len(piece) + 8
    return "\n\n---\n".join(parts)

@app.post("/chat")
def chat():
    data = request.get_json(force=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify({"error": "Question is required"}), 400
    qlower = q.lower()

    # 1) guaranteed inclusions (services/newsletters/landing/etc.)
    ctx_parts = force_context(qlower)

    # 2) local retrieval
    hits = retrieve(q, k=TOP_K)
    for h in hits:
        ctx_parts.append(h["text"])

    # 3) If local context weak → Google CSE fallback (site-limited)
    weak_local = (len(hits) < 3 or sum(len((h["text"] or "")) for h in hits) < 1200)
    web_hits = []
    if weak_local:
        web_hits = google_search(q, num=5)
        for wh in web_hits:
            page_txt = fetch_and_clean(wh["url"])
            if page_txt:
                ctx_parts.append(page_txt)

    # 4) Merge/cap
    merged, seenp = [], set()
    for p in ctx_parts:
        if p in seenp: continue
        seenp.add(p); merged.append(p)
    context = build_context(merged, MAX_CONTEXT)

    # 5) If still empty → return a clear site-limited message (no generic answers)
    if not context.strip():
        return jsonify({"answer": "I couldn’t find that in Upload Digital’s sources yet."})

    # 6) Prompt (clean paragraphs, bullets for lists)
    prompt = f"""Answer based ONLY on the CONTEXT below.
Write in clean short paragraphs. If you list items, use simple bullet points.

CONTEXT:
{context}

QUESTION: {q}

ANSWER:"""

    # 7) OpenAI call
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Upload Digital. Never invent external info; stick to the provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # 8) Citations (no 'URL not provided')
    citations = []
    for h in hits[:3]:
        if h.get("url"): citations.append({"title": h.get("title",""), "url": h.get("url","")})
    for wh in web_hits[:3]:
        if wh.get("url"): citations.append({"title": wh.get("title",""), "url": wh.get("url","")})

    return jsonify({"answer": answer, "citations": citations})

@app.get("/")
def health():
    return {"ok": True, "message": "UploadAI backend running."}

if __name__ == "__main__":
    # Disable reloader to avoid double init
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
