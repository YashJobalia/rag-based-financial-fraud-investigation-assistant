from datetime import timedelta

from fastapi import HTTPException

from .auth import Principal


def case_access(conn, case_id: str, user: Principal):
    row = conn.execute(
        """SELECT c.*, a.display_name FROM cases c
       JOIN accounts a ON a.tenant_id=c.tenant_id AND a.id=c.account_id
       JOIN case_assignments ca ON ca.tenant_id=c.tenant_id AND ca.case_id=c.id
       WHERE c.id=%s AND ca.actor=%s""",
        (case_id, user.actor),
    ).fetchone()
    if row is None:
        raise HTTPException(404, "Case not found")
    return row


def visible_chunks(conn, case, user):
    # Fictional restricted material is excluded for every MVP principal. Future grants must
    # explicitly enable access; an analyst role alone does not grant every document.
    return conn.execute(
        """SELECT id,document_id,title,kind,version,section,passage,
        content_hash,published_at,ingested_at,source_uri,synthetic FROM chunks
        WHERE access_group='demo' AND published_at<=%s AND ingested_at<=%s ORDER BY id""",
        (case["cutoff_at"], case["cutoff_at"]),
    ).fetchall()


def case_evidence(conn, case):
    cutoff = case["cutoff_at"]
    start = cutoff.replace(hour=0, minute=0, second=0, microsecond=0)
    params = (case["account_id"], start, cutoff, cutoff)
    events = conn.execute(
        """SELECT id,kind,occurred_at,recorded_at,title,description,
        device_id,recipient_id,source FROM events WHERE account_id=%s
        AND occurred_at>=%s AND occurred_at<=%s AND recorded_at<=%s ORDER BY occurred_at,id""",
        params,
    ).fetchall()
    txs = conn.execute(
        """SELECT id,recipient_id,amount_minor,currency,status,occurred_at,recorded_at
        FROM transactions WHERE account_id=%s AND occurred_at>=%s AND occurred_at<=%s
        AND recorded_at<=%s ORDER BY occurred_at,id""",
        params,
    ).fetchall()
    totals = conn.execute(
        """SELECT currency,sum(amount_minor)::bigint AS total_minor,
        count(*)::int AS count, array_agg(id ORDER BY occurred_at,id) AS source_ids
        FROM transactions WHERE account_id=%s AND occurred_at>=%s AND occurred_at<=%s
        AND recorded_at<=%s AND status='completed' GROUP BY currency ORDER BY currency""",
        params,
    ).fetchall()
    baseline = conn.execute(
        """SELECT currency,count(*)::int AS count,
        max(amount_minor)::bigint AS max_minor, sum(amount_minor)::bigint AS total_minor,
        array_agg(id ORDER BY occurred_at,id) AS source_ids FROM transactions
        WHERE account_id=%s AND occurred_at>=%s AND occurred_at<%s AND recorded_at<=%s
        AND status='completed' GROUP BY currency ORDER BY currency""",
        (case["account_id"], start - timedelta(days=30), start, cutoff),
    ).fetchall()
    evidence = []
    for event in events:
        evidence.append({**event, "evidence_type": "record", "version": "1", "synthetic": True})
    for tx in txs:
        evidence.append(
            {
                **tx,
                "title": f"{tx['currency']} {tx['amount_minor'] / 100:,.2f} transfer",
                "description": f"{tx['status'].capitalize()} transfer to {tx['recipient_id']}.",
                "kind": "transaction",
                "source": "transaction_ledger",
                "evidence_type": "record",
                "version": "1",
                "synthetic": True,
            }
        )
    for total in totals:
        evidence.append(
            {
                "id": f"CALC:{case['id']}:daily:{total['currency']}:v1",
                "title": "Completed transfer total",
                "kind": "calculation",
                "description": f"{total['count']} completed {total['currency']} transfers total {total['total_minor'] / 100:,.2f}.",
                "source": "sql:completed_transfers_v1",
                "evidence_type": "calculation",
                "version": "1",
                "synthetic": True,
                "occurred_at": cutoff,
                "parameters": {
                    "account": case["account_id"],
                    "start_inclusive": start,
                    "end_inclusive": cutoff,
                    "status": "completed",
                    "currency": total["currency"],
                },
                "source_ids": total["source_ids"],
                "result": total,
            }
        )
    for base in baseline:
        evidence.append(
            {
                "id": f"CALC:{case['id']}:baseline:{base['currency']}:v1",
                "title": "Previous 30 days",
                "kind": "calculation",
                "description": f"{base['count']} completed {base['currency']} transfers; largest {base['max_minor'] / 100:,.2f}.",
                "source": "sql:baseline_30d_v1",
                "evidence_type": "calculation",
                "version": "1",
                "synthetic": True,
                "occurred_at": start,
                "parameters": {
                    "account": case["account_id"],
                    "start_inclusive": start - timedelta(days=30),
                    "end_exclusive": start,
                    "status": "completed",
                    "currency": base["currency"],
                },
                "source_ids": base["source_ids"],
                "result": base,
            }
        )
    evidence.append(
        {
            "id": f"SCOPE:{case['id']}:v1",
            "title": "Available evidence and limitations",
            "kind": "scope",
            "source": "case_evidence_manifest_v1",
            "evidence_type": "scope",
            "version": "1",
            "synthetic": True,
            "occurred_at": cutoff,
            "description": "This snapshot includes account transaction records, login events, a support notice, a password-reset event, and recipient creation. It contains no independently verified customer confirmation, invoice, IP geolocation, reset delivery log, MFA challenge log, or recipient ownership verification. Absence from this snapshot does not prove the underlying event did not occur.",
        }
    )
    alerts = conn.execute(
        "SELECT * FROM alerts WHERE case_id=%s AND triggered_at<=%s ORDER BY id",
        (case["id"], cutoff),
    ).fetchall()
    for alert in alerts:
        evidence.append(
            {
                "id": alert["id"],
                "title": "Alert rule matched",
                "description": alert["description"],
                "kind": "alert",
                "evidence_type": "rule",
                "source": alert["rule_id"],
                "version": alert["rule_version"],
                "occurred_at": alert["triggered_at"],
                "source_ids": alert["evidence_ids"],
                "synthetic": True,
            }
        )
    timeline = sorted(
        [e for e in evidence if e["kind"] not in ("scope", "calculation")],
        key=lambda e: (e["occurred_at"], e["id"]),
    )
    return {
        "evidence": evidence,
        "timeline": timeline,
        "totals": totals,
        "baseline": baseline,
        "alerts": alerts,
    }


def resolve(conn, case, user, evidence_id):
    bundle = case_evidence(conn, case)
    for item in bundle["evidence"]:
        if item["id"] == evidence_id:
            return item
    for item in visible_chunks(conn, case, user):
        if item["id"] == evidence_id:
            return {
                **item,
                "description": item["passage"],
                "evidence_type": "passage",
                "source": item["source_uri"],
            }
    # A calculation may cite a historical ledger row outside today's timeline.
    row = conn.execute(
        """SELECT * FROM transactions WHERE id=%s AND account_id=%s
        AND occurred_at<=%s AND recorded_at<=%s""",
        (evidence_id, case["account_id"], case["cutoff_at"], case["cutoff_at"]),
    ).fetchone()
    if row:
        return {
            **row,
            "title": "Historical transaction",
            "evidence_type": "record",
            "synthetic": True,
            "description": f"{row['currency']} {row['amount_minor'] / 100:,.2f} {row['status']} transfer to {row['recipient_id']}.",
            "source": "transaction_ledger",
            "version": "1",
        }
    raise HTTPException(404, "Evidence not found")
