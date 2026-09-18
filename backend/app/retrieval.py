import hashlib
import json
from time import perf_counter
from uuid import uuid4

from fastapi import HTTPException
from psycopg.types.json import Jsonb

from .evidence import visible_chunks

DEFAULT_QUERY = '"new device" OR "new recipient" OR "replacement phone" OR "customer contact" OR "password reset"'


def retrieve(conn, case, user, query: str, mode="keyword", k=5):
    started = perf_counter()
    if mode != "keyword":
        raise HTTPException(
            409,
            "Vector and hybrid retrieval are not enabled in milestone 1. Keyword is the measured baseline.",
        )
    # The authorization and temporal predicate is inside the candidate query, not a post-filter.
    rows = conn.execute(
        """SELECT id,document_id,title,kind,version,section,passage,content_hash,
        published_at,ingested_at,source_uri,synthetic,
        ts_rank_cd(search_vector,websearch_to_tsquery('english',%s)) AS score
        FROM chunks c WHERE access_group='demo' AND published_at<=%s AND ingested_at<=%s
        AND NOT EXISTS (SELECT 1 FROM chunks newer WHERE newer.document_id=c.document_id
          AND newer.version::integer>c.version::integer
          AND newer.published_at<=%s AND newer.ingested_at<=%s)
        AND search_vector @@ websearch_to_tsquery('english',%s)
        ORDER BY score DESC,id LIMIT %s""",
        (
            query,
            case["cutoff_at"],
            case["cutoff_at"],
            case["cutoff_at"],
            case["cutoff_at"],
            query,
            k,
        ),
    ).fetchall()
    corpus = visible_chunks(conn, case, user)
    digest = hashlib.sha256(
        json.dumps(
            [
                (
                    c["id"],
                    c["content_hash"],
                    c["title"],
                    str(c["published_at"]),
                    str(c["ingested_at"]),
                )
                for c in corpus
            ]
        ).encode()
    ).hexdigest()
    duration = round((perf_counter() - started) * 1000, 2)
    run_id = str(uuid4())
    conn.execute(
        "INSERT INTO retrieval_runs(id,tenant_id,actor,case_id,mode,query,duration_ms,result_ids,corpus_hash) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            run_id,
            user.tenant,
            user.actor,
            case["id"],
            mode,
            query,
            duration,
            Jsonb([r["id"] for r in rows]),
            digest,
        ),
    )
    return {
        "run_id": run_id,
        "mode": mode,
        "query": query,
        "results": rows,
        "duration_ms": duration,
        "corpus_hash": digest,
        "explanation": "PostgreSQL full-text search over permitted, versioned fictional passages. Amounts and timelines come from separate SQL queries.",
        "abstained": not bool(rows),
    }
