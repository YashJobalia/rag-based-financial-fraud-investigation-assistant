"""Versioned ingestion of short, atomic fictional passages; no model calls required."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

PUBLISHED = datetime(2026, 6, 15, 10, tzinfo=timezone.utc)
INGESTED = datetime(2026, 7, 5, 10, tzinfo=timezone.utc)


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^(PROC|HIST)-[0-9]{3}$")
    title: str = Field(min_length=1, max_length=200)
    kind: Literal["procedure", "historical_report"]
    section: str = Field(min_length=1, max_length=200)
    passage: str = Field(min_length=20, max_length=4000)
    access_group: Literal["demo", "restricted"] = "demo"
    version: int = Field(default=1, ge=1)
    published_at: AwareDatetime = PUBLISHED
    ingested_at: AwareDatetime = INGESTED

    @model_validator(mode="after")
    def valid_dates(self):
        if self.ingested_at < self.published_at:
            raise ValueError("Ingestion cannot precede publication")
        if self.version > 1 and not {"published_at", "ingested_at"} <= self.model_fields_set:
            raise ValueError("New versions require explicit publication and ingestion timestamps")
        return self


def ingest_documents(conn, path: Path | None = None):
    path = path or Path(__file__).with_name("corpus") / "documents.json"
    docs = [
        SourceDocument.model_validate(row) for row in json.loads(path.read_text(encoding="utf-8"))
    ]
    seen = set()
    inserted = 0
    for doc in docs:
        eid = f"{doc.id}:v{doc.version}:1"
        if eid in seen:
            raise ValueError("Duplicate document version in ingestion input")
        seen.add(eid)
        passage = "FICTIONAL DEMONSTRATION DOCUMENT. " + doc.passage
        digest = hashlib.sha256(passage.encode()).hexdigest()
        existing = conn.execute(
            "SELECT content_hash,title,section,kind,access_group,published_at,ingested_at FROM chunks WHERE tenant_id='demo' AND id=%s",
            (eid,),
        ).fetchone()
        if existing:
            if tuple(existing) != (
                digest,
                doc.title,
                doc.section,
                doc.kind,
                doc.access_group,
                doc.published_at,
                doc.ingested_at,
            ):
                raise ValueError(
                    "A document version changed. Create an explicit new version; never overwrite indexed evidence."
                )
            continue
        conn.execute(
            """INSERT INTO chunks(tenant_id,id,document_id,title,kind,version,section,passage,
          content_hash,published_at,ingested_at,access_group,source_uri)
          VALUES('demo',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                eid,
                doc.id,
                doc.title,
                doc.kind,
                str(doc.version),
                doc.section,
                passage,
                digest,
                doc.published_at,
                doc.ingested_at,
                doc.access_group,
                "synthetic://corpus/" + doc.id,
            ),
        )
        inserted += 1
    return inserted
