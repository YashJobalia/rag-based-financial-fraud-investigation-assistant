"""Deterministic synthetic records. No hidden fraud labels or evaluation answers are loaded."""

import random
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Jsonb

from app.config import settings
from ingest import ingest_documents

ANCHOR = datetime(2026, 8, 14, 10, tzinfo=timezone.utc)


def seed():
    rng = random.Random(1729)
    with psycopg.connect(settings().admin_database_url.get_secret_value()) as conn:
        if conn.execute("SELECT 1 FROM cases WHERE tenant_id='demo' AND id='CASE-001'").fetchone():
            print("Seed already present; immutable evidence left unchanged.")
            return
        for actor, role in [("public-demo", "viewer"), ("analyst-local", "analyst")]:
            conn.execute("INSERT INTO memberships VALUES('demo',%s,%s)", (actor, role))
        for i in range(100):
            account = f"ACC-{i + 1:03}"
            conn.execute(
                "INSERT INTO accounts VALUES('demo',%s,%s,%s)",
                (account, f"Synthetic account {i + 1:03}", ANCHOR - timedelta(days=500 + i)),
            )
            for j in range(50):
                at = ANCHOR - timedelta(days=1 + j % 28, hours=j % 10)
                conn.execute(
                    "INSERT INTO transactions VALUES('demo',%s,%s,%s,%s,'USD','completed',%s,%s)",
                    (
                        f"TX-B{i:03}-{j:03}",
                        account,
                        f"REC-REG-{i:03}",
                        rng.randint(800, 24000),
                        at,
                        at,
                    ),
                )
            for j in range(10):
                at = ANCHOR - timedelta(days=1 + j, hours=2)
                conn.execute(
                    "INSERT INTO events VALUES('demo',%s,%s,'login',%s,%s,%s,%s,%s,NULL,'authentication_log')",
                    (
                        f"EV-B{i:03}-{j:03}",
                        account,
                        at,
                        at,
                        "Known device sign-in",
                        "Successful sign-in on the established device.",
                        f"DEV-KNOWN-{i:03}",
                    ),
                )
        conn.execute(
            "INSERT INTO cases VALUES('demo','CASE-001','ACC-001','New device, new recipient',%s,%s,'open')",
            (ANCHOR - timedelta(minutes=25), ANCHOR),
        )
        conn.execute(
            "INSERT INTO cases VALUES('demo','CASE-PRIVATE','ACC-002','Restricted test case',%s,%s,'open')",
            (ANCHOR, ANCHOR),
        )
        for actor in ["public-demo", "analyst-local"]:
            conn.execute("INSERT INTO case_assignments VALUES('demo','CASE-001',%s)", (actor,))
        events = [
            (
                "EV-001",
                "support_notice",
                "08:40",
                "Replacement phone reported",
                "An unverified support message reports a replacement phone. No independently verified customer contact is included.",
                None,
                None,
                "support_message",
            ),
            (
                "EV-002",
                "new_device_login",
                "09:12",
                "First sign-in on DEV-NEW-001",
                "Successful sign-in from DEV-NEW-001, first observed for this account. Session S-901.",
                "DEV-NEW-001",
                None,
                "authentication_log",
            ),
            (
                "EV-003",
                "password_reset",
                "09:16",
                "Password reset completed",
                "The reset workflow completed in session S-901. Reset delivery and MFA challenge records are not included.",
                "DEV-NEW-001",
                None,
                "authentication_log",
            ),
            (
                "EV-004",
                "recipient_added",
                "09:20",
                "Recipient REC-NEW-001 added",
                "REC-NEW-001 was added in session S-901. No prior payment to this recipient exists in the available account history.",
                "DEV-NEW-001",
                "REC-NEW-001",
                "recipient_registry",
            ),
            (
                "EV-005",
                "login",
                "09:45",
                "Established device signs in",
                "Successful sign-in from established device DEV-KNOWN-000. A sign-in does not confirm authorization of earlier transfers.",
                "DEV-KNOWN-000",
                None,
                "authentication_log",
            ),
        ]
        for eid, kind, clock, title, description, device, recipient, source in events:
            at = datetime.fromisoformat(f"2026-08-14T{clock}:00+00:00")
            conn.execute(
                "INSERT INTO events VALUES('demo',%s,'ACC-001',%s,%s,%s,%s,%s,%s,%s,%s)",
                (eid, kind, at, at, title, description, device, recipient, source),
            )
        for tid, clock, amount in [("TX-001", "09:28", 480000), ("TX-002", "09:35", 320000)]:
            at = datetime.fromisoformat(f"2026-08-14T{clock}:00+00:00")
            conn.execute(
                "INSERT INTO transactions VALUES('demo',%s,'ACC-001','REC-NEW-001',%s,'USD','completed',%s,%s)",
                (tid, amount, at, at),
            )
        # Detection is an explicit SQL rule, not a scenario label or LLM decision.
        triggered = conn.execute("""
          SELECT t.id FROM transactions t JOIN events r ON r.tenant_id=t.tenant_id
          AND r.account_id=t.account_id AND r.recipient_id=t.recipient_id AND r.kind='recipient_added'
          JOIN events l ON l.tenant_id=t.tenant_id AND l.account_id=t.account_id AND l.kind='new_device_login'
          WHERE t.tenant_id='demo' AND t.account_id='ACC-001' AND t.currency='USD'
          AND t.status='completed' AND t.amount_minor>=300000
          AND t.occurred_at BETWEEN r.occurred_at AND r.occurred_at+interval '30 minutes'
          AND r.occurred_at BETWEEN l.occurred_at AND l.occurred_at+interval '30 minutes'
          ORDER BY t.occurred_at
        """).fetchall()
        if triggered:
            conn.execute(
                "INSERT INTO alerts VALUES('demo','ALERT-001','CASE-001','NEW_DEVICE_NEW_PAYEE','1',%s,%s,%s)",
                (
                    ANCHOR - timedelta(minutes=25),
                    "New device login, followed within 30 minutes by a new recipient, then completed USD transfers of at least $3,000 within 30 minutes of recipient creation.",
                    Jsonb(["EV-002", "EV-004"] + [r[0] for r in triggered]),
                ),
            )
        ingest_documents(conn)
    print(
        "Seeded 100 accounts, 5,002 transactions, 1,005 events, 1 visible case, 1 isolation case, and 16 fictional documents."
    )


if __name__ == "__main__":
    seed()
