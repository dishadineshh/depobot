# build_index.py — merge website + gdocs, build TF-IDF + KNN
import os, pandas as pd, joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

CSV_WEB   = os.getenv("UD_CSV_PATH", "data/uploaddigital_corpus.csv")
CSV_GDOCS = "data/google_docs_corpus.csv"

OUT_DIR = "index_store"
os.makedirs(OUT_DIR, exist_ok=True)

def load_df(path, default_source):
    if not os.path.exists(path):
        return pd.DataFrame(columns=["id","url","title","section","content","published_at","updated_at","tags","source"])
    df = pd.read_csv(path)
    # normalize columns
    for col in ["id","url","title","section","content","published_at","updated_at","tags","source"]:
        if col not in df.columns: df[col] = ""
    if "source" not in df.columns or df["source"].eq("").all():
        df["source"] = default_source
    return df.fillna("")

web   = load_df(CSV_WEB,   "website")
gdocs = load_df(CSV_GDOCS, "gdoc")

records = pd.concat([web, gdocs], ignore_index=True)
records = records[records["content"].astype(str).str.len() > 0].copy()

vectorizer = TfidfVectorizer(stop_words="english", max_features=120000)
X = vectorizer.fit_transform(records["content"].astype(str).tolist())

knn = NearestNeighbors(n_neighbors=10, metric="cosine")
knn.fit(X)

joblib.dump(vectorizer, os.path.join(OUT_DIR, "tfidf_vectorizer.joblib"))
joblib.dump(knn,       os.path.join(OUT_DIR, "knn.joblib"))
records.to_pickle(     os.path.join(OUT_DIR, "records.pkl"))

print("Index built in index_store/ (TF-IDF + KNN).")
print(f"Total rows indexed: {len(records)} (website: {len(web)}, gdocs: {len(gdocs)})")
