import io, os

path = os.path.join("data", "docs_list.csv")
with open(path, "rb") as f:
    raw = f.read()

# Strip UTF-8 BOM if present
if raw.startswith(b'\xef\xbb\xbf'):
    raw = raw[3:]

text = raw.decode("utf-8", errors="replace").splitlines()
# Ensure header is correct
if text:
    header = text[0].strip()
    if header.lower().startswith("﻿doc_id") or header.lower().startswith("\\ufeffdoc_id"):
        text[0] = "doc_id,title,url,tags"
    elif header.lower() != "doc_id,title,url,tags":
        text[0] = "doc_id,title,url,tags"

fixed = "\n".join(text)
with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(fixed)

print("docs_list.csv cleaned and saved as UTF-8 (no BOM).")
