"""Explicit administration commands. Never imported by the request path."""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

import jwt
import psycopg
from psycopg import sql

from app.config import settings


def migrate():
    config = settings()
    password = unquote(urlparse(config.database_url.get_secret_value()).password or "")
    if not password:
        raise SystemExit("Set DATABASE_URL with the dedicated ffia_app runtime credentials.")
    with psycopg.connect(config.admin_database_url.get_secret_value()) as conn:
        if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='ffia_app'").fetchone():
            conn.execute(
                sql.SQL("CREATE ROLE ffia_app LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(
                    sql.Literal(password)
                )
            )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations(version integer PRIMARY KEY, applied_at timestamptz DEFAULT now())"
        )
        versions = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
        for path in sorted(Path(__file__).parent.joinpath("migrations").glob("*.sql")):
            version = int(path.name.split("_")[0])
            if version not in versions:
                conn.execute(path.read_text(encoding="utf-8"))
                print(f"Applied migration {version}")


def token():
    config = settings()
    secret = config.auth_secret.get_secret_value()
    if len(secret) < 32:
        raise SystemExit("Configure AUTH_SECRET with at least 32 random characters.")
    now = datetime.now(timezone.utc)
    encoded = jwt.encode(
        {
            "sub": "analyst-local",
            "tenant": "demo",
            "iat": now,
            "exp": now + timedelta(hours=8),
            "iss": "fraud-investigation",
            "aud": "fraud-investigation",
        },
        secret,
        algorithm="HS256",
    )
    # Write rather than print authentication material into terminal logs.
    destination = Path(__file__).resolve().parents[1] / ".local" / "analyst-token.txt"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(encoded, encoding="utf-8")
    destination.chmod(0o600)
    print("Analyst session written to ignored .local/analyst-token.txt (expires in 8 hours).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["migrate", "seed", "token", "ingest"])
    args = parser.parse_args()
    if args.command == "migrate":
        migrate()
    elif args.command == "token":
        token()
    elif args.command == "seed":
        from seed import seed

        seed()
    else:
        from ingest import ingest_documents

        with psycopg.connect(settings().admin_database_url.get_secret_value()) as conn:
            print(f"Ingested {ingest_documents(conn)} new fictional document versions.")
