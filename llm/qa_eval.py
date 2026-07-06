from __future__ import annotations
import json
import math
from pathlib import Path
from statistics import mean
from typing import List, Dict, Tuple

from qa_index import QAIndex, META_PATH, INDEX_PATH  # uses your existing QAIndex

# Utilities
def softmax(xs: List[float]) -> List[float]:
    if not xs:
        return []
    m = max(xs)
    ex = [math.exp(x - m) for x in xs]
    s = sum(ex)
    return [e / s for e in ex]

def normalize_answer(s: str) -> str:
    return (s or "").strip().lower()

def is_correct(pred_answer: str, gold_answer: str) -> bool:
    pa = normalize_answer(pred_answer)
    ga = normalize_answer(gold_answer)
    if not ga:
        return False
    if pa == ga:
        return True
    # fallback: containment match
    if ga in pa or pa in ga:
        return True
    return False

def load_gold(meta_path: Path) -> List[Dict]:
    with meta_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def evaluate(
    idx: QAIndex,
    gold_rows: List[Dict],
    k: int = 10,
    bins: int = 10,
) -> Dict:
    topk_counts = {1: 0, 3: 0, 5: 0, 10: 0}
    mrr_total = 0.0
    map_total = 0.0
    confidences: List[float] = []
    per_query: List[Dict] = []

    for r in gold_rows:
        q = r.get("question", "")
        gold = r.get("answer", "")
        results = idx.query(q, k=k)
        scores = [res.get("score", 0.0) for res in results]
        preds = [res.get("answer", "") for res in results]

        # top-k accuracy
        for cut in (1, 3, 5, 10):
            found = any(is_correct(p, gold) for p in preds[:cut])
            if found:
                topk_counts[cut] += 1

        # MRR and AP
        rr = 0.0
        ap = 0.0
        num_rel = 0
        for i, p in enumerate(preds, start=1):
            rel = 1 if is_correct(p, gold) else 0
            if rel and rr == 0.0:
                rr = 1.0 / i
            if rel:
                num_rel += 1
                ap += num_rel / i  # since only binary relevance, this yields precision accumulation
        if num_rel > 0:
            ap = ap / num_rel
        else:
            ap = 0.0

        mrr_total += rr
        map_total += ap

        # confidence: normalize top-k scores to a distribution; pick top-1 prob as confidence
        probs = softmax(scores)
        conf = float(probs[0]) if probs else 0.0
        confidences.append(conf)

        per_query.append(
            {
                "question": q,
                "gold": gold,
                "top_preds": preds[:k],
                "scores": scores,
                "probs": probs,
                "top1_confidence": conf,
                "mrr_rr": rr,
                "ap": ap,
            }
        )

    n = len(gold_rows)
    topk_acc = {cut: topk_counts[cut] / n for cut in topk_counts}
    mrr = mrr_total / n
    map_v = map_total / n
    mean_conf = mean(confidences) if confidences else 0.0

    # calibration (bins)
    calib_bins = []
    if confidences:
        bin_counts = [0] * bins
        bin_correct = [0] * bins
        for qd in per_query:
            conf = qd["top1_confidence"]
            pred = qd["top_preds"][0] if qd["top_preds"] else ""
            correct_flag = 1 if is_correct(pred, qd["gold"]) else 0
            bin_index = min(bins - 1, int(conf * bins))
            bin_counts[bin_index] += 1
            bin_correct[bin_index] += correct_flag

        for i in range(bins):
            cnt = bin_counts[i]
            corr = bin_correct[i]
            avg_conf = ((i + 0.5) / bins) if cnt == 0 else None
            acc = (corr / cnt) if cnt else None
            calib_bins.append({"bin": i, "count": cnt, "accuracy": acc, "avg_bucket_conf": avg_conf})

    report = {
        "n_queries": n,
        "topk_accuracy": topk_acc,
        "mrr": mrr,
        "map": map_v,
        "mean_top1_confidence": mean_conf,
        "calibration_bins": calib_bins,
        "per_query": per_query,
    }
    return report

def print_report(rep: Dict, topk_print: Tuple[int, ...] = (1, 3, 5, 10)) -> None:
    print("\nQA Index Evaluation Report\n")
    print(f"Queries: {rep['n_queries']}")
    for cut in topk_print:
        v = rep["topk_accuracy"].get(cut, 0.0)
        print(f"Top-{cut} Accuracy: {v*100:.2f}%")
    print(f"MRR: {rep['mrr']:.4f}")
    print(f"MAP: {rep['map']:.4f}")
    print(f"Mean top-1 confidence: {rep['mean_top1_confidence']:.3f}")

    print("\nCalibration bins (bin index, count, accuracy if available):")
    for b in rep["calibration_bins"]:
        acc = f"{b['accuracy']*100:.1f}%" if b["accuracy"] is not None else "N/A"
        print(f"  bin={b['bin']} count={b['count']} acc={acc}")

def save_report(rep: Dict, out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)

def main():
    print("Loading index...")
    idx = QAIndex.load()
    gold = load_gold(META_PATH)
    print(f"Loaded {len(gold)} gold rows")

    report = evaluate(idx, gold, k=10, bins=10)
    print_report(report)
    save_report(report, Path(__file__).with_name("qa_eval_report.json"))
    print("Saved report to qa_eval_report.json")

if __name__ == "__main__":
    main()