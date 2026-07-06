from __future__ import annotations
import csv
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

CSV_PATH = Path(__file__).with_name("train.csv")
INDEX_PATH = Path(__file__).with_name("qa.index")
META_PATH = Path(__file__).with_name("qa_meta.json")
EMB_MODEL = "all-MiniLM-L6-v2"

def load_rows(csv_path: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            qid = (r.get("question_id") or "").strip()
            q = (r.get("question") or "").strip()
            a = (r.get("answer") or "").strip()
            if not qid or not q:
                continue
            rows.append({"id": qid, "question": q, "answer": a})
    return rows

def build():
    rows = load_rows(CSV_PATH)
    if not rows:
        raise SystemExit("No rows found in CSV")

    model = SentenceTransformer(EMB_MODEL)
    texts = [r["question"].strip() for r in rows]
    embs = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)
    d = embs.shape[1]

    index = faiss.IndexFlatIP(d)  # cosine via inner-product on normalized vectors
    index.add(embs.astype("float32"))

    faiss.write_index(index, str(INDEX_PATH))
    with META_PATH.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"Built index: {INDEX_PATH} meta: {META_PATH} items: {len(rows)}")

if __name__ == "__main__":
    build()