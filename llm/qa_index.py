from __future__ import annotations
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from typing import List, Dict

INDEX_PATH = Path(__file__).with_name("qa.index")
META_PATH = Path(__file__).with_name("qa_meta.json")
EMB_MODEL = "all-MiniLM-L6-v2"

class QAIndex:
    def __init__(self, index: faiss.Index, meta: List[Dict], model: SentenceTransformer):
        self.index = index
        self.meta = meta
        self.model = model

    @classmethod
    def load(cls):
        idx = faiss.read_index(str(INDEX_PATH))
        with META_PATH.open("r", encoding="utf-8") as f:
            meta = json.load(f)
        model = SentenceTransformer(EMB_MODEL)
        return cls(idx, meta, model)

    def query(self, text: str, k: int = 3):
        v = self.model.encode([text], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        scores, ids = self.index.search(v, k)
        out = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0 or idx >= len(self.meta):
                continue
            m = self.meta[idx]
            out.append({"score": float(score), **m})
        return out