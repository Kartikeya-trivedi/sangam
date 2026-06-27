"""Evaluate the matching engine against the labelled test pairs — the killer demo metric.

Two views:
  1. RETRIEVAL — for each positive "lost" record, rank candidates across the whole live registry
     (its true "found" partner + the 300 seeded found records + other test founds as distractors).
     Reports recall@1, recall@5, and mean reciprocal rank (MRR). This is the real-world question:
     "given a family's report, does the system surface the right found-person near the top?"
  2. CLASSIFICATION — score every labelled (lost, found) pair directly and threshold it. Reports
     precision / recall / F1 at the high-confidence threshold, plus a sweep to pick the threshold.

Run from backend/:
  ./.venv/bin/python ../scripts/seed_dataset.py
  ./.venv/bin/python ../scripts/generate_test_pairs.py
  ./.venv/bin/python ../scripts/eval_matcher.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

from config import settings  # noqa: E402
from db import init_db, repo  # noqa: E402
from services import matching  # noqa: E402


def _retrieval_metrics(pair_ids: list[str]) -> dict:
    rr, top1, top5 = [], 0, 0
    for pair in pair_ids:
        people = repo.persons_by_test_pair(pair)
        lost = next((p for p in people if p.role == "lost"), None)
        partner = next((p for p in people if p.role == "found"), None)
        if not lost or not partner:
            continue
        ranked = matching.rank_candidates(lost, k=20, min_score=0.0)
        ids = [m.candidate_id for m in ranked]
        rank = ids.index(partner.id) + 1 if partner.id in ids else None
        rr.append(1.0 / rank if rank else 0.0)
        top1 += 1 if rank == 1 else 0
        top5 += 1 if (rank and rank <= 5) else 0
    n = len(rr) or 1
    return {"n": len(rr), "recall@1": top1 / n, "recall@5": top5 / n, "mrr": sum(rr) / n}


def _labelled_scores() -> list[tuple[int, float]]:
    """(label, score) for every labelled pair, scoring lost-vs-found directly."""
    out = []
    for pair, should in repo.test_pairs():
        people = repo.persons_by_test_pair(pair)
        lost = next((p for p in people if p.role == "lost"), None)
        found = next((p for p in people if p.role == "found"), None)
        if lost and found:
            out.append((should, matching.compute_match_score(lost, found).final_score))
    return out


def _prf(scores: list[tuple[int, float]], threshold: float) -> dict:
    tp = sum(1 for y, s in scores if y == 1 and s >= threshold)
    fp = sum(1 for y, s in scores if y == 0 and s >= threshold)
    fn = sum(1 for y, s in scores if y == 1 and s < threshold)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"threshold": threshold, "precision": precision, "recall": recall, "f1": f1,
            "tp": tp, "fp": fp, "fn": fn}


def main() -> None:
    init_db()
    pairs = repo.test_pairs()
    if not pairs:
        raise SystemExit("No test pairs found. Run generate_test_pairs.py first.")
    pos_ids = [p for p, s in pairs if s == 1]
    print(f"Evaluating against {len(pairs)} labelled pairs "
          f"({len(pos_ids)} positive, {len(pairs) - len(pos_ids)} negative).\n")

    print("=== RETRIEVAL (positive 'lost' query vs full live registry) ===")
    rm = _retrieval_metrics(pos_ids)
    print(f"  queries={rm['n']}  recall@1={rm['recall@1']:.1%}  recall@5={rm['recall@5']:.1%}  "
          f"MRR={rm['mrr']:.3f}")

    print("\n=== CLASSIFICATION (labelled lost-vs-found pairs) ===")
    scores = _labelled_scores()
    at = _prf(scores, settings.high_confidence_threshold)
    print(f"  at high-confidence threshold {at['threshold']:.2f}: "
          f"precision={at['precision']:.1%} recall={at['recall']:.1%} F1={at['f1']:.3f} "
          f"(tp={at['tp']} fp={at['fp']} fn={at['fn']})")
    print("  threshold sweep:")
    best = max((_prf(scores, t / 100) for t in range(30, 96, 5)), key=lambda d: d["f1"])
    for t in range(30, 96, 5):
        d = _prf(scores, t / 100)
        star = "  <- best F1" if abs(d["threshold"] - best["threshold"]) < 1e-9 else ""
        print(f"    T={d['threshold']:.2f}  P={d['precision']:.2f}  R={d['recall']:.2f}  "
              f"F1={d['f1']:.3f}{star}")
    print(f"\n  Recommended threshold (max F1): {best['threshold']:.2f} "
          f"(P={best['precision']:.1%} R={best['recall']:.1%} F1={best['f1']:.3f})")


if __name__ == "__main__":
    main()
