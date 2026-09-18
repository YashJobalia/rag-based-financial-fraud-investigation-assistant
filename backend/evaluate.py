"""Reproducible retrieval evaluation. Answers stay outside the application corpus."""

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from app.auth import Principal
from app.db import connection
from app.evidence import case_access
from app.retrieval import retrieve


def evaluate(split="dev", k=5):
    root = Path(__file__).resolve().parents[1]
    dataset = root / "evaluation" / f"{split}.json"
    questions = json.loads(dataset.read_text())
    rows = []
    user = Principal("demo", "public-demo", "viewer")
    for question in questions:
        with connection(user.tenant, user.actor) as conn:
            case = case_access(conn, "CASE-001", user)
            result = retrieve(conn, case, user, question["query"], "keyword", k)
        ids = [r["id"] for r in result["results"]]
        expected = set(question["expected"])
        recall = len(expected & set(ids)) / len(expected) if expected else None
        ranks = [i + 1 for i, eid in enumerate(ids) if eid in expected]
        dcg = sum(1 / math.log2(i + 2) for i, eid in enumerate(ids) if eid in expected)
        ideal = sum(1 / math.log2(i + 2) for i in range(min(len(expected), k)))
        rows.append(
            {
                "id": question["id"],
                "retrieved": ids,
                "recall_at_k": recall,
                "reciprocal_rank": 1 / min(ranks) if ranks else 0,
                "ndcg_at_k": dcg / ideal if ideal else None,
                "duration_ms": result["duration_ms"],
                "empty_on_unanswerable": not ids if not question["answerable"] else None,
                "corpus_hash": result["corpus_hash"],
            }
        )
    answerable = [r for r in rows if r["recall_at_k"] is not None]
    unanswerable = [r for r in rows if r["empty_on_unanswerable"] is not None]
    durations = sorted(r["duration_ms"] for r in rows)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "split": split,
        "mode": "keyword",
        "k": k,
        "question_count": len(rows),
        "dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
        "corpus_hash": rows[0]["corpus_hash"],
        "metrics": {
            "recall_at_k": mean(r["recall_at_k"] for r in answerable),
            "mrr": mean(r["reciprocal_rank"] for r in answerable),
            "ndcg_at_k": mean(r["ndcg_at_k"] for r in answerable),
            "empty_retrieval_on_unanswerable": mean(
                r["empty_on_unanswerable"] for r in unanswerable
            ),
            "latency_mean_ms": mean(durations),
            "latency_p95_ms": durations[math.ceil(0.95 * len(durations)) - 1],
            "model_tokens": 0,
            "model_cost_usd": 0,
        },
        "not_measured": [
            "live citation semantic correctness",
            "live citation completeness",
            "live groundedness",
            "live appropriate abstention",
            "vector retrieval",
            "hybrid retrieval",
        ],
        "limitations": [
            "Small synthetic corpus; no evidence of real-world accuracy.",
            "Held-out questions test document retrieval, not unseen case-family generalization.",
            "Empty retrieval is not equivalent to appropriate synthesis abstention.",
            "Latency excludes HTTP, rendering, database connection setup, and LLM synthesis.",
        ],
        "questions": rows,
    }
    output = root / "evaluation" / "results" / f"{split}-keyword.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(output), "metrics": report["metrics"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "heldout"], default="dev")
    parser.add_argument("--k", type=int, choices=range(1, 11), default=5)
    args = parser.parse_args()
    evaluate(args.split, args.k)
