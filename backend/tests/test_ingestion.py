import json
from pathlib import Path

import psycopg
import pytest

from app.auth import Principal
from app.config import settings
from app.limits import reserve_request
from fastapi import HTTPException
from ingest import ingest_documents


def test_idempotent_ingestion_and_immutable_version(test_database, tmp_path):
    with psycopg.connect(settings().admin_database_url.get_secret_value()) as conn:
        assert ingest_documents(conn) == 0
        source = json.loads(Path("corpus/documents.json").read_text())
        source[0]["passage"] += " Changed without a version bump."
        bad = tmp_path / "changed.json"
        bad.write_text(json.dumps(source))
        with pytest.raises(ValueError, match="version changed"):
            ingest_documents(conn, bad)


def test_future_document_version_not_used(client):
    admin_url = settings().admin_database_url.get_secret_value()
    with psycopg.connect(admin_url) as conn:
        conn.execute("""INSERT INTO chunks SELECT tenant_id,'PROC-002:v99:1',document_id,title,kind,
          '99',section,passage,content_hash,'2027-01-01','2027-01-01',access_group,source_uri,synthetic
          FROM chunks WHERE id='PROC-002:v1:1'""")
    try:
        rows = client.post(
            "/api/cases/CASE-001/retrieve", json={"query": "replacement phone"}
        ).json()["results"]
        assert "PROC-002:v1:1" in [r["id"] for r in rows]
        assert "PROC-002:v99:1" not in [r["id"] for r in rows]
        assert client.get("/api/cases/CASE-001/evidence/PROC-002:v99:1").status_code == 404
    finally:
        with psycopg.connect(admin_url) as conn:
            conn.execute("DELETE FROM chunks WHERE id='PROC-002:v99:1'")


def test_public_request_budget(test_database):
    user = Principal("demo", "test-budget", "viewer")
    with psycopg.connect(settings().admin_database_url.get_secret_value()) as conn:
        conn.execute("DELETE FROM request_budgets WHERE actor='test-budget'")
        conn.execute(
            "INSERT INTO request_budgets VALUES('demo','test-budget',date_trunc('minute',now()),60)"
        )
    with pytest.raises(HTTPException) as exc:
        reserve_request(user)
    assert exc.value.status_code == 429
